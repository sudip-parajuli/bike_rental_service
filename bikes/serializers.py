from datetime import datetime
from rest_framework import serializers
from .models import Bike

class BikehostCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for bike creation by hosts, excluding admin-controlled fields.
    """
    class Meta:
        model = Bike
        exclude = ['is_approved', 'is_featured', 'availability_status']
        read_only_fields = ['host', 'created_at', 'updated_at', 'average_rating', 'slug']

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

class BikeSerializer(serializers.ModelSerializer):
    """
    Full serializer for admin use, including all fields.
    """
    class Meta:
        model = Bike
        fields = '__all__'
        read_only_fields = ['host', 'created_at', 'updated_at', 'average_rating', 'slug']

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

class BikeRecommendationSerializer(serializers.ModelSerializer):
    """
    Serializer for bike recommendations with score and reason.
    """
    recommendation_score = serializers.FloatField(read_only=True, required=False)
    recommendation_reason = serializers.CharField(read_only=True, required=False)
    host_name = serializers.CharField(source='host.username', read_only=True)
    
    class Meta:
        model = Bike
        fields = [
            'id', 'name', 'type', 'brand', 'model_year', 'price_per_day',
            'average_rating', 'image', 'description', 'mileage',
            'engine_type', 'displacement', 'slug',
            'recommendation_score', 'recommendation_reason', 'host_name'
        ]
        read_only_fields = ['id', 'slug', 'average_rating']
