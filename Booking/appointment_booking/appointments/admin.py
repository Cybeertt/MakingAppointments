# appointments/admin.py
from django.contrib import admin
from .models import Appointment

class AppointmentAdmin(admin.ModelAdmin):
    list_display = ['date', 'hour', 'minute', 'user_name', 'email', 'phone_number']

    # Method to get the hour from the start_time
    def hour(self, obj):
        return obj.start_time.hour
    hour.admin_order_field = 'start_time'  # Allows sorting by start_time
    hour.short_description = 'Hour'  # Column title in the admin

    # Method to get the minute from the start_time
    def minute(self, obj):
        return obj.start_time.minute
    minute.admin_order_field = 'start_time'  # Allows sorting by start_time
    minute.short_description = 'Minute'  # Column title in the admin

admin.site.register(Appointment, AppointmentAdmin)
