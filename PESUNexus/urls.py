from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from django.views.static import serve as static_serve

urlpatterns = [
    path('admin/', admin.site.urls),
    path('users/', include('users.urls')),
    path('', include('core.urls')),
    path('mocktests/', include('mocktests.urls')),
    path('materials/', include('materials.lib_urls')),
    path('materials/', include('materials.urls')),
]

# Media files — always served, regardless of DEBUG
urlpatterns += [
    re_path(r'^media/(?P<path>.*)$', static_serve, {'document_root': settings.MEDIA_ROOT}),
]

# (Optional, still needed for DEBUG static files in dev)
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)