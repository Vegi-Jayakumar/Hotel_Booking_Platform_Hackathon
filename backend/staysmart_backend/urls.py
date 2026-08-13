from django.contrib import admin
from django.urls import path, include
from django.views.generic import TemplateView
from django.conf import settings

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('booking_api.urls')),
    # Frontend page routes
    path('', TemplateView.as_view(template_name='HomePage.html'), name='home'),
    path('login/', TemplateView.as_view(template_name='Loginpage.HTML'), name='login'),
    path('rooms/', TemplateView.as_view(template_name='Rooms.html'), name='rooms'),
    path('admin-dashboard/', TemplateView.as_view(template_name='AdminHomePage.HTML'), name='admin_dashboard'),
]

if settings.DEBUG:
    from django.conf.urls.static import static
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])
