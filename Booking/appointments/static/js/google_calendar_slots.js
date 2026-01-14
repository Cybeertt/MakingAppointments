// Fetch available slots from the backend
function fetchGoogleAvailableSlots() {
    const slotsContainer = document.getElementById('slots-container');
    
    fetch('/api/google-available-slots/')
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            // Clear the container
            slotsContainer.innerHTML = '';

            if (data.length === 0) {
                // No available slots
                const noSlotsMessage = document.createElement('p');
                noSlotsMessage.textContent = 'No available slots at the moment.';
                noSlotsMessage.classList.add('no-slots');
                slotsContainer.appendChild(noSlotsMessage);
                return;
            }

            // Render available slots
            data.forEach(slot => {
                const slotDiv = document.createElement('div');
                slotDiv.classList.add('slot');
                slotDiv.textContent = `${slot.summary || 'No Title'}: ${formatDate(slot.start)} to ${formatDate(slot.end)}`;
                
                // Add a click handler for booking (if required)
                slotDiv.addEventListener('click', () => {
                    alert(`You selected: ${slot.summary} from ${formatDate(slot.start)} to ${formatDate(slot.end)}`);
                });

                slotsContainer.appendChild(slotDiv);
            });
        })
        .catch(error => {
            slotsContainer.innerHTML = '<p>Error fetching available slots. Please try again later.</p>';
            console.error('Error fetching slots:', error);
        });
}

// Format date/time for display
function formatDate(datetime) {
    const dateObj = new Date(datetime);
    return dateObj.toLocaleString('en-US', {
        weekday: 'short',
        month: 'short',
        day: 'numeric',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
        hour12: true
    });
}

// Call the function on page load
document.addEventListener('DOMContentLoaded', fetchGoogleAvailableSlots);
