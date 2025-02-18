import django_filters
from .models import Testimonial

class TestimonialFilter(django_filters.FilterSet):
    min_rating = django_filters.NumberFilter(field_name="rating", lookup_expr='gte')
    max_rating = django_filters.NumberFilter(field_name="rating", lookup_expr='lte')
    is_approved = django_filters.BooleanFilter(field_name="is_approved")
    is_featured = django_filters.BooleanFilter(field_name="is_featured")
    username = django_filters.CharFilter(field_name="user__username", lookup_expr='icontains')

    class Meta:
        model = Testimonial
        fields = ['min_rating', 'max_rating', 'is_approved', 'is_featured', 'username']