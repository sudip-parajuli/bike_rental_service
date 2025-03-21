app_name = 'bookings'

from django.urls import path
from .views import BookingListView, BookingDetailView, BookingCreateView, BookingUpdateView, BookingDeleteView, \
    BookingPaymentSelectView, BookingApproveView, BookingRejectView, BookingCompleteView

urlpatterns = [
    path('', BookingListView.as_view(), name='booking-list'),
    path('<int:pk>/', BookingDetailView.as_view(), name='booking-detail'),
    path('create/', BookingCreateView.as_view(), name='booking-create'),
    path('<int:pk>/update/', BookingUpdateView.as_view(), name='booking-update'),
    path('<int:pk>/delete/', BookingDeleteView.as_view(), name='booking-delete'),
    path('<int:pk>/payment-select/', BookingPaymentSelectView.as_view(), name='booking-payment-select'),
    path('<int:pk>/approve/', BookingApproveView.as_view(), name='booking-approve'),
    path('<int:pk>/reject/', BookingRejectView.as_view(), name='booking-reject'),
    path('<int:pk>/complete/', BookingCompleteView.as_view(), name='booking-complete'),

]