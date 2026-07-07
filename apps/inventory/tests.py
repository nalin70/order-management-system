from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from rest_framework.test import APITestCase

from apps.inventory.models import Product


class InventoryApiTests(APITestCase):
    def setUp(self):
        user_model = get_user_model()
        self.admin = user_model.objects.create_user(
            username="admin@example.com",
            email="admin@example.com",
            password="password123",
            role="ADMIN",
        )
        self.customer = user_model.objects.create_user(
            username="customer@example.com",
            email="customer@example.com",
            password="password123",
            role="CUSTOMER",
        )

    def test_public_can_read_products_but_customer_cannot_create(self):
        response = self.client.get("/api/v1/products/")
        self.assertEqual(response.status_code, 200)

        self.client.force_authenticate(self.customer)
        response = self.client.post(
            "/api/v1/products/",
            {
                "name": "Widget",
                "description": "A widget",
                "sku": "WIDGET-001",
                "price": "10.00",
                "stock": 5,
            },
            format="json",
        )
        self.assertEqual(response.status_code, 403)

    def test_admin_can_create_product_and_negative_stock_is_rejected(self):
        self.client.force_authenticate(self.admin)
        response = self.client.post(
            "/api/v1/products/",
            {
                "name": "Widget",
                "description": "A widget",
                "sku": "WIDGET-001",
                "price": "10.00",
                "stock": 5,
            },
            format="json",
        )
        self.assertEqual(response.status_code, 201)

        response = self.client.post(
            "/api/v1/products/",
            {
                "name": "Bad Widget",
                "description": "Invalid",
                "sku": "BAD-001",
                "price": "10.00",
                "stock": -1,
            },
            format="json",
        )
        self.assertEqual(response.status_code, 400)

    def test_model_validation_rejects_negative_stock(self):
        product = Product(
            name="Bad",
            description="Bad",
            sku="BAD",
            price=Decimal("1.00"),
            stock=-1,
        )
        with self.assertRaises(ValidationError):
            product.full_clean()
