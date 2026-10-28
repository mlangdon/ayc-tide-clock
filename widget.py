"""
Atlantis Yacht Club Tide Clock - Windows Desktop Widget.
A floating, borderless desktop gadget with transparent circular cutout,
drag-and-drop placement, live NOAA tides, and Tempestwx Station 141221 weather.
"""

import sys
import os
import math
import ctypes
import subprocess
import datetime
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Dict, Any, Optional

# Enable Windows Per-Monitor High-DPI Awareness for razor-sharp text and fonts
if sys.platform == "win32":
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
    except Exception:
        try:
            ctypes.windll.user32.SetProcessDPIAware()
        except Exception:
            pass

from theme import THEMES
from tide_engine import TideEngine, PRESET_STATIONS
from tide_dial import TideDial
from tempest_weather import TempestWeatherService
from bridge_service import BridgeCurrentService
from ayc_branding import AYC_INFO, get_burgee_image, draw_ayc_burgee

TRANS_COLOR = "#010101"  # Windows transparent color key


class TideClockWidget:
    """Floating Windows Desktop Widget for Atlantis Yacht Club Tide Clock."""

    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("AYC Tide Widget")
        self.root.overrideredirect(True)

        # Transparency on Windows
        try:
            self.root.config(bg=TRANS_COLOR)
            self.root.attributes("-transparentcolor", TRANS_COLOR)
        except Exception:
            pass

        # Set taskbar / window icon
        icon = get_burgee_image("icon")
        if icon:
            try:
                self.root.iconphoto(False, icon)
            except Exception:
                pass

        # Engine & Services
        self.engine = TideEngine()
        self.theme_name = self.engine.theme if self.engine.theme in THEMES else "ayc_navy"
        self.theme = THEMES[self.theme_name]

        self.weather_service = TempestWeatherService(
            station_id=self.engine.tempest_station_id,
            token=self.engine.tempest_token
        )
        self._weather_poll_ticks = 0

        # Initialize Bridges and Currents Service
        self.bridge_service = BridgeCurrentService(tide_engine=self.engine)
        self.bridge_service.set_current_mode(getattr(self.engine, "bridge_current_mode", "api"))

        # Window state
        self.mode = self.engine.widget_mode if self.engine.widget_mode in ("circular", "hud") else "circular"
        self.alpha = getattr(self.engine, "widget_alpha", 0.95)
        self.topmost = getattr(self.engine, "widget_topmost", True)
        self.locked = getattr(self.engine, "widget_locked", False)

        try:
            self.root.attributes("-alpha", self.alpha)
            self.root.attributes("-topmost", self.topmost)
        except Exception:
            pass

        # Drag state
        self._drag_start_x = 0
        self._drag_start_y = 0

        # Setup initial layout
        self._build_widget()
        self._restore_position()
        self._setup_bindings()

        # Start 1-second update cycle
        self._tick()

    def _build_widget(self):
        """Construct the widget canvas and controls based on current mode."""
        # Clean existing widgets
        for child in self.root.winfo_children():
            child.destroy()

        t = self.theme

        if self.mode == "circular":
            self.width = 300
            self.height = 330
            self.root.geometry(f"{self.width}x{self.height}")

            self.canvas = tk.Canvas(
                self.root, width=self.width, height=self.height,
                bg=TRANS_COLOR, highlightthickness=0
            )
            self.canvas.pack(fill=tk.BOTH, expand=True)

            # Circular dial component inside canvas
            self.dial_comp = TideDial(self.canvas, self.theme, size=280)
            self.dial_comp.place(x=10, y=8, width=280, height=310)

        else:  # "hud" mode - Compact Dockside Card
            self.width = 490
            self.height = 265
            self.root.geometry(f"{self.width}x{self.height}")

            # Main Card Frame
            self.card = tk.Frame(
                self.root, bg=t["card_bg"],
                highlightbackground=t["card_border"], highlightthickness=1.5
            )
            self.card.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)

            # Left side: Dial
            self.left_box = tk.Frame(self.card, bg=t["card_bg"], width=200)
            self.left_box.pack(side=tk.LEFT, fill=tk.BOTH, expand=False, padx=(4, 0), pady=4)

            self.dial_comp = TideDial(self.left_box, self.theme, size=190)
            self.dial_comp.pack(fill=tk.BOTH, expand=True)

            # Right side: Tide schedule & Weather HUD
            self.right_box = tk.Frame(self.card, bg=t["card_bg"], padx=8, pady=6)
            self.right_box.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

            # Header row with mini burgee and club title
            header_row = tk.Frame(self.right_box, bg=t["card_bg"])
            header_row.pack(fill=tk.X, pady=(0, 2))

            self.burgee_canvas = tk.Canvas(header_row, width=28, height=20, bg=t["card_bg"], highlightthickness=0)
            self.burgee_canvas.pack(side=tk.LEFT, padx=(0, 6))
            draw_ayc_burgee(self.burgee_canvas, 0, 0, 28, 20, prefer_image=True)

            title_box = tk.Frame(header_row, bg=t["card_bg"])
            title_box.pack(side=tk.LEFT, fill=tk.X, expand=True)

            lbl_title = tk.Label(
                title_box, text="ATLANTIS YACHT CLUB",
                font=("Georgia", 9, "bold"), bg=t["card_bg"], fg=t["accent"], anchor="w"
            )
            lbl_title.pack(fill=tk.X)

            lbl_sub = tk.Label(
                title_box, text="Monmouth Beach, NJ • 40°20'12.7\"N",
                font=("Segoe UI", 6, "bold"), bg=t["card_bg"], fg=t["text_secondary"], anchor="w"
            )
            lbl_sub.pack(fill=tk.X)

            # Close / Min controls on top right
            ctrl_box = tk.Frame(header_row, bg=t["card_bg"])
            ctrl_box.pack(side=tk.RIGHT)

            btn_switch = tk.Button(
                ctrl_box, text="⭕", font=("Segoe UI", 7),
                bg=t["badge_bg"], fg=t["text_secondary"], activebackground=t["accent"],
                relief=tk.FLAT, bd=0, padx=4, pady=0, cursor="hand2",
                command=self._toggle_mode
            )
            btn_switch.pack(side=tk.LEFT, padx=(0, 2))

            btn_close = tk.Button(
                ctrl_box, text="✕", font=("Segoe UI", 7, "bold"),
                bg=t["badge_bg"], fg=t["text_secondary"], activebackground="#C8102E", activeforeground="#FFFFFF",
                relief=tk.FLAT, bd=0, padx=4, pady=0, cursor="hand2",
                command=self.root.quit
            )
            btn_close.pack(side=tk.LEFT)

            # Divider
            div1 = tk.Frame(self.right_box, bg=t["card_border"], height=1)
            div1.pack(fill=tk.X, pady=(2, 4))

            # Upcoming Tide Info
            self.lbl_hud_next_tide = tk.Label(
                self.right_box, text="Next Tide: Updating...",
                font=("Segoe UI", 9, "bold"), bg=t["card_bg"], fg=t["accent"], anchor="w"
            )
            self.lbl_hud_next_tide.pack(fill=tk.X)

            self.lbl_hud_countdown = tk.Label(
                self.right_box, text="Countdown: --",
                font=("Segoe UI", 8), bg=t["card_bg"], fg=t["text_primary"], anchor="w"
            )
            self.lbl_hud_countdown.pack(fill=tk.X)

            # Divider
            div2 = tk.Frame(self.right_box, bg=t["card_border"], height=1)
            div2.pack(fill=tk.X, pady=(3, 3))

            # Tempest Station 141221 Weather Strip
            wx_header = tk.Frame(self.right_box, bg=t["card_bg"])
            wx_header.pack(fill=tk.X)

            self.lbl_hud_wx_title = tk.Label(
                wx_header, text="TEMPEST #141221",
                font=("Segoe UI", 7, "bold"), bg=t["card_bg"], fg=t["accent_blue"], anchor="w"
            )
            self.lbl_hud_wx_title.pack(side=tk.LEFT)

            self.lbl_hud_wx_badge = tk.Label(
                wx_header, text="● Live",
                font=("Segoe UI", 6, "bold"), bg=t["card_bg"], fg="#2ECC71", anchor="e"
            )
            self.lbl_hud_wx_badge.pack(side=tk.RIGHT)

            self.lbl_hud_weather = tk.Label(
                self.right_box, text="--°F • -- kts • -- inHg",
                font=("Segoe UI", 8, "bold"), bg=t["card_bg"], fg=t["text_primary"], anchor="w"
            )
            self.lbl_hud_weather.pack(fill=tk.X, pady=(1, 0))

            self.lbl_hud_weather_sub = tk.Label(
                self.right_box, text="Humidity: --% • Rain: 0.00\"",
                font=("Segoe UI", 7), bg=t["card_bg"], fg=t["text_secondary"], anchor="w"
            )
            self.lbl_hud_weather_sub.pack(fill=tk.X)

            # Divider
            div3 = tk.Frame(self.right_box, bg=t["card_border"], height=1)
            div3.pack(fill=tk.X, pady=(3, 3))

            # Bridge Clearances & Tidal Current
            self.lbl_hud_bridges = tk.Label(
                self.right_box, text="SB Bridge: --' • Highlands: --'",
                font=("Segoe UI", 7, "bold"), bg=t["card_bg"], fg=t["accent"], anchor="w"
            )
            self.lbl_hud_bridges.pack(fill=tk.X)

            self.lbl_hud_current = tk.Label(
                self.right_box, text="SB Current: -- kts",
                font=("Segoe UI", 7), bg=t["card_bg"], fg=t["accent_blue"], anchor="w"
            )
            self.lbl_hud_current.pack(fill=tk.X)

    def _setup_bindings(self):
        """Bind drag, right-click menu, and double-click events across all elements."""
        self._bind_recursive(self.root)

    def _bind_recursive(self, widget):
        """Recursively attach mouse events to widget and its children."""
        widget.bind("<ButtonPress-1>", self._on_start_drag, add="+")
        widget.bind("<B1-Motion>", self._on_drag_motion, add="+")
        widget.bind("<ButtonRelease-1>", self._on_end_drag, add="+")
        widget.bind("<Button-3>", self._show_context_menu, add="+")
        widget.bind("<Double-Button-1>", self._on_double_click, add="+")

        for child in widget.winfo_children():
            self._bind_recursive(child)

    def _on_start_drag(self, event):
        if self.locked:
            return
        self._drag_start_x = event.x_root
        self._drag_start_y = event.y_root

    def _on_drag_motion(self, event):
        if self.locked:
            return
        dx = event.x_root - self._drag_start_x
        dy = event.y_root - self._drag_start_y
        new_x = self.root.winfo_x() + dx
        new_y = self.root.winfo_y() + dy
        self.root.geometry(f"+{new_x}+{new_y}")
        self._drag_start_x = event.x_root
        self._drag_start_y = event.y_root

    def _on_end_drag(self, event):
        if self.locked:
            return
        self.engine.widget_x = self.root.winfo_x()
        self.engine.widget_y = self.root.winfo_y()
        self.engine.save_settings()

    def _restore_position(self):
        """Restore last saved desktop position or default to top-right screen corner."""
        self.root.update_idletasks()
        scr_w = self.root.winfo_screenwidth()
        scr_h = self.root.winfo_screenheight()

        if self.engine.widget_x is not None and self.engine.widget_y is not None:
            x = max(10, min(scr_w - self.width - 10, self.engine.widget_x))
            y = max(10, min(scr_h - self.height - 10, self.engine.widget_y))
        else:
            # Default to top-right corner of main monitor
            x = scr_w - self.width - 30
            y = 40

        self.root.geometry(f"+{x}+{y}")

    def _show_context_menu(self, event):
        """Pop up desktop widget context menu."""
        menu = tk.Menu(self.root, tearoff=0)

        # Mode submenu
        mode_menu = tk.Menu(menu, tearoff=0)
        menu.add_cascade(label="Widget Mode", menu=mode_menu)
        mode_menu.add_command(
            label="✓ Circular Chronometer Gauge" if self.mode == "circular" else "  Circular Chronometer Gauge",
            command=lambda: self._set_mode("circular")
        )
        mode_menu.add_command(
            label="✓ Dockside Weather HUD Card" if self.mode == "hud" else "  Dockside Weather HUD Card",
            command=lambda: self._set_mode("hud")
        )

        menu.add_separator()

        # Lock position
        lock_label = "✓ Lock Position on Desktop" if self.locked else "Lock Position on Desktop"
        menu.add_command(label=lock_label, command=self._toggle_lock)

        # Always on top
        top_label = "✓ Always on Top" if self.topmost else "Always on Top"
        menu.add_command(label=top_label, command=self._toggle_topmost)

        # Opacity submenu
        alpha_menu = tk.Menu(menu, tearoff=0)
        menu.add_cascade(label="Widget Transparency", menu=alpha_menu)
        for pct, val in [("100% Solid", 1.0), ("95% Frosted", 0.95), ("85% Translucent", 0.85), ("75% Transparent", 0.75)]:
            prefix = "✓ " if abs(self.alpha - val) < 0.03 else "  "
            alpha_menu.add_command(
                label=f"{prefix}{pct}",
                command=lambda v=val: self._set_alpha(v)
            )

        # Appearance Theme submenu
        theme_menu = tk.Menu(menu, tearoff=0)
        menu.add_cascade(label="Theme Palette", menu=theme_menu)
        for key in ["ayc_navy", "ayc_quarterdeck", "classic"]:
            prefix = "✓ " if self.theme_name == key else "  "
            theme_menu.add_command(
                label=f"{prefix}{THEMES[key]['name']}",
                command=lambda k=key: self._set_theme(k)
            )

        # Current prediction mode submenu
        curr_menu = tk.Menu(menu, tearoff=0)
        menu.add_cascade(label="Sea Bright Current Model", menu=curr_menu)
        curr_is_api = (self.bridge_service.current_mode == "api")
        curr_menu.add_command(
            label="✓ NOAA CO-OPS API (ACT3886)" if curr_is_api else "  NOAA CO-OPS API (ACT3886)",
            command=lambda: self._set_current_mode("api")
        )
        curr_menu.add_command(
            label="✓ Hydraulic Tide Math Model" if not curr_is_api else "  Hydraulic Tide Math Model",
            command=lambda: self._set_current_mode("math")
        )

        menu.add_separator()
        menu.add_command(label="Refresh Data Now", command=self._refresh_weather)
        menu.add_command(label="Open Full Tide Clock & Dashboard...", command=self._launch_full_app)
        menu.add_separator()
        menu.add_command(label="Close Widget", command=self.root.quit)

        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            menu.grab_release()

    def _toggle_mode(self):
        new_mode = "hud" if self.mode == "circular" else "circular"
        self._set_mode(new_mode)

    def _set_mode(self, mode_str: str):
        if self.mode != mode_str:
            self.mode = mode_str
            self.engine.widget_mode = mode_str
            self.engine.save_settings()
            self._build_widget()
            self._setup_bindings()
            self.redraw()

    def _toggle_lock(self):
        self.locked = not self.locked
        self.engine.widget_locked = self.locked
        self.engine.save_settings()

    def _toggle_topmost(self):
        self.topmost = not self.topmost
        self.engine.widget_topmost = self.topmost
        self.root.attributes("-topmost", self.topmost)
        self.engine.save_settings()

    def _set_alpha(self, val: float):
        self.alpha = val
        self.engine.widget_alpha = val
        self.root.attributes("-alpha", val)
        self.engine.save_settings()

    def _set_theme(self, theme_key: str):
        if theme_key in THEMES:
            self.theme_name = theme_key
            self.theme = THEMES[theme_key]
            self.engine.theme = theme_key
            self.engine.save_settings()
            self._build_widget()
            self._setup_bindings()
            self.redraw()

    def _refresh_weather(self):
        self.weather_service.refresh_weather_async()
        self._update_data()

    def _on_double_click(self, event):
        """Double clicking widget launches the full desktop application."""
        self._launch_full_app()

    def _launch_full_app(self):
        """Launch the standalone full Tide Clock application."""
        import sys
        if getattr(sys, "frozen", False):
            app_dir = os.path.dirname(os.path.abspath(sys.executable))
            exe_path = os.path.join(app_dir, "Atlantis_Yacht_Club_Tide_Clock.exe")
            if os.path.exists(exe_path):
                subprocess.Popen([exe_path])
                return
        # Run python app.py as fallback
        script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "app.py")
        subprocess.Popen([sys.executable, script_path])

    def _tick(self):
        """1-second timer tick."""
        now = datetime.datetime.now()
        status = self.engine.get_status(now)

        # Update dial
        if hasattr(self, "dial_comp"):
            self.dial_comp.update_tide(status)

        # Update HUD if in card mode
        self._update_data(status)

        # Periodic weather refresh every 60 seconds
        self._weather_poll_ticks += 1
        if self._weather_poll_ticks >= 60:
            self._weather_poll_ticks = 0
            self.weather_service.refresh_weather_async()

        self.root.after(1000, self._tick)

    def redraw(self):
        now = datetime.datetime.now()
        status = self.engine.get_status(now)
        if hasattr(self, "dial_comp"):
            self.dial_comp.update_tide(status)
        self._update_data(status)

    def _update_data(self, status: Optional[Dict[str, Any]] = None):
        """Refresh HUD labels when in card mode."""
        if self.mode != "hud":
            return

        now = datetime.datetime.now()
        if status is None:
            status = self.engine.get_status(now)

        t = self.theme
        tides = self.engine.get_upcoming_tides(count=2, now=now)
        if tides:
            next_t = tides[0]
            type_str = "▲ HIGH TIDE" if next_t["is_high"] else "▼ LOW TIDE"
            color = t["high_badge_fg"] if next_t["is_high"] else t["low_badge_fg"]
            ht_str = f" ({next_t.get('height_str', '')})" if next_t.get('height_str') else ""
            self.lbl_hud_next_tide.config(
                text=f"{type_str}: {next_t['time_str']}{ht_str}",
                fg=color
            )
            self.lbl_hud_countdown.config(
                text=f"Countdown: {next_t['countdown_str']} • {status['state_desc']}"
            )

        # Weather
        if self.weather_service:
            try:
                w = self.weather_service.metrics
                temp_f = w.get("temp_f")
                icon = w.get("icon", "🌤")
                spd = w.get("wind_spd_kts")
                card = w.get("wind_cardinal", "--")
                p_in = w.get("pressure_inhg")
                hum = w.get("humidity_pct")
                p_today = w.get("precip_today_in") or 0.0
                is_tempest = w.get("is_tempest", False)

                if is_tempest:
                    self.lbl_hud_wx_badge.config(text="● Tempest 141221", fg="#2ECC71")
                else:
                    self.lbl_hud_wx_badge.config(text="● NOAA Coastal", fg=t["accent"])

                temp_str = f"{icon} {temp_f:.1f}°F" if temp_f is not None else "--°F"
                wind_str = f"💨 {spd:.1f} kts {card}" if spd is not None else "-- kts"
                baro_str = f"🧭 {p_in:.2f} inHg" if p_in is not None else "-- inHg"
                self.lbl_hud_weather.config(text=f"{temp_str}  •  {wind_str}  •  {baro_str}")

                fc_list = getattr(self.weather_service, "forecast_3day", [])
                fc_str = ""
                if fc_list:
                    d0 = fc_list[0]
                    d1 = fc_list[1] if len(fc_list) > 1 else None
                    fc_parts = [f"{d0['day_name']}: {d0['high_f']}/{d0['low_f']}°"]
                    if d1:
                        fc_parts.append(f"{d1['day_name']}: {d1['high_f']}/{d1['low_f']}°")
                    fc_str = " • 3D: " + ", ".join(fc_parts)

                hum_str = f"{hum}%" if hum is not None else "--%"
                self.lbl_hud_weather_sub.config(text=f"Humidity: {hum_str} • Rain: {p_today:.2f}\"{fc_str}")
            except Exception:
                pass

        # Bridges & Sea Bright Current
        if hasattr(self, "lbl_hud_bridges") and self.bridge_service:
            try:
                curr = self.bridge_service.get_sea_bright_current(now)
                sb_cl = self.bridge_service.get_sea_bright_clearance(now)
                hl_cl = self.bridge_service.get_highlands_clearance(now)

                sb_caret = sb_cl.get("trend_caret", "")
                hl_caret = hl_cl.get("trend_caret", "")
                self.lbl_hud_bridges.config(
                    text=f"SB Bridge: {sb_cl['clearance_str']} {sb_caret}  •  Highlands: {hl_cl['clearance_str']} {hl_caret}"
                )
                self.lbl_hud_current.config(
                    text=f"SB Current: {curr['speed_kts']:.1f} kts {curr['arrow']} {curr['state']} ({curr['direction']}) • [{curr['method']}]"
                )
            except Exception:
                pass

    def _set_current_mode(self, mode: str):
        if self.bridge_service:
            self.bridge_service.set_current_mode(mode)
            self.engine.bridge_current_mode = mode
            self.engine.save_settings()
            self.redraw()


def main():
    root = tk.Tk()
    widget = TideClockWidget(root)
    root.mainloop()


if __name__ == "__main__":
    main()
