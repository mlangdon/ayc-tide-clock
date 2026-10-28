"""
Tide Engine: Astronomical calculations, lunar cycle, NOAA CO-OPS live data integration,
and tide prediction model optimized for coastal locations including 40°20'12.7"N 73°58'42.7"W.
"""

import json
import math
import os
import datetime
import threading
import urllib.request
from typing import Dict, List, Any, Optional

# Primary Lunar Semidiurnal constituent (M2)
# Average period: 12 hours, 25 minutes, 14.4 seconds = 44714.4 seconds
TIDE_PERIOD_SECONDS = 44714.4
HALF_PERIOD_SECONDS = TIDE_PERIOD_SECONDS / 2.0  # 6h 12m 37.2s

# Synodic Lunar Month (New Moon to New Moon)
SYNODIC_MONTH_SECONDS = 29.530588853 * 86400.0
NEW_MOON_REFERENCE_UTC = datetime.datetime(2024, 1, 11, 11, 57, 0, tzinfo=datetime.timezone.utc)

# Preset coastal stations with coordinates, reference epochs, and NOAA station IDs
PRESET_STATIONS = {
    "Atlantis Yacht Club (Channel Interpolated - 40°20'12.7\"N)": {
        "name": "Atlantis Yacht Club (Channel Interpolated - 40°20'12.7\"N)",
        "coordinates": "40°20'12.7\"N 73°58'42.7\"W",
        "noaa_id": "8531680",  # Sandy Hook Control Station
        "noaa_name": "AYC Slips (Hydro-interpolated between 8531804 & 8531942)",
        "hydro_offset_high_min": 107,  # +107m from Sandy Hook (+32m past Sea Bright)
        "hydro_offset_low_min": 115,   # +115m from Sandy Hook (+48m past Sea Bright)
        "height_mult": 0.62,
        "ref_high_tide": "2026-10-22T07:08:00",
        "mean_range_ft": 2.50,
        "description": "66 River Ave, Monmouth Beach, NJ • Channel Hydrodynamic Model"
    },
    "Sea Bright / Shrewsbury River Bridge (NOAA 8531804)": {
        "name": "Sea Bright / Shrewsbury River Bridge (NOAA 8531804)",
        "coordinates": "40°21'54.0\"N 73°58'30.0\"W",
        "noaa_id": "8531804",
        "noaa_name": "Sea Bright / Shrewsbury River, NJ",
        "ref_high_tide": "2026-10-22T06:36:00",
        "mean_range_ft": 2.65,
        "description": "Route 36 Bridge ~1.7 mi North of AYC"
    },
    "Long Branch Reach / Shrewsbury River (NOAA 8531942)": {
        "name": "Long Branch Reach / Shrewsbury River (NOAA 8531942)",
        "coordinates": "40°18'36.0\"N 73°59'12.0\"W",
        "noaa_id": "8531942",
        "noaa_name": "Long Branch Reach, Shrewsbury River, NJ",
        "ref_high_tide": "2026-10-22T07:39:00",
        "mean_range_ft": 2.30,
        "description": "Upper River Channel ~1.8 mi South of AYC"
    },
    "Monmouth Beach (Oceanfront Surf, NJ)": {
        "name": "Monmouth Beach (Oceanfront Surf, NJ)",
        "coordinates": "40°20'12.7\"N 73°58'15.0\"W",
        "noaa_id": "8531991",
        "noaa_name": "Long Branch / Monmouth Beach Pier, NJ",
        "ref_high_tide": "2026-10-22T04:55:00",
        "mean_range_ft": 4.12,
        "description": "Monmouth Beach Atlantic Coastline (~500 ft East)"
    },
    "Sandy Hook (Fort Hancock, NJ)": {
        "name": "Sandy Hook (Fort Hancock, NJ)",
        "coordinates": "40°28'00.0\"N 74°00'36.0\"W",
        "noaa_id": "8531680",
        "noaa_name": "Sandy Hook, NJ",
        "ref_high_tide": "2026-10-22T05:21:00",
        "mean_range_ft": 4.85,
        "description": "Sandy Hook Bay / Ocean Entrance"
    },
    "New York Harbor (The Battery, NY)": {
        "name": "New York Harbor (The Battery, NY)",
        "coordinates": "40°42'00.0\"N 74°00'54.0\"W",
        "noaa_id": "8518750",
        "noaa_name": "The Battery, NY",
        "ref_high_tide": "2026-10-22T08:15:00",
        "mean_range_ft": 4.53,
        "description": "Upper New York Bay"
    },
    "Boston Harbor (Commonwealth Pier, MA)": {
        "name": "Boston Harbor (Commonwealth Pier, MA)",
        "coordinates": "42°21'00.0\"N 71°03'00.0\"W",
        "noaa_id": "8443970",
        "noaa_name": "Boston Harbor, MA",
        "ref_high_tide": "2026-10-22T10:45:00",
        "mean_range_ft": 9.50,
        "description": "Massachusetts Bay"
    },
    "Cape Hatteras / Outer Banks, NC": {
        "name": "Cape Hatteras / Outer Banks, NC",
        "coordinates": "35°13'12.0\"N 75°37'48.0\"W",
        "noaa_id": "8654467",
        "noaa_name": "USCG Station Hatteras, NC",
        "ref_high_tide": "2026-10-22T06:50:00",
        "mean_range_ft": 3.20,
        "description": "Outer Banks Atlantic Coast"
    },
    "Miami Beach (Government Cut, FL)": {
        "name": "Miami Beach (Government Cut, FL)",
        "coordinates": "25°46'12.0\"N 80°07'48.0\"W",
        "noaa_id": "8723214",
        "noaa_name": "Virginia Key / Miami, FL",
        "ref_high_tide": "2026-10-22T07:30:00",
        "mean_range_ft": 2.45,
        "description": "Biscayne Bay / Atlantic Entrance"
    },
    "San Francisco (Golden Gate), CA": {
        "name": "San Francisco (Golden Gate), CA",
        "coordinates": "37°48'24.0\"N 122°27'54.0\"W",
        "noaa_id": "9414290",
        "noaa_name": "San Francisco, CA",
        "ref_high_tide": "2026-10-22T11:20:00",
        "mean_range_ft": 4.10,
        "description": "San Francisco Bay"
    },
    "Seattle (Puget Sound), WA": {
        "name": "Seattle (Puget Sound), WA",
        "coordinates": "47°36'00.0\"N 122°20'00.0\"W",
        "noaa_id": "9447130",
        "noaa_name": "Seattle, WA",
        "ref_high_tide": "2026-10-22T04:40:00",
        "mean_range_ft": 7.60,
        "description": "Puget Sound"
    },
    "Custom Port (Manual Calibration)": {
        "name": "Custom Port (Manual Calibration)",
        "coordinates": "Custom Coordinates",
        "noaa_id": None,
        "noaa_name": None,
        "ref_high_tide": "2026-10-22T08:00:00",
        "mean_range_ft": 3.50,
        "description": "Custom calibrated to local tide table"
    }
}

