"""
News app models: Article and Category
"""
import uuid
from django.db import models
from django.core.validators import URLValidator
from django.utils import timezone


class Category(models.Model):
    """Category for news articles."""
    
    POLITICS = 'POLITICS'
    NATIONAL = 'NATIONAL'
    INTERNATIONAL = 'INTERNATIONAL'
    SPORT = 'SPORT'
    OTHER = 'OTHER'
    
    CATEGORY_CHOICES = [
        (POLITICS, 'Politiek'),
        (NATIONAL, 'Nationaal'),
        (INTERNATIONAL, 'Internationaal'),
        (SPORT, 'Sport'),
        (OTHER, 'Overig'),
    ]
    
    key = models.CharField(
        max_length=20,
        choices=CATEGORY_CHOICES,
        unique=True,
        help_text="Internal key for the category"
    )
    name = models.CharField(
        max_length=50,
        help_text="Display name in Dutch"
    )
    
    class Meta:
        verbose_name = 'Categorie'
        verbose_name_plural = 'Categorieën'
        ordering = ['key']
    
    def __str__(self):
        return self.name


class Article(models.Model):
    """News article from RSS feed."""
    
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    title = models.CharField(
        max_length=500,
        help_text="Article title"
    )
    summary = models.TextField(
        blank=True,
        null=True,
        help_text="Article summary/excerpt"
    )
    content = models.TextField(
        blank=True,
        null=True,
        help_text="Full article content"
    )
    link = models.URLField(
        max_length=1000,
        help_text="Original article URL"
    )
    guid = models.CharField(
        max_length=500,
        blank=True,
        null=True,
        unique=True,
        db_index=True,
        help_text="RSS guid (unique identifier)"
    )
    source_name = models.CharField(
        max_length=100,
        default='NOS',
        help_text="Source name"
    )
    source_feed_url = models.URLField(
        max_length=1000,
        help_text="RSS feed URL"
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='articles',
        help_text="Article category"
    )
    published_at = models.DateTimeField(
        help_text="Publication date from RSS"
    )
    image_url = models.URLField(
        max_length=1000,
        blank=True,
        null=True,
        help_text="Article image URL"
    )
    created_at = models.DateTimeField(
        auto_now_add=True
    )
    updated_at = models.DateTimeField(
        auto_now=True
    )
    
    class Meta:
        verbose_name = 'Artikel'
        verbose_name_plural = 'Artikelen'
        ordering = ['-published_at']
        indexes = [
            models.Index(fields=['-published_at']),
            models.Index(fields=['category']),
            models.Index(fields=['title']),
        ]
        # Unique constraint: guid if present, else link + published_at
        constraints = [
            models.UniqueConstraint(
                fields=['link', 'published_at'],
                name='unique_link_published',
                condition=models.Q(guid__isnull=True)
            ),
        ]
    
    def __str__(self):
        return self.title[:100]

