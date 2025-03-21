from rest_framework import serializers
from .models import ContactMessage

class ContactMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContactMessage
        fields = '__all__'

    def validate_message(self, value):
        """Sanitize message and enforce minimum length."""
        from django.utils.html import escape
        cleaned_value = escape(value) if value else value
        if len(cleaned_value.strip()) < 10:
            raise serializers.ValidationError("Message must be at least 10 characters long.")
        return cleaned_value

    def validate_reply(self, value):
        """Sanitize reply and enforce minimum length if provided."""
        from django.utils.html import escape
        cleaned_value = escape(value) if value else value
        if cleaned_value and len(cleaned_value.strip()) < 10:
            raise serializers.ValidationError("Reply must be at least 10 characters long if provided.")
        return cleaned_value

    def validate_contact_number(self, value):
        """Validate contact number format (basic validation)."""
        if not value:
            raise serializers.ValidationError("Contact number is required.")
        if not value.replace("+", "").replace(" ", "").isdigit():
            raise serializers.ValidationError("Contact number must contain only digits (and optionally a '+' prefix).")
        if len(value) < 7 or len(value) > 15:
            raise serializers.ValidationError("Contact number must be between 7 and 15 characters long.")
        return value