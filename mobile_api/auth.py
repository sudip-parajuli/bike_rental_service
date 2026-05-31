
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView
from django.contrib.auth import get_user_model, authenticate
from rest_framework import serializers

User = get_user_model()

class AdminTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Custom serializer that allows login with either username OR email.
    Only allows staff/admin users to get tokens.
    """
    username_field = 'login'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['login'] = serializers.CharField()
        self.fields.pop('username', None)

    def validate(self, attrs):
        login = attrs.get('login', '').strip()
        password = attrs.get('password', '')

        # Try to find user by username or email
        user = None
        try:
            if '@' in login:
                user_obj = User.objects.get(email__iexact=login)
                user = authenticate(username=user_obj.username, password=password)
            else:
                user = authenticate(username=login, password=password)
        except User.DoesNotExist:
            pass

        if not user:
            raise serializers.ValidationError(
                'No active admin account found with the given credentials. '
                'You can log in with your username or email address.'
            )

        if not (user.is_staff or user.is_superuser):
            raise serializers.ValidationError(
                'This app is for admin/staff only. Your account does not have admin access.'
            )

        if not user.is_active:
            raise serializers.ValidationError('This account is inactive.')

        refresh = self.get_token(user)
        return {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'username': user.username,
            'email': user.email,
            'is_superuser': user.is_superuser,
        }

class AdminTokenObtainPairView(TokenObtainPairView):
    serializer_class = AdminTokenObtainPairSerializer
