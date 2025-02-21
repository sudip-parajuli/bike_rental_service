from rest_framework import serializers
from .models import Booking
from django.utils.timezone import now

class BookingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Booking
        fields = [
            'id', 'user', 'bike', 'start_date', 'end_date', 'pickup_location',
            'rental_duration', 'payment_option', 'total_price', 'payment_status',
            'status', 'created_at', 'updated_at', 'is_active'
        ]
        read_only_fields = ['id', 'user', 'total_price', 'payment_status', 'status', 'created_at', 'updated_at', 'is_active']

    def validate_start_date(self, value):
        if value < now():
            raise serializers.ValidationError("Start date cannot be in the past.")
        return value

    def validate_end_date(self, value):
        if value < now():
            raise serializers.ValidationError("End date must be in the future.")
        return value

    def validate(self, data):
        if data['end_date'] <= data['start_date']:
            raise serializers.ValidationError("End date must be after the start date.")
        bike = data.get('bike')
        if bike and not bike.availability_status:
            raise serializers.ValidationError("Selected bike is not available for booking.")
        return data

    def validate_pickup_location(self, value):
        if len(value.strip()) < 3:
            raise serializers.ValidationError("Pickup location must be at least 3 characters long.")
        if len(value) > 200:
            raise serializers.ValidationError("Pickup location must not exceed 200 characters.")
        return value