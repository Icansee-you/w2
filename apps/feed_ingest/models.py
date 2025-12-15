"""
Feed ingestion app models: IngestionRun
"""
from django.db import models
from django.utils import timezone


class IngestionRun(models.Model):
    """Record of an RSS feed ingestion run."""
    
    SUCCESS = 'SUCCESS'
    PARTIAL = 'PARTIAL'
    FAILED = 'FAILED'
    
    STATUS_CHOICES = [
        (SUCCESS, 'Success'),
        (PARTIAL, 'Partieel'),
        (FAILED, 'Mislukt'),
    ]
    
    started_at = models.DateTimeField(
        auto_now_add=True,
        help_text="When the ingestion started"
    )
    finished_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When the ingestion finished"
    )
    fetched_count = models.IntegerField(
        default=0,
        help_text="Number of items fetched from feed"
    )
    inserted_count = models.IntegerField(
        default=0,
        help_text="Number of new articles inserted"
    )
    updated_count = models.IntegerField(
        default=0,
        help_text="Number of existing articles updated"
    )
    skipped_count = models.IntegerField(
        default=0,
        help_text="Number of articles skipped (duplicates)"
    )
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default=SUCCESS,
        help_text="Status of the ingestion run"
    )
    error_message = models.TextField(
        blank=True,
        null=True,
        help_text="Error message if status is FAILED"
    )
    
    class Meta:
        verbose_name = 'Ingestie Run'
        verbose_name_plural = 'Ingestie Runs'
        ordering = ['-started_at']
        indexes = [
            models.Index(fields=['-started_at']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return f"Ingestie {self.started_at.strftime('%Y-%m-%d %H:%M')} - {self.get_status_display()}"
    
    @classmethod
    def get_latest_failed(cls):
        """Get the latest failed run without a subsequent success."""
        latest_success = cls.objects.filter(status=cls.SUCCESS).order_by('-started_at').first()
        if latest_success:
            latest_failed = cls.objects.filter(
                status=cls.FAILED,
                started_at__gt=latest_success.started_at
            ).order_by('-started_at').first()
            return latest_failed
        else:
            # No success yet, return latest failed
            return cls.objects.filter(status=cls.FAILED).order_by('-started_at').first()

