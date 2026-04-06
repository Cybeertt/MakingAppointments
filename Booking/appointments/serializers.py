from rest_framework import serializers
from .models import Appointment, AvailableSlot

class AvailableSlotSerializer(serializers.ModelSerializer):
    class Meta:
        model = AvailableSlot
        fields = ['id', 'date', 'start_time', 'end_time', 'is_booked']

class AppointmentSerializer(serializers.ModelSerializer):
    slot = serializers.PrimaryKeyRelatedField(queryset=AvailableSlot.objects.all(), required=False)

    class Meta:
        model = Appointment
        fields = ['id', 'date', 'start_time', 'end_time', 'patient_name', 'email', 'phone_number', 'slot']
