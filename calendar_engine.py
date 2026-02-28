# calendar_engine.py

# Dictionary to store events in the format:
# {
#     "YYYY-MM-DD": {
#         "title": "Event Title",
#         "description": "Event Description"
#     }
# }
events_db = {
    "2026-03-02": {
        "title": "Date Night",
        "description": "Dinner at rooftop restaurant"
    },
    "2026-03-10": {
        "title": "Office Meeting",
        "description": "Quarterly review"
    }
}

def get_all_events():
    """Returns the current dictionary of events."""
    return events_db

def add_event(date_str, title, description):
    """Adds a new event to the dictionary cache."""
    events_db[date_str] = {
        "title": title,
        "description": description
    }
    return True
