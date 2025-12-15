"""
URL configuration for news aggregation project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include(('apps.web.urls', 'web'), namespace='web')),
    path('accounts/', include(('apps.accounts.urls', 'accounts'), namespace='accounts')),
    path('news/', include(('apps.news.urls', 'news'), namespace='news')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

