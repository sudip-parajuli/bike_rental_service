from django.db import models
from django.contrib.auth import get_user_model
from rest_framework.exceptions import ValidationError

User = get_user_model()

class Testimonial(models.Model):
    # Fields
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='testimonials', help_text="User who submitted the testimonial.")
    content = models.TextField(max_length=500, help_text="Content of the testimonial.")
    rating = models.PositiveIntegerField(help_text="Rating given by the user (1–5 stars).")
    is_approved = models.BooleanField(default=False, help_text="Indicates whether the testimonial is approved by the admin.")
    is_featured = models.BooleanField(default=False, help_text="Indicates whether the testimonial is featured on the homepage.")
    created_at = models.DateTimeField(auto_now_add=True, help_text="Timestamp for when the testimonial was submitted.")
    updated_at = models.DateTimeField(auto_now=True, help_text="Timestamp for the last update.")

    def clean(self):
        """
        Validate that the rating is between 1 and 5.
        """
        if not (1 <= self.rating <= 5):
            raise ValidationError("Rating must be between 1 and 5.")

    def __str__(self):
        return f"Testimonial by {self.user.username} ({self.rating} stars)"

    def mark_as_approved(self):
        """
        Mark the testimonial as approved.
        """
        self.is_approved = True
        self.save()

    def mark_as_featured(self):
        """
        Mark the testimonial as featured.
        """
        self.is_featured = True
        self.save()