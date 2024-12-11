# appointments/serializers.py
from rest_framework import serializers
from .models import Appointment

class AppointmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Appointment
        fields = ['id', 'date', 'start_time', 'end_time', 'user_name', 'email', 'phone_number']
