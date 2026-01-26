from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator
from django.urls import reverse
from django.core.files.storage import FileSystemStorage
import uuid
from django.utils import timezone

# Custom storage for uploaded files  for better organization
fs = FileSystemStorage(location='media/bike_host_requests/')

class User(AbstractUser):

    is_host = models.BooleanField(default=False, help_text="Indicates whether the user is a bike host.")
    phone_number = models.CharField(
        max_length=20,
        unique=True,
        blank=True,
        null=True,
        validators=[
            RegexValidator(
                regex=r'^\+?\d{7,15}$',
                message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed."
            )
        ],
        help_text="User's phone number."
    )
    nationality = models.CharField(max_length=100, blank=True, null=True, help_text="User's nationality.")
    address = models.TextField(blank=True, null=True, help_text="User's address (optional).")
    profile_picture = models.ImageField(
        upload_to='profile_pictures/',
        default='default_user.jpg',
        help_text="Profile image uploaded by the user."
    )
    date_of_birth = models.DateField(blank=True, null=True, help_text="User’s date of birth (optional).")
    bio = models.TextField(blank=True, null=True, help_text="Short description about the user.")
    created_at = models.DateTimeField(auto_now_add=True, help_text="Timestamp for when the user was created.")
    updated_at = models.DateTimeField(auto_now=True, help_text="Timestamp for the last update.")

    def __str__(self):
        return self.username

    @property
    def full_name(self):
        """Returns the full name of the user."""
        return f"{self.first_name} {self.last_name}".strip()

    @property
    def is_staff_or_superuser(self):
        """Check if the user is a staff member or superuser."""
        return self.is_staff or self.is_superuser

    def get_absolute_url(self):
        """Returns the URL for the user's profile."""
        return reverse('user_profile', kwargs={'username': self.username})


class hostProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='host_profile', help_text="User associated with this profile.")
    bank_account_details = models.TextField(blank=True, null=True, help_text="Bank account information for payouts.")
    total_bookings = models.PositiveIntegerField(default=0, help_text="Total number of bookings made for the host's bikes.")
    total_earnings = models.DecimalField(max_digits=10, decimal_places=2, default=0, help_text="Total earnings from all bookings.")
    created_at = models.DateTimeField(auto_now_add=True, help_text="Timestamp for when the profile was created.")
    updated_at = models.DateTimeField(auto_now=True, help_text="Timestamp for the last update.")

    def __str__(self):
        return f"host Profile for {self.user.username}"

    def update_earnings(self, amount):
        """
        Safely update the host's earnings and total bookings using F expressions.
        """
        if amount > 0:
            self.total_bookings += 1
            hostProfile.objects.filter(pk=self.pk).update(
                total_bookings=models.F('total_bookings') + 1,
                total_earnings=models.F('total_earnings') + amount
            )
            self.refresh_from_db()  # Refresh the instance to reflect the updated values

class BikehostRequest(models.Model):
    """
    Model to store bike host requests submitted by users.
    """
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE, help_text="User submitting the request.")
    bike_make = models.CharField(max_length=100, help_text="Make of the bike (e.g., Hero, Yamaha).")
    bike_model = models.CharField(max_length=100, help_text="Model of the bike (e.g., Splendor, FZ).")
    bike_year = models.PositiveIntegerField(help_text="Manufacturing year of the bike.")
    bike_registration_number = models.CharField(max_length=20, unique=True, help_text="Bike registration number.")
    registration_certificate = models.FileField(upload_to='bike_host_requests/bike_docs/registration/', storage=fs, help_text="Upload bike registration certificate.")
    insurance_certificate = models.FileField(upload_to='bike_host_requests/bike_docs/insurance/', storage=fs, help_text="Upload bike insurance certificate.")
    id_proof = models.FileField(upload_to='bike_host_requests/bike_docs/id_proof/', storage=fs, help_text="Upload user ID proof (e.g., driver’s license).")
    bike_photos = models.ImageField(upload_to='bike_host_requests/bike_photos/', storage=fs, help_text="Upload photos of the bike.")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', help_text="Request status.")
    requested_at = models.DateTimeField(auto_now_add=True, help_text="Timestamp when the request was submitted.")
    reviewed_at = models.DateTimeField(blank=True, null=True, help_text="Timestamp when the request was reviewed.")
    admin_notes = models.TextField(blank=True, null=True, help_text="Notes from the admin during review.")

    def __str__(self):
        return f"Request by {self.user.username} - {self.bike_make} {self.bike_model} ({self.status})"

    def approve(self):
        """Approve the request and update the user's is_host status."""
        self.status = 'approved'
        self.reviewed_at = timezone.now()
        self.user.is_host = True
        self.user.save()
        hostProfile.objects.get_or_create(user=self.user)  # Create hostProfile if it doesn't exist
        self.save()

    def reject(self, notes):
        """Reject the request with admin notes."""
        self.status = 'rejected'
        self.reviewed_at = timezone.now()
        self.admin_notes = notes
        self.save()