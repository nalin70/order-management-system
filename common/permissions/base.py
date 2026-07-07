from rest_framework.permissions import BasePermission


def is_admin_user(user):
    return bool(
        user
        and user.is_authenticated
        and (getattr(user, "role", None) == "ADMIN" or user.is_superuser)
    )


class IsAdminRole(BasePermission):
    def has_permission(self, request, view):
        return is_admin_user(request.user)


class IsAdminOrOwner(BasePermission):
    def has_object_permission(self, request, view, obj):
        if is_admin_user(request.user):
            return True
        return bool(
            request.user
            and request.user.is_authenticated
            and getattr(obj, "user", None) == request.user
        )
