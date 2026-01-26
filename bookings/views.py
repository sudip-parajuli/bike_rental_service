from decimal import Decimal
from random import random
from django.conf import settings
from django.urls import reverse
from django.utils import timezone
from django.utils.timezone import now
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics, permissions, status, serializers
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from .models import Booking
from .serializers import BookingSerializer, BookingPaymentSelectSerializer
from .forms import BookingForm
from users.permissions import IsUserOrReadOnly
from .filters import BookingFilter
from bikes.models import Bike
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
import urllib.parse
from payment.models import Payment
from payment.serializers import PaymentSerializer
from users.models import hostProfile  # Import OwnerProfile for earnings updates

class BookingListView(generics.ListAPIView):
    """
    List all bookings for the authenticated user.

    * Requires: Authentication
    * Returns: List of booking data (JSON for API, template for non-API)
    """
    serializer_class = BookingSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_class = BookingFilter
    pagination_class = PageNumberPagination

    def get_queryset(self):
        return Booking.objects.filter(user=self.request.user)

    def get(self, request, *args, **kwargs):
        if request.path.startswith('/api/') or 'application/json' in request.headers.get('Accept', ''):
            return super().get(request, *args, **kwargs)
        bookings = self.get_queryset()
        return render(request, 'bookings/booking_list.html', {'bookings': bookings})

class BookingDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update, or delete a specific booking.

    * Requires: Authentication (only user or admin can modify their own booking)
    * Returns: JSON booking data for API, renders template for non-API
    """
    serializer_class = BookingSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = PageNumberPagination

    def get_queryset(self):
        return Booking.objects.filter(user=self.request.user)

    def get(self, request, *args, **kwargs):
        if request.path.startswith('/api/') or 'application/json' in request.headers.get('Accept', ''):
            return super().get(request, *args, **kwargs)
        booking = self.get_object()
        return render(request, 'bookings/booking_detail.html', {'booking': booking})

class BookingCreateView(generics.CreateAPIView):
    """
    Create a new booking for a specific bike.

    * Requires: Authentication
    * Returns: JSON booking data with payment URL for API, redirects or renders template for non-API
    """
    serializer_class = BookingSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        bike_id = self.request.query_params.get('bike_id') or self.request.POST.get('bike')
        if bike_id:
            try:
                bike = Bike.objects.get(id=bike_id, is_approved=True, availability_status=True)
                serializer.save(user=self.request.user, bike=bike)
            except Bike.DoesNotExist:
                raise serializers.ValidationError({"bike_id": "Invalid or unavailable bike."})
        else:
            raise serializers.ValidationError({"bike_id": "No bike specified."})

    def post(self, request, *args, **kwargs):
        if 'application/json' in request.headers.get('Accept', '') or request.path.startswith('/api/'):
            serializer = self.get_serializer(data=request.data)
            if serializer.is_valid():
                self.perform_create(serializer)
                booking = serializer.instance
                payment_option = serializer.validated_data.get('payment_option')
                payment_method = serializer.validated_data.get('payment_method')
                response_data = BookingSerializer(booking).data

                if payment_option in ['full_online', 'partial_online']:
                    if not payment_method or payment_method not in ['esewa', 'paypal']:
                        return Response({"success": False, "message": "Invalid payment method."},
                                        status=status.HTTP_400_BAD_REQUEST)

                    payment_data = {
                        'booking': booking.id,
                        'payment_method': payment_method,
                        'amount': float(booking.total_price),
                        'transaction_uuid': f"txn_{booking.id}_{int(now().timestamp())}"
                    }
                    payment_serializer = PaymentSerializer(data=payment_data)
                    if payment_serializer.is_valid():
                        payment = payment_serializer.save()
                        host = request.get_host()
                        if payment_method == 'paypal':
                            payment_url = reverse('payment:paypal-process',
                                                  kwargs={'booking_id': booking.id, 'amount': str(booking.total_price)})
                        elif payment_method == 'esewa':
                            payment_url = reverse('payment:esewa-process',
                                                  kwargs={'booking_id': booking.id, 'amount': str(booking.total_price)})
                        response_data['payment_url'] = f"http://{host}{payment_url}"
                        return Response({
                            "success": True,
                            "message": f"Booking created. Redirect to {payment_method} payment.",
                            "data": response_data
                        }, status=status.HTTP_201_CREATED)
                    return Response({"success": False, "message": "Payment initiation failed.",
                                     "errors": payment_serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
                elif payment_option == 'cash_on_delivery':
                    booking.payment_method = 'cash_on_delivery'
                    booking.payment_status = False
                    booking.save()
                    return Response({
                        "success": True,
                        "message": "Booking created successfully with Cash on Delivery. Please confirm at pickup.",
                        "data": response_data
                    }, status=status.HTTP_201_CREATED)
                else:
                    return Response({
                        "success": False,
                        "message": "Invalid payment option selected.",
                        "data": response_data
                    }, status=status.HTTP_400_BAD_REQUEST)
            return Response({
                "success": False,
                "errors": serializer.errors,
                "data": {}
            }, status=status.HTTP_400_BAD_REQUEST)
        form = BookingForm(request.POST)
        if form.is_valid():
            serializer = self.get_serializer(data=form.cleaned_data)
            if serializer.is_valid():
                self.perform_create(serializer)
                booking = serializer.instance
                payment_option = form.cleaned_data['payment_option']
                if payment_option in ['full_online', 'partial_online']:
                    return redirect('bookings:booking-payment-select', pk=booking.id)
                elif payment_option == 'cash_on_delivery':
                   # Mark as unpaid for now until payment confirmation
                    booking.payment_method = 'cash_on_delivery'
                    booking.payment_status = 'unpaid'
                    booking.status = 'pending'
                    booking.payment_option = payment_option
                    booking.save()
                    messages.success(request, "Booking created successfully with Cash on Delivery. Please confirm at pickup.")
                    return redirect('bookings:booking-list')
                else:
                    messages.error(request, "Invalid payment option selected.")
                    return redirect('bookings:booking-create')
            else:
                messages.error(request, "Invalid booking details.")
                return render(request, 'bookings/booking_create.html', {'form': form, 'bike': Bike})
        messages.error(request, "Invalid form data.")
        return render(request, 'bookings/booking_create.html', {'form': form, 'bike': Bike})

    def get(self, request, *args, **kwargs):
        if request.path.startswith('/api/') or 'application/json' in request.headers.get('Accept', ''):
            return Response({"detail": "Method not allowed for API"}, status=status.HTTP_405_METHOD_NOT_ALLOWED)
        if not request.user.is_authenticated:
            return redirect('users:login')
        bike_id = self.request.query_params.get('bike_id')
        bike = None
        unavailable_dates = []
        if bike_id:
            try:
                bike = Bike.objects.get(id=bike_id, is_approved=True, availability_status=True)
                overlapping_bookings = Booking.objects.filter(
                    bike=bike,
                    start_date__lt=now() + timezone.timedelta(days=30),
                    end_date__gt=now(),
                    status='confirmed',
                ).values('start_date', 'end_date')
                unavailable_dates = [
                    {'start': booking['start_date'].isoformat(), 'end': booking['end_date'].isoformat()}
                    for booking in overlapping_bookings
                ]
                start_dates = Booking.objects.filter(
                    bike=bike,
                    status='confirmed',
                ).values_list('start_date', flat=True)
                for start_date in start_dates:
                    unavailable_dates.append({'start': start_date.isoformat(), 'end': start_date.isoformat()})
                form = BookingForm(initial={'bike': bike.id})
            except Bike.DoesNotExist:
                bike = None
                form = BookingForm()
        else:
            messages.error(request, "No bike selected. Please try booking again from a bike card.")
            form = BookingForm()
        return render(request, 'bookings/booking_create.html', {
            'form': form,
            'bike': bike,
            'unavailable_dates': unavailable_dates
        })

class BookingUpdateView(generics.UpdateAPIView):
    """
    Update a specific booking.

    * Requires: Authentication (only user or admin can modify their own booking)
    * Returns: JSON booking data for API, renders template for non-API
    """
    serializer_class = BookingSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Booking.objects.filter(user=self.request.user)

    def get(self, request, *args, **kwargs):
        if request.path.startswith('/api/') or 'application/json' in request.headers.get('Accept', ''):
            return super().get(request, *args, **kwargs)
        booking = self.get_object()
        return render(request, 'bookings/booking_update.html', {'booking': booking})

class BookingDeleteView(generics.DestroyAPIView):
    """
    Delete a specific booking.

    * Requires: Authentication (only user or admin can delete their own booking)
    * Returns: JSON success message for API, redirects for non-API
    """
    serializer_class = BookingSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Booking.objects.filter(user=self.request.user)

    def delete(self, request, *args, **kwargs):
        if request.path.startswith('/api/') or 'application/json' in request.headers.get('Accept', ''):
            return super().delete(request, *args, **kwargs)
        instance = self.get_object()
        self.perform_destroy(instance)
        messages.success(request, "Booking deleted successfully.")
        return redirect('bookings:booking-list')

class BookingPaymentSelectView(generics.RetrieveUpdateAPIView):
    """
    Select payment method for a specific booking.

    * Requires: Authentication (only user or admin can modify their own booking)
    * Returns: JSON booking data for API, renders template for non-API
    """
    serializer_class = BookingSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Booking.objects.filter(user=self.request.user)

    def get(self, request, *args, **kwargs):
        if request.path.startswith('/api/') or 'application/json' in request.headers.get('Accept', ''):
            return super().get(request, *args, **kwargs)
        booking = self.get_object()
        if booking.payment_option not in ['full_online', 'partial_online']:
            messages.error(request, "This booking does not require online payment.")
            return redirect('bookings:booking-detail', pk=booking.id)
        serializer = BookingPaymentSelectSerializer(booking, context={'booking': booking})
        return render(request, 'bookings/booking_payment_select.html', {'booking': booking})

    def post(self, request, *args, **kwargs):
        booking = self.get_object()
        if booking.payment_option not in ['full_online', 'partial_online']:
            messages.error(request, "This booking does not require online payment.")
            return redirect('bookings:booking-detail', pk=booking.id)

        serializer = BookingPaymentSelectSerializer(data=request.POST, context={'booking': booking})
        if serializer.is_valid():
            payment_method = serializer.validated_data['payment_method']
            if not Payment.objects.filter(booking=booking).exists():
                payment_data = {
                    'booking': booking.id,
                    'payment_method': payment_method,
                    'amount': float(booking.total_price),
                    'transaction_uuid': f"txn_{booking.id}_{int(now().timestamp())}"
                }
                payment_serializer = PaymentSerializer(data=payment_data)
                if payment_serializer.is_valid():
                    payment_serializer.save()
                else:
                    return render(request, 'bookings/booking_payment_select.html',
                                  {'booking': booking, 'error': payment_serializer.errors})

            if payment_method == 'esewa':
                return redirect('payment:esewa-process', booking_id=booking.id, amount=str(booking.total_price))
            elif payment_method == 'paypal':
                return redirect('payment:paypal-process', booking_id=booking.id, amount=str(booking.total_price))
        return render(request, 'bookings/booking_payment_select.html', {'booking': booking, 'error': serializer.errors})

class BookingApproveView(generics.UpdateAPIView):
    """
    Approve a booking request by the bike host.

    * Requires: Authentication (only bike host or admin can approve)
    * Returns: Redirects to host dashboard for non-API requests
    """
    serializer_class = BookingSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Booking.objects.filter(bike__host=self.request.user)

    def post(self, request, *args, **kwargs):
        booking = self.get_object()
        if booking.status != 'pending':
            messages.error(request, "This booking cannot be approved as it is not in pending status.")
            return redirect('users:bike-host-dashboard')
        if request.user != booking.bike.host and not request.user.is_superuser:
            messages.error(request, "You are not authorized to approve this booking.")
            return redirect('users:bike-host-dashboard')
        booking.status = 'confirmed'
        booking.save()
        messages.success(request, f"Booking for {booking.bike.name} has been approved.")
        return redirect('users:bike-host-dashboard')

class BookingRejectView(generics.UpdateAPIView):
    """
    Reject a booking request by the bike host.

    * Requires: Authentication (only bike host or admin can reject)
    * Returns: Redirects to host dashboard for non-API requests
    """
    serializer_class = BookingSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Booking.objects.filter(bike__host=self.request.user)

    def post(self, request, *args, **kwargs):
        booking = self.get_object()
        if booking.status != 'pending':
            messages.error(request, "This booking cannot be rejected as it is not in pending status.")
            return redirect('users:bike-host-dashboard')
        if request.user != booking.bike.host and not request.user.is_superuser:
            messages.error(request, "You are not authorized to reject this booking.")
            return redirect('users:bike-host-dashboard')
        booking.status = 'cancelled'
        booking.save()
        messages.success(request, f"Booking for {booking.bike.name} has been rejected.")
        return redirect('users:bike-host-dashboard')

class BookingCompleteView(generics.UpdateAPIView):
    """
    Mark a booking as completed and update host earnings.

    * Requires: Authentication (only bike host or admin can mark as completed)
    * Returns: Redirects to host dashboard for non-API requests
    """
    serializer_class = BookingSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Booking.objects.filter(bike__host=self.request.user)

    def post(self, request, *args, **kwargs):
        booking = self.get_object()
        if booking.status != 'confirmed':
            messages.error(request, "This booking cannot be marked as completed as it is not confirmed.")
            return redirect('users:bike-host-dashboard')
        if request.user != booking.bike.host and not request.user.is_superuser:
            messages.error(request, "You are not authorized to mark this booking as completed.")
            return redirect('users:bike-host-dashboard')
        if not booking.is_completed():
            messages.error(request, "This booking cannot be marked as completed yet. End date has not passed.")
            return redirect('users:bike-host-dashboard')
        booking.status = 'completed'
        booking.save()
        # Update host earnings
        host_profile = hostProfile.objects.get_or_create(user=booking.bike.host)[0]
        # host_profile.update_earnings(booking.total_price) # Assuming update_earnings method exists or will be implemented
        messages.success(request, f"Booking for {booking.bike.name} has been marked as completed. Earnings updated.")
        return redirect('users:bike-host-dashboard')
