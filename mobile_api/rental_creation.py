from decimal import Decimal

from django.contrib.auth import get_user_model
from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework.exceptions import ValidationError

from admin_panel.models import RentalContract
from bikes.models import Bike
from bookings.models import Booking
from payment.models import Payment, Invoice
from .models import RentalState
from .operations import ensure_vehicle_available, quote, audit, customer_for_phone


@transaction.atomic
def create_walkin(staff, data):
    user = customer_for_phone(data['phone_number'])
    if not user:
        raise ValidationError({'phone_number': 'Create or select this customer first.'})
    bike = get_object_or_404(Bike.objects.select_for_update(), pk=data['bike_id'])
    start, end = data['start_date'], data['end_date']
    ensure_vehicle_available(bike, start, end)
    pricing = quote(bike, start, end, data['manual_discount'])
    if data['manual_discount'] > pricing['base'] - pricing['auto_discount']:
        raise ValidationError({'manual_discount': 'Discount cannot exceed the rental subtotal.'})
    advance = data['advance_amount']
    if advance > pricing['total']:
        raise ValidationError({'advance_amount': 'Advance cannot exceed the rental price. Record security deposits separately.'})
    method = 'esewa' if data['payment_method'] == 'qr' else 'cash_on_delivery'
    booking = Booking.objects.create(user=user, bike=bike, start_date=start, end_date=end,
        pickup_location='Budhanilkantha-03, opposite Park Village Resort', status='confirmed',
        payment_option='cash_on_delivery', payment_method=method, total_price=pricing['total'])
    contract_fields = {key: data.get(key, default) for key, default in {
        'driving_license_no': '', 'passport_no': '', 'guarantor_name': '', 'guarantor_phone': '',
        'guarantor_address': '', 'helmet': True, 'bungy_cord': False, 'maps': False,
        'deposit_passport': False, 'deposit_citizenship': False, 'deposit_id_card': False, 'deposit_other': '',
    }.items()}
    contract = RentalContract.objects.create(booking=booking,
        customer_name=user.get_full_name() or user.username, customer_phone=user.phone_number,
        customer_address=user.address or '', nationality=user.nationality or 'Nepali',
        vehicle_model=bike.name, vehicle_number=bike.vehicle_number or 'N/A',
        rate_per_day=bike.price_per_day, total_amount=pricing['total'],
        discount_amount=pricing['auto_discount'], manual_discount=data['manual_discount'],
        advance_amount=advance, balance_amount=pricing['total'] - advance,
        remarks='Created by staff in EasyMoto Operations', **contract_fields)
    if advance > 0:
        Payment.objects.create(booking=booking, amount=advance, payment_method=method,
            status='completed' if advance >= pricing['total'] else 'partial')
    RentalState.objects.create(booking=booking, deposit_amount=data.get('deposit_amount', 0), notes=data.get('notes', ''))
    invoice = Invoice.objects.create(booking=booking, invoice_number=f'INV-{booking.pk}-{booking.created_at:%Y%m%d}')
    audit(staff, booking, 'walk_in_booking', f'Created rental #{booking.pk}, {start.isoformat()} -> {end.isoformat()}.')
    return {'booking_id': booking.pk, 'contract_id': contract.pk, 'invoice_number': invoice.invoice_number,
            'total_price': str(pricing['total']), 'advance_amount': str(advance),
            'balance_amount': str(pricing['total'] - advance)}
