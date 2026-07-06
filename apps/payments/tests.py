from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import override_settings
from rest_framework.test import APITestCase

from apps.inventory.models import Product
from apps.orders.models import Order
from apps.orders.services.order_service import OrderService
from apps.payments.models import PaymentTransaction


class PaymentWorkflowTests(APITestCase):
    def setUp(self):
        self.customer = get_user_model().objects.create_user(
            username="customer@example.com",
            email="customer@example.com",
            password="password123",
            role="CUSTOMER",
        )
        self.product = Product.objects.create(
            name="Widget",
            description="A widget",
            sku="WIDGET-PAY",
            price=Decimal("25.00"),
            stock=3,
        )

    @override_settings(CELERY_TASK_ALWAYS_EAGER=True)
    @patch(
        "apps.payments.services.payment_service.PaymentService._simulate_payment",
        side_effect=[False, True],
    )
    def test_failed_payment_can_be_retried_successfully(self, mock_payment):
        order = OrderService.create_order(
            self.customer,
            [{"product": self.product, "quantity": 1}],
            enqueue=False,
        )
        OrderService.process_order(order.id)
        order.refresh_from_db()
        self.assertEqual(order.status, Order.Status.PAYMENT_FAILED)

        payment = PaymentTransaction.objects.get(order=order)
        self.assertEqual(payment.status, PaymentTransaction.Status.FAILED)

        self.client.force_authenticate(self.customer)
        response = self.client.post(f"/api/v1/payments/{payment.id}/retry/")
        self.assertEqual(response.status_code, 202)

        payment.refresh_from_db()
        order.refresh_from_db()
        self.assertEqual(payment.status, PaymentTransaction.Status.SUCCESS)
        self.assertEqual(payment.retry_count, 1)
        self.assertEqual(order.status, Order.Status.COMPLETED)

    @override_settings(CELERY_TASK_ALWAYS_EAGER=True)
    @patch(
        "apps.payments.services.payment_service.PaymentService._simulate_payment",
        return_value=True,
    )
    def test_order_serializer_exposes_paid_state(self, mock_payment):
        order = OrderService.create_order(
            self.customer,
            [{"product": self.product, "quantity": 1}],
            enqueue=False,
        )
        OrderService.process_order(order.id)

        self.client.force_authenticate(self.customer)
        response = self.client.get(f"/api/v1/orders/{order.id}/")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data["is_paid"])
        self.assertEqual(response.data["payment_status"], PaymentTransaction.Status.SUCCESS)
