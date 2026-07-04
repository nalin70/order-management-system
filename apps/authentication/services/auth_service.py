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
            role="CUSTOMER",
        )

    @staticmethod
    def get_customer_profile(user):
        if user.role != "CUSTOMER":
            raise PermissionDenied("Only customers may access this profile endpoint.")
        return user

    @staticmethod
    def update_customer_profile(user, validated_data):
        if user.role != "CUSTOMER":
            raise PermissionDenied("Only customers may update their profile.")

        if "first_name" in validated_data:
            user.first_name = validated_data["first_name"]
        if "last_name" in validated_data:
            user.last_name = validated_data["last_name"]

        user.save()
        return user

    @staticmethod
    def change_customer_password(user, validated_data):
        if user.role != "CUSTOMER":
            raise PermissionDenied("Only customers may change their password.")

        if not check_password(validated_data["old_password"], user.password):
            raise ValidationError({"old_password": ["Old password is incorrect."]})

        user.set_password(validated_data["new_password"])
        user.save()
        return user
