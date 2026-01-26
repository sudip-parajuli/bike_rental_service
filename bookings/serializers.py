from rest_framework import serializers
from .models import Booking
from django.utils.timezone import now
from bikes.models import Bike


class BookingPaymentSelectSerializer(serializers.Serializer):
    payment_method = serializers.ChoiceField(choices=Booking.PAYMENT_METHOD_CHOICES, required=True)

    def validate_payment_method(self, value):
        """Ensure the payment method is valid for the booking's payment option."""
        booking = self.context['booking']
        if booking.payment_option not in ['full_online', 'partial_online']:
            raise serializers.ValidationError("Online payment not required for this booking.")
        if value not in ['esewa', 'paypal']:
            raise serializers.ValidationError("Only eSewa and PayPal are supported for online payments.")
        return value


class BookingSerializer(serializers.ModelSerializer):
    bike = serializers.PrimaryKeyRelatedField(queryset=Bike.objects.all())
    payment_method = serializers.ChoiceField(choices=Booking.PAYMENT_METHOD_CHOICES, required=False, allow_null=True,
                                             allow_blank=True)
    rental_duration = serializers.CharField(read_only=True)  # Make it read-only and calculated

    class Meta:
        model = Booking
        fields = [
            'id', 'user', 'bike', 'start_date', 'end_date', 'pickup_location',
            'rental_duration', 'payment_option', 'payment_method', 'total_price',
            'payment_status', 'status', 'created_at', 'updated_at', 'is_active'
        ]
        read_only_fields = ['id', 'user', 'total_price', 'payment_status', 'status', 'created_at', 'updated_at',
                            'is_active', 'rental_duration']

    def validate_start_date(self, value):
        if value.date() < now().date():
            raise serializers.ValidationError("Start date cannot be in the past.")
        return value

    def validate_end_date(self, value):
        if value.date() < now().date():
            raise serializers.ValidationError("End date must be in the future.")
        return value

    def validate(self, data):
        if data['end_date'] <= data['start_date']:
            raise serializers.ValidationError("End date must be after the start date.")

        bike = data.get('bike')
        if data['start_date'] > data['end_date']:
            raise serializers.ValidationError("End date must be after start date.")
        
        # Check for overlapping bookings
        overlapping_bookings = Booking.objects.filter(
            bike=data['bike'],
            start_date__lt=data['end_date'],
            end_date__gt=data['start_date'],
            status='confirmed',
            payment_status='paid'
        )
        if overlapping_bookings.exists():
            raise serializers.ValidationError("This bike is already booked for the selected dates.")

        return data

    def validate_pickup_location(self, value):
        if len(value.strip()) < 3:
            raise serializers.ValidationError("Pickup location must be at least 3 characters long.")
        if len(value) > 200:
            raise serializers.ValidationError("Pickup location must not exceed 200 characters.")
        return value

    def create(self, validated_data):
        booking = Booking.objects.create(**validated_data)
        booking.total_price = booking.calculate_total_price()
        # Set rental_duration based on duration (for display purposes, though read-only)
        duration_days = (booking.end_date - booking.start_date).days + 1
        if duration_days >= 28:
            booking.rental_duration = 'monthly'
        elif duration_days >= 21:
            booking.rental_duration = 'weekly'
        elif duration_days >= 14:
            booking.rental_duration = 'weekly'
        elif duration_days >= 7:
            booking.rental_duration = 'weekly'
        else:
            booking.rental_duration = 'daily'
        booking.save()
        return booking

    def update(self, instance, validated_data):
        instance.bike = validated_data.get('bike', instance.bike)
        instance.start_date = validated_data.get('start_date', instance.start_date)
        instance.end_date = validated_data.get('end_date', instance.end_date)
        instance.pickup_location = validated_data.get('pickup_location', instance.pickup_location)
        instance.payment_option = validated_data.get('payment_option', instance.payment_option)
        instance.payment_method = validated_data.get('payment_method', instance.payment_method)
        instance.payment_status = validated_data.get('payment_status', instance.payment_status)
        instance.save()
        instance.total_price = instance.calculate_total_price()
        # Update rental_duration based on new dates
        duration_days = (instance.end_date - instance.start_date).days + 1
        if duration_days >= 28:
            instance.rental_duration = 'monthly'
        elif duration_days >= 21:
            instance.rental_duration = 'weekly'
        elif duration_days >= 14:
            instance.rental_duration = 'weekly'
        elif duration_days >= 7:
            instance.rental_duration = 'weekly'
        else:
            instance.rental_duration = 'daily'
        instance.save()
        return instance

    def to_representation(self, instance):
        data = super().to_representation(instance)
        # Ensure rental_duration is included in the response
        duration_days = (instance.end_date - instance.start_date).days + 1
        if duration_days >= 28:
            data['rental_duration'] = 'monthly'
        elif duration_days >= 21:
            data['rental_duration'] = 'weekly'
        elif duration_days >= 14:
            data['rental_duration'] = 'weekly'
        elif duration_days >= 7:
            data['rental_duration'] = 'weekly'
        else:
            data['rental_duration'] = 'daily'
        return data