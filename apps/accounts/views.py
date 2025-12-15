"""
Views for accounts app.
"""
from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import RegisterForm, PreferencesForm


def register_view(request):
    """User registration view."""
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Registratie succesvol! Welkom!')
            return redirect('news:my_news')
    else:
        form = RegisterForm()
    
    return render(request, 'accounts/register.html', {'form': form})


@login_required
def preferences_view(request):
    """User preferences view."""
    if request.method == 'POST':
        form = PreferencesForm(request.POST, user=request.user)
        if form.is_valid():
            request.user.profile.selected_categories.set(
                form.cleaned_data['categories']
            )
            messages.success(request, 'Voorkeuren opgeslagen!')
            return redirect('news:my_news')
    else:
        form = PreferencesForm(user=request.user)
    
    return render(request, 'accounts/preferences.html', {'form': form})


def logout_view(request):
    """Logout view that handles GET requests."""
    logout(request)
    messages.success(request, 'Je bent uitgelogd.')
    return redirect('web:home')

