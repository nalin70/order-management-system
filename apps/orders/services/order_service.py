from django.db import transaction
from django.db.models import F

from apps.inventory.models import Product
from apps.orders.models import Order, OrderItem
from apps.orders.repositories.order_repository import OrderRepository


class OrderService:
    @staticmethod
    def list_orders(user):
        if user.is_staff:
            return OrderRepository.get_queryset().order_by("-created_at")
        return OrderRepository.get_user_orders(user).order_by("-created_at")

    @staticmethod
    def get_order(user, order_id):
        order = OrderRepository.get_order(order_id)
        if order is None:
            return None
        if user.is_staff or order.user == user:
            return order
        return None

    @staticmethod
    @transaction.atomic
    def create_order(user, items_data):
        if not items_data:
            raise ValueError("Order must contain at least one item.")

        order = Order.objects.create(user=user)
        total_amount = 0

        for item in items_data:
            product = Product.objects.select_for_update().filter(id=item["product"].id).first()
            if not product:
                raise ValueError(f"Product with id {item['product'].id} does not exist.")

            if item["quantity"] <= 0:
                raise ValueError("Quantity must be greater than zero.")

            if product.stock < item["quantity"]:
                order.status = Order.Status.OUT_OF_STOCK
                order.save()
                raise ValueError(f"Product {product.name} does not have enough stock.")

            OrderItem.objects.create(
                order=order,
                product=product,
                quantity=item["quantity"],
                price=product.price,
            )
            product.stock = F("stock") - item["quantity"]
            product.save()
            total_amount += product.price * item["quantity"]

        order.total_amount = total_amount
        order.status = Order.Status.INVENTORY_RESERVED
        order.save()
        return order

    @staticmethod
    def update_order_status(order, status):
        order.status = status
        return OrderRepository.save_order(order)
