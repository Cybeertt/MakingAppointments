from django.urls import path
from . import views

urlpatterns = [
    path('', views.calendar_view, name='calendar_view'),  # Home page showing the calendar
    path('appointment-list/', views.appointment_list_view, name='appointment_list'),
    path('available-slots/', views.get_available_slots, name='get_available_slots'),
    path('available-dates/', views.available_dates, name='available_dates'),
    path('available-slots-date/', views.get_available_slots, name='get_available_slots_date'),
    path('available-slots/post', views.post_available_slots, name='post_available_slots'),  # This allows both GET and POST
    path('appointments/', views.appointments, name='appointments'),  # List or create an appointment
    path('get_appointments', views.get_appointments, name='get_appointments'),
    path('appointments/<int:pk>/', views.appointment_detail, name='appointment_detail'),  # View, update, or delete an appointment
    path('book-appointment/', views.book_appointment, name='book_appointment'), 
]
