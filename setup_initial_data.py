"""
Setup script to populate the fresh database with initial data.
Run this after migrations: python manage.py shell < setup_initial_data.py
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bike_rental_service.settings')
django.setup()

from django.contrib.auth import get_user_model
from bikes.models import Bike
from bookings.models import Booking
from testimonials.models import Testimonial
from users.models import hostProfile
from datetime import datetime, timedelta
from django.utils import timezone

User = get_user_model()

print("=" * 60)
print("Setting up initial data for BikeRentalService")
print("=" * 60)

# 1. Create or get admin user
print("\n1. Setting up admin user...")
admin, created = User.objects.get_or_create(
    username='admin',
    defaults={
        'email': 'admin@easymoto.com',
        'is_staff': True,
        'is_superuser': True,
        'is_host': True,
        'first_name': 'Admin',
        'last_name': 'User'
    }
)
if created:
    admin.set_password('admin123')
    admin.save()
    print(f"✓ Admin user created: {admin.username}")
else:
    print(f"✓ Admin user already exists: {admin.username}")

# 2. Create test users
print("\n2. Creating test users...")
test_users = [
    {'username': 'testuser', 'email': 'test@easymoto.com', 'first_name': 'Test', 'last_name': 'User', 'is_host': False, 'phone': '+9779851234567'},
    {'username': 'host1', 'email': 'host1@easymoto.com', 'first_name': 'John', 'last_name': 'Host', 'is_host': True, 'phone': '+9779851234568'},
    {'username': 'host2', 'email': 'host2@easymoto.com', 'first_name': 'Jane', 'last_name': 'Host', 'is_host': True, 'phone': '+9779851234569'},
]

for user_data in test_users:
    user, created = User.objects.get_or_create(
        username=user_data['username'],
        defaults={
            'email': user_data['email'],
            'first_name': user_data['first_name'],
            'last_name': user_data['last_name'],
            'is_host': user_data['is_host'],
            'phone_number': user_data['phone']
        }
    )
    if created:
        user.set_password('password123')
        user.save()
        print(f"✓ Created user: {user.username}")
        
        # Create host profile for hosts
        if user.is_host:
            profile, _ = hostProfile.objects.get_or_create(user=user)
            print(f"  ✓ Created host profile for {user.username}")
    else:
        print(f"✓ User already exists: {user.username}")

# 3. Create sample bikes
print("\n3. Creating sample bikes...")
bikes_data = [
    {
        'name': 'Honda Activa 6G',
        'brand': 'Honda',
        'type': 'scooter',
        'model_year': 2023,
        'price_per_day': 1500.00,
        'description': 'Fuel-efficient scooter perfect for city rides',
        'mileage': 50,
        'engine_type': 'petrol',
        'displacement': 109,
        'host': admin,
        'is_approved': True,
        'availability_status': True,
        'is_featured': True
    },
    {
        'name': 'Yamaha FZ-S',
        'brand': 'Yamaha',
        'type': 'sports',
        'model_year': 2023,
        'price_per_day': 2800.00,
        'description': 'Stylish sports bike with great performance',
        'mileage': 45,
        'engine_type': 'petrol',
        'displacement': 149,
        'host': admin,
        'is_approved': True,
        'availability_status': True,
        'is_featured': False
    },
    {
        'name': 'Royal Enfield Classic 350',
        'brand': 'Royal Enfield',
        'type': 'cruiser',
        'model_year': 2023,
        'price_per_day': 3200.00,
        'description': 'Classic cruiser for long rides',
        'mileage': 35,
        'engine_type': 'petrol',
        'displacement': 349,
        'host': User.objects.get(username='host1'),
        'is_approved': True,
        'availability_status': True,
        'is_featured': True
    },
    {
        'name': 'TVS Apache RTR 160',
        'brand': 'TVS',
        'type': 'sports',
        'model_year': 2023,
        'price_per_day': 1700.00,
        'description': 'Performance-oriented sports bike',
        'mileage': 48,
        'engine_type': 'petrol',
        'displacement': 159,
        'host': User.objects.get(username='host2'),
        'is_approved': True,
        'availability_status': True,
        'is_featured': False
    },
    {
        'name': 'Suzuki Gixxer SF',
        'brand': 'Suzuki',
        'type': 'sports',
        'model_year': 2023,
        'price_per_day': 1900.00,
        'description': 'Fully-faired sports bike with excellent handling',
        'mileage': 45,
        'engine_type': 'petrol',
        'displacement': 155,
        'host': admin,
        'is_approved': True,
        'availability_status': True,
        'is_featured': False
    },
]

for bike_data in bikes_data:
    bike, created = Bike.objects.get_or_create(
        name=bike_data['name'],
        defaults=bike_data
    )
    if created:
        print(f"✓ Created bike: {bike.name}")
    else:
        print(f"✓ Bike already exists: {bike.name}")

# 4. Create sample bookings
print("\n4. Creating sample bookings...")
test_user = User.objects.get(username='testuser')
bikes = Bike.objects.filter(is_approved=True)[:3]

for i, bike in enumerate(bikes):
    start_date = timezone.now() - timedelta(days=30-i*10)
    end_date = start_date + timedelta(days=3)
    
    booking, created = Booking.objects.get_or_create(
        user=test_user,
        bike=bike,
        start_date=start_date,
        defaults={
            'end_date': end_date,
            'pickup_location': 'Budhanilkantha, Kathmandu',
            'status': 'completed',
            'payment_status': True,
            'total_price': bike.price_per_day * 3
        }
    )
    if created:
        print(f"✓ Created booking: {test_user.username} -> {bike.name}")
    else:
        print(f"✓ Booking already exists")

# 5. Create sample testimonials
print("\n5. Creating sample testimonials...")
testimonials_data = [
    {
        'user': test_user,
        'rating': 5,
        'content': 'Great service! The bike was in perfect condition and the process was smooth.',
        'is_approved': True,
    },
    {
        'user': User.objects.get(username='host1'),
        'rating': 4,
        'content': 'Very convenient platform for renting bikes. Highly recommended!',
        'is_approved': True,
    },
]

for testimonial_data in testimonials_data:
    testimonial, created = Testimonial.objects.get_or_create(
        user=testimonial_data['user'],
        defaults=testimonial_data
    )
    if created:
        print(f"✓ Created testimonial from: {testimonial.user.username}")
    else:
        print(f"✓ Testimonial already exists")

print("\n" + "=" * 60)
print("Initial data setup complete!")
print("=" * 60)
print("\nCredentials:")
print("  Admin:")
print("    Username: admin")
print("    Password: admin123")
print("  Test User:")
print("    Username: testuser")
print("    Password: password123")
print("  Hosts:")
print("    Username: host1 / host2")
print("    Password: password123")
print("=" * 60)
