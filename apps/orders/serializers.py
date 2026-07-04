from rest_framework import serializers

from apps.inventory.models import Product
from apps.orders.models import Order, OrderItem


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

    def validate_quantity(self, value):
        if value <= 0:
            raise serializers.ValidationError("Quantity must be greater than zero.")
        return value


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True)
    status = serializers.CharField(read_only=True)
    total_amount = serializers.DecimalField(
        max_digits=12, decimal_places=2, read_only=True
    )
    created_at = serializers.DateTimeField(read_only=True)

    class Meta:
        model = Order
        fields = ["id", "user", "status", "total_amount", "created_at", "items"]
        read_only_fields = ["id", "user", "status", "total_amount", "created_at"]

    def create(self, validated_data):
        items_data = validated_data.pop("items", [])
        order = Order.objects.create(**validated_data)
        total_amount = 0

        for item_data in items_data:
            product = item_data["product"]
            quantity = item_data["quantity"]

            if product.stock < quantity:
                order.delete()
                raise serializers.ValidationError(
                    f"Product {product.name} does not have enough stock."
                )

            OrderItem.objects.create(
                order=order,
                product=product,
                quantity=quantity,
                price=product.price,
            )
            total_amount += product.price * quantity
            product.stock -= quantity
            product.save()

        order.total_amount = total_amount
        order.save()
        return order


class OrderStatusUpdateSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=Order.Status.choices)
