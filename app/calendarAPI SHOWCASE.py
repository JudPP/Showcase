import datetime
import os.path
import pytz
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

#Used Googles Quick Start For Calendar API, 
#Python quickstart  |  google calendar  |  google for developers (no date) Google. Available at: https://developers.google.com/calendar/api/quickstart/python (Accessed: 01 May 2024). 

def get_calendar_events():
  
  SCOPES = ["https://www.googleapis.com/auth/calendar"]

  creds = None
  # The file token.json stores the user's access and refresh tokens, and is
  # created automatically when the authorization flow completes for the first
  # time.
  if os.path.exists("token.json"):
    creds = Credentials.from_authorized_user_file("token.json", SCOPES)
  # If there are no (valid) credentials available, let the user log in.
  if not creds or not creds.valid:
    if creds and creds.expired and creds.refresh_token:
      creds.refresh(Request())
    else:
      flow = InstalledAppFlow.from_client_secrets_file(
          "credentials.json", SCOPES
      )
      creds = flow.run_local_server(port=0)
    # Save the credentials for the next run
    with open("token.json", "w") as token:
      token.write(creds.to_json())

  try:
    service = build("calendar", "v3", credentials=creds)
    #todays schedule
    today = datetime.date.today().isoformat()

    # Call the Calendar API
    now = datetime.datetime.utcnow().isoformat() + "Z"  # 'Z' indicates UTC time
    print("Getting the upcoming 10 events")
    events_result = (
        service.events()
        .list(
            calendarId="primary",
            # timeMin=now,
            #todays schedule
            timeMin=today + "T00:00:00Z",
            timeMax=today + "T23:59:59Z",
            maxResults= 100,
            singleEvents=True,
            orderBy="startTime",
        )
        .execute()
    )
    events = events_result.get("items", [])

    if not events:
      print("No upcoming events found.")
      return

    # Prints the start and name of the next 10 events
    for event in events:
      start = event["start"].get("dateTime", event["start"].get("date"))
      print(start, event["summary"])
      
    return events

  except HttpError as error:
    print(f"An error occurred: {error}")

credentials_file = 'credentials.json'

if not os.path.exists(credentials_file):
  print(f"Error: File '{credentials_file}' not found.")
  print("Current Working Directory:", os.getcwd())
  # Handle the missing file situation (e.g., logging, raising an exception, etc.)
else:
  get_calendar_events()


def upload_calendar_event(datetime, duration, patient_name, doctor_name, id):
    """
    Uploads a new event to the user's primary calendar.
    """
    SCOPES = ["https://www.googleapis.com/auth/calendar"]

    # Load credentials
    creds = None
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                "credentials.json", SCOPES
            )
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open("token.json", "w") as token:
            token.write(creds.to_json())

    try:
        service = build("calendar", "v3", credentials=creds)

        # Convert datetime to GMT timezone
        gmt = pytz.timezone('GMT')
        start_datetime = datetime.astimezone(gmt)
        end_datetime = (datetime + duration).astimezone(gmt)

        # Create event body
        event = {
            "summary": "Appointment",
            "description": f"Patient: {patient_name}, Practitioner: {doctor_name}, Appointment ID: {id}",
            "start": {"dateTime": start_datetime.isoformat(), "timeZone": "GMT"},
            "end": {"dateTime": end_datetime.isoformat(), "timeZone": "GMT"},
        }

        # Upload event to the calendar
        service.events().insert(calendarId="primary", body=event).execute()
        print("Event added to the calendar successfully.")

    except HttpError as error:
        print(f"An error occurred: {error}")
        
        
def clear_calendar_events():
    """
    Clears all events from the user's primary calendar.
    """
    SCOPES = ["https://www.googleapis.com/auth/calendar"]

    # Load credentials
    creds = None
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                "credentials.json", SCOPES
            )
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open("token.json", "w") as token:
            token.write(creds.to_json())

    try:
        service = build("calendar", "v3", credentials=creds)

        # Retrieve all events from the calendar
        events_result = service.events().list(calendarId="primary").execute()
        events = events_result.get("items", [])

        # Delete each event from the calendar
        for event in events:
            service.events().delete(calendarId="primary", eventId=event["id"]).execute()
        
        print("All events deleted from the calendar.")

    except HttpError as error:
        print(f"An error occurred: {error}")


def delete_calendar_event(appointment_id):
    """
    Deletes the event associated with the given appointment ID from the user's primary calendar.
    """
    SCOPES = ["https://www.googleapis.com/auth/calendar"]

    # Load credentials
    creds = None
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                "credentials.json", SCOPES
            )
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open("token.json", "w") as token:
            token.write(creds.to_json())

    try:
        service = build("calendar", "v3", credentials=creds)

        # Retrieve all events from the calendar
        events_result = service.events().list(calendarId="primary").execute()
        events = events_result.get("items", [])

        # Find and delete the event associated with the given appointment ID
        for event in events:
            if "description" in event and f"Appointment ID: {appointment_id}" in event["description"]:
                service.events().delete(calendarId="primary", eventId=event["id"]).execute()
                print(f"Event with Appointment ID {appointment_id} deleted from the calendar.")
                return  # Exit function after deleting the first matching event

        print(f"No event found with Appointment ID {appointment_id}.")

    except HttpError as error:
        print(f"An error occurred: {error}")
        
        
def get_calendar_events_for(doctor_name):
    """
    Fetches calendar events for today where the description includes 'Doctor: [doctor_name]'.
    """
    SCOPES = ["https://www.googleapis.com/auth/calendar"]
    creds = None

    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                "credentials.json", SCOPES
            )
            creds = flow.run_local_server(port=0)

        # Save the credentials for the next run
        with open("token.json", "w") as token:
            token.write(creds.to_json())

    try:
        service = build("calendar", "v3", credentials=creds)
        today = datetime.date.today().isoformat()

        # Call the Calendar API
        events_result = service.events().list(
            calendarId="primary",
            timeMin=today + "T00:00:00Z",
            timeMax=today + "T23:59:59Z",
            maxResults=100,
            singleEvents=True,
            orderBy="startTime",
        ).execute()

        events = events_result.get("items", [])

        if not events:
            print("No upcoming events found.")
            return

        
        filtered_events = []
        for event in events:
            if "description" in event and f"Practitioner: {doctor_name}" in event["description"]:
                start = event["start"].get("dateTime", event["start"].get("date"))
                print(start, event["summary"])
                filtered_events.append(event)

        if not filtered_events:
            print(f"No events found for Doctor: {doctor_name}")
            return

        return filtered_events

    except HttpError as error:
        print(f"An error occurred: {error}")
        return None
    
    
    
def get_calendar_events():
    pass

def upload_calendar_event(datetime, duration, patient_name, doctor_name, id):
    pass

def clear_calendar_events():
    pass

def delete_calendar_event(appointment_id):
    pass

def get_calendar_events_for(doctor_name):
    pass