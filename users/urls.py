from django.urls import path
from .views import (
    UserListView, UserDetailView, RegisterUserView, LoginView, LogoutView,
    OwnerProfileListView, OwnerProfileDetailView, DashboardView, ContactView,
    BikeOwnerRequestView, AdminBikeOwnerRequestListView, BikeOwnerDashboardView
)

app_name = 'users'

urlpatterns = [
    path('register/', RegisterUserView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('', UserListView.as_view(), name='user-list'),
    path('profile/', UserDetailView.as_view(), name='user-detail'),
    path('owners/', OwnerProfileListView.as_view(), name='owner-list'),
    path('owners/<int:pk>/', OwnerProfileDetailView.as_view(), name='owner-detail'),
    path('dashboard/', DashboardView.as_view(), name='dashboard'),
    path('dashboard/owner/', BikeOwnerDashboardView.as_view(), name='bike-owner-dashboard'),
    path('contact/', ContactView.as_view(), name='contact'),
    path('bike-owner-request/', BikeOwnerRequestView.as_view(), name='bike-owner-request'),
    path('admin/bike-owner-requests/', AdminBikeOwnerRequestListView.as_view(), name='admin-bike-owner-request-list'),
    path('admin/bike-owner-requests/<int:pk>/', AdminBikeOwnerRequestListView.as_view(), name='admin-bike-owner-request-detail'),
]