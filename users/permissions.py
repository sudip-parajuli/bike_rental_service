from rest_framework.permissions import BasePermission


class IsUserOrReadOnly(BasePermission):
    """
    Only the user themselves or admins can view or modify their profile.
    Others (including unauthenticated users and regular users) cannot access.
    """

    def has_object_permission(self, request, view, obj):
        # Allow admins to view and modify any user's profile
        if request.user and request.user.is_staff or request.user.is_superuser:
            return True

        # Allow the user to view and modify only their own profile
        return request.user and request.user == obj


class IsOwnerOrAdmin(BasePermission):
    """Only bike owners or admins can modify owner profiles."""
    def has_object_permission(self, request, view, obj):
        return request.user.is_staff or obj.user == request.user
