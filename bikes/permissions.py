from rest_framework.permissions import BasePermission


class IsOwnerOrAdmin(BasePermission):
    """Only bike owners (who own the bike) or admins can modify it."""

    def has_object_permission(self, request, view, obj):
        # Allow admins full access
        if request.user.is_staff:
            return True

        # Ensure the user is the owner of the bike
        return obj.owner == request.user