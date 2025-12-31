
Action: file_editor view /app/ha_gfa_abfallsabholung/custom_components/gfa_abfallkalender/sensor.py
Observation: /app/ha_gfa_abfallsabholung/custom_components/gfa_abfallkalender/sensor.py:
1|"""Sensor platform for GFA Abfallkalender."""
2|from datetime import datetime
3|import logging
4|
5|from homeassistant.components.sensor import SensorEntity, SensorDeviceClass
6|from homeassistant.config_entries import ConfigEntry
7|from homeassistant.core import HomeAssistant, callback
8|from homeassistant.helpers.entity_platform import AddEntitiesCallback
9|from homeassistant.helpers.update_coordinator import CoordinatorEntity
10|
11|from .const import (
12|    DOMAIN,
13|    WASTE_TYPE_NAMES,
14|    WASTE_TYPE_ICONS,
15|)
16|from .coordinator import GFADataCoordinator
17|
18|_LOGGER = logging.getLogger(__name__)
19|
20|# Emoji mappings for waste types (for dashboard display)
21|WASTE_TYPE_EMOJIS = {
22|    "restmuell": "🗑️",
23|    "altpapier": "📰",
24|    "gelber_sack": "♻️",
25|    "biotonne": "🌱",
26|    "gruenabfall": "🌳",
27|    "sperrmuell": "🛋️",
28|    "schadstoffmobil": "☣️",
29|    "weihnachtsbaum": "🎄",
30|    "unknown": "📦",
31|}
32|
33|
34|async def async_setup_entry(
35|    hass: HomeAssistant,
36|    entry: ConfigEntry,
37|    async_add_entities: AddEntitiesCallback,
38|) -> None:
39|    """Set up GFA Abfallkalender sensors."""
40|    coordinator: GFADataCoordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
41|
42|    # Wait for first data fetch
43|    if not coordinator.data:
44|        await coordinator.async_refresh()
45|
46|    # Create sensors for each waste type found
47|    entities = []
48|    
49|    # Add a general "next pickup" sensor
50|    entities.append(GFANextPickupSensor(coordinator, entry))
51|    
52|    # Add "next 5 pickups" sensor for dashboard
53|    entities.append(GFAUpcomingPickupsSensor(coordinator, entry))
54|
55|    # Add sensors for each waste type
56|    waste_types = coordinator.get_all_waste_types()
57|    for waste_type in waste_types:
58|        entities.append(GFAWasteTypeSensor(coordinator, entry, waste_type))
59|
60|    async_add_entities(entities)
61|
62|
63|class GFANextPickupSensor(CoordinatorEntity, SensorEntity):
64|    """Sensor for the next waste pickup."""
65|
66|    _attr_device_class = SensorDeviceClass.DATE
67|    _attr_icon = "mdi:trash-can-outline"
68|
69|    def __init__(
70|        self,
71|        coordinator: GFADataCoordinator,
72|        entry: ConfigEntry,
73|    ) -> None:
74|        """Initialize the sensor."""
75|        super().__init__(coordinator)
76|        self._entry = entry
77|        self._attr_unique_id = f"{entry.entry_id}_next_pickup"
78|        self._attr_name = "GFA Nächste Abholung"
79|
80|    @property
81|    def native_value(self):
82|        """Return the next pickup date."""
83|        pickup = self.coordinator.get_next_pickup()
84|        if pickup:
85|            return pickup["date"]
86|        return None
87|
88|    @property
89|    def extra_state_attributes(self):
90|        """Return additional attributes."""
91|        pickup = self.coordinator.get_next_pickup()
92|        if pickup:
93|            days_until = (pickup["date"] - datetime.now().date()).days
94|            return {
95|                "waste_type": pickup["waste_type"],
96|                "waste_type_name": WASTE_TYPE_NAMES.get(
97|                    pickup["waste_type"], pickup["summary"]
98|                ),
99|                "summary": pickup["summary"],
100|                "days_until": days_until,
101|                "is_tomorrow": days_until == 1,
102|                "is_today": days_until == 0,
103|            }
104|        return {}
105|
106|
107|class GFAUpcomingPickupsSensor(CoordinatorEntity, SensorEntity):
108|    """Sensor showing the next 5 upcoming waste pickups."""
109|
110|    _attr_icon = "mdi:calendar-check"
111|
112|    def __init__(
113|        self,
114|        coordinator: GFADataCoordinator,
115|        entry: ConfigEntry,
116|    ) -> None:
117|        """Initialize the sensor."""
118|        super().__init__(coordinator)
119|        self._entry = entry
120|        self._attr_unique_id = f"{entry.entry_id}_upcoming_pickups"
121|        self._attr_name = "GFA Kommende Termine"
122|
123|    @property
124|    def native_value(self):
125|        """Return the count of upcoming pickups."""
126|        if self.coordinator.data:
127|            events = self.coordinator.data.get("events", [])
128|            today = datetime.now().date()
129|            upcoming = [e for e in events if e["date"] >= today][:5]
130|            return len(upcoming)
131|        return 0
132|
133|    @property
134|    def extra_state_attributes(self):
135|        """Return the next 5 pickups as attributes."""
136|        if not self.coordinator.data:
137|            return {}
138|        
139|        events = self.coordinator.data.get("events", [])
140|        today = datetime.now().date()
141|        upcoming = [e for e in events if e["date"] >= today][:5]
142|        
143|        attributes = {
144|            "pickups": [],
145|            "pickup_count": len(upcoming),
146|        }
147|        
148|        # German weekday names
149|        weekdays_de = ["Mo", "Di", "Mi", "Do", "Fr", "Sa", "So"]
150|        
151|        for i, event in enumerate(upcoming, 1):
152|            waste_type = event.get("waste_type", "unknown")
153|            event_date = event["date"]
154|            days_until = (event_date - today).days
155|            
156|            # Format date nicely
157|            weekday = weekdays_de[event_date.weekday()]
158|            date_str = event_date.strftime(f"{weekday}, %d.%m.%Y")
159|            
160|            # Day description
161|            if days_until == 0:
162|                day_desc = "Heute"
163|            elif days_until == 1:
164|                day_desc = "Morgen"
165|            elif days_until == 2:
166|                day_desc = "Übermorgen"
167|            else:
168|                day_desc = f"in {days_until} Tagen"
169|            
170|            pickup_data = {
171|                "nummer": i,
172|                "datum": date_str,
173|                "datum_iso": event_date.isoformat(),
174|                "tage_bis": days_until,
175|                "tag_beschreibung": day_desc,
176|                "abfallart": waste_type,
177|                "abfallart_name": WASTE_TYPE_NAMES.get(waste_type, event.get("summary", waste_type)),
178|                "icon": WASTE_TYPE_ICONS.get(waste_type, "mdi:trash-can"),
179|                "emoji": WASTE_TYPE_EMOJIS.get(waste_type, "📦"),
180|                "beschreibung": event.get("summary", ""),
181|            }
182|            attributes["pickups"].append(pickup_data)
183|            
184|            # Also add as individual attributes for easier template access
185|            attributes[f"termin_{i}_datum"] = date_str
186|            attributes[f"termin_{i}_typ"] = WASTE_TYPE_NAMES.get(waste_type, waste_type)
187|            attributes[f"termin_{i}_emoji"] = WASTE_TYPE_EMOJIS.get(waste_type, "📦")
188|            attributes[f"termin_{i}_tage"] = days_until
189|            attributes[f"termin_{i}_icon"] = WASTE_TYPE_ICONS.get(waste_type, "mdi:trash-can")
190|        
191|        return attributes
192|
193|
194|class GFAWasteTypeSensor(CoordinatorEntity, SensorEntity):
195|    """Sensor for a specific waste type."""
196|
197|    _attr_device_class = SensorDeviceClass.DATE
198|
199|    def __init__(
200|        self,
201|        coordinator: GFADataCoordinator,
202|        entry: ConfigEntry,
203|        waste_type: str,
204|    ) -> None:
205|        """Initialize the sensor."""
206|        super().__init__(coordinator)
207|        self._entry = entry
208|        self._waste_type = waste_type
209|        self._attr_unique_id = f"{entry.entry_id}_{waste_type}"
210|        self._attr_name = f"GFA {WASTE_TYPE_NAMES.get(waste_type, waste_type)}"
211|        self._attr_icon = WASTE_TYPE_ICONS.get(waste_type, "mdi:trash-can")
212|
213|    @property
214|    def native_value(self):
215|        """Return the next pickup date for this waste type."""
216|        pickup = self.coordinator.get_next_pickup(self._waste_type)
217|        if pickup:
218|            return pickup["date"]
219|        return None
220|
221|    @property
222|    def extra_state_attributes(self):
223|        """Return additional attributes."""
224|        pickup = self.coordinator.get_next_pickup(self._waste_type)
225|        if pickup:
226|            days_until = (pickup["date"] - datetime.now().date()).days
227|            return {
228|                "summary": pickup["summary"],
229|                "days_until": days_until,
230|                "is_tomorrow": days_until == 1,
231|                "is_today": days_until == 0,
232|                "emoji": WASTE_TYPE_EMOJIS.get(self._waste_type, "📦"),
233|            }
234|        return {}
235|
