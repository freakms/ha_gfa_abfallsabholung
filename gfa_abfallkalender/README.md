# GFA Abfallkalender - Home Assistant Integration

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)
[![GitHub Release](https://img.shields.io/github/release/your-username/gfa_abfallkalender.svg)](https://github.com/your-username/gfa_abfallkalender/releases)

Eine Home Assistant Integration für Abfallkalender der GFA (z.B. GFA Lüneburg). Die Integration liest ICS-Kalender aus und kann die Abholtermine automatisch über Alexa ansagen.

## Features

- 📅 **ICS-Kalender Import**: Importiert Abfalltermine aus einem ICS-Kalender
- 📱 **Sensoren**: Zeigt den nächsten Abholtermin für jede Abfallart an
- 🗓️ **Kalender-Entity**: Zeigt alle Termine im Home Assistant Kalender
- 🔊 **Alexa-Ankündigungen**: Automatische Ansagen über Alexa Media Player
- ⚙️ **Konfigurierbar**: Zeitpunkt, Alexa-Gerät und Abfallarten wählbar

## Installation

### HACS (empfohlen)

1. Öffnen Sie HACS in Home Assistant
2. Klicken Sie auf "Integrationen"
3. Klicken Sie auf die drei Punkte oben rechts → "Benutzerdefinierte Repositories"
4. Fügen Sie die Repository-URL hinzu: `https://github.com/your-username/gfa_abfallkalender`
5. Wählen Sie "Integration" als Kategorie
6. Klicken Sie auf "Hinzufügen"
7. Suchen Sie nach "GFA Abfallkalender" und installieren Sie es
8. Starten Sie Home Assistant neu

### Manuelle Installation

1. Kopieren Sie den Ordner `custom_components/gfa_abfallkalender` in Ihr Home Assistant `config/custom_components/` Verzeichnis
2. Starten Sie Home Assistant neu

## Konfiguration

### 1. Integration hinzufügen

1. Gehen Sie zu **Einstellungen** → **Geräte & Dienste**
2. Klicken Sie auf **Integration hinzufügen**
3. Suchen Sie nach "GFA Abfallkalender"
4. Folgen Sie dem Einrichtungsassistenten:
   - **ICS-URL**: Die URL zu Ihrem Abfallkalender (aus der GFA-App oder Webseite)
   - **Erinnerungszeit**: Wann soll Alexa erinnern? (z.B. 1 Tag vorher um 19:00)
   - **Alexa-Gerät**: Welches Gerät soll die Ansage machen?
   - **Abfallarten**: Für welche Abfallarten sollen Erinnerungen erfolgen?

### 2. Voraussetzungen für Alexa-Ansagen

Für die Alexa-Ankündigungen benötigen Sie die **Alexa Media Player** Integration:

1. Installieren Sie [Alexa Media Player](https://github.com/alandtse/alexa_media_player) über HACS
2. Richten Sie die Integration mit Ihrem Amazon-Konto ein
3. Ihre Alexa-Geräte erscheinen dann als `media_player` Entities

## Sensoren

Die Integration erstellt folgende Sensoren:

| Sensor | Beschreibung |
|--------|-------------|
| `sensor.gfa_nachste_abholung` | Datum der nächsten Abholung (egal welche Art) |
| `sensor.gfa_restmull` | Nächster Restmüll-Termin |
| `sensor.gfa_altpapier` | Nächster Altpapier-Termin |
| `sensor.gfa_gelber_sack` | Nächster Gelber Sack-Termin |
| `sensor.gfa_biotonne` | Nächster Biotonne-Termin |
| ... | (weitere je nach Kalender) |

### Sensor-Attribute

Jeder Sensor hat folgende Attribute:

- `waste_type`: Interne Bezeichnung der Abfallart
- `waste_type_name`: Deutscher Name der Abfallart
- `summary`: Original-Text aus dem Kalender
- `days_until`: Tage bis zur Abholung
- `is_tomorrow`: `true` wenn morgen abgeholt wird
- `is_today`: `true` wenn heute abgeholt wird

## Services

### `gfa_abfallkalender.announce_pickup`

Sagt die nächste Abholung manuell über Alexa an.

```yaml
service: gfa_abfallkalender.announce_pickup
```

### `gfa_abfallkalender.refresh_calendar`

Aktualisiert die Kalenderdaten vom ICS-Server.

```yaml
service: gfa_abfallkalender.refresh_calendar
```

## Beispiel-Automationen

### Zusätzliche Erinnerung am Morgen

```yaml
automation:
  - alias: "Abfall Morgenerinnerung"
    trigger:
      - platform: time
        at: "07:00:00"
    condition:
      - condition: state
        entity_id: sensor.gfa_nachste_abholung
        attribute: is_today
        state: true
    action:
      - service: gfa_abfallkalender.announce_pickup
```

### Benachrichtigung auf dem Handy

```yaml
automation:
  - alias: "Abfall Push-Benachrichtigung"
    trigger:
      - platform: time
        at: "18:00:00"
    condition:
      - condition: state
        entity_id: sensor.gfa_nachste_abholung
        attribute: is_tomorrow
        state: true
    action:
      - service: notify.mobile_app_mein_handy
        data:
          title: "Abholtermin morgen!"
          message: "Morgen wird {{ state_attr('sensor.gfa_nachste_abholung', 'waste_type_name') }} abgeholt."
```

## Alexa-Ansage Format

Die automatische Alexa-Ansage hat folgendes Format:

> "Abholtermin der GFA morgen. Abgeholt wird Altpapier. Alexa Stop."

Bei mehreren Abfallarten:

> "Abholtermin der GFA morgen. Abgeholt wird Restmüll und Gelber Sack. Alexa Stop."

Das "Alexa Stop" am Ende sorgt dafür, dass Alexa nicht auf weitere Befehle wartet.

## Unterstützte Abfallarten

Die Integration erkennt automatisch folgende Abfallarten anhand der Kalendereinträge:

- Restmüll
- Altpapier
- Gelber Sack / Wertstoffe
- Biotonne
- Sperrmüll
- Schadstoffmobil
- Weihnachtsbaum
- Grünabfall

Falls Ihre Abfallart nicht erkannt wird, wird sie als "Unbekannt" mit dem Original-Text aus dem Kalender angezeigt.

## ICS-URL finden

### GFA Lüneburg

1. Gehen Sie auf [gfa-lueneburg.de](https://gfa-lueneburg.de)
2. Navigieren Sie zum Abfallkalender
3. Geben Sie Ihre Adresse ein
4. Exportieren Sie den Kalender als ICS-Datei oder kopieren Sie die Kalender-URL

### Allgemein

Die meisten Abfallgesellschaften bieten einen ICS-Export an. Suchen Sie nach:
- "Kalender exportieren"
- "ICS Download"
- "Kalender abonnieren"

## Fehlerbehebung

### Kalender wird nicht geladen

- Prüfen Sie, ob die ICS-URL direkt im Browser erreichbar ist
- Stellen Sie sicher, dass die URL mit `http://` oder `https://` beginnt
- Einige Kalender erfordern aktuelle Adressparameter in der URL

### Alexa sagt nichts an

- Prüfen Sie, ob die Alexa Media Player Integration funktioniert
- Testen Sie die Ansage manuell über den Service `gfa_abfallkalender.announce_pickup`
- Prüfen Sie die Home Assistant Logs auf Fehler

### Abfallart wird nicht erkannt

Die Integration verwendet Schlüsselwörter zur Erkennung. Falls Ihre Abfallgesellschaft andere Bezeichnungen verwendet, öffnen Sie bitte ein Issue auf GitHub.

## Lizenz

MIT License - siehe [LICENSE](LICENSE)

## Beitragen

Beiträge sind willkommen! Bitte öffnen Sie ein Issue oder Pull Request auf GitHub.
