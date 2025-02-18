from django.urls import path
from .views import (
    UserListView, UserDetailView, RegisterUserView, LoginView, LogoutView,
    OwnerProfileListView, OwnerProfileDetailView
)

urlpatterns = [
    path('', UserListView.as_view(), name='user-list'),
    path('users/<int:pk>/', UserDetailView.as_view(), name='user-detail'),
    path('register/', RegisterUserView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('owners/', OwnerProfileListView.as_view(), name='owner-list'),
    path('owners/<int:pk>/', OwnerProfileDetailView.as_view(), name='owner-detail'),
]
