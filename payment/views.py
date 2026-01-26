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
from users.permissions import IshostOrAdmin
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
        return [IshostOrAdmin()]

class PaymentDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update, or delete a payment.

    * Requires: Authentication (only owner or admin)
    """
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer
    permission_classes = [IsAuthenticated, IshostOrAdmin]
    lookup_field = 'booking_id'


def payment_process(request, booking_id, amount):
    payment = get_object_or_404(Payment, booking_id=booking_id)
    amount_float = float(amount)
    host = request.get_host()
    
    # Currency Conversion: NPR to USD
    # Assuming 1 USD = 135 NPR (Fixed Rate for now)
    exchange_rate = 135
    amount_usd = amount_float / exchange_rate
    
    paypal_dict = {
        "business": settings.PAYPAL_RECEIVER_EMAIL,
        "amount": f"{amount_usd:.2f}",
        "item_name": f"Bike Rental for {payment.booking.bike.name} (NPR {amount_float:.2f})",
        "invoice": str(booking_id),
        "custom": str(booking_id),
        "currency_code": "USD",
        "notify_url": f"http://{host}{reverse('payment:paypal-ipn')}",
        "return_url": f"http://{host}{reverse('payment:payment-done')}?booking_id={booking_id}",
        "cancel_return": f"http://{host}{reverse('payment:payment-canceled')}",
    }

    form = PayPalPaymentsForm(initial=paypal_dict)
    request.session['booking_id'] = booking_id
    context = {"form": form, "payment": payment, "amount": amount_float, "amount_usd": amount_usd}
    return render(request, "payment/payment_process.html", context)


def esewa_payment_process(request, booking_id, amount):
    payment = get_object_or_404(Payment, booking_id=booking_id)
    host = request.get_host()
    
    # Use hyphens instead of underscores for transaction_uuid to be safe
    transaction_uuid = f"txn-{payment.id}-{int(now().timestamp())}"

    # Convert str amount to Decimal for processing
    amount_decimal = Decimal(amount)
    
    # Amount is already in NPR, so no conversion needed
    total_amount_npr = amount_decimal
    
    # Format amount to 2 decimal places string
    total_amount_str = "{:.2f}".format(total_amount_npr)

    # Generate HMAC-SHA256 signature for V2
    # Message format: total_amount=100,transaction_uuid=123,product_code=EPAYTEST
    message = f"total_amount={total_amount_str},transaction_uuid={transaction_uuid},product_code={settings.ESEWA_PRODUCT_CODE}"
    
    # Ensure secret key is stripped of whitespace
    secret_key = settings.ESEWA_SECRET_KEY.strip()
    
    signature = base64.b64encode(
        hmac.new(
            secret_key.encode('utf-8'),
            message.encode('utf-8'),
            hashlib.sha256
        ).digest()
    ).decode('utf-8')

    # Correct success URL construction
    success_url = f"{request.scheme}://{host}{reverse('payment:esewa_payment_success')}?booking_id={booking_id}"
    failure_url = f"{request.scheme}://{host}{reverse('payment:esewa_payment_failure')}?booking_id={booking_id}"

    # eSewa V2 request parameters
    esewa_dict = {
        "amount": total_amount_str,
        "tax_amount": "0.00",
        "product_service_charge": "0.00",
        "product_delivery_charge": "0.00",
        "total_amount": total_amount_str,
        "transaction_uuid": transaction_uuid,
        "product_code": settings.ESEWA_PRODUCT_CODE,
        "success_url": success_url,
        "failure_url": failure_url,
        "signed_field_names": "total_amount,transaction_uuid,product_code",
        "signature": signature,
    }
    
    print(f"DEBUG: eSewa Dict: {json.dumps(esewa_dict, indent=2)}")
    logger.info(f"eSewa request parameters: {esewa_dict}")
    logger.info(f"eSewa signature message: {message}")
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
    data_param = request.GET.get('data')

    logger.info(f"eSewa success callback: booking_id={booking_id}, data={data_param}")

    if not booking_id or not data_param:
        logger.error("Missing booking_id or no data parameter")
        return render(request, "payment/esewa_payment_failure.html", {'error': "Missing booking_id or eSewa response data."})

    try:
        decoded_data = base64.b64decode(data_param).decode('utf-8')
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

        # Extract payment ID from transaction_uuid (format: txn_{id}_{timestamp})
        try:
            payment_id = int(transaction_uuid.split('-')[1])
            payment = get_object_or_404(Payment, id=payment_id, booking_id=booking_id)
        except (IndexError, ValueError):
             payment = get_object_or_404(Payment, booking_id=booking_id)

        logger.info(f"Found payment: id={payment.id}, current_status={payment.status}")

        # Verify signature
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

            if signature != expected_signature:
                logger.error("Signature verification failed")
                return render(request, "payment/esewa_payment_failure.html", {'error': "Invalid signature from eSewa."})

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
        logger.error(f"Payment not found: booking_id={booking_id}")
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
    booking_id = (
        request.GET.get('booking_id')
        or request.GET.get('invoice')
        or request.session.get('booking_id')
    )
    payment_id = request.GET.get('paymentId')
    payer_id = request.GET.get('PayerID')
    token = request.GET.get('token')

    logger.info(f"PayPal success callback: booking_id={booking_id}, payment_id={payment_id}, payer_id={payer_id}, token={token}")

    if not booking_id:
        logger.error("Missing booking_id in PayPal callback.")
        return render(request, "payment/payment_canceled.html", {'error': "Missing booking ID."})

    try:
        payment = get_object_or_404(Payment, booking_id=booking_id)
        logger.info(f"Payment object fetched: ID={payment.id}, Status={payment.status}")

        # ✅ Already completed (e.g., via IPN)
        if payment.status == "completed":
            logger.info("Payment already marked as completed by IPN.")
            if 'booking_id' in request.session:
                del request.session['booking_id']
            return render(request, "payment/payment_done.html", {'payment': payment})

        # ✅ Treat missing payer_id as 'possibly completed' if payment not marked
        if not payer_id:
            logger.warning("PayerID not found, but payment might be successful via IPN.")
            return render(request, "payment/payment_pending.html", {
                'payment': payment,
                'warning': "Payment may have been completed. Awaiting confirmation. Please check your booking dashboard or contact support."
            })

        # ✅ Mark as completed manually (fallback)
        payment.mark_as_completed(
            transaction_id=payment_id or f"paypal_pending_{token}",
            transaction_uuid=payment_id or token
        )
        logger.info("Marked payment as completed.")

        payment.booking.status = 'confirmed'
        payment.booking.payment_status = True
        payment.booking.save(update_fields=['status', 'payment_status'])

        if 'booking_id' in request.session:
            del request.session['booking_id']

        return render(request, "payment/payment_done.html", {'payment': payment})

    except Payment.DoesNotExist:
        logger.error(f"Payment not found for booking_id={booking_id}")
        return render(request, "payment/payment_canceled.html", {'error': "No such payment found."})
    except Exception as e:
        logger.exception(f"Error during PayPal payment_done processing: {str(e)}")
        return render(request, "payment/payment_canceled.html", {'error': f"An unexpected error occurred: {str(e)}"})



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
        
        # Verify the specific status from PayPal IPN
        # Common statuses: "Completed", "Pending", "Denied", "Failed", "Refunded"
        
        if ipn_obj.payment_status == "Completed":
            # Check amounts match, currency, etc. (omitted for brevity but recommended)
            payment.mark_as_completed(transaction_id=ipn_obj.txn_id)
            
            # Payment model's save() hook will update Booking automatically:
            # Booking.payment_status = 'paid'
            # payment.booking.save()
            
        elif ipn_obj.payment_status in ["Failed", "Canceled"]:
             payment.mark_as_failed()
             logger.warning(f"IPN payment failed/canceled: {ipn_obj.payment_status}")
        else:
            logger.warning(f"IPN payment status unhandled: status={ipn_obj.payment_status}")
    except Payment.DoesNotExist:
        logger.error(f"IPN payment not found: booking_id={booking_id}, payment_id={payment_id}")

valid_ipn_received.connect(handle_ipn)
invalid_ipn_received.connect(lambda sender, **kwargs: print("Invalid IPN received"))