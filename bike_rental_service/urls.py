from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView, RedirectView
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from rest_framework import permissions
from .views import HomeView, PublicHomeView, PingView
from users.views import RegisterView

# Configure Swagger schema
schema_view = get_schema_view(
    openapi.Info(
        title="Bike Rental Service API",
        default_version='v1',
        description="API documentation for the Bike Rental Service",
        terms_of_service="https://www.example.com/terms/",
        contact=openapi.Contact(email="support@bikerental.com"),
        license=openapi.License(name="MIT License"),
    ),
    public=True,  # Allow public access to the schema
    permission_classes=(permissions.AllowAny,),  # Anyone can view the docs
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('ping/', PingView.as_view(), name='ping'),  # Health check for cron jobs / uptime monitors
    path('api/bike/', include('bikes.urls', namespace='bikes-api')),  # API routing for bikes (JSON)
    path('api/booking/', include('bookings.urls', namespace='bookings-api')),  # API routing for bookings (JSON)
    path('api/testimonial/', include('testimonials.urls', namespace='testimonials-api')),  # API routing for testimonials (JSON)
    path('api/payment/', include('payment.urls', namespace='payments-api')),  # API routing for payments (JSON)
    path('api/user/', include('users.urls', namespace='users-api')),  # API routing for users (JSON)
    path('api/mobile/', include('mobile_api.urls', namespace='mobile_api')), # Admin mobile app endpoints
    path('api/chatbot/', include('chatbot.urls')),  # API routing for chatbot
    path('api-auth/', include('rest_framework.urls')),
    path('admin-panel/', include('admin_panel.urls', namespace='admin_panel')),
    path('', HomeView.as_view(), name='home'),
    path('public-home/', PublicHomeView.as_view(), name='public-home'),
    path('bikes/', include('bikes.urls', namespace='bikes')),  # Template-based bikes (HTML)
    path('bookings/', include('bookings.urls', namespace='bookings')),  # Template-based bookings (HTML) - Ensure this is included
    path('testimonials/', include('testimonials.urls', namespace='testimonials')),  # Template-based testimonials (HTML)
    path('users/', include('users.urls', namespace='users')),  # Template-based users (HTML)
    path('register/', RegisterView.as_view(), name='register'),


    # Authentication
    path('accounts/', include('allauth.urls')),
    path('api/auth/', include('dj_rest_auth.urls')),
    path('api/auth/registration/', include('dj_rest_auth.registration.urls')),
    path('api/auth/', include('allauth.socialaccount.providers.google.urls')),

    # Swagger endpoints
    path('api/swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('api/redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
]

from django.views.static import serve
from django.urls import re_path

urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# Serve media files in production (Workaround for Render without S3/Cloudinary)
urlpatterns += [
    re_path(r'^media/(?P<path>.*)$', serve, {'document_root': settings.MEDIA_ROOT}),
]