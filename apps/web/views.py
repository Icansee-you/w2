"""
Views for web app.
"""
from django.shortcuts import render
from django.contrib.auth.decorators import login_required


def home_view(request):
    """Home page view."""
    if request.user.is_authenticated:
        return render(request, 'web/home.html', {'authenticated': True})
    else:
        return render(request, 'web/home.html', {'authenticated': False})

