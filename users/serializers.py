from rest_framework import serializers
from django.contrib.auth import authenticate
from rest_framework.authtoken.models import Token
from .models import User, OwnerProfile
from django.utils import timezone

class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    confirm_password = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'password', 'confirm_password', 'first_name', 'last_name',
            'is_owner', 'phone_number', 'address', 'profile_picture'
        ]

    def validate(self, data):
        """Ensure password and password_confirm match."""
        if data['password'] != data['confirm_password']:
            raise serializers.ValidationError({"confirm_password": "Passwords do not match."})
        return data

    def create(self, validated_data):
        """Create a new user with hashed password, excluding confirm_password."""
        # Remove confirm_password from validated_data as it’s not part of the model
        validated_data.pop('confirm_password', None)
        user = User.objects.create_user(**validated_data)
        return user

    def validate_date_of_birth(self, value):
        """Ensure date of birth is not in the future,less than 18 or too old."""
        if value and value > timezone.now().date():
            raise serializers.ValidationError("Date of birth cannot be in the future.")
        if value and (timezone.now().year - value.year) < 18:
            raise serializers.ValidationError("Date of birth indicates an age that is less than 18.")
        if value and (timezone.now().year - value.year) > 120:
            raise serializers.ValidationError("Date of birth indicates an unrealistic age.")
        return value

    def validate_email(self, value):
        """Ensure email is not from disposable domains."""
        disposable_domains = ['mailinator.com', 'tempmail.com', 'guerrillamail.com', '10MinuteMail.com', 'YOPmail.com', 'throwawaymail.com',  ]
        if any(domain in value.lower() for domain in disposable_domains):
            raise serializers.ValidationError("Disposable email addresses are not allowed.")
        return value


class OwnerProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = OwnerProfile
        fields = '__all__'

    def validate_bank_account_details(self, value):
        """Basic validation for bank account details format."""
        if value and len(value.strip()) < 5:
            raise serializers.ValidationError("Bank account details must be at least 5 characters long.")
        return value


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        """Authenticate user and return token"""
        user = authenticate(username=data['username'], password=data['password'])
        if not user:
            raise serializers.ValidationError("Invalid credentials")
        token, created = Token.objects.get_or_create(user=user)
        return {'token': token.key, 'user': UserSerializer(user).data}