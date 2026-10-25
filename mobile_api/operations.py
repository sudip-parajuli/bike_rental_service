"""Staff rental operations. Lock the vehicle before creating or changing its bookings."""
from datetime import timedelta
from decimal import Decimal
from urllib.parse import urlencode
from zoneinfo import ZoneInfo

from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from admin_panel.models import RentalContract
from bikes.models import Bike
from bookings.models import Booking
from payment.models import Payment
from .models import RentalState, StaffActivityLog, ReminderDelivery

NEPAL = ZoneInfo('Asia/Kathmandu')


def rental_days(start, end):
    return max(1, (timezone.localdate(end, NEPAL) - timezone.localdate(start, NEPAL)).days + 1)


def quote(bike, start, end, manual_discount=Decimal('0'), rate=None):
    days = rental_days(start, end)
    base = Decimal(rate if rate is not None else bike.price_per_day) * days
    percent = Decimal('.20') if days >= 28 else Decimal('.15') if days >= 21 else Decimal('.10') if days >= 14 else Decimal('.05') if days >= 7 else Decimal('0')
    auto = (base * percent).quantize(Decimal('.01'))
    return {'days': days, 'base': base, 'auto_discount': auto, 'total': max(Decimal('0'), base - auto - manual_discount)}


def ensure_dates(start, end):
    if end <= start:
        raise ValidationError({'end_date': 'Return must be after pickup.'})


def ensure_vehicle_available(bike, start, end, exclude=None):
    ensure_dates(start, end)
    if not bike.availability_status or not bike.is_approved:
        raise ValidationError({'bike_id': 'This vehicle is unavailable or not approved.'})
    others = Booking.objects.filter(bike=bike, is_active=True, status='confirmed').exclude(pk=exclude)
    if others.filter(start_date__lt=end, end_date__gt=start).exists():
        raise ValidationError({'end_date': 'This vehicle already has a confirmed rental during those dates.'})
    if others.filter(start_date__lte=timezone.now(), end_date__lt=timezone.now()).exists():
        raise ValidationError({'bike_id': 'This vehicle has an overdue rental. Record its return before assigning it again.'})


def amount_paid(booking):
    try:
        payment = booking.payment
        if payment.status in ('partial', 'completed'):
            return payment.amount
    except Payment.DoesNotExist:
        pass
    if booking.payment_status == 'paid':
        return booking.total_price or Decimal('0')
    try:
        return booking.contract.advance_amount
    except RentalContract.DoesNotExist:
        return Decimal('0')


def due_state(booking, now=None):
    now = now or timezone.now()
    if booking.status in ('completed', 'cancelled') or not booking.is_active:
        return booking.status
    if booking.status == 'pending':
        return 'pending'
    if booking.start_date > now:
        return 'upcoming'
    if booking.end_date <= now:
        return 'overdue'
    if timezone.localdate(booking.end_date, NEPAL) == timezone.localdate(now, NEPAL):
        return 'due_today'
    if booking.end_date <= now + timedelta(hours=24):
        return 'due_soon'
    return 'on_rent'


def check_version(booking, expected):
    if expected != booking.updated_at:
        from rest_framework.exceptions import APIException
        error = APIException('Another staff member updated this rental. Refresh it before saving your changes.')
        error.status_code = 409
        raise error


def locked_booking(pk):
    # Consistent vehicle -> booking lock order also serializes walk-in creation.
    from django.shortcuts import get_object_or_404
    basic = get_object_or_404(Booking, pk=pk, is_active=True)
    Bike.objects.select_for_update().get(pk=basic.bike_id)
    return Booking.objects.select_for_update().select_related('bike', 'user').get(pk=pk)


def audit(user, booking, action, description):
    StaffActivityLog.objects.create(staff_user=user, booking=booking, action=action, description=description)


