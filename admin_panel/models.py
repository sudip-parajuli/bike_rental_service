from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class ContactMessage(models.Model):
    name = models.CharField(max_length=100, help_text="Name of the person submitting the message.")
    email = models.EmailField(help_text="Email address of the person submitting the message.")
    contact_number = models.CharField(max_length=15, help_text="Contact number of the person submitting the message.")
    message = models.TextField(max_length=1000, help_text="The message submitted via the contact form.")
    reply = models.TextField(max_length=1000, blank=True, null=True, help_text="Admin's reply to the message.")
    created_at = models.DateTimeField(auto_now_add=True, help_text="Timestamp for when the message was submitted.")
    updated_at = models.DateTimeField(auto_now=True, help_text="Timestamp for the last update.")

    def __str__(self):
        return f"Message from {self.name} ({self.email})"