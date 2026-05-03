from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from apps.inventory import views as inv_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', inv_views.dashboard, name='dashboard'),
    path('accounts/', include('apps.accounts.urls')),
    path('inventory/', include('apps.inventory.urls')),
    path('pelanggan/', include('apps.pelanggan.urls')),
    path('transactions/', include('apps.transactions.urls')),
    path('reports/', include('apps.reports.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
