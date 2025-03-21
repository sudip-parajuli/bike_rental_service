from rest_framework import serializers
from django.contrib.auth import authenticate
from rest_framework.authtoken.models import Token
from .models import User, OwnerProfile, BikeOwnerRequest
from django.utils import timezone
from django.contrib.auth.password_validation import validate_password

class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'password', 'password_confirm', 'first_name', 'last_name',
            'is_owner', 'phone_number', 'address', 'profile_picture'
        ]

    def validate(self, data):
        """Ensure password and password_confirm match and apply password validation."""
        if data['password'] != data['password_confirm']:
            raise serializers.ValidationError({"password_confirm": "Passwords do not match."})

        # Remove password_confirm before validating password with Django's built-in validator
        data_copy = data.copy()
        data_copy.pop('password_confirm', None)

        validate_password(data['password'], user=User(**data_copy))
        return data

    def create(self, validated_data):
        """Create a new user with hashed password, excluding password_confirm."""
        validated_data.pop('password_confirm', None)  # Remove password_confirm before creating user

        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password'],
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', '')
        )
        return user

    def validate_email(self, value):
        """Ensure email is not from disposable domains."""
        disposable_domains = [
            'mailinator.com', 'tempmail.com', 'guerrillamail.com',
            '10MinuteMail.com', 'YOPmail.com', 'throwawaymail.com'
        ]
        if any(domain in value.lower() for domain in disposable_domains):
            raise serializers.ValidationError("Disposable email addresses are not allowed.")
        return value

    def validate_date_of_birth(self, value):
        """Ensure date of birth is realistic (not in the future, age >= 18, age <= 120)."""
        if value and value > timezone.now().date():
            raise serializers.ValidationError("Date of birth cannot be in the future.")
        if value and (timezone.now().year - value.year) < 18:
            raise serializers.ValidationError("User must be at least 18 years old.")
        if value and (timezone.now().year - value.year) > 120:
            raise serializers.ValidationError("Date of birth indicates an unrealistic age.")
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


class BikeOwnerRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = BikeOwnerRequest
        fields = [
            'bike_make', 'bike_model', 'bike_year', 'bike_registration_number',
            'registration_certificate', 'insurance_certificate', 'id_proof', 'bike_photos',
            'status', 'admin_notes', 'requested_at'
        ]
        read_only_fields = ['id', 'user', 'status', 'admin_notes', 'requested_at']

    def validate_bike_year(self, value):
        """Ensure bike year is not in the future and not too old (e.g., < 10 years)."""
        current_year = timezone.now().year
        if value > current_year:
            raise serializers.ValidationError("Bike year cannot be in the future.")
        if value < current_year - 10:
            raise serializers.ValidationError("Bike must be less than 10 years old.")
        return value

    def validate(self, data):
        """Ensure all required fields are provided."""
        request = self.context.get('request')
        if not request:
            raise serializers.ValidationError("Request context is required for file validation.")

        required_files = ['registration_certificate', 'insurance_certificate', 'id_proof', 'bike_photos']
        errors = {}

        # Check if each required file is present in request.FILES
        for field in required_files:
            if field not in request.FILES:
                errors[field] = "No file was submitted."

        if errors:
            raise serializers.ValidationError(errors)

        # Add files to validated data
        for field in required_files:
            data[field] = request.FILES[field]

        return data

    def validate_registration_certificate(self, value):
        """Validate file size and type for registration certificate."""
        if value:
            if value.size > 5 * 1024 * 1024:  # 5MB limit
                raise serializers.ValidationError("File size must not exceed 5MB.")
            if not value.name.lower().endswith(('.pdf', '.jpg', '.jpeg', '.png')):
                raise serializers.ValidationError("Only PDF, JPG, JPEG, or PNG files are allowed.")
        return value

    def validate_insurance_certificate(self, value):
        """Validate file size and type for insurance certificate."""
        if value:
            if value.size > 5 * 1024 * 1024:  # 5MB limit
                raise serializers.ValidationError("File size must not exceed 5MB.")
            if not value.name.lower().endswith(('.pdf', '.jpg', '.jpeg', '.png')):
                raise serializers.ValidationError("Only PDF, JPG, JPEG, or PNG files are allowed.")
        return value

    def validate_id_proof(self, value):
        """Validate file size and type for ID proof."""
        if value:
            if value.size > 5 * 1024 * 1024:  # 5MB limit
                raise serializers.ValidationError("File size must not exceed 5MB.")
            if not value.name.lower().endswith(('.pdf', '.jpg', '.jpeg', '.png')):
                raise serializers.ValidationError("Only PDF, JPG, JPEG, or PNG files are allowed.")
        return value

    def validate_bike_photos(self, value):
        """Validate file size and type for bike photos."""
        if value:
            if value.size > 5 * 1024 * 1024:  # 5MB limit
                raise serializers.ValidationError("Image file size must not exceed 5MB.")
            if not value.name.lower().endswith(('.jpg', '.jpeg', '.png')):
                raise serializers.ValidationError("Only JPG, JPEG, or PNG images are allowed.")
        return value

    def create(self, validated_data):
        """Custom create method to handle file fields."""
        # Remove user from validated_data if present (it will be set separately)
        validated_data.pop('user', None)
        # Create the instance with the validated data (including files)
        return BikeOwnerRequest.objects.create(**validated_data)