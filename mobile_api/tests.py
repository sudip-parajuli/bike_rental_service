from datetime import datetime, timedelta, timezone as dt_timezone
from decimal import Decimal
from unittest.mock import Mock, patch

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from bikes.models import Bike
from bookings.models import Booking
from payment.models import Payment
from .models import RentalState, StaffActivityLog, StaffDevice, ReminderDelivery
from .operations import due_state, quote, reformat_phone
from .reminders import dispatch_reminders

User = get_user_model()


class RentalOperationsTests(TestCase):
    def setUp(self):
        cache.clear()
        self.staff = User.objects.create_user(username='rental-staff', is_staff=True)
        self.owner = User.objects.create_user(username='rental-owner', is_superuser=True, is_staff=False)
        self.customer = User.objects.create_user(username='rental-customer', phone_number='+9779800000012', email='rider@example.com')
        self.bike = Bike.objects.create(name='City scooter', type='scooter', price_per_day=1000, host=self.owner, is_approved=True)
        self.now = timezone.now()
        self.booking = Booking.objects.create(user=self.customer, bike=self.bike, start_date=self.now - timedelta(days=1), end_date=self.now + timedelta(hours=2), status='confirmed', total_price=2000)
        self.client = APIClient()
        self.client.force_authenticate(self.staff)

    def url(self, name):
        return reverse('mobile_api:' + name, kwargs={'pk': self.booking.pk})

    def version(self):
        self.booking.refresh_from_db()
        return self.booking.updated_at.isoformat()

    def change(self, **data):
        return self.client.patch(self.url('rental_detail'), {'expected_updated_at': self.version(), **data}, format='json')

    def test_staff_and_owner_access_and_customer_denial(self):
        for user, code in [(None, 401), (self.customer, 403), (self.owner, 200), (self.staff, 200)]:
            self.client.force_authenticate(user)
            self.assertEqual(self.client.get(self.url('rental_detail')).status_code, code)

    def test_extension_is_audited_and_keeps_price_unless_repricing_requested(self):
        end = self.booking.end_date + timedelta(days=2)
        response = self.change(end_date=end.isoformat(), notes='Agreed by phone')
        self.assertEqual(response.status_code, 200, response.data)
        self.booking.refresh_from_db()
        self.assertEqual(self.booking.end_date, end)
        self.assertEqual(self.booking.total_price, Decimal('2000'))
        self.assertEqual(self.booking.rental_state.notes, 'Agreed by phone')
        self.assertTrue(StaffActivityLog.objects.filter(action='dates_updated', staff_user=self.staff).exists())

    def test_stale_changes_cannot_overwrite_another_staff_member(self):
        version = self.version()
        self.assertEqual(self.change(notes='First change').status_code, 200)
        response = self.client.patch(self.url('rental_detail'), {'expected_updated_at': version, 'notes': 'Overwrite'}, format='json')
        self.assertEqual(response.status_code, 409)
        self.assertEqual(RentalState.objects.get(booking=self.booking).notes, 'First change')

    def test_reversed_dates_and_overlap_with_unpaid_confirmed_rental_are_rejected(self):
        self.assertEqual(self.change(end_date=self.booking.start_date.isoformat()).status_code, 400)
        Booking.objects.create(user=self.customer, bike=self.bike, start_date=self.booking.end_date + timedelta(hours=1), end_date=self.booking.end_date + timedelta(days=3), status='confirmed', payment_status='unpaid')
        self.assertEqual(self.change(end_date=(self.booking.end_date + timedelta(days=2)).isoformat()).status_code, 400)

    def test_repricing_keeps_actual_payment_and_updates_remaining_balance(self):
        Payment.objects.create(booking=self.booking, amount=2000, payment_method='cash_on_delivery', status='completed')
        response = self.change(end_date=(self.booking.end_date + timedelta(days=3)).isoformat(), recalculate_price=True)
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(Decimal(response.data['paid_amount']), Decimal('2000'))
        self.assertGreater(Decimal(response.data['balance_due']), 0)
        self.assertEqual(response.data['payment_status'], 'partial')

    def test_repricing_legacy_paid_booking_preserves_cash_without_payment_row(self):
        Booking.objects.filter(pk=self.booking.pk).update(payment_status='paid')
        response = self.change(end_date=(self.booking.end_date + timedelta(days=3)).isoformat(), recalculate_price=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Decimal(response.data['paid_amount']), Decimal('2000'))

    def test_overdue_rental_stays_on_rent_until_physical_return(self):
        self.booking.end_date = self.now - timedelta(minutes=1); self.booking.save()
        self.assertEqual(due_state(self.booking), 'overdue')
        board = self.client.get(reverse('mobile_api:rental_board')).data
        self.assertEqual(board['overdue'], 1)
        self.assertEqual(board['on_rent'], 1)
        self.assertEqual(board['alerts'][0]['id'], self.booking.pk)

    def test_return_keeps_balance_and_deposit_can_be_recorded_later(self):
        response = self.client.post(self.url('rental_return'), {'expected_updated_at': self.version(), 'deposit_returned': False}, format='json')
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(response.data['status'], 'completed')
        self.assertGreater(Decimal(response.data['balance_due']), 0)
        self.assertIsNotNone(response.data['operations']['returned_at'])
        self.assertFalse(response.data['operations']['deposit_returned'])
        self.assertEqual(self.change(deposit_returned=True).status_code, 200)
        self.assertTrue(RentalState.objects.get(booking=self.booking).deposit_returned)

    def test_returned_dates_locked_and_payment_does_not_reopen_returned_rental(self):
        self.client.post(self.url('rental_return'), {'expected_updated_at': self.version()}, format='json')
        self.assertEqual(self.change(end_date=(self.now + timedelta(days=3)).isoformat()).status_code, 400)
        response = self.client.post(self.url('mark_booking_paid'), {'expected_updated_at': self.version()}, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['status'], 'completed')
        self.assertEqual(Decimal(response.data['balance_due']), 0)
        self.assertEqual(Payment.objects.get(booking=self.booking).amount, Decimal('2000'))

    def test_active_rental_cannot_be_cancelled_to_hide_outstanding_return(self):
        self.assertEqual(self.change(status='cancelled').status_code, 400)
        self.assertEqual(self.change(status='pending').status_code, 400)

    def test_payment_requires_current_version_and_preserves_overpayment(self):
        self.assertEqual(self.client.post(self.url('mark_booking_paid'), {}, format='json').status_code, 400)
        Payment.objects.create(booking=self.booking, amount=2500, payment_method='cash_on_delivery', status='completed')
        response = self.client.post(self.url('mark_booking_paid'), {'expected_updated_at': self.version()}, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Decimal(response.data['paid_amount']), Decimal('2500'))

    def test_notes_keep_pending_reminder_but_extension_cancels_old_due_snapshot(self):
        item = ReminderDelivery.objects.create(booking=self.booking, due_at=self.booking.end_date, kind='due_3h', channel='email', recipient_key=str(self.customer.pk))
        self.assertEqual(self.change(notes='Keep this reminder').status_code, 200)
        item.refresh_from_db(); self.assertEqual(item.state, 'pending')
        self.assertEqual(self.change(end_date=(self.booking.end_date + timedelta(days=1)).isoformat()).status_code, 200)
        item.refresh_from_db(); self.assertEqual(item.state, 'cancelled')

    def test_device_unregister_cannot_change_another_staff_members_phone(self):
        device = StaffDevice.objects.create(user=self.owner, token='ExpoPushToken[fixture-device-token]', platform='ios')
        response = self.client.delete(reverse('mobile_api:rental_devices'), {'token': device.token}, format='json')
        self.assertEqual(response.status_code, 204)
        device.refresh_from_db(); self.assertTrue(device.active)

    def test_whatsapp_has_customer_number_exact_due_time_and_no_false_delivery_record(self):
        response = self.client.post(self.url('rental_whatsapp'), {}, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data['url'].startswith('https://wa.me/9779800000012?'))
        self.assertIn('Nepal time', response.data['message'])
        self.assertIn(f'rental #{self.booking.pk}', response.data['message'])
        self.assertFalse(ReminderDelivery.objects.exists())
        self.assertIn('delivery is not verified', StaffActivityLog.objects.latest('pk').description)

    def test_nepal_business_day_is_not_server_utc_date(self):
        now = datetime(2026, 10, 25, 20, tzinfo=dt_timezone.utc)
        self.booking.start_date = now - timedelta(days=1)
        self.booking.end_date = datetime(2026, 10, 26, 13, 15, tzinfo=dt_timezone.utc)
        self.booking.save()
        with patch('mobile_api.rental_views.timezone.now', return_value=now):
            response = self.client.get(reverse('mobile_api:rental_board'))
        self.assertEqual(response.data['due_today'], 1)

    def test_inclusive_calendar_day_pricing_and_zero_agreed_total(self):
        start = datetime(2026, 10, 25, 9, tzinfo=dt_timezone.utc)
        end = datetime(2026, 10, 26, 8, tzinfo=dt_timezone.utc)
        self.assertEqual(quote(self.bike, start, end)['days'], 2)
        self.booking.total_price = Decimal('0'); self.booking.save(); self.booking.refresh_from_db()
        self.assertEqual(self.booking.total_price, Decimal('0'))

    def test_conflicting_walkin_is_atomic_and_negative_money_is_rejected(self):
        data = {'phone_number': self.customer.phone_number, 'bike_id': self.bike.pk, 'start_date': self.now.isoformat(), 'end_date': (self.now + timedelta(hours=1)).isoformat(), 'driving_license_no': 'fixture-licence'}
        self.assertEqual(self.client.post(reverse('mobile_api:create_walkin_booking'), data, format='json').status_code, 400)
        self.assertEqual(Booking.objects.count(), 1)
        self.assertFalse(RentalState.objects.exists())
        data['manual_discount'] = '-1'
        self.assertEqual(self.client.post(reverse('mobile_api:create_walkin_booking'), data, format='json').status_code, 400)

    def test_walkin_contract_invoice_and_deposit_separate_from_income(self):
        self.booking.status = 'completed'; self.booking.save()
        response = self.client.post(reverse('mobile_api:create_walkin_booking'), {'phone_number': '9800000012', 'bike_id': self.bike.pk, 'start_date': self.now.isoformat(), 'end_date': (self.now + timedelta(hours=2)).isoformat(), 'driving_license_no': 'fixture-licence', 'deposit_amount': '5000', 'advance_amount': '100'}, format='json')
        self.assertEqual(response.status_code, 201, response.data)
        booking = Booking.objects.get(pk=response.data['booking_id'])
        self.assertEqual(booking.payment.amount, Decimal('100'))
        self.assertEqual(booking.rental_state.deposit_amount, Decimal('5000'))
        self.assertTrue(booking.contract)
        self.assertTrue(booking.invoice)

    def test_customer_phone_alias_does_not_duplicate_or_email_password(self):
        response = self.client.post(reverse('mobile_api:create_walkin_customer'), {'phone_number': '9800000012', 'full_name': 'Existing rider'}, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['user_id'], self.customer.pk)
        response = self.client.post(reverse('mobile_api:create_walkin_customer'), {'phone_number': '9800000099', 'full_name': 'New rider'}, format='json')
        self.assertEqual(response.status_code, 201)
        self.assertFalse(User.objects.get(pk=response.data['user_id']).has_usable_password())

    def test_pdf_rejects_credentials_in_url(self):
        token = str(RefreshToken.for_user(self.staff).access_token)
        self.assertEqual(APIClient().get(self.url('booking_invoice_pdf') + '?token=' + token).status_code, 401)

    def test_payment_save_does_not_reopen_returned_booking(self):
        self.booking.status = 'completed'; self.booking.save()
        Payment.objects.create(booking=self.booking, amount=100, payment_method='cash_on_delivery', status='partial')
        self.booking.refresh_from_db(); self.assertEqual(self.booking.status, 'completed')


