from rest_framework import serializers
from .models import Bike
from datetime import datetime

class BikeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Bike
        fields = '__all__'

    def validate_model_year(self, value):
        """Ensure the bike's model year is reasonable."""
        current_year = datetime.now().year
        if value < 2000 or value > current_year:
            raise serializers.ValidationError("Invalid model year.")
        return value

    def validate_price_per_day(self, value):
        """Ensure the price is positive."""
        if value <= 0:
            raise serializers.ValidationError("Price per day must be greater than zero.")
        return value

    def validate_image(self, value):
        """Validate image file size and type."""
        if value:
            if value.size > 5 * 1024 * 1024:  # 5MB limit
                raise serializers.ValidationError("Image file size must not exceed 5MB.")
            if not value.name.lower().endswith(('.png', '.jpg', '.jpeg')):
                raise serializers.ValidationError("Only PNG, JPG, or JPEG images are allowed.")
        return value

    def validate_description(self, value):
        """Sanitize description to prevent basic XSS."""
        from django.utils.html import escape
        return escape(value) if value else value