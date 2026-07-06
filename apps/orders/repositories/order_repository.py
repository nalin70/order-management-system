from apps.orders.models import Order


class OrderRepository:
    @staticmethod
    def get_queryset():
        return (
            Order.objects.select_related("user")
            .prefetch_related("items__product", "payment_transactions")
            .all()
        )

    @staticmethod
    def get_order(order_id):
        return OrderRepository.get_queryset().filter(id=order_id).first()

    @staticmethod
    def get_user_orders(user):
        return OrderRepository.get_queryset().filter(user=user)

    @staticmethod
    def create_order(**validated_data):
        return Order.objects.create(**validated_data)

    @staticmethod
    def save_order(order):
        order.save()
        return order
