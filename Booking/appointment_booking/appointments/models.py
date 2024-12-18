from django.db import models

class AvailableSlot(models.Model):
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    is_booked = models.BooleanField(default=False)


class Appointment(models.Model):
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    email = models.EmailField()
    phone_number = models.CharField(max_length=15)
    slot = models.ForeignKey(AvailableSlot, on_delete=models.SET_NULL, null=True, blank=True, related_name='appointments')

