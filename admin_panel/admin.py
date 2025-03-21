from django.contrib import admin
from django.core.mail import send_mail
from .models import ContactMessage

class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'contact_number', 'message_preview', 'created_at', 'has_reply')
    list_filter = ('created_at',)
    search_fields = ('name', 'email', 'contact_number', 'message')
    date_hierarchy = 'created_at'
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        (None, {
            'fields': ('name', 'email', 'contact_number', 'message')
        }),
        ('Admin Response', {
            'fields': ('reply',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def message_preview(self, obj):
        """Display a preview of the message in the list view."""
        return obj.message[:50] + ('...' if len(obj.message) > 50 else '')
    message_preview.short_description = 'Message Preview'

    def has_reply(self, obj):
        """Display whether the message has a reply."""
        return bool(obj.reply)
    has_reply.boolean = True
    has_reply.short_description = 'Replied'

    def save_model(self, request, obj, form, change):
        """
        Override save_model to send an email to the user when a reply is added.
        """
        if change:  # Only send email on update, not on creation
            original = ContactMessage.objects.get(pk=obj.pk)
            if 'reply' in form.changed_data and obj.reply and not original.reply:
                # Send email notification to the user
                send_mail(
                    'Response to Your Contact Message',
                    f'Dear {obj.name},\n\nWe have responded to your message:\n\n'
                    f'Your Message:\n{obj.message}\n\n'
                    f'Our Response:\n{obj.reply}\n\n'
                    f'Thank you for reaching out!\nEasyMoto Team',
                    'from@example.com',
                    [obj.email],
                    fail_silently=True,
                )
        super().save_model(request, obj, form, change)

admin.site.register(ContactMessage, ContactMessageAdmin)