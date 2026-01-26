from rest_framework.permissions import BasePermission


class IshostOrAdmin(BasePermission):
    """Only bike hosts (who own the bike) or admins can modify it."""

    def has_object_permission(self, request, view, obj):
        # Allow admins full access
        if request.user.is_staff:
            return True

        # Ensure the user is the host of the bike
        return obj.host == request.user