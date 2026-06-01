from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import BasePermission
from rest_framework_simplejwt.authentication import JWTAuthentication
from django.utils.crypto import get_random_string
from django.utils import timezone
from django.core.mail import send_mail, EmailMessage
from django.conf import settings
from bikes.models import Bike
from bookings.models import Booking
from django.contrib.auth import get_user_model
from django.db.models import Sum
from datetime import timedelta
from io import BytesIO
from xhtml2pdf import pisa
from django.template.loader import get_template
from .models import StaffActivityLog


class IsStaffOrSuperuser(BasePermission):
    """
    Custom permission: allows access to users who are either is_staff OR is_superuser.

    This fixes the mismatch where the login endpoint allows both is_staff and is_superuser
    users, but Django's built-in IsAdminUser only checks is_staff — causing superuser-only
    accounts (is_superuser=True, is_staff=False) to receive 403 on every API call.
    """
    message = 'This action requires admin or staff privileges.'

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and (request.user.is_staff or request.user.is_superuser)
        )


class QueryParamJWTAuthentication(JWTAuthentication):
    """Allow JWT token to be passed as a ?token= query parameter.
    This is needed so mobile browsers can open authenticated PDF links
    without requiring custom Authorization headers."""

    def authenticate(self, request):
        # Try the standard header-based auth first
        header_result = super().authenticate(request)
        if header_result is not None:
            return header_result

        # Fall back to ?token= query param
        raw_token = request.query_params.get('token')
        if raw_token is None:
            return None
        try:
            validated_token = self.get_validated_token(raw_token)
            user = self.get_user(validated_token)
            return (user, validated_token)
        except Exception:
            return None

from .serializers import (
    BikeSerializer,
    BookingSerializer,
    WalkInCustomerSerializer,
    WalkInBookingSerializer,
    MaintenanceRecordSerializer,
    CustomerDetailSerializer,
)

User = get_user_model()

class AdminDashboardStatsView(APIView):
    permission_classes = [IsStaffOrSuperuser]

    def get(self, request):
        now = timezone.now()
        today = now.date()
        is_superuser = request.user.is_superuser

        # Today's pickups and returns
        today_pickups = Booking.objects.filter(start_date__date=today, status='confirmed').count()
        today_returns = Booking.objects.filter(end_date__date=today, status='confirmed').count()

        # Current inventory status
        total_bikes = Bike.objects.count()
        available_bikes = Bike.objects.filter(availability_status=True).count()

        # Financial Metrics — only for superusers
        financial_data = {}
        if is_superuser:
            from payment.models import Payment
            from bikes.models import MaintenanceRecord
            from decimal import Decimal
            total_revenue = Payment.objects.filter(status='completed').aggregate(Sum('amount'))['amount__sum'] or Decimal('0.00')
            total_expenditure = MaintenanceRecord.objects.aggregate(Sum('cost'))['cost__sum'] or Decimal('0.00')
            net_profit = total_revenue - total_expenditure
            financial_data = {
                'total_revenue': float(total_revenue),
                'total_expenditure': float(total_expenditure),
                'net_profit': float(net_profit),
            }

        # Rented Bikes
        rented_bookings = Booking.objects.filter(
            status='confirmed',
            payment_status__in=['paid', 'partial'],
            start_date__lte=now,
            end_date__gte=now
        ).select_related('bike', 'user').order_by('end_date')

        rented_bikes_data = []
        for booking in rented_bookings:
            rented_bikes_data.append({
                'booking_id': booking.id,
                'bike_id': booking.bike.id,
                'bike_name': f"{booking.bike.brand} {booking.bike.name}",
                'vehicle_number': booking.bike.vehicle_number or "N/A",
                'customer_name': booking.user.get_full_name() or booking.user.username,
                'customer_phone': booking.user.phone_number,
                'start_date': booking.start_date.isoformat(),
                'end_date': booking.end_date.isoformat(),
            })

        # Today's rental ending alerts
        rental_end_alerts = Booking.objects.filter(
            status='confirmed',
            end_date__date=today
        ).select_related('bike', 'user')

        rental_end_alerts_data = []
        for booking in rental_end_alerts:
            rental_end_alerts_data.append({
                'booking_id': booking.id,
                'bike_name': f"{booking.bike.brand} {booking.bike.name}",
                'vehicle_number': booking.bike.vehicle_number or "N/A",
                'customer_name': booking.user.get_full_name() or booking.user.username,
                'customer_phone': booking.user.phone_number,
                'end_date': booking.end_date.isoformat(),
            })

        # Staff Activity Notifications — only for superusers
        staff_activity_notifications = []
        if is_superuser:
            unread_logs = StaffActivityLog.objects.filter(is_read=False).select_related('staff_user', 'booking')[:50]
            for log in unread_logs:
                staff_name = (
                    log.staff_user.get_full_name() or log.staff_user.username
                    if log.staff_user else 'Unknown Staff'
                )
                staff_activity_notifications.append({
                    'id': log.id,
                    'action': log.action,
                    'action_label': log.get_action_display(),
                    'staff_name': staff_name,
                    'description': log.description,
                    'booking_id': log.booking_id,
                    'timestamp': log.timestamp.isoformat(),
                })

        response_data = {
            'today_pickups': today_pickups,
            'today_returns': today_returns,
            'total_bikes': total_bikes,
            'available_bikes': available_bikes,
            'rented_bikes': rented_bikes_data,
            'rental_end_alerts': rental_end_alerts_data,
            'staff_activity_notifications': staff_activity_notifications,
            'is_superuser': is_superuser,
        }
        response_data.update(financial_data)
        return Response(response_data)


