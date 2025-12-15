"""
URLs for accounts app.
"""
from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('registreren/', views.register_view, name='register'),
    path('inloggen/', auth_views.LoginView.as_view(template_name='accounts/login.html'), name='login'),
    path('uitloggen/', views.logout_view, name='logout'),
    path('voorkeuren/', views.preferences_view, name='preferences'),
]

