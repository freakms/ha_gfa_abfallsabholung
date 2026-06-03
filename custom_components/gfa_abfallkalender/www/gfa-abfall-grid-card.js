/**
 * GFA Abfall Grid Card
 * Custom Lovelace card – zeigt Müllabholtermine als Kachel-Grid statt Liste.
 *
 * Konfiguration:
 *   type: custom:gfa-abfall-grid-card
 *   entity: sensor.gfa_kommende_termine   # Pflichtfeld
 *   title: Nächste Abholtermine           # optional (leer = kein Titel)
 *   columns: 3                            # Spalten im Grid (default: 3)
 *   icon_size: 48                         # Emoji-Schriftgröße in px (default: 48)
 *   show_date: true                       # Datum anzeigen (default: true)
 *   show_days_text: true                  # "Heute/Morgen/in X Tagen" anzeigen (default: true)
 *   max_items: 5                          # max. Kacheln (default: 5)
 */

const DEFAULTS = {
  title: 'Nächste Abholtermine',
  columns: 3,
  icon_size: 48,
  show_date: true,
  show_days_text: true,
  max_items: 5,
};

const URGENCY = {
  today:    { color: '#f44336', bg: 'rgba(244,67,54,0.12)',  badge: '🔴' },
  tomorrow: { color: '#ff9800', bg: 'rgba(255,152,0,0.12)',  badge: '🟠' },
  soon:     { color: '#f9a825', bg: 'rgba(249,168,37,0.12)', badge: '🟡' },
  normal:   { color: 'var(--primary-text-color)', bg: 'transparent', badge: '' },
};

function urgencyFor(days) {
  if (days === 0) return URGENCY.today;
  if (days === 1) return URGENCY.tomorrow;
  if (days <= 3)  return URGENCY.soon;
  return URGENCY.normal;
}

class GfaAbfallGridCard extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: 'open' });
  }

  setConfig(config) {
    if (!config.entity) {
      throw new Error(
        'GFA Abfall Grid Card: "entity" ist erforderlich, z.B. sensor.gfa_kommende_termine'
      );
    }
    this._config = { ...DEFAULTS, ...config };
    this._render();
  }

  set hass(hass) {
    this._hass = hass;
    this._render();
  }

  _render() {
    if (!this._hass || !this._config) return;

    const cfg = this._config;
    const stateObj = this._hass.states[cfg.entity];

    if (!stateObj) {
      this.shadowRoot.innerHTML = `
        <ha-card>
          <div style="padding:16px;color:var(--error-color,#f44336)">
            ⚠️ Entity nicht gefunden: <code>${cfg.entity}</code>
          </div>
        </ha-card>`;
      return;
    }

    const pickups = (stateObj.attributes.pickups || []).slice(0, cfg.max_items);
    const cols    = Math.max(1, Math.min(cfg.columns, 6));
    const iconPx  = Math.max(16, Math.min(cfg.icon_size, 120));

    const css = `
      :host { display: block; }
      ha-card { padding: 16px 16px 12px; }
      .card-title {
        font-size: 1em;
        font-weight: 600;
        color: var(--primary-text-color);
        margin-bottom: 14px;
        display: flex;
        align-items: center;
        gap: 6px;
      }
      .grid {
        display: grid;
        grid-template-columns: repeat(${cols}, 1fr);
        gap: 10px;
      }
      .tile {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: flex-start;
        padding: 12px 6px 10px;
        border-radius: 12px;
        border: 1px solid var(--divider-color, rgba(128,128,128,0.2));
        text-align: center;
        transition: transform 0.15s ease, box-shadow 0.15s ease;
        cursor: default;
      }
      .tile:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 14px rgba(0,0,0,0.15);
      }
      .tile-emoji {
        font-size: ${iconPx}px;
        line-height: 1.1;
        margin-bottom: 8px;
        user-select: none;
      }
      .tile-name {
        font-size: 0.72em;
        font-weight: 600;
        color: var(--primary-text-color);
        margin-bottom: 5px;
        line-height: 1.3;
        word-break: break-word;
        hyphens: auto;
      }
      .tile-days {
        font-size: 0.68em;
        font-weight: 700;
        padding: 2px 8px;
        border-radius: 10px;
        margin-bottom: 3px;
        white-space: nowrap;
      }
      .tile-date {
        font-size: 0.62em;
        color: var(--secondary-text-color);
      }
      .empty {
        grid-column: 1 / -1;
        padding: 20px;
        text-align: center;
        color: var(--secondary-text-color);
        font-size: 0.9em;
      }
    `;

    const tilesHtml = pickups.length === 0
      ? `<div class="empty">Keine bevorstehenden Abholtermine</div>`
      : pickups.map(p => {
          const u = urgencyFor(p.tage_bis);
          return `
            <div class="tile" style="background:${u.bg}">
              <div class="tile-emoji">${p.emoji}</div>
              <div class="tile-name">${p.abfallart_name}</div>
              ${cfg.show_days_text ? `
                <div class="tile-days" style="color:${u.color}">
                  ${u.badge ? u.badge + ' ' : ''}${p.tag_beschreibung}
                </div>` : ''}
              ${cfg.show_date ? `<div class="tile-date">${p.datum}</div>` : ''}
            </div>`;
        }).join('');

    this.shadowRoot.innerHTML = `
      <style>${css}</style>
      <ha-card>
        ${cfg.title
          ? `<div class="card-title"><span>🗑️</span><span>${cfg.title}</span></div>`
          : ''}
        <div class="grid">${tilesHtml}</div>
      </ha-card>`;
  }

  getCardSize() {
    const cfg  = this._config || DEFAULTS;
    const rows = Math.ceil(cfg.max_items / Math.max(1, cfg.columns));
    return rows + 1;
  }
}

customElements.define('gfa-abfall-grid-card', GfaAbfallGridCard);

window.customCards = window.customCards || [];
window.customCards.push({
  type:             'gfa-abfall-grid-card',
  name:             'GFA Abfall Grid Card',
  description:      'Zeigt die nächsten GFA Müllabholtermine als Kachel-Grid.',
  preview:          true,
  documentationURL: 'https://github.com/freakms/ha_gfa_abfallsabholung',
});
