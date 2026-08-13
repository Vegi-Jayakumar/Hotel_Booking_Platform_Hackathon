import json
import datetime
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Sum, Q
from .models import Room, Booking, PricingRule

@csrf_exempt
def login_api(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            email = data.get('email', '').strip().lower()
            password = data.get('password', '')

            if email == 'admin@staysmart.com' and password == 'admin123':
                return JsonResponse({
                    'status': 'success',
                    'role': 'admin',
                    'email': email,
                    'message': 'Admin login successful!',
                    'redirect': '/admin-dashboard/',

                })
            elif (email == 'guest@example.com' and password == 'guest123') or (email and password):
                return JsonResponse({
                    'status': 'success',
                    'role': 'guest',
                    'email': email,
                    'message': 'Guest login successful!',
                    'redirect': 'HomePage.html'
                })
            else:
                return JsonResponse({'status': 'error', 'message': 'Invalid email or password.'}, status=400)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
    
    return JsonResponse({'status': 'error', 'message': 'Only POST method allowed'}, status=405)


def rooms_api(request):
    check_in_str = request.GET.get('checkIn')
    rooms = Room.objects.all()

    # Seed rooms if DB is empty
    if not rooms.exists():
        Room.objects.create(title="Deluxe Room", room_number="101", room_type="Deluxe Room", base_price=2499, capacity=2, total_rooms=10, amenities="Wi-Fi, AC, Smart TV, King Bed", image_key="deluxe")
        Room.objects.create(title="Deluxe Room", room_number="102", room_type="Deluxe Room", base_price=2499, capacity=2, total_rooms=10, amenities="Wi-Fi, AC, Smart TV, King Bed", image_key="deluxe")
        Room.objects.create(title="Premium Suite", room_number="201", room_type="Premium Suite", base_price=4499, capacity=3, total_rooms=6, amenities="Wi-Fi, AC, Breakfast, King Bed", image_key="premium")
        Room.objects.create(title="Family Suite", room_number="301", room_type="Family Suite", base_price=6999, capacity=5, total_rooms=3, amenities="Wi-Fi, AC, Living Room, Breakfast", image_key="family")
        rooms = Room.objects.all()

    room_list = []
    for r in rooms:
        price = float(r.base_price)
        if check_in_str:
            try:
                dt = datetime.datetime.strptime(check_in_str, '%Y-%m-%d').date()
                if dt.weekday() in (5, 6): # Weekend
                    price *= 1.15
                lead_days = (dt - datetime.date.today()).days
                if 0 <= lead_days <= 2:
                    price *= 1.10
            except ValueError:
                pass

        room_list.append({
            'id': r.id,
            'title': r.title,
            'room_number': r.room_number,
            'room_type': r.room_type,
            'base_price': float(r.base_price),
            'calculated_price': round(price),
            'capacity': r.capacity,
            'total_rooms': r.total_rooms,
            'amenities': r.amenities.split(', '),
            'image_key': r.image_key
        })

    return JsonResponse({'status': 'success', 'rooms': room_list})


@csrf_exempt
def bookings_api(request):
    if request.method == 'GET':
        status_filter = request.GET.get('status')
        search_query = request.GET.get('search')

        qs = Booking.objects.all().order_by('-id')

        # Seed sample data if empty
        if not qs.exists():
            today = datetime.date.today()
            Booking.objects.create(booking_id="BK-1001", guest_name="Priya Sharma", guest_email="priya.s@example.com", room_type_name="Deluxe Room", check_in=today - datetime.timedelta(days=1), check_out=today + datetime.timedelta(days=2), guests_count=2, price_paid=7497, status="Checked-In")
            Booking.objects.create(booking_id="BK-1002", guest_name="Vikram Malhotra", guest_email="vikram.m@example.com", room_type_name="Premium Suite", check_in=today, check_out=today + datetime.timedelta(days=3), guests_count=2, price_paid=13497, status="Confirmed")
            Booking.objects.create(booking_id="BK-1003", guest_name="Ananya Roy", guest_email="ananya.roy@example.com", room_type_name="Family Suite", check_in=today - datetime.timedelta(days=3), check_out=today - datetime.timedelta(days=1), guests_count=4, price_paid=13998, status="Checked-Out")
            qs = Booking.objects.all().order_by('-id')

        if status_filter and status_filter != 'all':
            qs = qs.filter(status=status_filter)

        if search_query:
            qs = qs.filter(
                Q(guest_name__icontains=search_query) |
                Q(guest_email__icontains=search_query) |
                Q(booking_id__icontains=search_query) |
                Q(room_type_name__icontains=search_query)
            )

        booking_data = []
        for b in qs:
            booking_data.append({
                'id': b.booking_id,
                'guestName': b.guest_name,
                'guestEmail': b.guest_email,
                'room': b.room_type_name,
                'checkIn': str(b.check_in),
                'checkOut': str(b.check_out),
                'guests': b.guests_count,
                'pricePaid': float(b.price_paid),
                'status': b.status
            })

        return JsonResponse({'status': 'success', 'bookings': booking_data})

    elif request.method == 'POST':
        try:
            data = json.loads(request.body)
            guest_name = data.get('guestName') or data.get('guest') or 'Guest User'
            guest_email = data.get('guestEmail') or data.get('email') or 'guest@example.com'
            room_type = data.get('room') or 'Deluxe Room'
            check_in = data.get('checkIn') or str(datetime.date.today())
            check_out = data.get('checkOut') or str(datetime.date.today() + datetime.timedelta(days=1))
            guests = int(data.get('guests', 1))
            price_paid = float(data.get('pricePaid', 2499))

            booking = Booking.objects.create(
                guest_name=guest_name,
                guest_email=guest_email,
                room_type_name=room_type,
                check_in=check_in,
                check_out=check_out,
                guests_count=guests,
                price_paid=price_paid,
                status='Confirmed'
            )

            return JsonResponse({
                'status': 'success',
                'message': 'Booking confirmed!',
                'booking': {
                    'id': booking.booking_id,
                    'guestName': booking.guest_name,
                    'room': booking.room_type_name,
                    'checkIn': str(booking.check_in),
                    'checkOut': str(booking.check_out),
                    'pricePaid': float(booking.price_paid),
                    'status': booking.status
                }
            })
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)


