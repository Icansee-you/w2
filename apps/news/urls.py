"""
URLs for news app.
"""
from django.urls import path
from . import views

urlpatterns = [
    path('mijn-nieuws/', views.my_news_view, name='my_news'),
    path('artikel/<uuid:article_id>/', views.article_detail_view, name='article_detail'),
]

