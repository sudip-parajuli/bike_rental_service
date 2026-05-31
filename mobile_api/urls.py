from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .auth import AdminTokenObtainPairView
from .views import (
    AdminBikeListView,
    AdminBikeDetailView,
    WalkInCustomerCreateView,
    WalkInBookingCreateView,
    AdminBookingListView,
    AdminDashboardStatsView,
    MarkBookingPaidView,
    AdminMaintenanceCreateView,
    AdminBikeBookingHistoryView,
    UpcomingMaintenanceAlertsView,
    AdminCustomerListView,
    AdminBookingInvoiceView,
    AdminBookingContractPDFView,
    StaffActivityLogListView,
    MarkNotificationsReadView,
)

app_name = 'mobile_api'

urlpatterns = [
    # Authentication
    path('auth/login/', AdminTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # Dashboard Stats
    path('dashboard/', AdminDashboardStatsView.as_view(), name='dashboard_stats'),

    # Bike Inventory & Maintenance
    path('bikes/', AdminBikeListView.as_view(), name='bike_list'),
    path('bikes/<int:pk>/', AdminBikeDetailView.as_view(), name='bike_detail'),
    path('bikes/<int:pk>/maintenance/', AdminMaintenanceCreateView.as_view(), name='bike_maintenance_create'),
    path('bikes/<int:pk>/bookings/', AdminBikeBookingHistoryView.as_view(), name='bike_booking_history'),
    path('alerts/maintenance/', UpcomingMaintenanceAlertsView.as_view(), name='maintenance_alerts'),

    # Customers
    path('customers/', AdminCustomerListView.as_view(), name='customer_list'),
    path('customers/walk-in/', WalkInCustomerCreateView.as_view(), name='create_walkin_customer'),

    # Bookings
    path('bookings/', AdminBookingListView.as_view(), name='booking_list'),
    path('bookings/walk-in/', WalkInBookingCreateView.as_view(), name='create_walkin_booking'),
    path('bookings/<int:pk>/mark-paid/', MarkBookingPaidView.as_view(), name='mark_booking_paid'),
    path('bookings/<int:pk>/invoice/', AdminBookingInvoiceView.as_view(), name='booking_invoice_pdf'),
    path('bookings/<int:pk>/contract/', AdminBookingContractPDFView.as_view(), name='booking_contract_pdf'),

    # Staff Activity Logs (admin-only)
    path('staff-activity/', StaffActivityLogListView.as_view(), name='staff_activity_logs'),
    path('staff-activity/mark-read/', MarkNotificationsReadView.as_view(), name='mark_notifications_read'),
]
