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