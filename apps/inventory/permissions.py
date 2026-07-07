from rest_framework.permissions import SAFE_METHODS, BasePermission

from common.permissions.base import is_admin_user


class IsAdminOrReadOnly(BasePermission):
    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        return is_admin_user(request.user)
