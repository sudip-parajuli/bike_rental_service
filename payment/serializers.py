from rest_framework import serializers
from .models import Payment
from bookings.models import Booking

class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = '__all__'
        read_only_fields = ['id', 'amount', 'transaction_id', 'status', 'created_at', 'updated_at']

    def validate(self, data):
        """Set amount from booking and validate."""
        booking = data.get('booking')
        if booking:
            # Automatically set amount from Booking.total_price
            data['amount'] = booking.total_price
        else:
            raise serializers.ValidationError("Booking is required.")
        return data

    def validate_transaction_id(self, value):
        """Ensure transaction ID is unique if provided."""
        if value and Payment.objects.filter(transaction_id=value).exists():
            raise serializers.ValidationError("This transaction ID is already in use.")
        return value