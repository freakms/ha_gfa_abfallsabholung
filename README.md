# GFA Abfallkalender - Home Assistant Integration

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)
[![GitHub Release](https://img.shields.io/github/release/freakms/ha_gfa_abfallsabholung.svg)](https://github.com/freakms/ha_gfa_abfallsabholung/releases)

Eine Home Assistant Integration für den Abfallkalender der GFA Lüneburg. Die Integration lädt Abfalltermine direkt von der GFA-Webseite und kann automatische Alexa-Ansagen durchführen.

## ✨ Features

- 📍 **Direkte Adressauswahl**: Ort, Straße und Hausnummer werden direkt von der GFA-Webseite geladen
- 📅 **Sensoren**: Zeigt den nächsten Abholtermin für jede Abfallart an
- 🗓️ **Kalender-Entity**: Zeigt alle Termine im Home Assistant Kalender
- 🔊 **Alexa-Ankündigungen**: Automatische Ansagen über Alexa Media Player
- ⚙️ **Konfigurierbar**: Zeitpunkt, Alexa-Gerät und Abfallarten wählbar
- 🔇 **"Alexa Stop"**: Ansagen enden automatisch mit "Alexa Stop"

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

### 1. Integration hinzufügen

1. Gehen Sie zu **Einstellungen** → **Geräte & Dienste**
2. Klicken Sie auf **Integration hinzufügen**
3. Suchen Sie nach "GFA Abfallkalender"
4. Folgen Sie dem Einrichtungsassistenten:

#### Schritt 1: Ort auswählen
Wählen Sie Ihren Ort aus der Dropdown-Liste (z.B. "Lüneburg", "Adendorf", etc.)

#### Schritt 2: Straße auswählen
Nach der Ortsauswahl werden automatisch alle Straßen geladen.

#### Schritt 3: Hausnummer auswählen
Wählen Sie Ihre Hausnummer aus der Liste.

#### Schritt 4: Erinnerung konfigurieren
- **Tage vor der Abholung**: z.B. 1 Tag vorher
- **Uhrzeit**: z.B. 19:00 Uhr

#### Schritt 5: Alexa-Gerät auswählen
Wählen Sie das Alexa-Gerät für die Ansagen.

#### Schritt 6: Abfallarten auswählen
Wählen Sie, für welche Abfallarten Erinnerungen erfolgen sollen.

### 2. Voraussetzungen für Alexa-Ansagen

Für die Alexa-Ankündigungen benötigen Sie die **Alexa Media Player** Integration:

1. Installieren Sie [Alexa Media Player](https://github.com/alandtse/alexa_media_player) über HACS
2. Richten Sie die Integration mit Ihrem Amazon-Konto ein
3. Ihre Alexa-Geräte erscheinen dann als `media_player` Entities

## 📊 Sensoren

Die Integration erstellt folgende Sensoren:

| Sensor | Beschreibung |
|--------|-------------|
| `sensor.gfa_nachste_abholung` | Datum der nächsten Abholung (egal welche Art) |
| `sensor.gfa_restmuell` | Nächster Restmüll-Termin |
| `sensor.gfa_altpapier` | Nächster Altpapier-Termin |
| `sensor.gfa_gelber_sack` | Nächster Gelber Sack-Termin |
| `sensor.gfa_biotonne` | Nächster Biotonne-Termin |
| `sensor.gfa_gruenabfall` | Nächster Grünabfall-Termin |

### Sensor-Attribute

Jeder Sensor hat folgende Attribute:

- `waste_type`: Interne Bezeichnung der Abfallart
- `waste_type_name`: Deutscher Name der Abfallart
- `summary`: Original-Text aus dem Kalender
- `days_until`: Tage bis zur Abholung
- `is_tomorrow`: `true` wenn morgen abgeholt wird
- `is_today`: `true` wenn heute abgeholt wird

## 🔧 Services

### `gfa_abfallkalender.announce_pickup`

Sagt die nächste Abholung manuell über Alexa an.

```yaml
service: gfa_abfallkalender.announce_pickup
```

### `gfa_abfallkalender.refresh_calendar`

Aktualisiert die Kalenderdaten von der GFA-Webseite.

```yaml
service: gfa_abfallkalender.refresh_calendar
```

## 🔊 Alexa-Ansage Format

Die automatische Alexa-Ansage hat folgendes Format:

> "Abholtermin der GFA morgen. Abgeholt wird Altpapier. Alexa Stop."

Bei mehreren Abfallarten:

> "Abholtermin der GFA morgen. Abgeholt wird Restmüll und Gelber Sack. Alexa Stop."

Das "Alexa Stop" am Ende sorgt dafür, dass Alexa nicht auf weitere Befehle wartet.

## 📝 Beispiel-Automationen

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

### Licht blinken lassen bei Termin

```yaml
automation:
  - alias: "Müll-Erinnerung Licht"
    trigger:
      - platform: time
        at: "19:30:00"
    condition:
      - condition: state
        entity_id: sensor.gfa_nachste_abholung
        attribute: is_tomorrow
        state: true
    action:
      - repeat:
          count: 3
          sequence:
            - service: light.turn_on
              target:
                entity_id: light.flur
              data:
                color_name: yellow
            - delay: 1
            - service: light.turn_off
              target:
                entity_id: light.flur
            - delay: 1
```

## 🗑️ Unterstützte Abfallarten

Die Integration erkennt automatisch folgende Abfallarten:

| Abfallart | Erkannte Begriffe |
|-----------|-------------------|
| Restmüll | Restmüll, Restabfall, Hausmüll |
| Altpapier | Altpapier, Papier, Papiertonne |
| Gelber Sack | Gelber Sack, Wertstoffe, Verpackungen |
| Biotonne | Biotonne, Bioabfall |
| Grünabfall | Grünabfall, Gartenabfall, Laub |
| Sperrmüll | Sperrmüll, Altmetall |
| Schadstoffmobil | Schadstoffmobil, Problemstoffe |
| Weihnachtsbaum | Weihnachtsbaum, Christbaum |

## 🌍 Unterstützte Orte

Alle Orte im Landkreis Lüneburg werden unterstützt:

Adendorf, Amelinghausen, Amt Neuhaus, Artlenburg, Bardowick, Barendorf, Barnstedt, Barum, Betzendorf, Bleckede, Boitze, Brietlingen, Dahlem, Dahlenburg, Deutsch Evern, Echem, Embsen, Haar, Handorf, Hittbergen, Hohnstorf, Kaarßen, Kirchgellersen, Lüdersburg, **Lüneburg**, Mechtersen, Melbeck, Nahrendorf, Neetze, Oldendorf/Luhe, Radbruch, Rehlingen, Reinstorf, Reppenstedt, Rullstorf, Scharnebeck, Soderstorf, Stapel, Südergellersen, Sumte, Thomasburg, Tosterglope, Tripkau, Vastorf, Vögelsen, Wehningen, Wendisch Evern, Westergellersen, Wittorf

## ❓ Fehlerbehebung

### Orte/Straßen werden nicht geladen

- Prüfen Sie Ihre Internetverbindung
- Die GFA-Webseite könnte vorübergehend nicht erreichbar sein
- Versuchen Sie es später erneut

### Alexa sagt nichts an

1. Prüfen Sie, ob die Alexa Media Player Integration korrekt eingerichtet ist
2. Testen Sie die Ansage manuell:
   ```yaml
   service: gfa_abfallkalender.announce_pickup
   ```
3. Prüfen Sie die Home Assistant Logs auf Fehler

### Termine werden nicht aktualisiert

Die Daten werden alle 6 Stunden automatisch aktualisiert. Sie können manuell aktualisieren:
```yaml
service: gfa_abfallkalender.refresh_calendar
```

## 📜 Lizenz

MIT License - siehe [LICENSE](LICENSE)

## 🤝 Beitragen

Beiträge sind willkommen! Bitte öffnen Sie ein Issue oder Pull Request auf GitHub.

## 🔗 Links

- [GFA Lüneburg Webseite](https://www.gfa-lueneburg.de/)
- [GFA Abfuhrkalender](https://gfa-lueneburg.de/service/abfuhrkalender.html)
- [Alexa Media Player Integration](https://github.com/alandtse/alexa_media_player)