@transaction.atomic
def update_rental(pk, user, values):
    booking = locked_booking(pk)
    check_version(booking, values['expected_updated_at'])
    if booking.status == 'completed':
        if any(key in values for key in ('start_date', 'end_date', 'status', 'deposit_amount')) or values.get('recalculate_price'):
            raise ValidationError('Returned rental dates and prices are locked; handover notes can still be updated.')
        state, _ = RentalState.objects.get_or_create(booking=booking)
        state.notes = values.get('notes', state.notes)
        state.deposit_returned = values.get('deposit_returned', state.deposit_returned)
        state.save()
        Booking.objects.filter(pk=booking.pk).update(updated_at=timezone.now())
        audit(user, booking, 'booking_updated', f'Returned rental #{booking.pk}: handover notes/deposit updated.')
        booking.refresh_from_db()
        return booking
    if booking.status in ('completed', 'cancelled'):
        raise ValidationError('Closed rentals cannot be rescheduled.')
    start, end = values.get('start_date', booking.start_date), values.get('end_date', booking.end_date)
    ensure_dates(start, end)
    new_status = values.get('status', booking.status)
    if booking.status == 'confirmed' and new_status == 'pending':
        raise ValidationError('A confirmed rental cannot be moved back to pending.')
    if new_status == 'cancelled' and booking.status == 'confirmed' and booking.start_date <= timezone.now():
        raise ValidationError('A rental already on the road must be returned, not cancelled.')
    if new_status == 'confirmed':
        ensure_vehicle_available(booking.bike, start, end, exclude=booking.pk)
    paid = amount_paid(booking)
    old_dates = f'{booking.start_date.isoformat()} -> {booking.end_date.isoformat()}'
    booking.start_date, booking.end_date, booking.status = start, end, new_status
    state, _ = RentalState.objects.get_or_create(booking=booking)
    for key in ('notes', 'deposit_amount', 'deposit_returned'):
        if key in values:
            setattr(state, key, values[key])
    state.save()
    try:
        contract = booking.contract
    except RentalContract.DoesNotExist:
        contract = None
    if values.get('recalculate_price'):
        pricing = quote(booking.bike, start, end, contract.manual_discount if contract else Decimal('0'), contract.rate_per_day if contract else None)
        booking.total_price = pricing['total']
        booking.payment_status = 'paid' if paid >= booking.total_price else 'partial' if paid > 0 else 'unpaid'
        if contract:
            contract.total_amount, contract.discount_amount = booking.total_price, pricing['auto_discount']
            contract.balance_amount = max(Decimal('0'), booking.total_price - paid)
            contract.save(update_fields=['total_amount', 'discount_amount', 'balance_amount'])
        # Reflect a larger agreed balance without changing cash already received.
        if paid > 0:
            payment, _ = Payment.objects.get_or_create(booking=booking, defaults={
                'amount': paid, 'payment_method': 'cash_on_delivery', 'status': 'pending'})
            Payment.objects.filter(pk=payment.pk).update(amount=paid,
                status='completed' if booking.payment_status == 'paid' else 'partial')
    # Avoid Booking.save's payment synchronization changing the amount/status behind us.
    Booking.objects.filter(pk=booking.pk).update(start_date=start, end_date=end, status=new_status,
        total_price=booking.total_price, payment_status=booking.payment_status, updated_at=timezone.now())
    obsolete = ReminderDelivery.objects.filter(booking=booking, state__in=['pending', 'failed'])
    if new_status == 'confirmed':
        obsolete = obsolete.exclude(due_at=end)
    obsolete.update(state='cancelled')
    audit(user, booking, 'dates_updated', f'Rental #{booking.pk}: {old_dates}; now {start.isoformat()} -> {end.isoformat()}; status {new_status}.')
    booking.refresh_from_db()
    return booking


@transaction.atomic
def return_rental(pk, user, values):
    booking = locked_booking(pk)
    check_version(booking, values['expected_updated_at'])
    if booking.status != 'confirmed':
        raise ValidationError('Only a confirmed rental can be returned.')
    if booking.start_date > timezone.now():
        raise ValidationError('This rental has not started yet. Cancel it instead of recording a return.')
    state, _ = RentalState.objects.get_or_create(booking=booking)
    state.returned_at, state.returned_by = timezone.now(), user
    state.deposit_returned = values.get('deposit_returned', state.deposit_returned)
    state.notes = values.get('notes', state.notes)
    state.save()
    Booking.objects.filter(pk=booking.pk).update(status='completed', updated_at=timezone.now())
    ReminderDelivery.objects.filter(booking=booking, state__in=['pending', 'failed']).update(state='cancelled')
    audit(user, booking, 'rental_returned', f'Bike returned for rental #{booking.pk}. Payment and deposit are recorded separately.')
    booking.refresh_from_db()
    return booking


@transaction.atomic
def mark_fully_paid(pk, user, expected=None):
    booking = locked_booking(pk)
    if expected:
        check_version(booking, expected)
    if booking.status == 'cancelled':
        raise ValidationError('A cancelled rental cannot be marked paid.')
    received = max(amount_paid(booking), booking.total_price or Decimal('0'))
    payment, _ = Payment.objects.get_or_create(booking=booking, defaults={
        'amount': received, 'payment_method': 'cash_on_delivery', 'status': 'pending'})
    Payment.objects.filter(pk=payment.pk).update(amount=received, status='completed', updated_at=timezone.now())
    Booking.objects.filter(pk=booking.pk).update(payment_status='paid', updated_at=timezone.now())
    RentalContract.objects.filter(booking=booking).update(advance_amount=received, balance_amount=Decimal('0'))
    audit(user, booking, 'mark_paid', f'Full payment recorded for rental #{booking.pk}.')
    booking.refresh_from_db()
    return booking


def whatsapp_draft(booking):
    raw = reformat_phone(booking.user.phone_number or '')
    if not raw:
        raise ValidationError({'phone': 'Add a valid international customer phone number first.'})
    due = timezone.localtime(booking.end_date, NEPAL).strftime('%d %b %Y at %I:%M %p')
    label = 'was due' if booking.end_date <= timezone.now() else 'is due'
    message = (f'Hello {booking.user.first_name or "there"}, this is EasyMoto. Your {booking.bike.name} '
               f'(rental #{booking.pk}) {label} for return on {due} Nepal time. '
               'Please return it to our Budhanilkantha-03 shop opposite Park Village Resort, '
               'or contact us to discuss an extension. Thank you! +977 9851401903')
    return {'url': f'https://wa.me/{raw}?' + urlencode({'text': message}), 'message': message}


def reformat_phone(value):
    import re
    digits = re.sub(r'[\s()+-]', '', str(value))
    if digits.startswith('00'):
        digits = digits[2:]
    if len(digits) == 10 and digits.startswith(('97', '98')):
        digits = '977' + digits
    return digits if digits.isdigit() and 8 <= len(digits) <= 15 else None


def customer_for_phone(phone):
    from django.contrib.auth import get_user_model
    digits = reformat_phone(phone)
    variants = {str(phone)}
    if digits:
        variants.update({digits, '+' + digits})
        if digits.startswith('977') and len(digits) == 13:
            variants.add(digits[3:])
    return get_user_model().objects.filter(phone_number__in=variants).first()
