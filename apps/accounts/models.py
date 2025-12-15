"""
Accounts app models: UserProfile
"""
from django.db import models
from django.contrib.auth.models import User


class UserProfile(models.Model):
    """User profile with category preferences."""
    
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='profile',
        help_text="Associated user"
    )
    selected_categories = models.ManyToManyField(
        'news.Category',
        blank=True,
        related_name='user_profiles',
        help_text="Selected news categories"
    )
    created_at = models.DateTimeField(
        auto_now_add=True
    )
    updated_at = models.DateTimeField(
        auto_now=True
    )
    
    class Meta:
        verbose_name = 'Gebruikersprofiel'
        verbose_name_plural = 'Gebruikersprofielen'
    
    def __str__(self):
        return f"Profiel van {self.user.username}"

