from rest_framework import viewsets
from rest_framework.permissions import IsAdminUser

from .models import Issue
from .serializers import AdminPanelSerializer

class IssueViewSet(viewsets.ModelViewSet):
    queryset = Issue.objects.all()
    serializer_class =AdminPanelSerializer
    permission_classes = [IsAdminUser]


