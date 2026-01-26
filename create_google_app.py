import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bike_rental_service.settings')
django.setup()

from django.contrib.sites.models import Site
from allauth.socialaccount.models import SocialApp

def create_google_app():
    # Get the current site (default ID=1)
    site = Site.objects.get_current()

    # Check if Google app exists
    if SocialApp.objects.filter(provider='google').exists():
        print("Google SocialApp already exists.")
        return

    # Use env vars or placeholders
    client_id = os.environ.get('GOOGLE_CLIENT_ID', 'ENTER_YOUR_CLIENT_ID_HERE')
    secret = os.environ.get('GOOGLE_CLIENT_SECRET', 'ENTER_YOUR_SECRET_HERE')
    
    # Create the app
    app = SocialApp.objects.create(
        provider='google',
        name='Google Auth',
        client_id=client_id,
        secret=secret,
    )
    
    # Link to the current site
    app.sites.add(site)
    
    print(f"Created Google SocialApp for site: {site.domain}")
    print(f"Client ID: {client_id}")
    print("NOTE: If you used the default placeholder, please update these credentials in the Admin Portal (http://127.0.0.1:8000/admin/).")

if __name__ == '__main__':
    try:
        create_google_app()
    except Exception as e:
        print(f"Error: {e}")
