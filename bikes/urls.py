from django.urls import path
from .views import BikeListView, BikeDetailView, BikeCreateView, BikeUpdateView, BikeDeleteView

urlpatterns = [
    path('bikes/', BikeListView.as_view(), name='bike-list'),
    path('bikes/<int:pk>/', BikeDetailView.as_view(), name='bike-detail'),
    path('bikes/create/', BikeCreateView.as_view(), name='bike-create'),
    path('bikes/<int:pk>/update/', BikeUpdateView.as_view(), name='bike-update'),
    path('bikes/<int:pk>/delete/', BikeDeleteView.as_view(), name='bike-delete'),
]