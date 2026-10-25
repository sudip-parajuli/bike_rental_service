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
from .rental_views import StaffPagination


from .permissions import IsStaffOrSuperuser


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
    pagination_class = StaffPagination
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
        from .operations import customer_for_phone
        from admin_panel.models import RentalContract
        user = customer_for_phone(request.query_params.get('phone', ''))
        if not user:
            return Response({'detail': 'Customer not found.'}, status=404)
        contract = RentalContract.objects.filter(booking__user=user).order_by('-created_at').first()
        return Response({'id': user.pk, 'user_id': user.pk, 'full_name': user.get_full_name() or user.username,
            'phone_number': user.phone_number, 'email': user.email, 'nationality': user.nationality,
            'driving_license_no': contract.driving_license_no if contract else (user.driving_license_no or ''),
            'passport_no': contract.passport_no if contract else (user.passport_no or '')})

    def post(self, request):
        from .operations import customer_for_phone, audit
        serializer = WalkInCustomerSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        values = serializer.validated_data
        user = customer_for_phone(values['phone_number'])
        created = user is None
        if created:
            names = values['full_name'].split(' ', 1)
            user = User(username='walkin_' + get_random_string(18), first_name=names[0],
                last_name=names[1] if len(names) > 1 else '', phone_number=values['phone_number'],
                email=values.get('email', ''), nationality=values['nationality'])
            user.set_unusable_password()
            user.save()
            audit(request.user, None, 'customer_created', f'Created customer record #{user.pk}.')
        return Response({'detail': 'Customer created.' if created else 'Existing customer selected.',
            'user_id': user.pk, 'phone_number': user.phone_number, 'full_name': user.get_full_name()}, status=201 if created else 200)

class WalkInBookingCreateView(APIView):
    permission_classes = [IsStaffOrSuperuser]

    def post(self, request):
        serializer = WalkInBookingSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        from .rental_creation import create_walkin
        return Response(create_walkin(request.user, serializer.validated_data), status=201)

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
        from .operations import mark_fully_paid
        from .rental_views import ReturnSerializer
        version = ReturnSerializer(data=request.data)
        version.is_valid(raise_exception=True)
        booking = mark_fully_paid(pk, request.user, version.validated_data['expected_updated_at'])
        return Response(BookingSerializer(booking).data)

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
    pagination_class = StaffPagination
    queryset = User.objects.filter(is_staff=False, is_superuser=False).prefetch_related('bookings', 'bookings__bike').order_by('-date_joined')
    serializer_class = CustomerDetailSerializer
    permission_classes = [IsStaffOrSuperuser]

class AdminBookingInvoiceView(APIView):
    authentication_classes = [JWTAuthentication]
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
    authentication_classes = [JWTAuthentication]
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
