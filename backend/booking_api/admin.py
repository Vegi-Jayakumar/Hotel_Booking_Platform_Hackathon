from django.contrib import admin
from .models import Room, Booking, PricingRule

@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ('title', 'room_number', 'room_type', 'base_price', 'capacity', 'total_rooms')
    search_fields = ('title', 'room_number', 'room_type')

@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ('booking_id', 'guest_name', 'guest_email', 'room_type_name', 'check_in', 'check_out', 'price_paid', 'status')
    list_filter = ('status', 'room_type_name')
    search_fields = ('booking_id', 'guest_name', 'guest_email')

@admin.register(PricingRule)
class PricingRuleAdmin(admin.ModelAdmin):
    list_display = ('room_type', 'weekend_multiplier', 'high_occupancy_multiplier')
