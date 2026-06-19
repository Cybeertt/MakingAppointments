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
    patient_name = models.CharField(max_length=100, null=True, blank=True)
    email = models.EmailField()
    phone_number = models.CharField(max_length=15)
    slot = models.ForeignKey(AvailableSlot, on_delete=models.SET_NULL, null=True, blank=True, related_name='appointments')


class SmsMessage(models.Model):
    direction = models.CharField(max_length=10)
    from_number = models.CharField(max_length=32, null=True, blank=True)
    to_number = models.CharField(max_length=32, null=True, blank=True)
    body = models.TextField(blank=True)
    twilio_sid = models.CharField(max_length=64, null=True, blank=True)
    status = models.CharField(max_length=32, null=True, blank=True)
    error = models.TextField(null=True, blank=True)
    payload = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

