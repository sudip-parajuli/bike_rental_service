from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.contrib.auth import get_user_model

User = get_user_model()

class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):
    def pre_social_login(self, request, sociallogin):
        """
        Invoked just after a user successfully authenticates via a
        social provider, but before the login is actually processed
        (and before the pre_social_login signal is emitted).
        """
        # If user is already logged in, let the default behavior happen (connect account)
        if request.user.is_authenticated:
            return

        # If the social account is already connected to a user, just log them in (default behavior)
        if sociallogin.is_existing:
            return

        # Check if the social account has an email
        if not sociallogin.email_addresses:
            return
        
        # We assume the first email is the primary one
        email_address = sociallogin.email_addresses[0]
        email = email_address.email

        # If we have an email, check if a user with that email already exists
        if email:
            try:
                existing_user = User.objects.get(email=email)
                
                # If user exists, connect the social account to this existing user
                # This bypasses the "signup" flow because allauth sees it as an existing social login
                sociallogin.connect(request, existing_user)
                
            except User.DoesNotExist:
                # If no user exists, let the default "signup" flow proceed
                pass
