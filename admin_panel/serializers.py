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

    def validate_description(self, value):
        """Sanitize description and enforce minimum length."""
        from django.utils.html import escape
        cleaned_value = escape(value) if value else value
        if len(cleaned_value.strip()) < 10:
            raise serializers.ValidationError("Issue description must be at least 10 characters long.")
        return cleaned_value