from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics, permissions
from rest_framework.filters import SearchFilter

from .filters import TestimonialFilter
from .models import Testimonial
from .serializers import TestimonialSerializer

class TestimonialListView(generics.ListAPIView):
    """
    List all testimonials.

    * Requires: None (public access)
    * Returns: List of testimonial data
    """
    queryset = Testimonial.objects.all()
    serializer_class = TestimonialSerializer
    permission_classes = [permissions.AllowAny]

class TestimonialCreateView(generics.CreateAPIView):
    """
    Create a new testimonial.

    * Requires: Authentication
    * Returns: Newly created testimonial data
    """
    serializer_class = TestimonialSerializer
    permission_classes = [permissions.IsAuthenticated]
    throttle_scope = 'testimonials'  # Scoped to 5/hour

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)  # Set the author of the testimonial

class TestimonialDetailView(generics.RetrieveAPIView):
    """
        Retrieve details of a specific testimonial.

        * Requires: None (public access)
        * Returns: Testimonial data
    """
    queryset = Testimonial.objects.all()
    serializer_class = TestimonialSerializer
    permission_classes = [permissions.AllowAny]

class TestimonialUpdateView(generics.UpdateAPIView):
    """
    Update an existing testimonial.

    * Requires: Authentication (only author or admin)
    * Returns: Updated testimonial data
    """
    serializer_class = TestimonialSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return Testimonial.objects.all()  # Admin can update any testimonial
        return Testimonial.objects.filter(user=user)  # Users can update only their own testimonials

class TestimonialDeleteView(generics.DestroyAPIView):
    """
    Delete a testimonial.

    * Requires: Authentication (only author or admin)
    * Returns: Success message
    """
    serializer_class = TestimonialSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_class = TestimonialFilter
    search_fields = ['content', 'user__username']

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return Testimonial.objects.all()  # Admin can delete any testimonial
        return Testimonial.objects.filter(user=user)  # Users can delete only their own testimonials