class StaffAuthenticationTests(TestCase):
    def setUp(self):
        cache.clear()
        self.client = APIClient()
        self.staff = User.objects.create_user(username='desk', email='desk@example.com', is_staff=True)
        self.staff.set_password('fake-staff-login-password'); self.staff.save()

    def test_email_login_refresh_rotation_and_logout(self):
        login = self.client.post(reverse('mobile_api:token_obtain_pair'), {'login': 'DESK@example.com', 'password': 'fake-staff-login-password'}, format='json')
        self.assertEqual(login.status_code, 200, login.data)
        refreshed = self.client.post(reverse('mobile_api:token_refresh'), {'refresh': login.data['refresh']}, format='json')
        self.assertEqual(refreshed.status_code, 200)
        self.assertEqual(self.client.post(reverse('mobile_api:token_refresh'), {'refresh': login.data['refresh']}, format='json').status_code, 401)
        self.client.post(reverse('mobile_api:staff_logout'), {'refresh': refreshed.data['refresh']}, format='json')
        self.assertEqual(self.client.post(reverse('mobile_api:token_refresh'), {'refresh': refreshed.data['refresh']}, format='json').status_code, 401)

    def test_removed_staff_privilege_cannot_be_refreshed(self):
        token = str(RefreshToken.for_user(self.staff))
        self.staff.is_staff = False; self.staff.save()
        self.assertEqual(self.client.post(reverse('mobile_api:token_refresh'), {'refresh': token}, format='json').status_code, 403)


