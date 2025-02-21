from payment.serializers import PaymentSerializer
from django.shortcuts import get_object_or_404
from rest_framework import generics, permissions, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.urls import reverse
from .models import Booking
from .serializers import BookingSerializer
from .filters import BookingFilter
from django_filters.rest_framework import DjangoFilterBackend


class BookingListView(generics.ListAPIView):
    """
    List all bookings (admins see all, users see their own).

    * Requires: Authentication
    * Returns: List of booking data
    """
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
    """
    Create a new booking.

    * Requires: Authentication, bike, start_date, end_date, pickup_location, rental_duration, payment_option
    * Returns: Booking data with optional payment redirect URL
    """
    serializer_class = BookingSerializer
    permission_classes = [IsAuthenticated]
    throttle_scope = 'bookings'

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            self.perform_create(serializer)
            booking = serializer.instance
            response_data = {
                "success": True,
                "data": serializer.data,
                "message": "Booking created successfully"
            }
            # Redirect to payment if online payment option is chosen
            if booking.payment_option in ['full_online', 'partial_online']:
                payment_data = {
                    "booking": booking.id,
                    "payment_method": "paypal"  # Default to PayPal
                }
                payment_serializer = PaymentSerializer(data=payment_data)
                if payment_serializer.is_valid():
                    payment = payment_serializer.save()
                    response_data["redirect_url"] = reverse('payment_process', kwargs={'payment_id': payment.id})
                    response_data["message"] += ". Redirecting to payment."
            return Response(response_data, status=status.HTTP_201_CREATED)
        return Response({"success": False, "errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

class BookingDetailView(generics.RetrieveAPIView):
    """
        Retrieve details of a specific booking.

        * Requires: Authentication
        * Returns: Booking data
    """
    queryset = Booking.objects.all()
    serializer_class = BookingSerializer
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        booking = get_object_or_404(Booking, id=kwargs["pk"])
        serializer = self.get_serializer(booking)
        return Response({"success": True, "data": serializer.data}, status=status.HTTP_200_OK)

class BookingUpdateView(generics.UpdateAPIView):
    """
    Update an existing booking.

    * Requires: Authentication (only owner or admin)
    * Returns: Updated booking data
    """
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
    """
    Delete a booking.

    * Requires: Authentication (only owner or admin)
    * Returns: Success message
    """
    serializer_class = BookingSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_class = BookingFilter

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return Booking.objects.all()  # Admin can delete any booking
        return Booking.objects.filter(user=user)  # Users can delete only their own bookings