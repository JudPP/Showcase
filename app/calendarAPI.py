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
    pass

def upload_calendar_event(datetime, duration, patient_name, doctor_name, id):
    pass

def clear_calendar_events():
    pass

def delete_calendar_event(appointment_id):
    pass

def get_calendar_events_for(doctor_name):
    pass