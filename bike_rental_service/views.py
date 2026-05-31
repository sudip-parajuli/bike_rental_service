from django.shortcuts import render, redirect
from django.views import View
from django.http import JsonResponse
from django.utils import timezone

class HomeView(View):
    """
    Custom home view that redirects authenticated users to dashboard
    and shows homepage to anonymous users.
    """
    def get(self, request):
        if request.user.is_authenticated:
            return redirect('users:dashboard')
        return render(request, 'home.html')

class PublicHomeView(View):
    """
    Always show homepage even if user is authenticated.
    Used only when clicking the logo.
    """
    def get(self, request):
        return render(request, 'home.html')


class PingView(View):
    """
    Health-check endpoint for cron jobs / uptime monitors.
    Always returns HTTP 200 with no redirects.
    Use this URL in cronjob.org: https://www.easymoto.com.np/ping/
    """
    def get(self, request):
        return JsonResponse({
            'status': 'ok',
            'time': timezone.now().isoformat(),
        })
