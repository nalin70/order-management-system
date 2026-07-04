from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_yasg.utils import swagger_auto_schema

from apps.orders.permissions import IsAdminOrOwner
from apps.orders.pagination import OrderPagination
from apps.orders.serializers import (
    OrderSerializer,
    OrderStatusUpdateSerializer,
)
from apps.orders.services.order_service import OrderService


class OrderListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        queryset = OrderService.list_orders(request.user)
        paginator = OrderPagination()
        page = paginator.paginate_queryset(queryset, request)
        serializer = OrderSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)

    @swagger_auto_schema(request_body=OrderSerializer)
    def post(self, request):
        serializer = OrderSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            order = OrderService.create_order(request.user, serializer.validated_data.get("items", []))
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(OrderSerializer(order).data, status=status.HTTP_201_CREATED)


class OrderDetailView(APIView):
    permission_classes = [IsAuthenticated, IsAdminOrOwner]

    def get(self, request, pk):
        order = OrderService.get_order(request.user, pk)
        if not order:
            return Response({"detail": "Order not found."}, status=status.HTTP_404_NOT_FOUND)
        self.check_object_permissions(request, order)
        serializer = OrderSerializer(order)
        return Response(serializer.data)


class OrderStatusUpdateView(APIView):
    permission_classes = [IsAuthenticated, IsAdminOrOwner]

    @swagger_auto_schema(request_body=OrderStatusUpdateSerializer)
    def patch(self, request, pk):
        order = OrderService.get_order(request.user, pk)
        if not order:
            return Response({"detail": "Order not found."}, status=status.HTTP_404_NOT_FOUND)
        if not request.user.is_staff:
            return Response({"detail": "Permission denied."}, status=status.HTTP_403_FORBIDDEN)

        serializer = OrderStatusUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        order = OrderService.update_order_status(order, serializer.validated_data["status"])
        return Response(OrderSerializer(order).data)
