from celery import shared_task

from apps.payments.services.payment_service import PaymentService


@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=True, max_retries=3)
def process_order_payment(self, order_id):
    payment = PaymentService.process_order_payment(order_id)
    return payment.id if payment else None


@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=True, max_retries=3)
def process_payment_transaction(self, payment_id):
    payment = PaymentService.process_pending_transaction(payment_id)
    return payment.id if payment else None
