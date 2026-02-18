"""
Root URL configuration.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView

urlpatterns = [
    path('admin/', admin.site.urls),

    # Registration HTML page (Task 1 — Sign-up form)
    path('register/', TemplateView.as_view(template_name='register.html'), name='register-page'),

    # All REST API endpoints
    path('api/', include('users.urls')),
]

# WhiteNoise handles /static/ automatically.
# Only media files need manual serving in development.
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

