from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import TemplateView, ListView, DetailView, CreateView, UpdateView, DeleteView, FormView
from django.contrib.messages.views import SuccessMessageMixin
from django.urls import reverse_lazy
from .forms import AdminUserForm, AdminBikeForm, AdminBookingForm
from rest_framework import viewsets
from rest_framework.permissions import IsAdminUser
from django.contrib.auth import get_user_model
from django.db import models
from django.contrib import messages
from django.http import HttpResponse
from django.template.loader import get_template
from xhtml2pdf import pisa
from io import BytesIO
from bikes.models import Bike
from bookings.models import Booking
from payment.models import Payment, Invoice
from testimonials.models import Testimonial
from .models import ContactMessage
from .serializers import ContactMessageSerializer

User = get_user_model()

class AdminDashboardHomeView(TemplateView):
    template_name = 'admin_panel/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['total_users'] = User.objects.count()
        context['active_bookings'] = Booking.objects.filter(status='confirmed').count()
        context['total_revenue'] = Payment.objects.filter(status='completed').aggregate(models.Sum('amount'))['amount__sum'] or 0
        context['recent_bookings'] = Booking.objects.order_by('-created_at')[:5]
        return context

class AdminUserListView(ListView):
    model = User
    template_name = 'admin_panel/user_list.html'
    context_object_name = 'users'
    paginate_by = 10

    def get_queryset(self):
        queryset = super().get_queryset()
        query = self.request.GET.get('q')
        if query:
            queryset = queryset.filter(
                models.Q(username__icontains=query) |
                models.Q(email__icontains=query) |
                models.Q(phone_number__icontains=query)
            )
        return queryset

class AdminUserDetailView(DetailView):
    model = User
    template_name = 'admin_panel/user_detail.html'
    context_object_name = 'user_obj'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.object
        context['bookings'] = Booking.objects.filter(user=user).order_by('-created_at')
        context['payments'] = Payment.objects.filter(booking__user=user).order_by('-created_at')
        context['contracts'] = RentalContract.objects.filter(booking__user=user).order_by('-created_at')
        return context

class AdminUserUpdateView(SuccessMessageMixin, UpdateView):
    model = User
    form_class = AdminUserForm
    template_name = 'admin_panel/form.html'
    success_url = reverse_lazy('admin_panel:user-list')
    success_message = "User updated successfully"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Edit User'
        return context

