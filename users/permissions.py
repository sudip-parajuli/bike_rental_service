from rest_framework.permissions import BasePermission, SAFE_METHODS

class IsUserOrReadOnly(BasePermission):
    """Only the user themselves can modify their profile. Others can only view."""
    def has_object_permission(self, request, view, obj):
        return request.method in SAFE_METHODS or obj == request.user


class IsOwnerOrAdmin(BasePermission):
    """Only bike owners or admins can modify owner profiles."""
    def has_object_permission(self, request, view, obj):
        return request.user.is_staff or obj.user == request.user
