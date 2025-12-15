"""
Admin configuration for news app
"""
from django.contrib import admin
from django.utils.html import format_html
from .models import Article, Category


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    """Admin for Category model."""
    list_display = ['key', 'name', 'article_count']
    search_fields = ['name', 'key']
    
    def article_count(self, obj):
        """Count of articles in this category."""
        return obj.articles.count()
    article_count.short_description = 'Aantal artikelen'


@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    """Admin for Article model."""
    list_display = ['title_short', 'category', 'published_at', 'source_name', 'has_image']
    list_filter = ['category', 'source_name', 'published_at', 'created_at']
    search_fields = ['title', 'summary', 'content']
    readonly_fields = ['id', 'created_at', 'updated_at']
    date_hierarchy = 'published_at'
    actions = ['bulk_recategorize']
    
    fieldsets = (
        ('Artikel informatie', {
            'fields': ('title', 'summary', 'content', 'category')
        }),
        ('Bron informatie', {
            'fields': ('link', 'guid', 'source_name', 'source_feed_url', 'published_at', 'image_url')
        }),
        ('Metadata', {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def title_short(self, obj):
        """Shortened title for list display."""
        return obj.title[:80] + '...' if len(obj.title) > 80 else obj.title
    title_short.short_description = 'Titel'
    
    def has_image(self, obj):
        """Check if article has image."""
        return '✓' if obj.image_url else '✗'
    has_image.short_description = 'Afbeelding'
    
    @admin.action(description='Herschik categorisatie voor geselecteerde artikelen')
    def bulk_recategorize(self, request, queryset):
        """Bulk recategorize action - shows intermediate form."""
        from django.contrib import messages
        from django.shortcuts import render, redirect
        
        if 'apply' in request.POST:
            category_id = request.POST.get('category')
            if category_id:
                try:
                    category = Category.objects.get(id=category_id)
                    updated = queryset.update(category=category)
                    messages.success(request, f'{updated} artikelen zijn gecategoriseerd als "{category.name}".')
                    return redirect('admin:news_article_changelist')
                except Category.DoesNotExist:
                    messages.error(request, 'Categorie niet gevonden.')
            else:
                messages.error(request, 'Selecteer een categorie.')
        
        categories = Category.objects.all()
        context = {
            'articles': queryset,
            'categories': categories,
            'article_count': queryset.count(),
        }
        return render(request, 'admin/bulk_recategorize.html', context)

