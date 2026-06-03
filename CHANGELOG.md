# Changelog

## [v1.2.2] - 2026-06-03

### Bugfix
- **`register_static_path` entfernt** – in HA 2024.x+ existiert diese Methode nicht mehr (`AttributeError`). Die Lovelace Card JS-Datei wird jetzt beim HA-Start in den `www`-Ordner kopiert und ist zuverlässig über `/local/gfa-abfall-grid-card.js` erreichbar

### ⚠️ Ressource-URL hat sich geändert
Die Lovelace-Ressource muss einmalig angepasst werden:
- **Alt:** `/gfa_abfallkalender/gfa-abfall-grid-card.js`
- **Neu:** `/local/gfa-abfall-grid-card.js`

### Nach dem Update erforderlich
- [ ] **Home Assistant neu starten** (Datei wird beim Start kopiert)
- [ ] **Lovelace-Ressource aktualisieren**: Einstellungen → Dashboards → Ressourcen → alte URL ersetzen durch `/local/gfa-abfall-grid-card.js`
- [ ] Seite hart neu laden (`Strg+Shift+R`)

---

## [v1.2.1] - 2026-06-03

### Bugfix
- **Lovelace Card nicht geladen** (`Custom element doesn't exist`): `register_static_path` wird jetzt mit explizitem Dateipfad statt Verzeichnis aufgerufen – behebt den Fehler in allen HA-Versionen

### Nach dem Update erforderlich
- [ ] **Home Assistant neu starten**
- [ ] Seite im Browser hart neu laden (`Strg+Shift+R`)
- Die bereits eingetragene Ressource `/gfa_abfallkalender/gfa-abfall-grid-card.js` bleibt unverändert

---

## [v1.2.0] - 2026-06-03

### Neu
- **Custom Lovelace Grid Card** (`custom:gfa-abfall-grid-card`): Kachel-Grid statt Liste – große Emoji-Symbole, konfigurierbare Größe (16–120 px), Spalten (1–6) und Dringlichkeitsfarbcodierung (🔴 Heute · 🟠 Morgen · 🟡 in 2–3 Tagen)
- **GitHub Actions Workflow**: Releases werden automatisch per Tag-Push oder manueller Auslösung erstellt (inkl. ZIP-Asset)

### Geändert
- `__init__.py`: Statischer Pfad `/gfa_abfallkalender/` wird beim HA-Start automatisch registriert
- `manifest.json`: Version 1.1.4 → 1.2.0

### Nach dem Update erforderlich
- [ ] **Home Assistant neu starten**
- [ ] **Einmalig – Lovelace-Ressource hinzufügen** (nur wenn die Grid Card das erste Mal genutzt wird):
  Einstellungen → Dashboards → Ressourcen → `+`
  - URL: `/gfa_abfallkalender/gfa-abfall-grid-card.js`
  - Typ: `JavaScript-Modul`
- [ ] **Karte zum Dashboard hinzufügen** (Minimalbeispiel):
  ```yaml
  type: custom:gfa-abfall-grid-card
  entity: sensor.gfa_kommende_termine
  ```
  Alle Optionen → [README](https://github.com/freakms/ha_gfa_abfallsabholung#-gfa-abfall-grid-card-empfohlen)

---

## [v1.1.4] - 2026-04-16

### Neu
- Initiale stabile Version mit Sensoren, Kalender-Entity, Kommende-Termine-Sensor und Alexa-Integration

### Nach dem Update erforderlich
- [ ] Home Assistant neu starten
