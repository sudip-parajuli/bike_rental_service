from rest_framework import viewsets
from rest_framework.permissions import IsAdminUser
from .models import ContactMessage
from .serializers import ContactMessageSerializer

class ContactMessageViewSet(viewsets.ModelViewSet):
    """
    Manage contact messages (create, list, retrieve, update, delete).

    * Requires: Admin authentication
    * Returns: Contact message data or list of messages
    """
    queryset = ContactMessage.objects.all()
    serializer_class = ContactMessageSerializer
    permission_classes = [IsAdminUser]
    throttle_scope = 'admin_contact_messages'  # Scoped to 50/day