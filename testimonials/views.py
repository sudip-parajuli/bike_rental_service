from django.contrib import messages
from django.shortcuts import redirect, render
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics, permissions, status
from rest_framework.filters import SearchFilter
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response

from .models import Testimonial
from .serializers import TestimonialSerializer
from users.permissions import IsUserOrReadOnly

class TestimonialListView(generics.ListAPIView):
    """
    List all testimonials.

    * Requires: None (public access)
    * Returns: List of testimonial data (JSON for API, template for non-API)
    """
    serializer_class = TestimonialSerializer
    permission_classes = [permissions.AllowAny]  # Public access
    filter_backends = [DjangoFilterBackend, SearchFilter]
    search_fields = ['user__username', 'content']
    pagination_class = PageNumberPagination

    def get_queryset(self):
        return Testimonial.objects.all().order_by('-created_at')  # Use created_at for ordering

    def get(self, request, *args, **kwargs):
        if request.path.startswith('/api/') or 'application/json' in request.headers.get('Accept', ''):
            # Return JSON for API requests (e.g., /api/testimonial/)
            return super().get(request, *args, **kwargs)
        # Render template for non-API requests (e.g., /testimonial/)
        testimonials = self.get_queryset()
        return render(request, 'testimonials/testimonial_list.html', {'testimonials': testimonials})

class TestimonialDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update, or delete a specific testimonial.

    * Requires: Authentication (only user or admin can modify their own testimonial)
    * Returns: JSON testimonial data for API, renders template for non-API
    """
    serializer_class = TestimonialSerializer
    permission_classes = [IsUserOrReadOnly]
    pagination_class = PageNumberPagination

    def get_queryset(self):
        return Testimonial.objects.all()

    def get(self, request, *args, **kwargs):
        if request.path.startswith('/api/') or 'application/json' in request.headers.get('Accept', ''):
            # Return JSON for API requests (e.g., /api/testimonial/<pk>/)
            return super().get(request, *args, **kwargs)
        # Render template for non-API requests (e.g., /testimonial/<pk>/)
        testimonial = self.get_object()
        return render(request, 'testimonials/testimonial_detail.html', {'testimonial': testimonial})

class TestimonialCreateView(generics.CreateAPIView):
    """
    Create a new testimonial.

    * Requires: Authentication
    * Returns: JSON testimonial data for API, renders template for non-API
    """
    serializer_class = TestimonialSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def get(self, request, *args, **kwargs):
        if request.path.startswith('/api/') or 'application/json' in request.headers.get('Accept', ''):
            return Response({"detail": "Method not allowed for API"}, status=status.HTTP_405_METHOD_NOT_ALLOWED)
        # Render template for non-API GET requests (e.g., /testimonial/create/)
        return render(request, 'testimonials/testimonial_create.html')

class TestimonialUpdateView(generics.UpdateAPIView):
    """
    Update a specific testimonial.

    * Requires: Authentication (only user or admin can modify their own testimonial)
    * Returns: JSON testimonial data for API, renders template for non-API
    """
    serializer_class = TestimonialSerializer
    permission_classes = [IsUserOrReadOnly]

    def get_queryset(self):
        return Testimonial.objects.all()

    def get(self, request, *args, **kwargs):
        if request.path.startswith('/api/') or 'application/json' in request.headers.get('Accept', ''):
            # Return JSON for API requests (e.g., /api/testimonial/<pk>/update/)
            return super().get(request, *args, **kwargs)
        # Render template for non-API requests (e.g., /testimonial/<pk>/update/)
        testimonial = self.get_object()
        return render(request, 'testimonials/testimonial_update.html', {'testimonial': testimonial})

class TestimonialDeleteView(generics.DestroyAPIView):
    """
    Delete a specific testimonial.

    * Requires: Authentication (only user or admin can delete their own testimonial)
    * Returns: JSON success message for API, redirects for non-API
    """
    serializer_class = TestimonialSerializer
    permission_classes = [IsUserOrReadOnly]

    def get_queryset(self):
        return Testimonial.objects.all()

    def delete(self, request, *args, **kwargs):
        if request.path.startswith('/api/') or 'application/json' in request.headers.get('Accept', ''):
            # Return JSON for API requests (e.g., /api/testimonial/<pk>/delete/)
            return super().delete(request, *args, **kwargs)
        # Handle non-API DELETE (e.g., form submission to /testimonial/<pk>/delete/)
        instance = self.get_object()
        self.perform_destroy(instance)
        messages.success(request, "Testimonial deleted successfully.")
        return redirect('testimonials:testimonial-list')