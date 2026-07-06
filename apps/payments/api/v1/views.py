from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_yasg.utils import swagger_auto_schema

from apps.orders.repositories.order_repository import OrderRepository
from apps.orders.permissions import IsAdminOrOwner
from apps.payments.models import PaymentTransaction
from apps.payments.services.payment_service import PaymentService
from common.permissions.base import is_admin_user
from .serializers import (
    PaymentInitiateSerializer,
    PaymentRetrySerializer,
    PaymentTransactionSerializer,
)


class PaymentListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if is_admin_user(request.user):
            transactions = PaymentTransaction.objects.all().order_by("-created_at")
        else:
            transactions = PaymentTransaction.objects.filter(order__user=request.user).order_by("-created_at")

        serializer = PaymentTransactionSerializer(transactions, many=True)
        return Response({"success": True, "message": "Payment transactions retrieved.", "data": serializer.data})


class PaymentDetailView(APIView):
    permission_classes = [IsAuthenticated, IsAdminOrOwner]

    def get(self, request, pk):
        payment = PaymentTransaction.objects.filter(id=pk).first()
        if not payment:
            return Response({"success": False, "message": "Payment transaction not found."}, status=status.HTTP_404_NOT_FOUND)
        self.check_object_permissions(request, payment.order)
        serializer = PaymentTransactionSerializer(payment)
        return Response({"success": True, "message": "Payment transaction retrieved.", "data": serializer.data})


class PaymentInitiateView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(request_body=PaymentInitiateSerializer)
    def post(self, request):
        serializer = PaymentInitiateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        order = OrderRepository.get_order(serializer.validated_data["order_id"])
        if not order:
            return Response({"success": False, "message": "Order not found."}, status=status.HTTP_404_NOT_FOUND)

        if order.user != request.user and not is_admin_user(request.user):
            return Response({"success": False, "message": "Permission denied."}, status=status.HTTP_403_FORBIDDEN)

        if order.status not in [
            order.Status.INVENTORY_RESERVED,
            order.Status.PAYMENT_FAILED,
        ]:
            return Response(
                {"success": False, "message": "Order is not in a payable state."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            payment = PaymentService.initiate_payment(order, order.total_amount)
        except ValueError as exc:
            return Response(
                {"success": False, "message": str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )
        serializer = PaymentTransactionSerializer(payment)
        return Response({"success": True, "message": "Payment queued.", "data": serializer.data}, status=status.HTTP_202_ACCEPTED)


class PaymentRetryView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(request_body=PaymentRetrySerializer)
    def post(self, request, pk):
        payment = PaymentTransaction.objects.filter(id=pk).first()
        if not payment:
            return Response({"success": False, "message": "Payment transaction not found."}, status=status.HTTP_404_NOT_FOUND)

        if payment.order.user != request.user and not is_admin_user(request.user):
            return Response({"success": False, "message": "Permission denied."}, status=status.HTTP_403_FORBIDDEN)

        if payment.status != PaymentTransaction.Status.FAILED:
            return Response(
                {"success": False, "message": "Only failed payments can be retried."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        payment = PaymentService.retry_payment(payment)
        serializer = PaymentTransactionSerializer(payment)
        return Response({"success": True, "message": "Payment retry queued.", "data": serializer.data}, status=status.HTTP_202_ACCEPTED)
