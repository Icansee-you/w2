"""
Views for news app.
"""
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from .models import Article, Category


@login_required
def my_news_view(request):
    """User's personalized news feed."""
    # Get user's selected categories
    user_categories = request.user.profile.selected_categories.all()
    
    # Start with all articles
    articles = Article.objects.all()
    
    # Filter by user's selected categories
    if user_categories.exists():
        articles = articles.filter(category__in=user_categories)
    else:
        # If no categories selected, show no articles
        articles = Article.objects.none()
    
    # Search functionality
    search_query = request.GET.get('q', '').strip()
    if search_query:
        articles = articles.filter(
            Q(title__icontains=search_query) |
            Q(summary__icontains=search_query) |
            Q(content__icontains=search_query)
        )
    
    # Category filter (additional filter on top of user preferences)
    category_filter = request.GET.get('category', '')
    if category_filter:
        try:
            category = Category.objects.get(key=category_filter)
            articles = articles.filter(category=category)
        except Category.DoesNotExist:
            pass
    
    # Order by published_at desc
    articles = articles.order_by('-published_at')
    
    # Pagination (max 50 per page)
    paginator = Paginator(articles, 50)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    # Get all categories for filter pills
    all_categories = Category.objects.all()
    
    context = {
        'articles': page_obj,
        'search_query': search_query,
        'category_filter': category_filter,
        'categories': all_categories,
        'user_categories': user_categories,
    }
    
    return render(request, 'news/my_news.html', context)


def article_detail_view(request, article_id):
    """Article detail view."""
    article = get_object_or_404(Article, id=article_id)
    
    context = {
        'article': article,
    }
    
    return render(request, 'news/article_detail.html', context)