class AdminBikeListView(generics.ListCreateAPIView):
    queryset = Bike.objects.all().order_by('-created_at')
    serializer_class = BikeSerializer
    permission_classes = [IsStaffOrSuperuser]

class AdminBikeDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Bike.objects.all()
    serializer_class = BikeSerializer
    permission_classes = [IsStaffOrSuperuser]

class AdminBookingListView(generics.ListAPIView):
    queryset = Booking.objects.all().order_by('-created_at')
    serializer_class = BookingSerializer
    permission_classes = [IsStaffOrSuperuser]

class WalkInCustomerCreateView(APIView):
    permission_classes = [IsStaffOrSuperuser]

    def get(self, request):
        phone_number = request.query_params.get('phone')
        if not phone_number:
            return Response({"detail": "Phone parameter is required."}, status=status.HTTP_400_BAD_REQUEST)
        
        user = User.objects.filter(phone_number=phone_number).first()
        if not user:
            return Response({"detail": "Customer not found."}, status=status.HTTP_404_NOT_FOUND)
            
        return Response({
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "full_name": user.get_full_name() or user.username,
            "phone_number": user.phone_number,
            "nationality": getattr(user, 'nationality', '') or 'Nepali',
            "driving_license_no": getattr(user, 'driving_license_no', '') or '',
            "passport_no": getattr(user, 'passport_no', '') or '',
        }, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = WalkInCustomerSerializer(data=request.data)
        if serializer.is_valid():
            phone_number = serializer.validated_data['phone_number']
            full_name = serializer.validated_data['full_name']
            email = serializer.validated_data.get('email', '')
            nationality = serializer.validated_data['nationality']

            # Check if user already exists
            user = User.objects.filter(phone_number=phone_number).first()
            if user:
                return Response({
                    "detail": "Customer already exists.",
                    "user_id": user.id,
                    "phone_number": user.phone_number
                }, status=status.HTTP_200_OK)

            # Generate random password
            temp_password = get_random_string(10)
            
            # Create user
            fallback_email = email if email else f"{phone_number}@example.com"
            user = User.objects.create_user(
                username=phone_number, # username is phone number
                email=fallback_email,
                password=temp_password,
                first_name=full_name.split(' ')[0],
                last_name=' '.join(full_name.split(' ')[1:]) if ' ' in full_name else '',
                phone_number=phone_number,
                nationality=nationality,
                is_active=True
            )

            # Send Email/SMS
            if email:
                try:
                    send_mail(
                        'Welcome to EasyMoto Rental Service',
                        f'Hello {full_name},\n\nYour account has been created successfully!\n\n'
                        f'You can log in to our website to track your rentals using these credentials:\n'
                        f'Username / Phone: {phone_number}\n'
                        f'Password: {temp_password}\n\n'
                        f'Please change your password after logging in.\n\nThank you for choosing EasyMoto.',
                        settings.DEFAULT_FROM_EMAIL,
                        [email],
                        fail_silently=True,
                    )
                except Exception as e:
                    print(f"Failed to send email: {e}")

            return Response({
                "detail": "Customer created successfully and credentials sent.",
                "user_id": user.id,
                "phone_number": user.phone_number
            }, status=status.HTTP_201_CREATED)
            
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class WalkInBookingCreateView(APIView):
    permission_classes = [IsStaffOrSuperuser]

    def post(self, request):
        serializer = WalkInBookingSerializer(data=request.data)
        if serializer.is_valid():
            phone_number = serializer.validated_data['phone_number']
            bike_id = serializer.validated_data['bike_id']
            start_date = serializer.validated_data['start_date']
            end_date = serializer.validated_data['end_date']

            user = User.objects.filter(phone_number=phone_number).first()
            if not user:
                return Response({"detail": "Customer not found. Create customer first."}, status=status.HTTP_404_NOT_FOUND)

            try:
                bike = Bike.objects.get(id=bike_id)
            except Bike.DoesNotExist:
                return Response({"detail": "Bike not found."}, status=status.HTTP_404_NOT_FOUND)

            from decimal import Decimal
            from admin_panel.models import RentalContract
            from payment.models import Payment, Invoice

            # Calculate duration in days
            duration_days = (end_date - start_date).days + 1
            base_price = bike.price_per_day * Decimal(duration_days)

            # Determine payment option and method
            payment_method_input = serializer.validated_data.get('payment_method', 'cash')
            if payment_method_input == 'qr':
                db_payment_method = 'esewa'
                db_payment_option = 'full_online'
            else:
                db_payment_method = 'cash_on_delivery'
                db_payment_option = 'cash_on_delivery'

            # Create Booking
            booking = Booking.objects.create(
                user=user,
                bike=bike,
                start_date=start_date,
                end_date=end_date,
                pickup_location="Office",
                status='confirmed',
                payment_status='unpaid',
                payment_option=db_payment_option,
                payment_method=db_payment_method
            )

            # Automatic discount (Base price - standard duration total)
            auto_discount = base_price - booking.total_price
            
            # Manual discount
            manual_discount = serializer.validated_data.get('manual_discount', Decimal('0.00'))
            
            # Recalculate total amount
            total_amount = max(Decimal('0.00'), base_price - auto_discount - manual_discount)
            booking.total_price = total_amount
            
            # Advance amount
            advance_amount = serializer.validated_data.get('advance_amount', Decimal('0.00'))
            
            # Balance amount
            balance_amount = max(Decimal('0.00'), total_amount - advance_amount)
            
            # Update payment status
            if advance_amount >= total_amount and total_amount > 0:
                booking.payment_status = 'paid'
            elif advance_amount > 0:
                booking.payment_status = 'partial'
            else:
                booking.payment_status = 'unpaid'
            
            booking.save(update_fields=['total_price', 'payment_status'])

            # Save customer details to User profile for future bookings
            license_val = serializer.validated_data.get('driving_license_no', '')
            passport_val = serializer.validated_data.get('passport_no', '')
            user_updated = False
            if license_val and getattr(user, 'driving_license_no', '') != license_val:
                user.driving_license_no = license_val
                user_updated = True
            if passport_val and getattr(user, 'passport_no', '') != passport_val:
                user.passport_no = passport_val
                user_updated = True
            if user_updated:
                user.save()

            # Create RentalContract record
            contract = RentalContract.objects.create(
                booking=booking,
                customer_name=user.get_full_name() or user.username,
                customer_address=user.address or "Office Address",
                customer_phone=user.phone_number or "N/A",
                nationality=user.nationality or "Nepali",
                driving_license_no=serializer.validated_data.get('driving_license_no', ''),
                passport_no=serializer.validated_data.get('passport_no', ''),
                vehicle_model=f"{bike.brand} {bike.name}",
                vehicle_number=bike.vehicle_number or "N/A",
                vehicle_color=bike.color or "",
                chassis_no=bike.chassis_no or "",
                engine_no=bike.engine_no or "",
                guarantor_name=serializer.validated_data.get('guarantor_name', ''),
                guarantor_phone=serializer.validated_data.get('guarantor_phone', ''),
                guarantor_address=serializer.validated_data.get('guarantor_address', ''),
                helmet=serializer.validated_data.get('helmet', True),
                bungy_cord=serializer.validated_data.get('bungy_cord', False),
                maps=serializer.validated_data.get('maps', False),
                deposit_passport=serializer.validated_data.get('deposit_passport', False),
                deposit_citizenship=serializer.validated_data.get('deposit_citizenship', False),
                deposit_id_card=serializer.validated_data.get('deposit_id_card', False),
                deposit_other=serializer.validated_data.get('deposit_other', ''),
                rate_per_day=bike.price_per_day,
                total_amount=total_amount,
                discount_amount=auto_discount,
                manual_discount=manual_discount,
                advance_amount=advance_amount,
                balance_amount=balance_amount,
                remarks="Created via Mobile Admin App"
            )

            # Create Payment record if advance > 0
            if advance_amount > 0:
                Payment.objects.create(
                    booking=booking,
                    amount=advance_amount,
                    payment_method=db_payment_method,
                    status='completed' if booking.payment_status == 'paid' else 'partial'
                )

            # Create Invoice record
            invoice, created = Invoice.objects.get_or_create(
                booking=booking,
                defaults={'invoice_number': f"INV-{booking.id}-{booking.created_at.strftime('%Y%m%d')}"}
            )

            # --- Email both PDFs to the customer ---
            customer_email = user.email
            # Only send if email is real (not the dummy placeholder)
            if customer_email and '@example.com' not in customer_email:
                try:
                    payment_obj = None
                    try:
                        payment_obj = booking.payment
                    except Exception:
                        pass

                    invoice_ctx = {
                        'booking': booking,
                        'invoice': invoice,
                        'payment': payment_obj,
                        'base_url': request.build_absolute_uri('/')
                    }
                    invoice_pdf_bytes = _generate_pdf_bytes('admin_panel/invoice_pdf.html', invoice_ctx)

                    contract_ctx = {'contract': contract}
                    contract_pdf_bytes = _generate_pdf_bytes('admin_panel/contract_pdf.html', contract_ctx)

                    email = EmailMessage(
                        subject=f'EasyMoto – Your Rental Invoice & Agreement ({invoice.invoice_number})',
                        body=(
                            f'Dear {user.get_full_name() or user.username},\n\n'
                            f'Thank you for choosing EasyMoto Rental Service!\n\n'
                            f'Please find your rental Invoice and Agreement attached to this email.\n'
                            f'Invoice Number: {invoice.invoice_number}\n'
                            f'Vehicle: {bike.brand} {bike.name}\n'
                            f'Period: {start_date.date()} to {end_date.date()} ({duration_days} days)\n'
                            f'Total Amount: Rs. {total_amount}\n'
                            f'Advance Paid: Rs. {advance_amount}\n'
                            f'Balance Due: Rs. {balance_amount}\n\n'
                            f'We look forward to serving you.\n\n'
                            f'EasyMoto Rental Service Pvt. Ltd.\n'
                            f'Ph: 9860702780'
                        ),
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        to=[customer_email],
                    )
                    if invoice_pdf_bytes:
                        email.attach(f'Invoice_{invoice.invoice_number}.pdf', invoice_pdf_bytes, 'application/pdf')
                    if contract_pdf_bytes:
                        email.attach(f'Contract_{contract.contract_number}.pdf', contract_pdf_bytes, 'application/pdf')
                    email.send(fail_silently=True)
                except Exception as e:
                    print(f'Email dispatch error: {e}')

            # --- Staff Activity Log ---
            # Record this booking with the staff member who created it
            staff_user = request.user
            staff_name = staff_user.get_full_name() or staff_user.username
            customer_name = user.get_full_name() or user.username
            bike_label = f"{bike.brand} {bike.name}"
            StaffActivityLog.objects.create(
                staff_user=staff_user,
                action='walk_in_booking',
                description=(
                    f"{staff_name} created a walk-in booking for {customer_name} "
                    f"({user.phone_number}) on {bike_label} "
                    f"from {start_date.date()} to {end_date.date()} "
                    f"(Rs. {total_amount})."
                ),
                booking=booking,
                is_read=False,
            )

            return Response({
                "detail": "Booking & Contract created successfully.",
                "booking_id": booking.id,
                "contract_id": contract.id,
                "total_price": float(booking.total_price),
                "advance_amount": float(advance_amount),
                "balance_amount": float(balance_amount),
                "invoice_number": invoice.invoice_number
            }, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

def _generate_pdf_bytes(template_name, context):
    """Render a Django template and return a BytesIO of the PDF, or None on error."""
    tmpl = get_template(template_name)
    html = tmpl.render(context)
    buf = BytesIO()
    result = pisa.pisaDocument(BytesIO(html.encode('UTF-8')), buf)
    if not result.err:
        return buf.getvalue()
    return None

class MarkBookingPaidView(APIView):
    permission_classes = [IsStaffOrSuperuser]

    def post(self, request, pk):
        try:
            booking = Booking.objects.get(id=pk)
            booking.payment_status = 'paid'
            booking.save()
            return Response({"detail": "Booking marked as paid successfully."}, status=status.HTTP_200_OK)
        except Booking.DoesNotExist:
            return Response({"detail": "Booking not found."}, status=status.HTTP_404_NOT_FOUND)

class AdminMaintenanceCreateView(APIView):
    permission_classes = [IsStaffOrSuperuser]

    def post(self, request, pk):
        try:
            bike = Bike.objects.get(id=pk)
        except Bike.DoesNotExist:
            return Response({"detail": "Bike not found."}, status=status.HTTP_404_NOT_FOUND)

        serializer = MaintenanceRecordSerializer(data=request.data)
        if serializer.is_valid():
            # Automatically calculate next_maintenance_date (e.g., 3 months from now) if not provided
            maintenance_date = serializer.validated_data.get('date', timezone.now().date())
            next_date = maintenance_date + timedelta(days=90)
            
            serializer.save(bike=bike)
            
            # Update the bike's next maintenance date
            bike.next_maintenance_date = next_date
            bike.save()
            
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class AdminBikeBookingHistoryView(generics.ListAPIView):
    serializer_class = BookingSerializer
    permission_classes = [IsStaffOrSuperuser]

    def get_queryset(self):
        bike_id = self.kwargs['pk']
        return Booking.objects.filter(bike_id=bike_id).order_by('-created_at')

class UpcomingMaintenanceAlertsView(APIView):
    permission_classes = [IsStaffOrSuperuser]

    def get(self, request):
        now_date = timezone.now().date()
        # Notify if next maintenance is within 1 day or overdue
        target_date = now_date + timedelta(days=1)
        
        bikes_needing_maintenance = Bike.objects.filter(
            next_maintenance_date__lte=target_date
        ).order_by('next_maintenance_date')
        
        from .serializers import BikeSerializer
        serializer = BikeSerializer(bikes_needing_maintenance, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

class AdminCustomerListView(generics.ListAPIView):
    queryset = User.objects.filter(is_staff=False, is_superuser=False).prefetch_related('bookings', 'bookings__bike').order_by('-date_joined')
    serializer_class = CustomerDetailSerializer
    permission_classes = [IsStaffOrSuperuser]

class AdminBookingInvoiceView(APIView):
    authentication_classes = [QueryParamJWTAuthentication]
    permission_classes = [IsStaffOrSuperuser]

    def get(self, request, pk):
        from django.http import HttpResponse
        from django.shortcuts import get_object_or_404
        from payment.models import Invoice

        booking = get_object_or_404(Booking, id=pk)

        invoice, _ = Invoice.objects.get_or_create(
            booking=booking,
            defaults={'invoice_number': f"INV-{booking.id}-{booking.created_at.strftime('%Y%m%d')}"}
        )

        try:
            payment = booking.payment
        except Exception:
            payment = None

        context = {
            'booking': booking,
            'invoice': invoice,
            'payment': payment,
            'base_url': request.build_absolute_uri('/')
        }

        pdf_bytes = _generate_pdf_bytes('admin_panel/invoice_pdf.html', context)
        if pdf_bytes:
            from django.http import HttpResponse
            response = HttpResponse(pdf_bytes, content_type='application/pdf')
            filename = f"Invoice_{invoice.invoice_number}.pdf"
            response['Content-Disposition'] = f'inline; filename="{filename}"'
            return response

        return Response({"detail": "Error generating PDF"}, status=status.HTTP_400_BAD_REQUEST)


class AdminBookingContractPDFView(APIView):
    """Serve the full rental agreement (contract + bill) as a PDF for a given booking."""
    authentication_classes = [QueryParamJWTAuthentication]
    permission_classes = [IsStaffOrSuperuser]

    def get(self, request, pk):
        from django.http import HttpResponse
        from django.shortcuts import get_object_or_404
        from admin_panel.models import RentalContract

        booking = get_object_or_404(Booking, id=pk)

        try:
            contract = booking.contract
        except Exception:
            from decimal import Decimal
            duration_days = (booking.end_date - booking.start_date).days + 1
            base_price = booking.bike.price_per_day * Decimal(duration_days)
            auto_discount = base_price - booking.total_price
            
            contract = RentalContract.objects.create(
                booking=booking,
                customer_name=booking.user.get_full_name() or booking.user.username,
                customer_address=getattr(booking.user, 'address', '') or "N/A",
                customer_phone=getattr(booking.user, 'phone_number', '') or "N/A",
                nationality=getattr(booking.user, 'nationality', '') or "Nepali",
                driving_license_no="",
                passport_no="",
                vehicle_model=f"{booking.bike.brand} {booking.bike.name}",
                vehicle_number=booking.bike.vehicle_number or "N/A",
                vehicle_color=booking.bike.color or "",
                chassis_no=booking.bike.chassis_no or "",
                engine_no=booking.bike.engine_no or "",
                rate_per_day=booking.bike.price_per_day,
                total_amount=booking.total_price,
                discount_amount=auto_discount,
                manual_discount=Decimal('0.00'),
                advance_amount=booking.total_price if booking.payment_status == 'paid' else Decimal('0.00'),
                balance_amount=Decimal('0.00') if booking.payment_status == 'paid' else booking.total_price,
                remarks="Auto-generated contract for online booking"
            )

        pdf_bytes = _generate_pdf_bytes('admin_panel/contract_pdf.html', {'contract': contract})
        if pdf_bytes:
            response = HttpResponse(pdf_bytes, content_type='application/pdf')
            filename = f"Contract_{contract.contract_number}.pdf"
            response['Content-Disposition'] = f'inline; filename="{filename}"'
            return response

        return Response({"detail": "Error generating contract PDF"}, status=status.HTTP_400_BAD_REQUEST)


class StaffActivityLogListView(APIView):
    """Admin-only view to list all staff activity logs (with optional ?unread=1 filter)."""
    permission_classes = [IsStaffOrSuperuser]

    def get(self, request):
        if not request.user.is_superuser:
            return Response(
                {"detail": "Only administrators can view activity logs."},
                status=status.HTTP_403_FORBIDDEN
            )
        unread_only = request.query_params.get('unread', '0') == '1'
        qs = StaffActivityLog.objects.select_related('staff_user', 'booking')
        if unread_only:
            qs = qs.filter(is_read=False)
        logs = []
        for log in qs[:100]:
            staff_name = (
                log.staff_user.get_full_name() or log.staff_user.username
                if log.staff_user else 'Unknown Staff'
            )
            logs.append({
                'id': log.id,
                'action': log.action,
                'action_label': log.get_action_display(),
                'staff_name': staff_name,
                'description': log.description,
                'booking_id': log.booking_id,
                'is_read': log.is_read,
                'timestamp': log.timestamp.isoformat(),
            })
        return Response(logs)


class MarkNotificationsReadView(APIView):
    """Admin marks all (or specific) staff activity notifications as read."""
    permission_classes = [IsStaffOrSuperuser]

    def post(self, request):
        if not request.user.is_superuser:
            return Response(
                {"detail": "Only administrators can mark notifications as read."},
                status=status.HTTP_403_FORBIDDEN
            )
        # Optional: pass {"ids": [1, 2, 3]} to mark specific ones; otherwise marks all
        ids = request.data.get('ids', None)
        qs = StaffActivityLog.objects.filter(is_read=False)
        if ids:
            qs = qs.filter(id__in=ids)
        count = qs.update(is_read=True)
        return Response({"detail": f"{count} notification(s) marked as read."})
