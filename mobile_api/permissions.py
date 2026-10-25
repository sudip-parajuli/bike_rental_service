from rest_framework.permissions import BasePermission


class IsStaffOrSuperuser(BasePermission):
    message = 'This action requires an active staff or administrator account.'

    def has_permission(self, request, view):
        user = request.user
        return bool(user and user.is_authenticated and user.is_active and (user.is_staff or user.is_superuser))
