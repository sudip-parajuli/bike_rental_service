from django.shortcuts import redirect
from django.urls import reverse
from django.conf import settings

class MobileNumberRequiredMiddleware:
    """
    Middleware to ensure authenticated users have a phone number.
    Redirects to 'add-phone-number' if phone number is missing.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated and not request.user.phone_number:
            # List of paths to exclude from redirection to avoid infinite loops
            # or blocking essential functionality (like logout or admin)
            exempt_paths = [
                reverse('users:add-phone-number'),
                reverse('users:logout'),
                '/admin/', # Allow admin access even if admin user has no phone (optional, but safer)
                '/static/',
                '/media/',
            ]
            
            # Check if current path starts with any exempt path
            if not any(request.path.startswith(path) for path in exempt_paths):
                return redirect('users:add-phone-number')

        response = self.get_response(request)
        return response
