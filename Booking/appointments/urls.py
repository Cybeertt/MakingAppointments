from django.urls import path
from . import views

urlpatterns = [
    path('', views.calendar_view, name='calendar_view'),
    path('calendarmark/', views.calendarmark_view, name='calendarmark_view'),
    path('appointment-list/', views.appointment_list_view, name='appointment_list'),
    path('available-slots/', views.get_available_slots, name='get_available_slots'),
    path('available-dates/', views.available_dates, name='available_dates'),
    path('available-datesmarked/', views.available_datesmarked, name='available_datesmarked'),
    path('available-slots-date/', views.get_available_slots, name='get_available_slots_date'),
    path('available-slots/post', views.post_available_slots, name='post_available_slots'),
    path('appointments/', views.appointments, name='appointments'),
    path('get_appointments', views.get_appointments, name='get_appointments'),
    path('appointments/<int:pk>/', views.appointment_detail, name='appointment_detail'),
    path('book-appointment/', views.book_appointment, name='book_appointment'),
    path('seed-test-slots/', views.seed_test_slots, name='seed_test_slots'),
    path('locations/', views.get_locations, name='get_locations'),
]
