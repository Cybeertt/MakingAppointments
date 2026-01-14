from django.db import models

class Location(models.Model):
    name = models.CharField(max_length=100)
    address = models.CharField(max_length=255)

    def __str__(self):
        return self.name

class AvailableSlot(models.Model):
    location = models.ForeignKey(Location, on_delete=models.CASCADE, related_name='slots', null=True)
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

