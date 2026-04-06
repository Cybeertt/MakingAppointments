from django.shortcuts import render
from appointments.models import Appointment


def index(request):
    appointments = Appointment.objects.all().order_by('date', 'start_time')
    events = []
    for appointment in appointments:
        events.append({
            'title': f'{(appointment.patient_name or appointment.email)} - {(appointment.slot.location.name if appointment.slot and appointment.slot.location else "No location")}',
            'start': f'{appointment.date}T{appointment.start_time}',
            'end': f'{appointment.date}T{appointment.end_time}',
            'id': appointment.id,
            'allDay': False,
        })
    context = {'appointments': appointments, 'events': events}
    return render(request, 'dashboard/index.html', context)





