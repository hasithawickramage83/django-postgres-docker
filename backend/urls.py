from django.contrib import admin
from django.http import HttpResponse
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
def home(request):
    return HttpResponse("Django app is live on Render!")
urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('users.urls')),      # Auth routes
    path('api/products/', include('products.urls')),  # Product routes
    path('api/orders/', include('orders.urls')),  # Cart & Order endpoints
    path('api/payments/', include('payments.urls')),  # Payment endpoints


]

# Serve media files during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
