from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model

User = get_user_model()

class AdminAccessTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.admin_user = User.objects.create_superuser(
            username='admin', 
            email='admin@test.com', 
            password='password123'
        )
        self.normal_user = User.objects.create_user(
            username='user', 
            email='user@test.com', 
            password='password123'
        )

    def test_dashboard_access_denied_for_anonymous(self):
        response = self.client.get(reverse('admin_panel:dashboard'))
        # Should redirect to home with error message
        self.assertEqual(response.status_code, 302)
        self.assertIn('/', response.url)

    def test_dashboard_access_denied_for_normal_user(self):
        self.client.login(username='user', password='password123')
        response = self.client.get(reverse('admin_panel:dashboard'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/', response.url)

    def test_dashboard_access_allowed_for_admin(self):
        self.client.login(username='admin', password='password123')
        response = self.client.get(reverse('admin_panel:dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'admin_panel/dashboard.html')
