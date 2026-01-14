from collections import defaultdict
from datetime import datetime, timedelta
from django.shortcuts import render
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Count
from .models import Appointment, AvailableSlot, Location
import json
import os
from django.http import JsonResponse
from .serializers import AppointmentSerializer, AvailableSlotSerializer
from twilio.rest import Client

# Path to your credentials file
CREDENTIALS_FILE = os.path.join(os.path.dirname(__file__), 'google_credentials.json')

# Twilio configuration from environment (do NOT hardcode secrets)
TWILIO_ACCOUNT_SID = os.environ.get('TWILIO_ACCOUNT_SID')
TWILIO_AUTH_TOKEN = os.environ.get('TWILIO_AUTH_TOKEN')
TWILIO_FROM_NUMBER = os.environ.get('TWILIO_FROM_NUMBER')
DOCTOR_PHONE = os.environ.get('DOCTOR_PHONE')  # Doctor's phone for notifications

client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN) if TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN else None

def send_sms(to_phone_number, message_body):
    if not client or not TWILIO_FROM_NUMBER:
        return None
    try:
        message = client.messages.create(
            body=message_body,
            from_=TWILIO_FROM_NUMBER,
            to=to_phone_number
        )
        return message.sid
    except Exception:
        # Optionally log the error; return None to avoid breaking booking flow
        return None



@api_view(['GET'])
def get_available_slots_date(request):
    date_str = request.GET.get('date')
    
    if not date_str:
        return JsonResponse({"error": "Date parameter is missing"}, status=400)

    # Parse the date string into a date object (YYYY-MM-DD format)
    try:
        date = datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError as ve:
        return JsonResponse({"error": f"Invalid date format: {str(ve)}"}, status=400)

    # Fetch available slots for the given date
    available_slots = AvailableSlot.objects.filter(date=date, is_booked=False)

    slots_data = [
        {
            'start_time': slot.start_time.strftime("%H:%M"),
            'end_time': slot.end_time.strftime("%H:%M"),
        }
        for slot in available_slots
    ]

    return JsonResponse({"available_slots": slots_data})

