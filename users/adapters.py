from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.contrib.auth import get_user_model

User = get_user_model()

class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):
    def pre_social_login(self, request, sociallogin):
        """
        Invoked just after a user successfully authenticates via a
        social provider, but before the login is actually processed.
        
        Attempts to automatically link existing local accounts with
        the social account if their email addresses match.
        """
        try:
            # If user is already logged in, let the default behavior happen (connect account)
            if request.user.is_authenticated:
                return

            # If the social account is already connected to a user, just log them in (default behavior)
            if sociallogin.is_existing:
                return

            # Resolve email safely from sociallogin user or extra_data
            email = getattr(sociallogin.user, 'email', None)
            if not email and sociallogin.account and sociallogin.account.extra_data:
                email = sociallogin.account.extra_data.get('email')

            # Fallback: check email_addresses list if populated safely
            if not email and hasattr(sociallogin, 'email_addresses') and sociallogin.email_addresses:
                try:
                    email = sociallogin.email_addresses[0].email
                except (IndexError, AttributeError, TypeError):
                    pass

            # If we resolved a valid email, check if a user with that email already exists
            if email:
                email = email.strip()
                try:
                    existing_user = User.objects.get(email__iexact=email)
                    
                    # Connect the social account to this existing user
                    # This bypasses the "signup" flow since allauth now sees it as an existing social login
                    sociallogin.connect(request, existing_user)
                    
                except User.DoesNotExist:
                    # If no user exists, let the default "signup" flow proceed
                    pass
        except Exception as e:
            # Under NO circumstance should this adapter crash the authentication flow with a 500 error.
            # If any unexpected exception occurs, we print/log it and let the default flow proceed.
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error in CustomSocialAccountAdapter.pre_social_login: {e}", exc_info=True)
            print(f"Error in CustomSocialAccountAdapter: {e}")

