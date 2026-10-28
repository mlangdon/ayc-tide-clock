import base64

with open('web/burgee_base64.txt', 'r') as f:
    b64 = f.read().strip()

template = """/**
 * Atlantis Yacht Club (AYC) - Tide Clock & Harbor Dashboard
 * Embeddable JavaScript Web Component & Widget
 * Hosted on GitHub Pages / Private GitHub Repository
 */
(function() {
  'use strict';

  // Obfuscated internal token key storage (decoded at runtime)
  const _K = 'NjNiMWRlZTctNDUzYS00OWNkLWJlNWMtOWM5MDVjMjBmYTc1';
  const TEMPEST_TOKEN = atob(_K);
  const TEMPEST_STATION_ID = 141221;
  const TEMPEST_URL = 'https://tempestwx.com/station/141221/';
  const BURGEE_B64 = 'data:image/png;base64,BURGEE_BASE64_PLACEHOLDER';

  // Physical Marine Constants
  const TIDE_PERIOD_HOURS = 12.42066667; // 12h 25m 14.4s
  const SEA_BRIGHT_MHW_CLEARANCE = 15.0; // ft
  const SEA_BRIGHT_MHW_DATUM = 3.64;     // ft MLLW
  const HIGHLANDS_MHW_CLEARANCE = 65.0;  // ft
  const HIGHLANDS_MHW_DATUM = 4.41;      // ft MLLW

  // Preset Reference Station
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
      name: 'AYC Regatta Navy',
      window_bg: '#0E1724',
      card_bg: '#152234',
      card_border: '#24364E',
      header_bg: '#1A2A40',
      text_primary: '#FFFFFF',
      text_secondary: '#9BB0C8',
      accent: '#E6A13B',
      accent_blue: '#3E95FF',
      dial_bg: '#101B2B',
      bezel_main: '#C99D46',
      bezel_light: '#F3DB94',
      bezel_shadow: '#1A2433',
      bezel_outer: '#080E17',
      high_badge_bg: '#7A1C22',
      high_badge_fg: '#FF858B',
      low_badge_bg: '#17406B',
      low_badge_fg: '#76B8FF',
      rising_color: '#3498DB',
      falling_color: '#E67E22'
    }
  };

  class AYCTideClockWidget extends HTMLElement {
    constructor() {
      super();
      this.attachShadow({ mode: 'open' });
      this.theme = THEMES.ayc_navy;
      this.currentMode = 'math';
      this.currentAngle = 0;
      this.tideStatus = { state: 'CALCULATING', countdown_str: '--', water_level_pct: 50, is_falling: false };
      this.tideEvents = [];
      this.weather = {
        temp_f: null, feels_f: null, cond: 'Connecting...', icon: '🌤',
        wind_kts: null, wind_gust: null, wind_card: '--', wind_deg: null,
        press_inhg: null, press_mb: null, press_trend: 'steady',
        humidity: null, dew_f: null, rain_rate: 0, rain_today: 0, uv: 0, solar: 0,
        is_live: false, forecast_3day: []
      };
      this.currents = { speed: '0.0', state: 'SLACK', dir: 'Slack', method: 'MATH', arrow: '◆' };
      this.sbClearance = { clearance_str: '-- ft', trend_caret: '–', trend_desc: 'Steady' };
      this.hlClearance = { clearance_str: '-- ft', trend_caret: '–', trend_desc: 'Steady' };
      this.burgeeImg = new Image();
      this.burgeeImg.src = BURGEE_B64;
    }

    connectedCallback() {
      this.renderSkeleton();
      this.startClock();
      this.fetchNOAATides();
      this.fetchTempestWeather();
      this.pollInterval = setInterval(() => {
        this.fetchNOAATides();
        this.fetchTempestWeather();
      }, 60000);
    }

    disconnectedCallback() {
      if (this.timer) clearInterval(this.timer);
      if (this.pollInterval) clearInterval(this.pollInterval);
    }

    startClock() {
      this.updateClock();
      this.timer = setInterval(() => this.updateClock(), 1000);
    }

    updateClock() {
      const now = new Date();
      this.computeTideStatus(now);
      this.computeBridgeNav(now);
      this.drawDial();
      this.drawWave();
      this.updateDOMText(now);
    }

    computeTideStatus(now) {
      const baseEpoch = new Date(2026, 9, 28, 11, 27, 0);
      const diffMs = now - baseEpoch;
      const periodMs = TIDE_PERIOD_HOURS * 3600 * 1000;
      let phase = (diffMs % periodMs) / periodMs;
      if (phase < 0) phase += 1.0;

      const angleDeg = phase * 360.0;
      this.currentAngle = angleDeg;

      const isFalling = (angleDeg >= 0 && angleDeg < 180);
      let state = 'HIGH TIDE';
      let stateDesc = 'High Tide Slack';
      let countdownSec = 0;

      if (angleDeg < 10 || angleDeg > 350) {
        state = 'HIGH TIDE';
        stateDesc = 'High Tide Slack';
      } else if (angleDeg > 170 && angleDeg < 190) {
        state = 'LOW TIDE';
        stateDesc = 'Low Tide Slack';
      } else if (isFalling) {
        state = 'FALLING';
        stateDesc = 'Falling (Ebb Tide)';
        const toLowDeg = 180 - angleDeg;
        countdownSec = (toLowDeg / 360) * (TIDE_PERIOD_HOURS * 3600);
      } else {
        state = 'RISING';
        stateDesc = 'Rising (Flood Tide)';
        const toHighDeg = 360 - angleDeg;
        countdownSec = (toHighDeg / 360) * (TIDE_PERIOD_HOURS * 3600);
      }

      const cdHrs = Math.floor(countdownSec / 3600);
      const cdMins = Math.floor((countdownSec % 3600) / 60);
      const countdownStr = cdHrs > 0 ? `${cdHrs}h ${cdMins}m` : `${cdMins}m`;

      const cosVal = Math.cos(angleDeg * Math.PI / 180);
      const waterPct = Math.round(50.0 + 50.0 * cosVal);

      this.tideStatus = {
        angle_deg: angleDeg,
        state: state,
        state_desc: stateDesc,
        countdown_str: countdownStr,
        water_level_pct: waterPct,
        is_falling: isFalling
      };
    }

    computeBridgeNav(now) {
      const angleRad = this.currentAngle * Math.PI / 180;
      const sbRange = 3.64 - 0.13;
      const sbWater = 0.13 + (this.tideStatus.water_level_pct / 100.0) * sbRange;
      const sbClearance = SEA_BRIGHT_MHW_CLEARANCE + (SEA_BRIGHT_MHW_DATUM - sbWater);

      const hlRange = 4.41 - 0.18;
      const hlWater = 0.18 + (this.tideStatus.water_level_pct / 100.0) * hlRange;
      const hlClearance = HIGHLANDS_MHW_CLEARANCE + (HIGHLANDS_MHW_DATUM - hlWater);

      const isEbb = this.tideStatus.is_falling;
      const sbCaret = isEbb ? '▲' : '▼';
      const hlCaret = isEbb ? '▲' : '▼';

      this.sbClearance = {
        clearance_str: sbClearance.toFixed(1) + ' ft',
        trend_caret: sbCaret,
        trend_desc: isEbb ? 'Increasing (Ebb Tide)' : 'Decreasing (Flood Tide)'
      };

      this.hlClearance = {
        clearance_str: hlClearance.toFixed(1) + ' ft',
        trend_caret: hlCaret,
        trend_desc: isEbb ? 'Increasing (Ebb Tide)' : 'Decreasing (Flood Tide)'
      };

      const vSine = -Math.sin(angleRad);
      const speedAbs = Math.abs(vSine * 1.85);
      const speedTrend = (Math.abs(vSine) > 0.7) ? '▼' : '▲';

      let currState = 'SLACK';
      let currDir = 'Slack';
      if (speedAbs < 0.25) {
        currState = 'SLACK';
        currDir = 'Slack';
      } else if (vSine < 0) {
        currState = 'FLOOD';
        currDir = 'South (185°)';
      } else {
        currState = 'EBB';
        currDir = 'North (005°)';
      }

      this.currents = {
        speed: speedAbs.toFixed(1),
        state: currState,
        dir: currDir,
        method: this.currentMode.toUpperCase(),
        arrow: speedTrend
      };
    }

    async fetchNOAATides() {
      try {
        const url = 'https://api.tidesandcurrents.noaa.gov/api/prod/datagetter?date=today&station=8531680&product=predictions&datum=MLLW&time_zone=lst_ldt&units=english&interval=hilo&format=json';
        const res = await fetch(url);
        const data = await res.json();
        if (data && data.predictions) {
          const now = new Date();
          this.tideEvents = data.predictions.map(p => {
            const dt = new Date(p.t.replace(/-/g, '/'));
            const isHigh = (p.type === 'H');
            const offsetMin = isHigh ? AYC_STATION.offset_high_min : AYC_STATION.offset_low_min;
            const aycDt = new Date(dt.getTime() + offsetMin * 60000);
            const ht = (parseFloat(p.v) * AYC_STATION.height_mult).toFixed(1);
            return {
              type: isHigh ? 'HIGH TIDE' : 'LOW TIDE',
              is_high: isHigh,
              time: aycDt,
              time_str: aycDt.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
              height_str: ht + ' ft'
            };
          }).filter(e => e.time >= new Date(now.getTime() - 3600000));
          this.renderTideTable();
        }
      } catch (err) {}
    }

    async fetchTempestWeather() {
      try {
        const obsUrl = `https://swd.weatherflow.com/swd/rest/observations/station/${TEMPEST_STATION_ID}?token=${TEMPEST_TOKEN}`;
        const res = await fetch(obsUrl);
        const data = await res.json();
        if (data && data.obs && data.obs.length > 0) {
          const o = data.obs[0];
          const tempF = (o.air_temperature * 9 / 5 + 32);
          const feelsF = o.feels_like ? (o.feels_like * 9 / 5 + 32) : tempF;
          const windKts = (o.wind_avg * 1.94384);
          const gustKts = (o.wind_gust * 1.94384);
          const pInhg = o.sea_level_pressure ? (o.sea_level_pressure * 0.02953) : (o.barometric_pressure * 0.02953);

          this.weather.temp_f = tempF.toFixed(1);
          this.weather.feels_f = feelsF.toFixed(1);
          this.weather.wind_kts = windKts.toFixed(1);
          this.weather.wind_gust = gustKts.toFixed(1);
          this.weather.wind_deg = o.wind_direction;
          this.weather.wind_card = this.degToCard(o.wind_direction);
          this.weather.press_inhg = pInhg.toFixed(2);
          this.weather.press_mb = o.sea_level_pressure || o.barometric_pressure;
          this.weather.humidity = o.relative_humidity;
          this.weather.dew_f = (o.dew_point * 9 / 5 + 32).toFixed(1);
          this.weather.rain_rate = (o.precip * 0.03937).toFixed(2);
          this.weather.rain_today = (o.precip_accum_local_day * 0.03937).toFixed(2);
          this.weather.uv = o.uv;
          this.weather.solar = o.solar_radiation;
          this.weather.is_live = true;
        }

        const fcUrl = `https://swd.weatherflow.com/swd/rest/better_forecast?station_id=${TEMPEST_STATION_ID}&token=${TEMPEST_TOKEN}&units_temp=f`;
        const fcRes = await fetch(fcUrl);
        const fcData = await fcRes.json();
        if (fcData && fcData.forecast && fcData.forecast.daily) {
          this.weather.cond = fcData.current_conditions ? fcData.current_conditions.conditions : 'Clear';
          this.weather.icon = this.getWeatherIcon(this.weather.cond);
          this.weather.forecast_3day = fcData.forecast.daily.slice(0, 3).map(d => {
            const dt = new Date(d.day_start_local * 1000);
            return {
              day: dt.toLocaleDateString([], { weekday: 'short' }),
              date: dt.toLocaleDateString([], { month: 'short', day: 'numeric' }),
              high: Math.round(d.air_temp_high),
              low: Math.round(d.air_temp_low),
              cond: d.conditions,
              icon: this.getWeatherIcon(d.conditions),
              precip_pct: d.precip_probability || 0
            };
          });
          this.renderForecast();
        }
      } catch (err) {
        console.warn('Tempest fetch notice:', err);
      }
    }

    degToCard(deg) {
      if (deg === null || deg === undefined) return '--';
      const val = Math.floor((deg / 22.5) + 0.5) % 16;
      const cards = ['N', 'NNE', 'NE', 'ENE', 'E', 'ESE', 'SE', 'SSE', 'S', 'SSW', 'SW', 'WSW', 'W', 'WNW', 'NW', 'NNW'];
      return cards[val];
    }

    getWeatherIcon(cond) {
      const c = (cond || '').toLowerCase();
      if (c.includes('rain') || c.includes('shower')) return '🌧';
      if (c.includes('thunder') || c.includes('storm')) return '⛈';
      if (c.includes('snow') || c.includes('flurr')) return '❄';
      if (c.includes('fog') || c.includes('mist')) return '🌫';
      if (c.includes('partly') || c.includes('mostly')) return '🌤';
      if (c.includes('cloud')) return '☁';
      return '☀️';
    }

    drawDial() {
      const canvas = this.shadowRoot.getElementById('dial-canvas');
      if (!canvas) return;
      const ctx = canvas.getContext('2d');
      const w = canvas.width;
      const h = canvas.height;
      ctx.clearRect(0, 0, w, h);

      const cx = w / 2;
      const cy = (h - 28) / 2;
      const radius = Math.min(cx, cy) - 10;
      const t = this.theme;

      // Drop shadow & Bezel
      ctx.save();
      ctx.beginPath();
      ctx.arc(cx, cy + 3, radius, 0, Math.PI * 2);
      ctx.fillStyle = t.bezel_outer;
      ctx.fill();

      ctx.beginPath();
      ctx.arc(cx, cy, radius, 0, Math.PI * 2);
      ctx.fillStyle = t.bezel_shadow;
      ctx.fill();

      ctx.beginPath();
      ctx.arc(cx, cy, radius * 0.965, 0, Math.PI * 2);
      ctx.fillStyle = t.bezel_main;
      ctx.fill();

      ctx.beginPath();
      ctx.arc(cx, cy, radius * 0.935, 0, Math.PI * 2);
      ctx.fillStyle = t.bezel_light;
      ctx.fill();

      ctx.beginPath();
      ctx.arc(cx, cy, radius * 0.905, 0, Math.PI * 2);
      ctx.fillStyle = t.bezel_shadow;
      ctx.fill();

      // Rivets
      const rivR = radius * 0.95;
      [45, 135, 225, 315].forEach(deg => {
        const rad = deg * Math.PI / 180;
        const rx = cx + rivR * Math.cos(rad);
        const ry = cy + rivR * Math.sin(rad);
        ctx.beginPath();
        ctx.arc(rx, ry, 2.5, 0, Math.PI * 2);
        ctx.fillStyle = t.bezel_outer;
        ctx.fill();
        ctx.strokeStyle = t.bezel_light;
        ctx.lineWidth = 1;
        ctx.stroke();
      });

      // Dial Face Center
      const innerR = radius * 0.885;
      ctx.beginPath();
      ctx.arc(cx, cy, innerR, 0, Math.PI * 2);
      ctx.fillStyle = t.dial_bg;
      ctx.fill();
      ctx.strokeStyle = t.card_border;
      ctx.lineWidth = 1.5;
      ctx.stroke();

      // Sector Arcs
      const arcR = innerR * 0.95;
      ctx.beginPath();
      ctx.arc(cx, cy, arcR, -Math.PI / 2, Math.PI / 2);
      ctx.strokeStyle = t.falling_color;
      ctx.lineWidth = 2.5;
      ctx.stroke();

      ctx.beginPath();
      ctx.arc(cx, cy, arcR, Math.PI / 2, 3 * Math.PI / 2);
      ctx.strokeStyle = t.rising_color;
      ctx.lineWidth = 2.5;
      ctx.stroke();

      // Railway Tracks
      const trackOutR = innerR * 0.94;
      const trackInR = innerR * 0.86;
      ctx.beginPath();
      ctx.arc(cx, cy, trackOutR, 0, Math.PI * 2);
      ctx.strokeStyle = '#4A6572';
      ctx.lineWidth = 0.9;
      ctx.stroke();

      ctx.beginPath();
      ctx.arc(cx, cy, trackInR, 0, Math.PI * 2);
      ctx.strokeStyle = '#4A6572';
      ctx.lineWidth = 0.9;
      ctx.stroke();

      for (let i = 0; i < 60; i++) {
        const angRad = (i * 6.0 - 90) * Math.PI / 180;
        const isHour = (i % 5 === 0);
        const isHalf = (i % 2.5 === 0) && !isHour;

        let r1 = trackOutR;
        let r2 = trackInR;
        let strokeCol = '#4A6572';
        let lineW = 0.9;

        if (isHour) {
          r2 = trackInR - (innerR * 0.02);
          strokeCol = t.bezel_main;
          lineW = 2.0;
        } else if (isHalf) {
          r2 = trackInR + (innerR * 0.015);
          strokeCol = t.bezel_main;
          lineW = 1.2;
        } else {
          r2 = trackOutR - (innerR * 0.035);
        }

        ctx.beginPath();
        ctx.moveTo(cx + r1 * Math.cos(angRad), cy + r1 * Math.sin(angRad));
        ctx.lineTo(cx + r2 * Math.cos(angRad), cy + r2 * Math.sin(angRad));
        ctx.strokeStyle = strokeCol;
        ctx.lineWidth = lineW;
        ctx.stroke();
      }

      // Hour Numbers
      ctx.fillStyle = t.text_primary;
      ctx.font = `bold ${Math.max(10, Math.round(innerR * 0.082))}px Georgia, serif`;
      ctx.textAlign = 'center';
      ctx.textBaseline = 'middle';

      const numR = innerR * 0.77;
      for (let hr = 1; hr <= 5; hr++) {
        const rad = (hr * 30.0 - 90) * Math.PI / 180;
        ctx.fillText(hr.toString(), cx + numR * Math.cos(rad), cy + numR * Math.sin(rad));
      }
      [5, 4, 3, 2, 1].forEach((hr, idx) => {
        const rad = (210.0 + idx * 30.0 - 90) * Math.PI / 180;
        ctx.fillText(hr.toString(), cx + numR * Math.cos(rad), cy + numR * Math.sin(rad));
      });

      // Cardinals
      ctx.font = `bold ${Math.max(9, Math.round(innerR * 0.068))}px Georgia, serif`;
      ctx.fillStyle = '#E74C3C';
      ctx.fillText('HIGH TIDE', cx, cy - innerR * 0.70);

      ctx.beginPath();
      ctx.arc(cx, cy - innerR * 0.79, 3, 0, Math.PI * 2);
      ctx.fillStyle = '#E74C3C';
      ctx.fill();

      ctx.fillStyle = '#3498DB';
      ctx.fillText('LOW TIDE', cx, cy + innerR * 0.70);

      ctx.beginPath();
      ctx.arc(cx, cy + innerR * 0.79, 3, 0, Math.PI * 2);
      ctx.fillStyle = '#3498DB';
      ctx.fill();

      ctx.font = `bold ${Math.max(8, Math.round(innerR * 0.062))}px "Segoe UI", sans-serif`;
      ctx.fillStyle = t.falling_color;
      ctx.fillText('HALF', cx + innerR * 0.54, cy);

      ctx.fillStyle = t.rising_color;
      ctx.fillText('HALF', cx - innerR * 0.54, cy);

      // Insignia
      if (this.burgeeImg.complete && this.burgeeImg.naturalWidth > 0) {
        const bw = 50;
        const bh = 35;
        ctx.drawImage(this.burgeeImg, cx - bw / 2, cy - innerR * 0.49 - bh / 2, bw, bh);
      }

      ctx.font = `bold ${Math.max(9, Math.round(innerR * 0.076))}px Georgia, serif`;
      ctx.fillStyle = t.text_primary;
      ctx.fillText('ATLANTIS YACHT CLUB', cx, cy - innerR * 0.25);

      ctx.font = `normal ${Math.max(7, Math.round(innerR * 0.055))}px "Segoe UI", sans-serif`;
      ctx.fillStyle = t.text_secondary;
      ctx.fillText('MONMOUTH BEACH, NJ', cx, cy - innerR * 0.17);
      ctx.fillText('12h 25m TIDE GAUGE', cx, cy + innerR * 0.28);

      // Pointer Hand
      const handRad = (this.currentAngle - 90) * Math.PI / 180;
      const handLen = innerR * 0.86;
      const cosA = Math.cos(handRad);
      const sinA = Math.sin(handRad);
      const perpX = -sinA;
      const perpY = cosA;

      const tipX = cx + handLen * cosA;
      const tipY = cy + handLen * sinA;

      const flareD = handLen * 0.72;
      const flareW = Math.max(3.0, handLen * 0.038);
      const flX = cx + flareD * cosA + flareW * perpX;
      const flY = cy + flareD * sinA + flareW * perpY;
      const frX = cx + flareD * cosA - flareW * perpX;
      const frY = cy + flareD * sinA - flareW * perpY;

      const baseW = Math.max(2.0, handLen * 0.024);
      const blX = cx + baseW * perpX;
      const blY = cy + baseW * perpY;
      const brX = cx - baseW * perpX;
      const brY = cy - baseW * perpY;

      ctx.beginPath();
      ctx.moveTo(cx, cy);
      ctx.lineTo(blX, blY);
      ctx.lineTo(flX, flY);
      ctx.lineTo(tipX, tipY);
      ctx.fillStyle = t.bezel_main;
      ctx.fill();

      ctx.beginPath();
      ctx.moveTo(cx, cy);
      ctx.lineTo(tipX, tipY);
      ctx.lineTo(frX, frY);
      ctx.lineTo(brX, brY);
      ctx.fillStyle = t.bezel_light;
      ctx.fill();

      // Counterweight tail
      const tailLen = handLen * 0.26;
      const cwCenterX = cx - (tailLen * 0.65) * cosA;
      const cwCenterY = cy - (tailLen * 0.65) * sinA;
      const cwRadius = Math.max(4.0, handLen * 0.055);

      ctx.beginPath();
      ctx.arc(cwCenterX, cwCenterY, cwRadius, 0, Math.PI * 2);
      ctx.fillStyle = t.bezel_main;
      ctx.fill();

      ctx.beginPath();
      ctx.arc(cwCenterX, cwCenterY, cwRadius * 0.48, 0, Math.PI * 2);
      ctx.fillStyle = t.dial_bg;
      ctx.fill();

      ctx.beginPath();
      ctx.moveTo(cx, cy);
      ctx.lineTo(cx - tailLen * cosA, cy - tailLen * sinA);
      ctx.strokeStyle = t.bezel_main;
      ctx.lineWidth = 2;
      ctx.stroke();

      // Hub
      const hubR = Math.max(5.0, handLen * 0.065);
      ctx.beginPath();
      ctx.arc(cx, cy, hubR, 0, Math.PI * 2);
      ctx.fillStyle = t.bezel_shadow;
      ctx.fill();

      ctx.beginPath();
      ctx.arc(cx, cy, hubR * 0.72, 0, Math.PI * 2);
      ctx.fillStyle = t.bezel_light;
      ctx.fill();

      ctx.beginPath();
      ctx.arc(cx, cy, hubR * 0.32, 0, Math.PI * 2);
      ctx.fillStyle = t.bezel_main;
      ctx.fill();

      ctx.restore();
    }

    drawWave() {
      const canvas = this.shadowRoot.getElementById('wave-canvas');
      if (!canvas) return;
      const ctx = canvas.getContext('2d');
      const w = canvas.width;
      const h = canvas.height;
      const t = this.theme;
      ctx.clearRect(0, 0, w, h);

      const midY = h / 2;
      const amp = (h - 18) / 2;

      ctx.fillStyle = t.card_bg;
      ctx.fillRect(0, 0, w, h);

      ctx.setLineDash([3, 4]);
      ctx.strokeStyle = t.card_border;
      ctx.lineWidth = 1;
      ctx.beginPath();
      ctx.moveTo(0, midY - amp);
      ctx.lineTo(w, midY - amp);
      ctx.moveTo(0, midY + amp);
      ctx.lineTo(w, midY + amp);
      ctx.stroke();
      ctx.setLineDash([]);

      const pts = [];
      const steps = Math.max(60, w);
      for (let i = 0; i <= steps; i++) {
        const px = (i / steps) * w;
        const phase = (i / steps) * 2 * Math.PI;
        const py = midY - amp * Math.cos(phase);
        pts.push({ x: px, y: py });
      }

      ctx.beginPath();
      ctx.moveTo(0, h);
      pts.forEach(p => ctx.lineTo(p.x, p.y));
      ctx.lineTo(w, h);
      ctx.fillStyle = '#152E48';
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
      ctx.arc(currX, currY, 5.5, 0, Math.PI * 2);
      ctx.fillStyle = this.tideStatus.is_falling ? t.falling_color : t.rising_color;
      ctx.fill();
      ctx.strokeStyle = t.bezel_light;
      ctx.lineWidth = 1.6;
      ctx.stroke();

      const dirArrow = this.tideStatus.is_falling ? '▼' : '▲';
      const labelText = `Water Level: ${this.tideStatus.water_level_pct}%  ${dirArrow} ${this.tideStatus.state}`;
      ctx.font = 'bold 11px "Segoe UI", sans-serif';
      ctx.fillStyle = t.text_primary;
      ctx.textAlign = 'center';
      const tx = Math.max(80, Math.min(w - 80, currX));
      const ty = (currY > 22) ? 12 : (h - 10);
      ctx.fillText(labelText, tx, ty);
    }

    updateDOMText(now) {
      const sr = this.shadowRoot;
      if (!sr) return;

      const timeEl = sr.getElementById('live-time');
      if (timeEl) timeEl.textContent = now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });

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
      const wxHum = sr.getElementById('wx-hum');
      const wxRain = sr.getElementById('wx-rain');
      const wxSolar = sr.getElementById('wx-solar');
      const wxSource = sr.getElementById('wx-source');

      if (wxTemp && w.temp_f !== null) wxTemp.textContent = `${w.icon} ${w.temp_f}°F`;
      if (wxCond && w.feels_f !== null) wxCond.textContent = `Feels ${w.feels_f}° • ${w.cond}`;
      if (wxWind && w.wind_kts !== null) wxWind.textContent = `💨 ${w.wind_kts} kts ${w.wind_card}`;
      if (wxGust && w.wind_gust !== null) wxGust.textContent = `Gusts ${w.wind_gust} kts • ${w.wind_deg}°`;
      if (wxBaro && w.press_inhg !== null) wxBaro.textContent = `🧭 ${w.press_inhg} inHg`;
      if (wxBaroSub && w.press_mb !== null) wxBaroSub.textContent = `${w.press_mb} mb • Steady`;
      if (wxHum && w.humidity !== null) wxHum.textContent = `Humidity: ${w.humidity}% • Dew: ${w.dew_f}°F`;
      if (wxRain) wxRain.textContent = `Rain: ${w.rain_rate}\"/hr (${w.rain_today}\" day)`;
      if (wxSolar) wxSolar.textContent = `UV: ${w.uv} • Solar: ${w.solar} W/m²`;
      if (wxSource) {
        wxSource.textContent = w.is_live ? '● Tempest #141221 (Live)' : '● Connecting...';
        wxSource.style.color = w.is_live ? '#2ECC71' : '#E6A13B';
      }

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
    }

    renderTideTable() {
      const tbody = this.shadowRoot.getElementById('tide-tbody');
      if (!tbody) return;
      tbody.innerHTML = '';
      this.tideEvents.slice(0, 5).forEach((e, i) => {
        const tr = document.createElement('tr');
        tr.style.backgroundColor = (i % 2 === 0) ? this.theme.card_bg : '#121D2C';
        tr.innerHTML = `
          <td style="padding:4px 8px; font-weight:bold; color:${e.is_high ? this.theme.high_badge_fg : this.theme.low_badge_fg}">${e.type}</td>
          <td style="padding:4px 8px;">${e.time_str}</td>
          <td style="padding:4px 8px; font-weight:bold; color:${this.theme.accent}">${e.height_str}</td>
        `;
        tbody.appendChild(tr);
      });
    }

    renderForecast() {
      const fcContainer = this.shadowRoot.getElementById('forecast-strip');
      if (!fcContainer) return;
      fcContainer.innerHTML = '';
      this.weather.forecast_3day.forEach(f => {
        const item = document.createElement('div');
        item.style.flex = '1';
        item.style.padding = '4px 6px';
        item.style.borderRadius = '4px';
        item.style.backgroundColor = 'rgba(255,255,255,0.04)';
        item.innerHTML = `
          <div style="font-size:10px; color:${this.theme.text_secondary}; font-weight:bold;">${f.day} ${f.date}</div>
          <div style="font-size:12px; font-weight:bold; color:${this.theme.text_primary}; margin:2px 0;">${f.icon} ${f.high}° / ${f.low}°F</div>
          <div style="font-size:10px; color:${this.theme.text_secondary};">${f.cond} (${f.precip_pct}% rain)</div>
        `;
        fcContainer.appendChild(item);
      });
    }

    renderSkeleton() {
      const t = this.theme;
      this.shadowRoot.innerHTML = `
        <style>
          :host {
            display: block;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            color: ${t.text_primary};
            background-color: ${t.window_bg};
            box-sizing: border-box;
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 8px 24px rgba(0,0,0,0.5);
            max-width: 980px;
            margin: 0 auto;
          }
          * { box-sizing: border-box; }
          .app-container {
            display: flex;
            flex-direction: row;
            flex-wrap: wrap;
            padding: 12px;
            gap: 12px;
          }
          .dial-column {
            flex: 1 1 380px;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            background: ${t.window_bg};
            padding: 8px;
          }
          .dash-column {
            flex: 1 1 480px;
            display: flex;
            flex-direction: column;
            gap: 8px;
          }
          .card {
            background: ${t.card_bg};
            border: 1px solid ${t.card_border};
            border-radius: 6px;
            padding: 10px 12px;
          }
          .card-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 6px;
            font-size: 11px;
            font-weight: bold;
            color: ${t.accent};
            letter-spacing: 0.5px;
          }
          .burgee-header {
            display: flex;
            align-items: center;
            gap: 10px;
          }
          .badge {
            padding: 4px 10px;
            border-radius: 4px;
            font-size: 11px;
            font-weight: bold;
            display: inline-block;
            margin-top: 6px;
            border: 1px solid ${t.card_border};
          }
          .grid-3 {
            display: grid;
            grid-template-columns: 1fr 1fr 1fr;
            gap: 8px;
            margin-top: 4px;
          }
          .metric-val {
            font-size: 14px;
            font-weight: bold;
            color: ${t.text_primary};
          }
          .metric-sub {
            font-size: 10px;
            color: ${t.text_secondary};
            margin-top: 2px;
          }
          .external-link {
            color: ${t.accent_blue};
            text-decoration: none;
            font-size: 10px;
            font-weight: bold;
            padding: 2px 6px;
            background: rgba(62, 149, 255, 0.12);
            border-radius: 3px;
            border: 1px solid rgba(62, 149, 255, 0.25);
            transition: all 0.2s ease;
          }
          .external-link:hover {
            background: rgba(62, 149, 255, 0.25);
            text-decoration: underline;
          }
          .btn-toggle {
            background: rgba(230, 161, 59, 0.15);
            color: ${t.accent};
            border: 1px solid rgba(230, 161, 59, 0.3);
            border-radius: 3px;
            padding: 2px 6px;
            font-size: 9px;
            font-weight: bold;
            cursor: pointer;
          }
          table {
            width: 100%;
            border-collapse: collapse;
            font-size: 11px;
            margin-top: 4px;
          }
          th {
            text-align: left;
            padding: 4px 8px;
            background: ${t.header_bg};
            color: ${t.text_secondary};
            font-size: 10px;
          }
          @media (max-width: 768px) {
            .app-container { flex-direction: column; }
            .grid-3 { grid-template-columns: 1fr; }
          }
        </style>

        <div class="app-container">
          <!-- Left Column: Analog Tide Chronometer Dial -->
          <div class="dial-column">
            <div style="font-size:11px; font-weight:bold; color:${t.text_secondary}; margin-bottom:4px;">TIDE CHRONOMETER</div>
            <canvas id="dial-canvas" width="380" height="380" style="max-width:100%; height:auto;"></canvas>
            <div id="dial-badge" class="badge">CALCULATING...</div>
          </div>

          <!-- Right Column: Navigation, Harbor Weather & Predictions Dashboard -->
          <div class="dash-column">
            <!-- Club & Station Info Card -->
            <div class="card">
              <div class="burgee-header">
                <img src="${BURGEE_B64}" width="48" height="34" style="border-radius:2px;" alt="AYC Burgee" />
                <div>
                  <div style="font-family:Georgia, serif; font-size:15px; font-weight:bold; color:${t.accent};">ATLANTIS YACHT CLUB</div>
                  <div style="font-size:10px; color:${t.text_secondary};">66 River Ave, Monmouth Beach, NJ • Est. 1961</div>
                </div>
                <div style="margin-left:auto; text-align:right;">
                  <div id="live-time" style="font-size:15px; font-weight:bold; font-family:monospace; color:${t.text_primary};">--:--:--</div>
                  <div style="font-size:9px; color:${t.accent};">GPS: 40°20'12.7"N 73°58'42.7"W</div>
                </div>
              </div>
            </div>

            <!-- Tempest Harbor Weather Card with 3-Day Forecast -->
            <div class="card">
              <div class="card-header">
                <span>TEMPEST HARBOR WEATHER • STN 141221</span>
                <div>
                  <span id="wx-source" style="color:#2ECC71; margin-right:8px;">● Tempest #141221</span>
                  <a href="${TEMPEST_URL}" target="_blank" rel="noopener" class="external-link">🔗 tempestwx.com/station/141221</a>
                </div>
              </div>
              <div class="grid-3">
                <div>
                  <div id="wx-temp" class="metric-val">--°F</div>
                  <div id="wx-cond" class="metric-sub">Initializing...</div>
                </div>
                <div>
                  <div id="wx-wind" class="metric-val" style="color:${t.accent_blue};">💨 -- kts --</div>
                  <div id="wx-gust" class="metric-sub">Gusts --</div>
                </div>
                <div>
                  <div id="wx-baro" class="metric-val" style="color:${t.accent};">🧭 -- inHg</div>
                  <div id="wx-baro-sub" class="metric-sub">-- mb • Steady</div>
                </div>
              </div>
              <div style="display:flex; justify-content:space-between; font-size:10px; color:${t.text_secondary}; margin-top:6px; border-top:1px solid ${t.card_border}; padding-top:4px;">
                <span id="wx-hum">Humidity: --% • Dew: --°F</span>
                <span id="wx-rain">Rain: 0.00\"/hr</span>
                <span id="wx-solar">UV: 0 • Solar: 0 W/m²</span>
              </div>
              <!-- 3-Day Forecast Strip -->
              <div style="margin-top:6px; padding-top:4px; border-top:1px dashed ${t.card_border};">
                <div style="font-size:9px; font-weight:bold; color:${t.accent}; margin-bottom:4px;">3-DAY HARBOR FORECAST:</div>
                <div id="forecast-strip" style="display:flex; gap:6px;">
                  <div style="font-size:10px; color:${t.text_secondary};">Fetching forecast from Tempestwx...</div>
                </div>
              </div>
            </div>

            <!-- Bridges & Shrewsbury Navigation Card -->
            <div class="card">
              <div class="card-header">
                <span>BRIDGES & CURRENTS • SHREWSBURY NAVIGATION</span>
                <button id="btn-toggle-curr" class="btn-toggle">🌊 Toggle Model</button>
              </div>
              <div class="grid-3">
                <div>
                  <div style="font-size:9px; font-weight:bold; color:${t.text_secondary};">SEA BRIGHT BRIDGE</div>
                  <div id="sb-clearance" class="metric-val">📐 -- ft</div>
                  <div id="sb-clearance-sub" class="metric-sub">Draw • 15.0' MHW</div>
                </div>
                <div>
                  <div style="font-size:9px; font-weight:bold; color:${t.accent_blue};">SEA BRIGHT CURRENT</div>
                  <div id="sb-current" class="metric-val" style="color:${t.accent_blue};">🌊 -- kts</div>
                  <div id="sb-current-sub" class="metric-sub">Slack • 0 kts</div>
                </div>
                <div>
                  <div style="font-size:9px; font-weight:bold; color:${t.text_secondary};">HIGHLANDS BRIDGE</div>
                  <div id="hl-clearance" class="metric-val">📐 -- ft</div>
                  <div id="hl-clearance-sub" class="metric-sub">Fixed • 65.0' MHW</div>
                </div>
              </div>
            </div>

            <!-- Water Level Sine Visualizer -->
            <div class="card" style="padding:4px 6px;">
              <canvas id="wave-canvas" width="480" height="52" style="width:100%; height:52px; display:block;"></canvas>
            </div>

            <!-- Upcoming Predictions Table -->
            <div class="card" style="padding:6px 10px;">
              <div class="card-header" style="margin-bottom:2px;">
                <span>TIDE TABLE • PREDICTIONS (AYC SLIPS & DOCKS)</span>
              </div>
              <table>
                <thead>
                  <tr>
                    <th>EVENT</th>
                    <th>TIME</th>
                    <th>HEIGHT (MLLW)</th>
                  </tr>
                </thead>
                <tbody id="tide-tbody">
                  <tr><td colspan="3" style="padding:6px 8px; color:${t.text_secondary};">Loading NOAA predictions...</td></tr>
                </tbody>
              </table>
            </div>
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

  if (!customElements.get('ayc-tide-clock')) {
    customElements.define('ayc-tide-clock', AYCTideClockWidget);
  }

  window.AYCTideClock = {
    init: function(selector, options) {
      const container = document.querySelector(selector);
      if (container) {
        const widget = document.createElement('ayc-tide-clock');
        if (options && options.theme) widget.theme = THEMES[options.theme] || THEMES.ayc_navy;
        container.appendChild(widget);
        return widget;
      }
    }
  };
})();
"""

final_js = template.replace('BURGEE_BASE64_PLACEHOLDER', b64)
with open('web/ayc-tide-clock.js', 'w', encoding='utf-8') as f:
    f.write(final_js)

print('Generated web/ayc-tide-clock.js successfully! Length:', len(final_js))
