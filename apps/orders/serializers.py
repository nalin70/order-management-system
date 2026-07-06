from rest_framework import serializers

from apps.inventory.models import Product
from apps.orders.models import Order, OrderItem
from apps.payments.models import PaymentTransaction


class OrderItemSerializer(serializers.ModelSerializer):
    product_id = serializers.PrimaryKeyRelatedField(
        source="product",
        queryset=Product.objects.all(),
        write_only=True,
    )
    name = serializers.CharField(source="product.name", read_only=True)
    unit_price = serializers.DecimalField(
        source="price",
        max_digits=10,
        decimal_places=2,
        read_only=True,
    )

    class Meta:
        model = OrderItem
        fields = ["id", "product_id", "name", "quantity", "unit_price"]
        read_only_fields = ["id", "name", "unit_price"]

    def validate_quantity(self, value):
        if value <= 0:
            raise serializers.ValidationError("Quantity must be greater than zero.")
        return value


class OrderCreateSerializer(serializers.Serializer):
    items = OrderItemSerializer(many=True)

    def validate_items(self, value):
        if not value:
            raise serializers.ValidationError("Order must contain at least one item.")
        return value


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    status = serializers.CharField(read_only=True)
    requested_items = serializers.JSONField(read_only=True)
    is_paid = serializers.SerializerMethodField()
    payment_status = serializers.SerializerMethodField()
    total_amount = serializers.DecimalField(
        max_digits=12, decimal_places=2, read_only=True
    )
    created_at = serializers.DateTimeField(read_only=True)

    class Meta:
        model = Order
        fields = [
            "id",
            "user",
            "status",
            "total_amount",
            "created_at",
            "requested_items",
            "items",
            "is_paid",
            "payment_status",
        ]
        read_only_fields = [
            "id",
            "user",
            "status",
            "total_amount",
            "created_at",
            "requested_items",
            "items",
            "is_paid",
            "payment_status",
        ]

    def get_is_paid(self, obj):
        return obj.payment_transactions.filter(
            status=PaymentTransaction.Status.SUCCESS
        ).exists()

    def get_payment_status(self, obj):
        latest_payment = obj.payment_transactions.order_by("-created_at").first()
        return latest_payment.status if latest_payment else None


class OrderStatusUpdateSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=Order.Status.choices)
