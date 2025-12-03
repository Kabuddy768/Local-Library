from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('catalog/', include('catalog.urls')),
    path('accounts/', include('django.contrib.auth.urls')),
]

# Redirect root URL to /catalog/
urlpatterns += [
    path('', RedirectView.as_view(url='/catalog/', permanent=True)),
]
