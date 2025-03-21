from django import forms

class BookingForm(forms.Form):
    start_date = forms.DateTimeField(
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        required=True,
    )
    end_date = forms.DateTimeField(
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        required=True,
    )
    pickup_location = forms.ChoiceField(
        choices=[
            ("Budhanilkantha Bus Station", "Budhanilkantha Bus Station"),
            ("Park village Opposite", "Park village Opposite"),
        ],
        required=True,
    )
    payment_option = forms.ChoiceField(
        choices=[
            ("full_online", "Full Payment Online"),
            ("partial_online", "Partial Payment Online"),
            ("cash_on_delivery", "Cash on Delivery"),
        ],
        required=True,
    )
    bike = forms.IntegerField(widget=forms.HiddenInput())