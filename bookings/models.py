from django.db import models
from django.contrib.auth import get_user_model
from rest_framework.exceptions import ValidationError

from bikes.models import Bike  # Import the Bike model from the Bikes app
from decimal import Decimal

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
    rental_duration = models.CharField(max_length=10, choices=RENTAL_DURATION_CHOICES, default='daily', help_text="Rental duration (e.g., hourly, daily, weekly).")
    total_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, help_text="Total rental cost.")
    payment_status = models.BooleanField(default=False, help_text="Indicates whether the payment is completed.")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', help_text="Current status of the booking.")
    created_at = models.DateTimeField(auto_now_add=True, help_text="Timestamp for when the booking was created.")
    updated_at = models.DateTimeField(auto_now=True, help_text="Timestamp for the last update.")

    def clean(self):
        """
        Validate that the end date is not earlier than the start date.
        """
        if self.end_date < self.start_date:
            raise ValidationError("End date cannot be earlier than start date.")

        """
        Validate that the bike is not already booked for the selected dates.
        """
        overlapping_bookings = Booking.objects.filter(
            bike=self.bike,
            start_date__lt=self.end_date,
            end_date__gt=self.start_date,
            status__in=['pending', 'confirmed']
        ).exclude(id=self.id)  # Exclude the current booking during updates
        if overlapping_bookings.exists():
            raise ValidationError("This bike is already booked for the selected dates.")

    def calculate_total_price(self):
        """
        Calculate the total price based on rental duration and bike's price per day.
        """
        if self.rental_duration == 'hourly':
            duration = (self.end_date - self.start_date).total_seconds()
            hourly_rate = Decimal(self.bike.price_per_day) / Decimal(24)
            return hourly_rate * Decimal(duration / 3600)
        elif self.rental_duration == 'daily':
            days = (self.end_date - self.start_date).days + 1
            return self.bike.price_per_day * days
        elif self.rental_duration == 'weekly':
            weeks = (self.end_date - self.start_date).days / 7
            return self.bike.price_per_day * 7 * weeks
        return Decimal(0)

    def save(self, *args, **kwargs):
        """
        Automatically calculate the total price if not provided.
        """
        if not self.total_price:
            self.total_price = self.calculate_total_price()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Booking {self.id} by {self.user.username} for {self.bike.name}"

    def is_completed(self):
        """
        Check if the booking is completed based on the current date.
        """
        from django.utils.timezone import now
        return self.end_date < now()

    def update_status(self):
        """
        Update the status of the booking if it's completed.
        """
        if self.is_completed() and self.status != 'completed':
            self.status = 'completed'
            self.save()
