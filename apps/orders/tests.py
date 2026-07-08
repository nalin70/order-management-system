from decimal import Decimal

from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase

from apps.inventory.models import Product
from apps.orders.models import Order, OrderItem
from apps.orders.services.order_service import OrderService
from apps.payments.models import PaymentTransaction


class OrderCreationWorkflowTests(APITestCase):
    def setUp(self):
        self.customer = get_user_model().objects.create_user(
            username="customer",
            email="customer@example.com",
            password="password123",
            role="CUSTOMER",
        )
        self.other_customer = get_user_model().objects.create_user(
            username="other",
            email="other@example.com",
            password="password123",
            role="CUSTOMER",
        )
        self.product = Product.objects.create(
            name="Widget",
            description="A test widget",
            sku="WIDGET-001",
            price=Decimal("19.99"),
            stock=5,
        )

    def test_customer_creates_order_and_reserves_inventory(self):
        self.client.force_authenticate(self.customer)

        response = self.client.post(
            "/api/v1/orders/",
            {"items": [{"product_id": self.product.id, "quantity": 2}]},
            format="json",
        )

        self.assertEqual(response.status_code, 201)
        order = Order.objects.get(id=response.data["id"])
        self.assertEqual(order.user, self.customer)
        self.assertEqual(order.status, Order.Status.INVENTORY_RESERVED)
        self.assertEqual(order.total_amount, Decimal("39.98"))
        self.assertEqual(order.requested_items, [{"product_id": self.product.id, "quantity": 2}])
        self.assertEqual(OrderItem.objects.filter(order=order).count(), 1)
        self.assertFalse(PaymentTransaction.objects.filter(order=order).exists())
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 3)

    def test_order_creation_ignores_submitted_user_id(self):
        self.client.force_authenticate(self.customer)

        response = self.client.post(
            "/api/v1/orders/",
            {
                "user_id": self.other_customer.id,
                "items": [{"product_id": self.product.id, "quantity": 1}],
            },
            format="json",
        )

        self.assertEqual(response.status_code, 201)
        order = Order.objects.get(id=response.data["id"])
        self.assertEqual(order.user, self.customer)

    def test_order_creation_reserves_inventory_without_auto_payment(self):
        order = OrderService.create_order(
            self.customer,
            [{"product": self.product, "quantity": 2}],
        )

        order.refresh_from_db()
        self.product.refresh_from_db()
        self.assertEqual(order.status, Order.Status.INVENTORY_RESERVED)
        self.assertEqual(order.total_amount, Decimal("39.98"))
        self.assertEqual(OrderItem.objects.filter(order=order).count(), 1)
        self.assertEqual(order.items.get().price, Decimal("19.99"))
        self.assertEqual(self.product.stock, 3)
        self.assertFalse(PaymentTransaction.objects.filter(order=order).exists())

    def test_order_creation_marks_out_of_stock_without_decrement(self):
        order = OrderService.create_order(
            self.customer,
            [{"product": self.product, "quantity": 6}],
        )

        order.refresh_from_db()
        self.product.refresh_from_db()
        self.assertEqual(order.status, Order.Status.OUT_OF_STOCK)
        self.assertEqual(OrderItem.objects.count(), 0)
        self.assertEqual(self.product.stock, 5)
