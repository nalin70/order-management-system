import logging
import random
import uuid

from django.db import transaction

from apps.orders.models import Order
from apps.payments.models import PaymentTransaction
from apps.payments.repositories.payment_repository import PaymentRepository
from common.utils.tasks import enqueue_task

logger = logging.getLogger(__name__)


class PaymentService:
    @staticmethod
    def _generate_reference():
        return uuid.uuid4().hex

    @staticmethod
    def initiate_payment(order: Order, amount=None, enqueue=True):
        logger.info(
            "Initiating payment for order=%s amount=%s",
            order.id,
            amount or order.total_amount,
        )

        with transaction.atomic():
            order = Order.objects.select_for_update().filter(id=order.id).first()
            if not order:
                raise ValueError("Order not found.")
            if order.payment_transactions.filter(
                status=PaymentTransaction.Status.SUCCESS
            ).exists():
                raise ValueError("Order has already been paid.")
            if order.status not in [
                Order.Status.INVENTORY_RESERVED,
                Order.Status.PAYMENT_FAILED,
            ]:
                raise ValueError("Order is not in a payable state.")

            order.status = Order.Status.PAYMENT_PROCESSING
            order.save(update_fields=["status", "updated_at"])

            payment = PaymentRepository.create_transaction(
                order=order,
                amount=amount or order.total_amount,
                status=PaymentTransaction.Status.PENDING,
                transaction_reference=PaymentService._generate_reference(),
            )

        if enqueue:
            from apps.payments.tasks import process_payment_transaction

            enqueue_task(process_payment_transaction, payment.id)
        return payment

    @staticmethod
    def retry_payment(payment: PaymentTransaction, enqueue=True):
        with transaction.atomic():
            payment = (
                PaymentTransaction.objects.select_for_update()
                .select_related("order")
                .filter(id=payment.id)
                .first()
            )
            if not payment:
                raise ValueError("Payment transaction not found.")
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
            payment.save(update_fields=["retry_count", "status"])

            order = payment.order
            order.status = Order.Status.PAYMENT_PROCESSING
            order.save(update_fields=["status", "updated_at"])

        if enqueue:
            from apps.payments.tasks import process_payment_transaction

            enqueue_task(process_payment_transaction, payment.id)
        return payment

    @staticmethod
    def process_order_payment(order_id):
        order = Order.objects.filter(id=order_id).first()
        if not order:
            return None
        return PaymentService.initiate_payment(order, order.total_amount, enqueue=True)

    @staticmethod
    @transaction.atomic
    def process_pending_transaction(payment_id):
        payment = (
            PaymentTransaction.objects.select_for_update()
            .select_related("order")
            .filter(id=payment_id)
            .first()
        )
        if not payment:
            return None
        if payment.status != PaymentTransaction.Status.PENDING:
            return payment

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
        order.save(update_fields=["status", "updated_at"])

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
        order.save(update_fields=["status", "updated_at"])

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
