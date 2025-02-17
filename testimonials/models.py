from django.db import models
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, MaxValueValidator

User = get_user_model()

class ApprovedTestimonialManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(is_approved=True)

class Testimonial(models.Model):
    # Fields
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='testimonials',
        help_text="User who submitted the testimonial."
    )
    content = models.TextField(
        max_length=500,
        help_text="Content of the testimonial."
    )
    rating = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="Rating given by the user (1–5 stars)."
    )
    is_approved = models.BooleanField(
        default=False,
        db_index=True,
        help_text="Indicates whether the testimonial is approved by the admin."
    )
    is_featured = models.BooleanField(
        default=False,
        db_index=True,
        help_text="Indicates whether the testimonial is featured on the homepage."
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="Timestamp for when the testimonial was submitted."
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="Timestamp for the last update."
    )

    # Managers
    objects = models.Manager()  # Default manager
    approved = ApprovedTestimonialManager()  # Custom manager for approved testimonials

    def clean(self):
        """
        Validate that the rating is between 1 and 5.
        Raises:
            ValidationError: If the rating is not within the valid range.
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
        self.save(update_fields=['is_approved'])

    def mark_as_featured(self):
        """
        Mark the testimonial as featured.
        """
        self.is_featured = True
        self.save(update_fields=['is_featured'])

    def is_approved_status(self):
        """
        Check if the testimonial is approved.
        Returns:
            bool: True if approved, False otherwise.
        """
        return self.is_approved