from rest_framework import generics, permissions
from .models import Testimonial
from .serializers import TestimonialSerializer

class TestimonialListView(generics.ListAPIView):
    """List all testimonials (Anyone can view)."""
    queryset = Testimonial.objects.all()
    serializer_class = TestimonialSerializer
    permission_classes = [permissions.AllowAny]  # Publicly accessible

class TestimonialCreateView(generics.CreateAPIView):
    """Create a new testimonial (Only authenticated users)."""
    serializer_class = TestimonialSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)  # Set the author of the testimonial

class TestimonialDetailView(generics.RetrieveAPIView):
    """Retrieve a single testimonial."""
    queryset = Testimonial.objects.all()
    serializer_class = TestimonialSerializer
    permission_classes = [permissions.AllowAny]  # Publicly accessible

class TestimonialUpdateView(generics.UpdateAPIView):
    """Update a testimonial (Only the author or an admin)."""
    serializer_class = TestimonialSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return Testimonial.objects.all()  # Admin can update any testimonial
        return Testimonial.objects.filter(user=user)  # Users can update only their own testimonials

class TestimonialDeleteView(generics.DestroyAPIView):
    """Delete a testimonial (Only the author or an admin)."""
    serializer_class = TestimonialSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return Testimonial.objects.all()  # Admin can delete any testimonial
        return Testimonial.objects.filter(user=user)  # Users can delete only their own testimonials
