from django.db import models
from django.contrib.auth import get_user_model
from django.db.models import Avg
from django.utils.text import slugify
from django.core.exceptions import ValidationError
from datetime import datetime
from django.utils.timezone import now

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
    brand = models.CharField(max_length=50, null=True, blank=True, help_text="Brand of the bike.")
    model_year = models.PositiveIntegerField(null=True, blank=True, help_text="Year of manufacture.")
    mileage = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, help_text="Mileage of the bike.")
    description = models.TextField(max_length=500, null=True, blank=True, help_text="Detailed description of the bike.")
    price_per_day = models.DecimalField(max_digits=10, decimal_places=2, help_text="Rental price per day.")
    availability_status = models.BooleanField(default=True, help_text="Indicates whether the bike is available for booking.")
    is_approved = models.BooleanField(default=False, help_text="Indicates whether the bike is approved by the admin.")
    is_featured = models.BooleanField(default=False, help_text="Mark this bike as featured on the homepage.")
    image = models.ImageField(upload_to='bikes/', default='default_bike.png', help_text="Image of the bike.")
    slug = models.SlugField(unique=True, blank=True, null=True, help_text="SEO-friendly URL slug for the bike.")
    host = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bikes', help_text="host of the bike.")
    created_at = models.DateTimeField(auto_now_add=True, help_text="Timestamp for when the bike was added.")
    updated_at = models.DateTimeField(auto_now=True, help_text="Timestamp for the last update.")
    average_rating = models.DecimalField(max_digits=3, decimal_places=1, null=True, blank=True)
    
    # Engine & Performance
    engine_type = models.CharField(max_length=50, blank=True, null=True, help_text="Type of engine (e.g., 4-stroke, 2-stroke).")
    displacement = models.CharField(max_length=20, blank=True, null=True, help_text="Engine displacement (e.g., 125 cc).")
    max_power = models.CharField(max_length=20, blank=True, null=True, help_text="Maximum power output (e.g., 8.5 hp).")
    torque = models.CharField(max_length=20, blank=True, null=True, help_text="Torque output (e.g., 10 Nm).")
    transmission = models.CharField(max_length=50, blank=True, null=True, help_text="Transmission type (e.g., Automatic, 5-speed manual).")
    brakes = models.CharField(max_length=50, blank=True, null=True, help_text="Brake system (e.g., Disc/Drum).")
    dimensions = models.CharField(max_length=50, blank=True, null=True, help_text="Bike dimensions (e.g., 1800 x 700 x 1100 mm).")
    fuel_capacity = models.DecimalField(max_digits=5, decimal_places=1, blank=True, null=True, help_text="Fuel tank capacity in liters (e.g., 5.3 L).")
    
    # Vehicle Identification (Admin/Contract use)
    vehicle_number = models.CharField(max_length=20, blank=True, null=True, help_text="Vehicle Registration Number (Plate No).")
    color = models.CharField(max_length=50, blank=True, null=True, help_text="Vehicle Color.")
    chassis_no = models.CharField(max_length=100, blank=True, null=True, help_text="Chassis Number (VIN). Restricted view.")
    engine_no = models.CharField(max_length=100, blank=True, null=True, help_text="Engine Number. Restricted view.")

    # Maintenance
    next_maintenance_date = models.DateField(null=True, blank=True, help_text="Automatically calculated date for the next maintenance.")

    def is_booked_for_dates(self, start_date, end_date):
        """
        Check if the bike is booked for the given date range based on confirmed bookings
        with payment (partial or full).
        """
        from bookings.models import Booking
        return Booking.objects.filter(
            bike=self,
            start_date__lt=end_date,
            end_date__gt=start_date,
            status='confirmed',  # Only confirmed bookings
            payment_status__in=['paid', 'partial']  # Payment must be made (partial or full)
        ).exists()

    def is_available(self):
        """
        Check if the bike is currently available, considering both admin-set status
        and active confirmed bookings.
        """
        from bookings.models import Booking
        current_bookings = Booking.objects.filter(
            bike=self,
            start_date__lte=now(),
            end_date__gte=now(),
            status='confirmed',
            payment_status__in=['paid', 'partial']
        ).exists()
        return self.availability_status and not current_bookings

    @property
    def total_earnings(self):
        """Calculate the total earnings from confirmed and partially paid bookings for this bike."""
        from bookings.models import Booking
        bookings = Booking.objects.filter(
            bike=self,
            status='confirmed',
            payment_status__in=['paid', 'partial']  # Payment must be made (partial or full)
        ).aggregate(total_earnings=models.Sum('total_price'))
        return bookings['total_earnings'] or 0

    @property
    def total_maintenance_cost(self):
        """Calculate the total maintenance cost for this bike."""
        maintenance = self.maintenance_records.aggregate(total_cost=models.Sum('cost'))
        return maintenance['total_cost'] or 0

    @property
    def maintenance_count(self):
        """Count the total number of maintenance records for this bike."""
        return self.maintenance_records.count()

    @property
    def is_currently_rented(self):
        """Check if the bike is currently rented."""
        now_time = now()
        from bookings.models import Booking
        return Booking.objects.filter(
            bike=self,
            start_date__lte=now_time,
            end_date__gte=now_time,
            status='confirmed',
            payment_status__in=['paid', 'partial']
        ).exists()

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
        # Only validate model_year if it is provided (not None)
        if self.model_year is not None:
            if self.model_year < 2000 or self.model_year > current_year:
                raise ValidationError("Invalid model year.")
        if self.price_per_day <= 0:
            raise ValidationError("Price per day must be greater than zero.")
        if self.mileage is not None and self.mileage < 0:
            raise ValidationError("Mileage cannot be negative.")

class MaintenanceRecord(models.Model):
    bike = models.ForeignKey(Bike, on_delete=models.CASCADE, related_name='maintenance_records', help_text="Bike that was maintained.")
    date = models.DateField(help_text="Date of maintenance.")
    cost = models.DecimalField(max_digits=10, decimal_places=2, help_text="Cost of the maintenance.")
    description = models.TextField(help_text="Details of the maintenance work performed.")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Maintenance for {self.bike.name} on {self.date}"