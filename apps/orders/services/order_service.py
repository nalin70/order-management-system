from django.db import transaction
from django.db.models import F

from apps.inventory.models import Product
from apps.orders.models import Order, OrderItem
from apps.orders.repositories.order_repository import OrderRepository
from common.permissions.base import is_admin_user
from common.utils.tasks import enqueue_task


class OrderService:
    @staticmethod
    def list_orders(user):
        if is_admin_user(user):
            return OrderRepository.get_queryset().order_by("-created_at")
        return OrderRepository.get_user_orders(user).order_by("-created_at")

    @staticmethod
    def get_order(user, order_id):
        order = OrderRepository.get_order(order_id)
        if order is None:
            return None
        if is_admin_user(user) or order.user == user:
            return order
        return None

    @staticmethod
    def create_order(user, items_data, enqueue=True):
        if not items_data:
            raise ValueError("Order must contain at least one item.")

        requested_items = []
        for item in items_data:
            if item["quantity"] <= 0:
                raise ValueError("Quantity must be greater than zero.")
            requested_items.append(
                {
                    "product_id": item["product"].id,
                    "quantity": item["quantity"],
                }
            )

        with transaction.atomic():
            order = Order.objects.create(
                user=user,
                status=Order.Status.PENDING,
                requested_items=requested_items,
            )

        if enqueue:
            from apps.orders.tasks import process_order

            enqueue_task(process_order, order.id)
        return order

    @staticmethod
    def update_order_status(order, status):
        order.status = status
        return OrderRepository.save_order(order)

    @staticmethod
    def process_order(order_id):
        queue_payment = False
        with transaction.atomic():
            order = Order.objects.select_for_update().filter(id=order_id).first()
            if not order:
                return None
            if order.status != Order.Status.PENDING:
                return order
            if not order.requested_items:
                order.status = Order.Status.CANCELLED
                order.save(update_fields=["status", "updated_at"])
                return order

            quantity_by_product = {}
            for item in order.requested_items:
                product_id = int(item["product_id"])
                quantity = int(item["quantity"])
                if quantity <= 0:
                    order.status = Order.Status.CANCELLED
                    order.save(update_fields=["status", "updated_at"])
                    return order
                quantity_by_product[product_id] = (
                    quantity_by_product.get(product_id, 0) + quantity
                )

            product_ids = sorted(quantity_by_product)
            products = {
                product.id: product
                for product in Product.objects.select_for_update()
                .filter(id__in=product_ids)
                .order_by("id")
            }

            for product_id, quantity in quantity_by_product.items():
                product = products.get(product_id)
                if not product or product.stock < quantity:
                    order.status = Order.Status.OUT_OF_STOCK
                    order.save(update_fields=["status", "updated_at"])
                    return order

            total_amount = 0
            order.items.all().delete()
            for requested_item in order.requested_items:
                product = products[int(requested_item["product_id"])]
                quantity = int(requested_item["quantity"])
                OrderItem.objects.create(
                    order=order,
                    product=product,
                    quantity=quantity,
                    price=product.price,
                )
                total_amount += product.price * quantity

            for product_id, quantity in quantity_by_product.items():
                Product.objects.filter(id=product_id).update(
                    stock=F("stock") - quantity
                )

            order.total_amount = total_amount
            order.status = Order.Status.INVENTORY_RESERVED
            order.save(update_fields=["total_amount", "status", "updated_at"])
            queue_payment = True

        if queue_payment:
            from apps.payments.tasks import process_order_payment

            enqueue_task(process_order_payment, order_id)
        return OrderRepository.get_order(order_id)
