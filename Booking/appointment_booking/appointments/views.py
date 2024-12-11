from django.shortcuts import render
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.http import JsonResponse
from .models import Appointment
from django.utils.timezone import make_aware
from django.core.mail import send_mail
import json
from django.http import JsonResponse
from .google_calendar import get_available_events
import os
from googleapiclient.discovery import build
from google.oauth2.service_account import Credentials
from django.http import JsonResponse
from .serializers import AppointmentSerializer

# Path to your credentials file
CREDENTIALS_FILE = os.path.join(os.path.dirname(__file__), 'google_credentials.json')

from .models import Appointment

def available_slots(request):
    # Query all appointments
    appointments = Appointment.objects.all()

    # Convert to JSON-friendly format
    slots = [
        {"start": f"{appt.date}T{appt.hour:02d}:{appt.minute:02d}:00", 
         "end": f"{appt.date}T{appt.hour:02d}:{(appt.minute + 30) % 60:02d}:00"}
        for appt in appointments
    ]

    return JsonResponse({"available_slots": slots})

@api_view(['GET'])
def get_available_slots(request):
    """
    List all available slots.
    """
    available_slots = AvailableSlot.objects.filter(is_booked=False)
    serializer = AvailableSlotSerializer(available_slots, many=True)
    return Response(serializer.data)

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
    # Fetch appointments from the database
    appointments = Appointment.objects.all()

    # Pass appointments to the template
    context = {'appointments': appointments}
    return render(request, 'appointments/appointments_list.html', context)

