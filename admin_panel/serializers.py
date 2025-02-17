from rest_framework import serializers
from .models import Issue

class AdminPanelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Issue
        fields = '__all__'

    def validate_status(self, value):
        """Ensure only valid status values are used."""
        if value not in ['open', 'in_progress', 'resolved']:
            raise serializers.ValidationError("Invalid status choice.")
        return value