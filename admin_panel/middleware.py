from django.shortcuts import redirect
from django.urls import reverse
from django.contrib import messages

class AdminAccessMiddleware:
    """
    Middleware to restrict access to /admin-panel/ to staff and superusers only.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Check if the request is for the admin panel
        if request.path.startswith('/admin-panel/'):
            # Allow staff and superusers
            if not request.user.is_authenticated or not (request.user.is_staff or request.user.is_superuser):
                messages.error(request, "Access denied. You do not have permission to view the Admin Portal.")
                return redirect('home')
        
        response = self.get_response(request)
        return response
