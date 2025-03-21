from django.contrib import admin
from .models import Payment

class PaymentAdmin(admin.ModelAdmin):
    """
    Custom admin interface for Payment model.
    """
    list_display = ('id', 'booking', 'amount', 'payment_method', 'status', 'transaction_id', 'created_at')
    list_filter = ('payment_method', 'status', 'created_at')
    search_fields = ('booking__id', 'transaction_id')
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'updated_at')

admin.site.register(Payment, PaymentAdmin)