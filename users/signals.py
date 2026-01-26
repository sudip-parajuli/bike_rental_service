from django.db.models.signals import post_save
from django.dispatch import receiver
from allauth.socialaccount.models import SocialAccount
from .models import User, hostProfile

@receiver(post_save, sender=User)
def create_host_profile(sender, instance, created, **kwargs):
    """
    Automatically create an hostProfile when a user is marked as an host.
    """
    if created and instance.is_host:
        hostProfile.objects.get_or_create(user=instance)

@receiver(post_save, sender=SocialAccount)
def populate_user_profile(sender, instance, created, **kwargs):
    """
    Populate User's first_name, last_name, and profile_picture from Google OAuth data.
    """
    if created:
        user = instance.user
        data = instance.extra_data
        if instance.provider == 'google':
            user.first_name = data.get('given_name', user.first_name)
            user.last_name = data.get('family_name', user.last_name)
            # Full name check if given/family name are missing
            if not user.first_name and data.get('name'):
                user.first_name = data.get('name')
            user.save()