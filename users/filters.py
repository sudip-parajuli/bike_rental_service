import django_filters
from users.models import User
from django.db.models import Q
from django.db import models

class UserFilter(django_filters.FilterSet):
    is_owner = django_filters.BooleanFilter(field_name="is_owner")
    phone_number = django_filters.CharFilter(field_name="phone_number", lookup_expr='icontains')
    full_name = django_filters.CharFilter(method='filter_full_name', label="Full Name (First + Last)")
    username = django_filters.CharFilter(field_name="username", lookup_expr='icontains')

    class Meta:
        model = User
        fields = ['is_owner', 'phone_number', 'username', 'full_name']

    def filter_full_name(self, queryset, _, value):
        """
        Custom filter to search by full name (first_name + last_name).
        Supports both partial matches and exact matches.
        """
        # Split the input value into first and last name
        parts = value.split()
        if len(parts) == 2:
            first_name, last_name = parts
            return queryset.filter(
                Q(first_name__icontains=first_name) & Q(last_name__icontains=last_name)
            )
        return queryset.filter(
            Q(first_name__icontains=value) | Q(last_name__icontains=value)
        )