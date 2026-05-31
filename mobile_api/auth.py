from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView
from django.contrib.auth import get_user_model, authenticate
from rest_framework import serializers

User = get_user_model()


class AdminTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Custom serializer that allows login with either username OR email.
    Only allows staff/admin users to get tokens.
    Embeds role flags and user info directly into the JWT payload.
    """
    username_field = 'login'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['login'] = serializers.CharField()
        self.fields.pop('username', None)

    @classmethod
    def get_token(cls, user):
        """Embed role flags into the token payload for easy client-side access."""
        token = super().get_token(user)
        token['is_superuser'] = user.is_superuser
        token['is_staff'] = user.is_staff
        token['username'] = user.username
        token['full_name'] = user.get_full_name() or user.username
        return token

    def validate(self, attrs):
        login = attrs.get('login', '').strip()
        password = attrs.get('password', '')

        # Try to find user by username or email
        user = None
        db_user = None

        try:
            if '@' in login:
                db_user = User.objects.get(email__iexact=login)
                user = authenticate(username=db_user.username, password=password)
            else:
                db_user = User.objects.filter(username__iexact=login).first()
                if db_user:
                    user = authenticate(username=db_user.username, password=password)
        except User.DoesNotExist:
            pass

        if not user:
            # Check if the user exists but has no password (Google/social login only)
            if db_user and not db_user.has_usable_password():
                raise serializers.ValidationError(
                    'This account uses Google Sign-In only and has no password. '
                    'Please visit the EasyMoto website, go to your profile, and set a password '
                    'to enable mobile app access.'
                )
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
            'full_name': user.get_full_name() or user.username,
            'email': user.email,
            'is_superuser': user.is_superuser,
            'is_staff': user.is_staff,
        }


class AdminTokenObtainPairView(TokenObtainPairView):
    serializer_class = AdminTokenObtainPairSerializer
