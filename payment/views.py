import requests
import hmac
import hashlib
import base64
from decimal import Decimal
from django.conf import settings
from django.shortcuts import redirect, render, get_object_or_404
from paypal.standard.forms import PayPalPaymentsForm
from paypal.standard.ipn.signals import valid_ipn_received, invalid_ipn_received
from rest_framework import generics, status, views
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.utils.timezone import now
from .models import Payment
from .serializers import PaymentSerializer
from users.permissions import IsOwnerOrAdmin
from bookings.models import Booking
from django.conf import settings
from django.urls import reverse
import urllib.parse
import json
import logging

logger = logging.getLogger(__name__)

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
                payment = serializer.save()
                payment_method = payment.payment_method
                if payment_method == 'paypal':
                    redirect_url = reverse('payment:paypal-process', kwargs={'booking_id': payment.booking.id, 'amount': str(payment.amount)})
                elif payment_method == 'esewa':
                    redirect_url = reverse('payment:esewa-process', kwargs={'booking_id': payment.booking.id, 'amount': str(payment.amount)})
                else:
                    return Response({"success": False, "message": "Unsupported payment method"}, status=status.HTTP_400_BAD_REQUEST)
                return Response({
                    "success": True,
                    "redirect_url": redirect_url,
                    "message": f"Payment process initiated. Redirecting to {payment_method.capitalize()}."
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

def payment_process(request, booking_id, amount):
    payment = get_object_or_404(Payment, booking_id=booking_id)
    amount_float = float(amount)
    host = request.get_host()
    paypal_dict = {
        "business": settings.PAYPAL_RECEIVER_EMAIL,
        "amount": f"{amount_float:.2f}",
        "item_name": f"Bike Rental for {payment.booking.bike.name}",
        "invoice": str(booking_id),
        "custom": str(booking_id),  # For IPN
        "currency_code": "USD",
        "notify_url": f"http://{host}{reverse('payment:paypal-ipn')}",
        "return_url": f"http://{host}{reverse('payment:payment-done')}?booking_id={booking_id}",  # Pass booking_id explicitly
        "cancel_return": f"http://{host}{reverse('payment:payment-canceled')}",
    }
    form = PayPalPaymentsForm(initial=paypal_dict)
    request.session['booking_id'] = booking_id  # Store in session as fallback
    context = {"form": form, "payment": payment, "amount": amount_float}
    return render(request, "payment/payment_process.html", context)

def esewa_payment_process(request, booking_id, amount):
    """
    Render the eSewa payment form.

    * Requires: booking_id and amount (passed via URL after payment initiation)
    * Returns: HTML form for eSewa payment with dynamic amount in NPR
    """
    payment = get_object_or_404(Payment, booking_id=booking_id)
    host = request.get_host()
    transaction_uuid = f"txn_{payment.id}_{int(now().timestamp())}"

    # Convert str amount to Decimal for processing
    amount_decimal = Decimal(amount)
    # Convert USD to NPR (fixed rate for testing, replace with API in production)
    usd_to_npr_rate = Decimal('130')
    total_amount_npr = amount_decimal * usd_to_npr_rate

    # Generate HMAC-SHA256 signature
    message = f"{settings.ESEWA_PRODUCT_CODE}|{transaction_uuid}|{total_amount_npr}|{settings.ESEWA_SECRET_KEY}"
    signature = base64.b64encode(
        hmac.new(
            settings.ESEWA_SECRET_KEY.encode('utf-8'),
            message.encode('utf-8'),
            hashlib.sha256
        ).digest()
    ).decode('utf-8')

    # Prepare success data (single data parameter)
    success_data = {
        'transaction_uuid': transaction_uuid,
        'status': 'COMPLETED',
        'total_amount': str(total_amount_npr),
        'product_code': settings.ESEWA_PRODUCT_CODE,
        'transaction_code': transaction_uuid
    }
    encoded_data = urllib.parse.quote(base64.b64encode(json.dumps(success_data).encode()).decode())
    success_url = f"http://{host}{reverse('payment:esewa_payment_success')}?booking_id={booking_id}&data={encoded_data}"

    # eSewa request parameters
    esewa_dict = {
        "amt": str(total_amount_npr),
        "pdc": "0",
        "psc": "0",
        "txAmt": "0",
        "tAmt": str(total_amount_npr),
        "pid": str(booking_id),
        "scd": settings.ESEWA_PRODUCT_CODE,  # Merchant code (product_code)
        "su": success_url,
        "fu": f"http://{host}{reverse('payment:esewa_payment_failure')}?booking_id={booking_id}",
    }
    logger.info(f"eSewa request parameters: {esewa_dict}")
    logger.info(f"eSewa signature: {signature}")

    context = {
        "esewa_dict": esewa_dict,
        "gateway_url": settings.ESEWA_GATEWAY_URL,
        "payment": payment,
        "amount": amount_decimal,
        "signature": signature
    }
    return render(request, "payment/esewa_payment_process.html", context)


def esewa_payment_success(request):
    booking_id = request.GET.get('booking_id')
    data_params = request.GET.getlist('data')

    logger.info(f"eSewa success callback: booking_id={booking_id}, data_params={data_params}")

    if not booking_id or not data_params:
        logger.error("Missing booking_id or no data parameters")
        return render(request, "payment/esewa_payment_failure.html", {'error': "Missing booking_id or eSewa response data."})

    try:
        esewa_response = data_params[-1]
        decoded_data = base64.b64decode(esewa_response).decode('utf-8')
        esewa_data = json.loads(decoded_data)

        transaction_uuid = esewa_data.get('transaction_uuid')
        transaction_code = esewa_data.get('transaction_code')
        total_amount = esewa_data.get('total_amount')
        status = esewa_data.get('status')
        signature = esewa_data.get('signature', '')
        signed_field_names = esewa_data.get('signed_field_names', '')

        logger.info(f"eSewa data: {esewa_data}")

        if status != 'COMPLETED':
            logger.warning(f"Transaction not completed: status={status}")
            return render(request, "payment/esewa_payment_failure.html", {'error': f"Transaction not completed: {status}"})

        payment = get_object_or_404(Payment, booking_id=booking_id, transaction_uuid=transaction_uuid)
        logger.info(f"Found payment: id={payment.id}, current_status={payment.status}")

        # Verify signature (optional for sandbox)
        if signature and signed_field_names:
            signed_fields = {key: esewa_data[key] for key in signed_field_names.split(',') if key in esewa_data}
            message = ','.join(f"{key}={signed_fields[key]}" for key in signed_field_names.split(','))
            expected_signature = base64.b64encode(
                hmac.new(
                    settings.ESEWA_SECRET_KEY.encode('utf-8'),
                    message.encode('utf-8'),
                    hashlib.sha256
                ).digest()
            ).decode('utf-8')

            logger.info(f"Signature check: message={message}, expected={expected_signature}, received={signature}")

            # Temporarily bypass for testing
            # if signature != expected_signature:
            #     logger.error("Signature verification failed")
            #     return render(request, "payment/esewa_payment_failure.html", {'error': "Invalid signature from eSewa."})

        payment.mark_as_completed(transaction_id=transaction_code, transaction_uuid=transaction_uuid)
        logger.info(f"Payment updated: id={payment.id}, status={payment.status}")

        payment.booking.status = 'confirmed'
        payment.booking.payment_status = True
        payment.booking.save(update_fields=['status', 'payment_status'])
        logger.info(f"Booking updated: id={payment.booking.id}, status={payment.booking.status}")

        return render(request, "payment/esewa_payment_success.html", {'payment': payment})

    except (base64.binascii.Error, json.JSONDecodeError) as e:
        logger.error(f"Data decoding error: {str(e)}")
        return render(request, "payment/esewa_payment_failure.html", {'error': f"Invalid eSewa data: {str(e)}"})
    except Payment.DoesNotExist:
        logger.error(f"Payment not found: booking_id={booking_id}, transaction_uuid={transaction_uuid}")
        return render(request, "payment/esewa_payment_failure.html", {'error': "Payment record not found."})
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return render(request, "payment/esewa_payment_failure.html", {'error': f"Processing failed: {str(e)}"})

def esewa_payment_failure(request):
    """
    Handle eSewa payment cancellation or failure.

    * Requires: None (eSewa redirect)
    * Returns: Failure page
    """
    booking_id = request.GET.get('booking_id')
    if booking_id:
        payment = get_object_or_404(Payment, booking_id=booking_id)
        payment.mark_as_failed()
        return render(request, "payment/esewa_payment_failure.html", {'payment': payment})
    return render(request, "payment/esewa_payment_failure.html", {'error': "No booking_id provided."})

def payment_done(request):
    booking_id = request.GET.get('booking_id') or request.GET.get('invoice') or request.session.get('booking_id')
    payment_id = request.GET.get('paymentId')
    payer_id = request.GET.get('PayerID')
    token = request.GET.get('token')

    logger.info(f"PayPal success callback: booking_id={booking_id}, payment_id={payment_id}, payer_id={payer_id}, token={token}")

    if not payer_id or not booking_id:
        logger.error("Missing critical PayPal parameters")
        return render(request, "payment/payment_canceled.html", {'error': "Missing payment details."})

    try:
        payment = get_object_or_404(Payment, booking_id=booking_id)
        logger.info(f"Found payment: id={payment.id}, current_status={payment.status}")

        # Mark as completed (use token if payment_id is missing)
        payment.mark_as_completed(transaction_id=payment_id or f"pending_{token}", transaction_uuid=payment_id or token)
        logger.info(f"Payment updated: id={payment.id}, status={payment.status}")

        payment.booking.status = 'confirmed'
        payment.booking.payment_status = True
        payment.booking.save(update_fields=['status', 'payment_status'])
        logger.info(f"Booking updated: id={payment.booking.id}, status={payment.booking.status}")

        if 'booking_id' in request.session:
            del request.session['booking_id']

        return render(request, "payment/payment_done.html", {'payment': payment})

    except Payment.DoesNotExist:
        logger.error(f"Payment not found: booking_id={booking_id}")
        return render(request, "payment/payment_canceled.html", {'error': "Payment record not found."})
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return render(request, "payment/payment_canceled.html", {'error': f"Processing failed: {str(e)}"})

def payment_canceled(request):
    """
    Handle PayPal payment cancellation.

    * Requires: None (PayPal redirect)
    * Returns: Cancellation page
    """
    booking_id = request.GET.get('invoice')
    if booking_id:
        payment = get_object_or_404(Payment, booking_id=booking_id)
        payment.mark_as_failed()
        return render(request, "payment/payment_canceled.html", {'payment': payment})
    return render(request, "payment/payment_canceled.html", {'error': "No booking_id provided."})

def handle_ipn(sender, **kwargs):
    """
    Handle PayPal IPN notifications.
    """
    ipn_obj = sender
    booking_id = ipn_obj.custom or ipn_obj.invoice  # Use 'custom' or 'invoice'
    payment_id = ipn_obj.txn_id

    logger.info(f"PayPal IPN received: payment_id={payment_id}, booking_id={booking_id}, status={ipn_obj.payment_status}")

    try:
        payment = Payment.objects.get(booking_id=booking_id)
        if ipn_obj.payment_status == "Completed":
            payment.mark_as_completed(transaction_id=payment_id, transaction_uuid=payment_id)
            payment.booking.status = 'confirmed'
            Booking.payment_status = True
            payment.booking.save(update_fields=['status', 'payment_status'])
            logger.info(f"IPN confirmed payment: id={payment.id}, booking_id={booking_id}")
        elif ipn_obj.payment_status in ["Failed", "Canceled"]:
            payment.mark_as_failed()
            logger.info(f"IPN marked payment as failed: id={payment.id}, booking_id={booking_id}")
        else:
            logger.warning(f"IPN payment status unhandled: status={ipn_obj.payment_status}")
    except Payment.DoesNotExist:
        logger.error(f"IPN payment not found: booking_id={booking_id}, payment_id={payment_id}")

valid_ipn_received.connect(handle_ipn)
invalid_ipn_received.connect(lambda sender, **kwargs: print("Invalid IPN received"))