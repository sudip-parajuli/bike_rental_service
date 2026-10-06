from datetime import timedelta
from decimal import Decimal
from unittest.mock import patch
from django.test import TestCase, RequestFactory
from django.contrib.auth import get_user_model
from django.db import DatabaseError
from django.urls import reverse
from bikes.models import Bike
from bike_rental_service.views import PublicHomeView
from testimonials.models import Testimonial


class StorefrontTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = get_user_model().objects.create_user(username='rider', email='rider@example.com', phone_number='+9779800000000')
        cls.bike = Bike.objects.create(name='Honda Dio', type='scooter', host=cls.user, is_approved=True, is_featured=True, price_per_day=Decimal('1500'))
        Bike.objects.create(name='Private bike', type='motorcycle', host=cls.user, price_per_day=100)

    def test_home_renders_fleet_without_javascript(self):
        response = self.client.get(reverse('public-home'))
        self.assertContains(response, 'Honda Dio')
        self.assertContains(response, 'NPR 1500')
        self.assertContains(response, 'Browse bikes')
        self.assertNotContains(response, 'Private bike')
        self.assertNotContains(response, 'Customer stories')

    def test_only_approved_reviews_are_shown(self):
        Testimonial.objects.create(user=self.user, content='Approved review', rating=5, is_approved=True)
        Testimonial.objects.create(user=self.user, content='Unapproved review', rating=3)
        response = self.client.get(reverse('public-home'))
        self.assertContains(response, 'Approved review')
        self.assertNotContains(response, 'Unapproved review')

    def test_database_outage_preserves_contact(self):
        with patch('bikes.models.Bike.objects.filter', side_effect=DatabaseError('offline')):
            response = PublicHomeView.as_view()(RequestFactory().get('/'))
        self.assertContains(response, 'temporarily unavailable')
        self.assertContains(response, '9779851401903')

    def test_fleet_filters_and_pages_preserve_search(self):
        for n in range(7):
            Bike.objects.create(name=f'Tour scooter {n}', type='scooter', host=self.user, is_approved=True, price_per_day=1500)
        response = self.client.get(reverse('bikes:bike-list'), {'search': 'Tour', 'type': 'scooter'})
        self.assertContains(response, 'Page 1 of 2')
        self.assertContains(response, 'search=Tour')
        self.assertNotContains(response, 'Honda Dio')

    def test_public_api_omits_internal_identifiers(self):
        response = self.client.get(reverse('bikes:bike-detail', args=[self.bike.pk]), HTTP_ACCEPT='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertNotIn('chassis_no', response.json())
        self.assertNotIn('engine_no', response.json())
        self.assertNotIn('host', response.json())

    def test_partially_paid_booking_blocks_overlapping_dates(self):
        from bookings.models import Booking
        from bookings.serializers import BookingSerializer
        from django.utils import timezone
        start = timezone.now() + timedelta(days=2)
        end = start + timedelta(days=1)
        Booking.objects.create(user=self.user, bike=self.bike, start_date=start,
                               end_date=end, pickup_location='Budhanilkantha',
                               status='confirmed', payment_status='partial')
        serializer = BookingSerializer(data={
            'bike': self.bike.pk, 'start_date': start.isoformat(),
            'end_date': end.isoformat(), 'pickup_location': 'Budhanilkantha',
        })
        self.assertFalse(serializer.is_valid())
        self.assertIn('already booked', str(serializer.errors))

from django.test import SimpleTestCase


class StorageConfigurationTests(SimpleTestCase):
    def test_staticfiles_use_manifest_storage(self):
        from bike_rental_service.settings.base import STORAGES
        self.assertEqual(STORAGES['staticfiles']['BACKEND'], 'whitenoise.storage.CompressedManifestStaticFilesStorage')

    def test_cloudinary_image_url_uses_https(self):
        # Isolate the third-party package's global setting-change receivers.
        import subprocess
        import sys
        script = (
            f'import sys; sys.path = {sys.path!r}; '
            'from django.conf import settings; '
            "settings.configure(STORAGES={'default': {'BACKEND': 'cloudinary_storage.storage.MediaCloudinaryStorage'}}, "
            "CLOUDINARY_STORAGE={'CLOUD_NAME': 'easymoto-test', 'API_KEY': 'test', 'API_SECRET': 'test'}); "
            'from django.core.files.storage import storages; '
            "print(storages['default'].url('bikes/test-bike'))"
        )
        url = subprocess.check_output([sys.executable, '-c', script], text=True).strip()
        self.assertTrue(url.startswith('https://res.cloudinary.com/easymoto-test/'))

class ExternalImagesAndPublicInfoTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = get_user_model().objects.create_user(username='rider', email='rider@example.com', phone_number='+9779800000000')
        cls.bike = Bike.objects.create(name='Honda Dio', type='scooter', host=cls.user, is_approved=True, price_per_day=1500)
        Bike.objects.create(name='Private bike', type='motorcycle', host=cls.user, price_per_day=100)

    def test_admin_form_accepts_url_without_upload(self):
        from admin_panel.forms import AdminBikeForm
        from django.forms.models import model_to_dict
        data = model_to_dict(self.bike)
        data['image_url'] = 'https://images.example.org/ride.jpg'
        form = AdminBikeForm(data=data, instance=self.bike)
        self.assertFalse(form.fields['image'].required)
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.save().image_url, data['image_url'])

    def test_mobile_api_preserves_external_url(self):
        from mobile_api.serializers import BikeSerializer
        self.bike.image_url = 'https://images.example.org/ride.jpg'
        self.assertEqual(BikeSerializer(self.bike).data['image_url'], self.bike.image_url)

    def test_google_timeout_preserves_profile_fallback(self):
        import requests
        from django.test import override_settings
        with override_settings(GOOGLE_PLACES_API_KEY='test-private-key', GOOGLE_PLACE_ID='test-place'), patch('bike_rental_service.public_info.requests.get', side_effect=requests.Timeout):
            response = self.client.get(reverse('google-reviews'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {'available': False})

    def test_profile_only_mode_does_not_schedule_live_review_request(self):
        from django.test import override_settings
        with override_settings(GOOGLE_PLACES_API_KEY='', GOOGLE_PLACE_ID=''):
            response = self.client.get(reverse('public-home'))
        self.assertContains(response, 'https://share.google/iGOVRN5QGg3pxlHIp')
        self.assertNotContains(response, 'data-endpoint=')

    def test_external_image_has_priority_and_is_used_in_public_api(self):
        self.bike.image_url = 'https://images.example.org/ride.jpg'
        self.bike.save()
        self.assertEqual(self.bike.display_image_url, self.bike.image_url)
        response = self.client.get(reverse('bikes:bike-detail', args=[self.bike.pk]), HTTP_ACCEPT='application/json')
        self.assertEqual(response.json()['image'], self.bike.image_url)
        self.assertContains(self.client.get(reverse('public-home')), self.bike.image_url)

    def test_image_url_rejects_insecure_and_script_schemes(self):
        from django.core.exceptions import ValidationError
        field = Bike._meta.get_field('image_url')
        for url in ['http://images.example.org/bike.jpg', 'javascript:alert(1)']:
            with self.assertRaises(ValidationError):
                field.clean(url, self.bike)
        self.assertEqual(self.bike.display_image_url, '')

    def test_schema_matches_visible_document_and_price_information(self):
        import json
        import re
        response = self.client.get(reverse('public-home'))
        html = response.content.decode()
        data = json.loads(re.search(r'<script type="application/ld\+json">(.*?)</script>', html).group(1))
        self.assertEqual(data['@graph'][0]['address']['addressLocality'], 'Kathmandu')
        self.assertContains(response, 'International Driving Permit (IDP)')
        self.assertContains(response, 'NPR 5,000')
        self.assertContains(response, 'NPR 500')
        self.assertNotIn('aggregateRating', data['@graph'][0])

    def test_sitemap_excludes_unapproved_bikes(self):
        response = self.client.get(reverse('sitemap'))
        self.assertContains(response, reverse('bikes:bike-detail', args=[self.bike.pk]))
        self.assertNotContains(response, reverse('bikes:bike-detail', args=[Bike.objects.get(name='Private bike').pk]))

    def test_google_disabled_does_not_contact_upstream(self):
        from django.test import override_settings
        with override_settings(GOOGLE_PLACES_API_KEY='', GOOGLE_PLACE_ID=''), patch('bike_rental_service.public_info.requests.get') as get:
            response = self.client.get(reverse('google-reviews'))
        get.assert_not_called()
        self.assertEqual(response.json(), {'available': False})
        self.assertEqual(response['Cache-Control'], 'no-store')

    def test_google_reviews_keep_attribution_and_hide_key(self):
        from django.test import override_settings
        from unittest.mock import Mock
        upstream = Mock()
        upstream.json.return_value = {'rating': 4.9, 'userRatingCount': 18, 'googleMapsUri': 'https://maps.google.com/', 'reviews': [{'rating': 5, 'text': {'text': '<script>customer text</script>'}, 'authorAttribution': {'displayName': 'Rider', 'uri': 'https://maps.google.com/author'}, 'googleMapsUri': 'https://maps.google.com/review'}]}
        with override_settings(GOOGLE_PLACES_API_KEY='test-private-key', GOOGLE_PLACE_ID='test-place'), patch('bike_rental_service.public_info.requests.get', return_value=upstream):
            response = self.client.get(reverse('google-reviews'))
        self.assertEqual(response.json()['reviews'][0]['author'], 'Rider')
        self.assertNotContains(response, 'test-private-key')

class AvailabilityEnquiryTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = get_user_model().objects.create_user(username='enquiry-rider', phone_number='+9779800000001')
        cls.bike = Bike.objects.create(name='Honda Dio & City', type='scooter', host=cls.user, is_approved=True, price_per_day=1500)
        cls.private = Bike.objects.create(name='Unapproved', type='scooter', host=cls.user, price_per_day=1500)

    def dates(self):
        from bikes.availability import nepal_today
        start = nepal_today() + timedelta(days=2)
        return start.isoformat(), (start + timedelta(days=3)).isoformat()

    def test_no_javascript_enquiry_contains_selected_dates_and_vehicle(self):
        from urllib.parse import urlparse, parse_qs
        start, end = self.dates()
        response = self.client.get(reverse('availability'), {'bike': self.bike.pk, 'start': start, 'end': end})
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith('https://wa.me/9779851401903?'))
        message = parse_qs(urlparse(response.url).query)['text'][0]
        self.assertIn(self.bike.name, message)
        self.assertIn(f'Pickup: {start}', message)
        self.assertIn(f'Return: {end} by 7 PM (Nepal time).', message)
        form_page = self.client.get(reverse('availability'), {'bike': self.bike.pk})
        self.assertContains(form_page, 'Continue to WhatsApp')
        self.assertContains(form_page, 'noindex, nofollow')

    def test_enquiry_requires_dates_and_rejects_backwards_or_past_dates(self):
        from bikes.availability import nepal_today
        start, end = self.dates()
        for data in ({'start': start}, {'start': end, 'end': start}, {'start': (nepal_today()-timedelta(days=1)).isoformat(), 'end': end}, {'start': 'invalid', 'end': end}):
            response = self.client.get(reverse('availability'), {'bike': self.bike.pk, **data})
            self.assertIsNone(response.context['whatsapp_url'])
            self.assertTrue(response.context['form'].errors)

    def test_same_day_daily_rental_is_allowed(self):
        start, _ = self.dates()
        response = self.client.get(reverse('availability'), {'bike': self.bike.pk, 'start': start, 'end': start})
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith('https://wa.me/9779851401903?'))

    def test_unapproved_or_invalid_bike_cannot_be_enquired_about(self):
        for pk in [self.private.pk, 'not-a-number', '999999999999999999999999']:
            self.assertEqual(self.client.get(reverse('availability'), {'bike': pk}).status_code, 404)

    def test_fleet_links_to_date_selection_instead_of_undated_whatsapp_draft(self):
        response = self.client.get(reverse('public-home'))
        self.assertContains(response, 'fleet-carousel')
        self.assertContains(response, 'availability-trigger')
        self.assertContains(response, 'images/linkypot.png')
        self.assertNotContains(response, 'YOUR KATHMANDU STARTING POINT')
        self.assertNotContains(response, 'available%20for%20my%20dates')

    def test_nepal_date_is_used_even_when_server_date_is_previous_day(self):
        from datetime import datetime, timezone as dt_timezone
        from bikes.availability import nepal_today
        with patch('bikes.availability.timezone.now', return_value=datetime(2026, 10, 6, 20, tzinfo=dt_timezone.utc)):
            self.assertEqual(nepal_today().isoformat(), '2026-10-07')
