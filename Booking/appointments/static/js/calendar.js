

document.addEventListener("DOMContentLoaded", function () {
    // Fetch available slots from the API
    fetch('/api/google-available-slots/')
        .then(response => response.json())
        .then(data => {
            if (data.available_slots) {
                console.log('Available Slots:', data.available_slots);
                renderCalendar(data.available_slots);
            } else {
                console.error('Error:', data.error);
            }
        })
        .catch(error => console.error('Error fetching available slots:', error));
});

// Render the calendar with available slots
function renderCalendar(availableSlots) {
    const calendarDays = document.getElementById('calendar-days');
    const today = new Date();

    // Clear existing days
    calendarDays.innerHTML = '';

    for (let i = 0; i < 7; i++) {
        const currentDate = new Date(today.getTime() + i * 24 * 60 * 60 * 1000);
        const dayElement = document.createElement('div');
        dayElement.classList.add('day');
        dayElement.textContent = currentDate.toDateString();

        // Check if the date has available slots
        const slotsForDate = availableSlots.filter(slot => {
            const slotDate = new Date(slot.start).toDateString();
            return slotDate === currentDate.toDateString();
        });

        if (slotsForDate.length > 0) {
            dayElement.style.backgroundColor = '#d4edda'; // Highlight available days
            dayElement.addEventListener('click', () => showTimeSlots(slotsForDate));
        } else {
            dayElement.style.backgroundColor = '#f8d7da'; // No slots available
        }

        calendarDays.appendChild(dayElement);
    }
}

// Show time slots for a selected day
function showTimeSlots(slots) {
    const timeSlotsList = document.getElementById('time-slots-list');
    timeSlotsList.innerHTML = '';

    slots.forEach(slot => {
        const slotElement = document.createElement('div');
        slotElement.classList.add('time-slot');
        slotElement.textContent = `${new Date(slot.start).toLocaleTimeString()} - ${new Date(slot.end).toLocaleTimeString()}`;
        timeSlotsList.appendChild(slotElement);
    });

    document.getElementById('time-slots').style.display = 'block';
}

