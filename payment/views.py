import requests
from django.conf import settings
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
    """List all payments (Admin only) or create a payment (User only)."""
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer

    def create(self, request, *args, **kwargs):
        try:
            serializer = self.get_serializer(data=request.data)
            if serializer.is_valid():
                booking_id = request.data.get('booking')
                booking = get_object_or_404(Booking, id=booking_id)

                # Use the booking's total_price
                amount = booking.total_price

                # Create the payment with the calculated amount from the booking
                payment = serializer.save(
                    booking=booking,
                    amount=amount,  # Set the amount here with booking's total price
                    payment_method=request.data.get('payment_method')
                )

                # Now initiate PayPal payment
                host = request.get_host()
                paypal_dict = {
                    "business": settings.PAYPAL_RECEIVER_EMAIL,
                    "amount": payment.amount,  # Use the saved amount
                    "item_name": "Bike Rental",
                    "invoice": str(payment.booking.id),
                    "currency_code": "USD",
                    "notify_url": f"http://{host}{reverse('paypal-ipn')}",
                    "return_url": f"http://{host}{reverse('payment-done')}",
                    "cancel_return": f"http://{host}{reverse('payment-canceled')}",
                }

                form = PayPalPaymentsForm(initial=paypal_dict)
                return Response({
                    "success": True,
                    "redirect_url": reverse('payment_process'),  # Return a URL or token for payment processing
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
    """Retrieve, update, or delete a payment (Only owner or admin)."""
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer
    permission_classes = [IsOwnerOrAdmin]





def payment_process(request):
    host = request.get_host()

    paypal_dict = {
        "business": settings.PAYPAL_RECEIVER_EMAIL,
        "amount": "10.00",  # The amount of the payment
        "item_name": "Bike Rental",
        "invoice": "unique-invoice-id",
        "currency_code": "USD",
        "notify_url": f"http://{host}{reverse('paypal-ipn')}",
        "return_url": f"http://{host}{reverse('payment-done')}",
        "cancel_return": f"http://{host}{reverse('payment-canceled')}",
    }

    form = PayPalPaymentsForm(initial=paypal_dict)
    context = {"form": form}
    return render(request, "payment/payment_process.html", context)


def payment_done(request):
    return render(request, "payment/payment_done.html")


def payment_canceled(request):
    return render(request, "payment/payment_canceled.html")



def handle_ipn(sender, **kwargs):
    ipn_obj = sender
    if ipn_obj.payment_status == "Completed":
        # Payment was successful
        payment = Payment.objects.create(
            amount=ipn_obj.mc_gross,
            booking_id=ipn_obj.invoice,
            # other fields...
        )
        # Update the booking status here if needed

valid_ipn_received.connect(handle_ipn)
invalid_ipn_received.connect(lambda sender, **kwargs: print("Invalid IPN received"))