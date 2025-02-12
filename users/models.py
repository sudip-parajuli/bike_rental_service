from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator

class User(AbstractUser):
    # Additional Fields
    is_owner = models.BooleanField(default=False, help_text="Indicates whether the user is a bike owner.")
    phone_number = models.CharField(
        max_length=15,
        blank=True,
        null=True,
        validators=[
            RegexValidator(
                regex=r'^\+?[1-9]\d{1,14}$',
                message="Phone number must follow the international format (e.g., '+9779841234567')."
            )
        ],
        help_text="User's phone number (optional)."
    )
    address = models.TextField(blank=True, null=True, help_text="User's address (optional).")
    profile_picture = models.ImageField(
        upload_to='profile_pictures/',
        default='default_.png',
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
        """
        Returns the full name of the user (first_name + last_name).
        """
        return f"{self.first_name} {self.last_name}".strip()

    @property
    def is_staff_or_superuser(self):
        """
        Check if the user is a staff member or superuser.
        """
        return self.is_staff or self.is_superuser


class OwnerProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='owner_profile', help_text="User associated with this profile.")
    earnings = models.DecimalField(max_digits=10, decimal_places=2, default=0, help_text="Total earnings of the bike owner.")
    bank_account_details = models.TextField(blank=True, null=True, help_text="Bank account information for payouts.")
    total_bookings = models.PositiveIntegerField(default=0, help_text="Total number of bookings made for the owner's bikes.")
    total_earnings = models.DecimalField(max_digits=10, decimal_places=2, default=0, help_text="Total earnings from all bookings.")
    created_at = models.DateTimeField(auto_now_add=True, help_text="Timestamp for when the profile was created.")
    updated_at = models.DateTimeField(auto_now=True, help_text="Timestamp for the last update.")

    def __str__(self):
        return f"Owner Profile for {self.user.username}"

    def update_earnings(self, amount):
        """
        Update the owner's earnings and total bookings.
        """
        self.total_bookings += 1
        self.total_earnings += amount
        self.save()
