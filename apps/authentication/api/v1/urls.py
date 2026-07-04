from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from apps.authentication.api.v1.views import (
    ChangePasswordView,
    CustomerProfileView,
    CustomerRegisterView,
    LoginView,
)

urlpatterns = [
    path('register/', CustomerRegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('profile/', CustomerProfileView.as_view(), name='profile'),
    path('change-password/', ChangePasswordView.as_view(), name='change_password'),
]
