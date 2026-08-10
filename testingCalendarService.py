import calendar_service

#Getting the service and all calendars for the user
service = calendar_service.get_service()
calendars = calendar_service.list_calendars(service)

# Getting events for a specific calendar (e.g., "Faculdade")
events = calendar_service.list_events(service, calendar_id = calendars["Faculdade"])
for event in events:
    print(f"Event: {event['summary']} (ID: {event['id']})")

# Creating a new event in the "Faculdade" calendar
new_event = calendar_service.create_event(
    service,
    calendar_id=calendars["Faculdade"],
    summary="Teste de aula nova",
    start="2026-08-10T18:00:00",
    end="2026-08-10T19:00:00",
    description="This is a new event."
)
print(f"Created event: {new_event['summary']} (ID: {new_event['id']})")

# Moving an existing event to a new time
event_id_to_move = new_event['id']  # Use the ID of the newly created event
moved_event = calendar_service.move_event(
    service,
    calendar_id=calendars["Faculdade"],
    event_id=event_id_to_move,
    new_start="2026-08-11T20:00:00",
    new_end="2026-08-11T21:00:00"
)
print(f"Moved event: {moved_event['summary']} (ID: {moved_event['id']})")

# Deleting the moved event
service.events().delete(calendarId=calendars["Faculdade"], eventId=moved_event['id']).execute()
print(f"Deleted event with ID: {moved_event['id']}")


