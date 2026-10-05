from django.shortcuts import render, redirect
from django.views import View
from django.http import JsonResponse
from django.utils import timezone
from django.db import DatabaseError
from django.db.models import Min
import logging

logger = logging.getLogger(__name__)


def storefront_context():
    from bikes.models import Bike
    from testimonials.models import Testimonial
    try:
        bikes = Bike.objects.filter(is_approved=True, availability_status=True)
        return {
            'featured_bikes': list(bikes.order_by('-is_featured', 'name', 'pk')[:3]),
            'starting_price': bikes.aggregate(price=Min('price_per_day'))['price'],
            'reviews': list(Testimonial.approved.select_related('user').order_by('-is_featured', '-created_at')[:3]),
        }
    except DatabaseError:
        logger.exception('Could not load storefront inventory')
        return {'inventory_unavailable': True}

class HomeView(View):
    """
    Custom home view that redirects authenticated users to dashboard
    and shows homepage to anonymous users.
    """
    def get(self, request):
        if request.user.is_authenticated:
            return redirect('users:dashboard')
        return render(request, 'home.html', storefront_context())

class PublicHomeView(View):
    """
    Always show homepage even if user is authenticated.
    Used only when clicking the logo.
    """
    def get(self, request):
        return render(request, 'home.html', storefront_context())


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
