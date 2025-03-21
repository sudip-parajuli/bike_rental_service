from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from rest_framework import permissions

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
    path('api/bike/', include('bikes.urls', namespace='bikes-api')),  # API routing for bikes (JSON)
    path('api/booking/', include('bookings.urls', namespace='bookings-api')),  # API routing for bookings (JSON)
    path('api/testimonial/', include('testimonials.urls', namespace='testimonials-api')),  # API routing for testimonials (JSON)
    path('api/payment/', include('payment.urls', namespace='payments-api')),  # API routing for payments (JSON)
    path('api/user/', include('users.urls', namespace='users-api')),  # API routing for users (JSON)
    path('api/admin/', include('admin_panel.urls')),
    path('api-auth/', include('rest_framework.urls')),
    path('', TemplateView.as_view(template_name='home.html'), name='home'),
    path('bikes/', include('bikes.urls', namespace='bikes')),  # Template-based bikes (HTML)
    path('bookings/', include('bookings.urls', namespace='bookings')),  # Template-based bookings (HTML) - Ensure this is included
    path('testimonials/', include('testimonials.urls', namespace='testimonials')),  # Template-based testimonials (HTML)
    path('users/', include('users.urls', namespace='users')),  # Template-based users (HTML)

    # Swagger endpoints
    path('api/swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('api/redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
]

urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)