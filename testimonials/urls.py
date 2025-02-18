from django.urls import path
from .views import (
    TestimonialListView, TestimonialCreateView, TestimonialDetailView,
    TestimonialUpdateView, TestimonialDeleteView
)

urlpatterns = [
    path('', TestimonialListView.as_view(), name='testimonial-list'),
    path('testimonials/create/', TestimonialCreateView.as_view(), name='testimonial-create'),
    path('testimonials/<int:pk>/', TestimonialDetailView.as_view(), name='testimonial-detail'),
    path('testimonials/<int:pk>/update/', TestimonialUpdateView.as_view(), name='testimonial-update'),
    path('testimonials/<int:pk>/delete/', TestimonialDeleteView.as_view(), name='testimonial-delete'),
]
