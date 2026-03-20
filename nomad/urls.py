from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

handler403 = 'core.views.error_403'
handler404 = 'core.views.error_404'
handler500 = 'core.views.error_500'

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('core.urls')),
    path('dashboard/', include('restaurant.urls')),
    path('workers/', include('workers.urls')),
    path('orders/', include('orders.urls')),
    path('billing/', include('billing.urls')),
    path('reviews/', include('reviews.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
