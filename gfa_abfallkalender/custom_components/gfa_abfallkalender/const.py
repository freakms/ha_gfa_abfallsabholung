"""Constants for GFA Abfallkalender integration."""
from datetime import timedelta

DOMAIN = "gfa_abfallkalender"

# Configuration keys
CONF_ICS_URL = "ics_url"
CONF_CITY = "city"
CONF_STREET = "street"
CONF_HOUSE_NUMBER = "house_number"
CONF_REMINDER_TIME = "reminder_time"
CONF_REMINDER_DAYS_BEFORE = "reminder_days_before"
CONF_ALEXA_ENTITY = "alexa_entity"
CONF_WASTE_TYPES = "waste_types"
CONF_ENABLED_WASTE_TYPES = "enabled_waste_types"

# Default values
DEFAULT_REMINDER_TIME = "19:00"
DEFAULT_REMINDER_DAYS_BEFORE = 1
DEFAULT_SCAN_INTERVAL = timedelta(hours=6)

# Waste type mappings (German)
WASTE_TYPE_MAPPINGS = {
    "restmuell": ["restmüll", "restabfall", "restabfallbehälter", "restabfallbehaelter", "hausmüll", "schwarze tonne"],
    "altpapier": ["altpapier", "papier", "pappe", "papiertonne", "blaue tonne"],
    "gelber_sack": ["gelber sack", "gelbe tonne", "verpackungen", "leichtverpackungen", "wertstoffe"],
    "biotonne": ["biotonne", "bioabfall", "grüne tonne", "kompost", "bio"],
    "gruenabfall": ["grünabfall", "gruenabfall", "gartenabfall", "laub"],
    "sperrmuell": ["sperrmüll", "sperrmuell", "sperrgut", "altmetall"],
    "schadstoffmobil": ["schadstoffmobil", "schadstoffe", "problemstoffe"],
    "weihnachtsbaum": ["weihnachtsbaum", "christbaum", "tannenbaum"],
}

# Friendly names for waste types
WASTE_TYPE_NAMES = {
    "restmuell": "Restmüll",
    "altpapier": "Altpapier/Papiertonne",
    "gelber_sack": "Gelber Sack",
    "biotonne": "Biotonne",
    "gruenabfall": "Grünabfall",
    "sperrmuell": "Sperrmüll/Altmetall",
    "schadstoffmobil": "Schadstoffmobil",
    "weihnachtsbaum": "Weihnachtsbaum",
}

# Icons for waste types
WASTE_TYPE_ICONS = {
    "restmuell": "mdi:trash-can",
    "altpapier": "mdi:newspaper-variant-multiple",
    "gelber_sack": "mdi:recycle",
    "biotonne": "mdi:leaf",
    "gruenabfall": "mdi:tree",
    "sperrmuell": "mdi:sofa",
    "schadstoffmobil": "mdi:bottle-tonic-skull",
    "weihnachtsbaum": "mdi:pine-tree",
}

# Service names
SERVICE_ANNOUNCE = "announce_pickup"
SERVICE_REFRESH = "refresh_calendar"

# Platforms
PLATFORMS = ["sensor", "calendar"]
