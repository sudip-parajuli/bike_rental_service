import django_filters
from .models import Booking

class BookingFilter(django_filters.FilterSet):
    start_date = django_filters.DateFilter(field_name="start_date", lookup_expr='gte')
    end_date = django_filters.DateFilter(field_name="end_date", lookup_expr='lte')

    class Meta:
        model = Booking
        fields = ['start_date', 'end_date']