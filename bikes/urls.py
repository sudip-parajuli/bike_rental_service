app_name = 'bikes'

from django.urls import path
from .views import BikeListView, BikeDetailView, BikeCreateView, BikeUpdateView, BikeDeleteView

urlpatterns = [
    path('', BikeListView.as_view(), name='bike-list'),
    path('<int:pk>/', BikeDetailView.as_view(), name='bike-detail'),
    path('create/', BikeCreateView.as_view(), name='bike-create'),
    path('<int:pk>/update/', BikeUpdateView.as_view(), name='bike-update'),
    path('<int:pk>/delete/', BikeDeleteView.as_view(), name='bike-delete'),
]