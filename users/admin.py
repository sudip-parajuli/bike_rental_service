from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse, path
from django.shortcuts import get_object_or_404, render
from .models import User, hostProfile, BikehostRequest

class UserAdmin(admin.ModelAdmin):
    """
    Custom admin interface for User model.
    """
    list_display = ('username', 'email', 'is_host', 'phone_number', 'created_at', 'is_active')
    list_filter = ('is_host', 'is_staff', 'is_active', 'created_at')
    search_fields = ('username', 'email', 'phone_number')
    ordering = ('-created_at',)
    fieldsets = (
        (None, {'fields': ('username', 'email', 'password')}),
        ('Personal Info', {'fields': ('first_name', 'last_name', 'phone_number', 'address', 'profile_picture', 'date_of_birth', 'bio')}),
        ('Permissions', {'fields': ('is_host', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Status', {'fields': ('is_active', 'last_login', 'date_joined')}),
    )
    readonly_fields = ('last_login', 'date_joined', 'created_at', 'updated_at')

class hostProfileAdmin(admin.ModelAdmin):
    """
    Custom admin interface for hostProfile model.
    """
    list_display = ('user', 'total_bookings', 'total_earnings', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('user__username', 'user__email')
    ordering = ('-created_at',)

class BikehostRequestAdmin(admin.ModelAdmin):
    """
    Custom admin interface for BikehostRequest model.
    """
    list_display = (
        'user', 'bike_make', 'bike_model', 'status', 'requested_at',
        'view_documents'  # Single link to view all documents
    )
    list_filter = ('status', 'requested_at')
    search_fields = ('user__username', 'bike_make', 'bike_model', 'bike_registration_number')
    ordering = ('-requested_at',)
    actions = ['approve_selected', 'reject_selected']
    fieldsets = (
        (None, {'fields': ('user', 'status', 'admin_notes')}),
        ('Bike Details', {'fields': ('bike_make', 'bike_model', 'bike_year', 'bike_registration_number')}),
        ('Documents', {
            'fields': (
                'registration_certificate', 'insurance_certificate',
                'id_proof', 'bike_photos'
            )
        }),
        ('Timestamps', {'fields': ('requested_at',)}),
    )
    readonly_fields = ('requested_at',)

    def view_documents(self, obj):
        # Link to the custom view that displays all documents
        return format_html(
            '<a href="{}">View Documents</a>',
            reverse('admin:bike_host_request_documents', args=[obj.pk])
        )
    view_documents.short_description = "Documents"

    def get_urls(self):
        # Add a custom URL for the documents view
        urls = super().get_urls()
        custom_urls = [
            path(
                '<int:pk>/documents/',
                self.admin_site.admin_view(self.view_documents_page),
                name='bike_host_request_documents'
            ),
        ]
        return custom_urls + urls

    def view_documents_page(self, request, pk):
        # View to render the documents template
        bike_host_request = get_object_or_404(BikehostRequest, pk=pk)
        print(f"Registration Certificate URL: {bike_host_request.registration_certificate.url}")
        print(f"Insurance Certificate URL: {bike_host_request.insurance_certificate.url}")
        print(f"ID Proof URL: {bike_host_request.id_proof.url}")
        print(f"Bike Photos URL: {bike_host_request.bike_photos.url}")
        context = {
            'title': f"Bike host Request Documents - {bike_host_request.user.username}",
            'bike_host_request': bike_host_request,
        }
       
        return render(request, 'users/admin/bike_host_request_documents.html', context)

    def approve_selected(self, request, queryset):
        for request_instance in queryset:
            if request_instance.status == 'pending':
                request_instance.approve()
        self.message_user(request, f"{queryset.count()} request(s) approved.")

    def reject_selected(self, request, queryset):
        notes = request.POST.get('admin_notes', 'No reason provided')
        for request_instance in queryset:
            if request_instance.status == 'pending':
                request_instance.reject(notes)
        self.message_user(request, f"{queryset.count()} request(s) rejected.")

    approve_selected.short_description = "Approve selected requests"
    reject_selected.short_description = "Reject selected requests"

admin.site.register(User, UserAdmin)
admin.site.register(hostProfile, hostProfileAdmin)
admin.site.register(BikehostRequest, BikehostRequestAdmin)