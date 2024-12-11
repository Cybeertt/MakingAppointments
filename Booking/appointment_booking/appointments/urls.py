from django.urls import path
from . import views

urlpatterns = [
    path('', views.calendar_view, name='calendar_view'),  # Home page showing the calendar
    path('available-slots/', views.get_available_slots, name='get_available_slots'),
    path('appointments/', views.appointments, name='appointments'),  # List or create an appointment
    path('get_appointments', views.get_appointments, name='get_appointments'),
    path('appointments/<int:pk>/', views.appointment_detail, name='appointment_detail'),  # View, update, or delete an appointment
]
