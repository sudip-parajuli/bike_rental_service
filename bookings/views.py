from rest_framework import generics, permissions
from rest_framework.permissions import IsAuthenticated
from .models import Booking
from .serializers import BookingSerializer

class BookingListView(generics.ListAPIView):
    """List all bookings (Admins see all, users see their own)."""
    serializer_class = BookingSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:  # Admin can see all bookings
            return Booking.objects.all()
        return Booking.objects.filter(user=user)  # Users see their own bookings

class BookingCreateView(generics.CreateAPIView):
    """Create a new booking (Authenticated users only)."""
    serializer_class = BookingSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)  # Set the user making the booking

class BookingDetailView(generics.RetrieveAPIView):
    """Retrieve details of a single booking."""
    queryset = Booking.objects.all()
    serializer_class = BookingSerializer
    permission_classes = [IsAuthenticated]

class BookingUpdateView(generics.UpdateAPIView):
    """Update a booking (Only the owner or admin can update)."""
    serializer_class = BookingSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return Booking.objects.all()  # Admin can update any booking
        return Booking.objects.filter(user=user)  # Users can update only their own bookings

class BookingDeleteView(generics.DestroyAPIView):
    """Delete a booking (Only the owner or admin can delete)."""
    serializer_class = BookingSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return Booking.objects.all()  # Admin can delete any booking
        return Booking.objects.filter(user=user)  # Users can delete only their own bookings
