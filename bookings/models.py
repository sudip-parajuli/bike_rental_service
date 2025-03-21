from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
from rest_framework.exceptions import ValidationError
from bikes.models import Bike
from decimal import Decimal
from django.utils.timezone import now

User = get_user_model()

class Booking(models.Model):
    # Choices for booking status
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('cancelled', 'Cancelled'),
        ('completed', 'Completed'),
    ]

    # Choices for payment options
    PAYMENT_OPTION_CHOICES = [
        ('full_online', 'Full Payment Online'),
        ('partial_online', 'Partial Payment Online'),
        ('cash_on_delivery', 'Cash on Delivery'),
    ]

    # Choices for payment methods (eSewa, PayPal, or Cash on Delivery)
    PAYMENT_METHOD_CHOICES = [
        ('esewa', 'eSewa'),
        ('paypal', 'PayPal'),
        ('cash_on_delivery', 'Cash on Delivery'),
    ]

    # Fields
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bookings', help_text="User who made the booking.")
    bike = models.ForeignKey(Bike, on_delete=models.CASCADE, related_name='bookings', help_text="Bike being booked.")
    start_date = models.DateTimeField(help_text="Start date of the rental period.")
    end_date = models.DateTimeField(help_text="End date of the rental period.")
    pickup_location = models.CharField(max_length=200, help_text="Location where the bike will be picked up.")
    total_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, help_text="Total rental cost.")
    payment_status = models.BooleanField(default=False, help_text="Indicates whether the payment is completed.")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', help_text="Current status of the booking.")
    payment_option = models.CharField(max_length=20, choices=PAYMENT_OPTION_CHOICES, default='full_online', help_text="User’s chosen payment method.")
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES, null=True, blank=True, help_text="Selected payment method (eSewa, PayPal, or Cash on Delivery).")
    created_at = models.DateTimeField(auto_now_add=True, help_text="Timestamp for when the booking was created.")
    updated_at = models.DateTimeField(auto_now=True, help_text="Timestamp for the last update.")
    is_active = models.BooleanField(default=True, help_text="Indicates if the booking is active.")

    class Meta:
        constraints = [
            models.CheckConstraint(
                check=models.Q(end_date__gt=models.F('start_date')),
                name='end_date_after_start_date'
            )
        ]

    def clean(self):
        """Ensure end_date is after start_date and check for overlapping confirmed bookings."""
        if self.end_date <= self.start_date:
            raise ValidationError("End date must be later than start date.")

        # Check for overlapping confirmed bookings with payment
        overlapping_bookings = Booking.objects.filter(
            bike=self.bike,
            start_date__lt=self.end_date,
            end_date__gt=self.start_date,
            status='confirmed',
            payment_status=True
        ).exclude(id=self.id)  # Exclude the current booking during updates

        if overlapping_bookings.exists():
            raise ValidationError("This bike is already booked and paid for during the selected dates.")

    def calculate_total_price(self):
        """Calculate the total rental price based on the duration with discounts."""
        duration_days = (self.end_date - self.start_date).days + 1
        if not self.bike or not self.bike.price_per_day:
            return Decimal(0)

        base_price = self.bike.price_per_day * Decimal(duration_days)

        # Apply discounts based on duration in days
        if duration_days >= 28:
            discount = base_price * Decimal('0.20')  # 20% discount for 28+ days
        elif duration_days >= 21:
            discount = base_price * Decimal('0.15')  # 15% discount for 21-27 days
        elif duration_days >= 14:
            discount = base_price * Decimal('0.10')  # 10% discount for 14-20 days
        elif duration_days >= 7:
            discount = base_price * Decimal('0.05')  # 5% discount for 7-13 days
        else:
            discount = Decimal('0')  # No discount for 0-6 days

        return round(base_price - discount, 2)

    def save(self, *args, **kwargs):
        """Automatically calculate the total price if not provided."""
        if not self.total_price:
            self.total_price = self.calculate_total_price()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Booking {self.id} by {self.user.username} for {self.bike.name}"

    def is_completed(self):
        """Check if the booking is completed based on the current date."""
        return self.end_date < now()

    def update_status(self):
        """Update the status of the booking if it's completed."""
        if self.is_completed() and self.status != 'completed':
            self.status = 'completed'
            self.save()

    def get_feedback(self):
        """Retrieve feedback for the booking if available."""
        return getattr(self, 'feedback', None)

    def soft_delete(self):
        """Soft delete the booking by setting is_active to False."""
        self.is_active = False
        self.save()

    def restore(self):
        """Restore a soft-deleted booking by setting is_active to True."""
        self.is_active = True
        self.save()


class Feedback(models.Model):
    """Represents feedback submitted by a user for a specific booking."""
    booking = models.OneToOneField(
        Booking, on_delete=models.CASCADE, related_name='feedback',
        help_text="Booking associated with this feedback."
    )
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='feedbacks',
        help_text="User who submitted the feedback."
    )
    rating = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="Rating given by the user (1–5 stars)."
    )
    comments = models.TextField(
        max_length=500, blank=True, null=True, default="No additional comments.",
        help_text="Additional comments from the user."
    )
    created_at = models.DateTimeField(auto_now_add=True, help_text="Timestamp for when the feedback was submitted.")

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['booking', 'user'],
                name='unique_feedback_per_booking_user'
            )
        ]

    def clean(self):
        """Validate that the rating is between 1 and 5."""
        if not (1 <= self.rating <= 5):
            raise ValidationError("Rating must be between 1 and 5.")

    def __str__(self):
        return f"Feedback by {self.user.username} for Booking {self.booking.id}"