from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import User, OwnerProfile

@receiver(post_save, sender=User)
def create_owner_profile(sender, instance, created, **kwargs):
    """
    Automatically create an OwnerProfile when a user is marked as an owner.
    """
    if created and instance.is_owner:
        OwnerProfile.objects.create(user=instance)