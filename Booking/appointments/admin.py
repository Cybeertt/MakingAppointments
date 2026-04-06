# appointments/admin.py
from django.contrib import admin
from .models import Appointment, AvailableSlot, Location

class AppointmentAdmin(admin.ModelAdmin):
    list_display = ['date', 'hour', 'minute', 'patient_name', 'email', 'phone_number', 'location']
    list_filter = ['date', 'slot__location']
    search_fields = ['patient_name', 'email', 'phone_number']

    def hour(self, obj):
        return obj.start_time.hour
    hour.admin_order_field = 'start_time'
    hour.short_description = 'Hour'

    def minute(self, obj):
        return obj.start_time.minute
    minute.admin_order_field = 'start_time'
    minute.short_description = 'Minute'
    
    def location(self, obj):
        return getattr(getattr(obj.slot, 'location', None), 'name', None)
    location.short_description = 'Location'

class AvailableSlotAdmin(admin.ModelAdmin):
    list_display = ['date', 'start_time', 'end_time', 'location', 'is_booked']
    list_filter = ['date', 'location', 'is_booked']
    search_fields = ['date', 'location__name']

class LocationAdmin(admin.ModelAdmin):
    list_display = ['name', 'address']
    search_fields = ['name']

admin.site.register(Appointment, AppointmentAdmin)
admin.site.register(AvailableSlot, AvailableSlotAdmin)
admin.site.register(Location, LocationAdmin)
