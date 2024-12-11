from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from datetime import datetime, timedelta

def get_available_events():
    # Replace these with your actual credentials file and token
    creds = Credentials.from_authorized_user_file('path/to/your/token.json')

    # Connect to Google Calendar API
    service = build('calendar', 'v3', credentials=creds)

    # Get events from the primary calendar for the next 7 days
    now = datetime.utcnow().isoformat() + 'Z'  # Current time in UTC
    one_week_later = (datetime.utcnow() + timedelta(days=7)).isoformat() + 'Z'

    events_result = service.events().list(
        calendarId='primary',
        timeMin=now,
        timeMax=one_week_later,
        singleEvents=True,
        orderBy='startTime'
    ).execute()

    events = events_result.get('items', [])

    # Format the events for frontend
    available_slots = []
    for event in events:
        available_slots.append({
            'summary': event.get('summary', 'No Title'),
            'start': event['start'].get('dateTime', event['start'].get('date')),
            'end': event['end'].get('dateTime', event['end'].get('date'))
        })

    return available_slots
