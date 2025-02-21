from rest_framework import serializers
from .models import Testimonial

class TestimonialSerializer(serializers.ModelSerializer):
    class Meta:
        model = Testimonial
        fields = '__all__'

    def validate_content(self, value):
        """Sanitize content to prevent XSS and enforce minimum length."""
        from django.utils.html import escape
        cleaned_value = escape(value) if value else value
        if len(cleaned_value.strip()) < 10:
            raise serializers.ValidationError("Testimonial content must be at least 10 characters long.")
        return cleaned_value


    def validate(self, data):
        user = self.context['request'].user
        from bookings.models import Booking
        completed_bookings = Booking.objects.filter(user=user, status='completed').exists()
        if not completed_bookings:
            raise serializers.ValidationError("You must have a completed booking to submit a testimonial.")
        return data