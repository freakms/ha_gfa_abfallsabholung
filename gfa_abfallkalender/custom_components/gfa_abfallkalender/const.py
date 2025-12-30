"""Constants for GFA Abfallkalender integration."""
from datetime import timedelta

DOMAIN = "gfa_abfallkalender"

# Configuration keys
CONF_ICS_URL = "ics_url"
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
    "restmüll": ["restmüll", "restabfall", "hausmüll", "schwarze tonne"],
    "altpapier": ["altpapier", "papier", "pappe", "blaue tonne"],
    "gelber_sack": ["gelber sack", "gelbe tonne", "verpackungen", "leichtverpackungen", "wertstoffe"],
    "biotonne": ["biotonne", "bioabfall", "grüne tonne", "kompost"],
    "sperrmüll": ["sperrmüll", "sperrgut"],
    "schadstoffmobil": ["schadstoffmobil", "schadstoffe", "problemstoffe"],
    "weihnachtsbaum": ["weihnachtsbaum", "christbaum", "tannenbaum"],
    "grünabfall": ["grünabfall", "gartenabfall", "laub"],
}

# Friendly names for waste types
WASTE_TYPE_NAMES = {
    "restmüll": "Restmüll",
    "altpapier": "Altpapier",
    "gelber_sack": "Gelber Sack",
    "biotonne": "Biotonne",
    "sperrmüll": "Sperrmüll",
    "schadstoffmobil": "Schadstoffmobil",
    "weihnachtsbaum": "Weihnachtsbaum",
    "grünabfall": "Grünabfall",
}

# Icons for waste types
WASTE_TYPE_ICONS = {
    "restmüll": "mdi:trash-can",
    "altpapier": "mdi:newspaper-variant-multiple",
    "gelber_sack": "mdi:recycle",
    "biotonne": "mdi:leaf",
    "sperrmüll": "mdi:sofa",
    "schadstoffmobil": "mdi:bottle-tonic-skull",
    "weihnachtsbaum": "mdi:pine-tree",
    "grünabfall": "mdi:tree",
}

# Service names
SERVICE_ANNOUNCE = "announce_pickup"
SERVICE_REFRESH = "refresh_calendar"

# Platforms
PLATFORMS = ["sensor", "calendar"]
