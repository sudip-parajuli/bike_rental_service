from rest_framework import serializers
from .models import Booking
from django.utils.timezone import now

class BookingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Booking
        fields = '__all__'

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
        return data
