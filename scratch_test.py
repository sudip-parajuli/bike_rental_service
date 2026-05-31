import os
import django
import sys
from decimal import Decimal

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bike_rental_service.settings')
django.setup()

from django.contrib.auth import get_user_model
from bikes.models import Bike
from bookings.models import Booking
from admin_panel.models import RentalContract
from django.utils import timezone
from datetime import timedelta

User = get_user_model()

def test_booking_creation():
    try:
        # Get a test user and bike
        user = User.objects.first()
        bike = Bike.objects.filter(availability_status=True).first()
        
        if not user or not bike:
            print("Error: Need at least one user and available bike in DB to test.")
            return
            
        print(f"Testing with User: {user.username}, Bike: {bike.brand} {bike.name}")
        
        start_date = timezone.now() + timedelta(days=1)
        end_date = timezone.now() + timedelta(days=3)
        
        # Simulating view logic
        duration_days = (end_date - start_date).days + 1
        base_price = bike.price_per_day * Decimal(duration_days)

        print("Creating Booking...")
        booking = Booking.objects.create(
            user=user,
            bike=bike,
            start_date=start_date,
            end_date=end_date,
            pickup_location="Office",
            status='confirmed',
            payment_status='unpaid',
            payment_option='cash_on_delivery',
            payment_method='cash_on_delivery'
        )
        print(f"Booking created successfully: ID {booking.id}, Total: {booking.total_price}")

        # Automatic discount
        auto_discount = base_price - booking.total_price
        manual_discount = Decimal('0.00')
        total_amount = max(Decimal('0.00'), base_price - auto_discount - manual_discount)
        booking.total_price = total_amount
        
        advance_amount = Decimal('0.00')
        balance_amount = max(Decimal('0.00'), total_amount - advance_amount)
        
        booking.payment_status = 'unpaid'
        booking.save(update_fields=['total_price', 'payment_status'])
        print("Updated Booking fields.")

        print("Creating Contract...")
        contract = RentalContract.objects.create(
            booking=booking,
            customer_name=user.get_full_name() or user.username,
            customer_address=user.address or "Office Address",
            customer_phone=user.phone_number or "N/A",
            nationality=user.nationality or "Nepali",
            driving_license_no="DL-12345",
            passport_no="",
            vehicle_model=f"{bike.brand} {bike.name}",
            vehicle_number=bike.vehicle_number or "N/A",
            vehicle_color=bike.color or "",
            chassis_no=bike.chassis_no or "",
            engine_no=bike.engine_no or "",
            guarantor_name="",
            guarantor_phone="",
            guarantor_address="",
            helmet=True,
            bungy_cord=False,
            maps=False,
            deposit_passport=False,
            deposit_citizenship=False,
            deposit_id_card=False,
            deposit_other="",
            rate_per_day=bike.price_per_day,
            total_amount=total_amount,
            discount_amount=auto_discount,
            manual_discount=manual_discount,
            advance_amount=advance_amount,
            balance_amount=balance_amount,
            remarks="Test creation"
        )
        print(f"Contract created successfully: {contract.contract_number}")
        
    except Exception as e:
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_booking_creation()
