from django.urls import path
from .views import (
    BookingListView, BookingCreateView, BookingDetailView,
    BookingUpdateView, BookingDeleteView
)

urlpatterns = [
    path('bookings/', BookingListView.as_view(), name='booking-list'),
    path('create/', BookingCreateView.as_view(), name='booking-create'),
    path('<int:pk>/', BookingDetailView.as_view(), name='booking-detail'),
    path('<int:pk>/update/', BookingUpdateView.as_view(), name='booking-update'),
    path('<int:pk>/delete/', BookingDeleteView.as_view(), name='booking-delete'),
]
