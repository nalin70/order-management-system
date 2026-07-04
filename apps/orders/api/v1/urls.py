from django.urls import path

from apps.orders.api.v1.views import (
    OrderListCreateView,
    OrderDetailView,
    OrderStatusUpdateView,
)

urlpatterns = [
    path("orders/", OrderListCreateView.as_view(), name="order-list-create"),
    path("orders/<int:pk>/", OrderDetailView.as_view(), name="order-detail"),
    path("orders/<int:pk>/status/", OrderStatusUpdateView.as_view(), name="order-status-update"),
]
