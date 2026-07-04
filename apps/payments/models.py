import uuid

from django.db import models


def generate_transaction_reference():
    return uuid.uuid4().hex


class PaymentTransaction(models.Model):
    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        SUCCESS = "SUCCESS", "Success"
        FAILED = "FAILED", "Failed"

    order = models.ForeignKey(
        "orders.Order",
        on_delete=models.CASCADE,
        related_name="payment_transactions",
    )
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )
    retry_count = models.IntegerField(default=0)
    transaction_reference = models.CharField(
        max_length=64,
        unique=True,
        default=generate_transaction_reference,
        editable=False,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"PaymentTransaction {self.transaction_reference} ({self.status})"

