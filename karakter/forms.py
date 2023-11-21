from django import forms
from .models import Profile

class ProfileForm(forms.ModelForm):
    bio = forms.CharField(widget=forms.Textarea(attrs={'rows': 3, 'cols': 40}))


    class Meta:
        model = Profile
        fields = ['bio', 'name']
