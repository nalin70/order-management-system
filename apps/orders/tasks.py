from celery import shared_task

from apps.orders.services.order_service import OrderService


@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=True, max_retries=3)
def process_order(self, order_id):
    order = OrderService.process_order(order_id)
    return order.id if order else None
