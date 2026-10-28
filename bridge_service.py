"""
Bridge & Currents Service: Real-time bridge overhead clearance and tidal current speeds
for the Shrewsbury River navigational channels:
1. Sea Bright Bridge (Rumson-Sea Bright / CR 520) - Clearance & Current Speed (API + Hydraulic Math)
2. Highlands Bridge (Route 36) - Overhead Clearance
"""

import math
import json
import datetime
import threading
import urllib.request
from typing import Dict, Any, List, Optional, Tuple


class BridgeCurrentService:
    """Manages real-time bridge clearance and tidal current calculations."""

    # Bridge Specifications (Official NOAA / USCG Navigation Charts)
    # Sea Bright Bridge (Rumson-Sea Bright Bridge over Shrewsbury River)
    # Location: 40°21'36"N, 73°58'30"W
    SEA_BRIGHT_MHW_CLEARANCE = 15.0      # Feet at Mean High Water (closed position)
    SEA_BRIGHT_MHW_DATUM = 3.64          # Feet MLLW at Station 8531804
    SEA_BRIGHT_MLW_DATUM = 0.13          # Feet MLLW at Station 8531804
    SEA_BRIGHT_MLW_CLEARANCE = 18.51     # Feet at Mean Low Water
    SEA_BRIGHT_CURRENT_STATION = "ACT3886"  # NOAA CO-OPS Seabright Bridge Current Station
    SEA_BRIGHT_FLOOD_DIR = 185           # Degrees True (Southbound into Shrewsbury / AYC)
    SEA_BRIGHT_EBB_DIR = 5               # Degrees True (Northbound toward Sandy Hook Bay)

    # Highlands Bridge (Route 36 Bridge over Shrewsbury River / Sandy Hook Bay)
    # Location: 40°23'47"N, 73°58'47"W
    HIGHLANDS_MHW_CLEARANCE = 65.0       # Feet at Mean High Water (Fixed span)
    HIGHLANDS_MHW_DATUM = 4.41           # Feet MLLW at Station 8531712 (0.90x Sandy Hook)
    HIGHLANDS_MLW_DATUM = 0.18           # Feet MLLW at Station 8531712
    HIGHLANDS_MLW_CLEARANCE = 69.23      # Feet at Mean Low Water
    HIGHLANDS_TIDE_STATION = "8531712"   # NOAA CO-OPS Highlands, NJ

    def __init__(self, tide_engine=None):
        self.tide_engine = tide_engine
        self._lock = threading.Lock()

        # Calculation preference: "api" (NOAA ACT3886) or "math" (Hydraulic Tide-to-Current)
        self.current_mode: str = "api"

        # Cached API data
        self.current_events: List[Dict[str, Any]] = []
        self.highlands_tide_events: List[Dict[str, Any]] = []
        self.sea_bright_tide_events: List[Dict[str, Any]] = []

        self.last_sync: Optional[datetime.datetime] = None
        self.is_current_api_live: bool = False
        self.is_highlands_api_live: bool = False

        # Start initial background fetch
        self.refresh_async()

    def set_current_mode(self, mode: str):
        """Set calculation mode: 'api' or 'math'."""
        if mode in ("api", "math"):
            self.current_mode = mode

    def toggle_current_mode(self) -> str:
        """Toggle between 'api' and 'math' modes."""
        self.current_mode = "math" if self.current_mode == "api" else "api"
        return self.current_mode

    def refresh_async(self):
        """Launches background worker to query NOAA currents and tides."""
        t = threading.Thread(target=self._fetch_worker, daemon=True)
        t.start()

    def _fetch_worker(self):
        """Worker thread to query NOAA API endpoints."""
        with self._lock:
            now = datetime.datetime.now()
            today_str = (now - datetime.timedelta(days=1)).strftime("%Y%m%d")

            # 1. Fetch NOAA Current Predictions for Seabright Bridge (ACT3886)
            try:
                url_curr = (
                    f"https://api.tidesandcurrents.noaa.gov/api/prod/datagetter"
                    f"?begin_date={today_str}&range=72&station={self.SEA_BRIGHT_CURRENT_STATION}"
                    f"&product=currents_predictions&time_zone=lst_ldt"
                    f"&interval=MAX_SLACK&units=english&format=json"
                )
                req = urllib.request.Request(url_curr, headers={"User-Agent": "AYCTideClock/1.0"})
                with urllib.request.urlopen(req, timeout=7) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
                    if "current_predictions" in data and "cp" in data["current_predictions"]:
                        self.current_events = data["current_predictions"]["cp"]
                        self.is_current_api_live = True
            except Exception:
                pass

            # 2. Fetch Highlands Tide Predictions (8531712) for Highlands Bridge
            try:
                url_hl = (
                    f"https://api.tidesandcurrents.noaa.gov/api/prod/datagetter"
                    f"?begin_date={today_str}&range=72&station={self.HIGHLANDS_TIDE_STATION}"
                    f"&product=predictions&datum=MLLW&time_zone=lst_ldt"
                    f"&interval=hilo&units=english&format=json"
                )
                req_hl = urllib.request.Request(url_hl, headers={"User-Agent": "AYCTideClock/1.0"})
                with urllib.request.urlopen(req_hl, timeout=7) as resp:
                    data_hl = json.loads(resp.read().decode("utf-8"))
                    if "predictions" in data_hl:
                        self.highlands_tide_events = data_hl["predictions"]
                        self.is_highlands_api_live = True
            except Exception:
                pass

            # 3. Fetch Sea Bright Tide Predictions (8531804) for Sea Bright Bridge
            try:
                url_sb = (
                    f"https://api.tidesandcurrents.noaa.gov/api/prod/datagetter"
                    f"?begin_date={today_str}&range=72&station=8531804"
                    f"&product=predictions&datum=MLLW&time_zone=lst_ldt"
                    f"&interval=hilo&units=english&format=json"
                )
                req_sb = urllib.request.Request(url_sb, headers={"User-Agent": "AYCTideClock/1.0"})
                with urllib.request.urlopen(req_sb, timeout=7) as resp:
                    data_sb = json.loads(resp.read().decode("utf-8"))
                    if "predictions" in data_sb:
                        self.sea_bright_tide_events = data_sb["predictions"]
            except Exception:
                pass

            self.last_sync = datetime.datetime.now()

    # -------------------------------------------------------------------------
    # Water Level Interpolation Helpers
    # -------------------------------------------------------------------------
    def get_sea_bright_water_level(self, dt: datetime.datetime) -> float:
        """Returns instantaneous water level (ft MLLW) at Sea Bright Bridge."""
        # 1. If we have Sea Bright predictions from API:
        if self.sea_bright_tide_events:
            val = self._interpolate_hilo(self.sea_bright_tide_events, dt)
            if val is not None:
                return val

        # 2. If tide engine has predictions for Sea Bright:
        if self.tide_engine and self.tide_engine.noaa_predictions:
            val = self._interpolate_engine_predictions(self.tide_engine.noaa_predictions, dt)
            if val is not None:
                return val

        # 3. Fallback: Astronomical cosine model from tide engine
        if self.tide_engine:
            status = self.tide_engine.get_status(dt)
            pct = status["water_level_pct"] / 100.0  # 0.0 to 1.0
            # Scale across mean range (0.13 to 3.64 ft MLLW)
            return self.SEA_BRIGHT_MLW_DATUM + pct * (self.SEA_BRIGHT_MHW_DATUM - self.SEA_BRIGHT_MLW_DATUM)

        return 1.85  # Approximate mid-tide level

    def get_highlands_water_level(self, dt: datetime.datetime) -> float:
        """Returns instantaneous water level (ft MLLW) at Highlands Bridge."""
        # 1. If we have Highlands predictions from API:
        if self.highlands_tide_events:
            val = self._interpolate_hilo(self.highlands_tide_events, dt)
            if val is not None:
                return val

        # 2. Derive from Sea Bright level with tidal scaling
        sb_level = self.get_sea_bright_water_level(dt)
        # Highlands has ~1.20x range of Sea Bright due to proximity to Sandy Hook Bay
        sb_range = self.SEA_BRIGHT_MHW_DATUM - self.SEA_BRIGHT_MLW_DATUM
        hl_range = self.HIGHLANDS_MHW_DATUM - self.HIGHLANDS_MLW_DATUM
        ratio = hl_range / sb_range if sb_range > 0 else 1.2
        return self.HIGHLANDS_MLW_DATUM + (sb_level - self.SEA_BRIGHT_MLW_DATUM) * ratio

    def _interpolate_hilo(self, events: List[Dict[str, Any]], dt: datetime.datetime) -> Optional[float]:
        """Interpolates water level between Hi/Lo events using standard cosine tidal curve."""
        parsed = []
        for e in events:
            try:
                t = datetime.datetime.strptime(e["t"], "%Y-%m-%d %H:%M")
                v = float(e["v"])
                parsed.append((t, v, e["type"]))
            except Exception:
                continue

        for i in range(len(parsed) - 1):
            t0, v0, type0 = parsed[i]
            t1, v1, type1 = parsed[i + 1]
            if t0 <= dt <= t1:
                span_sec = (t1 - t0).total_seconds()
                if span_sec <= 0:
                    return v0
                elapsed_sec = (dt - t0).total_seconds()
                ratio = elapsed_sec / span_sec
                # Half-cosine transition
                if type0 == "H":
                    return v1 + (v0 - v1) * (0.5 * (1.0 + math.cos(math.pi * ratio)))
                else:
                    return v0 + (v1 - v0) * (0.5 * (1.0 - math.cos(math.pi * ratio)))

        return None

    def _interpolate_engine_predictions(self, events: List[Dict[str, Any]], dt: datetime.datetime) -> Optional[float]:
        """Interpolates between tide engine's cached prediction objects."""
        for i in range(len(events) - 1):
            e0 = events[i]
            e1 = events[i + 1]
            t0 = e0["datetime"]
            t1 = e1["datetime"]
            if t0 <= dt <= t1:
                span_sec = (t1 - t0).total_seconds()
                if span_sec <= 0:
                    return e0["height_ft"]
                elapsed_sec = (dt - t0).total_seconds()
                ratio = elapsed_sec / span_sec
                v0 = e0["height_ft"]
                v1 = e1["height_ft"]
                if e0["type"] == "HIGH":
                    return v1 + (v0 - v1) * (0.5 * (1.0 + math.cos(math.pi * ratio)))
                else:
                    return v0 + (v1 - v0) * (0.5 * (1.0 - math.cos(math.pi * ratio)))
        return None

    # -------------------------------------------------------------------------
    # 1. Sea Bright Bridge Current Speed (API & Mathematical Models)
    # -------------------------------------------------------------------------
    def get_sea_bright_current(self, now: Optional[datetime.datetime] = None) -> Dict[str, Any]:
        """
        Calculates instantaneous current speed and state under Sea Bright Bridge.
        Provides both NOAA API-based (ACT3886) and mathematical tide-to-current predictions.
        """
        if now is None:
            now = datetime.datetime.now()

        # Calculate via both methods
        api_res = self._calc_api_current(now)
        math_res = self._calc_math_current(now)

        # Active selection
        active_res = api_res if (self.current_mode == "api" and self.is_current_api_live) else math_res

        speed_signed = active_res["speed_signed"]
        speed_abs = abs(speed_signed)

        # Evaluate future current speed (+15 mins) to determine whether speed is increasing or decreasing
        dt_future = now + datetime.timedelta(minutes=15)
        api_res_future = self._calc_api_current(dt_future)
        math_res_future = self._calc_math_current(dt_future)
        active_res_future = api_res_future if (self.current_mode == "api" and self.is_current_api_live) else math_res_future
        speed_abs_future = abs(active_res_future["speed_signed"])

        # Determine speed trend arrow:
        # "▲" if speed is increasing (building current)
        # "▼" if speed is decreasing (easing current)
        # "◆" if steady / slack peak
        if speed_abs_future > speed_abs + 0.04:
            speed_trend = "increasing"
            speed_trend_desc = "Increasing (Building Current)"
            arrow = "▲"
        elif speed_abs_future < speed_abs - 0.04:
            speed_trend = "decreasing"
            speed_trend_desc = "Decreasing (Easing Current)"
            arrow = "▼"
        else:
            speed_trend = "steady"
            speed_trend_desc = "Steady Speed"
            arrow = "◆"

        # Slack threshold: < 0.25 knots
        if speed_abs < 0.25:
            state = "SLACK"
            state_desc = "Slack Water (Minimal Current)"
            direction = "Slack"
            bearing = 0
        elif speed_signed > 0:
            state = "FLOOD"
            state_desc = "Flood Current (Flowing South into Shrewsbury River)"
            direction = "South (185°)"
            bearing = self.SEA_BRIGHT_FLOOD_DIR
        else:
            state = "EBB"
            state_desc = "Ebb Current (Flowing North toward Sandy Hook Bay)"
            direction = "North (005°)"
            bearing = self.SEA_BRIGHT_EBB_DIR

        return {
            "speed_kts": round(speed_abs, 2),
            "speed_signed": round(speed_signed, 2),
            "state": state,
            "state_desc": state_desc,
            "direction": direction,
            "bearing_deg": bearing,
            "arrow": arrow,
            "speed_trend": speed_trend,
            "speed_trend_desc": speed_trend_desc,
            "method": self.current_mode.upper(),
            "is_api_mode": (self.current_mode == "api" and self.is_current_api_live),
            "api_speed_kts": round(abs(api_res["speed_signed"]), 2),
            "math_speed_kts": round(abs(math_res["speed_signed"]), 2),
            "next_slack_str": active_res.get("next_slack_str", "--"),
            "next_peak_str": active_res.get("next_peak_str", "--"),
            "station_id": self.SEA_BRIGHT_CURRENT_STATION
        }

    def _calc_api_current(self, now: datetime.datetime) -> Dict[str, Any]:
        """Interpolates NOAA CO-OPS Station ACT3886 Current Prediction events."""
        if not self.current_events:
            return self._calc_math_current(now)

        parsed = []
        for c in self.current_events:
            try:
                t = datetime.datetime.strptime(c["Time"], "%Y-%m-%d %H:%M")
                v = float(c["Velocity_Major"])
                c_type = c["Type"].lower()
                parsed.append({"time": t, "velocity": v, "type": c_type})
            except Exception:
                continue

        if not parsed:
            return self._calc_math_current(now)

        # Find next slack and peak for countdowns
        future = [p for p in parsed if p["time"] > now]
        next_slack_str = "--"
        next_peak_str = "--"

        for p in future:
            diff = (p["time"] - now).total_seconds()
            hrs = int(diff // 3600)
            mins = int((diff % 3600) // 60)
            time_str = f"in {hrs}h {mins}m" if hrs > 0 else f"in {mins}m"
            if p["type"] == "slack" and next_slack_str == "--":
                next_slack_str = f"{p['time'].strftime('%I:%M %p')} ({time_str})"
            elif p["type"] in ("flood", "ebb") and next_peak_str == "--":
                type_label = "Flood" if p["type"] == "flood" else "Ebb"
                next_peak_str = f"{type_label} {abs(p['velocity']):.1f}k at {p['time'].strftime('%I:%M %p')} ({time_str})"

        # Bracket current time for sinusoidal interpolation
        for i in range(len(parsed) - 1):
            p0 = parsed[i]
            p1 = parsed[i + 1]
            t0 = p0["time"]
            t1 = p1["time"]
            if t0 <= now <= t1:
                span_sec = (t1 - t0).total_seconds()
                if span_sec <= 0:
                    return {"speed_signed": p0["velocity"], "next_slack_str": next_slack_str, "next_peak_str": next_peak_str}

                elapsed_sec = (now - t0).total_seconds()
                ratio = elapsed_sec / span_sec
                v0 = p0["velocity"]
                v1 = p1["velocity"]

                # Standard quarter-diurnal sinusoidal transition:
                # 1. Slack to Peak (v0 == 0) -> v = v1 * sin(pi/2 * ratio)
                if abs(v0) < 0.05:
                    v_interp = v1 * math.sin(0.5 * math.pi * ratio)
                # 2. Peak to Slack (v1 == 0) -> v = v0 * cos(pi/2 * ratio)
                elif abs(v1) < 0.05:
                    v_interp = v0 * math.cos(0.5 * math.pi * ratio)
                else:
                    v_interp = v0 + (v1 - v0) * ratio

                return {
                    "speed_signed": v_interp,
                    "next_slack_str": next_slack_str,
                    "next_peak_str": next_peak_str
                }

        # If bracketing fails, use math fallback
        math_fallback = self._calc_math_current(now)
        math_fallback["next_slack_str"] = next_slack_str
        math_fallback["next_peak_str"] = next_peak_str
        return math_fallback

    def _calc_math_current(self, now: datetime.datetime) -> Dict[str, Any]:
        """
        Mathematical 'Tide-to-Current' Hydrodynamic Prediction Model.
        Continuity Equation: v(t) = K * dh/dt(t - lag)
        Derives current velocity directly from the rate of water level change and tidal phase.
        """
        # Estuary momentum lag: slack water in Shrewsbury River lags High/Low tide by ~45-55 mins
        lag_minutes = 50
        eval_dt = now - datetime.timedelta(minutes=lag_minutes)

        # Numerical derivative of water level (ft / hr)
        dt_plus = eval_dt + datetime.timedelta(minutes=10)
        dt_minus = eval_dt - datetime.timedelta(minutes=10)
        h_plus = self.get_sea_bright_water_level(dt_plus)
        h_minus = self.get_sea_bright_water_level(dt_minus)
        dh_dt = (h_plus - h_minus) / (20.0 / 60.0)  # ft / hr

        # Hydraulic channel calibration factor:
        # Cross-sectional constriction at Rumson-Sea Bright Bridge produces ~1.8 kts per 1.0 ft/hr water level rate
        k_factor = 1.82

        # Astronomical Spring/Neap Scaling factor based on Moon cycle
        scale = 1.0
        if self.tide_engine:
            moon = self.tide_engine.get_moon_info(now)
            # Spring tide (New / Full moon, ill = 0% or 100%): up to 1.15x
            # Neap tide (Quarter moons, ill = 50%): down to 0.85x
            dev = abs(moon["illumination"] - 50.0) / 50.0  # 0.0 at Quarter, 1.0 at New/Full
            scale = 0.86 + 0.28 * dev

        v_signed = dh_dt * k_factor * scale

        # Cap within physical hydrographic boundaries of Shrewsbury channel (-2.6 kts to +2.4 kts)
        v_signed = max(-2.6, min(2.4, v_signed))

        return {
            "speed_signed": v_signed,
            "next_slack_str": "Estimated by Harmonic Math",
            "next_peak_str": "Estimated by Harmonic Math"
        }

    # -------------------------------------------------------------------------
    # 2. Sea Bright Bridge Overhead Clearance
    # -------------------------------------------------------------------------
    def get_sea_bright_clearance(self, now: Optional[datetime.datetime] = None) -> Dict[str, Any]:
        """
        Calculates instantaneous overhead vertical clearance under Sea Bright Bridge.
        Formula: Clearance(t) = MHW_Clearance + (MHW_Datum - WaterLevel(t))
        Charted: 15.0 ft at MHW (Closed), 18.5 ft at MLW (Closed), Unlimited when opened.
        """
        if now is None:
            now = datetime.datetime.now()

        water_level = self.get_sea_bright_water_level(now)
        # Overhead clearance = 15.0 ft + (3.64 ft - water_level)
        clearance = self.SEA_BRIGHT_MHW_CLEARANCE + (self.SEA_BRIGHT_MHW_DATUM - water_level)

        # Clearance trend (is headroom increasing or decreasing?)
        wl_future = self.get_sea_bright_water_level(now + datetime.timedelta(minutes=15))
        if wl_future > water_level + 0.03:
            trend = "decreasing"  # Water rising -> headroom decreasing
            trend_desc = "Decreasing (Flood Tide)"
            trend_caret = "▼"     # Matching Sea Bright Current indicator
            trend_arrow = "▼"
        elif wl_future < water_level - 0.03:
            trend = "increasing"  # Water falling -> headroom increasing
            trend_desc = "Increasing (Ebb Tide)"
            trend_caret = "▲"     # Matching Sea Bright Current indicator
            trend_arrow = "▲"
        else:
            trend = "steady"
            trend_desc = "Steady (Slack Water)"
            trend_caret = "–"     # Steady
            trend_arrow = "–"

        # Safety status alert
        if clearance < 15.0:
            caution = True
            status_badge = "Spring / Surge Alert"
        elif clearance < 16.0:
            caution = False
            status_badge = "Near High Water"
        else:
            caution = False
            status_badge = "Normal Clearance"

        return {
            "bridge_name": "Sea Bright Bridge",
            "route": "Rumson Rd / CR 520",
            "type": "Bascule Drawbridge (Unlimited when open)",
            "clearance_ft": round(clearance, 1),
            "clearance_str": f"{clearance:.1f} ft",
            "water_level_ft": round(water_level, 2),
            "mhw_clearance_ft": self.SEA_BRIGHT_MHW_CLEARANCE,
            "mlw_clearance_ft": self.SEA_BRIGHT_MLW_CLEARANCE,
            "trend": trend,
            "trend_desc": trend_desc,
            "trend_caret": trend_caret,
            "trend_arrow": trend_caret,  # Alias for backward compatibility
            "caution": caution,
            "status_badge": status_badge,
            "is_drawbridge": True
        }

    # -------------------------------------------------------------------------
    # 3. Highlands Bridge Overhead Clearance
    # -------------------------------------------------------------------------
    def get_highlands_clearance(self, now: Optional[datetime.datetime] = None) -> Dict[str, Any]:
        """
        Calculates instantaneous overhead vertical clearance under Highlands Bridge (Route 36).
        Formula: Clearance(t) = MHW_Clearance + (MHW_Datum - WaterLevel(t))
        Charted: 65.0 ft at MHW, 69.2 ft at MLW (Fixed span).
        """
        if now is None:
            now = datetime.datetime.now()

        water_level = self.get_highlands_water_level(now)
        # Overhead clearance = 65.0 ft + (4.41 ft - water_level)
        clearance = self.HIGHLANDS_MHW_CLEARANCE + (self.HIGHLANDS_MHW_DATUM - water_level)

        wl_future = self.get_highlands_water_level(now + datetime.timedelta(minutes=15))
        if wl_future > water_level + 0.04:
            trend = "decreasing"
            trend_desc = "Decreasing (Flood Tide)"
            trend_caret = "▼"     # Matching Sea Bright Current indicator
            trend_arrow = "▼"
        elif wl_future < water_level - 0.04:
            trend = "increasing"
            trend_desc = "Increasing (Ebb Tide)"
            trend_caret = "▲"     # Matching Sea Bright Current indicator
            trend_arrow = "▲"
        else:
            trend = "steady"
            trend_desc = "Steady (Slack Water)"
            trend_caret = "–"
            trend_arrow = "–"

        return {
            "bridge_name": "Highlands Bridge",
            "route": "Route 36 (Highlands - Sea Bright)",
            "type": "Fixed High-Level Span",
            "clearance_ft": round(clearance, 1),
            "clearance_str": f"{clearance:.1f} ft",
            "water_level_ft": round(water_level, 2),
            "mhw_clearance_ft": self.HIGHLANDS_MHW_CLEARANCE,
            "mlw_clearance_ft": self.HIGHLANDS_MLW_CLEARANCE,
            "trend": trend,
            "trend_desc": trend_desc,
            "trend_caret": trend_caret,
            "trend_arrow": trend_caret,  # Alias for backward compatibility
            "is_drawbridge": False
        }
