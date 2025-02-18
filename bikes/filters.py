import django_filters
from .models import Bike

class BikeFilter(django_filters.FilterSet):
    min_price = django_filters.NumberFilter(field_name="price_per_day", lookup_expr='gte')
    max_price = django_filters.NumberFilter(field_name="price_per_day", lookup_expr='lte')
    name = django_filters.CharFilter(field_name="name", lookup_expr='icontains')

    class Meta:
        model = Bike
        fields = ['min_price', 'max_price', 'name']