DEFAULT_STATION = "Atlantis Yacht Club (Channel Interpolated - 40°20'12.7\"N)"


DEFAULT_TEMPEST_STATION_ID = 141221
DEFAULT_TEMPEST_TOKEN = "63b1dee7-453a-49cd-be5c-9c905c20fa75"


class TideEngine:
    """Core tidal computation model integrating astronomical harmonics and live NOAA data."""

    def __init__(self, settings_path: Optional[str] = None):
        if settings_path is None:
            import sys
            if getattr(sys, "frozen", False):
                app_dir = os.path.dirname(os.path.abspath(sys.executable))
            else:
                app_dir = os.path.dirname(os.path.abspath(__file__))
            settings_path = os.path.join(app_dir, "tide_settings.json")
        self.settings_path = settings_path
        
        # Primary default is Atlantis Yacht Club 40°20'12.7"N 73°58'42.7"W
        self.station_name = DEFAULT_STATION
        now = datetime.datetime.now()
        # Default ref high tide: 6:36 AM today (exact Monmouth Beach / Shrewsbury River high tide)
        self.ref_high_tide = datetime.datetime(now.year, now.month, now.day, 6, 36, 0)
        self.theme = "ayc_navy"
        self.always_on_top = False
        self.sound_alert = False
        self.tempest_station_id = DEFAULT_TEMPEST_STATION_ID
        self.tempest_token = DEFAULT_TEMPEST_TOKEN

        # Desktop Widget Preferences
        self.widget_x = None
        self.widget_y = None
        self.widget_mode = "circular"   # "circular" or "hud"
        self.widget_alpha = 0.95
        self.widget_topmost = True
        self.widget_locked = False

        # Bridge & Current Calculation Settings
        self.bridge_current_mode = "api"  # "api" or "math"

        # Live NOAA data cache
        self.noaa_predictions: List[Dict[str, Any]] = []
        self.noaa_last_sync: Optional[datetime.datetime] = None
        self.is_noaa_live = False
        self._fetching_lock = threading.Lock()

        self.load_settings()
        self._trigger_background_noaa_sync()

    @property
    def current_station_info(self) -> Dict[str, Any]:
        return PRESET_STATIONS.get(self.station_name, PRESET_STATIONS[DEFAULT_STATION])

    def set_station(self, station_name: str):
        """Switch to a preset station and trigger sync."""
        if station_name in PRESET_STATIONS:
            self.station_name = station_name
            station_info = PRESET_STATIONS[station_name]
            now = datetime.datetime.now()
            raw_iso = station_info["ref_high_tide"]
            try:
                base_dt = datetime.datetime.fromisoformat(raw_iso)
                self.ref_high_tide = datetime.datetime(now.year, now.month, now.day, base_dt.hour, base_dt.minute, 0)
            except Exception:
                pass
            self.noaa_predictions = []
            self.is_noaa_live = False
            self.save_settings()
            self._trigger_background_noaa_sync()

    def set_reference_high(self, dt: datetime.datetime):
        """Directly set a known High Tide timestamp."""
        self.ref_high_tide = dt
        self.is_noaa_live = False
        self.save_settings()

    def calibrate_to_now(self, is_high: bool = True):
        """Calibrates the tide clock so that current moment is High or Low tide."""
        now = datetime.datetime.now()
        if is_high:
            self.ref_high_tide = now
        else:
            self.ref_high_tide = now - datetime.timedelta(seconds=HALF_PERIOD_SECONDS)
        self.is_noaa_live = False
        self.save_settings()

    def adjust_reference_minutes(self, minutes: int):
        """Adjust reference tide time by +/- N minutes."""
        self.ref_high_tide += datetime.timedelta(minutes=minutes)
        self.is_noaa_live = False
        self.save_settings()

    def sync_noaa_now(self):
        """Manually trigger background NOAA sync."""
        self._trigger_background_noaa_sync()

    def _trigger_background_noaa_sync(self):
        """Launches background thread to fetch NOAA predictions if station has NOAA ID."""
        st = self.current_station_info
        noaa_id = st.get("noaa_id")
        if not noaa_id:
            return

        t = threading.Thread(target=self._fetch_noaa_data, args=(noaa_id,), daemon=True)
        t.start()

    def _fetch_noaa_data(self, noaa_id: str):
        """Worker thread querying NOAA CO-OPS REST API with hydrodynamic interpolation support."""
        with self._fetching_lock:
            try:
                st = self.current_station_info
                now = datetime.datetime.now()
                # Query window covering yesterday through 4 days ahead to bracket current events
                yesterday = now - datetime.timedelta(days=1)
                begin_date = yesterday.strftime("%Y%m%d")
                url = (
                    f"https://api.tidesandcurrents.noaa.gov/api/prod/datagetter"
                    f"?begin_date={begin_date}&range=120&station={noaa_id}"
                    f"&product=predictions&datum=MLLW&time_zone=lst_ldt"
                    f"&interval=hilo&units=english&format=json"
                )
                req = urllib.request.Request(url, headers={"User-Agent": "TideClockDesktop/1.0"})
                with urllib.request.urlopen(req, timeout=6) as response:
                    raw_data = response.read().decode("utf-8")
                    data = json.loads(raw_data)

                if "predictions" in data and len(data["predictions"]) > 0:
                    parsed = []
                    h_offset = st.get("hydro_offset_high_min", 0)
                    l_offset = st.get("hydro_offset_low_min", 0)
                    h_mult = st.get("height_mult", 1.0)

                    for item in data["predictions"]:
                        dt = datetime.datetime.strptime(item["t"], "%Y-%m-%d %H:%M")
                        val_ft = float(item["v"])
                        t_type = "HIGH" if item["type"] == "H" else "LOW"

                        # Apply hydrodynamic river channel lag and dampening if modeled
                        if h_offset != 0 or l_offset != 0 or h_mult != 1.0:
                            if t_type == "HIGH":
                                dt += datetime.timedelta(minutes=h_offset)
                                val_ft *= h_mult
                            else:
                                dt += datetime.timedelta(minutes=l_offset)
                                val_ft *= h_mult

                        parsed.append({
                            "type": t_type,
                            "datetime": dt,
                            "height_ft": val_ft
                        })

                    self.noaa_predictions = parsed
                    self.noaa_last_sync = now
                    self.is_noaa_live = True

                    # Update reference high tide to most recent high from NOAA data
                    past_highs = [p["datetime"] for p in parsed if p["type"] == "HIGH" and p["datetime"] <= now]
                    if past_highs:
                        self.ref_high_tide = past_highs[-1]
                    elif parsed and parsed[0]["type"] == "HIGH":
                        self.ref_high_tide = parsed[0]["datetime"]
            except Exception:
                # Retains harmonic engine fallback silently
                pass

    def get_status(self, now: Optional[datetime.datetime] = None) -> Dict[str, Any]:
        """Calculates current clock angle, tide state, water level, and time to events."""
        if now is None:
            now = datetime.datetime.now()

        # If NOAA predictions exist, use exact NOAA bracket
        if self.is_noaa_live and self.noaa_predictions:
            future = [p for p in self.noaa_predictions if p["datetime"] > now]
            past = [p for p in self.noaa_predictions if p["datetime"] <= now]

            if future and past:
                prev_ev = past[-1]
                next_ev = future[0]

                span_sec = (next_ev["datetime"] - prev_ev["datetime"]).total_seconds()
                elapsed_sec = (now - prev_ev["datetime"]).total_seconds()
                ratio = max(0.0, min(1.0, elapsed_sec / span_sec)) if span_sec > 0 else 0.5

                if prev_ev["type"] == "HIGH":
                    # High to Low -> Falling (0 deg to 180 deg)
                    angle_deg = ratio * 180.0
                    is_falling = True
                else:
                    # Low to High -> Rising (180 deg to 360 deg)
                    angle_deg = 180.0 + (ratio * 180.0)
                    is_falling = False

                sec_to_next = (next_ev["datetime"] - now).total_seconds()
                next_type = next_ev["type"]
                next_time = next_ev["datetime"]
                next_height = next_ev["height_ft"]

                # Slack water detection: within 12 minutes (720s) of peak
                if elapsed_sec < 720:
                    state = f"{prev_ev['type']} TIDE"
                    state_desc = f"Slack Water (Peak {prev_ev['type'].title()})"
                elif sec_to_next < 720:
                    state = f"{next_type} TIDE"
                    state_desc = f"Slack Water (Approaching {next_type.title()})"
                elif is_falling:
                    state = "FALLING"
                    state_desc = "Ebb Tide (Water Level Falling)"
                else:
                    state = "RISING"
                    state_desc = "Flood Tide (Water Level Rising)"

                # Smooth water level percentage
                rad = math.radians(angle_deg)
                water_level_pct = ((math.cos(rad) + 1.0) / 2.0) * 100.0

                hrs_until_next = int(sec_to_next // 3600)
                mins_until_next = int((sec_to_next % 3600) // 60)
                secs_until_next = int(sec_to_next % 60)
                countdown_str = f"{hrs_until_next}h {mins_until_next:02d}m"

                return {
                    "now": now,
                    "angle_deg": angle_deg,
                    "state": state,
                    "state_desc": state_desc,
                    "is_falling": is_falling,
                    "water_level_pct": water_level_pct,
                    "next_type": next_type,
                    "next_time": next_time,
                    "next_height": next_height,
                    "sec_to_next": sec_to_next,
                    "countdown_str": countdown_str,
                    "hrs_until_next": hrs_until_next,
                    "mins_until_next": mins_until_next,
                    "secs_until_next": secs_until_next,
                    "is_noaa": True
                }

        # Harmonic semidiurnal calculation fallback
        diff_seconds = (now - self.ref_high_tide).total_seconds()
        cycle_sec = diff_seconds % TIDE_PERIOD_SECONDS
        if cycle_sec < 0:
            cycle_sec += TIDE_PERIOD_SECONDS

        angle_deg = (cycle_sec / TIDE_PERIOD_SECONDS) * 360.0
        is_falling = cycle_sec < HALF_PERIOD_SECONDS

        if cycle_sec < 600 or cycle_sec > (TIDE_PERIOD_SECONDS - 600):
            state = "HIGH TIDE"
            state_desc = "Slack Water (Peak High)"
        elif abs(cycle_sec - HALF_PERIOD_SECONDS) < 600:
            state = "LOW TIDE"
            state_desc = "Slack Water (Peak Low)"
        elif is_falling:
            state = "FALLING"
            state_desc = "Ebb Tide (Water Level Falling)"
        else:
            state = "RISING"
            state_desc = "Flood Tide (Water Level Rising)"

        if is_falling:
            sec_to_next = HALF_PERIOD_SECONDS - cycle_sec
            next_type = "LOW"
            next_time = now + datetime.timedelta(seconds=sec_to_next)
        else:
            sec_to_next = TIDE_PERIOD_SECONDS - cycle_sec
            next_type = "HIGH"
            next_time = now + datetime.timedelta(seconds=sec_to_next)

        rad = math.radians(angle_deg)
        water_level_pct = ((math.cos(rad) + 1.0) / 2.0) * 100.0

        hrs_until_next = int(sec_to_next // 3600)
        mins_until_next = int((sec_to_next % 3600) // 60)
        secs_until_next = int(sec_to_next % 60)
        countdown_str = f"{hrs_until_next}h {mins_until_next:02d}m"

        return {
            "now": now,
            "angle_deg": angle_deg,
            "state": state,
            "state_desc": state_desc,
            "is_falling": is_falling,
            "water_level_pct": water_level_pct,
            "next_type": next_type,
            "next_time": next_time,
            "next_height": None,
            "sec_to_next": sec_to_next,
            "countdown_str": countdown_str,
            "hrs_until_next": hrs_until_next,
            "mins_until_next": mins_until_next,
            "secs_until_next": secs_until_next,
            "is_noaa": False
        }

    def get_upcoming_tides(self, count: int = 8, now: Optional[datetime.datetime] = None) -> List[Dict[str, Any]]:
        """Projects upcoming tide events using NOAA data when available, else harmonics."""
        if now is None:
            now = datetime.datetime.now()

        formatted = []

        # If NOAA live predictions exist for this station
        if self.is_noaa_live and self.noaa_predictions:
            future_noaa = [p for p in self.noaa_predictions if p["datetime"] > now]
            for ev in future_noaa[:count]:
                dt = ev["datetime"]
                delta = (dt - now).total_seconds()
                hrs = int(delta // 3600)
                mins = int((delta % 3600) // 60)

                today = now.date()
                if dt.date() == today:
                    day_str = "Today"
                elif dt.date() == today + datetime.timedelta(days=1):
                    day_str = "Tomorrow"
                else:
                    day_str = dt.strftime("%a %b %d")

                time_str = dt.strftime("%I:%M %p")
                countdown_str = f"in {hrs}h {mins:02d}m"
                ht = ev.get("height_ft")
                ht_str = f"{ht:+.1f} ft MLLW" if ht is not None else ("High Water" if ev["type"] == "HIGH" else "Low Water")

                src_label = "Channel Interpolated" if self.current_station_info.get("hydro_offset_high_min") else "NOAA Verified"
                formatted.append({
                    "type": ev["type"],
                    "datetime": dt,
                    "day_label": day_str,
                    "time_str": time_str,
                    "countdown_str": countdown_str,
                    "height_str": ht_str,
                    "is_high": ev["type"] == "HIGH",
                    "source": src_label
                })
            if formatted:
                return formatted

        # Fallback to harmonic calculations
        diff_seconds = (now - self.ref_high_tide).total_seconds()
        current_cycle = math.floor(diff_seconds / TIDE_PERIOD_SECONDS)

        events = []
        for k in range(current_cycle - 1, current_cycle + count + 2):
            high_dt = self.ref_high_tide + datetime.timedelta(seconds=k * TIDE_PERIOD_SECONDS)
            if high_dt > now:
                events.append({"type": "HIGH", "datetime": high_dt, "delta_seconds": (high_dt - now).total_seconds()})
            low_dt = self.ref_high_tide + datetime.timedelta(seconds=(k * TIDE_PERIOD_SECONDS) + HALF_PERIOD_SECONDS)
            if low_dt > now:
                events.append({"type": "LOW", "datetime": low_dt, "delta_seconds": (low_dt - now).total_seconds()})

        events.sort(key=lambda x: x["datetime"])
        results = events[:count]

        mean_range = self.current_station_info.get("mean_range_ft", 3.5)
        for ev in results:
            dt = ev["datetime"]
            delta = ev["delta_seconds"]
            hrs = int(delta // 3600)
            mins = int((delta % 3600) // 60)

            today = now.date()
            if dt.date() == today:
                day_str = "Today"
            elif dt.date() == today + datetime.timedelta(days=1):
                day_str = "Tomorrow"
            else:
                day_str = dt.strftime("%a %b %d")

            time_str = dt.strftime("%I:%M %p")
            countdown_str = f"in {hrs}h {mins:02d}m"
            ht_est = f"~{mean_range:.1f} ft (Est)" if ev["type"] == "HIGH" else "~0.5 ft (Est)"

            formatted.append({
                "type": ev["type"],
                "datetime": dt,
                "day_label": day_str,
                "time_str": time_str,
                "countdown_str": countdown_str,
                "height_str": ht_est,
                "is_high": ev["type"] == "HIGH",
                "source": "Lunar Harmonic"
            })

        return formatted

    def get_moon_info(self, now: Optional[datetime.datetime] = None) -> Dict[str, Any]:
        """Calculates current Moon Phase and Tidal Range (Spring / Neap)."""
        if now is None:
            now_utc = datetime.datetime.now(datetime.timezone.utc)
        elif now.tzinfo is None:
            now_utc = now.replace(tzinfo=datetime.timezone.utc)
        else:
            now_utc = now.astimezone(datetime.timezone.utc)

        diff_sec = (now_utc - NEW_MOON_REFERENCE_UTC).total_seconds()
        age_sec = diff_sec % SYNODIC_MONTH_SECONDS
        fraction = age_sec / SYNODIC_MONTH_SECONDS
        age_days = age_sec / 86400.0

        if fraction < 0.03 or fraction >= 0.97:
            phase_name = "New Moon"
            icon_char = "NEW"
            tide_type = "Spring Tide"
            tide_sub = "Strongest currents • Max range"
        elif fraction < 0.22:
            phase_name = "Waxing Crescent"
            icon_char = "CRES"
            tide_type = "Normal Tide"
            tide_sub = "Moderate tidal range"
        elif fraction < 0.28:
            phase_name = "First Quarter"
            icon_char = "1ST"
            tide_type = "Neap Tide"
            tide_sub = "Weakest currents • Min range"
        elif fraction < 0.47:
            phase_name = "Waxing Gibbous"
            icon_char = "GIBB"
            tide_type = "Normal Tide"
            tide_sub = "Moderate tidal range"
        elif fraction < 0.53:
            phase_name = "Full Moon"
            icon_char = "FULL"
            tide_type = "Spring Tide"
            tide_sub = "Strongest currents • Max range"
        elif fraction < 0.72:
            phase_name = "Waning Gibbous"
            icon_char = "GIBB"
            tide_type = "Normal Tide"
            tide_sub = "Moderate tidal range"
        elif fraction < 0.78:
            phase_name = "Third Quarter"
            icon_char = "3RD"
            tide_type = "Neap Tide"
            tide_sub = "Weakest currents • Min range"
        else:
            phase_name = "Waning Crescent"
            icon_char = "CRES"
            tide_type = "Normal Tide"
            tide_sub = "Moderate tidal range"

        illumination = round(((1.0 - math.cos(fraction * 2.0 * math.pi)) / 2.0) * 100.0)

        return {
            "fraction": fraction,
            "age_days": round(age_days, 1),
            "phase_name": phase_name,
            "icon_char": icon_char,
            "tide_type": tide_type,
            "tide_sub": tide_sub,
            "illumination": illumination
        }

    def save_settings(self):
        """Persists current calibration and preferences to JSON."""
        data = {
            "station_name": self.station_name,
            "ref_high_tide": self.ref_high_tide.isoformat(),
            "theme": self.theme,
            "always_on_top": self.always_on_top,
            "sound_alert": self.sound_alert,
            "tempest_station_id": self.tempest_station_id,
            "tempest_token": self.tempest_token,
            "widget_x": self.widget_x,
            "widget_y": self.widget_y,
            "widget_mode": self.widget_mode,
            "widget_alpha": self.widget_alpha,
            "widget_topmost": self.widget_topmost,
            "widget_locked": self.widget_locked,
            "bridge_current_mode": self.bridge_current_mode
        }
        try:
            with open(self.settings_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except Exception:
            pass

    def load_settings(self):
        """Loads calibration and preferences from JSON."""
        if not os.path.exists(self.settings_path):
            return
        try:
            with open(self.settings_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if "station_name" in data and data["station_name"] in PRESET_STATIONS:
                self.station_name = data["station_name"]
            if "ref_high_tide" in data:
                self.ref_high_tide = datetime.datetime.fromisoformat(data["ref_high_tide"])
            if "theme" in data:
                self.theme = data["theme"]
            if "always_on_top" in data:
                self.always_on_top = bool(data["always_on_top"])
            if "sound_alert" in data:
                self.sound_alert = bool(data["sound_alert"])
            if "tempest_station_id" in data:
                self.tempest_station_id = int(data["tempest_station_id"])
            if "tempest_token" in data and data["tempest_token"]:
                self.tempest_token = str(data["tempest_token"])
            else:
                self.tempest_token = DEFAULT_TEMPEST_TOKEN
            if "widget_x" in data and data["widget_x"] is not None:
                self.widget_x = int(data["widget_x"])
            if "widget_y" in data and data["widget_y"] is not None:
                self.widget_y = int(data["widget_y"])
            if "widget_mode" in data and data["widget_mode"] in ("circular", "hud"):
                self.widget_mode = str(data["widget_mode"])
            if "widget_alpha" in data:
                self.widget_alpha = float(data["widget_alpha"])
            if "widget_topmost" in data:
                self.widget_topmost = bool(data["widget_topmost"])
            if "widget_locked" in data:
                self.widget_locked = bool(data["widget_locked"])
            if "bridge_current_mode" in data and data["bridge_current_mode"] in ("api", "math"):
                self.bridge_current_mode = str(data["bridge_current_mode"])
        except Exception:
            pass