@csrf_exempt
def book_appointment(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            email = data.get('email')
            phone_number = data.get('phone_number')
            date = data.get('date')
            start_time = data.get('start_time')
            end_time = data.get('end_time')
            location_id = data.get('location')

            if not all([email, phone_number, date, start_time, end_time, location_id]):
                return JsonResponse({'error': 'Missing required fields'}, status=400)

            # Check if the slot exists and is not booked
            try:
                location = Location.objects.get(pk=location_id)
                slot = AvailableSlot.objects.get(
                    date=date,
                    start_time=start_time,
                    end_time=end_time,
                    location=location,
                    is_booked=False
                )
            except Location.DoesNotExist:
                return JsonResponse({'error': 'Invalid location'}, status=400)
            except AvailableSlot.DoesNotExist:
                return JsonResponse({'error': 'Selected slot not available or already booked'}, status=400)

            # Create the appointment
            appointment = Appointment.objects.create(
                email=email,
                phone_number=phone_number,
                date=date,
                start_time=start_time,
                end_time=end_time,
                slot=slot  # Link to the slot
            )

            # Mark the slot as booked
            slot.is_booked = True
            slot.save()

            # Send confirmation SMS to patient
            message_body = f"Your appointment at {location.name} is confirmed for {date} from {start_time} to {end_time}."
            send_sms(phone_number, message_body)

            # Notify doctor via SMS
            if DOCTOR_PHONE:
                doctor_msg = f"New booking at {location.name}: {date} {start_time}-{end_time} for {email} ({phone_number})."
                send_sms(DOCTOR_PHONE, doctor_msg)

            return JsonResponse({'message': 'Appointment booked successfully'})

        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
        except Exception as e:
            return JsonResponse({'error': f'An error occurred: {str(e)}'}, status=500)
    else:
        return JsonResponse({'error': 'Invalid request method'}, status=405)

@api_view(['GET'])
def get_available2_slots(request):
    """
    List all available slots.
    """
    available_slots = AvailableSlot.objects.filter(is_booked=False)
    serializer = AvailableSlotSerializer(available_slots, many=True)
    return Response(serializer.data)

@api_view(['GET'])
def available_dates(request):
    if request.method == 'GET':
        try:
            # Parse the year and month from request parameters
            year = int(request.GET.get('year'))
            month = int(request.GET.get('month'))

            # Query for available slots in the given month
            available_slots = AvailableSlot.objects.filter(
                date__year=year,
                date__month=month,
                is_booked=False
            ).values_list('date', flat=True).distinct()

            # Convert dates to a list of strings (ISO format for easier parsing in JS)
            available_dates = [date.strftime('%Y-%m-%d') for date in available_slots]
            return JsonResponse({'available_dates': available_dates}, status=200)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    return JsonResponse({'error': 'Invalid request method'}, status=400)

@api_view(['GET'])
def available_datesmarked(request):
    try:
        year = int(request.GET.get('year'))
        month = int(request.GET.get('month'))

        # Get all appointments for the given year and month
        appointments = Appointment.objects.filter(date__year=year, date__month=month)

        # Organize appointments by date
        booked_dates = defaultdict(list)
        for appt in appointments:
            date_str = appt.date.strftime('%Y-%m-%d')
            booked_dates[date_str].append({
                'start_time': appt.start_time.strftime('%H:%M'),
                'end_time': appt.end_time.strftime('%H:%M'),
                'email': appt.email,
                'phone_number': appt.phone_number,
                'slot': str(appt.slot) if appt.slot else None,
            })

        return JsonResponse({'booked_dates': booked_dates}, status=200)
    
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@api_view(['GET'])
def get_available_slots(request):
    """
    Fetch available slots for a given date and optional location.
    Expects 'date' and optional 'location' parameters.
    """
    try:
        date_str = request.GET.get('date')
        location_id = request.GET.get('location')

        if not date_str:
            return Response({"error": "Date parameter is missing"}, status=400)

        date = datetime.strptime(date_str, "%Y-%m-%d").date()

        # Start with a base query
        query = AvailableSlot.objects.filter(date=date, is_booked=False)

        # If location is provided, filter by it
        if location_id:
            try:
                location = Location.objects.get(pk=location_id)
                query = query.filter(location=location)
            except (Location.DoesNotExist, ValueError):
                return Response({"error": "Invalid location ID"}, status=400)

        available_slots = query.all()

        # Prepare response data
        slots_data = [
            {
                'start_time': slot.start_time.strftime("%H:%M"),
                'end_time': slot.end_time.strftime("%H:%M"),
                'is_booked': slot.is_booked,
                'location': slot.location.name if slot.location else None,
                'location_id': slot.location.id if slot.location else None,
            }
            for slot in available_slots
        ]

        return Response({"available_slots": slots_data})

    except ValueError:
        return Response({"error": "Invalid date format"}, status=400)
    except Exception as e:
        return Response({"error": str(e)}, status=500)


@api_view(['GET', 'POST'])
def post_available_slots(request):
    """
    Handles both GET and POST requests:
    - GET: Returns a list of available slots
    - POST: Creates available slots for a range of dates and times.
    Expects JSON input with 'start_date', 'end_date', 'start_time', 'end_time', 'slot_duration', and 'location_id' for POST.
    """
    if request.method == 'GET':
        # Handle GET request: Return available slots (for simplicity, returning all slots)
        available_slots = AvailableSlot.objects.filter(is_booked=False)
        
        # Serialize the slots to return them as JSON
        slots_data = [{"date": slot.date, "start_time": slot.start_time, "end_time": slot.end_time} for slot in available_slots]
        
        return Response({"available_slots": slots_data}, status=status.HTTP_200_OK)
    
    elif request.method == 'POST':
        # Handle POST request: Create available slots
        data = request.data
        
        # Ensure required fields are present in the request
        required_fields = ['start_date', 'end_date', 'start_time', 'end_time', 'location_id']
        for field in required_fields:
            if field not in data:
                return Response({"error": f"Missing field: {field}"}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Get the location
            location_id = data['location_id']
            location = Location.objects.get(pk=location_id)

            # Parse the dates and times
            start_date = datetime.strptime(data['start_date'], "%Y-%m-%d").date()
            end_date = datetime.strptime(data['end_date'], "%Y-%m-%d").date()
            start_time = datetime.strptime(data['start_time'], "%H:%M:%S").time()
            end_time = datetime.strptime(data['end_time'], "%H:%M:%S").time()
            
            # Use a default duration of 60 minutes if not provided
            slot_duration = int(data.get('slot_duration', 60))

            slots = []
            current_date = start_date

            # Loop over the date range
            while current_date <= end_date:
                current_time = datetime.combine(current_date, start_time)
                end_time_datetime = datetime.combine(current_date, end_time)

                # Loop over the time range, creating slots
                while current_time < end_time_datetime:
                    next_time = current_time + timedelta(minutes=slot_duration)
                    slot = AvailableSlot(
                        date=current_date,
                        start_time=current_time.time(),
                        end_time=next_time.time(),
                        is_booked=False,
                        location=location  # Assign the location
                    )
                    slots.append(slot)
                    current_time = next_time

                current_date += timedelta(days=1)

            # Bulk create the slots in the database
            AvailableSlot.objects.bulk_create(slots)

            return Response({"message": f"Slots created successfully for {location.name}"}, status=status.HTTP_201_CREATED)

        except Location.DoesNotExist:
            return Response({"error": "Invalid location ID"}, status=status.HTTP_400_BAD_REQUEST)
        except ValueError as e:
            return Response({"error": f"Invalid date/time format. {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)



@api_view(['GET'])
def get_locations(request):
    """Returns a list of all office locations."""
    try:
        locations = Location.objects.all()
        locations_data = [
            {
                "id": location.id,
                "name": location.name,
                "address": location.address
            }
            for location in locations
        ]
        return Response({"locations": locations_data}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



@api_view(['GET'])
def get_appointments(request):
    appointments = Appointment.objects.all()  # Get all appointments
    serializer = AppointmentSerializer(appointments, many=True)  # Serialize the data
    return Response(serializer.data)  # Return the serialized data as JSON

@api_view(['GET', 'POST'])
def appointments(request):
    """
    List all appointments or create a new one.
    """
    if request.method == 'GET':
        appointments = Appointment.objects.all()
        serializer = AppointmentSerializer(appointments, many=True)
        return Response(serializer.data)

    elif request.method == 'POST':
        serializer = AppointmentSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET', 'PUT', 'DELETE'])
def appointment_detail(request, pk):
    """
    Retrieve, update, or delete an appointment.
    """
    try:
        appointment = Appointment.objects.get(pk=pk)
    except Appointment.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        serializer = AppointmentSerializer(appointment)
        return Response(serializer.data)

    elif request.method == 'PUT':
        serializer = AppointmentSerializer(appointment, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'DELETE':
        appointment.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

def calendar_view(request):
    return render(request, 'appointments/calendar.html')

def calendarmark_view(request):
    return render(request, 'appointments/calendarmark.html')

#List Everything
def appointment_list_view(request):
    appointments = Appointment.objects.all()
    available_slots = AvailableSlot.objects.all()

    context = {
        'appointments': appointments,
        'available_slots': available_slots,
    }
    return render(request, 'appointments/appointment_list.html', context)


def create_available_slots(start_date, end_date, start_time, end_time):
    """
    Creates available slots for the specified date range and time range with a 1-hour duration.

    :param start_date: Start date in 'YYYY-MM-DD' format.
    :param end_date: End date in 'YYYY-MM-DD' format.
    :param start_time: Start time in 'HH:MM:SS' format.
    :param end_time: End time in 'HH:MM:SS' format.
    """
    start_date_obj = datetime.strptime(start_date, "%Y-%m-%d").date()
    end_date_obj = datetime.strptime(end_date, "%Y-%m-%d").date()
    start_time_obj = datetime.strptime(start_time, "%H:%M:%S").time()
    end_time_obj = datetime.strptime(end_time, "%H:%M:%S").time()

    delta = timedelta(days=1)
    current_date = start_date_obj

    while current_date <= end_date_obj:
        current_time = datetime.combine(current_date, start_time_obj)
        end_time_datetime = datetime.combine(current_date, end_time_obj)

        while current_time < end_time_datetime:
            next_time = current_time + timedelta(hours=1)  # 1-hour slots
            AvailableSlot.objects.create(
                date=current_date,
                start_time=current_time.time(),
                end_time=next_time.time(),
                is_booked=False
            )
            current_time = next_time

        current_date += delta

# Example usage:
#create_available_slots('2025-7-1', '2025-7-31', '16:00:00', '20:00:00')


@api_view(['POST'])
def seed_test_slots(request):
    """Seed a week of demo slots for testing (next 7 days, 9:00-12:00, 30min)."""
    try:
        # Create 4 locations
        locations_data = [
            {"name": "Office 1", "address": "123 Main St"},
            {"name": "Office 2", "address": "456 Oak Ave"},
            {"name": "Office 3", "address": "789 Pine Ln"},
            {"name": "Office 4", "address": "101 Maple Dr"},
        ]

        locations = []
        for loc_data in locations_data:
            location, created = Location.objects.get_or_create(name=loc_data['name'], defaults={'address': loc_data['address']})
            locations.append(location)

        today = datetime.today().date()
        for d in range(0, 7):
            current_date = today + timedelta(days=d)
            start_dt = datetime.combine(current_date, datetime.strptime('09:00', '%H:%M').time())
            end_dt = datetime.combine(current_date, datetime.strptime('12:00', '%H:%M').time())
            current = start_dt
            slots = []
            
            # Cycle through locations
            location_index = 0

            while current < end_dt:
                next_dt = current + timedelta(minutes=30)
                
                # Assign a location to the slot
                location = locations[location_index % len(locations)]
                location_index += 1

                # Avoid duplicates
                if not AvailableSlot.objects.filter(date=current_date, start_time=current.time(), end_time=next_dt.time(), location=location).exists():
                    slots.append(AvailableSlot(
                        date=current_date,
                        start_time=current.time(),
                        end_time=next_dt.time(),
                        is_booked=False,
                        location=location
                    ))
                current = next_dt
            if slots:
                AvailableSlot.objects.bulk_create(slots)
                # Retrieve the created slots to link them to appointments
                created_slots = AvailableSlot.objects.filter(
                    date__in=[s.date for s in slots],
                    start_time__in=[s.start_time for s in slots],
                    end_time__in=[s.end_time for s in slots],
                    location__in=[s.location for s in slots]
                )
                # Create a dictionary for quick lookup of slots
                slot_lookup = {(s.date, s.start_time, s.end_time, s.location_id): s for s in created_slots}

            # Create appointments for the seeded slots
            appointments_to_create = []
            for actual_slot in created_slots:
                appointments_to_create.append(
                    Appointment(
                        date=actual_slot.date,
                        start_time=actual_slot.start_time,
                        end_time=actual_slot.end_time,
                        email=f"test_{actual_slot.date.strftime("%Y%m%d")}_{actual_slot.start_time.strftime("%H%M")}@example.com",
                        phone_number="555-123-4567",
                        slot=actual_slot
                    )
                )
            if appointments_to_create:
                Appointment.objects.bulk_create(appointments_to_create)

        return Response({"message": "Seeded 7 days of demo slots (9:00-12:00, 30min) with 4 locations and created appointments"}, status=status.HTTP_201_CREATED)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)