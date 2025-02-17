from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
from rest_framework.exceptions import ValidationError
from bikes.models import Bike
from decimal import Decimal
from django.utils.timezone import now

User = get_user_model()

class Booking(models.Model):
    # Choices for rental duration
    RENTAL_DURATION_CHOICES = [
        ('hourly', 'Hourly'),
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
    ]

    # Choices for booking status
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('cancelled', 'Cancelled'),
        ('completed', 'Completed'),
    ]

    # Fields
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bookings', help_text="User who made the booking.")
    bike = models.ForeignKey(Bike, on_delete=models.CASCADE, related_name='bookings', help_text="Bike being booked.")
    start_date = models.DateTimeField(help_text="Start date of the rental period.")
    end_date = models.DateTimeField(help_text="End date of the rental period.")
    pickup_location = models.CharField(max_length=200, help_text="Location where the bike will be picked up.")
    rental_duration = models.CharField(max_length=10, choices=RENTAL_DURATION_CHOICES, default='daily', help_text="Rental duration.")
    total_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, help_text="Total rental cost.")
    payment_status = models.BooleanField(default=False, help_text="Indicates whether the payment is completed.")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', help_text="Current status of the booking.")
    created_at = models.DateTimeField(auto_now_add=True, help_text="Timestamp for when the booking was created.")
    updated_at = models.DateTimeField(auto_now=True, help_text="Timestamp for the last update.")

    def clean(self):
        """Ensure end_date is after start_date and check for overlapping bookings."""
        if self.end_date <= self.start_date:
            raise ValidationError("End date must be later than start date.")

        overlapping_bookings = Booking.objects.filter(
            bike=self.bike,
            start_date__lt=self.end_date,
            end_date__gt=self.start_date,
            status__in=['pending', 'confirmed']
        ).exclude(id=self.id)  # Exclude the current booking during updates

        if overlapping_bookings.exists():
            raise ValidationError("This bike is already booked for the selected dates.")

    def calculate_total_price(self):
        """Calculate the total price based on rental duration."""
        duration_days = (self.end_date - self.start_date).days + 1

        if self.rental_duration == 'hourly':
            duration_hours = (self.end_date - self.start_date).total_seconds() / 3600
            return round((self.bike.price_per_day / 24) * Decimal(duration_hours), 2)

        elif self.rental_duration == 'daily':
            return round(self.bike.price_per_day * Decimal(duration_days), 2)

        elif self.rental_duration == 'weekly':
            full_weeks = duration_days // 7
            return round(self.bike.price_per_day * Decimal(7) * Decimal(full_weeks), 2)

        return Decimal(0)

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

    def clean(self):
        """Validate that the rating is between 1 and 5."""
        if not (1 <= self.rating <= 5):
            raise ValidationError("Rating must be between 1 and 5.")

    def __str__(self):
        return f"Feedback by {self.user.username} for Booking {self.booking.id}"
