from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.login_api, name='api_login'),
    path('rooms/', views.rooms_api, name='api_rooms'),
    path('bookings/', views.bookings_api, name='api_bookings'),
    path('bookings/<str:booking_id>/status/', views.update_booking_status_api, name='api_update_status'),
    path('admin/stats/', views.admin_stats_api, name='api_admin_stats'),
]
