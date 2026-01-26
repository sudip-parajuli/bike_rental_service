from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    ContactMessageViewSet, AdminDashboardHomeView, AdminUserListView,
    AdminBikeListView, AdminBookingListView, AdminPaymentListView,
    AdminTestimonialListView, toggle_user_status, approve_bike,
    reject_bike, toggle_testimonial, generate_invoice_pdf,
    AdminUserUpdateView, AdminUserDeleteView, AdminUserDetailView,
    AdminBikeCreateView, AdminBikeUpdateView, AdminBikeDeleteView,
    AdminBookingUpdateView, AdminBookingDeleteView,
    AdminContractCreateView, AdminContractUpdateView, AdminContractPrintView,
    AdminContractListView, AdminWalkInBookingView, AdminUserLookupView
)

app_name = 'admin_panel'

router = DefaultRouter()
router.register(r'contact-messages', ContactMessageViewSet, basename='contactmessage')

urlpatterns = [
    # Template-based Admin Panel
    path('', AdminDashboardHomeView.as_view(), name='dashboard'),
    
    # User Management
    path('users/', AdminUserListView.as_view(), name='user-list'),
    path('users/<int:pk>/', AdminUserDetailView.as_view(), name='user-detail'),
    path('users/<int:pk>/edit/', AdminUserUpdateView.as_view(), name='user-update'),
    path('users/<int:pk>/delete/', AdminUserDeleteView.as_view(), name='user-delete'),
    
    # Bike Management
    path('bikes/', AdminBikeListView.as_view(), name='bike-list'),
    path('bikes/add/', AdminBikeCreateView.as_view(), name='bike-create'),
    path('bikes/<int:pk>/edit/', AdminBikeUpdateView.as_view(), name='bike-update'),
    path('bikes/<int:pk>/delete/', AdminBikeDeleteView.as_view(), name='bike-delete'),
    
    # Booking Management
    path('bookings/', AdminBookingListView.as_view(), name='booking-list'),
    path('bookings/<int:pk>/edit/', AdminBookingUpdateView.as_view(), name='booking-update'),
    path('bookings/<int:pk>/delete/', AdminBookingDeleteView.as_view(), name='booking-delete'),
    
    path('payments/', AdminPaymentListView.as_view(), name='payment-list'),
    path('testimonials/', AdminTestimonialListView.as_view(), name='testimonial-list'),
    
    # Actions
    path('users/<int:pk>/toggle/', toggle_user_status, name='toggle-user-status'),
    path('bikes/<int:pk>/approve/', approve_bike, name='approve-bike'),
    path('bikes/<int:pk>/reject/', reject_bike, name='reject-bike'),
    path('testimonials/<int:pk>/toggle/', toggle_testimonial, name='toggle-testimonial-status'),
    path('bookings/<int:booking_id>/invoice/', generate_invoice_pdf, name='generate-invoice'),
    
    # Rental Contracts
    path('contract/create/', AdminContractCreateView.as_view(), name='contract-create'),
    path('contract/<int:pk>/edit/', AdminContractUpdateView.as_view(), name='contract-update'),
    path('contract/<int:pk>/print/', AdminContractPrintView.as_view(), name='contract-print'),
    path('invoices/', AdminContractListView.as_view(), name='contract-list'),
    path('walkin/create/', AdminWalkInBookingView.as_view(), name='walkin-create'),
    path('api/user-lookup/', AdminUserLookupView.as_view(), name='user-lookup'),
    
    # API endpoints
    path('api/', include(router.urls)),
]