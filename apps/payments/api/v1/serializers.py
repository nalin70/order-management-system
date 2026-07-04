from rest_framework import serializers

from apps.payments.models import PaymentTransaction


class PaymentTransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentTransaction
        fields = [
            "id",
            "order",
            "amount",
            "status",
            "transaction_reference",
            "retry_count",
            "created_at",
        ]
        read_only_fields = [
            "id",
            "status",
            "transaction_reference",
            "retry_count",
            "created_at",
        ]


class PaymentInitiateSerializer(serializers.Serializer):
    order_id = serializers.IntegerField()


class PaymentRetrySerializer(serializers.Serializer):
    pass
