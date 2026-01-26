import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'BikeRentalService.settings')
django.setup()

from payment.models import Payment
from django.contrib.auth import get_user_model
from django.db.models import Sum

User = get_user_model()
user = User.objects.filter(username='host1').first()

if user:
    print(f"=== Payment Status for {user.username} ===\n")
    
    payments = Payment.objects.filter(booking__user=user).order_by('id')
    print(f"Total Payments: {payments.count()}\n")
    
    for p in payments:
        print(f"Payment ID {p.id}:")
        print(f"  Amount: NPR {p.amount}")
        print(f"  Status: {p.status}")
        print(f"  Booking ID: {p.booking.id}")
        print(f"  Booking Status: {p.booking.status}")
        print()
    
    pending = Payment.objects.filter(booking__user=user, status='pending')
    pending_total = pending.aggregate(Sum('amount'))['amount__sum'] or 0
    print(f"Pending Payments: {pending.count()}")
    print(f"Outstanding Amount: NPR {pending_total}")
    
    completed = Payment.objects.filter(booking__user=user, status='completed')
    completed_total = completed.aggregate(Sum('amount'))['amount__sum'] or 0
    print(f"\nCompleted Payments: {completed.count()}")
    print(f"Completed Amount: NPR {completed_total}")
else:
    print('User host1 not found')
