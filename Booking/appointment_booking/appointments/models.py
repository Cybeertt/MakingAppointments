from django.db import models

class AvailableSlot(models.Model):
    slot_time = models.DateTimeField(unique=True)
    is_booked = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.slot_time} - {'Booked' if self.is_booked else 'Available'}"

class Appointment(models.Model):
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    user_name = models.CharField(max_length=100)
    email = models.EmailField()
    phone_number = models.CharField(max_length=15)

    def __str__(self):
        return f"{self.date} {self.start_time} - {self.end_time}"