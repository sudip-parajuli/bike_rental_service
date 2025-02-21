"""
URL configuration for bike_rental_service project.
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
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
    path('api/bikes/', include('bikes.urls')),  # Updated for clarity
    path('api/bookings/', include('bookings.urls')),
    path('api/testimonials/', include('testimonials.urls')),
    path('api/payments/', include('payment.urls')),
    path('api/users/', include('users.urls')),
    path('api/admin/', include('admin_panel.urls')),
    path('api-auth/', include('rest_framework.urls')),
    # Swagger endpoints
    path('api/swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('api/redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)