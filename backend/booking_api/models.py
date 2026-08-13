from django.db import models
import random

class Room(models.Model):
    title = models.CharField(max_length=100)
    room_number = models.CharField(max_length=20, unique=True)
    room_type = models.CharField(max_length=50) # Deluxe Room, Premium Suite, Family Suite
    base_price = models.DecimalField(max_digits=10, decimal_places=2)
    capacity = models.IntegerField(default=2)
    total_rooms = models.IntegerField(default=5)
    amenities = models.TextField(default="Wi-Fi, AC, TV")
    image_key = models.CharField(max_length=50, default="deluxe")

    def __str__(self):
        return f"{self.title} ({self.room_number})"


class Booking(models.Model):
    STATUS_CHOICES = [
        ('Confirmed', 'Confirmed'),
        ('Checked-In', 'Checked-In'),
        ('Checked-Out', 'Checked-Out'),
        ('Cancelled', 'Cancelled'),
    ]

    booking_id = models.CharField(max_length=20, unique=True)
    guest_name = models.CharField(max_length=150)
    guest_email = models.EmailField()
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='bookings', null=True, blank=True)
    room_type_name = models.CharField(max_length=100, default="Deluxe Room")
    check_in = models.DateField()
    check_out = models.DateField()
    guests_count = models.IntegerField(default=1)
    price_paid = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Confirmed')
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.booking_id:
            self.booking_id = f"BK-{random.randint(1000, 9999)}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.booking_id} - {self.guest_name} ({self.status})"


class PricingRule(models.Model):
    room_type = models.CharField(max_length=50, unique=True)
    weekend_multiplier = models.FloatField(default=1.15)
    high_occupancy_multiplier = models.FloatField(default=1.25)

    def __str__(self):
        return f"Rule for {self.room_type}"
