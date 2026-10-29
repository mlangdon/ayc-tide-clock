/**
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
  const BURGEE_B64 = 'data:image/png;base64,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';

  // Physical Marine Constants
  const TIDE_PERIOD_HOURS = 12.42066667; // 12h 25m 14.4s
  const SEA_BRIGHT_MHW_CLEARANCE = 15.0; // ft
  const SEA_BRIGHT_MHW_DATUM = 3.64;     // ft MLLW
  const HIGHLANDS_MHW_CLEARANCE = 65.0;  // ft
  const HIGHLANDS_MHW_DATUM = 4.41;      // ft MLLW

  // Preset Reference Station
  const AYC_STATION = {
    name: 'Atlantis Yacht Club (Channel Hydro-Model)',
    coords: '40°20\'12.7"N 73°58\'42.7"W',
    noaa_id: '8531680',
    offset_high_min: 107,
    offset_low_min: 115,
    height_mult: 0.62,
    mean_range: 2.50
  };

  // Color Palette aligned with https://www.atlantisyachtclub.org
  // Atlantic Ocean Blue (#457B9D / #437B9D), Deep Slate Navy (#1D3557 / #102035),
  // Crisp Honeydew (#F1FAEE), Regatta Red (#E63946 / #C8102E), Marine Link (#1E7ABE), Yacht Gold (#D4AF37)
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
      rising_color: '#457B9D',  // AYC Ocean Blue
      falling_color: '#E63946'  // AYC Regatta Red
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
      this.moonInfo = { phaseName: 'Calculating...', icon: '🌕', illumination: 100, tideType: 'Spring Tide', tideSub: 'Strongest currents' };
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
      this.computeMoonInfo(now);
      this.drawDial();
      this.drawWave();
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
        phaseName = 'New Moon';
        icon = '🌑';
        tideType = 'Spring Tide';
        tideSub = 'Strongest currents • Max range';
      } else if (fraction < 0.22) {
        phaseName = 'Waxing Crescent';
        icon = '🌒';
        tideType = 'Normal Tide';
        tideSub = 'Moderate tidal range';
      } else if (fraction < 0.28) {
        phaseName = 'First Quarter';
        icon = '🌓';
        tideType = 'Neap Tide';
        tideSub = 'Weakest currents • Min range';
      } else if (fraction < 0.47) {
        phaseName = 'Waxing Gibbous';
        icon = '🌔';
        tideType = 'Normal Tide';
        tideSub = 'Moderate tidal range';
      } else if (fraction < 0.53) {
        phaseName = 'Full Moon';
        icon = '🌕';
        tideType = 'Spring Tide';
        tideSub = 'Strongest currents • Max range';
      } else if (fraction < 0.72) {
        phaseName = 'Waning Gibbous';
        icon = '🌖';
        tideType = 'Normal Tide';
        tideSub = 'Moderate tidal range';
      } else if (fraction < 0.78) {
        phaseName = 'Third Quarter';
        icon = '🌗';
        tideType = 'Neap Tide';
        tideSub = 'Weakest currents • Min range';
      } else {
        phaseName = 'Waning Crescent';
        icon = '🌘';
        tideType = 'Normal Tide';
        tideSub = 'Moderate tidal range';
      }

      this.moonInfo = { phaseName, icon, illumination, tideType, tideSub };
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
        const now = new Date();
        const future = new Date(now.getTime() + 4 * 86400000);
        const yyyymmdd = (d) => {
          const y = d.getFullYear();
          const m = String(d.getMonth() + 1).padStart(2, '0');
          const day = String(d.getDate()).padStart(2, '0');
          return `${y}${m}${day}`;
        };
        const url = `https://api.tidesandcurrents.noaa.gov/api/prod/datagetter?begin_date=${yyyymmdd(now)}&end_date=${yyyymmdd(future)}&station=8531680&product=predictions&datum=MLLW&time_zone=lst_ldt&units=english&interval=hilo&format=json`;
        const res = await fetch(url);
        const data = await res.json();
        if (data && data.predictions) {
          this.tideEvents = data.predictions.map(p => {
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
              height_str: `${parseFloat(ht) >= 0 ? '+' : ''}${ht} ft`
            };
          }).filter(e => e.time >= new Date(now.getTime() - 3600000));
          this.renderTideTable();
        }
      } catch (err) {}
    }

    async fetchTempestWeather() {
      let gotTempest = false;

      // 1. Primary: Better Forecast Endpoint (contains official station current_conditions + 10-day forecast)
      try {
        const fcUrl = `https://swd.weatherflow.com/swd/rest/better_forecast?station_id=${TEMPEST_STATION_ID}&token=${TEMPEST_TOKEN}&units_temp=f&units_wind=kts&units_pressure=inhg`;
        const fcRes = await fetch(fcUrl);
        const fcData = await fcRes.json();
        if (fcData && fcData.current_conditions) {
          const cc = fcData.current_conditions;
          this.weather.temp_f = (cc.air_temperature !== undefined && cc.air_temperature !== null) ? Number(cc.air_temperature).toFixed(1) : null;
          this.weather.feels_f = (cc.feels_like !== undefined && cc.feels_like !== null) ? Number(cc.feels_like).toFixed(1) : this.weather.temp_f;
          this.weather.cond = cc.conditions || 'Clear';
          this.weather.icon = this.getWeatherIcon(cc.icon || cc.conditions);
          this.weather.wind_kts = (cc.wind_avg !== undefined && cc.wind_avg !== null) ? Number(cc.wind_avg).toFixed(1) : '0.0';
          this.weather.wind_gust = (cc.wind_gust !== undefined && cc.wind_gust !== null) ? Number(cc.wind_gust).toFixed(1) : '0.0';
          this.weather.wind_deg = cc.wind_direction;
          this.weather.wind_card = cc.wind_direction_cardinal || this.degToCard(cc.wind_direction);
          this.weather.press_inhg = (cc.sea_level_pressure !== undefined && cc.sea_level_pressure !== null) ? Number(cc.sea_level_pressure).toFixed(2) : (cc.station_pressure ? Number(cc.station_pressure).toFixed(2) : null);
          this.weather.press_mb = this.weather.press_inhg ? Math.round(Number(this.weather.press_inhg) * 33.8639) : 1016;
          this.weather.press_trend = cc.pressure_trend || 'steady';
          this.weather.humidity = cc.relative_humidity;
          this.weather.dew_f = (cc.dew_point !== undefined && cc.dew_point !== null) ? Number(cc.dew_point).toFixed(1) : '--';
          this.weather.uv = cc.uv !== undefined ? cc.uv : 0;
          this.weather.solar = cc.solar_radiation !== undefined ? cc.solar_radiation : 0;
          this.weather.is_live = true;
          this.weather.source = 'Tempest #141221 (Live)';
          gotTempest = true;
        }

        if (fcData && fcData.forecast && fcData.forecast.daily) {
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
        console.warn('Tempest forecast notice:', err);
      }

      // 2. Direct device telemetry for live precipitation (Device 344469 / ST-00144769)
      try {
        const devUrl = `https://swd.weatherflow.com/swd/rest/observations/device/344469?token=${TEMPEST_TOKEN}`;
        const dRes = await fetch(devUrl);
        const dData = await dRes.json();
        if (dData && dData.obs && dData.obs.length > 0) {
          const o = dData.obs[0];
          if (Array.isArray(o) && o.length >= 19) {
            const pMm = o[12] || 0.0;
            const pTodayMm = o[18] || 0.0;
            this.weather.rain_rate = (pMm * 0.03937).toFixed(2);
            this.weather.rain_today = (pTodayMm * 0.03937).toFixed(2);
            if (o[10] !== undefined) this.weather.uv = o[10];
            if (o[11] !== undefined) this.weather.solar = o[11];
          }
        }
      } catch (err) {}

      // 3. Fallback: NOAA NWS Monmouth County Station (KBLM) if Tempest returned no data
      if (!gotTempest) {
        try {
          const nwsUrl = 'https://api.weather.gov/stations/KBLM/observations/latest';
          const nwsRes = await fetch(nwsUrl);
          const nwsData = await nwsRes.json();
          if (nwsData && nwsData.properties) {
            const p = nwsData.properties;
            const cTemp = p.temperature && p.temperature.value;
            if (cTemp !== null && cTemp !== undefined) {
              const tempF = (cTemp * 9 / 5 + 32);
              this.weather.temp_f = tempF.toFixed(1);
              this.weather.feels_f = (p.windChill && p.windChill.value !== null) 
                ? (p.windChill.value * 9 / 5 + 32).toFixed(1) 
                : (p.heatIndex && p.heatIndex.value !== null ? (p.heatIndex.value * 9 / 5 + 32).toFixed(1) : this.weather.temp_f);
            }
            if (p.windSpeed && p.windSpeed.value !== null) {
              this.weather.wind_kts = (p.windSpeed.value * 0.539957).toFixed(1);
            }
            if (p.windGust && p.windGust.value !== null) {
              this.weather.wind_gust = (p.windGust.value * 0.539957).toFixed(1);
            }
            if (p.windDirection && p.windDirection.value !== null) {
              this.weather.wind_deg = Math.round(p.windDirection.value);
              this.weather.wind_card = this.degToCard(this.weather.wind_deg);
            }
            if (p.barometricPressure && p.barometricPressure.value !== null) {
              const pIn = p.barometricPressure.value * 0.0002953;
              this.weather.press_inhg = pIn.toFixed(2);
              this.weather.press_mb = Math.round(p.barometricPressure.value / 100);
            }
            if (p.relativeHumidity && p.relativeHumidity.value !== null) {
              this.weather.humidity = Math.round(p.relativeHumidity.value);
            }
            if (p.dewpoint && p.dewpoint.value !== null) {
              this.weather.dew_f = (p.dewpoint.value * 9 / 5 + 32).toFixed(1);
            }
            if (p.textDescription) {
              this.weather.cond = p.textDescription;
              this.weather.icon = this.getWeatherIcon(p.textDescription);
            }
            this.weather.is_live = true;
            this.weather.source = 'NOAA NWS KBLM (Monmouth Co)';
          }
        } catch (nwsErr) {
          console.warn('NWS fallback notice:', nwsErr);
        }
      }

      this.updateDOMText(new Date());
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
      ctx.strokeStyle = '#3E6188';
      ctx.lineWidth = 0.9;
      ctx.stroke();

      ctx.beginPath();
      ctx.arc(cx, cy, trackInR, 0, Math.PI * 2);
      ctx.strokeStyle = '#3E6188';
      ctx.lineWidth = 0.9;
      ctx.stroke();

      for (let i = 0; i < 60; i++) {
        const angRad = (i * 6.0 - 90) * Math.PI / 180;
        const isHour = (i % 5 === 0);
        const isHalf = (i % 2.5 === 0) && !isHour;

        let r1 = trackOutR;
        let r2 = trackInR;
        let strokeCol = '#3E6188';
        let lineW = 0.9;

        if (isHour) {
          r2 = trackInR - (innerR * 0.02);
          strokeCol = t.bezel_light;
          lineW = 2.0;
        } else if (isHalf) {
          r2 = trackInR + (innerR * 0.015);
          strokeCol = t.bezel_light;
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

      // Cardinal Labels (HIGH TIDE & LOW TIDE)
      const lblFontSize = Math.max(9, Math.round(innerR * 0.068));
      ctx.font = `bold ${lblFontSize}px "Segoe UI", sans-serif`;

      // HIGH TIDE
      ctx.fillStyle = t.falling_color;
      ctx.fillText('HIGH TIDE', cx, cy - innerR * 0.65);
      ctx.beginPath();
      ctx.arc(cx, cy - innerR * 0.74, 3, 0, Math.PI * 2);
      ctx.fill();

      // LOW TIDE
      ctx.fillStyle = t.rising_color;
      ctx.fillText('LOW TIDE', cx, cy + innerR * 0.65);
      ctx.beginPath();
      ctx.arc(cx, cy + innerR * 0.74, 3, 0, Math.PI * 2);
      ctx.fill();

      // HALF Labels
      ctx.fillStyle = t.text_secondary;
      ctx.font = `bold ${Math.max(8, Math.round(innerR * 0.055))}px "Segoe UI", sans-serif`;
      ctx.fillText('HALF', cx + innerR * 0.65, cy);
      ctx.fillText('HALF', cx - innerR * 0.65, cy);

      // Central AYC Burgee Emblem
      if (this.burgeeImg.complete && this.burgeeImg.naturalWidth > 0) {
        const bW = innerR * 0.38;
        const bH = bW * (this.burgeeImg.naturalHeight / this.burgeeImg.naturalWidth);
        ctx.drawImage(this.burgeeImg, cx - bW / 2, cy - bH / 2 - 12, bW, bH);
      }

      // Club Inscription
      ctx.fillStyle = t.accent;
      ctx.font = `bold ${Math.max(8, Math.round(innerR * 0.058))}px Georgia, serif`;
      ctx.fillText('ATLANTIS YACHT CLUB', cx, cy + innerR * 0.22);
      ctx.fillStyle = t.text_secondary;
      ctx.font = `${Math.max(7, Math.round(innerR * 0.046))}px "Segoe UI", sans-serif`;
      ctx.fillText('SHREWSBURY RIVER, NJ', cx, cy + innerR * 0.31);

      // Dial Hand (Pointer)
      const needleAngleRad = (this.currentAngle - 90) * Math.PI / 180;
      const handLen = innerR * 0.82;
      const tailLen = innerR * 0.22;
      const perpAngle = needleAngleRad + Math.PI / 2;
      const halfW = 4.0;

      const tipX = cx + handLen * Math.cos(needleAngleRad);
      const tipY = cy + handLen * Math.sin(needleAngleRad);
      const tailX = cx - tailLen * Math.cos(needleAngleRad);
      const tailY = cy - tailLen * Math.sin(needleAngleRad);

      const p1X = cx + halfW * Math.cos(perpAngle);
      const p1Y = cy + halfW * Math.sin(perpAngle);
      const p2X = cx - halfW * Math.cos(perpAngle);
      const p2Y = cy - halfW * Math.sin(perpAngle);

      // Needle Shadow
      ctx.beginPath();
      ctx.moveTo(tipX + 2, tipY + 2);
      ctx.lineTo(p1X + 2, p1Y + 2);
      ctx.lineTo(tailX + 2, tailY + 2);
      ctx.lineTo(p2X + 2, p2Y + 2);
      ctx.closePath();
      ctx.fillStyle = 'rgba(0,0,0,0.4)';
      ctx.fill();

      // Needle Body (Blued steel / Deep marine navy)
      ctx.beginPath();
      ctx.moveTo(tipX, tipY);
      ctx.lineTo(p1X, p1Y);
      ctx.lineTo(tailX, tailY);
      ctx.lineTo(p2X, p2Y);
      ctx.closePath();
      ctx.fillStyle = '#0B2044';
      ctx.fill();
      ctx.strokeStyle = t.bezel_light;
      ctx.lineWidth = 1.0;
      ctx.stroke();

      // Hand Center Spine (Gold Accent)
      ctx.beginPath();
      ctx.moveTo(cx, cy);
      ctx.lineTo(tipX, tipY);
      ctx.strokeStyle = t.accent;
      ctx.lineWidth = 1.5;
      ctx.stroke();

      // Center Hub Pin
      ctx.beginPath();
      ctx.arc(cx, cy, 6.5, 0, Math.PI * 2);
      ctx.fillStyle = t.bezel_main;
      ctx.fill();
      ctx.strokeStyle = t.bezel_light;
      ctx.lineWidth = 1.5;
      ctx.stroke();

      ctx.beginPath();
      ctx.arc(cx, cy, 2.5, 0, Math.PI * 2);
      ctx.fillStyle = t.dial_bg;
      ctx.fill();

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
      const amp = (h / 2) - 8;

      ctx.beginPath();
      ctx.moveTo(0, midY);
      ctx.lineTo(w, midY);
      ctx.strokeStyle = 'rgba(255, 255, 255, 0.12)';
      ctx.lineWidth = 1.0;
      ctx.stroke();

      ctx.beginPath();
      const pts = [];
      for (let x = 0; x <= w; x += 2) {
        const rad = (x / w) * Math.PI * 2;
        const y = midY - amp * Math.cos(rad);
        pts.push({ x, y });
      }

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

      // Update Moon Phase Info
      const moonEl = sr.getElementById('moon-phase-text');
      const moonIcon = sr.getElementById('moon-icon');
      const moonTide = sr.getElementById('moon-tide-text');
      if (moonEl && this.moonInfo) {
        moonEl.textContent = `${this.moonInfo.phaseName} (${this.moonInfo.illumination}%)`;
      }
      if (moonIcon && this.moonInfo) {
        moonIcon.textContent = this.moonInfo.icon;
      }
      if (moonTide && this.moonInfo) {
        moonTide.textContent = `${this.moonInfo.tideType} • ${this.moonInfo.tideSub}`;
      }

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

      if (wxTemp && w.temp_f !== null) wxTemp.textContent = `${w.icon} ${w.temp_f}°F`;
      if (wxCond && w.feels_f !== null) wxCond.textContent = `Feels ${w.feels_f}° • ${w.cond}`;
      if (wxWind && w.wind_kts !== null) wxWind.textContent = `💨 ${w.wind_kts} kts ${w.wind_card}`;
      if (wxGust && w.wind_gust !== null) wxGust.textContent = `Gusts ${w.wind_gust} kts • ${w.wind_deg}°`;
      if (wxBaro && w.press_inhg !== null) wxBaro.textContent = `🧭 ${w.press_inhg} inHg`;
      if (wxBaroSub && w.press_mb !== null) wxBaroSub.textContent = `${w.press_mb} mb • ${w.press_trend}`;
      if (wxHum && w.humidity !== null) wxHum.textContent = `Humidity: ${w.humidity}% • Dew: ${w.dew_f}°F`;
      if (wxRain) wxRain.textContent = `Rain: ${w.rain_rate}"/hr (${w.rain_today}" day)`;
      if (wxSolar) wxSolar.textContent = `UV: ${w.uv} • Solar: ${w.solar} W/m²`;

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
      const events = this.tideEvents.slice(0, 8);
      if (events.length === 0) {
        tbody.innerHTML = `<tr><td colspan="3" style="padding:6px 8px; color:${this.theme.text_secondary};">Loading NOAA predictions...</td></tr>`;
        return;
      }
      events.forEach((e, i) => {
        const tr = document.createElement('tr');
        tr.style.backgroundColor = (i % 2 === 0) ? this.theme.card_bg : 'rgba(255,255,255,0.03)';
        tr.innerHTML = `
          <td style="padding:3px 8px; font-weight:bold; color:${e.is_high ? this.theme.high_badge_fg : this.theme.low_badge_fg}">${e.type}</td>
          <td style="padding:3px 8px; color:${this.theme.text_primary}; font-size:10.5px;">${e.time_str}</td>
          <td style="padding:3px 8px; font-weight:bold; color:${this.theme.accent}; text-align:right;">${e.height_str}</td>
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
            justify-content: flex-start;
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
            color: ${t.text_primary};
            text-decoration: none;
            font-size: 10.5px;
            font-weight: bold;
            padding: 3px 8px;
            background: rgba(69, 123, 157, 0.35);
            border-radius: 4px;
            border: 1px solid ${t.accent_blue};
            transition: all 0.2s ease;
          }
          .external-link:hover {
            background: rgba(69, 123, 157, 0.6);
            color: #FFFFFF;
            text-decoration: none;
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
          .disclaimer-box {
            font-size: 9.5px;
            line-height: 1.45;
            color: ${t.text_secondary};
            opacity: 0.85;
            padding: 8px 10px;
            border-radius: 5px;
            background: rgba(0, 0, 0, 0.25);
            border: 1px solid rgba(255, 255, 255, 0.08);
            margin-top: 14px;
            text-align: justify;
            max-width: 380px;
            width: 100%;
          }
          @media (max-width: 768px) {
            .app-container { flex-direction: column; }
            .grid-3 { grid-template-columns: 1fr; }
          }
        </style>

        <div class="app-container">
          <!-- Left Column: Analog Tide Chronometer Dial with Disclaimer -->
          <div class="dial-column">
            <div style="font-size:11px; font-weight:bold; color:${t.text_secondary}; margin-bottom:4px;">TIDE CHRONOMETER</div>
            <canvas id="dial-canvas" width="380" height="380" style="max-width:100%; height:auto;"></canvas>
            <div id="dial-badge" class="badge">CALCULATING...</div>
            <!-- Legal & Navigational Disclaimer Under Chronometer -->
            <div class="disclaimer-box">
              ⚖ <strong>Navigational Notice:</strong> This application is provided for informational and recreational convenience only. Data is not intended for passage planning or safe harbor piloting decisions. Always consult official NOAA nautical charts, USCG Local Notices to Mariners, real-time bridge clearance boards, and official navigation aids. Neither Atlantis Yacht Club nor its representatives assume any liability or responsibility for loss, damage, or injury arising from the use of this application.
            </div>
          </div>

          <!-- Right Column: Navigation, Harbor Weather & Predictions Dashboard -->
          <div class="dash-column">
            <!-- Club & Station Info Card with Moon Phase -->
            <div class="card">
              <div class="burgee-header">
                <img src="${BURGEE_B64}" width="48" height="34" style="border-radius:2px;" alt="AYC Burgee" />
                <div>
                  <div style="font-family:Georgia, serif; font-size:15px; font-weight:bold; color:${t.accent}; letter-spacing:0.5px;">ATLANTIS YACHT CLUB</div>
                  <div style="font-size:10px; color:${t.text_secondary};">Monmouth Beach, NJ • Shrewsbury River</div>
                  <div style="font-size:11px; font-weight:600; color:${t.text_primary}; margin-top:2px;">Tide Chronometer &amp; Weather Dashboard</div>
                </div>
                <div style="margin-left:auto; text-align:right;">
                  <div id="live-time" style="font-size:15px; font-weight:bold; font-family:monospace; color:${t.text_primary};">--:--:--</div>
                  <div style="font-size:9px; color:${t.accent};">GPS: 40°20'12.7"N 73°58'42.7"W</div>
                </div>
              </div>
              <!-- Moon Phase & Tidal Range Row -->
              <div style="display:flex; align-items:center; justify-content:space-between; margin-top:8px; padding-top:6px; border-top:1px solid ${t.card_border};">
                <div style="display:flex; align-items:center; gap:6px;">
                  <span id="moon-icon" style="font-size:16px;">🌕</span>
                  <span id="moon-phase-text" style="font-size:11px; font-weight:bold; color:${t.text_primary};">Moon Phase</span>
                </div>
                <div id="moon-tide-text" style="font-size:10px; font-weight:600; color:${t.accent};">Spring Tide • Max Range</div>
              </div>
            </div>

            <!-- Current Weather Card with 3-Day Forecast -->
            <div class="card">
              <div class="card-header">
                <span>Current Weather</span>
                <a href="${TEMPEST_URL}" target="_blank" rel="noopener" class="external-link">Weather Station ↗</a>
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
                <span id="wx-rain">Rain: 0.00"/hr</span>
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

            <!-- Upcoming Predictions Table (Next 8 Events) -->
            <div class="card" style="padding:6px 10px;">
              <div class="card-header" style="margin-bottom:2px;">
                <span>TIDE TABLE • PREDICTIONS (AYC SLIPS & DOCKS)</span>
              </div>
              <table>
                <thead>
                  <tr>
                    <th>EVENT</th>
                    <th>DATE & TIME</th>
                    <th style="text-align:right;">HEIGHT (MLLW)</th>
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
