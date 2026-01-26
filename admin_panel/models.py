from django.db import models
from django.contrib.auth import get_user_model
from bookings.models import Booking
import uuid

User = get_user_model()

class ContactMessage(models.Model):
    name = models.CharField(max_length=100, help_text="Name of the person submitting the message.")
    email = models.EmailField(help_text="Email address of the person submitting the message.")
    contact_number = models.CharField(max_length=15, help_text="Contact number of the person submitting the message.")
    message = models.TextField(max_length=1000, help_text="The message submitted via the contact form.")
    reply = models.TextField(max_length=1000, blank=True, null=True, help_text="Admin's reply to the message.")
    created_at = models.DateTimeField(auto_now_add=True, help_text="Timestamp for when the message was submitted.")
    updated_at = models.DateTimeField(auto_now=True, help_text="Timestamp for the last update.")

    def __str__(self):
        return f"Message from {self.name} ({self.email})"

class RentalContract(models.Model):
    booking = models.OneToOneField(Booking, on_delete=models.CASCADE, related_name='contract')
    contract_number = models.CharField(max_length=50, unique=True, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    # Customer Details (Snapshot/Override)
    customer_name = models.CharField(max_length=150)
    customer_address = models.CharField(max_length=255)
    customer_phone = models.CharField(max_length=20)
    nationality = models.CharField(max_length=50, default='Nepali')
    driving_license_no = models.CharField(max_length=50, blank=True)
    passport_no = models.CharField(max_length=50, blank=True)
    
    # Vehicle Details
    vehicle_model = models.CharField(max_length=100, default='')
    vehicle_number = models.CharField(max_length=50, default='N/A')
    vehicle_color = models.CharField(max_length=50, blank=True, default='')
    chassis_no = models.CharField(max_length=100, blank=True, default='')
    engine_no = models.CharField(max_length=100, blank=True, default='')
    
    # Guarantor Details
    guarantor_name = models.CharField(max_length=150, blank=True, default='')
    guarantor_address = models.CharField(max_length=255, blank=True, default='')
    guarantor_phone = models.CharField(max_length=20, blank=True, default='')
    
    # Checklist
    helmet = models.BooleanField(default=True)
    bungy_cord = models.BooleanField(default=False)
    maps = models.BooleanField(default=False)
    
    # Security Deposit
    deposit_passport = models.BooleanField(default=False)
    deposit_citizenship = models.BooleanField(default=False)
    deposit_id_card = models.BooleanField(default=False)
    deposit_other = models.CharField(max_length=100, blank=True)
    
    # Financials
    rate_per_day = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0, help_text="System calculated discount.")
    manual_discount = models.DecimalField(max_digits=10, decimal_places=2, default=0, help_text="Additional manual discount.")
    advance_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    balance_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    remarks = models.TextField(blank=True)

    def save(self, *args, **kwargs):
        if not self.contract_number:
            self.contract_number = f"CNT-{uuid.uuid4().hex[:8].upper()}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Contract {self.contract_number} for {self.booking}"