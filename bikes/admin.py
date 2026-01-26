from django.contrib import admin
from .models import Bike

class BikeAdmin(admin.ModelAdmin):
    """
    Custom admin interface for Bike model.
    """
    list_display = (
        'name', 'type', 'brand', 'vehicle_number', 'price_per_day', 'availability_status', 'is_approved', 'is_featured',
        'host', 'created_at'
    )
    list_filter = ('type', 'availability_status', 'is_approved', 'is_featured', 'created_at')
    search_fields = ('name', 'brand', 'vehicle_number', 'host__username')
    ordering = ('-created_at',)
    list_editable = ('availability_status', 'is_approved')  # Allow inline editing
    fieldsets = (
        (None, {
            'fields': ('name', 'type', 'brand', 'model_year', 'host')
        }),
        ('Vehicle Identification', {
            'fields': ('vehicle_number', 'color', 'chassis_no', 'engine_no')
        }),
        ('Details', {
            'fields': ('mileage', 'description', 'price_per_day', 'image', 'engine_type', 'displacement',
                       'max_power', 'torque', 'transmission', 'brakes', 'dimensions', 'fuel_capacity')
        }),
        ('Status', {
            'fields': ('availability_status', 'is_approved', 'is_featured')
        }),
        ('Metadata', {
            'fields': ('slug', 'created_at', 'updated_at', 'average_rating'),
            'classes': ('collapse',)  # Optional: collapsible section
        }),
    )
    readonly_fields = ('slug', 'created_at', 'updated_at', 'average_rating')  # Prevent editing auto fields

admin.site.register(Bike, BikeAdmin)