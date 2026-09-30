"""
Google Calendar tool for the agent. Uses a service account so the
container never needs an interactive OAuth consent flow -- the trade-off
is that the service account's email must be added as a collaborator on
the calendar it's writing to (Calendar settings -> Share with specific
people -> add the service account's `client_email`, "Make changes to
events" permission).

Setup:
1. Google Cloud Console -> create/select a project -> enable the
   "Google Calendar API".
2. IAM & Admin -> Service Accounts -> create one -> Keys -> Add key ->
   JSON. Save it somewhere NOT committed to git.
3. Share the target calendar with the service account's `client_email`
   (found inside the downloaded JSON file).
4. Set GOOGLE_SERVICE_ACCOUNT_FILE (path to that JSON, mounted into the
   container) and GOOGLE_CALENDAR_ID (the calendar's ID -- usually just
   the owner's email address for their primary calendar) for each agent.
"""
from functools import lru_cache

from google.oauth2 import service_account
from googleapiclient.discovery import build

from . import config

SCOPES = ["https://www.googleapis.com/auth/calendar"]


@lru_cache(maxsize=1)
def _service():
    creds = service_account.Credentials.from_service_account_file(
        config.GOOGLE_SERVICE_ACCOUNT_FILE, scopes=SCOPES
    )
    return build("calendar", "v3", credentials=creds, cache_discovery=False)


def create_event(summary: str, start_iso: str, end_iso: str, attendees: list[str] | None = None) -> dict:
    """
    start_iso / end_iso must be RFC3339 datetimes with a timezone offset,
    e.g. "2026-09-10T14:00:00+05:30". Returns the created event resource
    (includes 'id' and 'htmlLink').
    """
    body = {
        "summary": summary,
        "start": {"dateTime": start_iso},
        "end": {"dateTime": end_iso},
    }
    if attendees:
        body["attendees"] = [{"email": a} for a in attendees]

    service = _service()
    return service.events().insert(calendarId=config.GOOGLE_CALENDAR_ID, body=body).execute()


def list_upcoming_events(max_results: int = 10) -> list[dict]:
    """Used to check availability before proposing a time."""
    import datetime

    service = _service()
    now = datetime.datetime.utcnow().isoformat() + "Z"
    result = (
        service.events()
        .list(
            calendarId=config.GOOGLE_CALENDAR_ID,
            timeMin=now,
            maxResults=max_results,
            singleEvents=True,
            orderBy="startTime",
        )
        .execute()
    )
    return result.get("items", [])
