from datetime import datetime, timedelta
from django.shortcuts import render
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import Appointment, AvailableSlot
from django.utils.timezone import make_aware
from django.core.mail import send_mail
import json
from django.http import JsonResponse
import os
from googleapiclient.discovery import build
from google.oauth2.service_account import Credentials
from django.http import JsonResponse
from .serializers import AppointmentSerializer, AvailableSlotSerializer

# Path to your credentials file
CREDENTIALS_FILE = os.path.join(os.path.dirname(__file__), 'google_credentials.json')

from .models import Appointment

from datetime import datetime
from rest_framework.response import Response
from rest_framework.decorators import api_view
from .models import AvailableSlot

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

            if not email or not phone_number or not date or not start_time or not end_time:
                return JsonResponse({'error': 'Missing required fields'}, status=400)

            # Check if the slot exists
            try:
                slot = AvailableSlot.objects.get(date=date, start_time=start_time, end_time=end_time)
                if slot.is_booked:
                    return JsonResponse({'error': 'Slot already booked'}, status=400)
            except AvailableSlot.DoesNotExist:
                return JsonResponse({'error': 'Selected slot not available'}, status=400)

            # Check if an appointment already exists
            if Appointment.objects.filter(date=date, start_time=start_time, end_time=end_time).exists():
                return JsonResponse({'error': 'Appointment already exists for the selected slot'}, status=400)

            # Create the appointment
            Appointment.objects.create(
                email=email,
                phone_number=phone_number,
                date=date,
                start_time=start_time,
                end_time=end_time
            )
            # Mark the slot as booked
            slot.is_booked = True
            slot.save()

            return JsonResponse({'message': 'Appointment booked successfully'})

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
def get_available_slots(request):
    """
    Fetch available slots for a given date.
    Expects a 'date' parameter in the query string (format: YYYY-MM-DD).
    """
    try:
        # Get the 'date' parameter from the query string
        date_str = request.GET.get('date')
        
        if not date_str:
            return Response({"error": "Date parameter is missing"}, status=400)

        # Parse the date string into a date object (YYYY-MM-DD format)
        date = datetime.strptime(date_str, "%Y-%m-%d").date()

        # Log the date for debugging purposes
        print("Parsed date:", date)

        # Filter available slots for the given date
        available_slots = AvailableSlot.objects.filter(date=date, is_booked=False)

        # Prepare the response data with available slots
        slots_data = [
            {
                'start_time': slot.start_time.strftime("%H:%M"),
                'end_time': slot.end_time.strftime("%H:%M"),
                'is_booked': slot.is_booked  # Include the booking status
            }
            for slot in available_slots
        ]

        # Return the available slots
        return Response({"available_slots": slots_data})

    except Exception as e:
        # Log the error
        print("Error:", str(e))
        return Response({"error": str(e)}, status=400)


@api_view(['GET', 'POST'])
def post_available_slots(request):
    """
    Handles both GET and POST requests:
    - GET: Returns a list of available slots
    - POST: Creates available slots for a range of dates and times.
    Expects JSON input with 'start_date', 'end_date', 'start_time', 'end_time', and 'slot_duration' for POST.
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
        required_fields = ['start_date', 'end_date', 'start_time', 'end_time']
        for field in required_fields:
            if field not in data:
                return Response({"error": f"Missing field: {field}"}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
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
                        is_booked=False
                    )
                    slots.append(slot)
                    current_time = next_time

                current_date += timedelta(days=1)

            # Bulk create the slots in the database
            AvailableSlot.objects.bulk_create(slots)

            return Response({"message": "Slots created successfully"}, status=status.HTTP_201_CREATED)

        except ValueError as e:
            return Response({"error": f"Invalid date/time format. {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)



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

def appointment_list_view(request):
    appointments = Appointment.objects.all()
    available_slots = AvailableSlot.objects.all()

    context = {
        'appointments': appointments,
        'available_slots': available_slots,
    }
    return render(request, 'appointments/appointment_list.html', context)
