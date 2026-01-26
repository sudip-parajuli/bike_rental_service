from django import forms
from django.contrib.auth import get_user_model
from bikes.models import Bike
from bookings.models import Booking
from django.apps import apps
from django.utils.translation import gettext_lazy as _

User = get_user_model()

class AdminUserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'is_active', 'is_staff', 'is_superuser', 'is_host']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_staff': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_superuser': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_host': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

class AdminBikeForm(forms.ModelForm):
    class Meta:
        model = Bike
        fields = '__all__'
        exclude = ['created_at', 'updated_at', 'slug', 'average_rating']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'brand': forms.TextInput(attrs={'class': 'form-control'}),
            'model_year': forms.NumberInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'price_per_day': forms.NumberInput(attrs={'class': 'form-control'}),
            'availability_status': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_approved': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

class AdminBookingForm(forms.ModelForm):
    payment_status = forms.ChoiceField(
        choices=Booking.PAYMENT_STATUS_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    amount_paid = forms.DecimalField(
        required=False, 
        max_digits=10, 
        decimal_places=2,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Enter amount if partial'})
    )

    class Meta:
        model = Booking
        fields = ['status', 'payment_status', 'payment_method', 'start_date', 'end_date', 'total_price']
        widgets = {
            'status': forms.Select(attrs={'class': 'form-select'}),
            'payment_method': forms.Select(attrs={'class': 'form-select'}),
            'start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'end_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'total_price': forms.NumberInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            # Pre-fill amount_paid if a payment exists
            from payment.models import Payment
            try:
                payment = Payment.objects.get(booking=self.instance)
                self.fields['amount_paid'].initial = payment.amount
            except Payment.DoesNotExist:
                pass

    def save(self, commit=True):
        booking = super().save(commit=False)
        
        if commit:
            booking.save()
            
            # Sync with Payment model
            from payment.models import Payment
            # Determine payment status mapping
            payment_status_map = {
                'paid': 'completed',
                'partial': 'partial',
                'unpaid': 'pending'
            }
            new_payment_status = payment_status_map.get(booking.payment_status, 'pending')
            
            payment, created = Payment.objects.get_or_create(
                booking=booking,
                defaults={
                    'amount': booking.total_price if booking.payment_status == 'paid' else (self.cleaned_data.get('amount_paid') or 0),
                    'payment_method': booking.payment_method or 'cash_on_delivery',
                    'status': new_payment_status
                }
            )
            
            # Update existing payment if needed
            if not created:
                if booking.payment_status == 'paid':
                    payment.amount = booking.total_price
                    payment.status = 'completed'
                elif booking.payment_status == 'partial':
                    # Only update amount if explicitly provided, otherwise keep existing
                    if self.cleaned_data.get('amount_paid'):
                         payment.amount = self.cleaned_data.get('amount_paid')
                    payment.status = 'partial'
                else:
                    payment.status = 'pending'
                
                if booking.payment_method:
                     payment.payment_method = booking.payment_method
                
                payment.save()
                
        return booking

class WalkInBookingForm(forms.Form):
    # Customer Details
    nationality = forms.CharField(label="Nationality", max_length=100, widget=forms.TextInput(attrs={'class': 'form-control', 'id': 'nationalityInput', 'readonly': 'readonly'}))
    phone_number = forms.CharField(label="Phone Number", max_length=20, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+977...', 'id': 'phoneNumberInput'}))
    full_name = forms.CharField(label="Customer Name", max_length=150, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter full name'}))
    email = forms.EmailField(label="Email (Optional)", required=False, widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'email@example.com (optional)'}))
    
    # Booking Details
    bike = forms.ModelChoiceField(queryset=Bike.objects.filter(availability_status=True), widget=forms.Select(attrs={'class': 'form-select'}))
    start_date = forms.DateTimeField(widget=forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}))
    end_date = forms.DateTimeField(widget=forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}))

    def clean_phone_number(self):
        phone = self.cleaned_data['phone_number']
        return phone

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get("start_date")
        end_date = cleaned_data.get("end_date")
        bike = cleaned_data.get("bike")

        if start_date and end_date:
            if end_date < start_date:
                raise forms.ValidationError("End date must be after or equal to start date.")
            
            if bike:
                overlapping = Booking.objects.filter(
                    bike=bike,
                    start_date__lt=end_date,
                    end_date__gt=start_date,
                    status='confirmed'
                ).exists()
                if overlapping:
                    raise forms.ValidationError(f"The bike {bike.name} is already booked for these dates.")
        return cleaned_data

class RentalContractForm(forms.ModelForm):
    class Meta:
        model = apps.get_model('admin_panel', 'RentalContract')
        exclude = ('booking', 'contract_number', 'created_at')
        widgets = {
            # Customer Details
            'customer_name': forms.TextInput(attrs={'class': 'form-control'}),
            'customer_address': forms.TextInput(attrs={'class': 'form-control'}),
            'customer_phone': forms.TextInput(attrs={'class': 'form-control'}),
            'nationality': forms.TextInput(attrs={'class': 'form-control'}),
            'driving_license_no': forms.TextInput(attrs={'class': 'form-control'}),
            'passport_no': forms.TextInput(attrs={'class': 'form-control'}),
            
            # Vehicle Details
            'vehicle_model': forms.TextInput(attrs={'class': 'form-control'}),
            'vehicle_number': forms.TextInput(attrs={'class': 'form-control'}),
            'vehicle_color': forms.TextInput(attrs={'class': 'form-control'}),
            'chassis_no': forms.TextInput(attrs={'class': 'form-control'}),
            'engine_no': forms.TextInput(attrs={'class': 'form-control'}),
            
            # Guarantor
            'guarantor_name': forms.TextInput(attrs={'class': 'form-control'}),
            'guarantor_address': forms.TextInput(attrs={'class': 'form-control'}),
            'guarantor_phone': forms.TextInput(attrs={'class': 'form-control'}),
            
            # Checklist
            'helmet': forms.CheckboxInput(attrs={'class': 'form-check-input', 'checked': 'checked'}),
            'bungy_cord': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'maps': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            
            # Security Deposit
            'deposit_passport': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'deposit_citizenship': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'deposit_id_card': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'deposit_other': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Other deposit item...'}),
            
            # Financials
            'rate_per_day': forms.NumberInput(attrs={'class': 'form-control'}),
            'total_amount': forms.NumberInput(attrs={'class': 'form-control'}),
            'discount_amount': forms.NumberInput(attrs={'class': 'form-control', 'readonly': 'readonly'}),
            'manual_discount': forms.NumberInput(attrs={'class': 'form-control'}),
            'advance_amount': forms.NumberInput(attrs={'class': 'form-control'}),
            'balance_amount': forms.NumberInput(attrs={'class': 'form-control'}),
            'remarks': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'contract_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        }
