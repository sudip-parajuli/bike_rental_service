from django.contrib import admin
from .models import Testimonial

class TestimonialAdmin(admin.ModelAdmin):
    """
    Custom admin interface for Testimonial model.
    """
    list_display = ('user', 'rating', 'is_approved', 'is_featured', 'created_at')
    list_filter = ('is_approved', 'is_featured', 'rating', 'created_at')
    search_fields = ('user__username', 'content')
    ordering = ('-created_at',)
    list_editable = ('is_approved', 'is_featured')  # Allow inline editing
    fieldsets = (
        (None, {'fields': ('user', 'content', 'rating')}),
        ('Status', {'fields': ('is_approved', 'is_featured')}),
    )

admin.site.register(Testimonial, TestimonialAdmin)