@csrf_exempt
def update_booking_status_api(request, booking_id):
    if request.method == 'PATCH' or request.method == 'POST':
        try:
            data = json.loads(request.body)
            new_status = data.get('status')
            booking = Booking.objects.get(booking_id=booking_id)
            booking.status = new_status
            booking.save()
            return JsonResponse({'status': 'success', 'message': f'Booking {booking_id} status updated to {new_status}'})
        except Booking.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Booking not found'}, status=404)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)


def admin_stats_api(request):
    today = datetime.date.today()
    
    total_rev = Booking.objects.filter(~Q(status='Cancelled')).aggregate(Sum('price_paid'))['price_paid__sum'] or 0
    checked_in_count = Booking.objects.filter(status='Checked-In').count()
    check_ins_today = Booking.objects.filter(check_in=today).count()
    check_outs_today = Booking.objects.filter(check_out=today).count()
    total_bookings = Booking.objects.count()
    total_rooms = Room.objects.count() or 10

    occ_percentage = round((checked_in_count / total_rooms) * 100) if total_rooms else 0

    return JsonResponse({
        'status': 'success',
        'kpis': {
            'totalRevenue': float(total_rev),
            'totalBookings': total_bookings,
            'occupancyPercentage': occ_percentage,
            'checkedInCount': checked_in_count,
            'totalRooms': total_rooms,
            'checkInsToday': check_ins_today,
            'checkOutsToday': check_outs_today
        }
    })
