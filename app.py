"""
Main Application: Mariner's Tide Clock & Table Desktop App.
Combines traditional analog nautical tide dial with modern tide schedule,
moon phase indicator, live water level visualizer, and station calibration.
"""

import sys
import os
import ctypes
import datetime
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog

# Enable Windows Per-Monitor High-DPI Awareness for razor-sharp text and fonts
if sys.platform == "win32":
    try:
        # PROCESS_PER_MONITOR_DPI_AWARE = 2
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
    except Exception:
        try:
            ctypes.windll.user32.SetProcessDPIAware()
        except Exception:
            pass

from theme import THEMES
from tide_engine import TideEngine, PRESET_STATIONS
from tide_dial import TideDial
from tide_table_view import TideTableView
from tempest_weather import TempestWeatherService
from bridge_service import BridgeCurrentService
from ayc_branding import AYC_INFO, get_burgee_image


class TideClockApp:
    """Top-level desktop application controller."""

    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Atlantis Yacht Club - Monmouth Beach Tide Clock & Table")
        self.root.geometry("980x680")
        self.root.minsize(900, 620)

        # Set official AYC burgee as window & taskbar icon
        icon = get_burgee_image("icon")
        if icon:
            try:
                self.root.iconphoto(False, icon)
            except Exception:
                pass

        # Initialize engine and settings
        self.engine = TideEngine()
        self.theme_name = self.engine.theme if self.engine.theme in THEMES else "ayc_navy"
        self.theme = THEMES[self.theme_name]

        # Initialize Tempestwx Weather Service for Station 141221
        self.weather_service = TempestWeatherService(
            station_id=self.engine.tempest_station_id,
            token=self.engine.tempest_token
        )
        self._weather_poll_ticks = 0

        # Initialize Bridges and Currents Service
        self.bridge_service = BridgeCurrentService(tide_engine=self.engine)
        self.bridge_service.set_current_mode(getattr(self.engine, "bridge_current_mode", "api"))

        # Audio alert state tracking (prevent repeated beeping in same peak window)
        self.last_alert_state = None

        # Build application UI
        self._apply_window_settings()
        self._build_menu()
        self._build_layout()

        # Start 1-second update cycle
        self._tick()

    def _apply_window_settings(self):
        """Configure root window background and topmost state."""
        self.root.config(bg=self.theme["window_bg"])
        self.root.attributes("-topmost", self.engine.always_on_top)

    def _build_menu(self):
        """Construct the top menu bar."""
        self.menubar = tk.Menu(self.root)
        self.root.config(menu=self.menubar)

        # File Menu
        file_menu = tk.Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label="File", menu=file_menu)

        self.topmost_var = tk.BooleanVar(value=self.engine.always_on_top)
        file_menu.add_checkbutton(label="Always on Top (Pin Window)", variable=self.topmost_var, command=self._toggle_topmost)

        self.sound_var = tk.BooleanVar(value=self.engine.sound_alert)
        file_menu.add_checkbutton(label="Sound Chime at High/Low Tide", variable=self.sound_var, command=self._toggle_sound)

        file_menu.add_separator()
        file_menu.add_command(label="Open Mini Desktop Widget Mode", command=self._launch_widget_mode)
        file_menu.add_separator()
        file_menu.add_command(label="Enter Custom High Tide Time...", command=self._open_custom_calibration)
        file_menu.add_command(label="Reset Calibration to Port Default", command=self._reset_to_preset)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)

        # Stations Menu
        stations_menu = tk.Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label="Ports & Stations", menu=stations_menu)
        for st_name in PRESET_STATIONS.keys():
            stations_menu.add_command(label=st_name, command=lambda name=st_name: self._change_station(name))

        # Weather Menu
        wx_menu = tk.Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label="Weather", menu=wx_menu)
        wx_menu.add_command(label="Refresh Tempest & Coastal Weather Now", command=self._refresh_weather)
        wx_menu.add_separator()
        wx_menu.add_command(label="Open Tempestwx Live Station 141221 in Browser...", command=self._open_tempest_website)

        # Bridges & Currents Menu
        bridge_menu = tk.Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label="Bridges & Currents", menu=bridge_menu)
        self.current_mode_var = tk.StringVar(value=self.bridge_service.current_mode)
        bridge_menu.add_radiobutton(
            label="Sea Bright Current: NOAA CO-OPS API (ACT3886)",
            variable=self.current_mode_var, value="api",
            command=lambda: self._set_current_mode("api")
        )
        bridge_menu.add_radiobutton(
            label="Sea Bright Current: Hydraulic Tide-to-Current Math",
            variable=self.current_mode_var, value="math",
            command=lambda: self._set_current_mode("math")
        )
        bridge_menu.add_separator()
        bridge_menu.add_command(label="Sea Bright Bridge Clearances & Specs...", command=self._show_sea_bright_bridge_info)
        bridge_menu.add_command(label="Highlands Bridge Clearances & Specs...", command=self._show_highlands_bridge_info)
        bridge_menu.add_separator()
        bridge_menu.add_command(label="Refresh Bridges & Currents Now", command=self._refresh_bridges)

        # Themes Menu
        theme_menu = tk.Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label="Appearance", menu=theme_menu)
        self.theme_var = tk.StringVar(value=self.theme_name)
        theme_menu.add_radiobutton(label="AYC Regatta Navy (Clubhouse Official)", variable=self.theme_var, value="ayc_navy", command=lambda: self._set_theme("ayc_navy"))
        theme_menu.add_radiobutton(label="AYC Quarterdeck (Midnight Fleet)", variable=self.theme_var, value="ayc_quarterdeck", command=lambda: self._set_theme("ayc_quarterdeck"))
        theme_menu.add_radiobutton(label="AYC Teak & Brass (Classic)", variable=self.theme_var, value="classic", command=lambda: self._set_theme("classic"))

        # Help Menu
        help_menu = tk.Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label="AYC & Help", menu=help_menu)
        help_menu.add_command(label="About Atlantis Yacht Club", command=self._show_about_ayc)
        help_menu.add_command(label="How Tide Clocks Work", command=self._show_tide_guide)

    def _build_layout(self):
        """Construct the split pane layout: Clock Dial on left, Table on right."""
        self.main_container = tk.Frame(self.root, bg=self.theme["window_bg"])
        self.main_container.pack(fill=tk.BOTH, expand=True)

        # Left Column: Analog Tide Clock Dial
        self.left_frame = tk.Frame(self.main_container, bg=self.theme["window_bg"], padx=8, pady=8)
        self.left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Dial Header (clean, understated)
        dial_title = tk.Label(
            self.left_frame, text="TIDE CHRONOMETER",
            font=("Segoe UI", 9, "bold"), bg=self.theme["window_bg"], fg=self.theme["text_secondary"]
        )
        dial_title.pack(anchor="center", pady=(4, 2))

        self.tide_dial = TideDial(self.left_frame, self.theme, size=380)
        self.tide_dial.pack(fill=tk.BOTH, expand=True)

        # Right Column: Upcoming Tide Table & Control Dashboard
        self.right_frame = tk.Frame(self.main_container, bg=self.theme["window_bg"], width=430)
        self.right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        self.right_frame.pack_propagate(False)

        self.table_view = TideTableView(
            self.right_frame, self.engine, self.theme,
            on_change_callback=self._on_calibration_changed,
            weather_service=self.weather_service,
            bridge_service=self.bridge_service
        )
        self.table_view.pack(fill=tk.BOTH, expand=True)

    def _tick(self):
        """Main timer tick triggered once per second."""
        now = datetime.datetime.now()
        status = self.engine.get_status(now)

        # Periodic background weather and bridge poll every 60 seconds
        self._weather_poll_ticks += 1
        if self._weather_poll_ticks >= 60:
            self._weather_poll_ticks = 0
            self.weather_service.refresh_weather_async()
            self.bridge_service.refresh_async()

        # Update dial widget
        self.tide_dial.update_tide(status)

        # Update table and wave dashboard
        self.table_view.update_data()

        # Handle slack water audio chime
        self._check_sound_alert(status)

        # Schedule next tick in 1000ms
        self.root.after(1000, self._tick)

    def _check_sound_alert(self, status):
        """Play soft chime when transitioning into high or low slack water."""
        if not self.engine.sound_alert:
            return

        current_state = status["state"]
        if current_state in ("HIGH TIDE", "LOW TIDE") and self.last_alert_state != current_state:
            self.last_alert_state = current_state
            try:
                self.root.bell()
            except Exception:
                pass
        elif current_state not in ("HIGH TIDE", "LOW TIDE"):
            self.last_alert_state = None

    def _on_calibration_changed(self):
        """Callback when user modifies calibration or station."""
        status = self.engine.get_status()
        self.tide_dial.update_tide(status)
        self.table_view.update_data()

    def _change_station(self, station_name: str):
        """Switch station from menu."""
        self.engine.set_station(station_name)
        self._on_calibration_changed()

    def _set_theme(self, theme_key: str):
        """Switch appearance theme."""
        if theme_key in THEMES:
            self.theme_name = theme_key
            self.theme = THEMES[theme_key]
            self.engine.theme = theme_key
            self.engine.save_settings()

            self._apply_window_settings()
            self.main_container.config(bg=self.theme["window_bg"])
            self.left_frame.config(bg=self.theme["window_bg"])
            self.right_frame.config(bg=self.theme["window_bg"])

            self.tide_dial.set_theme(self.theme)
            self.table_view.set_theme(self.theme)

    def _toggle_topmost(self):
        """Toggle window pin to top."""
        val = self.topmost_var.get()
        self.engine.always_on_top = val
        self.root.attributes("-topmost", val)
        self.engine.save_settings()

    def _toggle_sound(self):
        """Toggle sound chime."""
        val = self.sound_var.get()
        self.engine.sound_alert = val
        self.engine.save_settings()

    def _launch_widget_mode(self):
        """Launch the standalone mini desktop widget and minimize full app."""
        import subprocess
        if getattr(sys, "frozen", False):
            app_dir = os.path.dirname(os.path.abspath(sys.executable))
            exe_path = os.path.join(app_dir, "Atlantis_Yacht_Club_Tide_Widget.exe")
            if os.path.exists(exe_path):
                subprocess.Popen([exe_path])
                self.root.iconify()
                return
        script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "widget.py")
        subprocess.Popen([sys.executable, script_path])
        self.root.iconify()

    def _reset_to_preset(self):
        """Reset calibration back to preset default."""
        self.engine.set_station(self.engine.station_name)
        self._on_calibration_changed()
        messagebox.showinfo("Calibration Reset", f"Reset calibration to default reference for {self.engine.station_name}.")

    def _open_custom_calibration(self):
        """Prompt user for exact known High Tide time."""
        curr = self.engine.ref_high_tide.strftime("%Y-%m-%d %H:%M")
        val = simpledialog.askstring(
            "Custom High Tide Calibration",
            f"Enter known High Tide date and time (YYYY-MM-DD HH:MM):\n\nCurrent reference: {curr}",
            initialvalue=curr,
            parent=self.root
        )
        if val:
            try:
                new_dt = datetime.datetime.strptime(val.strip(), "%Y-%m-%d %H:%M")
                self.engine.set_reference_high(new_dt)
                self._on_calibration_changed()
                messagebox.showinfo("Success", f"Reference High Tide calibrated to:\n{new_dt.strftime('%A, %b %d %Y at %I:%M %p')}")
            except ValueError:
                messagebox.showerror("Invalid Format", "Please enter the date and time in format:\nYYYY-MM-DD HH:MM\nExample: 2026-10-22 08:30")

    def _show_tide_guide(self):
        """Display educational guide explaining tide clocks and tidal astronomy."""
        guide = (
            "How Traditional Tide Clocks Work\n"
            "=================================\n\n"
            "1. The Lunar Tidal Day:\n"
            "   Because the Moon orbits the Earth in the same direction the Earth rotates,\n"
            "   it takes the Moon 24 hours, 50 minutes, and 28 seconds to return to the same\n"
            "   overhead position. This is called a 'lunar day'.\n\n"
            "2. Semidiurnal Tides (12h 25m Cycle):\n"
            "   Most Atlantic and worldwide coastal waters experience two high tides and two low\n"
            "   tides each lunar day. The time between high tides averages exactly:\n"
            "   12 hours, 25 minutes, and 14 seconds.\n\n"
            "3. Reading the Tide Clock Dial:\n"
            "   - 12 o'clock (Top): HIGH TIDE\n"
            "   - 6 o'clock (Bottom): LOW TIDE\n"
            "   - Right half (0° to 180°): FALLING (Ebb Tide, counting 1 to 5 hours until low tide)\n"
            "   - Left half (180° to 360°): RISING (Flood Tide, counting 5 to 1 hours until high tide)\n"
            "   - 3 and 9 o'clock: HALF TIDE (slack water halfway between high and low)\n\n"
            "4. Spring vs. Neap Tides:\n"
            "   - Spring Tides occur near New Moon and Full Moon when the Sun and Moon pull together,\n"
            "     producing the highest high tides and strongest tidal currents.\n"
            "   - Neap Tides occur during Quarter Moons, producing moderate tides.\n\n"
            "5. Calibration:\n"
            "   Tide clocks are calibrated by setting the clock hand to 'HIGH TIDE' at the exact moment\n"
            "   of high tide on the day of a full or new moon for maximum long-term accuracy."
        )
        messagebox.showinfo("How Tide Clocks Work", guide, parent=self.root)

    def _refresh_weather(self):
        """Trigger immediate background fetch of weather metrics."""
        self.weather_service.refresh_weather_async()
        self.table_view.update_data()

    def _open_tempest_website(self):
        """Open official Tempestwx Station 141221 live web dashboard in default browser."""
        import webbrowser
        webbrowser.open_new_tab("https://tempestwx.com/station/141221/")

    def _set_current_mode(self, mode: str):
        """Switch Sea Bright current calculation mode (API vs Math)."""
        self.bridge_service.set_current_mode(mode)
        self.engine.bridge_current_mode = mode
        self.engine.save_settings()
        self.current_mode_var.set(mode)
        self.table_view.update_data()

    def _refresh_bridges(self):
        """Force immediate refresh of bridge currents and clearances."""
        self.bridge_service.refresh_async()
        self.table_view.update_data()

    def _show_sea_bright_bridge_info(self):
        """Display navigational specs and clearance for Sea Bright Bridge."""
        now = datetime.datetime.now()
        sb_cl = self.bridge_service.get_sea_bright_clearance(now)
        curr = self.bridge_service.get_sea_bright_current(now)
        msg = (
            "Sea Bright Bridge (Rumson-Sea Bright Bridge)\n"
            "===========================================\n\n"
            f"• Location: Rumson Road (CR 520) over Shrewsbury River\n"
            f"• GPS: 40°21'36\"N 73°58'30\"W (Approx 1.4 nm north of AYC)\n"
            f"• Structure: Double-leaf Bascule Drawbridge\n\n"
            f"CLEARANCES (Closed Span):\n"
            f"• Current Estimated Clearance: {sb_cl['clearance_str']} ({sb_cl['trend_desc']})\n"
            f"• Charted Clearance at MHW: 15.0 ft\n"
            f"• Clearance at Mean Low Water (MLW): 18.5 ft\n"
            f"• Open Position: Unlimited vertical clearance\n\n"
            f"TIDAL CURRENTS (Station ACT3886):\n"
            f"• Current Velocity: {curr['speed_kts']:.1f} kts ({curr['state']} toward {curr['direction']})\n"
            f"• Active Model: {curr['method']} (API: {curr['api_speed_kts']:.1f} kts | Math: {curr['math_speed_kts']:.1f} kts)\n"
            f"• Next Slack: {curr['next_slack_str']}\n"
            f"• Next Peak: {curr['next_peak_str']}\n\n"
            f"VHF & OPERATIONS:\n"
            f"• Bridge Tender: VHF Channel 13 / (732) 842-1718\n"
            f"• Sound Signal: One prolonged blast followed by one short blast"
        )
        messagebox.showinfo("Sea Bright Bridge Navigational Specs", msg, parent=self.root)

    def _show_highlands_bridge_info(self):
        """Display navigational specs and clearance for Highlands Bridge."""
        now = datetime.datetime.now()
        hl_cl = self.bridge_service.get_highlands_clearance(now)
        msg = (
            "Highlands Bridge (Route 36)\n"
            "===========================\n\n"
            f"• Location: Route 36 connecting Highlands and Sea Bright / Sandy Hook\n"
            f"• Waterway: Shrewsbury River / Sandy Hook Bay Entrance Channel\n"
            f"• Structure: Fixed High-Level Concrete Span\n\n"
            f"CLEARANCES:\n"
            f"• Current Estimated Clearance: {hl_cl['clearance_str']} ({hl_cl['trend_desc']})\n"
            f"• Charted Clearance at MHW: 65.0 ft\n"
            f"• Clearance at Mean Low Water (MLW): 69.2 ft\n"
            f"• Horizontal Clearance: 130.0 ft\n\n"
            f"NOTES FOR MARINERS:\n"
            f"• Vertical clearances are referenced to Mean High Water (MHW).\n"
            f"• During extreme spring high tides or easterly storm surges, overhead\n"
            f"  clearance can drop below the 65.0 ft charted baseline.\n"
            f"• Vessel operators with tall masts must check tide levels before transit."
        )
        messagebox.showinfo("Highlands Bridge Navigational Specs", msg, parent=self.root)

    def _show_about_ayc(self):
        """Show information regarding Atlantis Yacht Club and the app."""
        msg = (
            "Atlantis Yacht Club Tide Table Clock\n"
            "====================================\n\n"
            "• Club: Atlantis Yacht Club (AYC)\n"
            "• Established: 1961\n"
            "• Address: 66 River Avenue, Monmouth Beach, NJ 07750\n"
            "• Waterway: Shrewsbury River & Atlantic Coastal Waters\n"
            "• GPS Coordinates: 40°20'12.7\"N 73°58'42.7\"W\n"
            "• Primary NOAA Station: 8531804 (Sea Bright / Shrewsbury River)\n"
            "• Weather Station: Tempestwx #141221 (AYC Clubhouse)\n"
            "• Website: www.atlantisyachtclub.org\n\n"
            "Club Burgee:\n"
            "The official AYC burgee features the letter 'A' tipped on its\n"
            "side against traditional red, white, and blue, representing the\n"
            "bow of an Atlantis cruising yacht heading forward.\n\n"
            "Tidal Predictions, Weather & Navigation:\n"
            "Synchronized live with NOAA CO-OPS REST API for high-precision\n"
            "water heights and slack water predictions for AYC slips and docks,\n"
            "real-time meteorological conditions from Tempestwx Station 141221,\n"
            "and dynamic clearance and tidal current speeds under the Sea Bright\n"
            "Bridge (ACT3886) and Highlands Bridge (8531712)."
        )
        messagebox.showinfo("About Atlantis Yacht Club", msg, parent=self.root)


def main():
    root = tk.Tk()
    app = TideClockApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
