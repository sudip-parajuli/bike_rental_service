from django.urls import path
from .views import (
    UserListView, UserDetailView, LoginView, LogoutView, RegisterView,
    hostProfileListView, hostProfileDetailView, DashboardView, ContactView,
    BikehostRequestView, AdminBikehostRequestListView, BikehostDashboardView,
    AddPhoneNumberView
)

app_name = 'users'

urlpatterns = [
    path('login/', LoginView.as_view(), name='login'),
    path('register/', RegisterView.as_view(), name='register'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('', UserListView.as_view(), name='user-list'),
    path('profile/', UserDetailView.as_view(), name='user-detail'),
    path('hosts/', hostProfileListView.as_view(), name='host-list'),
    path('hosts/<int:pk>/', hostProfileDetailView.as_view(), name='host-detail'),
    path('dashboard/', DashboardView.as_view(), name='dashboard'),
    path('dashboard/host/', BikehostDashboardView.as_view(), name='bike-host-dashboard'),
    path('contact/', ContactView.as_view(), name='contact'),
    path('add-phone-number/', AddPhoneNumberView.as_view(), name='add-phone-number'),
    path('bike-host-request/', BikehostRequestView.as_view(), name='bike-host-request'),
    path('admin/bike-host-requests/', AdminBikehostRequestListView.as_view(), name='admin-bike-host-request-list'),
    path('admin/bike-host-requests/<int:pk>/', AdminBikehostRequestListView.as_view(), name='admin-bike-host-request-detail'),
]