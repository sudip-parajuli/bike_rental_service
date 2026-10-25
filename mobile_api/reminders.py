"""Small-shop reminder outbox: no WhatsApp API, no paid messaging dependency."""
from datetime import timedelta

import requests
from django.conf import settings
from django.core.mail import send_mail
from django.db.models import Q
from django.utils import timezone

from bookings.models import Booking
from .models import StaffDevice, ReminderDelivery
from .operations import NEPAL


def reminder_kind(booking, now):
    if booking.end_date <= now:
        return 'overdue'
    if booking.end_date <= now + timedelta(hours=3):
        return 'due_3h'
    return 'due_24h'


def push_headers():
    headers = {'Content-Type': 'application/json'}
    if settings.EXPO_ACCESS_TOKEN:
        headers['Authorization'] = f'Bearer {settings.EXPO_ACCESS_TOKEN}'
    return headers


def check_receipts():
    accepted = list(ReminderDelivery.objects.filter(state='accepted', channel='push').exclude(provider_ticket='')[:100])
    if not accepted:
        return
    try:
        response = requests.post('https://exp.host/--/api/v2/push/getReceipts',
            headers=push_headers(), json={'ids': [item.provider_ticket for item in accepted]}, timeout=(3, 10), allow_redirects=False)
        if response.status_code != 200:
            return
        receipts = response.json().get('data', {})
        for item in accepted:
            receipt = receipts.get(item.provider_ticket)
            if not receipt:
                continue
            if receipt.get('status') == 'ok':
                ReminderDelivery.objects.filter(pk=item.pk).update(state='sent', error_code='')
            else:
                error = receipt.get('details', {}).get('error', 'delivery_error')
                ReminderDelivery.objects.filter(pk=item.pk).update(state='failed', error_code=str(error)[:100])
                if error == 'DeviceNotRegistered' and item.device_id:
                    StaffDevice.objects.filter(pk=item.device_id).update(active=False)
    except (requests.RequestException, ValueError, AttributeError, TypeError):
        return


def send_delivery(item, now):
    # Atomic claim prevents overlapping schedulers from sending the same outbox row.
    claimed = ReminderDelivery.objects.filter(pk=item.pk, state__in=['pending', 'failed'], attempts__lt=3).filter(
        Q(attempted_at__isnull=True) | Q(attempted_at__lte=now - timedelta(minutes=30)))
    if not claimed.update(state='processing', attempted_at=now, attempts=item.attempts + 1):
        return 'skipped'
    booking = Booking.objects.select_related('bike', 'user').get(pk=item.booking_id)
    if not booking.is_active or booking.status != 'confirmed' or booking.end_date != item.due_at:
        ReminderDelivery.objects.filter(pk=item.pk).update(state='cancelled')
        return 'skipped'
    due = timezone.localtime(booking.end_date, NEPAL).strftime('%d %b %Y, %I:%M %p')
    try:
        if item.channel == 'email':
            # One-shot email: ambiguous SMTP failures are not automatically retried.
            count = send_mail('EasyMoto rental return reminder',
                f'Hello {booking.user.first_name or "there"},\n\nYour {booking.bike.name} rental #{booking.pk} '
                f'is due for return on {due} Nepal time. Please return it to Budhanilkantha-03, '
                'opposite Park Village Resort, or contact +977 9851401903 to discuss an extension.\n\nThank you, EasyMoto',
                settings.DEFAULT_FROM_EMAIL, [booking.user.email], fail_silently=False)
            if count != 1:
                raise RuntimeError('email_not_accepted')
            ReminderDelivery.objects.filter(pk=item.pk).update(state='sent', sent_at=now, error_code='')
            return 'sent'
        device = StaffDevice.objects.filter(pk=item.device_id, active=True, user__is_active=True).filter(
            Q(user__is_staff=True) | Q(user__is_superuser=True)).first()
        if not device:
            ReminderDelivery.objects.filter(pk=item.pk).update(state='cancelled')
            return 'skipped'
        response = requests.post('https://exp.host/--/api/v2/push/send', headers=push_headers(),
            json={'to': device.token, 'title': 'Rental overdue' if item.kind == 'overdue' else 'Rental return reminder',
                  'body': f'Rental #{booking.pk} return: {due} Nepal time. Open EasyMoto to review.',
                  'data': {'booking_id': booking.pk}, 'sound': 'default', 'channelId': 'rentals',
                  'priority': 'high', 'ttl': 900}, timeout=(3, 10), allow_redirects=False)
        if response.status_code == 200:
            ticket = response.json().get('data', {})
            if isinstance(ticket, list):
                ticket = ticket[0] if ticket else {}
            if ticket.get('status') == 'ok' and ticket.get('id'):
                ReminderDelivery.objects.filter(pk=item.pk).update(state='accepted', provider_ticket=ticket['id'], sent_at=now, error_code='')
                return 'accepted'
            code = ticket.get('details', {}).get('error', 'push_rejected')
            if code == 'DeviceNotRegistered':
                StaffDevice.objects.filter(pk=device.pk).update(active=False)
            ReminderDelivery.objects.filter(pk=item.pk).update(state='failed', error_code=str(code)[:100])
        else:
            ReminderDelivery.objects.filter(pk=item.pk).update(state='failed', error_code=f'push_http_{response.status_code}')
        return 'failed'
    except requests.ConnectTimeout:
        ReminderDelivery.objects.filter(pk=item.pk).update(state='failed', error_code='connection_timeout')
        return 'failed'
    except Exception:
        # An accepted message might have lost its response: do not duplicate it on retry.
        ReminderDelivery.objects.filter(pk=item.pk).update(state='uncertain', error_code='delivery_outcome_unknown')
        return 'uncertain'


def dispatch_reminders(dry_run=False):
    now = timezone.now()
    bookings = Booking.objects.filter(is_active=True, status='confirmed', end_date__lte=now + timedelta(hours=24))
    devices = list(StaffDevice.objects.filter(active=True, user__is_active=True).filter(Q(user__is_staff=True) | Q(user__is_superuser=True)))
    if dry_run:
        return {'eligible_rentals': bookings.count(), 'staff_devices': len(devices), 'dry_run': True}
    if not settings.RENTAL_REMINDERS_ENABLED:
        return {'disabled': True}
    check_receipts()
    ReminderDelivery.objects.filter(state='processing', attempted_at__lt=now - timedelta(minutes=5)).update(
        state='uncertain', error_code='worker_interrupted')
    counts = {'accepted': 0, 'sent': 0, 'failed': 0, 'uncertain': 0, 'skipped': 0}
    for booking in bookings.select_related('user').iterator(chunk_size=100):
        kind = reminder_kind(booking, now)
        recipients = [('push', str(device.pk), device) for device in devices]
        email = booking.user.email
        if settings.RENTAL_EMAIL_REMINDERS_ENABLED and email and not email.lower().endswith('@example.com'):
            recipients.append(('email', str(booking.user_id), None))
        for channel, recipient, device in recipients:
            item, _ = ReminderDelivery.objects.get_or_create(booking=booking, due_at=booking.end_date,
                kind=kind, channel=channel, recipient_key=recipient, defaults={'device': device})
            counts[send_delivery(item, now)] += 1
    return counts
