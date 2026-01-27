app_name = 'bikes'

from django.urls import path
from .views import (
    BikeListView, BikeDetailView, BikeCreateView, BikeUpdateView, BikeDeleteView,
    BikeRecommendationsView, SimilarBikesView
)

urlpatterns = [
    path('', BikeListView.as_view(), name='bike-list'),
    path('<int:pk>/', BikeDetailView.as_view(), name='bike-detail'),
    path('create/', BikeCreateView.as_view(), name='bike-create'),
    path('<int:pk>/update/', BikeUpdateView.as_view(), name='bike-update'),
    path('<int:pk>/delete/', BikeDeleteView.as_view(), name='bike-delete'),
    path('recommendations/', BikeRecommendationsView.as_view(), name='bike-recommendations'),
    path('<int:pk>/similar/', SimilarBikesView.as_view(), name='similar-bikes'),
]