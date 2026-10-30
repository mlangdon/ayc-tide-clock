import base64
import os

img_path = 'ayc_burgee_small.png' if os.path.exists('ayc_burgee_small.png') else '../ayc_burgee_small.png'
with open(img_path, 'rb') as f:
    b64 = base64.b64encode(f.read()).decode('utf-8')

template = """/**
 * Atlantis Yacht Club (AYC) - Mobile Tide Clock & Harbor Dashboard
 * Dedicated Mobile Web Component (<ayc-tide-mobile>) & Embeddable App
 * Optimized for Smart Phones, Narrow Touch Viewports (320px - 480px) & Web Views
 */
(function() {
  'use strict';

  const _K = 'NjNiMWRlZTctNDUzYS00OWNkLWJlNWMtOWM5MDVjMjBmYTc1';
  const TEMPEST_TOKEN = atob(_K);
  const TEMPEST_STATION_ID = 141221;
  const TEMPEST_URL = 'https://tempestwx.com/station/141221/';
  const BURGEE_B64 = 'data:image/png;base64,BURGEE_BASE64_PLACEHOLDER';

  const SEA_BRIGHT_MHW_CLEARANCE = 15.0; // ft
  const SEA_BRIGHT_MHW_DATUM = 3.64;     // ft MLLW
  const HIGHLANDS_MHW_CLEARANCE = 65.0;  // ft
  const HIGHLANDS_MHW_DATUM = 4.41;      // ft MLLW

  const AYC_STATION = {
    name: 'Atlantis Yacht Club (Channel Hydro-Model)',
    coords: '40°20\\'12.7"N 73°58\\'42.7"W',
    noaa_id: '8531680',
    offset_high_min: 107,
    offset_low_min: 115,
    height_mult: 0.62,
    mean_range: 2.50
  };

  const THEMES = {
    ayc_navy: {
      name: 'Atlantis Yacht Club Official',
      window_bg: '#0F1E33',
      card_bg: '#162840',
      card_border: '#274266',
      header_bg: '#1D3557',
      text_primary: '#F1FAEE',
      text_secondary: '#A8DADC',
      accent: '#E6A13B',        // Nautical Gold
      accent_blue: '#457B9D',   // AYC Ocean Blue
      link_blue: '#1E7ABE',
      dial_bg: '#0A1524',
      bezel_main: '#B38728',
      bezel_light: '#FDE68A',
      bezel_shadow: '#101D2E',
      bezel_outer: '#060D17',
      high_badge_bg: '#5E1B24',
      high_badge_fg: '#FF8A9B',
      low_badge_bg: '#173C66',
      low_badge_fg: '#A8DADC',
      rising_color: '#457B9D',
      falling_color: '#E63946'
    }
  };

  class AYCTideMobileWidget extends HTMLElement {
    static get observedAttributes() {
      return [
        'show-dial', 'dial-size', 'show-weather', 'show-forecast',
        'show-bridges', 'show-currents', 'show-table', 'show-wave',
        'tide-count', 'compact', 'theme'
      ];
    }

    constructor() {
      super();
      this.attachShadow({ mode: 'open' });
      this.theme = THEMES.ayc_navy;
      this.currentMode = 'api';
      this.currentAngle = 0;
      this.tideStatus = { state: 'CALCULATING', countdown_str: '--', water_level_pct: 50, is_falling: false };
      this.moonInfo = { phaseName: 'Calculating...', icon: '🌕', illumination: 100, tideType: 'Spring Tide', tideSub: 'Strongest currents' };
      this.allPredictions = [];
      this.tideEvents = [];
      this.sbPredictions = [];
      this.hlPredictions = [];
      this.apiCurrentEvents = [];
      this.weather = {
        temp_f: null, feels_f: null, cond: 'Connecting...', icon: '🌤',
        wind_kts: null, wind_gust: null, wind_card: '--', wind_deg: null,
        press_inhg: null, press_mb: null, press_trend: 'steady',
        humidity: null, dew_f: null, rain_rate: 0, rain_today: 0, uv: 0, solar: 0,
        is_live: false, forecast_3day: []
      };
      this.currents = { speed: '0.0', state: 'SLACK', dir: 'Slack', method: 'API', arrow: '◆' };
      this.sbClearance = { clearance_str: '-- ft', trend_caret: '–', trend_desc: 'Steady' };
      this.hlClearance = { clearance_str: '-- ft', trend_caret: '–', trend_desc: 'Steady' };
      this.burgeeImg = new Image();
      this.burgeeImg.src = BURGEE_B64;

      this.readConfig();
    }

    readConfig() {
      const getBool = (attr, def) => {
        if (!this.hasAttribute(attr)) return def;
        const v = this.getAttribute(attr);
        return v !== 'false' && v !== '0';
      };
      const isCompact = getBool('compact', false);

      this.config = {
        compact: isCompact,
        showDial: isCompact ? false : getBool('show-dial', true),
        dialSize: parseInt(this.getAttribute('dial-size') || '250', 10),
        showWeather: getBool('show-weather', true),
        showForecast: isCompact ? false : getBool('show-forecast', true),
        showBridges: getBool('show-bridges', true),
        showCurrents: getBool('show-currents', true),
        showTable: getBool('show-table', true),
        showWave: isCompact ? false : getBool('show-wave', true),
        tideCount: parseInt(this.getAttribute('tide-count') || (isCompact ? '4' : '6'), 10),
        themeName: this.getAttribute('theme') || 'ayc_navy'
      };
      this.theme = THEMES[this.config.themeName] || THEMES.ayc_navy;
    }

    attributeChangedCallback(name, oldVal, newVal) {
      if (oldVal !== newVal) {
        this.readConfig();
        if (this.shadowRoot && this.shadowRoot.innerHTML) {
          this.renderSkeleton();
          this.updateClock();
          this.renderTideTable();
        }
      }
    }

    connectedCallback() {
      this.readConfig();
      this.renderSkeleton();
      this.startClock();
      this.fetchNOAATides();
      this.fetchNOAABridges();
      this.fetchNOAACurrents();
      this.fetchTempestWeather();

      this.pollInterval = setInterval(() => {
        this.fetchNOAATides();
        this.fetchNOAABridges();
        this.fetchNOAACurrents();
        this.fetchTempestWeather();
      }, 60000);
    }

    disconnectedCallback() {
      if (this.timer) clearInterval(this.timer);
      if (this.pollInterval) clearInterval(this.pollInterval);
    }

    startClock() {
      this.updateClock();
      this.timer = setInterval(() => {
        this.updateClock();
      }, 1000);
    }

    updateClock() {
      const now = new Date();
      this.computeTideStatus(now);
      this.computeBridgeNav(now);
      this.computeMoonInfo(now);
      if (this.config.showDial) this.drawDial();
      if (this.config.showWave) this.drawWave();
      this.updateDOMText(now);
    }

    computeMoonInfo(now) {
      const NEW_MOON_REF_MS = Date.UTC(2024, 0, 11, 11, 57, 0);
      const SYNODIC_MS = 29.530588853 * 86400 * 1000;
      let diffMs = now.getTime() - NEW_MOON_REF_MS;
      let ageMs = diffMs % SYNODIC_MS;
      if (ageMs < 0) ageMs += SYNODIC_MS;
      const fraction = ageMs / SYNODIC_MS;
      const illumination = Math.round(50 * (1 - Math.cos(fraction * 2 * Math.PI)));

      let phaseName = 'New Moon';
      let icon = '🌑';
      let tideType = 'Spring Tide';
      let tideSub = 'Strongest currents • Max range';

      if (fraction < 0.03 || fraction >= 0.97) {
        phaseName = 'New Moon'; icon = '🌑'; tideType = 'Spring Tide'; tideSub = 'Strongest currents • Max range';
      } else if (fraction < 0.22) {
        phaseName = 'Waxing Crescent'; icon = '🌒'; tideType = 'Normal Tide'; tideSub = 'Moderate tidal range';
      } else if (fraction < 0.28) {
        phaseName = 'First Quarter'; icon = '🌓'; tideType = 'Neap Tide'; tideSub = 'Weakest currents • Min range';
      } else if (fraction < 0.47) {
        phaseName = 'Waxing Gibbous'; icon = '🌔'; tideType = 'Normal Tide'; tideSub = 'Moderate tidal range';
      } else if (fraction < 0.53) {
        phaseName = 'Full Moon'; icon = '🌕'; tideType = 'Spring Tide'; tideSub = 'Strongest currents • Max range';
      } else if (fraction < 0.72) {
        phaseName = 'Waning Gibbous'; icon = '🌖'; tideType = 'Normal Tide'; tideSub = 'Moderate tidal range';
      } else if (fraction < 0.78) {
        phaseName = 'Third Quarter'; icon = '🌗'; tideType = 'Neap Tide'; tideSub = 'Weakest currents • Min range';
      } else {
        phaseName = 'Waning Crescent'; icon = '🌘'; tideType = 'Normal Tide'; tideSub = 'Moderate tidal range';
      }

      this.moonInfo = { phaseName, icon, illumination, tideType, tideSub };
    }

    computeTideStatus(now) {
      if (this.allPredictions && this.allPredictions.length > 0) {
        const past = this.allPredictions.filter(p => p.time <= now);
        const future = this.allPredictions.filter(p => p.time > now);

        if (past.length > 0 && future.length > 0) {
          const prevEv = past[past.length - 1];
          const nextEv = future[0];

          const spanSec = (nextEv.time - prevEv.time) / 1000;
          const elapsedSec = (now - prevEv.time) / 1000;
          const ratio = (spanSec > 0) ? Math.max(0.0, Math.min(1.0, elapsedSec / spanSec)) : 0.5;

          let angleDeg = 0;
          let isFalling = false;
          if (prevEv.is_high) {
            angleDeg = ratio * 180.0;
            isFalling = true;
          } else {
            angleDeg = 180.0 + (ratio * 180.0);
            isFalling = false;
          }
          this.currentAngle = angleDeg;

          const secToNext = (nextEv.time - now) / 1000;
          const cdHrs = Math.floor(secToNext / 3600);
          const cdMins = Math.floor((secToNext % 3600) / 60);
          const countdownStr = cdHrs > 0 ? `${cdHrs}h ${cdMins < 10 ? '0' : ''}${cdMins}m` : `${cdMins}m`;

          let state = isFalling ? 'FALLING' : 'RISING';
          let stateDesc = isFalling ? 'Falling (Ebb Tide)' : 'Rising (Flood Tide)';

          if (elapsedSec < 720) {
            state = prevEv.is_high ? 'HIGH TIDE' : 'LOW TIDE';
            stateDesc = prevEv.is_high ? 'High Tide Slack Water' : 'Low Tide Slack Water';
          } else if (secToNext < 720) {
            state = nextEv.is_high ? 'HIGH TIDE' : 'LOW TIDE';
            stateDesc = nextEv.is_high ? 'High Tide Slack Water' : 'Low Tide Slack Water';
          }

          let waterPct = isFalling ? Math.round(100.0 - (ratio * 100.0)) : Math.round(ratio * 100.0);
          waterPct = Math.max(0, Math.min(100, waterPct));

          this.tideStatus = {
            state: state,
            state_desc: stateDesc,
            countdown_str: countdownStr,
            water_level_pct: waterPct,
            is_falling: isFalling,
            next_event_name: nextEv.is_high ? 'High Tide' : 'Low Tide',
            next_event_time: nextEv.time
          };
          return;
        }
      }

      // Fallback
      this.tideStatus = {
        state: 'CALCULATING',
        state_desc: 'Synchronizing with NOAA...',
        countdown_str: '--',
        water_level_pct: 50,
        is_falling: false,
        next_event_name: 'Tide',
        next_event_time: null
      };
    }

    interpolateWaterLevel(predictions, dt) {
      if (!predictions || predictions.length < 2) return null;
      for (let i = 0; i < predictions.length - 1; i++) {
        const p0 = predictions[i];
        const p1 = predictions[i + 1];
        if (p0.time <= dt && dt <= p1.time) {
          const span = (p1.time - p0.time);
          if (span <= 0) return p0.height_ft;
          const ratio = (dt - p0.time) / span;
          if (p0.type === 'H') {
            return p1.height_ft + (p0.height_ft - p1.height_ft) * (0.5 * (1 + Math.cos(Math.PI * ratio)));
          } else {
            return p0.height_ft + (p1.height_ft - p0.height_ft) * (0.5 * (1 - Math.cos(Math.PI * ratio)));
          }
        }
      }
      return null;
    }

    computeBridgeNav(now) {
      // 1. Sea Bright Bridge (NOAA 8531804)
      let sbWater = this.interpolateWaterLevel(this.sbPredictions, now);
      let sbWaterFuture = this.interpolateWaterLevel(this.sbPredictions, new Date(now.getTime() + 15 * 60000));
      if (sbWater === null) {
        const sbRange = 3.64 - 0.13;
        sbWater = 0.13 + (this.tideStatus.water_level_pct / 100.0) * sbRange;
        sbWaterFuture = sbWater + (this.tideStatus.is_falling ? -0.05 : 0.05);
      }
      const sbClearance = SEA_BRIGHT_MHW_CLEARANCE + (SEA_BRIGHT_MHW_DATUM - sbWater);
      let sbCaret = '–';
      let sbTrendDesc = 'Steady';
      if (sbWaterFuture > sbWater + 0.02) {
        sbCaret = '▼'; sbTrendDesc = 'Decreasing (Flood Tide)';
      } else if (sbWaterFuture < sbWater - 0.02) {
        sbCaret = '▲'; sbTrendDesc = 'Increasing (Ebb Tide)';
      }

      this.sbClearance = {
        clearance_str: sbClearance.toFixed(1) + ' ft',
        trend_caret: sbCaret,
        trend_desc: sbTrendDesc,
        water_level_ft: sbWater.toFixed(2)
      };

      // 2. Highlands Bridge (NOAA 8531712)
      let hlWater = this.interpolateWaterLevel(this.hlPredictions, now);
      let hlWaterFuture = this.interpolateWaterLevel(this.hlPredictions, new Date(now.getTime() + 15 * 60000));
      if (hlWater === null) {
        const hlRange = 4.41 - 0.18;
        hlWater = 0.18 + (this.tideStatus.water_level_pct / 100.0) * hlRange;
        hlWaterFuture = hlWater + (this.tideStatus.is_falling ? -0.05 : 0.05);
      }
      const hlClearance = HIGHLANDS_MHW_CLEARANCE + (HIGHLANDS_MHW_DATUM - hlWater);
      let hlCaret = '–';
      let hlTrendDesc = 'Steady';
      if (hlWaterFuture > hlWater + 0.02) {
        hlCaret = '▼'; hlTrendDesc = 'Decreasing (Flood Tide)';
      } else if (hlWaterFuture < hlWater - 0.02) {
        hlCaret = '▲'; hlTrendDesc = 'Increasing (Ebb Tide)';
      }

      this.hlClearance = {
        clearance_str: hlClearance.toFixed(1) + ' ft',
        trend_caret: hlCaret,
        trend_desc: hlTrendDesc,
        water_level_ft: hlWater.toFixed(2)
      };

      // 3. Sea Bright Current (NOAA ACT3886)
      let speedAbs = 0;
      let currState = 'SLACK';
      let currDir = 'Slack';
      let speedTrend = '–';
      let usedMethod = this.currentMode.toUpperCase();

      if (this.currentMode === 'api' && this.apiCurrentEvents && this.apiCurrentEvents.length > 0) {
        const past = this.apiCurrentEvents.filter(c => c.time <= now);
        const future = this.apiCurrentEvents.filter(c => c.time > now);
        if (past.length > 0 && future.length > 0) {
          const p0 = past[past.length - 1];
          const p1 = future[0];
          const span = (p1.time - p0.time) / 1000;
          const prog = (span > 0) ? Math.max(0, Math.min(1, (now - p0.time) / 1000 / span)) : 0.5;
          const vCurr = p0.velocity + (p1.velocity - p0.velocity) * (0.5 - 0.5 * Math.cos(prog * Math.PI));
          const vNext = p0.velocity + (p1.velocity - p0.velocity) * (0.5 - 0.5 * Math.cos(Math.min(1, prog + 0.05) * Math.PI));
          speedAbs = Math.abs(vCurr);
          speedTrend = (Math.abs(vNext) >= Math.abs(vCurr)) ? '▲' : '▼';

          if (speedAbs < 0.25) {
            currState = 'SLACK'; currDir = 'Slack';
          } else if (vCurr > 0) {
            currState = 'FLOOD'; currDir = 'South (185°)';
          } else {
            currState = 'EBB'; currDir = 'North (005°)';
          }
        }
      }

      if (currState === 'SLACK' && (this.currentMode !== 'api' || !this.apiCurrentEvents || this.apiCurrentEvents.length === 0)) {
        const isFalling = this.tideStatus.is_falling;
        const vMagnitude = Math.sin(this.currentAngle * Math.PI / 180);
        speedAbs = Math.abs(vMagnitude * 1.85);

        if (speedAbs < 0.25) {
          currState = 'SLACK'; currDir = 'Slack';
        } else if (isFalling) {
          currState = 'EBB'; currDir = 'North (005°)';
        } else {
          currState = 'FLOOD'; currDir = 'South (185°)';
        }
        speedTrend = (this.currentAngle < 90 || (this.currentAngle >= 180 && this.currentAngle < 270)) ? '▲' : '▼';
        usedMethod = 'MATH';
      }

      this.currents = {
        speed: speedAbs.toFixed(1),
        state: currState,
        dir: currDir,
        method: usedMethod,
        arrow: speedTrend
      };
    }

    async fetchNOAATides() {
      try {
        const now = new Date();
        const yesterday = new Date(now.getTime() - 86400000);
        const future = new Date(now.getTime() + 4 * 86400000);
        const yyyymmdd = (d) => {
          const y = d.getFullYear();
          const m = String(d.getMonth() + 1).padStart(2, '0');
          const day = String(d.getDate()).padStart(2, '0');
          return `${y}${m}${day}`;
        };
        const url = `https://api.tidesandcurrents.noaa.gov/api/prod/datagetter?begin_date=${yyyymmdd(yesterday)}&end_date=${yyyymmdd(future)}&station=8531680&product=predictions&datum=MLLW&time_zone=lst_ldt&units=english&interval=hilo&format=json`;
        const res = await fetch(url);
        const data = await res.json();
        if (data && data.predictions) {
          this.allPredictions = data.predictions.map(p => {
            const dt = new Date(p.t.replace(/-/g, '/'));
            const isHigh = (p.type === 'H');
            const offsetMin = isHigh ? AYC_STATION.offset_high_min : AYC_STATION.offset_low_min;
            const aycDt = new Date(dt.getTime() + offsetMin * 60000);
            const ht = (parseFloat(p.v) * AYC_STATION.height_mult).toFixed(1);
            const dayStr = aycDt.toLocaleDateString([], { weekday: 'short', month: 'numeric', day: 'numeric' });
            const timeOnly = aycDt.toLocaleTimeString([], { hour: 'numeric', minute: '2-digit' });
            return {
              type: isHigh ? 'HIGH TIDE' : 'LOW TIDE',
              is_high: isHigh,
              time: aycDt,
              time_str: `${dayStr} ${timeOnly}`,
              height_str: `${parseFloat(ht) >= 0 ? '+' : ''}${ht} ft`,
              height_ft: parseFloat(ht)
            };
          });
          this.allPredictions.sort((a, b) => a.time - b.time);
          this.tideEvents = this.allPredictions.filter(e => e.time >= new Date(now.getTime() - 15 * 60000));
          this.renderTideTable();
          this.updateClock();
        }
      } catch (err) {
        console.warn('NOAA tides fetch notice:', err);
      }
    }

    async fetchNOAABridges() {
      try {
        const now = new Date();
        const yesterday = new Date(now.getTime() - 86400000);
        const future = new Date(now.getTime() + 4 * 86400000);
        const yyyymmdd = (d) => {
          const y = d.getFullYear();
          const m = String(d.getMonth() + 1).padStart(2, '0');
          const day = String(d.getDate()).padStart(2, '0');
          return `${y}${m}${day}`;
        };

        const urlSb = `https://api.tidesandcurrents.noaa.gov/api/prod/datagetter?begin_date=${yyyymmdd(yesterday)}&end_date=${yyyymmdd(future)}&station=8531804&product=predictions&datum=MLLW&time_zone=lst_ldt&units=english&interval=hilo&format=json`;
        const resSb = await fetch(urlSb);
        const dataSb = await resSb.json();
        if (dataSb && dataSb.predictions) {
          this.sbPredictions = dataSb.predictions.map(p => ({
            time: new Date(p.t.replace(/-/g, '/')),
            height_ft: parseFloat(p.v),
            type: p.type
          }));
          this.sbPredictions.sort((a, b) => a.time - b.time);
        }

        const urlHl = `https://api.tidesandcurrents.noaa.gov/api/prod/datagetter?begin_date=${yyyymmdd(yesterday)}&end_date=${yyyymmdd(future)}&station=8531712&product=predictions&datum=MLLW&time_zone=lst_ldt&units=english&interval=hilo&format=json`;
        const resHl = await fetch(urlHl);
        const dataHl = await resHl.json();
        if (dataHl && dataHl.predictions) {
          this.hlPredictions = dataHl.predictions.map(p => ({
            time: new Date(p.t.replace(/-/g, '/')),
            height_ft: parseFloat(p.v),
            type: p.type
          }));
          this.hlPredictions.sort((a, b) => a.time - b.time);
        }

        this.computeBridgeNav(now);
        this.updateDOMText(now);
      } catch (err) {
        console.warn('NOAA bridge tides fetch notice:', err);
      }
    }

    async fetchNOAACurrents() {
      try {
        const now = new Date();
        const yesterday = new Date(now.getTime() - 86400000);
        const future = new Date(now.getTime() + 2 * 86400000);
        const yyyymmdd = (d) => {
          const y = d.getFullYear();
          const m = String(d.getMonth() + 1).padStart(2, '0');
          const day = String(d.getDate()).padStart(2, '0');
          return `${y}${m}${day}`;
        };
        const url = `https://api.tidesandcurrents.noaa.gov/api/prod/datagetter?begin_date=${yyyymmdd(yesterday)}&end_date=${yyyymmdd(future)}&station=ACT3886&product=currents_predictions&time_zone=lst_ldt&units=english&interval=max_slack&format=json`;
        const res = await fetch(url);
        const data = await res.json();
        if (data && data.current_predictions && data.current_predictions.cp) {
          this.apiCurrentEvents = data.current_predictions.cp.map(c => ({
            time: new Date(c.Time.replace(/-/g, '/')),
            velocity: parseFloat(c.Velocity_Major || 0),
            type: (c.Type || '').toLowerCase()
          }));
          this.apiCurrentEvents.sort((a, b) => a.time - b.time);
          this.computeBridgeNav(now);
          this.updateDOMText(now);
        }
      } catch (err) {
        console.warn('NOAA currents fetch notice:', err);
      }
    }

    async fetchTempestWeather() {
      try {
        const urlObs = `https://swd.weatherflow.com/swd/rest/observations/station/${TEMPEST_STATION_ID}?token=${TEMPEST_TOKEN}`;
        const resObs = await fetch(urlObs);
        const dataObs = await resObs.json();
        if (dataObs && dataObs.obs && dataObs.obs.length > 0) {
          const o = dataObs.obs[0];
          const tempC = o.air_temperature;
          const tempF = (tempC !== null && tempC !== undefined) ? Math.round(tempC * 9 / 5 + 32) : null;
          const feelsC = o.feels_like || tempC;
          const feelsF = (feelsC !== null && feelsC !== undefined) ? Math.round(feelsC * 9 / 5 + 32) : null;
          const windMps = o.wind_avg || 0;
          const windKts = Math.round(windMps * 1.94384);
          const gustMps = o.wind_gust || 0;
          const gustKts = Math.round(gustMps * 1.94384);
          const windDeg = o.wind_direction || 0;
          const windCard = this.degToCardinal(windDeg);
          const pressMb = o.barometric_pressure || o.station_pressure || 1013.25;
          const pressInHg = (pressMb * 0.02953).toFixed(2);
          const humidity = o.relative_humidity || 0;
          const uv = o.uv || 0;
          const solar = Math.round(o.solar_radiation || 0);

          let icon = '🌤';
          let cond = 'Clear / Fair';
          if (solar > 600) { icon = '☀️'; cond = 'Sunny'; }
          else if (solar > 250) { icon = '🌤'; cond = 'Partly Cloudy'; }
          else if (solar > 50) { icon = '⛅'; cond = 'Overcast'; }
          else { icon = '🌙'; cond = 'Clear Night'; }

          this.weather.temp_f = tempF;
          this.weather.feels_f = feelsF;
          this.weather.wind_kts = windKts;
          this.weather.wind_gust = gustKts;
          this.weather.wind_card = windCard;
          this.weather.wind_deg = windDeg;
          this.weather.press_inhg = pressInHg;
          this.weather.press_mb = Math.round(pressMb);
          this.weather.humidity = humidity;
          this.weather.uv = uv;
          this.weather.solar = solar;
          this.weather.icon = icon;
          this.weather.cond = cond;
          this.weather.is_live = true;
        }

        const urlFc = `https://swd.weatherflow.com/swd/rest/better_forecast?station_id=${TEMPEST_STATION_ID}&token=${TEMPEST_TOKEN}`;
        const resFc = await fetch(urlFc);
        const dataFc = await resFc.json();
        if (dataFc && dataFc.forecast && dataFc.forecast.daily) {
          this.weather.forecast_3day = dataFc.forecast.daily.slice(0, 3).map(d => {
            const dt = new Date(d.day_start_local * 1000);
            return {
              day: dt.toLocaleDateString([], { weekday: 'short' }),
              date: dt.toLocaleDateString([], { month: 'numeric', day: 'numeric' }),
              icon: this.weatherflowIcon(d.icon),
              cond: d.conditions || 'Fair',
              high: Math.round(d.air_temp_high),
              low: Math.round(d.air_temp_low),
              precip_pct: d.precip_probability || 0
            };
          });
          this.renderForecastStrip();
        }
        this.updateDOMText(new Date());
      } catch (err) {
        console.warn('Tempest weather fetch notice:', err);
      }
    }

    degToCardinal(deg) {
      const dirs = ['N', 'NNE', 'NE', 'ENE', 'E', 'ESE', 'SE', 'SSE', 'S', 'SSW', 'SW', 'WSW', 'W', 'WNW', 'NW', 'NNW'];
      return dirs[Math.round(deg / 22.5) % 16];
    }

    weatherflowIcon(ico) {
      const map = {
        'clear-day': '☀️', 'clear-night': '🌙', 'partly-cloudy-day': '🌤',
        'partly-cloudy-night': '☁️', 'cloudy': '☁️', 'rainy': '🌧',
        'possibly-rainy-day': '🌦', 'possibly-rainy-night': '🌧',
        'thunderstorm': '⛈', 'windy': '💨', 'foggy': '🌫'
      };
      return map[ico] || '🌤';
    }

    drawDial() {
      const canvas = this.shadowRoot.getElementById('dial-canvas');
      if (!canvas) return;
      const ctx = canvas.getContext('2d');
      const dpr = window.devicePixelRatio || 2;
      const size = this.config.dialSize || 250;

      if (canvas.width !== size * dpr) {
        canvas.width = size * dpr;
        canvas.height = size * dpr;
        canvas.style.width = size + 'px';
        canvas.style.height = size + 'px';
      }

      ctx.save();
      ctx.scale(dpr, dpr);
      ctx.clearRect(0, 0, size, size);

      const cx = size / 2;
      const cy = size / 2;
      const t = this.theme;
      const outerR = size / 2 - 4;
      const bezelW = Math.max(7, outerR * 0.08);
      const innerR = outerR - bezelW;

      // Bezel
      ctx.beginPath();
      ctx.arc(cx, cy, outerR, 0, Math.PI * 2);
      ctx.fillStyle = t.bezel_outer;
      ctx.fill();

      const bgGrad = ctx.createRadialGradient(cx, cy, innerR * 0.2, cx, cy, innerR);
      bgGrad.addColorStop(0, '#102035');
      bgGrad.addColorStop(0.7, t.dial_bg);
      bgGrad.addColorStop(1, '#050B12');
      ctx.beginPath();
      ctx.arc(cx, cy, innerR, 0, Math.PI * 2);
      ctx.fillStyle = bgGrad;
      ctx.fill();

      // Flood/Ebb sector arcs
      ctx.lineWidth = Math.max(3, innerR * 0.05);
      // Falling / Ebb (Right side: -90° to 90°)
      ctx.beginPath();
      ctx.arc(cx, cy, innerR * 0.88, -Math.PI / 2, Math.PI / 2, false);
      ctx.strokeStyle = t.falling_color;
      ctx.stroke();

      // Rising / Flood (Left side: 90° to 270°)
      ctx.beginPath();
      ctx.arc(cx, cy, innerR * 0.88, Math.PI / 2, 3 * Math.PI / 2, false);
      ctx.strokeStyle = t.rising_color;
      ctx.stroke();

      // Hour Numbers (1-5, High, Low, Half)
      ctx.textAlign = 'center';
      ctx.textBaseline = 'middle';
      ctx.fillStyle = t.text_primary;
      ctx.font = `bold ${Math.max(9, Math.round(innerR * 0.09))}px Georgia, serif`;

      const numR = innerR * 0.74;
      for (let h = 1; h <= 5; h++) {
        const angFalling = (-90 + h * 30) * Math.PI / 180;
        ctx.fillText(h.toString(), cx + numR * Math.cos(angFalling), cy + numR * Math.sin(angFalling));
        const angRising = (90 + h * 30) * Math.PI / 180;
        ctx.fillText((6 - h).toString(), cx + numR * Math.cos(angRising), cy + numR * Math.sin(angRising));
      }

      // HIGH TIDE
      ctx.fillStyle = t.falling_color;
      ctx.font = `bold ${Math.max(8, Math.round(innerR * 0.075))}px "Segoe UI", sans-serif`;
      ctx.fillText('HIGH TIDE', cx, cy - innerR * 0.65);

      // LOW TIDE
      ctx.fillStyle = t.rising_color;
      ctx.fillText('LOW TIDE', cx, cy + innerR * 0.65);

      // HALF
      ctx.fillStyle = t.text_secondary;
      ctx.font = `bold ${Math.max(7, Math.round(innerR * 0.06))}px "Segoe UI", sans-serif`;
      ctx.fillText('HALF', cx + innerR * 0.65, cy);
      ctx.fillText('HALF', cx - innerR * 0.65, cy);

      // Centered Burgee between Hub and HIGH TIDE
      if (this.burgeeImg.complete && this.burgeeImg.naturalWidth > 0) {
        const bW = innerR * 0.36;
        const bH = bW * (this.burgeeImg.naturalHeight / this.burgeeImg.naturalWidth);
        const burgeeCenterY = cy - innerR * 0.325;
        ctx.drawImage(this.burgeeImg, cx - bW / 2, burgeeCenterY - bH / 2, bW, bH);
      }

      // Club Inscription
      ctx.fillStyle = t.accent;
      ctx.font = `bold ${Math.max(8, Math.round(innerR * 0.06))}px Georgia, serif`;
      ctx.fillText('ATLANTIS YACHT CLUB', cx, cy + innerR * 0.22);
      ctx.fillStyle = t.text_secondary;
      ctx.font = `${Math.max(7, Math.round(innerR * 0.048))}px "Segoe UI", sans-serif`;
      ctx.fillText('SHREWSBURY RIVER, NJ', cx, cy + innerR * 0.31);

      // Dial Hand
      const needleAngleRad = (this.currentAngle - 90) * Math.PI / 180;
      const handLen = innerR * 0.82;
      const tipX = cx + handLen * Math.cos(needleAngleRad);
      const tipY = cy + handLen * Math.sin(needleAngleRad);

      ctx.beginPath();
      ctx.moveTo(cx, cy);
      ctx.lineTo(tipX, tipY);
      ctx.strokeStyle = t.accent;
      ctx.lineWidth = 2.5;
      ctx.stroke();

      // Center Hub Pin
      ctx.beginPath();
      ctx.arc(cx, cy, 6, 0, Math.PI * 2);
      ctx.fillStyle = t.bezel_main;
      ctx.fill();
      ctx.strokeStyle = t.bezel_light;
      ctx.lineWidth = 1.5;
      ctx.stroke();

      ctx.restore();
    }

    drawWave() {
      const canvas = this.shadowRoot.getElementById('wave-canvas');
      if (!canvas) return;
      const ctx = canvas.getContext('2d');
      const w = canvas.width;
      const h = canvas.height;
      ctx.clearRect(0, 0, w, h);

      const t = this.theme;
      const midY = h / 2;
      const amp = (h / 2) - 6;

      ctx.beginPath();
      ctx.moveTo(0, midY);
      ctx.lineTo(w, midY);
      ctx.strokeStyle = 'rgba(255, 255, 255, 0.12)';
      ctx.lineWidth = 1.0;
      ctx.stroke();

      const pts = [];
      for (let x = 0; x <= w; x += 2) {
        const rad = (x / w) * Math.PI * 2;
        const y = midY - amp * Math.cos(rad);
        pts.push({ x, y });
      }

      ctx.beginPath();
      ctx.moveTo(0, h);
      pts.forEach(p => ctx.lineTo(p.x, p.y));
      ctx.lineTo(w, h);
      ctx.closePath();
      const grad = ctx.createLinearGradient(0, 0, 0, h);
      grad.addColorStop(0, 'rgba(69, 123, 157, 0.45)');
      grad.addColorStop(1, 'rgba(29, 53, 87, 0.1)');
      ctx.fillStyle = grad;
      ctx.fill();

      ctx.beginPath();
      pts.forEach((p, idx) => {
        if (idx === 0) ctx.moveTo(p.x, p.y);
        else ctx.lineTo(p.x, p.y);
      });
      ctx.strokeStyle = t.accent_blue;
      ctx.lineWidth = 2.0;
      ctx.stroke();

      const currRatio = this.currentAngle / 360.0;
      const currX = currRatio * w;
      const currY = midY - amp * Math.cos(this.currentAngle * Math.PI / 180);

      ctx.beginPath();
      ctx.arc(currX, currY, 5, 0, Math.PI * 2);
      ctx.fillStyle = this.tideStatus.is_falling ? t.falling_color : t.rising_color;
      ctx.fill();
      ctx.strokeStyle = t.bezel_light;
      ctx.lineWidth = 1.5;
      ctx.stroke();

      const dirArrow = this.tideStatus.is_falling ? '▼' : '▲';
      const labelText = `AYC Docks Water: ${this.tideStatus.water_level_pct}% ${dirArrow} ${this.tideStatus.state}`;
      ctx.font = 'bold 10px "Segoe UI", sans-serif';
      ctx.fillStyle = t.text_primary;
      ctx.textAlign = 'center';
      const tx = Math.max(70, Math.min(w - 70, currX));
      const ty = (currY > 20) ? 11 : (h - 8);
      ctx.fillText(labelText, tx, ty);
    }

    renderForecastStrip() {
      const fcContainer = this.shadowRoot.getElementById('forecast-strip');
      if (!fcContainer || !this.weather.forecast_3day) return;
      fcContainer.innerHTML = '';
      this.weather.forecast_3day.forEach(f => {
        const item = document.createElement('div');
        item.style.flex = '1';
        item.style.padding = '4px 6px';
        item.style.borderRadius = '4px';
        item.style.backgroundColor = 'rgba(255,255,255,0.04)';
        item.style.textAlign = 'center';
        item.innerHTML = `
          <div style="font-size:10px; color:${this.theme.text_secondary}; font-weight:bold;">${f.day}</div>
          <div style="font-size:12px; font-weight:bold; color:${this.theme.text_primary}; margin:1px 0;">${f.icon} ${f.high}°</div>
          <div style="font-size:9px; color:${this.theme.text_secondary};">${f.precip_pct}% rain</div>
        `;
        fcContainer.appendChild(item);
      });
    }

    renderTideTable() {
      const tbody = this.shadowRoot.getElementById('tide-table-body');
      if (!tbody) return;
      tbody.innerHTML = '';
      const limit = this.config.tideCount || 4;
      const eventsToShow = (this.tideEvents || []).slice(0, limit);

      eventsToShow.forEach(e => {
        const tr = document.createElement('tr');
        const badgeBg = e.is_high ? this.theme.high_badge_bg : this.theme.low_badge_bg;
        const badgeFg = e.is_high ? this.theme.high_badge_fg : this.theme.low_badge_fg;
        tr.innerHTML = `
          <td><span class="badge" style="background:${badgeBg}; color:${badgeFg}; font-size:9px; padding:2px 6px;">${e.is_high ? 'HIGH' : 'LOW'}</span></td>
          <td style="font-size:11px; font-weight:600; color:${this.theme.text_primary};">${e.time_str}</td>
          <td style="font-size:11px; font-weight:bold; color:${this.theme.accent}; text-align:right;">${e.height_str}</td>
        `;
        tbody.appendChild(tr);
      });
    }

    updateDOMText(now) {
      const sr = this.shadowRoot;
      if (!sr) return;

      const timeEl = sr.getElementById('live-time');
      if (timeEl) timeEl.textContent = now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });

      const moonEl = sr.getElementById('moon-phase-text');
      const moonIcon = sr.getElementById('moon-icon');
      const moonTide = sr.getElementById('moon-tide-text');
      if (moonEl && this.moonInfo) moonEl.textContent = `${this.moonInfo.phaseName} (${this.moonInfo.illumination}%)`;
      if (moonIcon && this.moonInfo) moonIcon.textContent = this.moonInfo.icon;
      if (moonTide && this.moonInfo) moonTide.textContent = `${this.moonInfo.tideType} • ${this.moonInfo.tideSub}`;

      const badge = sr.getElementById('dial-badge');
      if (badge) {
        let badgeTxt = '';
        let badgeBg = this.theme.card_bg;
        let badgeFg = this.theme.text_primary;

        if (this.tideStatus.state === 'HIGH TIDE') {
          badgeTxt = `HIGH TIDE SLACK WATER (${this.tideStatus.water_level_pct}%)`;
          badgeBg = this.theme.high_badge_bg;
          badgeFg = this.theme.high_badge_fg;
        } else if (this.tideStatus.state === 'LOW TIDE') {
          badgeTxt = `LOW TIDE SLACK WATER (${this.tideStatus.water_level_pct}%)`;
          badgeBg = this.theme.low_badge_bg;
          badgeFg = this.theme.low_badge_fg;
        } else if (this.tideStatus.is_falling) {
          badgeTxt = `▼ EBB • ${this.tideStatus.countdown_str} to Low Tide (${this.tideStatus.water_level_pct}%)`;
          badgeFg = this.theme.falling_color;
        } else {
          badgeTxt = `▲ FLOOD • ${this.tideStatus.countdown_str} to High Tide (${this.tideStatus.water_level_pct}%)`;
          badgeFg = this.theme.rising_color;
        }
        badge.textContent = badgeTxt;
        badge.style.backgroundColor = badgeBg;
        badge.style.color = badgeFg;
      }

      const w = this.weather;
      const wxTemp = sr.getElementById('wx-temp');
      const wxCond = sr.getElementById('wx-cond');
      const wxWind = sr.getElementById('wx-wind');
      const wxGust = sr.getElementById('wx-gust');
      const wxBaro = sr.getElementById('wx-baro');
      const wxBaroSub = sr.getElementById('wx-baro-sub');

      if (wxTemp && w.temp_f !== null) wxTemp.textContent = `${w.icon} ${w.temp_f}°F`;
      if (wxCond && w.feels_f !== null) wxCond.textContent = `Feels ${w.feels_f}° • ${w.cond}`;
      if (wxWind && w.wind_kts !== null) wxWind.textContent = `💨 ${w.wind_kts} kts ${w.wind_card}`;
      if (wxGust && w.wind_gust !== null) wxGust.textContent = `Gusts ${w.wind_gust} kts`;
      if (wxBaro && w.press_inhg !== null) wxBaro.textContent = `🧭 ${w.press_inhg} inHg`;
      if (wxBaroSub && w.press_mb !== null) wxBaroSub.textContent = `${w.press_mb} mb • ${w.press_trend}`;

      const sbCl = sr.getElementById('sb-clearance');
      const sbClSub = sr.getElementById('sb-clearance-sub');
      const hlCl = sr.getElementById('hl-clearance');
      const hlClSub = sr.getElementById('hl-clearance-sub');
      const sbCurr = sr.getElementById('sb-current');
      const sbCurrSub = sr.getElementById('sb-current-sub');

      if (sbCl) sbCl.textContent = `📐 ${this.sbClearance.clearance_str} ${this.sbClearance.trend_caret}`;
      if (sbClSub) sbClSub.textContent = `Draw • 15.0' MHW • ${this.sbClearance.trend_desc}`;
      if (hlCl) hlCl.textContent = `📐 ${this.hlClearance.clearance_str} ${this.hlClearance.trend_caret}`;
      if (hlClSub) hlClSub.textContent = `Fixed • 65.0' MHW • ${this.hlClearance.trend_desc}`;
      if (sbCurr) sbCurr.textContent = `🌊 ${this.currents.speed} kts ${this.currents.arrow}`;
      if (sbCurrSub) sbCurrSub.textContent = `${this.currents.state} (${this.currents.dir}) • [${this.currents.method}]`;

      const btnToggle = sr.getElementById('btn-toggle-curr');
      if (btnToggle) {
        btnToggle.textContent = (this.currentMode === 'api') ? '🌊 Mode: NOAA API' : '🌊 Mode: Math Model';
      }
    }

    renderSkeleton() {
      const t = this.theme;
      const c = this.config;

      this.shadowRoot.innerHTML = `
        <style>
          :host {
            display: block;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            color: ${t.text_primary};
            background-color: ${t.window_bg};
            box-sizing: border-box;
            border-radius: 12px;
            overflow: hidden;
            box-shadow: 0 4px 16px rgba(0,0,0,0.45);
            max-width: 440px;
            margin: 0 auto;
            width: 100%;
          }
          * { box-sizing: border-box; }
          .mobile-container {
            display: flex;
            flex-direction: column;
            gap: 8px;
            padding: 8px;
          }
          .card {
            background: ${t.card_bg};
            border: 1px solid ${t.card_border};
            border-radius: 8px;
            padding: 8px 10px;
          }
          .card-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 4px;
            font-size: 10px;
            font-weight: bold;
            color: ${t.accent};
            letter-spacing: 0.5px;
          }
          .burgee-header {
            display: grid;
            grid-template-columns: 1fr auto 1fr;
            align-items: center;
            gap: 6px;
          }
          .badge {
            padding: 3px 8px;
            border-radius: 4px;
            font-size: 10px;
            font-weight: bold;
            display: inline-block;
            border: 1px solid ${t.card_border};
          }
          .dial-box {
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            padding: 4px 0;
          }
          .grid-3 {
            display: grid;
            grid-template-columns: 1fr 1fr 1fr;
            gap: 6px;
          }
          .metric-val {
            font-size: 12px;
            font-weight: bold;
            color: ${t.text_primary};
          }
          .metric-sub {
            font-size: 9px;
            color: ${t.text_secondary};
          }
          .external-link {
            color: ${t.accent_blue};
            text-decoration: none;
            font-size: 10px;
            font-weight: bold;
          }
          .btn-toggle {
            background: rgba(255,255,255,0.08);
            border: 1px solid ${t.card_border};
            color: ${t.text_secondary};
            border-radius: 4px;
            padding: 2px 6px;
            font-size: 9px;
            cursor: pointer;
          }
          table {
            width: 100%;
            border-collapse: collapse;
            font-size: 10px;
          }
          th {
            color: ${t.text_secondary};
            font-size: 9px;
            font-weight: bold;
            text-align: left;
            padding: 2px 4px;
            border-bottom: 1px solid ${t.card_border};
          }
          td {
            padding: 4px;
            border-bottom: 1px solid rgba(255,255,255,0.04);
          }
          .disclaimer-text {
            font-size: 8px;
            color: #718096;
            line-height: 1.3;
            text-align: center;
            padding: 4px 8px;
          }
        </style>

        <div class="mobile-container">
          <!-- 1. Header Card: Moon Phase (Left) & Clock / GPS (Right) -->
          <div class="card" style="padding: 6px 10px;">
            <div style="display:flex; justify-content:space-between; align-items:center;">
              <!-- Left: Moon Phase -->
              <div style="display:flex; align-items:center; gap:8px;">
                <span id="moon-icon" style="font-size:20px; line-height:1; flex-shrink:0;">🌖</span>
                <div>
                  <div id="moon-phase-text" style="font-size:11px; font-weight:bold; color:${t.text_primary};">Waning Gibbous</div>
                  <div id="moon-tide-text" style="font-size:9px; font-weight:600; color:${t.accent}; margin-top:1px;">Normal Tide</div>
                </div>
              </div>

              <!-- Right: Live Clock & GPS -->
              <div style="text-align:right; flex-shrink:0;">
                <div id="live-time" style="font-size:14px; font-weight:bold; font-family:monospace; color:${t.text_primary};">--:--:--</div>
                <div style="font-size:9px; color:${t.accent};">40°20'12.7"N 73°58'42.7"W</div>
              </div>
            </div>
          </div>

          <!-- 2. Analog Chronometer Dial (Configurable show-dial) -->
          ${c.showDial ? `
          <div class="card dial-box">
            <div style="font-size:9px; font-weight:bold; color:${t.text_secondary}; margin-bottom:2px;">TIDE CHRONOMETER • AYC DOCKS</div>
            <canvas id="dial-canvas" width="${c.dialSize}" height="${c.dialSize}" style="max-width:100%; height:auto;"></canvas>
            <div id="dial-badge" class="badge" style="margin-top:4px;">CALCULATING...</div>
          </div>
          ` : `
          <!-- Compact Status Card when Dial is Hidden -->
          <div class="card" style="text-align:center; padding:10px;">
            <div style="font-size:10px; font-weight:bold; color:${t.text_secondary};">AYC DOCKS TIDE STATUS</div>
            <div id="dial-badge" class="badge" style="font-size:12px; padding:6px 12px; margin-top:4px;">CALCULATING...</div>
          </div>
          `}

          <!-- 3. Water Level Sine Wave (Configurable show-wave) -->
          ${c.showWave ? `
          <div class="card" style="padding:2px 4px;">
            <canvas id="wave-canvas" width="380" height="42" style="width:100%; height:42px; display:block;"></canvas>
          </div>
          ` : ''}

          <!-- 4. Bridges & Shrewsbury Navigation (Configurable show-bridges) -->
          ${c.showBridges ? `
          <div class="card">
            <div class="card-header">
              <span>BRIDGES & CURRENTS</span>
              <button id="btn-toggle-curr" class="btn-toggle">🌊 Toggle Model</button>
            </div>
            <div class="grid-3">
              <div>
                <div style="font-size:8px; font-weight:bold; color:${t.text_secondary};">SEA BRIGHT BR.</div>
                <div id="sb-clearance" class="metric-val">📐 -- ft</div>
                <div id="sb-clearance-sub" class="metric-sub">Draw • 15.0' MHW</div>
              </div>
              <div>
                <div style="font-size:8px; font-weight:bold; color:${t.accent_blue};">SEA BRIGHT CURR.</div>
                <div id="sb-current" class="metric-val" style="color:${t.accent_blue};">🌊 -- kts</div>
                <div id="sb-current-sub" class="metric-sub">Slack • 0 kts</div>
              </div>
              <div>
                <div style="font-size:8px; font-weight:bold; color:${t.text_secondary};">HIGHLANDS BR.</div>
                <div id="hl-clearance" class="metric-val">📐 -- ft</div>
                <div id="hl-clearance-sub" class="metric-sub">Fixed • 65.0' MHW</div>
              </div>
            </div>
          </div>
          ` : ''}

          <!-- 5. Harbor Weather (Configurable show-weather) -->
          ${c.showWeather ? `
          <div class="card">
            <div class="card-header">
              <span>CURRENT WEATHER</span>
              <a href="${TEMPEST_URL}" target="_blank" rel="noopener" class="external-link">Tempest #141221 ↗</a>
            </div>
            <div class="grid-3">
              <div>
                <div id="wx-temp" class="metric-val">--°F</div>
                <div id="wx-cond" class="metric-sub">Initializing...</div>
              </div>
              <div>
                <div id="wx-wind" class="metric-val" style="color:${t.accent_blue};">💨 -- kts</div>
                <div id="wx-gust" class="metric-sub">Gusts --</div>
              </div>
              <div>
                <div id="wx-baro" class="metric-val">🧭 -- inHg</div>
                <div id="wx-baro-sub" class="metric-sub">-- mb</div>
              </div>
            </div>

            ${c.showForecast ? `
            <div style="margin-top:6px; padding-top:4px; border-top:1px dashed ${t.card_border};">
              <div id="forecast-strip" style="display:flex; gap:4px;">
                <div style="font-size:9px; color:${t.text_secondary};">Fetching forecast...</div>
              </div>
            </div>
            ` : ''}
          </div>
          ` : ''}

          <!-- 6. Upcoming Predictions Table (Configurable show-table) -->
          ${c.showTable ? `
          <div class="card" style="padding:6px 8px;">
            <div class="card-header" style="margin-bottom:2px;">
              <span>TIDE TABLE • AYC DOCKS (NEXT ${c.tideCount})</span>
            </div>
            <table>
              <thead>
                <tr>
                  <th>EVENT</th>
                  <th>DATE & TIME</th>
                  <th style="text-align:right;">HEIGHT</th>
                </tr>
              </thead>
              <tbody id="tide-table-body">
                <tr><td colspan="3" style="text-align:center; color:${t.text_secondary}; font-size:10px;">Loading AYC predictions...</td></tr>
              </tbody>
            </table>
          </div>
          ` : ''}

          <!-- 7. Safety Notice -->
          <div class="disclaimer-text">
            ⚖ <strong>Navigational Notice:</strong> For informational convenience only. Rely strictly on official NOAA nautical charts and navigation aids. Atlantis Yacht Club assumes no liability.
          </div>
        </div>
      `;

      const btnToggle = this.shadowRoot.getElementById('btn-toggle-curr');
      if (btnToggle) {
        btnToggle.addEventListener('click', () => {
          this.currentMode = (this.currentMode === 'api') ? 'math' : 'api';
          this.computeBridgeNav(new Date());
          this.updateDOMText(new Date());
        });
      }
    }
  }

  if (!customElements.get('ayc-tide-mobile')) {
    customElements.define('ayc-tide-mobile', AYCTideMobileWidget);
  }

  window.AYCTideMobile = {
    init: function(selector, options) {
      const container = document.querySelector(selector);
      if (container) {
        const widget = document.createElement('ayc-tide-mobile');
        if (options) {
          if (options.compact !== undefined) widget.setAttribute('compact', options.compact);
          if (options.showDial !== undefined) widget.setAttribute('show-dial', options.showDial);
          if (options.dialSize !== undefined) widget.setAttribute('dial-size', options.dialSize);
          if (options.showWeather !== undefined) widget.setAttribute('show-weather', options.showWeather);
          if (options.showForecast !== undefined) widget.setAttribute('show-forecast', options.showForecast);
          if (options.showBridges !== undefined) widget.setAttribute('show-bridges', options.showBridges);
          if (options.showTable !== undefined) widget.setAttribute('show-table', options.showTable);
          if (options.showWave !== undefined) widget.setAttribute('show-wave', options.showWave);
          if (options.tideCount !== undefined) widget.setAttribute('tide-count', options.tideCount);
          if (options.theme) widget.setAttribute('theme', options.theme);
        }
        container.appendChild(widget);
        return widget;
      }
    }
  };
})();
"""

final_js = template.replace('BURGEE_BASE64_PLACEHOLDER', b64)
with open('web/ayc-tide-mobile.js', 'w', encoding='utf-8') as f:
    f.write(final_js)

print('Generated web/ayc-tide-mobile.js successfully! Length:', len(final_js))
