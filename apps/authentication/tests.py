from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase


class AuthenticationWorkflowTests(APITestCase):
    def test_customer_can_register_login_refresh_and_view_profile(self):
        register_response = self.client.post(
            "/api/auth/register/",
            {
                "first_name": "Ada",
                "last_name": "Lovelace",
                "email": "ada@example.com",
                "password": "StrongPass123!",
                "confirm_password": "StrongPass123!",
            },
            format="json",
        )
        self.assertEqual(register_response.status_code, 201)

        login_response = self.client.post(
            "/api/auth/login/",
            {"email": "ada@example.com", "password": "StrongPass123!"},
            format="json",
        )
        self.assertEqual(login_response.status_code, 200)
        access = login_response.data["data"]["access"]
        refresh = login_response.data["data"]["refresh"]

        refresh_response = self.client.post(
            "/api/auth/refresh/",
            {"refresh": refresh},
            format="json",
        )
        self.assertEqual(refresh_response.status_code, 200)
        self.assertIn("access", refresh_response.data)

        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")
        profile_response = self.client.get("/api/auth/profile/")
        self.assertEqual(profile_response.status_code, 200)
        self.assertEqual(profile_response.data["data"]["email"], "ada@example.com")

    def test_invalid_credentials_return_401(self):
        response = self.client.post(
            "/api/auth/login/",
            {"email": "missing@example.com", "password": "bad"},
            format="json",
        )
        self.assertEqual(response.status_code, 401)

    def test_admin_can_manage_users_by_role(self):
        user_model = get_user_model()
        admin = user_model.objects.create_user(
            username="admin@example.com",
            email="admin@example.com",
            password="password123",
            role="ADMIN",
        )
        customer = user_model.objects.create_user(
            username="customer@example.com",
            email="customer@example.com",
            password="password123",
            role="CUSTOMER",
        )
        self.client.force_authenticate(admin)

        list_response = self.client.get("/api/auth/users/")
        self.assertEqual(list_response.status_code, 200)
        self.assertEqual(len(list_response.data["data"]), 2)

        patch_response = self.client.patch(
            f"/api/auth/users/{customer.id}/",
            {"is_active": False, "role": "CUSTOMER"},
            format="json",
        )
        self.assertEqual(patch_response.status_code, 200)
        customer.refresh_from_db()
        self.assertFalse(customer.is_active)
