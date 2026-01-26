import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bike_rental_service.settings')
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()

try:
    admin = User.objects.get(username='admin')
    admin.set_password('admin123')
    admin.save()
    print("Successfully reset password for user 'admin' to 'admin123'")
except User.DoesNotExist:
    print("User 'admin' does not exist. Creating it...")
    User.objects.create_superuser('admin', 'admin@easymoto.com', 'admin123')
    print("Successfully created superuser 'admin' with password 'admin123'")
except Exception as e:
    print(f"An error occurred: {e}")
