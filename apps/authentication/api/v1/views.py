from django.contrib.auth import authenticate
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.exceptions import PermissionDenied, ValidationError
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema

from apps.authentication.services.auth_service import AuthService
from .serializers import (
    ChangePasswordSerializer,
    CustomerProfileSerializer,
    CustomerRegisterSerializer,
    CustomerUpdateSerializer,
    LoginSerializer,
)


def success_response(data=None, message="Operation completed successfully."):
    return Response({"success": True, "message": message, "data": data or {}}, status=status.HTTP_200_OK)


def error_response(errors, message="Validation failed.", status_code=status.HTTP_400_BAD_REQUEST):
    return Response(
        {"success": False, "message": message, "errors": errors},
        status=status_code,
    )


class LoginView(APIView):
    @swagger_auto_schema(
        request_body=LoginSerializer,
        responses={
            200: openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "refresh": openapi.Schema(type=openapi.TYPE_STRING),
                    "access": openapi.Schema(type=openapi.TYPE_STRING),
                    "email": openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_EMAIL),
                    "role": openapi.Schema(type=openapi.TYPE_STRING),
                },
            ),
            401: "Invalid credentials",
            403: "User account is disabled",
        },
    )
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response(serializer.errors)

        user = authenticate(
            request,
            username=serializer.validated_data["email"],
            password=serializer.validated_data["password"],
        )
        if not user:
            return error_response(
                {"detail": "Invalid credentials."},
                message="Authentication failed.",
                status_code=status.HTTP_401_UNAUTHORIZED,
            )
        if not user.is_active:
            return error_response(
                {"detail": "User account is disabled."},
                message="Authentication failed.",
                status_code=status.HTTP_403_FORBIDDEN,
            )

        refresh = RefreshToken.for_user(user)
        return Response(
            {
                "success": True,
                "message": "Login successful.",
                "data": {
                    "refresh": str(refresh),
                    "access": str(refresh.access_token),
                    "email": user.email,
                    "role": user.role,
                },
            },
            status=status.HTTP_200_OK,
        )


class CustomerRegisterView(APIView):
    @swagger_auto_schema(request_body=CustomerRegisterSerializer)
    def post(self, request):
        serializer = CustomerRegisterSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response(serializer.errors)

        user = AuthService.register_customer(serializer.validated_data)
        data = CustomerProfileSerializer(user).data
        return Response({"success": True, "message": "Customer registered successfully.", "data": data}, status=status.HTTP_201_CREATED)


class CustomerProfileView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(responses={200: CustomerProfileSerializer()})
    def get(self, request):
        try:
            user = AuthService.get_customer_profile(request.user)
        except PermissionDenied as exc:
            return error_response({"detail": str(exc)}, status_code=status.HTTP_403_FORBIDDEN)

        return success_response(CustomerProfileSerializer(user).data)

    @swagger_auto_schema(request_body=CustomerUpdateSerializer, responses={200: CustomerProfileSerializer()})
    def patch(self, request):
        serializer = CustomerUpdateSerializer(data=request.data, partial=True)
        if not serializer.is_valid():
            return error_response(serializer.errors)

        try:
            user = AuthService.update_customer_profile(request.user, serializer.validated_data)
        except PermissionDenied as exc:
            return error_response({"detail": str(exc)}, status_code=status.HTTP_403_FORBIDDEN)

        return success_response(CustomerProfileSerializer(user).data)


class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(request_body=ChangePasswordSerializer)
    def patch(self, request):
        serializer = ChangePasswordSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response(serializer.errors)

        try:
            AuthService.change_customer_password(request.user, serializer.validated_data)
        except ValidationError as exc:
            return error_response(exc.detail)
        except PermissionDenied as exc:
            return error_response({"detail": str(exc)}, status_code=status.HTTP_403_FORBIDDEN)

        return success_response({}, message="Password changed successfully.")
