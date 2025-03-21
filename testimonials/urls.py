app_name = 'testimonials'

from django.urls import path
from .views import TestimonialListView, TestimonialDetailView, TestimonialCreateView, TestimonialUpdateView, TestimonialDeleteView

urlpatterns = [
    path('', TestimonialListView.as_view(), name='testimonial-list'),
    path('<int:pk>/', TestimonialDetailView.as_view(), name='testimonial-detail'),
    path('create/', TestimonialCreateView.as_view(), name='testimonial-create'),
    path('<int:pk>/update/', TestimonialUpdateView.as_view(), name='testimonial-update'),
    path('<int:pk>/delete/', TestimonialDeleteView.as_view(), name='testimonial-delete'),
]