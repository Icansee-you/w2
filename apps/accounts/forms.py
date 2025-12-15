"""
Forms for accounts app.
"""
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from apps.news.models import Category


class RegisterForm(UserCreationForm):
    """User registration form."""
    email = forms.EmailField(
        label='E-mailadres',
        required=False,
        help_text='Optioneel'
    )
    
    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']
        labels = {
            'username': 'Gebruikersnaam',
        }


class PreferencesForm(forms.Form):
    """User preferences form for category selection."""
    categories = forms.ModelMultipleChoiceField(
        queryset=Category.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label='Categorieën',
        help_text='Selecteer de categorieën waarvan je nieuws wilt ontvangen.'
    )
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        if user and hasattr(user, 'profile'):
            self.fields['categories'].initial = user.profile.selected_categories.all()

