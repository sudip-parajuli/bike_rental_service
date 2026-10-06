"""Date-aware WhatsApp enquiries; this does not create or confirm a booking."""
from urllib.parse import urlencode
from zoneinfo import ZoneInfo
from django import forms
from django.shortcuts import get_object_or_404, render
from django.http import Http404
from django.utils import timezone
from .models import Bike


def nepal_today():
    return timezone.localtime(timezone.now(), ZoneInfo('Asia/Kathmandu')).date()


class AvailabilityDatesForm(forms.Form):
    start = forms.DateField(label='Pickup date', widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}))
    end = forms.DateField(label='Return date', widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['min'] = nepal_today().isoformat()

    def clean(self):
        data = super().clean()
        start, end = data.get('start'), data.get('end')
        if start and start < nepal_today():
            self.add_error('start', 'Choose today or a future pickup date.')
        if start and end and end < start:
            self.add_error('end', 'The return date cannot be before pickup.')
        return data


def availability_request(request):
    try:
        bike_id = forms.IntegerField(min_value=1, max_value=9223372036854775807).clean(request.GET.get('bike'))
    except forms.ValidationError:
        raise Http404('Choose a public bike.')
    bike = get_object_or_404(Bike, pk=bike_id, is_approved=True)
    submitted = 'start' in request.GET or 'end' in request.GET
    form = AvailabilityDatesForm(request.GET if submitted else None)
    whatsapp_url = None
    if submitted and form.is_valid():
        start, end = form.cleaned_data['start'], form.cleaned_data['end']
        message = (f'Hello EasyMoto, is {bike.name} (fleet #{bike.pk}) available?\n'
                   f'Pickup: {start.isoformat()}\nReturn: {end.isoformat()} by 7 PM (Nepal time).\n'
                   'Please confirm availability and the total rental cost.')
        whatsapp_url = 'https://wa.me/9779851401903?' + urlencode({'text': message})
    return render(request, 'bikes/availability_request.html', {'bike': bike, 'form': form, 'whatsapp_url': whatsapp_url})
