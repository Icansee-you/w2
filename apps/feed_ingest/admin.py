"""
Admin configuration for feed_ingest app
"""
from django.contrib import admin
from .models import IngestionRun


@admin.register(IngestionRun)
class IngestionRunAdmin(admin.ModelAdmin):
    """Admin for IngestionRun model."""
    list_display = ['started_at', 'finished_at', 'status', 'fetched_count', 
                   'inserted_count', 'updated_count', 'skipped_count', 'has_error']
    list_filter = ['status', 'started_at']
    search_fields = ['error_message']
    readonly_fields = ['started_at', 'finished_at', 'fetched_count', 'inserted_count',
                      'updated_count', 'skipped_count', 'status', 'error_message']
    date_hierarchy = 'started_at'
    
    def has_error(self, obj):
        """Check if run has error message."""
        return '✓' if obj.error_message else '✗'
    has_error.short_description = 'Fout'
    
    def has_add_permission(self, request):
        """Disable manual creation."""
        return False

