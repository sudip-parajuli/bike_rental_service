from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse, path
from django.shortcuts import get_object_or_404, render
from .models import User, OwnerProfile, BikeOwnerRequest

class UserAdmin(admin.ModelAdmin):
    """
    Custom admin interface for User model.
    """
    list_display = ('username', 'email', 'is_owner', 'phone_number', 'created_at', 'is_active')
    list_filter = ('is_owner', 'is_staff', 'is_active', 'created_at')
    search_fields = ('username', 'email', 'phone_number')
    ordering = ('-created_at',)
    fieldsets = (
        (None, {'fields': ('username', 'email', 'password')}),
        ('Personal Info', {'fields': ('first_name', 'last_name', 'phone_number', 'address', 'profile_picture', 'date_of_birth', 'bio')}),
        ('Permissions', {'fields': ('is_owner', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Status', {'fields': ('is_active', 'last_login', 'date_joined')}),
    )
    readonly_fields = ('last_login', 'date_joined', 'created_at', 'updated_at')

class OwnerProfileAdmin(admin.ModelAdmin):
    """
    Custom admin interface for OwnerProfile model.
    """
    list_display = ('user', 'total_bookings', 'total_earnings', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('user__username', 'user__email')
    ordering = ('-created_at',)

class BikeOwnerRequestAdmin(admin.ModelAdmin):
    """
    Custom admin interface for BikeOwnerRequest model.
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
            reverse('admin:bike_owner_request_documents', args=[obj.pk])
        )
    view_documents.short_description = "Documents"

    def get_urls(self):
        # Add a custom URL for the documents view
        urls = super().get_urls()
        custom_urls = [
            path(
                '<int:pk>/documents/',
                self.admin_site.admin_view(self.view_documents_page),
                name='bike_owner_request_documents'
            ),
        ]
        return custom_urls + urls

    def view_documents_page(self, request, pk):
        # View to render the documents template
        bike_owner_request = get_object_or_404(BikeOwnerRequest, pk=pk)
        print(f"Registration Certificate URL: {bike_owner_request.registration_certificate.url}")
        print(f"Insurance Certificate URL: {bike_owner_request.insurance_certificate.url}")
        print(f"ID Proof URL: {bike_owner_request.id_proof.url}")
        print(f"Bike Photos URL: {bike_owner_request.bike_photos.url}")
        context = {
            'title': f"Bike Owner Request Documents - {bike_owner_request.user.username}",
            'bike_owner_request': bike_owner_request,
        }
       
        return render(request, 'users/admin/bike_owner_request_documents.html', context)

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
admin.site.register(OwnerProfile, OwnerProfileAdmin)
admin.site.register(BikeOwnerRequest, BikeOwnerRequestAdmin)