@override_settings(RENTAL_REMINDERS_ENABLED=True, RENTAL_EMAIL_REMINDERS_ENABLED=False)
class ReminderTests(TestCase):
    def setUp(self):
        self.staff = User.objects.create_user(username='reminder-staff', is_staff=True)
        customer = User.objects.create_user(username='reminder-customer', email='rider@example.com')
        bike = Bike.objects.create(host=self.staff, name='Reminder scooter', type='scooter', price_per_day=1000, is_approved=True)
        self.booking = Booking.objects.create(user=customer, bike=bike, start_date=timezone.now() - timedelta(hours=2), end_date=timezone.now() + timedelta(hours=2), status='confirmed')
        self.device = StaffDevice.objects.create(user=self.staff, platform='android', token='ExpoPushToken[fixture-device-token]')

    @patch('mobile_api.reminders.requests.post')
    def test_idempotency_receipts_and_no_customer_data_on_lock_screen(self, post):
        def response(url, **kwargs):
            body = {'data': {'ticket-fixture': {'status': 'ok'}}} if url.endswith('getReceipts') else {'data': {'status': 'ok', 'id': 'ticket-fixture'}}
            return Mock(status_code=200, json=Mock(return_value=body))
        post.side_effect = response
        self.assertEqual(dispatch_reminders()['accepted'], 1)
        self.assertEqual(dispatch_reminders()['accepted'], 0)
        self.assertEqual(ReminderDelivery.objects.get().state, 'sent')
        self.assertEqual(sum(call.args[0].endswith('/send') for call in post.call_args_list), 1)
        self.assertNotIn('reminder-customer', post.call_args_list[0].kwargs['json']['body'])

    @patch('mobile_api.reminders.requests.post')
    def test_dry_run_and_returned_rental_do_not_send(self, post):
        self.assertTrue(dispatch_reminders(dry_run=True)['dry_run'])
        self.assertFalse(ReminderDelivery.objects.exists())
        self.booking.status = 'completed'; self.booking.save(); dispatch_reminders()
        post.assert_not_called()

    @patch('mobile_api.reminders.requests.post')
    def test_old_due_snapshot_is_cancelled(self, post):
        from .reminders import send_delivery
        item = ReminderDelivery.objects.create(booking=self.booking, due_at=self.booking.end_date - timedelta(days=1), kind='overdue', channel='push', recipient_key=str(self.device.pk), device=self.device)
        self.assertEqual(send_delivery(item, timezone.now()), 'skipped')
        item.refresh_from_db(); self.assertEqual(item.state, 'cancelled'); post.assert_not_called()

    @patch('mobile_api.reminders.requests.post')
    def test_unknown_delivery_outcome_does_not_send_twice(self, post):
        import requests
        post.side_effect = requests.ReadTimeout('fixture timeout')
        dispatch_reminders(); dispatch_reminders()
        self.assertEqual(post.call_count, 1)
        self.assertEqual(ReminderDelivery.objects.get().state, 'uncertain')

    @patch('mobile_api.reminders.requests.post')
    def test_invalid_device_is_disabled(self, post):
        post.return_value = Mock(status_code=200, json=Mock(return_value={'data': {'status': 'error', 'details': {'error': 'DeviceNotRegistered'}}}))
        dispatch_reminders(); self.device.refresh_from_db(); self.assertFalse(self.device.active)

    @override_settings(RENTAL_CRON_SECRET='fake-cron-secret-at-least-thirty-two-characters')
    @patch('mobile_api.reminders.dispatch_reminders', return_value={'accepted': 0})
    def test_scheduler_authentication(self, dispatch):
        client = APIClient(); url = reverse('mobile_api:rental_reminders_run')
        self.assertEqual(client.post(url, {}, format='json').status_code, 403)
        dispatch.assert_not_called()
        self.assertEqual(client.post(url, {}, format='json', HTTP_X_RENTAL_CRON_SECRET='fake-cron-secret-at-least-thirty-two-characters').status_code, 200)

    def test_phone_normalization(self):
        self.assertEqual(reformat_phone('9800000000'), '9779800000000')
        self.assertEqual(reformat_phone('+44 7700 900123'), '447700900123')
        self.assertIsNone(reformat_phone('not-a-number'))

    @override_settings(RENTAL_EMAIL_REMINDERS_ENABLED=True, EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
    def test_automatic_email_reminder_is_sent_once_without_live_provider(self):
        from django.core import mail
        self.booking.user.email = 'rider@example.test'; self.booking.user.save()
        self.device.active = False; self.device.save()
        self.assertEqual(dispatch_reminders()['sent'], 1)
        self.assertEqual(dispatch_reminders()['sent'], 0)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('Nepal time', mail.outbox[0].body)

    @override_settings(RENTAL_REMINDERS_ENABLED=False)
    @patch('mobile_api.reminders.requests.post')
    def test_disabled_reminders_do_not_send_anything(self, post):
        self.assertTrue(dispatch_reminders()['disabled'])
        post.assert_not_called()
