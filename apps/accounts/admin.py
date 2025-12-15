"""
Admin configuration for accounts app
"""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import UserProfile


class UserProfileInline(admin.StackedInline):
    """Inline admin for UserProfile."""
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Profiel'
    filter_horizontal = ['selected_categories']


class UserAdmin(BaseUserAdmin):
    """Extended User admin with profile."""
    inlines = [UserProfileInline]


# Re-register UserAdmin
admin.site.unregister(User)
admin.site.register(User, UserAdmin)


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    """Admin for UserProfile model."""
    list_display = ['user', 'category_count', 'created_at']
    list_filter = ['created_at', 'updated_at']
    search_fields = ['user__username', 'user__email']
    filter_horizontal = ['selected_categories']
    
    def category_count(self, obj):
        """Count of selected categories."""
        return obj.selected_categories.count()
    category_count.short_description = 'Aantal categorieën'

