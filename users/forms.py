from django import forms
from .models import BikehostRequest, User
from django.utils import timezone
from django.contrib.auth.forms import UserCreationForm

class RegisterForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'modern-form-control', 'placeholder': 'Create a strong password'}))
    password_confirm = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'modern-form-control', 'placeholder': 'Confirm your password'}))
    email = forms.EmailField(widget=forms.EmailInput(attrs={'class': 'modern-form-control', 'placeholder': 'Enter your email'}))

    class Meta:
        model = User
        fields = ['username', 'email', 'password']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'modern-form-control', 'placeholder': 'Choose a username'}),
        }

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("Email is already registered.")
        return email

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        password_confirm = cleaned_data.get("password_confirm")

        if password and password_confirm and password != password_confirm:
            self.add_error('password_confirm', "Passwords do not match")
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password"])
        if commit:
            user.save()
        return user

class BikehostRequestForm(forms.ModelForm):
    class Meta:
        model = BikehostRequest
        fields = [
            'bike_make', 'bike_model', 'bike_year', 'bike_registration_number',
            'registration_certificate', 'insurance_certificate', 'id_proof', 'bike_photos'
        ]
        widgets = {
            'bike_make': forms.TextInput(attrs={'class': 'form-control'}),
            'bike_model': forms.TextInput(attrs={'class': 'form-control'}),
            'bike_year': forms.NumberInput(attrs={'class': 'form-control'}),
            'bike_registration_number': forms.TextInput(attrs={'class': 'form-control'}),
            'registration_certificate': forms.FileInput(attrs={'class': 'form-control'}),
            'insurance_certificate': forms.FileInput(attrs={'class': 'form-control'}),
            'id_proof': forms.FileInput(attrs={'class': 'form-control'}),
            'bike_photos': forms.FileInput(attrs={'class': 'form-control'}),
        }

    def clean_bike_year(self):
        bike_year = self.cleaned_data['bike_year']
        current_year = timezone.now().year
        if bike_year > current_year:
            raise forms.ValidationError("Bike year cannot be in the future.")
        if bike_year < current_year - 10:
            raise forms.ValidationError("Bike must be less than 10 years old.")
        return bike_year

    def clean_registration_certificate(self):
        file = self.cleaned_data.get('registration_certificate')
        if file:
            if file.size > 5 * 1024 * 1024:  # 5MB limit
                raise forms.ValidationError("File size must not exceed 5MB.")
            if not file.name.lower().endswith(('.pdf', '.jpg', '.jpeg', '.png')):
                raise forms.ValidationError("Only PDF, JPG, JPEG, or PNG files are allowed.")
        return file

    def clean_insurance_certificate(self):
        file = self.cleaned_data.get('insurance_certificate')
        if file:
            if file.size > 5 * 1024 * 1024:  # 5MB limit
                raise forms.ValidationError("File size must not exceed 5MB.")
            if not file.name.lower().endswith(('.pdf', '.jpg', '.jpeg', '.png')):
                raise forms.ValidationError("Only PDF, JPG, JPEG, or PNG files are allowed.")
        return file

    def clean_id_proof(self):
        file = self.cleaned_data.get('id_proof')
        if file:
            if file.size > 5 * 1024 * 1024:  # 5MB limit
                raise forms.ValidationError("File size must not exceed 5MB.")
            if not file.name.lower().endswith(('.pdf', '.jpg', '.jpeg', '.png')):
                raise forms.ValidationError("Only PDF, JPG, JPEG, or PNG files are allowed.")
        return file

    def clean_bike_photos(self):
        file = self.cleaned_data.get('bike_photos')
        if file:
            if file.size > 5 * 1024 * 1024:  # 5MB limit
                raise forms.ValidationError("Image file size must not exceed 5MB.")
            if not file.name.lower().endswith(('.jpg', '.jpeg', '.png')):
                raise forms.ValidationError("Only JPG, JPEG, or PNG images are allowed.")
        return file

class PhoneNumberForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['nationality', 'phone_number']
        widgets = {
            'nationality': forms.TextInput(attrs={'class': 'modern-form-control', 'placeholder': 'Select your nationality', 'id': 'nationalityInput'}),
            'phone_number': forms.TextInput(attrs={'class': 'modern-form-control', 'placeholder': 'Phone number', 'id': 'phoneNumberInput'})
        }

    def clean_phone_number(self):
        phone = self.cleaned_data.get('phone_number')
        if not phone:
            raise forms.ValidationError("Phone number is required.")
        return phone