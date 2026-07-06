from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    class Roles(models.TextChoices):
        ADMIN = "ADMIN", "Admin"
        CUSTOMER = "CUSTOMER", "Customer"

    email = models.EmailField(unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    role = models.CharField(
        max_length=20,
        choices=Roles.choices,
        default=Roles.CUSTOMER,
    )

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]

    @property
    def is_admin_role(self):
        return self.role == self.Roles.ADMIN or self.is_superuser

    @property
    def is_customer_role(self):
        return self.role == self.Roles.CUSTOMER

    def save(self, *args, **kwargs):
        if (self.is_staff or self.is_superuser) and not self.role:
            self.role = self.Roles.ADMIN
        elif not self.role:
            self.role = self.Roles.CUSTOMER
        super().save(*args, **kwargs)

    def __str__(self):
        return self.email
