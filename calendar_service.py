import datetime
import os.path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/calendar"]

# Returns a service object for interacting with the Google Calendar API
def get_service():
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
    with open("token.json", "w") as token:
      token.write(creds.to_json())

  return build("calendar", "v3", credentials=creds)

# Returns a dic of calendars with their IDs for the user
def list_calendars(service):
  calendar_result = service.calendarList().list(maxResults=20).execute()
  calendars = calendar_result.get("items", [])
  calendars_by_summary = {calendar["summary"]: calendar["id"] for calendar in calendars}

  return calendars_by_summary

# Returns a list of events for a given calendar, optionally bounded by [time_min, time_max)
def list_events(service, calendar_id="primary", time_min=None, time_max=None, max_results=10):
  if time_min is None:
    time_min = datetime.datetime.now(tz=datetime.timezone.utc).isoformat()

  request_params = {
      "calendarId": calendar_id,
      "timeMin": time_min,
      "maxResults": max_results,
      "singleEvents": True,
      "orderBy": "startTime",
  }
  if time_max is not None:
    request_params["timeMax"] = time_max

  events_result = service.events().list(**request_params).execute()
  return events_result.get("items", [])


def create_event(
    service,
    calendar_id,
    summary,
    start,
    end,
    description=None,
    time_zone="America/Sao_Paulo",
):
  event_body = {
      "summary": summary,
      "start": {"dateTime": start, "timeZone": time_zone},
      "end": {"dateTime": end, "timeZone": time_zone},
  }
  if description:
    event_body["description"] = description

  return service.events().insert(calendarId=calendar_id, body=event_body).execute()


def move_event(
    service,
    calendar_id,
    event_id,
    new_start,
    new_end,
    time_zone="America/Sao_Paulo",
):
  event_body = {
      "start": {"dateTime": new_start, "timeZone": time_zone},
      "end": {"dateTime": new_end, "timeZone": time_zone},
  }
  return (
      service.events()
      .patch(calendarId=calendar_id, eventId=event_id, body=event_body)
      .execute()
  )


def delete_event(service, calendar_id, event_id):
  service.events().delete(calendarId=calendar_id, eventId=event_id).execute()
