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
