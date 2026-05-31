from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class StaffActivityLog(models.Model):
    """Records actions performed by staff members so admins can audit activity."""

    ACTION_CHOICES = [
        ('walk_in_booking', 'Walk-in Booking Created'),
        ('mark_paid', 'Booking Marked as Paid'),
        ('maintenance', 'Maintenance Record Added'),
        ('customer_created', 'Customer Created'),
    ]

    staff_user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='activity_logs',
    )
    action = models.CharField(max_length=50, choices=ACTION_CHOICES)
    description = models.TextField()
    booking = models.ForeignKey(
        'bookings.Booking',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='activity_logs',
    )
    is_read = models.BooleanField(default=False)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']
        verbose_name = 'Staff Activity Log'
        verbose_name_plural = 'Staff Activity Logs'

    def __str__(self):
        staff_name = self.staff_user.get_full_name() or self.staff_user.username if self.staff_user else 'Unknown'
        return f"[{self.get_action_display()}] by {staff_name} at {self.timestamp:%Y-%m-%d %H:%M}"
