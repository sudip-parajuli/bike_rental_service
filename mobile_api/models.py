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
        ('dates_updated', 'Rental Dates Updated'),
        ('rental_returned', 'Bike Returned'),
        ('booking_updated', 'Booking Updated'),
        ('customer_reminder', 'Customer Reminder Opened'),
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


class RentalState(models.Model):
    booking = models.OneToOneField('bookings.Booking', on_delete=models.CASCADE, related_name='rental_state')
    notes = models.TextField(blank=True, max_length=2000)
    deposit_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    deposit_returned = models.BooleanField(default=False)
    returned_at = models.DateTimeField(null=True, blank=True)
    returned_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)


class StaffDevice(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='rental_devices')
    token = models.CharField(max_length=255, unique=True)
    platform = models.CharField(max_length=10, choices=[('android', 'Android'), ('ios', 'iOS')])
    active = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)


class ReminderDelivery(models.Model):
    booking = models.ForeignKey('bookings.Booking', on_delete=models.CASCADE, related_name='reminder_deliveries')
    due_at = models.DateTimeField()
    kind = models.CharField(max_length=20)
    channel = models.CharField(max_length=10, choices=[('push', 'Push'), ('email', 'Email')])
    recipient_key = models.CharField(max_length=255)
    device = models.ForeignKey(StaffDevice, null=True, blank=True, on_delete=models.SET_NULL)
    state = models.CharField(max_length=15, default='pending')
    attempts = models.PositiveIntegerField(default=0)
    attempted_at = models.DateTimeField(null=True, blank=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    error_code = models.CharField(max_length=100, blank=True)
    provider_ticket = models.CharField(max_length=255, blank=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=['booking', 'due_at', 'kind', 'channel', 'recipient_key'], name='unique_rental_reminder_delivery')]
        indexes = [models.Index(fields=['state', 'attempted_at'])]
