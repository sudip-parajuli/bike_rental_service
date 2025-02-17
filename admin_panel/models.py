from django.db import models
from django.contrib.auth import get_user_model
from rest_framework.exceptions import ValidationError

from bikes.models import Bike  # Import the Bike model from the Bikes app

User = get_user_model()

class Issue(models.Model):
    # Choices for issue status
    STATUS_CHOICES = [
        ('open', 'Open'),
        ('in_progress', 'In Progress'),
        ('resolved', 'Resolved'),
    ]

    # Fields
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='issues', help_text="User who reported the issue.")
    bike = models.ForeignKey(Bike, on_delete=models.SET_NULL, null=True, blank=True, related_name='issues', help_text="Bike associated with the issue (optional).")
    description = models.TextField(max_length=1000, help_text="Detailed description of the issue.")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open', help_text="Current status of the issue.")
    resolved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='resolved_issues', help_text="Admin who resolved the issue.")
    created_at = models.DateTimeField(auto_now_add=True, help_text="Timestamp for when the issue was reported.")
    updated_at = models.DateTimeField(auto_now=True, help_text="Timestamp for the last update.")

    def __str__(self):
        return f"Issue {self.id} by {self.user.username}: {self.description[:50]}..."

    def mark_as_resolved(self, admin_user=None):
        """
        Mark the issue as resolved and assign the resolving admin.
        """
        self.status = 'resolved'
        if admin_user:
            self.resolved_by = admin_user
        self.save()

    def is_open(self):
        """
        Check if the issue is still open.
        """
        return self.status == 'open'

    def is_resolved(self):
        """
        Check if the issue has been resolved.
        """
        return self.status == 'resolved'

    def clean(self):
        """Ensure that only admins can mark an issue as resolved."""
        if self.status == 'resolved' and not self.resolved_by.is_staff:
            raise ValidationError("Only an admin can mark an issue as resolved.")