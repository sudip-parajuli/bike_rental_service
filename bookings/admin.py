from django.contrib import admin
from .models import Booking, Feedback

class BookingAdmin(admin.ModelAdmin):
    """
    Custom admin interface for Booking model.
    """
    list_display = ('id', 'user', 'bike', 'start_date', 'end_date', 'total_price', 'payment_status', 'status', 'payment_option', 'get_rental_duration')
    list_filter = ('status', 'payment_status', 'payment_option', 'created_at')
    search_fields = ('user__username', 'bike__name')
    ordering = ('-created_at',)
    fieldsets = (
        (None, {'fields': ('user', 'bike', 'start_date', 'end_date')}),
        ('Details', {'fields': ('pickup_location', 'payment_option', 'total_price')}),
        ('Status', {'fields': ('status', 'payment_status', 'is_active')}),
    )
    readonly_fields = ('total_price', 'created_at', 'updated_at')

    def get_rental_duration(self, obj):
        """Calculate and display the rental duration category based on the date range."""
        duration_days = (obj.end_date - obj.start_date).days + 1
        if duration_days >= 28:
            return 'Monthly'
        elif duration_days >= 21:
            return 'Weekly (21-27 days)'
        elif duration_days >= 14:
            return 'Weekly (14-20 days)'
        elif duration_days >= 7:
            return 'Weekly (7-13 days)'
        else:
            return 'Daily'
    get_rental_duration.short_description = 'Rental Duration'

class FeedbackAdmin(admin.ModelAdmin):
    """
    Custom admin interface for Feedback model.
    """
    list_display = ('booking', 'user', 'rating', 'created_at')
    list_filter = ('rating', 'created_at')
    search_fields = ('user__username', 'booking__id')
    ordering = ('-created_at',)

admin.site.register(Booking, BookingAdmin)
admin.site.register(Feedback, FeedbackAdmin)