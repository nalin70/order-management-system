import logging
import random
import uuid

from django.db import transaction

from apps.orders.models import Order
from apps.payments.models import PaymentTransaction
from apps.payments.repositories.payment_repository import PaymentRepository

logger = logging.getLogger(__name__)


class PaymentService:
    @staticmethod
    def _generate_reference():
        return uuid.uuid4().hex

    @staticmethod
    @transaction.atomic
    def initiate_payment(order: Order, amount):
        logger.info(
            "Initiating payment for order=%s amount=%s",
            order.id,
            amount,
        )

        payment = PaymentRepository.create_transaction(
            order=order,
            amount=amount,
            status=PaymentTransaction.Status.PENDING,
            transaction_reference=PaymentService._generate_reference(),
        )

        success = PaymentService._simulate_payment()
        if success:
            return PaymentService.mark_success(payment)

        return PaymentService.mark_failed(payment)

    @staticmethod
    @transaction.atomic
    def retry_payment(payment: PaymentTransaction):
        if payment.status == PaymentTransaction.Status.SUCCESS:
            logger.info(
                "Retry skipped for already successful payment=%s",
                payment.transaction_reference,
            )
            return payment

        payment.retry_count += 1
        logger.info(
            "Retrying payment=%s retry_count=%s",
            payment.transaction_reference,
            payment.retry_count,
        )
        payment.status = PaymentTransaction.Status.PENDING
        payment.save()

        success = PaymentService._simulate_payment()
        if success:
            return PaymentService.mark_success(payment)

        return PaymentService.mark_failed(payment)

    @staticmethod
    def mark_success(payment: PaymentTransaction):
        payment.status = PaymentTransaction.Status.SUCCESS
        payment = PaymentRepository.save_transaction(payment)

        order = payment.order
        order.status = Order.Status.COMPLETED
        order.save()

        logger.info(
            "Payment success for order=%s transaction=%s",
            order.id,
            payment.transaction_reference,
        )
        return payment

    @staticmethod
    def mark_failed(payment: PaymentTransaction):
        payment.status = PaymentTransaction.Status.FAILED
        payment = PaymentRepository.save_transaction(payment)

        order = payment.order
        order.status = Order.Status.PAYMENT_FAILED
        order.save()

        logger.warning(
            "Payment failed for order=%s transaction=%s retry_count=%s",
            order.id,
            payment.transaction_reference,
            payment.retry_count,
        )
        return payment

    @staticmethod
    def _simulate_payment():
        return random.random() < 0.8
