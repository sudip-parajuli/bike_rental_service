from django import forms
from .models import Bike
from datetime import datetime

class BikeOwnerCreateForm(forms.ModelForm):
    class Meta:
        model = Bike
        exclude = ['is_approved', 'is_featured', 'availability_status', 'owner', 'created_at', 'updated_at', 'average_rating', 'slug']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Name of the bike (e.g., Honda Activa)'}),
            'type': forms.Select(attrs={'class': 'form-control', 'placeholder': 'Type of bike'}),
            'brand': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Brand of the bike'}),
            'model_year': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Year of manufacture'}),
            'mileage': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Mileage of the bike'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Detailed description of the bike'}),
            'price_per_day': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Rental price per day'}),
            'image': forms.FileInput(attrs={'class': 'form-control', 'placeholder': 'Image of the bike'}),
            'engine_type': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Type of engine (e.g., 4-stroke, 2-stroke)'}),
            'displacement': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Engine displacement (e.g., 125 cc)'}),
            'max_power': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Maximum power output (e.g., 8.5 hp)'}),
            'torque': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Torque output (e.g., 10 Nm)'}),
            'transmission': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Transmission type (e.g., Automatic, 5-speed manual)'}),
            'brakes': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Brake system (e.g., Disc/Drum)'}),
            'dimensions': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Bike dimensions (e.g., 1800 x 700 x 1100 mm)'}),
            'fuel_capacity': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Fuel tank capacity in liters (e.g., 5.3 L)'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Mark required fields
        self.fields['name'].required = True
        self.fields['type'].required = True
        self.fields['price_per_day'].required = True
        self.fields['image'].required = True

    def clean_model_year(self):
        model_year = self.cleaned_data.get('model_year')
        if model_year:
            current_year = datetime.now().year
            if model_year < 2000 or model_year > current_year:
                raise forms.ValidationError("Invalid model year.")
        return model_year

    def clean_price_per_day(self):
        price = self.cleaned_data['price_per_day']
        if price <= 0:
            raise forms.ValidationError("Price per day must be greater than zero.")
        return price

    def clean_image(self):
        image = self.cleaned_data.get('image')
        if image:
            if image.size > 5 * 1024 * 1024:  # 5MB limit
                raise forms.ValidationError("Image file size must not exceed 5MB.")
            if not image.name.lower().endswith(('.png', '.jpg', '.jpeg')):
                raise forms.ValidationError("Only PNG, JPG, or JPEG images are allowed.")
        return image

    def clean_description(self):
        description = self.cleaned_data.get('description')
        from django.utils.html import escape
        return escape(description) if description else description

    def clean_mileage(self):
        mileage = self.cleaned_data.get('mileage')
        if mileage is not None and mileage < 0:
            raise forms.ValidationError("Mileage cannot be negative.")
        return mileage

    def clean_fuel_capacity(self):
        fuel_capacity = self.cleaned_data.get('fuel_capacity')
        if fuel_capacity is not None and fuel_capacity < 0:
            raise forms.ValidationError("Fuel capacity cannot be negative.")
        return fuel_capacity