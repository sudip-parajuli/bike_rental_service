from rest_framework import viewsets
from rest_framework.permissions import IsAdminUser

from .models import Issue
from .serializers import AdminPanelSerializer

class IssueViewSet(viewsets.ModelViewSet):
    """
    Manage issues (create, list, retrieve, update, delete).

    * Requires: Admin authentication
    * Returns: Issue data or list of issues
    """
    queryset = Issue.objects.all()
    serializer_class = AdminPanelSerializer
    permission_classes = [IsAdminUser]
    throttle_scope = 'admin_issues'  # Scoped to 50/day