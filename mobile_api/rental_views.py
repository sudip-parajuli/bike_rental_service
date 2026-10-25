import re
from decimal import Decimal
from datetime import datetime, time, timedelta

from django.conf import settings
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.crypto import constant_time_compare
from rest_framework import generics, serializers
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from bookings.models import Booking
from .models import StaffDevice
from .permissions import IsStaffOrSuperuser
from .serializers import BookingSerializer
from .operations import NEPAL, update_rental, return_rental, whatsapp_draft, audit


def rental_queryset():
    return Booking.objects.filter(is_active=True).select_related('bike', 'user', 'payment', 'contract', 'rental_state')


class StaffPagination(PageNumberPagination):
    page_size = 25
    page_size_query_param = 'page_size'
    max_page_size = 100


def day_bounds(now):
    begin = timezone.make_aware(datetime.combine(timezone.localdate(now, NEPAL), time.min), NEPAL)
    return begin, begin + timedelta(days=1)


class RentalUpdateSerializer(serializers.Serializer):
    expected_updated_at = serializers.DateTimeField()
    start_date = serializers.DateTimeField(required=False)
    end_date = serializers.DateTimeField(required=False)
    status = serializers.ChoiceField(choices=['pending', 'confirmed', 'cancelled'], required=False)
    notes = serializers.CharField(max_length=2000, required=False, allow_blank=True)
    deposit_amount = serializers.DecimalField(max_digits=10, decimal_places=2, min_value=Decimal('0'), required=False)
    deposit_returned = serializers.BooleanField(required=False)
    recalculate_price = serializers.BooleanField(default=False)


class ReturnSerializer(serializers.Serializer):
    expected_updated_at = serializers.DateTimeField()
    deposit_returned = serializers.BooleanField(required=False)
    notes = serializers.CharField(max_length=2000, required=False, allow_blank=True)


class StaffMeView(APIView):
    permission_classes = [IsStaffOrSuperuser]

    def get(self, request):
        user = request.user
        return Response({'id': user.pk, 'username': user.username, 'full_name': user.get_full_name() or user.username,
                         'email': user.email, 'is_staff': user.is_staff, 'is_superuser': user.is_superuser,
                         'timezone': 'Asia/Kathmandu', 'reminders_enabled': settings.RENTAL_REMINDERS_ENABLED})


class RentalBookingListView(generics.ListAPIView):
    permission_classes = [IsStaffOrSuperuser]
    serializer_class = BookingSerializer
    pagination_class = StaffPagination

    def get_queryset(self):
        query = rental_queryset()
        search = self.request.query_params.get('search', '').strip()[:100]
        if search:
            query = query.filter(Q(bike__name__icontains=search) | Q(bike__vehicle_number__icontains=search)
                                 | Q(user__first_name__icontains=search) | Q(user__last_name__icontains=search)
                                 | Q(user__phone_number__icontains=search))
        status = self.request.query_params.get('status')
        if status in ('pending', 'confirmed', 'completed', 'cancelled'):
            query = query.filter(status=status)
        due = self.request.query_params.get('due')
        now = timezone.now()
        begin, finish = day_bounds(now)
        if due in ('overdue', 'today', 'soon', 'upcoming', 'active'):
            query = query.filter(status='confirmed')
            if due == 'overdue':
                query = query.filter(end_date__lte=now)
            elif due == 'today':
                query = query.filter(end_date__gte=begin, end_date__lt=finish)
            elif due == 'soon':
                query = query.filter(end_date__gt=now, end_date__lte=now + timedelta(hours=24))
            elif due == 'upcoming':
                query = query.filter(start_date__gt=now)
            else:
                query = query.filter(start_date__lte=now)
        return query.order_by('end_date', 'pk')


class RentalBookingDetailView(APIView):
    permission_classes = [IsStaffOrSuperuser]

    def get(self, request, pk):
        return Response(BookingSerializer(get_object_or_404(rental_queryset(), pk=pk)).data)

    def patch(self, request, pk):
        data = RentalUpdateSerializer(data=request.data)
        data.is_valid(raise_exception=True)
        booking = update_rental(pk, request.user, data.validated_data)
        return Response(BookingSerializer(booking).data)


class RentalReturnView(APIView):
    permission_classes = [IsStaffOrSuperuser]

    def post(self, request, pk):
        data = ReturnSerializer(data=request.data)
        data.is_valid(raise_exception=True)
        return Response(BookingSerializer(return_rental(pk, request.user, data.validated_data)).data)


class RentalReminderDraftView(APIView):
    permission_classes = [IsStaffOrSuperuser]

    def post(self, request, pk):
        booking = get_object_or_404(rental_queryset(), pk=pk, status='confirmed')
        draft = whatsapp_draft(booking)
        # Opening a draft is not evidence of delivery; never mark it as sent.
        audit(request.user, booking, 'customer_reminder', f'WhatsApp reminder prepared for rental #{booking.pk}; delivery is not verified.')
        return Response(draft)


class RentalBoardView(APIView):
    permission_classes = [IsStaffOrSuperuser]

    def get(self, request):
        now = timezone.now()
        begin, finish = day_bounds(now)
        query = rental_queryset().filter(status='confirmed')
        alerts = query.filter(end_date__lte=now + timedelta(hours=24)).order_by('end_date')[:50]
        return Response({'server_now': now.isoformat(), 'timezone': 'Asia/Kathmandu',
            'overdue': query.filter(end_date__lte=now).count(),
            'due_today': query.filter(end_date__gte=begin, end_date__lt=finish).count(),
            'on_rent': query.filter(start_date__lte=now).count(),
            'pickups_today': query.filter(start_date__gte=begin, start_date__lt=finish).count(),
            'upcoming': query.filter(start_date__gt=now).count(),
            'pending': rental_queryset().filter(status='pending').count(),
            'alerts': BookingSerializer(alerts, many=True).data,
            'reminders_enabled': settings.RENTAL_REMINDERS_ENABLED})


class RentalDeviceView(APIView):
    permission_classes = [IsStaffOrSuperuser]

    def post(self, request):
        token, platform = request.data.get('token', ''), request.data.get('platform')
        if not isinstance(token, str) or not re.fullmatch(r'(?:ExponentPushToken|ExpoPushToken)\[[A-Za-z0-9_-]{10,200}\]', token) or platform not in ('android', 'ios'):
            raise serializers.ValidationError('A valid Expo push token and mobile platform are required.')
        StaffDevice.objects.update_or_create(token=token, defaults={'user': request.user, 'platform': platform, 'active': True})
        return Response({'registered': True})

    def delete(self, request):
        StaffDevice.objects.filter(user=request.user, token=request.data.get('token', '')).update(active=False)
        return Response(status=204)


class RentalReminderRunView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        secret = settings.RENTAL_CRON_SECRET
        if not secret or len(secret) < 32 or not constant_time_compare(request.headers.get('X-Rental-Cron-Secret', ''), secret):
            return Response({'detail': 'Not authorized.'}, status=403)
        if not settings.RENTAL_REMINDERS_ENABLED:
            return Response({'detail': 'Server reminders are disabled.'}, status=503)
        from .reminders import dispatch_reminders
        return Response(dispatch_reminders())
