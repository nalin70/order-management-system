from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from apps.authentication.api.v1.views import (
    AdminUserDetailView,
    AdminUserListView,
    ChangePasswordView,
    CustomerProfileView,
    CustomerRegisterView,
    LoginView,
)

urlpatterns = [
    path('register/', CustomerRegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('refresh/', TokenRefreshView.as_view(), name='refresh'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('profile/', CustomerProfileView.as_view(), name='profile'),
    path('change-password/', ChangePasswordView.as_view(), name='change_password'),
    path('users/', AdminUserListView.as_view(), name='admin-user-list'),
    path('users/<int:pk>/', AdminUserDetailView.as_view(), name='admin-user-detail'),
]
