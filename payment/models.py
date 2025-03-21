from django.db import models
from bookings.models import Booking  # Import the Booking model from the Bookings app

class Payment(models.Model):
    # Choices for payment methods
    PAYMENT_METHOD_CHOICES = [
        ('paypal', 'PayPal'),
        ('esewa', 'eSewa'),
    ]

    # Choices for payment status
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]

    # Fields
    booking = models.OneToOneField(
        Booking,
        on_delete=models.CASCADE,
        related_name='payment',
        help_text="Booking associated with this payment."
    )
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Amount paid for the booking."
    )
    payment_method = models.CharField(
        max_length=50,
        choices=PAYMENT_METHOD_CHOICES,
        help_text="Select payment method"
    )
    transaction_id = models.CharField(
        max_length=100,
        unique=True,
        blank=True,
        null=True,
        help_text="Unique Transaction ID from the payment gateway."
    )
    transaction_uuid = models.CharField(
        max_length=100,
        unique=True,
        blank=True,
        null=True,
        help_text="Unique transaction UUID from eSewa payment gateway."
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        help_text="Current status of the payment."
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="Timestamp for when the payment was initiated."
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="Timestamp for the last update."
    )

    class Meta:
        indexes = [
            models.Index(fields=['transaction_id']),
            models.Index(fields=['booking']),
        ]

    def __str__(self):
        return f"Payment {self.id} for Booking {self.booking.id} via {self.payment_method}"

    def is_successful(self):
        """
        Check if the payment was successful.
        """
        return self.status == 'completed'

    def mark_as_completed(self, transaction_id=None, transaction_uuid=None):
        """
        Mark the payment as completed and update the transaction ID or UUID.
        Raises ValueError if transaction_id is not provided for online payments.
        """
        if self.payment_method in ['paypal', 'esewa'] and not (transaction_id or transaction_uuid):
            raise ValueError("Transaction ID or UUID is required for online payment completion.")
        self.status = 'completed'
        if transaction_id:
            self.transaction_id = transaction_id
        if transaction_uuid and self.payment_method == 'esewa':
            self.transaction_uuid = transaction_uuid
        self.save()

    def mark_as_failed(self):
        """
        Mark the payment as failed.
        """
        self.status = 'failed'
        self.save()

    def save(self, *args, **kwargs):
        """Override save to update booking payment status."""
        if self.pk:  # Existing instance
            original = Payment.objects.get(pk=self.pk)
            if original.status != 'completed' and self.status == 'completed':
                self.booking.payment_status = True
                self.booking.status = 'confirmed'
                self.booking.save(update_fields=['payment_status', 'status'])
        elif self.status == 'completed':  # New instance
            self.booking.payment_status = True
            self.booking.status = 'confirmed'
            self.booking.save(update_fields=['payment_status', 'status'])
        super().save(*args, **kwargs)