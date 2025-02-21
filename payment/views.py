import requests
from django.shortcuts import redirect
from rest_framework import generics, status, views
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Payment
from .serializers import PaymentSerializer
from users.permissions import IsOwnerOrAdmin
from bookings.models import Booking

from django.conf import settings
from django.urls import reverse
from django.shortcuts import render, get_object_or_404
from paypal.standard.forms import PayPalPaymentsForm
from paypal.standard.ipn.signals import valid_ipn_received, invalid_ipn_received

class PaymentListView(generics.ListCreateAPIView):
    """
    List all payments or create a new payment.

    * Requires: Authentication (admin for listing, user for creation), booking ID, payment method
    * Returns: List of payments or payment initiation redirect URL
    """
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer
    throttle_scope = 'payments'

    def create(self, request, *args, **kwargs):
        try:
            serializer = self.get_serializer(data=request.data)
            if serializer.is_valid():
                booking_id = request.data.get('booking')
                booking = get_object_or_404(Booking, id=booking_id)

                payment = serializer.save()
                host = request.get_host()
                paypal_dict = {
                    "business": settings.PAYPAL_RECEIVER_EMAIL,
                    "amount": f"{payment.amount:.2f}",
                    "item_name": f"Bike Rental for {booking.bike.name}",
                    "invoice": str(payment.id),
                    "currency_code": "USD",
                    "notify_url": f"http://{host}{reverse('paypal-ipn')}",
                    "return_url": f"http://{host}{reverse('payment-done')}",
                    "cancel_return": f"http://{host}{reverse('payment-canceled')}",
                }
                form = PayPalPaymentsForm(initial=paypal_dict)
                return Response({
                    "success": True,
                    "redirect_url": reverse('payment_process', kwargs={'payment_id': payment.id}),
                    "message": "Payment process initiated. Redirect to PayPal for completion."
                }, status=status.HTTP_201_CREATED)
            return Response({"success": False, "errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response(
                {"success": False, "message": "An error occurred while initiating payment", "details": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def get_permissions(self):
        if self.request.method == "GET":
            return [IsAuthenticated()]
        return [IsOwnerOrAdmin()]


class PaymentDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update, or delete a payment.

    * Requires: Authentication (only owner or admin)
    * Returns: Payment data or success message on deletion
    """
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer
    permission_classes = [IsOwnerOrAdmin]

def payment_process(request, payment_id):
    """
    Render the PayPal payment form.

    * Requires: payment_id (passed via URL after payment initiation)
    * Returns: HTML form for PayPal payment with dynamic amount
    """
    payment = get_object_or_404(Payment, id=payment_id)
    host = request.get_host()
    paypal_dict = {
        "business": settings.PAYPAL_RECEIVER_EMAIL,
        "amount": f"{payment.amount:.2f}",  # Use dynamic amount from Payment object
        "item_name": f"Bike Rental for {payment.booking.bike.name}",
        "invoice": str(payment.booking.id),
        "currency_code": "USD",
        "notify_url": f"http://{host}{reverse('paypal-ipn')}",
        "return_url": f"http://{host}{reverse('payment-done')}",
        "cancel_return": f"http://{host}{reverse('payment-canceled')}",
    }
    form = PayPalPaymentsForm(initial=paypal_dict)
    context = {"form": form}
    return render(request, "payment/payment_process.html", context)

def payment_done(request):
    """
    Handle successful payment completion.

    * Requires: None (PayPal redirect)
    * Returns: Success page
    """
    return render(request, "payment/payment_done.html")

def payment_canceled(request):
    """
    Handle payment cancellation.

    * Requires: None (PayPal redirect)
    * Returns: Cancellation page
    """
    return render(request, "payment/payment_canceled.html")

def handle_ipn(sender, **kwargs):
    """
    Handle PayPal IPN notifications.

    * Requires: None (PayPal callback)
    * Returns: None (updates payment status)
    """
    ipn_obj = sender
    if ipn_obj.payment_status == "Completed":
        try:
            payment = Payment.objects.get(booking_id=ipn_obj.invoice)
            payment.mark_as_completed(transaction_id=ipn_obj.txn_id)
        except Payment.DoesNotExist:
            print(f"Payment for booking {ipn_obj.invoice} not found.")
    elif ipn_obj.payment_status == "Failed":
        try:
            payment = Payment.objects.get(booking_id=ipn_obj.invoice)
            payment.mark_as_failed()
        except Payment.DoesNotExist:
            print(f"Payment for booking {ipn_obj.invoice} not found.")

valid_ipn_received.connect(handle_ipn)
invalid_ipn_received.connect(lambda sender, **kwargs: print("Invalid IPN received"))