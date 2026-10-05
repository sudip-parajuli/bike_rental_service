from datetime import timedelta
from decimal import Decimal
import base64
import hashlib
import hmac
import json
from types import SimpleNamespace
from django.test import TestCase, RequestFactory, override_settings
from django.contrib.auth import get_user_model
from django.utils import timezone
from bikes.models import Bike
from bookings.models import Booking
from payment.models import Payment
from payment.views import payment_done, esewa_payment_success, handle_ipn, esewa_payment_process


@override_settings(ESEWA_SECRET_KEY='test-secret', ESEWA_PRODUCT_CODE='EPAYTEST', PAYPAL_RECEIVER_EMAIL='merchant@example.com', PAYPAL_TEST=True)
class PaymentVerificationTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username='payer', phone_number='+9779800000001')
        self.bike = Bike.objects.create(name='Test scooter', type='scooter', host=self.user, price_per_day=1350)
        self.booking = Booking.objects.create(user=self.user, bike=self.bike, start_date=timezone.now()+timedelta(days=1), end_date=timezone.now()+timedelta(days=2), pickup_location='Budhanilkantha', total_price=1350)
        self.payment = Payment.objects.create(booking=self.booking, amount=1350, payment_method='esewa', transaction_uuid='txn-1-test')
        self.factory = RequestFactory()

    def callback(self, signed=True, amount='1350.00'):
        payload = {'status':'COMPLETED', 'total_amount':amount, 'transaction_uuid':self.payment.transaction_uuid, 'product_code':'EPAYTEST', 'transaction_code':'gateway-code'}
        if signed:
            fields = ','.join(payload)
            payload['signed_field_names'] = fields
            message = ','.join(f'{key}={payload[key]}' for key in fields.split(','))
            payload['signature'] = base64.b64encode(hmac.new(b'test-secret', message.encode(), hashlib.sha256).digest()).decode()
        data = base64.b64encode(json.dumps(payload).encode()).decode()
        return esewa_payment_success(self.factory.get('/', {'booking_id':self.booking.pk, 'data':data}))

    def test_unsigned_esewa_callback_cannot_confirm_payment(self):
        self.callback(signed=False)
        self.payment.refresh_from_db()
        self.assertEqual(self.payment.status, 'pending')

    def test_signed_wrong_amount_cannot_confirm_payment(self):
        self.callback(amount='1.00')
        self.payment.refresh_from_db()
        self.assertEqual(self.payment.status, 'pending')

    def test_valid_esewa_callback_uses_payment_status_choices(self):
        self.callback()
        self.booking.refresh_from_db()
        self.assertEqual(self.booking.payment_status, 'paid')
        self.assertEqual(self.booking.status, 'confirmed')

    def test_browser_paypal_return_does_not_confirm_payment(self):
        self.payment.payment_method = 'paypal'
        self.payment.save()
        request = self.factory.get('/', {'booking_id':self.booking.pk, 'PayerID':'forged', 'paymentId':'forged'})
        request.session = {}
        payment_done(request)
        self.payment.refresh_from_db()
        self.assertEqual(self.payment.status, 'pending')

    def test_paypal_ipn_rejects_wrong_amount(self):
        self.payment.payment_method = 'paypal'
        self.payment.save()
        handle_ipn(SimpleNamespace(custom=str(self.booking.pk), invoice='', txn_id='test-id', payment_status='Completed', mc_currency='USD', mc_gross='0.01', receiver_email='merchant@example.com', test_ipn=True))
        self.payment.refresh_from_db()
        self.assertEqual(self.payment.status, 'pending')

    def test_paypal_ipn_accepts_verified_matching_details(self):
        self.payment.payment_method = 'paypal'
        self.payment.save()
        handle_ipn(SimpleNamespace(custom=str(self.booking.pk), invoice='', txn_id='test-id', payment_status='Completed', mc_currency='USD', mc_gross='10.00', receiver_email='merchant@example.com', test_ipn=True))
        self.payment.refresh_from_db()
        self.assertEqual(self.payment.status, 'completed')

    def test_url_amount_cannot_change_gateway_charge(self):
        request = self.factory.get('/')
        request.user = self.user
        response = esewa_payment_process(request, self.booking.pk, '1.00')
        self.assertContains(response, '1350.00')

    def test_cancellation_cannot_downgrade_completed_payment(self):
        self.payment.mark_as_completed(transaction_id='verified')
        self.payment.mark_as_failed()
        self.payment.refresh_from_db()
        self.assertEqual(self.payment.status, 'completed')

    def test_gateway_rejects_another_customers_booking(self):
        from django.http import Http404
        other = get_user_model().objects.create_user(username='other', phone_number='+9779800000002')
        request = self.factory.get('/')
        request.user = other
        with self.assertRaises(Http404):
            esewa_payment_process(request, self.booking.pk, '1350.00')

    def test_payment_api_hides_another_customers_payment(self):
        from django.urls import reverse
        other = get_user_model().objects.create_user(username='other', phone_number='+9779800000002')
        self.client.force_login(other)
        response = self.client.get(reverse('payment:payment-list'), HTTP_ACCEPT='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['count'], 0)
