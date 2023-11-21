from django import forms
from django.conf import settings
from fakts import models


class ConfigureForm(forms.Form):
    device_code = forms.CharField(required=False, widget=forms.HiddenInput())
    composition = forms.ModelChoiceField(models.Composition.objects.all(), required=False, initial=1, widget=forms.HiddenInput())


class DeviceForm(forms.Form):
    device_code = forms.CharField(required=True)