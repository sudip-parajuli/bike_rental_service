from django import forms
from .models import BikeOwnerRequest
from django.utils import timezone

class BikeOwnerRequestForm(forms.ModelForm):
    class Meta:
        model = BikeOwnerRequest
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