from django.urls import path

from .views import PaymentDetailView, PaymentInitiateView, PaymentListView, PaymentRetryView

urlpatterns = [
    path("", PaymentListView.as_view(), name="payment-list"),
    path("initiate/", PaymentInitiateView.as_view(), name="payment-initiate"),
    path("<int:pk>/", PaymentDetailView.as_view(), name="payment-detail"),
    path("<int:pk>/retry/", PaymentRetryView.as_view(), name="payment-retry"),
]
