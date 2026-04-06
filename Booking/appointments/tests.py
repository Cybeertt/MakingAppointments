from django.test import TestCase, Client
from datetime import date, time
from .models import Location, AvailableSlot, Appointment

class ApiIntegrationTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.loc = Location.objects.create(name="Test Office", address="1 Test St")
        self.test_date = date.today()
        self.slot1 = AvailableSlot.objects.create(
            location=self.loc, date=self.test_date, start_time=time(9, 0), end_time=time(9, 30), is_booked=False
        )
        self.slot2 = AvailableSlot.objects.create(
            location=self.loc, date=self.test_date, start_time=time(9, 30), end_time=time(10, 0), is_booked=False
        )

    def test_locations_endpoint(self):
        resp = self.client.get("/appointments/locations/")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        names = [l["name"] for l in data.get("locations", [])]
        self.assertIn(self.loc.name, names)

    def test_available_dates_filter_by_location(self):
        year = self.test_date.year
        month = self.test_date.month
        resp = self.client.get(f"/appointments/available-dates/?year={year}&month={month}&location={self.loc.id}")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn(self.test_date.strftime("%Y-%m-%d"), data.get("available_dates", []))

    def test_available_slots_by_date_and_location(self):
        resp = self.client.get(
            f"/appointments/available-slots/?date={self.test_date.strftime('%Y-%m-%d')}&location={self.loc.id}"
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        times = [s["start_time"] for s in data.get("available_slots", [])]
        self.assertIn("09:00", times)
        self.assertIn("09:30", times)

    def test_book_appointment_sets_name_and_marks_slot_booked(self):
        payload = {
            "name": "Alice Patient",
            "email": "alice@example.com",
            "phone_number": "555-000-1111",
            "date": self.test_date.strftime("%Y-%m-%d"),
            "start_time": "09:00",
            "end_time": "09:30",
            "location": self.loc.id,
        }
        resp = self.client.post("/appointments/book-appointment/", data=payload, content_type="application/json")
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(AvailableSlot.objects.get(pk=self.slot1.pk).is_booked)
        appt = Appointment.objects.latest("id")
        self.assertEqual(appt.patient_name, "Alice Patient")
