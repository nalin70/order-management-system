from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import check_password
from rest_framework.exceptions import PermissionDenied, ValidationError

User = get_user_model()


class AuthService:
    @staticmethod
    def register_customer(validated_data):
        return User.objects.create_user(
            username=validated_data["email"],
            email=validated_data["email"],
            password=validated_data["password"],
            first_name=validated_data.get("first_name", ""),
            last_name=validated_data.get("last_name", ""),
            role=User.Roles.CUSTOMER,
        )

    @staticmethod
    def get_customer_profile(user):
        if not user.is_authenticated:
            raise PermissionDenied("Authentication is required.")
        return user

    @staticmethod
    def update_customer_profile(user, validated_data):
        if user.role != User.Roles.CUSTOMER:
            raise PermissionDenied("Only customers may update their profile.")

        if "first_name" in validated_data:
            user.first_name = validated_data["first_name"]
        if "last_name" in validated_data:
            user.last_name = validated_data["last_name"]

        user.save()
        return user

    @staticmethod
    def change_customer_password(user, validated_data):
        if not check_password(validated_data["old_password"], user.password):
            raise ValidationError({"old_password": ["Old password is incorrect."]})

        user.set_password(validated_data["new_password"])
        user.save()
        return user

    @staticmethod
    def list_users():
        return User.objects.all().order_by("-created_at")

    @staticmethod
    def get_user(user_id):
        return User.objects.filter(id=user_id).first()

    @staticmethod
    def update_user(user, validated_data):
        for attr, value in validated_data.items():
            setattr(user, attr, value)
        if user.role == User.Roles.ADMIN:
            user.is_staff = True
        elif user.role == User.Roles.CUSTOMER and not user.is_superuser:
            user.is_staff = False
        user.save()
        return user
