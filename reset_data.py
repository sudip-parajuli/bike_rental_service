import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bike_rental_service.settings')
django.setup()

from django.contrib.auth import get_user_model
from bikes.models import Bike
from bookings.models import Booking, Feedback
from payment.models import Payment, Invoice
from testimonials.models import Testimonial
from users.models import BikehostRequest, hostProfile
from allauth.socialaccount.models import SocialApp, SocialAccount

User = get_user_model()

def reset_data():
    print("WARNING: This will delete ALL application data (Users, Bikes, Bookings, etc.).")
    print("Configuration (SocialApp) will be preserved.")
    
    # Order matters due to foreign keys
    
    print("Deleting Invoices...")
    Invoice.objects.all().delete()
    
    print("Deleting Payments...")
    Payment.objects.all().delete()
    
    print("Deleting Feedbacks...")
    Feedback.objects.all().delete()
    
    print("Deleting Bookings...")
    Booking.objects.all().delete()
    
    print("Deleting Testimonials...")
    Testimonial.objects.all().delete()
    
    print("Deleting Bike Host Requests...")
    BikehostRequest.objects.all().delete()
    
    print("Deleting Bikes...")
    Bike.objects.all().delete()
    
    print("Deleting Host Profiles...")
    hostProfile.objects.all().delete()
    
    # Delete Users (this cascades to SocialAccounts)
    print("Deleting Users...")
    count = User.objects.all().count()
    User.objects.all().delete()
    print(f"Deleted {count} users.")
    
    print("-" * 30)
    print("Data reset complete.")
    print("NOTE: You have deleted all users, including the Superuser.")
    print("You will need to sign up again or create a new superuser.")
    
    if SocialApp.objects.filter(provider='google').exists():
        print("Google OAuth configuration (SocialApp) was PRESERVED.")

if __name__ == '__main__':
    try:
        reset_data()
    except Exception as e:
        print(f"Error during reset: {e}")
