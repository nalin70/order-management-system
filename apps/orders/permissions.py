from rest_framework.permissions import BasePermission


class IsAdminOrOwner(BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.user and request.user.is_staff:
            return True
        return bool(request.user and request.user.is_authenticated and getattr(obj, "user", None) == request.user)