class AdminUserDeleteView(DeleteView):
    model = User
    template_name = 'admin_panel/confirm_delete.html'
    success_url = reverse_lazy('admin_panel:user-list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Delete User'
        context['item_name'] = self.object.username
        return context

class AdminBikeListView(ListView):
    model = Bike
    template_name = 'admin_panel/bike_list.html'
    context_object_name = 'bikes'
    paginate_by = 10

class AdminBikeCreateView(SuccessMessageMixin, CreateView):
    model = Bike
    form_class = AdminBikeForm
    template_name = 'admin_panel/form.html'
    success_url = reverse_lazy('admin_panel:bike-list')
    success_message = "Bike created successfully"

    def form_valid(self, form):
        form.instance.host = self.request.user # Admin creates it for themselves, or could be improved later
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Add New Bike'
        return context

class AdminBikeUpdateView(SuccessMessageMixin, UpdateView):
    model = Bike
    form_class = AdminBikeForm
    template_name = 'admin_panel/form.html'
    success_url = reverse_lazy('admin_panel:bike-list')
    success_message = "Bike updated successfully"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Edit Bike'
        return context

class AdminBikeDeleteView(DeleteView):
    model = Bike
    template_name = 'admin_panel/confirm_delete.html'
    success_url = reverse_lazy('admin_panel:bike-list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Delete Bike'
        context['item_name'] = f"{self.object.brand} {self.object.name}"
        return context

class AdminBookingListView(ListView):
    model = Booking
    template_name = 'admin_panel/booking_list.html'
    context_object_name = 'bookings'
    paginate_by = 10

class AdminBookingUpdateView(SuccessMessageMixin, UpdateView):
    model = Booking
    form_class = AdminBookingForm
    template_name = 'admin_panel/form.html'
    success_url = reverse_lazy('admin_panel:booking-list')
    success_message = "Booking updated successfully"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Edit Booking'
        return context

class AdminBookingDeleteView(DeleteView):
    model = Booking
    template_name = 'admin_panel/confirm_delete.html'
    success_url = reverse_lazy('admin_panel:booking-list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Delete Booking'
        context['item_name'] = f"Booking #{self.object.id}"
        return context

class AdminPaymentListView(ListView):
    model = Payment
    template_name = 'admin_panel/payment_list.html'
    context_object_name = 'payments'
    paginate_by = 10

class AdminTestimonialListView(ListView):
    model = Testimonial
    template_name = 'admin_panel/testimonial_list.html'
    context_object_name = 'testimonials'
    paginate_by = 10

def toggle_user_status(request, pk):
    user = get_object_or_404(User, pk=pk)
    user.is_active = not user.is_active
    user.save()
    messages.success(request, f"User {user.username} has been {'activated' if user.is_active else 'deactivated'}.")
    return redirect('admin_panel:user-list')

def approve_bike(request, pk):
    bike = get_object_or_404(Bike, pk=pk)
    bike.availability_status = True
    bike.save()
    messages.success(request, f"Bike {bike.brand} {bike.name} approved.")
    return redirect('admin_panel:bike-list')

def reject_bike(request, pk):
    bike = get_object_or_404(Bike, pk=pk)
    bike.availability_status = False
    bike.save()
    messages.success(request, f"Bike {bike.brand} {bike.name} rejected/hidden.")
    return redirect('admin_panel:bike-list')

def toggle_testimonial(request, pk):
    testimonial = get_object_or_404(Testimonial, pk=pk)
    testimonial.is_approved = not testimonial.is_approved
    testimonial.save()
    messages.success(request, f"Testimonial from {testimonial.user.username} {'approved' if testimonial.is_approved else 'hidden'}.")
    return redirect('admin_panel:testimonial-list')

def generate_invoice_pdf(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id)
    
    # Ensure invoice exists or create it
    invoice, created = Invoice.objects.get_or_create(
        booking=booking,
        defaults={'invoice_number': f"INV-{booking.id}-{booking.created_at.strftime('%Y%m%d')}"}
    )
    
    template = get_template('admin_panel/invoice_pdf.html')
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
    
    html = template.render(context)
    result = BytesIO()
    pdf = pisa.pisaDocument(BytesIO(html.encode("UTF-8")), result)
    
    if not pdf.err:
        response = HttpResponse(result.getvalue(), content_type='application/pdf')
        filename = f"Invoice_{invoice.invoice_number}.pdf"
        response['Content-Disposition'] = f'inline; filename="{filename}"'
        return response
    
    return HttpResponse("Error generating PDF", status=400)

class ContactMessageViewSet(viewsets.ModelViewSet):
    """
    Manage contact messages (create, list, retrieve, update, delete).

    * Requires: Admin authentication
    * Returns: Contact message data or list of messages
    """
    queryset = ContactMessage.objects.all()
    serializer_class = ContactMessageSerializer
    permission_classes = [IsAdminUser]
    throttle_scope = 'admin_contact_messages'  # Scoped to 50/day

from .models import RentalContract
from .forms import RentalContractForm, WalkInBookingForm

class AdminContractCreateView(CreateView):
    model = RentalContract
    form_class = RentalContractForm
    template_name = 'admin_panel/contract_form.html'
    
    def get_initial(self):
        initial = super().get_initial()
        booking_id = self.request.GET.get('booking_id')
        if booking_id:
            booking = get_object_or_404(Booking, id=booking_id)
            initial['booking'] = booking
            
            # 1. Auto-fill Customer Details (from previous contract if available)
            last_contract = RentalContract.objects.filter(booking__user=booking.user).order_by('-created_at').first()
            if last_contract:
                initial['customer_name'] = last_contract.customer_name
                initial['customer_address'] = last_contract.customer_address
                initial['customer_phone'] = last_contract.customer_phone
                initial['nationality'] = last_contract.nationality
                initial['driving_license_no'] = last_contract.driving_license_no
                initial['passport_no'] = last_contract.passport_no
            else:
                # Fallback to User profile
                initial['customer_name'] = booking.user.get_full_name() or booking.user.username
                initial['customer_email'] = booking.user.email
                initial['customer_phone'] = booking.user.phone_number
                initial['nationality'] = getattr(booking.user, 'nationality', '')

            # 2. Auto-fill Vehicle Details (from Bike model)
            initial['vehicle_model'] = f"{booking.bike.brand} {booking.bike.name}"
            initial['vehicle_number'] = booking.bike.vehicle_number or "N/A"
            initial['vehicle_color'] = booking.bike.color or ""
            initial['chassis_no'] = booking.bike.chassis_no or ""
            initial['engine_no'] = booking.bike.engine_no or ""

            # 3. Auto-fill Financials
            initial['rate_per_day'] = booking.bike.price_per_day
            
            # Calculate Discount
            # Logic: Base Price - Total Price (from booking logic) = Discount
            duration_days = booking.duration_days
            base_price = booking.bike.price_per_day * duration_days
            # booking.total_price is already calculated with discount in Booking.save()
            # If not, we calculate it here
            if not booking.total_price:
                booking.total_price = booking.calculate_total_price()
            
            discount = base_price - booking.total_price
            initial['discount_amount'] = discount
            initial['total_amount'] = booking.total_price
            initial['balance_amount'] = booking.total_price # Default balance is full amount
        return initial

    def form_valid(self, form):
        booking_id = self.request.GET.get('booking_id')
        if booking_id:
            booking = get_object_or_404(Booking, id=booking_id)
            form.instance.booking = booking
            
        # Enforce math calculations to ensure manual discount is applied
        duration = form.instance.booking.duration_days if form.instance.booking else 1
        base_total = form.instance.rate_per_day * duration
        new_total = max(0, base_total - form.instance.discount_amount - form.instance.manual_discount)
        form.instance.total_amount = new_total
        form.instance.balance_amount = max(0, new_total - form.instance.advance_amount)
        
        response = super().form_valid(form)
        
        # Sync changes to Booking
        contract = self.object
        if contract.booking:
            booking = contract.booking
            if contract.total_amount != booking.total_price:
                booking.total_price = contract.total_amount
                booking.save(update_fields=['total_price'])
                try:
                    payment = booking.payment
                    if payment.status in ['completed', 'pending']:
                        payment.amount = booking.total_price
                        payment.save(update_fields=['amount'])
                except Exception:
                    pass
                    
        return response

    def get_success_url(self):
        return reverse_lazy('admin_panel:contract-print', kwargs={'pk': self.object.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Create Rental Contract'
        return context

class AdminContractUpdateView(UpdateView):
    model = RentalContract
    form_class = RentalContractForm
    template_name = 'admin_panel/contract_form.html'
    
    def form_valid(self, form):
        # Enforce math calculations to ensure manual discount is applied
        if form.instance.booking:
            duration = form.instance.booking.duration_days
            base_total = form.instance.rate_per_day * duration
            new_total = max(0, base_total - form.instance.discount_amount - form.instance.manual_discount)
            form.instance.total_amount = new_total
            form.instance.balance_amount = max(0, new_total - form.instance.advance_amount)
            
        response = super().form_valid(form)
        # Sync changes to Booking
        contract = self.object
        if contract.booking:
            booking = contract.booking
            # Update booking total price if contract total amount changed
            if contract.total_amount != booking.total_price:
                booking.total_price = contract.total_amount
                booking.save(update_fields=['total_price'])
                
                # Also update Payment if it exists and was fully paid or needs adjustment
                try:
                    payment = booking.payment
                    if payment.status in ['completed', 'pending']:
                        payment.amount = booking.total_price
                        payment.save(update_fields=['amount'])
                except Exception:
                    pass
        return response

    def get_success_url(self):
        return reverse_lazy('admin_panel:contract-print', kwargs={'pk': self.object.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Edit Rental Contract'
        return context

class AdminContractPrintView(DetailView):
    model = RentalContract
    template_name = 'admin_panel/contract_print.html'
    context_object_name = 'contract'

class AdminContractListView(ListView):
    model = RentalContract
    template_name = 'admin_panel/contract_list.html'
    context_object_name = 'contracts'
    ordering = ['-created_at']
    paginate_by = 10

from .forms import WalkInBookingForm
from django.utils.crypto import get_random_string

class AdminWalkInBookingView(SuccessMessageMixin, FormView):
    template_name = 'admin_panel/walkin_form.html'
    form_class = WalkInBookingForm
    success_message = "Walk-in booking created successfully. Proceed to contract."

    def get_initial(self):
        initial = super().get_initial()
        phone = self.request.GET.get('phone')
        if phone:
            # Try to find user by phone (handling spaces)
            from django.db.models import Value
            from django.db.models.functions import Replace
            
            clean_phone = phone.replace(' ', '')
            user = User.objects.annotate(
                clean_phone=Replace('phone_number', models.Value(' '), models.Value(''))
            ).filter(clean_phone=clean_phone).first()
            
            if user:
                initial['nationality'] = user.nationality
                initial['phone_number'] = user.phone_number
                initial['full_name'] = user.get_full_name() or user.username
                initial['email'] = user.email
        return initial

    def form_valid(self, form):
        # Extract data
        nationality = form.cleaned_data['nationality']
        full_name = form.cleaned_data['full_name']
        phone_number = form.cleaned_data['phone_number']
        email = form.cleaned_data['email'] or f"{phone_number}@example.com" # Dummy email if not provided
        bike = form.cleaned_data['bike']
        start_date = form.cleaned_data['start_date']
        end_date = form.cleaned_data['end_date']

        # 1. Start Transaction
        # 2. Get or Create User
        # Robust lookup: Check by phone number first (unique field)
        user = User.objects.filter(phone_number=phone_number).first()
        
        if not user:
            # Create new user if not found
            user = User.objects.create_user(
                username=phone_number,
                email=email,
                password=get_random_string(8),
                first_name=full_name.split(' ')[0],
                last_name=' '.join(full_name.split(' ')[1:]) if ' ' in full_name else '',
                phone_number=phone_number,
                nationality=nationality,
                is_active=True
            )
            created = True
        else:
            created = False
            # Update existing user details if needed (optional)
            if not user.nationality:
                user.nationality = nationality
                user.save(update_fields=['nationality'])

            # 3. Create Booking
            booking = Booking.objects.create(
                user=user,
                bike=bike,
                start_date=start_date,
                end_date=end_date,
                pickup_location="Office",
                status='confirmed', # Auto-confirm
                payment_status='unpaid', # Payment not yet recorded
                payment_option='cash_on_delivery',
                payment_method='cash_on_delivery'
            )

        # 4. Redirect to Contract Create
        return redirect(f"{reverse_lazy('admin_panel:contract-create')}?booking_id={booking.id}")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'New Walk-in Booking'
        return context

from django.http import JsonResponse
from django.views import View
from django.db.models import Value
from django.db.models.functions import Replace

class AdminUserLookupView(View):
    def get(self, request, *args, **kwargs):
        phone = request.GET.get('phone')
        if phone:
            # Normalize input: remove spaces
            clean_input = phone.replace(' ', '')
            
            # Search DB: remove spaces from stored numbers for comparison
            user = User.objects.annotate(
                clean_phone=Replace('phone_number', Value(' '), Value(''))
            ).filter(clean_phone=clean_input).first()
            
            if user:
                return JsonResponse({
                    'found': True,
                    'full_name': user.get_full_name() or user.username,
                    'email': user.email,
                    'nationality': getattr(user, 'nationality', '') # Return nationality too
                })
        return JsonResponse({'found': False})


