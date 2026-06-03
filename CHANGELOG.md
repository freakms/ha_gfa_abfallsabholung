# Changelog

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
