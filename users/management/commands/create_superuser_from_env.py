from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.conf import settings
import os

class Command(BaseCommand):
    help = 'Creates a superuser from environment variables if one does not exist'

    def handle(self, *args, **options):
        User = get_user_model()
        username = os.environ.get('DJANGO_SUPERUSER_USERNAME')
        email = os.environ.get('DJANGO_SUPERUSER_EMAIL')
        password = os.environ.get('DJANGO_SUPERUSER_PASSWORD')

        if not username or not password:
            self.stdout.write(self.style.WARNING('DJANGO_SUPERUSER_USERNAME or DJANGO_SUPERUSER_PASSWORD missing. Skipping superuser creation.'))
            return

        if User.objects.filter(username=username).exists():
            self.stdout.write(self.style.SUCCESS(f'Superuser "{username}" already exists.'))
        else:
            self.stdout.write(f'Creating superuser "{username}"...')
            try:
                User.objects.create_superuser(username=username, email=email, password=password)
                self.stdout.write(self.style.SUCCESS(f'Successfully created superuser "{username}"!'))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Error creating superuser: {e}'))

        # Update Site domain for Google OAuth
        from django.contrib.sites.models import Site
        try:
            site = Site.objects.get(id=settings.SITE_ID)
            site_domain = os.environ.get('SITE_DOMAIN', 'www.easymoto.com.np')
            site_name = os.environ.get('SITE_NAME', 'EasyMoto')
            site.domain = site_domain
            site.name = site_name
            site.save()
            self.stdout.write(self.style.SUCCESS(f'Updated Site configuration: {site.domain}'))
        except Exception as e:
            self.stdout.write(self.style.WARNING(f'Could not update Site: {e}'))
