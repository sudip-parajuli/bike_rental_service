from django.contrib import admin
from .models import RentalState, StaffActivityLog, StaffDevice, ReminderDelivery


@admin.register(RentalState)
class RentalStateAdmin(admin.ModelAdmin):
    list_display = ['booking', 'deposit_amount', 'deposit_returned', 'returned_at']
    readonly_fields = ['booking', 'returned_at', 'returned_by']

    def has_add_permission(self, request):
        return False


@admin.register(StaffActivityLog)
class StaffActivityAdmin(admin.ModelAdmin):
    list_display = ['staff_user', 'action', 'booking', 'timestamp']
    list_filter = ['action']
    readonly_fields = ['staff_user', 'action', 'description', 'booking', 'timestamp']

    def has_add_permission(self, request):
        return False


@admin.register(StaffDevice)
class StaffDeviceAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'platform', 'active', 'updated_at']
    exclude = ['token']
    readonly_fields = ['user', 'platform', 'updated_at']

    def has_add_permission(self, request):
        return False


@admin.register(ReminderDelivery)
class ReminderDeliveryAdmin(admin.ModelAdmin):
    list_display = ['booking', 'kind', 'channel', 'state', 'attempts', 'error_code', 'sent_at']
    list_filter = ['state', 'channel', 'kind']
    readonly_fields = [field.name for field in ReminderDelivery._meta.fields]

    def has_add_permission(self, request):
        return False
