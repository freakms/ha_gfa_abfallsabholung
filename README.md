# GFA Abfallkalender - Home Assistant Integration

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)
[![GitHub Release](https://img.shields.io/github/release/freakms/ha_gfa_abfallsabholung.svg)](https://github.com/freakms/ha_gfa_abfallsabholung/releases)

Eine Home Assistant Integration für den Abfallkalender der GFA Lüneburg. Die Integration lädt Abfalltermine direkt von der GFA-Webseite und kann automatische Alexa-Ansagen durchführen.

## ✨ Features

- 📍 **Direkte Adressauswahl**: Ort, Straße und Hausnummer werden direkt von der GFA-Webseite geladen
- 📅 **Sensoren**: Zeigt den nächsten Abholtermin für jede Abfallart an
- 🗓️ **Kalender-Entity**: Zeigt alle Termine im Home Assistant Kalender
- 📋 **Kommende Termine Sensor**: Zeigt die nächsten 5 Termine mit Emojis
- 🧩 **Custom Grid Card**: Kachel-Grid statt Liste – Symbolgröße konfigurierbar
- 🔊 **Alexa-Ankündigungen**: Automatische Ansagen über Alexa Media Player
- ⚙️ **Konfigurierbar**: Zeitpunkt, Alexa-Gerät und Abfallarten wählbar

## 📦 Installation

### HACS (empfohlen)

1. Öffnen Sie HACS in Home Assistant
2. Klicken Sie auf "Integrationen"
3. Klicken Sie auf die drei Punkte oben rechts → **"Benutzerdefinierte Repositories"**
4. Fügen Sie die Repository-URL hinzu: `https://github.com/freakms/ha_gfa_abfallsabholung`
5. Wählen Sie "Integration" als Kategorie
6. Klicken Sie auf "Hinzufügen"
7. Suchen Sie nach "GFA Abfallkalender" und installieren Sie es
8. **Starten Sie Home Assistant neu**

### Manuelle Installation

1. Kopieren Sie den Ordner `custom_components/gfa_abfallkalender` in Ihr Home Assistant `config/custom_components/` Verzeichnis
2. Starten Sie Home Assistant neu

## ⚙️ Konfiguration

### Integration hinzufügen

1. Gehen Sie zu **Einstellungen** → **Geräte & Dienste**
2. Klicken Sie auf **Integration hinzufügen**
3. Suchen Sie nach "GFA Abfallkalender"
4. Folgen Sie dem Einrichtungsassistenten (Ort → Straße → Hausnummer → Erinnerung → Alexa)

## 📊 Sensoren

| Sensor | Beschreibung |
|--------|-------------|
| `sensor.gfa_nachste_abholung` | Datum der nächsten Abholung |
| `sensor.gfa_kommende_termine` | **NEU!** Die nächsten 5 Termine mit Details |
| `sensor.gfa_restmuell` | Nächster Restmüll-Termin |
| `sensor.gfa_altpapier` | Nächster Altpapier-Termin |
| `sensor.gfa_gelber_sack` | Nächster Gelber Sack-Termin |
| `sensor.gfa_biotonne` | Nächster Biotonne-Termin |
| `sensor.gfa_gruenabfall` | Nächster Grünabfall-Termin |

## 🎨 Dashboard-Karten

### ⭐ GFA Abfall Grid Card (empfohlen)

Die mitgelieferte Custom Lovelace Card zeigt die Mülltermine als **Kachel-Grid** mit großen Emojis – statt einer Liste.

#### Einmalige Einrichtung: Lovelace-Ressource hinzufügen

1. Home Assistant → **Einstellungen** → **Dashboards**
2. Drei-Punkte-Menü oben rechts → **Ressourcen**
3. **+ Ressource hinzufügen** mit:
   - URL: `/gfa_abfallkalender/gfa-abfall-grid-card.js`
   - Ressourcentyp: **JavaScript-Modul**
4. Speichern und Seite neu laden

> **Alternativ** direkt in `configuration.yaml`:
> ```yaml
> lovelace:
>   resources:
>     - url: /gfa_abfallkalender/gfa-abfall-grid-card.js
>       type: module
> ```

#### Karte in Dashboard einfügen

```yaml
type: custom:gfa-abfall-grid-card
entity: sensor.gfa_kommende_termine
```

#### Alle Konfigurationsoptionen

```yaml
type: custom:gfa-abfall-grid-card
entity: sensor.gfa_kommende_termine  # Pflichtfeld
title: Nächste Abholtermine          # Kartentitel (leer lassen = kein Titel)
columns: 3                           # Spalten im Grid (1–6, default: 3)
icon_size: 48                        # Emoji-Größe in Pixeln (16–120, default: 48)
show_days_text: true                 # "Heute/Morgen/in X Tagen" anzeigen (default: true)
show_date: true                      # Datum unter dem Badge anzeigen (default: true)
max_items: 5                         # Maximale Kachelanzahl (default: 5)
```

**Farbcodierung:**
| Farbe | Bedeutung |
|:---:|---|
| 🔴 Rot | Abholung heute |
| 🟠 Orange | Abholung morgen |
| 🟡 Gelb | Abholung in 2–3 Tagen |
| – | Abholung in 4+ Tagen |

---

### Markdown-Karte: Nächste 5 Termine

Fügen Sie diese Markdown-Karte zu Ihrem Dashboard hinzu:

```yaml
type: markdown
title: 🗑️ Abfallkalender
content: >-
  {% set pickups = state_attr('sensor.gfa_kommende_termine', 'pickups') %}
  {% if pickups %}
  {% for p in pickups %}
  **{{ p.emoji }} {{ p.abfallart_name }}**
  {{ p.datum }} ({{ p.tag_beschreibung }})

  {% endfor %}
  {% else %}
  Keine Termine gefunden
  {% endif %}
```

### Erweiterte Markdown-Karte mit Farben

```yaml
type: markdown
title: 🗑️ GFA Abfallkalender
content: >-
  {% set pickups = state_attr('sensor.gfa_kommende_termine', 'pickups') %}
  {% if pickups %}
  | | Abfallart | Datum | |
  |:---:|:---|:---|:---:|
  {% for p in pickups %}
  | {{ p.emoji }} | **{{ p.abfallart_name }}** | {{ p.datum }} | {% if p.tage_bis == 0 %}🔴 Heute{% elif p.tage_bis == 1 %}🟠 Morgen{% elif p.tage_bis <= 3 %}🟡 {{ p.tag_beschreibung }}{% else %}{{ p.tag_beschreibung }}{% endif %} |
  {% endfor %}
  {% else %}
  *Keine Termine gefunden*
  {% endif %}
```

### Entities-Karte

```yaml
type: entities
title: Nächste Abholtermine
entities:
  - entity: sensor.gfa_nachste_abholung
    name: Nächste Abholung
  - entity: sensor.gfa_restmuell
    name: Restmüll
    icon: mdi:trash-can
  - entity: sensor.gfa_altpapier
    name: Altpapier
    icon: mdi:newspaper-variant-multiple
  - entity: sensor.gfa_gelber_sack
    name: Gelber Sack
    icon: mdi:recycle
  - entity: sensor.gfa_biotonne
    name: Biotonne
    icon: mdi:leaf
  - entity: sensor.gfa_gruenabfall
    name: Grünabfall
    icon: mdi:tree
```

### Kompakte Glance-Karte

```yaml
type: glance
title: Abfalltermine
entities:
  - entity: sensor.gfa_restmuell
    name: Restmüll
  - entity: sensor.gfa_altpapier
    name: Papier
  - entity: sensor.gfa_gelber_sack
    name: Gelb
  - entity: sensor.gfa_biotonne
    name: Bio
columns: 4
```

### Custom Button Card (falls installiert)

Wenn Sie [button-card](https://github.com/custom-cards/button-card) installiert haben:

```yaml
type: custom:button-card
entity: sensor.gfa_kommende_termine
name: Nächster Abholtermin
show_state: false
show_icon: true
icon: mdi:trash-can-outline
styles:
  card:
    - padding: 16px
  icon:
    - width: 40px
    - color: var(--primary-color)
custom_fields:
  info: |
    [[[
      var pickups = entity.attributes.pickups;
      if (pickups && pickups.length > 0) {
        var p = pickups[0];
        return `<div style="text-align: center;">
          <div style="font-size: 2em;">${p.emoji}</div>
          <div style="font-weight: bold;">${p.abfallart_name}</div>
          <div>${p.datum}</div>
          <div style="color: var(--secondary-text-color);">${p.tag_beschreibung}</div>
        </div>`;
      }
      return 'Keine Termine';
    ]]]
```

## 🔔 Alexa-Ansagen

Die automatische Alexa-Ansage erfolgt zur konfigurierten Zeit (z.B. 19:00 Uhr, 1 Tag vorher):

> "Abholtermin der GFA morgen. Abgeholt wird Gelbe Tonne und Biotonne. Alexa Stop."

## 🔧 Services

| Service | Beschreibung |
|---------|-------------|
| `gfa_abfallkalender.announce_pickup` | Manuelle Alexa-Ansage auslösen |
| `gfa_abfallkalender.refresh_calendar` | Kalenderdaten aktualisieren |

## 📝 Beispiel-Automationen

### Morgendliche Handy-Benachrichtigung

```yaml
automation:
  - alias: "Abfall Push morgens"
    trigger:
      - platform: time
        at: "07:00:00"
    condition:
      - condition: template
        value_template: "{{ state_attr('sensor.gfa_nachste_abholung', 'is_today') }}"
    action:
      - service: notify.mobile_app
        data:
          title: "🗑️ Heute Abholung!"
          message: "{{ state_attr('sensor.gfa_nachste_abholung', 'waste_type_name') }} wird heute abgeholt."
```

## 🗑️ Unterstützte Abfallarten

| Emoji | Abfallart | Icon |
|:---:|---|---|
| 🗑️ | Restmüll | mdi:trash-can |
| 📰 | Altpapier/Papiertonne | mdi:newspaper-variant-multiple |
| ♻️ | Gelber Sack/Gelbe Tonne | mdi:recycle |
| 🌱 | Biotonne | mdi:leaf |
| 🌳 | Grünabfall | mdi:tree |
| 🛋️ | Sperrmüll/Altmetall | mdi:sofa |
| ☣️ | Schadstoffmobil | mdi:bottle-tonic-skull |
| 🎄 | Weihnachtsbaum | mdi:pine-tree |

## 🌍 Unterstützte Orte

Alle Orte im Landkreis Lüneburg werden unterstützt (Adendorf, Amelinghausen, Lüneburg, Bleckede, etc.)

## ❓ Fehlerbehebung

### Sensoren zeigen keine Daten
- Die Integration holt Daten für das aktuelle UND nächste Jahr
- Starten Sie Home Assistant neu nach der Installation
- Prüfen Sie die Logs unter Einstellungen → System → Protokolle

### Alexa sagt nichts an
1. Prüfen Sie, ob Alexa Media Player korrekt eingerichtet ist
2. Testen Sie manuell: `service: gfa_abfallkalender.announce_pickup`

## 📜 Lizenz

MIT License

## 🔗 Links

- [GFA Lüneburg](https://www.gfa-lueneburg.de/)
- [Alexa Media Player](https://github.com/alandtse/alexa_media_player)
