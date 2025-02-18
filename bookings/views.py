from django.shortcuts import get_object_or_404
from rest_framework import generics, permissions, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Booking
from .serializers import BookingSerializer
from .filters import BookingFilter
from django_filters.rest_framework import DjangoFilterBackend


class BookingListView(generics.ListAPIView):
    """List all bookings (Admins see all, users see their own)."""
    serializer_class = BookingSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_class = BookingFilter

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

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            self.perform_create(serializer)
            return Response(
                {"success": True, "data": serializer.data, "message": "Booking created successfully"},
                status=status.HTTP_201_CREATED
            )
        return Response(
            {"success": False, "errors": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST
        )

class BookingDetailView(generics.RetrieveAPIView):
    """Retrieve details of a single booking."""
    queryset = Booking.objects.all()
    serializer_class = BookingSerializer
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        booking = get_object_or_404(Booking, id=kwargs["pk"])
        serializer = self.get_serializer(booking)
        return Response({"success": True, "data": serializer.data}, status=status.HTTP_200_OK)

class BookingUpdateView(generics.UpdateAPIView):
    """Update a booking (Only the owner or admin can update)."""
    serializer_class = BookingSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return Booking.objects.all()  # Admin can update any booking
        return Booking.objects.filter(user=user)  # Users can update only their own bookings

    def update(self, request, *args, **kwargs):
        try:
            return super().update(request, *args, **kwargs)
        except Exception as e:
            return Response(
                {"success": False, "message": "Failed to update booking", "details": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

class BookingDeleteView(generics.DestroyAPIView):
    """Delete a booking (Only the owner or admin can delete)."""
    serializer_class = BookingSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_class = BookingFilter

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return Booking.objects.all()  # Admin can delete any booking
        return Booking.objects.filter(user=user)  # Users can delete only their own bookings
