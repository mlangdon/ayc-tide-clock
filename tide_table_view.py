"""
Tide Table View: Interactive side dashboard with upcoming tide schedule,
wave visualizer, moon phase, NOAA status, and calibration controls.
Optimized for 40°20'12.7"N 73°58'42.7"W (Monmouth Beach / Shrewsbury River, NJ).
"""

import math
import tkinter as tk
from tkinter import ttk, messagebox
import datetime
from typing import Dict, Any, List, Callable, Optional
from PIL import Image, ImageDraw, ImageTk
from ayc_branding import draw_ayc_burgee, AYC_INFO


class TideTableView(tk.Frame):
    """Dashboard pane showing tidal table, lunar cycle, wave visualizer, weather metrics, and controls."""

    def __init__(self, parent, engine, theme_data: Dict[str, Any], on_change_callback: Callable,
                 weather_service=None, on_open_weather_settings: Optional[Callable] = None,
                 bridge_service=None, **kwargs):
        super().__init__(parent, bg=theme_data["window_bg"], **kwargs)
        self.engine = engine
        self.theme = theme_data
        self.on_change_callback = on_change_callback
        self.weather_service = weather_service
        self.on_open_weather_settings = on_open_weather_settings
        self.bridge_service = bridge_service
        self._wave_photo: Optional[ImageTk.PhotoImage] = None

        self._build_ui()

    def set_theme(self, theme_data: Dict[str, Any]):
        """Update colors when switching themes."""
        self.theme = theme_data
        self.config(bg=self.theme["window_bg"])
        self._apply_theme_styles()
        self.update_data()

    def _apply_theme_styles(self):
        """Update widget background and foreground colors according to active theme."""
        t = self.theme
        self.loc_card.config(bg=t["card_bg"], highlightbackground=t["card_border"])
        self.burgee_canvas.config(bg=t["card_bg"])
        self.burgee_canvas.delete("all")
        draw_ayc_burgee(self.burgee_canvas, 0, 0, 44, 32, prefer_image=True)

        self.lbl_club_name.config(bg=t["card_bg"], fg=t["accent"])
        self.lbl_club_sub.config(bg=t["card_bg"], fg=t["text_primary"])
        self.lbl_station.config(bg=t["card_bg"], fg=t["text_primary"])
        self.lbl_station_coords.config(bg=t["card_bg"], fg=t["accent"])
        self.lbl_website.config(bg=t["card_bg"], fg=t["text_secondary"])
        self.lbl_station_sub.config(bg=t["card_bg"], fg=t["text_secondary"])
        self.lbl_noaa_status.config(bg=t["card_bg"])
        self.lbl_datetime.config(bg=t["card_bg"], fg=t["text_primary"])
        self.lbl_moon_icon.config(bg=t["card_bg"], fg=t["accent"])
        self.lbl_moon_desc.config(bg=t["card_bg"], fg=t["text_primary"])
        self.lbl_tide_type.config(bg=t["card_bg"], fg=t["accent"])

        # Weather card theme styling
        self.weather_card.config(bg=t["card_bg"], highlightbackground=t["card_border"])
        self.lbl_wx_title.config(bg=t["card_bg"], fg=t["accent"])
        self.lbl_wx_source.config(bg=t["card_bg"])
        if hasattr(self, "btn_wx_config") and self.btn_wx_config:
            self.btn_wx_config.config(bg=t["badge_bg"], fg=t["text_secondary"], activebackground=t["accent"])
        self.lbl_wx_temp.config(bg=t["card_bg"], fg=t["text_primary"])
        self.lbl_wx_cond.config(bg=t["card_bg"], fg=t["text_secondary"])
        self.lbl_wx_wind.config(bg=t["card_bg"], fg=t["accent_blue"])
        self.lbl_wx_gust.config(bg=t["card_bg"], fg=t["text_secondary"])
        self.lbl_wx_baro.config(bg=t["card_bg"], fg=t["accent"])
        self.lbl_wx_baro_sub.config(bg=t["card_bg"], fg=t["text_secondary"])
        self.lbl_wx_humidity.config(bg=t["card_bg"], fg=t["text_secondary"])
        self.lbl_wx_rain.config(bg=t["card_bg"], fg=t["text_secondary"])
        self.lbl_wx_solar.config(bg=t["card_bg"], fg=t["text_secondary"])
        for f in getattr(self, "wx_frames", []):
            f.config(bg=t["card_bg"])

        # Navigation & Bridges card theme styling
        if hasattr(self, "nav_card"):
            self.nav_card.config(bg=t["card_bg"], highlightbackground=t["card_border"])
            self.lbl_nav_title.config(bg=t["card_bg"], fg=t["accent"])
            self.btn_current_mode.config(bg=t["badge_bg"], fg=t["accent_blue"], activebackground=t["accent"])
            self.lbl_sb_clearance.config(bg=t["card_bg"], fg=t["text_primary"])
            self.lbl_sb_clearance_sub.config(bg=t["card_bg"], fg=t["text_secondary"])
            self.lbl_current_title.config(bg=t["card_bg"], fg=t["accent_blue"])
            self.lbl_sb_current.config(bg=t["card_bg"], fg=t["accent_blue"])
            self.lbl_sb_current_sub.config(bg=t["card_bg"], fg=t["text_secondary"])
            self.lbl_hl_clearance.config(bg=t["card_bg"], fg=t["text_primary"])
            self.lbl_hl_clearance_sub.config(bg=t["card_bg"], fg=t["text_secondary"])
            for f in getattr(self, "nav_frames", []):
                f.config(bg=t["card_bg"])
            for lbl in getattr(self, "nav_sub_headers", []):
                lbl.config(bg=t["card_bg"], fg=t["text_secondary"])

        self.wave_canvas.config(bg=t["card_bg"], highlightbackground=t["card_border"])
        self.table_card.config(bg=t["card_bg"], highlightbackground=t["card_border"])
        self.lbl_table_title.config(bg=t["card_bg"], fg=t["accent"])
        self.ctrl_card.config(bg=t["card_bg"], highlightbackground=t["card_border"])
        self.lbl_ctrl_title.config(bg=t["card_bg"], fg=t["text_primary"])

        for lbl in self.header_labels:
            lbl.config(bg=t["table_header_bg"], fg=t["text_secondary"])

    def _build_ui(self):
        """Construct the dashboard widgets."""
        t = self.theme

        # Top Section: Station, Coordinates, Local Time & Moon Phase Card
        self.loc_card = tk.Frame(self, bg=t["card_bg"], highlightbackground=t["card_border"], highlightthickness=1, padx=10, pady=8)
        self.loc_card.pack(fill=tk.X, padx=10, pady=(10, 4))

        # AYC Header Row with Club Burgee
        ayc_header_row = tk.Frame(self.loc_card, bg=t["card_bg"])
        ayc_header_row.pack(fill=tk.X, pady=(0, 4))

        # Canvas for AYC Burgee
        self.burgee_canvas = tk.Canvas(ayc_header_row, width=48, height=34, bg=t["card_bg"], highlightthickness=0)
        self.burgee_canvas.pack(side=tk.LEFT, padx=(0, 8))
        draw_ayc_burgee(self.burgee_canvas, 0, 0, 48, 34, prefer_image=True)

        ayc_title_box = tk.Frame(ayc_header_row, bg=t["card_bg"])
        ayc_title_box.pack(side=tk.LEFT, fill=tk.X, expand=True)

        self.lbl_club_name = tk.Label(ayc_title_box, text="ATLANTIS YACHT CLUB", font=("Georgia", 11, "bold"), bg=t["card_bg"], fg=t["accent"], anchor="w")
        self.lbl_club_name.pack(fill=tk.X)

        self.lbl_club_sub = tk.Label(ayc_title_box, text="66 River Ave, Monmouth Beach, NJ • Est. 1961", font=("Segoe UI", 8, "bold"), bg=t["card_bg"], fg=t["text_primary"], anchor="w")
        self.lbl_club_sub.pack(fill=tk.X)

        btn_box_top = tk.Frame(ayc_header_row, bg=t["card_bg"])
        btn_box_top.pack(side=tk.RIGHT)

        self.btn_sync = tk.Button(
            btn_box_top, text="Sync NOAA", font=("Segoe UI", 8, "bold"),
            bg=t["badge_bg"], fg=t["accent_blue"], activebackground=t["accent"],
            relief=tk.FLAT, bd=0, padx=6, pady=2, cursor="hand2",
            command=self._sync_noaa
        )
        self.btn_sync.pack(side=tk.LEFT, padx=(0, 4))

        btn_station = tk.Button(
            btn_box_top, text="Ports", font=("Segoe UI", 8, "bold"),
            bg=t["badge_bg"], fg=t["text_primary"], activebackground=t["accent"],
            relief=tk.FLAT, bd=0, padx=6, pady=2, cursor="hand2",
            command=self._open_station_dialog
        )
        btn_station.pack(side=tk.LEFT)

        # Station Title / Docks
        self.lbl_station = tk.Label(self.loc_card, text=self.engine.station_name, font=("Segoe UI", 10, "bold"), bg=t["card_bg"], fg=t["text_primary"], anchor="w")
        self.lbl_station.pack(fill=tk.X, pady=(2, 0))

        # GPS Coordinates Badge & Website
        coords_row = tk.Frame(self.loc_card, bg=t["card_bg"])
        coords_row.pack(fill=tk.X, pady=(1, 0))

        coords_str = self.engine.current_station_info.get("coordinates", "40°20'12.7\"N 73°58'42.7\"W")
        self.lbl_station_coords = tk.Label(
            coords_row, text=f"GPS: {coords_str}",
            font=("Consolas", 8, "bold"), bg=t["card_bg"], fg=t["accent"], anchor="w"
        )
        self.lbl_station_coords.pack(side=tk.LEFT)

        self.lbl_website = tk.Label(coords_row, text="atlantisyachtclub.org", font=("Segoe UI", 8, "italic"), bg=t["card_bg"], fg=t["text_secondary"])
        self.lbl_website.pack(side=tk.RIGHT)

        # Station description and NOAA verified badge
        status_row = tk.Frame(self.loc_card, bg=t["card_bg"])
        status_row.pack(fill=tk.X, pady=(1, 4))

        self.lbl_station_sub = tk.Label(status_row, text=self.engine.current_station_info.get("description", "Shrewsbury River"), font=("Segoe UI", 8), bg=t["card_bg"], fg=t["text_secondary"], anchor="w")
        self.lbl_station_sub.pack(side=tk.LEFT)

        self.lbl_noaa_status = tk.Label(status_row, text="● NOAA Syncing...", font=("Segoe UI", 8, "bold"), bg=t["card_bg"], fg=t["accent"])
        self.lbl_noaa_status.pack(side=tk.RIGHT)

        # Time and Moon split row
        info_row = tk.Frame(self.loc_card, bg=t["card_bg"])
        info_row.pack(fill=tk.X, pady=(2, 0))

        time_col = tk.Frame(info_row, bg=t["card_bg"])
        time_col.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.lbl_datetime = tk.Label(time_col, text="--:--:--", font=("Segoe UI", 11, "bold"), bg=t["card_bg"], fg=t["text_primary"], anchor="w")
        self.lbl_datetime.pack(fill=tk.X)

        moon_col = tk.Frame(info_row, bg=t["card_bg"])
        moon_col.pack(side=tk.RIGHT)
        
        self.lbl_moon_icon = tk.Label(moon_col, text="●", font=("Segoe UI", 12), bg=t["card_bg"], fg=t["accent"])
        self.lbl_moon_icon.pack(side=tk.LEFT, padx=(0, 4))

        moon_text_frame = tk.Frame(moon_col, bg=t["card_bg"])
        moon_text_frame.pack(side=tk.LEFT)
        self.lbl_moon_desc = tk.Label(moon_text_frame, text="Moon Phase", font=("Segoe UI", 8, "bold"), bg=t["card_bg"], fg=t["text_primary"], anchor="e")
        self.lbl_moon_desc.pack(anchor="e")
        self.lbl_tide_type = tk.Label(moon_text_frame, text="Tidal Range", font=("Segoe UI", 8), bg=t["card_bg"], fg=t["accent"], anchor="e")
        self.lbl_tide_type.pack(anchor="e")

        # Weather Section: Tempestwx Station 141221 Meteorological Card
        self.weather_card = tk.Frame(self, bg=t["card_bg"], highlightbackground=t["card_border"], highlightthickness=1, padx=8, pady=5)
        self.weather_card.pack(fill=tk.X, padx=10, pady=(0, 3))

        # Weather Header
        wx_head = tk.Frame(self.weather_card, bg=t["card_bg"])
        wx_head.pack(fill=tk.X, pady=(0, 2))

        self.lbl_wx_title = tk.Label(
            wx_head, text="TEMPEST HARBOR WEATHER • STN 141221",
            font=("Segoe UI", 8, "bold"), bg=t["card_bg"], fg=t["accent"], anchor="w"
        )
        self.lbl_wx_title.pack(side=tk.LEFT)

        wx_head_right = tk.Frame(wx_head, bg=t["card_bg"])
        wx_head_right.pack(side=tk.RIGHT)

        self.lbl_wx_source = tk.Label(
            wx_head_right, text="● Connecting...",
            font=("Segoe UI", 8, "bold"), bg=t["card_bg"], fg=t["text_secondary"]
        )
        self.lbl_wx_source.pack(side=tk.LEFT, padx=(0, 6))

        # Direct link to Tempestwx Station 141221 live web dashboard
        self.btn_wx_link = tk.Button(
            wx_head_right, text="🔗 tempestwx.com/station/141221", font=("Segoe UI", 7, "bold"),
            bg=t["badge_bg"], fg=t["accent_blue"], activebackground=t["accent"],
            relief=tk.FLAT, bd=0, padx=6, pady=1, cursor="hand2",
            command=self._open_tempest_website
        )
        self.btn_wx_link.pack(side=tk.LEFT)

        # Weather Main Metrics Row (Temp / Wind / Pressure)
        wx_main = tk.Frame(self.weather_card, bg=t["card_bg"])
        wx_main.pack(fill=tk.X, pady=(1, 2))

        # 1. Temperature Block
        temp_block = tk.Frame(wx_main, bg=t["card_bg"])
        temp_block.pack(side=tk.LEFT, fill=tk.X, expand=True)

        self.lbl_wx_temp = tk.Label(
            temp_block, text="--°F",
            font=("Segoe UI", 12, "bold"), bg=t["card_bg"], fg=t["text_primary"], anchor="w"
        )
        self.lbl_wx_temp.pack(fill=tk.X)

        self.lbl_wx_cond = tk.Label(
            temp_block, text="Feels --° • Initializing...",
            font=("Segoe UI", 8), bg=t["card_bg"], fg=t["text_secondary"], anchor="w"
        )
        self.lbl_wx_cond.pack(fill=tk.X)

        # 2. Wind Block
        wind_block = tk.Frame(wx_main, bg=t["card_bg"])
        wind_block.pack(side=tk.LEFT, fill=tk.X, expand=True)

        self.lbl_wx_wind = tk.Label(
            wind_block, text="💨 -- kts --",
            font=("Segoe UI", 9, "bold"), bg=t["card_bg"], fg=t["accent_blue"], anchor="w"
        )
        self.lbl_wx_wind.pack(fill=tk.X)

        self.lbl_wx_gust = tk.Label(
            wind_block, text="Gusts -- • Dir --°",
            font=("Segoe UI", 8), bg=t["card_bg"], fg=t["text_secondary"], anchor="w"
        )
        self.lbl_wx_gust.pack(fill=tk.X)

        # 3. Barometer Block
        baro_block = tk.Frame(wx_main, bg=t["card_bg"])
        baro_block.pack(side=tk.LEFT, fill=tk.X, expand=True)

        self.lbl_wx_baro = tk.Label(
            baro_block, text="🧭 -- inHg",
            font=("Segoe UI", 9, "bold"), bg=t["card_bg"], fg=t["accent"], anchor="w"
        )
        self.lbl_wx_baro.pack(fill=tk.X)

        self.lbl_wx_baro_sub = tk.Label(
            baro_block, text="-- mb • Steady",
            font=("Segoe UI", 8), bg=t["card_bg"], fg=t["text_secondary"], anchor="w"
        )
        self.lbl_wx_baro_sub.pack(fill=tk.X)

        # Weather Sub Strip (Humidity & Dew Point | Rain | UV / Solar)
        wx_sub = tk.Frame(self.weather_card, bg=t["card_bg"])
        wx_sub.pack(fill=tk.X, pady=(2, 2))

        self.lbl_wx_humidity = tk.Label(
            wx_sub, text="Humidity: --% • Dew: --°F",
            font=("Segoe UI", 8), bg=t["card_bg"], fg=t["text_secondary"], anchor="w"
        )
        self.lbl_wx_humidity.pack(side=tk.LEFT, fill=tk.X, expand=True)

        self.lbl_wx_rain = tk.Label(
            wx_sub, text="Rain: 0.00\"/hr",
            font=("Segoe UI", 8), bg=t["card_bg"], fg=t["text_secondary"], anchor="w"
        )
        self.lbl_wx_rain.pack(side=tk.LEFT, fill=tk.X, expand=True)

        self.lbl_wx_solar = tk.Label(
            wx_sub, text="UV: 0 • Solar: 0 W/m²",
            font=("Segoe UI", 8), bg=t["card_bg"], fg=t["text_secondary"], anchor="e"
        )
        self.lbl_wx_solar.pack(side=tk.RIGHT)

        # 3-Day Harbor Forecast Strip
        self.wx_forecast_frame = tk.Frame(self.weather_card, bg=t["table_header_bg"], padx=6, pady=3)
        self.wx_forecast_frame.pack(fill=tk.X, pady=(2, 0))

        self.lbl_fc_title = tk.Label(
            self.wx_forecast_frame, text="3-DAY FORECAST:",
            font=("Segoe UI", 7, "bold"), bg=t["table_header_bg"], fg=t["accent"], anchor="w"
        )
        self.lbl_fc_title.pack(side=tk.LEFT, padx=(0, 8))

        self.fc_day_labels = []
        for d_idx in range(3):
            lbl_d = tk.Label(
                self.wx_forecast_frame, text=f"Day {d_idx+1}: --",
                font=("Segoe UI", 8), bg=t["table_header_bg"], fg=t["text_primary"], anchor="w"
            )
            lbl_d.pack(side=tk.LEFT, expand=True, fill=tk.X)
            self.fc_day_labels.append(lbl_d)

        self.wx_frames = [wx_head, wx_head_right, wx_main, temp_block, wind_block, baro_block, wx_sub, self.wx_forecast_frame]

        # Navigation & Bridges Card: Sea Bright Bridge (Clearance & Current) and Highlands Bridge (Clearance)
        self.nav_card = tk.Frame(self, bg=t["card_bg"], highlightbackground=t["card_border"], highlightthickness=1, padx=8, pady=5)
        self.nav_card.pack(fill=tk.X, padx=10, pady=(0, 3))

        # Nav Header row
        nav_head = tk.Frame(self.nav_card, bg=t["card_bg"])
        nav_head.pack(fill=tk.X, pady=(0, 2))

        self.lbl_nav_title = tk.Label(
            nav_head, text="BRIDGES & CURRENTS • SHREWSBURY NAVIGATION",
            font=("Segoe UI", 8, "bold"), bg=t["card_bg"], fg=t["accent"], anchor="w"
        )
        self.lbl_nav_title.pack(side=tk.LEFT)

        nav_head_right = tk.Frame(nav_head, bg=t["card_bg"])
        nav_head_right.pack(side=tk.RIGHT)

        curr_mode_label = "🌊 Current: API" if (self.bridge_service and self.bridge_service.current_mode == "api") else "🌊 Current: Math"
        self.btn_current_mode = tk.Button(
            nav_head_right, text=curr_mode_label, font=("Segoe UI", 7, "bold"),
            bg=t["badge_bg"], fg=t["accent_blue"], activebackground=t["accent"],
            relief=tk.FLAT, bd=0, padx=5, pady=1, cursor="hand2",
            command=self._toggle_current_mode
        )
        self.btn_current_mode.pack(side=tk.LEFT)

        # Main 3-column row:
        nav_main = tk.Frame(self.nav_card, bg=t["card_bg"])
        nav_main.pack(fill=tk.X, pady=(1, 1))

        # 1. Sea Bright Bridge Clearance Block
        sb_block = tk.Frame(nav_main, bg=t["card_bg"])
        sb_block.pack(side=tk.LEFT, fill=tk.X, expand=True)

        lbl_sb_hdr = tk.Label(
            sb_block, text="SEA BRIGHT BRIDGE",
            font=("Segoe UI", 7, "bold"), bg=t["card_bg"], fg=t["text_secondary"], anchor="w"
        )
        lbl_sb_hdr.pack(fill=tk.X)

        self.lbl_sb_clearance = tk.Label(
            sb_block, text="📐 -- ft",
            font=("Segoe UI", 10, "bold"), bg=t["card_bg"], fg=t["text_primary"], anchor="w"
        )
        self.lbl_sb_clearance.pack(fill=tk.X)

        self.lbl_sb_clearance_sub = tk.Label(
            sb_block, text="Draw • 15.0' MHW",
            font=("Segoe UI", 7), bg=t["card_bg"], fg=t["text_secondary"], anchor="w"
        )
        self.lbl_sb_clearance_sub.pack(fill=tk.X)

        # 2. Sea Bright Current Block
        curr_block = tk.Frame(nav_main, bg=t["card_bg"])
        curr_block.pack(side=tk.LEFT, fill=tk.X, expand=True)

        self.lbl_current_title = tk.Label(
            curr_block, text="SEA BRIGHT CURRENT",
            font=("Segoe UI", 7, "bold"), bg=t["card_bg"], fg=t["accent_blue"], anchor="w"
        )
        self.lbl_current_title.pack(fill=tk.X)

        self.lbl_sb_current = tk.Label(
            curr_block, text="🌊 -- kts --",
            font=("Segoe UI", 10, "bold"), bg=t["card_bg"], fg=t["accent_blue"], anchor="w"
        )
        self.lbl_sb_current.pack(fill=tk.X)

        self.lbl_sb_current_sub = tk.Label(
            curr_block, text="Slack • 0 kts",
            font=("Segoe UI", 7), bg=t["card_bg"], fg=t["text_secondary"], anchor="w"
        )
        self.lbl_sb_current_sub.pack(fill=tk.X)

        # 3. Highlands Bridge Clearance Block
        hl_block = tk.Frame(nav_main, bg=t["card_bg"])
        hl_block.pack(side=tk.LEFT, fill=tk.X, expand=True)

        lbl_hl_hdr = tk.Label(
            hl_block, text="HIGHLANDS BRIDGE",
            font=("Segoe UI", 7, "bold"), bg=t["card_bg"], fg=t["text_secondary"], anchor="w"
        )
        lbl_hl_hdr.pack(fill=tk.X)

        self.lbl_hl_clearance = tk.Label(
            hl_block, text="📐 -- ft",
            font=("Segoe UI", 10, "bold"), bg=t["card_bg"], fg=t["text_primary"], anchor="w"
        )
        self.lbl_hl_clearance.pack(fill=tk.X)

        self.lbl_hl_clearance_sub = tk.Label(
            hl_block, text="Fixed • 65.0' MHW",
            font=("Segoe UI", 7), bg=t["card_bg"], fg=t["text_secondary"], anchor="w"
        )
        self.lbl_hl_clearance_sub.pack(fill=tk.X)

        self.nav_frames = [nav_head, nav_head_right, nav_main, sb_block, curr_block, hl_block]
        self.nav_sub_headers = [lbl_sb_hdr, lbl_hl_hdr]

        # Middle Section: Tidal Wave & Water Level Visualizer Canvas
        self.wave_canvas = tk.Canvas(self, height=54, bg=t["card_bg"], highlightbackground=t["card_border"], highlightthickness=1)
        self.wave_canvas.pack(fill=tk.X, padx=10, pady=3)
        self.wave_canvas.bind("<Configure>", lambda e: self._draw_wave())

        # Upcoming Tide Table Card
        self.table_card = tk.Frame(self, bg=t["card_bg"], highlightbackground=t["card_border"], highlightthickness=1, padx=8, pady=6)
        self.table_card.pack(fill=tk.BOTH, expand=True, padx=10, pady=3)

        table_top_row = tk.Frame(self.table_card, bg=t["card_bg"])
        table_top_row.pack(fill=tk.X, pady=(0, 4))

        self.lbl_table_title = tk.Label(
            table_top_row, text="TIDE TABLE • PREDICTIONS",
            font=("Segoe UI", 9, "bold"), bg=t["card_bg"], fg=t["accent"], anchor="w"
        )
        self.lbl_table_title.pack(side=tk.LEFT)

        # Table Header
        header_frame = tk.Frame(self.table_card, bg=t["table_header_bg"])
        header_frame.pack(fill=tk.X, pady=(0, 2))

        col_configs = [
            ("EVENT", 12),
            ("DATE & TIME", 18),
            ("COUNTDOWN", 13),
            ("HEIGHT (MLLW)", 14)
        ]
        self.header_labels = []
        for title, width in col_configs:
            lbl = tk.Label(header_frame, text=title, font=("Segoe UI", 8, "bold"), bg=t["table_header_bg"], fg=t["text_secondary"], width=width, anchor="w", padx=4, pady=2)
            lbl.pack(side=tk.LEFT, fill=tk.X, expand=(title == "DATE & TIME"))
            self.header_labels.append(lbl)

        # Container for dynamic table rows (6 rows)
        self.rows_container = tk.Frame(self.table_card, bg=t["card_bg"])
        self.rows_container.pack(fill=tk.BOTH, expand=True)

        self.row_widgets = []
        for i in range(6):
            row = tk.Frame(self.rows_container, bg=t["table_row_even"], pady=2, padx=4)
            row.pack(fill=tk.X, pady=1)

            lbl_type = tk.Label(row, text="--", font=("Segoe UI", 9, "bold"), width=12, anchor="w", bg=t["table_row_even"], fg=t["text_primary"])
            lbl_type.pack(side=tk.LEFT)

            lbl_time = tk.Label(row, text="--", font=("Segoe UI", 9), anchor="w", bg=t["table_row_even"], fg=t["text_primary"])
            lbl_time.pack(side=tk.LEFT, fill=tk.X, expand=True)

            lbl_countdown = tk.Label(row, text="--", font=("Segoe UI", 9), width=13, anchor="w", bg=t["table_row_even"], fg=t["text_secondary"])
            lbl_countdown.pack(side=tk.LEFT)

            lbl_height = tk.Label(row, text="--", font=("Segoe UI", 9, "bold"), width=14, anchor="w", bg=t["table_row_even"], fg=t["text_secondary"])
            lbl_height.pack(side=tk.LEFT)

            self.row_widgets.append({
                "frame": row,
                "lbl_type": lbl_type,
                "lbl_time": lbl_time,
                "lbl_countdown": lbl_countdown,
                "lbl_height": lbl_height
            })

        # Bottom Section: Quick Calibration & Tuning Controls
        self.ctrl_card = tk.Frame(self, bg=t["card_bg"], highlightbackground=t["card_border"], highlightthickness=1, padx=10, pady=6)
        self.ctrl_card.pack(fill=tk.X, padx=10, pady=(2, 8))

        ctrl_header = tk.Frame(self.ctrl_card, bg=t["card_bg"])
        ctrl_header.pack(fill=tk.X, pady=(0, 2))
        self.lbl_ctrl_title = tk.Label(ctrl_header, text="CALIBRATION & OFFSETS", font=("Segoe UI", 8, "bold"), bg=t["card_bg"], fg=t["text_primary"])
        self.lbl_ctrl_title.pack(side=tk.LEFT)

        # Quick shift buttons
        btn_row = tk.Frame(self.ctrl_card, bg=t["card_bg"])
        btn_row.pack(fill=tk.X, pady=1)

        shifts = [("-15m", -15), ("+15m", 15), ("-1h", -60), ("+1h", 60)]
        for text, mins in shifts:
            btn = tk.Button(
                btn_row, text=text, font=("Segoe UI", 8, "bold"),
                bg=t["badge_bg"], fg=t["text_primary"], activebackground=t["accent"],
                relief=tk.FLAT, bd=0, padx=4, pady=2, cursor="hand2",
                command=lambda m=mins: self._adjust_minutes(m)
            )
            btn.pack(side=tk.LEFT, padx=1, expand=True, fill=tk.X)

        # Direct calibration row
        action_row = tk.Frame(self.ctrl_card, bg=t["card_bg"])
        action_row.pack(fill=tk.X, pady=(3, 1))

        btn_set_high = tk.Button(
            action_row, text="Set NOW as High Tide", font=("Segoe UI", 8, "bold"),
            bg=t["high_badge_bg"], fg=t["high_badge_fg"], activebackground=t["accent"],
            relief=tk.FLAT, bd=0, padx=4, pady=3, cursor="hand2",
            command=lambda: self._calibrate_now(True)
        )
        btn_set_high.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 2))

        btn_set_low = tk.Button(
            action_row, text="Set NOW as Low Tide", font=("Segoe UI", 8, "bold"),
            bg=t["low_badge_bg"], fg=t["low_badge_fg"], activebackground=t["accent"],
            relief=tk.FLAT, bd=0, padx=4, pady=3, cursor="hand2",
            command=lambda: self._calibrate_now(False)
        )
        btn_set_low.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(2, 0))

    def update_data(self):
        """Refresh digital time, upcoming tides table, NOAA status, and wave visualizer."""
        now = datetime.datetime.now()
        t = self.theme
        st_info = self.engine.current_station_info

        # Station Title and Coordinates
        self.lbl_station.config(text=self.engine.station_name)
        coords = st_info.get("coordinates", "40°20'12.7\"N 73°58'42.7\"W")
        self.lbl_station_coords.config(text=f"GPS: {coords}")
        self.lbl_station_sub.config(text=st_info.get("description", "Shrewsbury River, NJ"))

        # NOAA Live Verification Status
        noaa_id = st_info.get("noaa_id")
        if self.engine.is_noaa_live:
            self.lbl_noaa_status.config(text=f"● NOAA Live ({noaa_id})", fg="#2ECC71")
        elif noaa_id:
            self.lbl_noaa_status.config(text=f"○ NOAA Syncing ({noaa_id})", fg=t["accent"])
        else:
            self.lbl_noaa_status.config(text="● Lunar Harmonic", fg=t["accent_blue"])

        # Current Local Time
        time_formatted = now.strftime("%A, %b %d • %I:%M:%S %p")
        self.lbl_datetime.config(text=time_formatted)

        # Moon Phase
        moon = self.engine.get_moon_info(now)
        self.lbl_moon_icon.config(text=moon["icon_char"])
        self.lbl_moon_desc.config(text=f"{moon['phase_name']} ({moon['illumination']}%)")
        self.lbl_tide_type.config(text=f"{moon['tide_type']} • {moon['tide_sub']}")

        # Update Tempestwx Station 141221 Weather Metrics
        if self.weather_service:
            try:
                w = self.weather_service.metrics
                temp_f = w.get("temp_f")
                feels_f = w.get("feels_like_f")
                cond = w.get("conditions", "")
                icon = w.get("icon", "🌤")
                spd = w.get("wind_spd_kts")
                gust = w.get("wind_gust_kts")
                card = w.get("wind_cardinal", "--")
                deg = w.get("wind_dir_deg")
                p_in = w.get("pressure_inhg")
                p_mb = w.get("pressure_mb")
                trend = w.get("pressure_trend", "steady") or "steady"
                hum = w.get("humidity_pct")
                dew = w.get("dew_point_f")
                p_rate = w.get("precip_rate_in")
                p_rate_val = p_rate if p_rate is not None else 0.0
                p_today = w.get("precip_today_in")
                p_today_val = p_today if p_today is not None else 0.0
                uv = w.get("uv_index")
                uv_val = uv if uv is not None else 0
                solar = w.get("solar_radiation")
                solar_val = solar if solar is not None else 0
                is_tempest = w.get("is_tempest", False)
                is_live = w.get("is_live", False)
                st_id = getattr(self.weather_service, "station_id", 141221)

                # Status badge
                if is_tempest:
                    self.lbl_wx_source.config(text=f"● Tempest #{st_id} (Live)", fg="#2ECC71")
                elif is_live:
                    self.lbl_wx_source.config(text=f"● NOAA KBLM (Token Needed)", fg=t["accent"])
                else:
                    self.lbl_wx_source.config(text="○ Connecting...", fg=t["text_secondary"])

                # Temperature
                if temp_f is not None:
                    self.lbl_wx_temp.config(text=f"{icon} {temp_f:.1f}°F")
                    feels_str = f"Feels {feels_f:.1f}°F" if feels_f is not None else ""
                    cond_str = f" • {cond}" if cond else ""
                    self.lbl_wx_cond.config(text=f"{feels_str}{cond_str}".strip(" •"))
                else:
                    self.lbl_wx_temp.config(text="--°F")
                    self.lbl_wx_cond.config(text="Connecting...")

                # Wind
                if spd is not None:
                    self.lbl_wx_wind.config(text=f"💨 {spd:.1f} kts {card}")
                    gust_str = f"Gusts {gust:.1f} kts" if gust is not None else "No gusts"
                    deg_str = f" • {deg}°" if deg is not None else ""
                    self.lbl_wx_gust.config(text=f"{gust_str}{deg_str}")
                else:
                    self.lbl_wx_wind.config(text="💨 -- kts --")
                    self.lbl_wx_gust.config(text="Calm")

                # Barometer
                if p_in is not None:
                    trend_arrow = "↑" if trend == "rising" else ("↓" if trend == "falling" else "→")
                    self.lbl_wx_baro.config(text=f"🧭 {p_in:.2f} inHg")
                    mb_str = f"{p_mb:.1f} mb" if p_mb is not None else ""
                    self.lbl_wx_baro_sub.config(text=f"{mb_str} {trend_arrow} {trend.title()}".strip())
                else:
                    self.lbl_wx_baro.config(text="🧭 -- inHg")
                    self.lbl_wx_baro_sub.config(text="-- mb")

                # Humidity & Dew
                hum_str = f"{hum}%" if hum is not None else "--%"
                dew_str = f"{dew:.1f}°F" if dew is not None else "--°F"
                self.lbl_wx_humidity.config(text=f"Humidity: {hum_str} • Dew: {dew_str}")

                # Precipitation
                self.lbl_wx_rain.config(text=f"Rain: {p_rate_val:.2f}\"/hr ({p_today_val:.2f}\" day)")

                # Solar & UV
                self.lbl_wx_solar.config(text=f"UV: {uv_val} • Solar: {solar_val} W/m²")

                # 3-Day Forecast
                fc_list = getattr(self.weather_service, "forecast_3day", [])
                for idx, lbl in enumerate(self.fc_day_labels):
                    if idx < len(fc_list):
                        fd = fc_list[idx]
                        lbl.config(
                            text=f"{fd['day_name']} {fd['date_str']}: {fd['icon']} {fd['high_f']}° / {fd['low_f']}°F • {fd['conditions']} ({fd['precip_pct']}% rain)",
                            fg=t["text_primary"]
                        )
                    else:
                        lbl.config(text=f"Day {idx+1}: Forecast Pending...", fg=t["text_secondary"])
            except Exception:
                pass

        # Update Bridge Overhead Clearances & Sea Bright Tidal Current
        if self.bridge_service:
            try:
                curr = self.bridge_service.get_sea_bright_current(now)
                sb_cl = self.bridge_service.get_sea_bright_clearance(now)
                hl_cl = self.bridge_service.get_highlands_clearance(now)

                # 1. Sea Bright Bridge Clearance
                sb_caret = sb_cl.get("trend_caret", "")
                self.lbl_sb_clearance.config(text=f"📐 {sb_cl['clearance_str']} {sb_caret}")
                self.lbl_sb_clearance_sub.config(text=f"Draw • 15.0' MHW • {sb_cl.get('trend_desc', '')}")
                if sb_cl.get("caution", False):
                    self.lbl_sb_clearance.config(fg="#FF5964")
                else:
                    self.lbl_sb_clearance.config(fg=t["text_primary"])

                # 2. Sea Bright Current (API or Math)
                spd = curr["speed_kts"]
                arrow = curr["arrow"]
                state = curr["state"]
                dir_str = curr["direction"]
                self.lbl_sb_current.config(text=f"🌊 {spd:.1f} kts {arrow}")
                mode_tag = "API" if curr["is_api_mode"] else "Math"
                self.lbl_sb_current_sub.config(text=f"{state} ({dir_str}) • [{mode_tag}]")
                self.btn_current_mode.config(text=f"🌊 Current: {curr['method']}")

                # 3. Highlands Bridge Clearance
                hl_caret = hl_cl.get("trend_caret", "")
                self.lbl_hl_clearance.config(text=f"📐 {hl_cl['clearance_str']} {hl_caret}")
                self.lbl_hl_clearance_sub.config(text=f"Fixed • 65.0' MHW • {hl_cl.get('trend_desc', '')}")
            except Exception:
                pass

        # Upcoming tides table
        tides = self.engine.get_upcoming_tides(count=6, now=now)
        for i, row_data in enumerate(tides):
            if i >= len(self.row_widgets):
                break
            rw = self.row_widgets[i]
            is_high = row_data["is_high"]
            is_first = (i == 0)

            row_bg = t["table_row_highlight"] if is_first else (t["table_row_even"] if i % 2 == 0 else t["table_row_odd"])
            rw["frame"].config(bg=row_bg)

            if is_high:
                type_text = "▲ HIGH TIDE"
                type_fg = t["high_badge_fg"]
            else:
                type_text = "▼ LOW TIDE"
                type_fg = t["low_badge_fg"]

            rw["lbl_type"].config(text=type_text, fg=type_fg, bg=row_bg)
            rw["lbl_time"].config(text=f"{row_data['day_label']} {row_data['time_str']}", fg=t["table_text"], bg=row_bg)
            rw["lbl_countdown"].config(text=row_data["countdown_str"], fg=t["accent"] if is_first else t["text_secondary"], bg=row_bg)
            rw["lbl_height"].config(text=row_data.get("height_str", "--"), fg=t["accent"] if is_first else t["text_secondary"], bg=row_bg)

        # Draw wave visualizer
        self._draw_wave()

    def _draw_wave(self):
        """Draw smooth, anti-aliased mathematical tidal sine curve and current water level bead."""
        c = self.wave_canvas
        w = c.winfo_width()
        h = c.winfo_height()
        if w < 20 or h < 20:
            return

        c.delete("all")
        t = self.theme
        status = self.engine.get_status()
        current_angle = status["angle_deg"]
        water_pct = status["water_level_pct"]
        is_falling = status["is_falling"]

        mid_y = h / 2.0
        amp = (h - 18) / 2.0

        # Render 4x supersampled anti-aliased wave graphic
        scale = 4
        sw = max(10, int(w * scale))
        sh = max(10, int(h * scale))
        s_mid_y = mid_y * scale
        s_amp = amp * scale

        im = Image.new("RGBA", (sw, sh), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)

        # Background card color
        bg_hex = t["card_bg"]
        d.rectangle([0, 0, sw, sh], fill=bg_hex)

        # Reference grid lines (high tide & low tide dotted lines)
        s_high_y = s_mid_y - s_amp
        s_low_y = s_mid_y + s_amp
        dash_len = int(3 * scale)
        gap_len = int(4 * scale)

        for sx in range(0, sw, dash_len + gap_len):
            d.line([(sx, s_high_y), (min(sw, sx + dash_len), s_high_y)], fill=t["card_border"], width=max(1, int(scale)))
            d.line([(sx, s_low_y), (min(sw, sx + dash_len), s_low_y)], fill=t["card_border"], width=max(1, int(scale)))

        # Compute sine wave points across width
        pts = []
        steps = max(60, int(w))
        for i in range(steps + 1):
            px = (i / float(steps)) * sw
            phase = (i / float(steps)) * 2.0 * math.pi
            py = s_mid_y - s_amp * math.cos(phase)
            pts.append((px, py))

        # Fill water area under curve
        fill_poly = [(0, sh)] + pts + [(sw, sh)]
        water_color = "#152E48" if t == self.theme else "#112233"
        d.polygon(fill_poly, fill=water_color)

        # Draw anti-aliased sine wave crest
        d.line(pts, fill=t["accent_blue"], width=max(2, int(2.2 * scale)))

        # Downsample with Lanczos anti-aliasing
        final_im = im.resize((w, h), Image.Resampling.LANCZOS)
        self._wave_photo = ImageTk.PhotoImage(final_im)
        c.create_image(w / 2.0, h / 2.0, image=self._wave_photo)

        # Current water level marker bead (crisp on top of smoothed background)
        curr_ratio = current_angle / 360.0
        curr_x = curr_ratio * w
        curr_y = mid_y - amp * math.cos(math.radians(current_angle))

        marker_color = t["falling_color"] if is_falling else t["rising_color"]
        bead_r = 5.5
        c.create_oval(curr_x - bead_r, curr_y - bead_r, curr_x + bead_r, curr_y + bead_r,
                      fill=marker_color, outline=t["bezel_light"], width=1.6)

        dir_arrow = "▼" if is_falling else "▲"
        label_text = f"Water Level: {water_pct:.0f}%  {dir_arrow} {status['state']}"
        tx = max(80, min(w - 80, curr_x))
        ty = 11 if curr_y > 22 else (h - 11)
        c.create_text(tx, ty, text=label_text, font=("Segoe UI", 8, "bold"), fill=t["text_primary"])

    def _open_tempest_website(self):
        """Open official Tempestwx Station 141221 live page in default browser."""
        import webbrowser
        url = getattr(self.weather_service, "station_url", "https://tempestwx.com/station/141221/")
        webbrowser.open_new_tab(url)

    def _toggle_current_mode(self):
        """Toggle between NOAA Current API and Mathematical Tide-to-Current prediction."""
        if self.bridge_service:
            new_mode = self.bridge_service.toggle_current_mode()
            if self.engine:
                self.engine.bridge_current_mode = new_mode
                self.engine.save_settings()
            self.update_data()

    def _sync_noaa(self):
        """Trigger instant NOAA sync."""
        self.engine.sync_noaa_now()
        self.on_change_callback()

    def _adjust_minutes(self, minutes: int):
        """Shift tide calibration."""
        self.engine.adjust_reference_minutes(minutes)
        self.on_change_callback()

    def _calibrate_now(self, is_high: bool):
        """Set current moment as high or low tide."""
        state_str = "High Tide" if is_high else "Low Tide"
        if messagebox.askyesno("Calibrate Clock", f"Are you sure you want to set the current time as {state_str} for {self.engine.station_name}?"):
            self.engine.calibrate_to_now(is_high)
            self.on_change_callback()

    def _open_station_dialog(self):
        """Open station selector dialog."""
        from tide_engine import PRESET_STATIONS
        dialog = tk.Toplevel(self)
        dialog.title("Select Tide Reference Station")
        dialog.geometry("480x380")
        dialog.resizable(False, False)
        dialog.transient(self)
        dialog.grab_set()

        t = self.theme
        dialog.config(bg=t["window_bg"])

        lbl = tk.Label(dialog, text="Select Coastal Station / Reference Port:", font=("Segoe UI", 10, "bold"), bg=t["window_bg"], fg=t["text_primary"])
        lbl.pack(padx=16, pady=(16, 6), anchor="w")

        listbox_frame = tk.Frame(dialog, bg=t["window_bg"])
        listbox_frame.pack(fill=tk.BOTH, expand=True, padx=16, pady=4)

        scrollbar = tk.Scrollbar(listbox_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        stations_list = list(PRESET_STATIONS.keys())
        listbox = tk.Listbox(
            listbox_frame, yscrollcommand=scrollbar.set,
            font=("Segoe UI", 9), bg=t["card_bg"], fg=t["text_primary"],
            selectbackground=t["accent"], selectforeground="#FFFFFF",
            relief=tk.FLAT, bd=1, highlightthickness=1, highlightbackground=t["card_border"]
        )
        listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=listbox.yview)

        for s in stations_list:
            listbox.insert(tk.END, s)

        if self.engine.station_name in stations_list:
            idx = stations_list.index(self.engine.station_name)
            listbox.selection_set(idx)
            listbox.see(idx)

        btn_box = tk.Frame(dialog, bg=t["window_bg"])
        btn_box.pack(fill=tk.X, padx=16, pady=12)

        def on_apply():
            sel = listbox.curselection()
            if sel:
                st_name = stations_list[sel[0]]
                self.engine.set_station(st_name)
                self.on_change_callback()
                dialog.destroy()

        btn_ok = tk.Button(
            btn_box, text="Apply Station", font=("Segoe UI", 9, "bold"),
            bg=t["accent"], fg="#1A2530", activebackground=t["accent_hover"],
            relief=tk.FLAT, padx=14, pady=4, cursor="hand2", command=on_apply
        )
        btn_ok.pack(side=tk.RIGHT, padx=4)

        btn_cancel = tk.Button(
            btn_box, text="Cancel", font=("Segoe UI", 9),
            bg=t["card_bg"], fg=t["text_primary"],
            relief=tk.FLAT, padx=12, pady=4, cursor="hand2", command=dialog.destroy
        )
        btn_cancel.pack(side=tk.RIGHT, padx=4)
