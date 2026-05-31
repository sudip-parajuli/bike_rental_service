from rest_framework import serializers
from bikes.models import Bike, MaintenanceRecord
from bookings.models import Booking
from django.contrib.auth import get_user_model

User = get_user_model()

class MaintenanceRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = MaintenanceRecord
        fields = '__all__'

class BikeSerializer(serializers.ModelSerializer):
    total_earnings = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    total_maintenance_cost = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    maintenance_count = serializers.IntegerField(read_only=True)
    maintenance_records = MaintenanceRecordSerializer(many=True, read_only=True)

    class Meta:
        model = Bike
        fields = '__all__'

class BookingSerializer(serializers.ModelSerializer):
    bike_name = serializers.CharField(source='bike.name', read_only=True)
    bike_brand = serializers.CharField(source='bike.brand', read_only=True)
    customer_name = serializers.CharField(source='user.get_full_name', read_only=True)
    customer_phone = serializers.CharField(source='user.phone_number', read_only=True)
    customer_email = serializers.CharField(source='user.email', read_only=True)
    customer_nationality = serializers.CharField(source='user.nationality', read_only=True)
    customer_address = serializers.CharField(source='user.address', read_only=True)
    
    class Meta:
        model = Booking
        fields = '__all__'

class WalkInCustomerSerializer(serializers.Serializer):
    full_name = serializers.CharField(max_length=150)
    phone_number = serializers.CharField(max_length=20)
    email = serializers.EmailField(required=False, allow_blank=True)
    nationality = serializers.CharField(max_length=50, default='Nepali')
    
class WalkInBookingSerializer(serializers.Serializer):
    phone_number = serializers.CharField(max_length=20)
    bike_id = serializers.IntegerField()
    start_date = serializers.DateTimeField()
    end_date = serializers.DateTimeField()
    
    # Financial overrides
    manual_discount = serializers.DecimalField(max_digits=10, decimal_places=2, required=False, default=0.0)
    advance_amount = serializers.DecimalField(max_digits=10, decimal_places=2, required=False, default=0.0)
    payment_method = serializers.CharField(max_length=20, required=False, default='cash')
    
    # Customer Documents
    driving_license_no = serializers.CharField(max_length=50, required=True, allow_blank=False)
    passport_no = serializers.CharField(max_length=50, required=False, allow_blank=True, default='')
    
    # Guarantor
    guarantor_name = serializers.CharField(max_length=150, required=False, allow_blank=True, default='')
    guarantor_phone = serializers.CharField(max_length=20, required=False, allow_blank=True, default='')
    guarantor_address = serializers.CharField(max_length=255, required=False, allow_blank=True, default='')
    
    # Checklist
    helmet = serializers.BooleanField(required=False, default=True)
    bungy_cord = serializers.BooleanField(required=False, default=False)
    maps = serializers.BooleanField(required=False, default=False)
    
    # Deposits
    deposit_passport = serializers.BooleanField(required=False, default=False)
    deposit_citizenship = serializers.BooleanField(required=False, default=False)
    deposit_id_card = serializers.BooleanField(required=False, default=False)
    deposit_other = serializers.CharField(max_length=100, required=False, allow_blank=True, default='')


class CustomerBookingHistorySerializer(serializers.ModelSerializer):
    bike_name = serializers.CharField(source='bike.name', read_only=True)
    bike_brand = serializers.CharField(source='bike.brand', read_only=True)
    
    class Meta:
        model = Booking
        fields = ['id', 'bike_name', 'bike_brand', 'start_date', 'end_date', 'total_price', 'status', 'payment_status']

class CustomerDetailSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(source='get_full_name', read_only=True)
    bookings = CustomerBookingHistorySerializer(many=True, read_only=True)
    booking_count = serializers.IntegerField(source='bookings.count', read_only=True)

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'full_name', 'phone_number', 'nationality', 'address', 'profile_picture', 'booking_count', 'bookings']

