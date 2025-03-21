import django_filters
from .models import Bike

class BikeFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(lookup_expr='icontains')
    brand = django_filters.CharFilter(lookup_expr='icontains')
    type = django_filters.CharFilter(lookup_expr='icontains')
    availability_status = django_filters.BooleanFilter()

    class Meta:
        model = Bike
        fields = ['name', 'brand', 'type', 'availability_status']