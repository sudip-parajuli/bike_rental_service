from django.db import models
from django.contrib.auth import get_user_model
from django.db.models import Avg
from django.utils.text import slugify
from django.core.exceptions import ValidationError
from datetime import datetime

User = get_user_model()

class Bike(models.Model):
    # Choices for bike types
    BIKE_TYPES = [
        ('scooter', 'Scooter'),
        ('motorcycle', 'Motorcycle'),
        ('electric', 'Electric Bike'),
    ]

    # Fields
    name = models.CharField(max_length=100, help_text="Name of the bike (e.g., Honda Activa).")
    type = models.CharField(max_length=20, choices=BIKE_TYPES, help_text="Type of bike.")
    brand = models.CharField(max_length=50, help_text="Brand of the bike.")
    model_year = models.PositiveIntegerField(help_text="Year of manufacture.")
    mileage = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, help_text="Mileage of the bike.")
    description = models.TextField(max_length=500, help_text="Detailed description of the bike.")
    price_per_day = models.DecimalField(max_digits=10, decimal_places=2, help_text="Rental price per day.")
    availability_status = models.BooleanField(default=True, help_text="Indicates whether the bike is available for booking.")
    is_approved = models.BooleanField(default=False, help_text="Indicates whether the bike is approved by the admin.")
    image = models.ImageField(upload_to='bikes/', default='default_bike.png', help_text="Image of the bike.")
    slug = models.SlugField(unique=True, blank=True, null=True, help_text="SEO-friendly URL slug for the bike.")
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bikes', help_text="Owner of the bike.")
    created_at = models.DateTimeField(auto_now_add=True, help_text="Timestamp for when the bike was added.")
    updated_at = models.DateTimeField(auto_now=True, help_text="Timestamp for the last update.")
    average_rating = models.DecimalField(max_digits=3, decimal_places=1, null=True, blank=True)

    def save(self, *args, **kwargs):
        """Automatically generate a unique slug from the bike's name."""
        if not self.slug:
            base_slug = slugify(self.name)
            unique_slug = base_slug
            counter = 1
            while Bike.objects.filter(slug=unique_slug).exists():
                unique_slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = unique_slug

        super().save(*args, **kwargs)

    def update_average_rating(self):
        """Recalculate and update the stored average rating."""
        from bookings.models import Feedback
        avg_rating = Feedback.objects.filter(booking__bike=self).aggregate(Avg('rating'))['rating__avg']
        self.average_rating = round(avg_rating, 1) if avg_rating else None
        self.save()

    def __str__(self):
        return f"{self.brand} {self.name} ({self.model_year})"

    def clean(self):
        """Custom model validations."""
        current_year = datetime.now().year
        if self.model_year < 2000 or self.model_year > current_year:
            raise ValidationError("Invalid model year.")
        if self.price_per_day <= 0:
            raise ValidationError("Price per day must be greater than zero.")
        if self.mileage is not None and self.mileage < 0:
            raise ValidationError("Mileage cannot be negative.")
