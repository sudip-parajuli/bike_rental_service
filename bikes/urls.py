    path('create/', BikeCreateView.as_view(), name='bike-create'),
    path('<int:pk>/update/', BikeUpdateView.as_view(), name='bike-update'),
    path('<int:pk>/delete/', BikeDeleteView.as_view(), name='bike-delete'),
    path('recommendations/', BikeRecommendationsView.as_view(), name='bike-recommendations'),
    path('<int:pk>/similar/', SimilarBikesView.as_view(), name='similar-bikes'),
]