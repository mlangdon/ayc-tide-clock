# Atlantis Yacht Club — Tide Table Clock & Predictor

An authentic, fully functional Windows desktop tide clock and tidal prediction table application custom-branded for the **Atlantis Yacht Club** ([atlantisyachtclub.org](https://www.atlantisyachtclub.org)), located in Monmouth Beach, New Jersey.

---

## ⚓ Atlantis Yacht Club Identity

- **Club**: Atlantis Yacht Club (AYC)
- **Founded**: 1961 by a cruising group of yachtsmen
- **Clubhouse & Slips**: 66 River Avenue, Monmouth Beach, NJ 07750
- **Waterway**: Shrewsbury River & Atlantic Coastal Waters
- **Coordinates**: 40°20'12.7"N 73°58'42.7"W
- **Official Burgee**: Features the iconic letter **"A" tipped over on its side** (resembling a yacht's bow cutting through water) in **Regatta Red, Marine White, and Yacht Club Navy Blue**.
- **Official Colors**: AYC Deep Navy (`#081426` / `#0B2044`), Regatta Red (`#C8102E`), Marine White (`#FFFFFF`), and Signal Gold (`#D4AF37`).
- **Official NOAA Tide Station**: **8531804 (Sea Bright / Shrewsbury River, NJ)**

---

## ✨ Application Features

1. **Luxury Marine Chronometer Dial**:
   - **Chronometer Railway Track**: Dual-ring precision railway track with lunar hour graduations and fine fraction divisions.
   - **Understated Cardinal Markers**: Clean `HIGH TIDE` and `LOW TIDE` markers flanked by subtle color-coded pinnacle/trough pips.
   - **Clear Hour Progression**: Classic tidal hour numbers (1 to 5 for Ebb, 5 to 1 for Flood) with single-word `HALF` at the 3 and 9 o'clock positions.
   - **Slender Marine Pointer Hand**: Finely tapered blued-steel needle hand with gold ridge accent and teardrop counterweight.
   - **Official AYC Heraldry**: Centered Atlantis Yacht Club burgee insignia with clean tracked typography.
   - **Floating Status Pill**: Modern minimalist capsule under the dial displaying real-time Ebb/Flood status, time-to-peak countdown, and water level percentage.

2. **Official NOAA Live Tide Predictions**:
   - Synchronized live with **NOAA Station 8531804** (Sea Bright / Shrewsbury River) right at AYC slips and docks.
   - Displays water level heights in **Feet MLLW** (e.g. `+3.3 ft MLLW` High, `+0.6 ft MLLW` Low).
   - Instant **"Sync NOAA"** button for on-demand refreshes.
   - Graceful fallback to local lunar harmonic calculations when offline.

3. **Tempestwx Harbor Weather & Marine Metrics (Station 141221)**:
   - Synchronized with **WeatherFlow / Tempestwx Station #141221** located directly at the Atlantis Yacht Club clubhouse.
   - **Real-Time Meteorological Metrics**:
     - **Temperature & Feels Like**: e.g. `51.8°F (Feels 50°F)` with live sky conditions icon.
     - **Wind Speed, Gusts & Bearing**: Marine wind in knots (`kts`) with 16-point cardinal compass direction and degrees (e.g. `10.0 kts NW • Gusts 14 kts`).
     - **Barometric Pressure & Tendency**: High-precision altimeter in inches of mercury (`inHg`) and millibars (`mb`) with live pressure trend arrows (`↑`, `↓`, `→`).
     - **Humidity & Dew Point**: Relative humidity percentage and dew point temperature.
     - **Precipitation & UV / Solar**: Hourly rain rates, daily accumulation totals, UV index, and solar irradiance (`W/m²`).
   - **Dual-Mode Connectivity**:
     - *Direct Tempest Access*: Users can input their Tempest Personal Access Token via **Weather > Tempestwx Station Settings...** or the `⚙ Token` button.
     - *Seamless Live Coastal Fallback*: When no token is configured or when offline, the app seamlessly pulls live observations from NOAA / NWS Station `KBLM` (Monmouth County) so marine data is always populated out of the box.

4. **Bridges & Navigational Channels (Sea Bright & Highlands Bridges)**:
   - **Sea Bright Bridge Current Speed (CR 520 / Rumson-Sea Bright)**:
     - Real-time tidal current velocity (knots) and flow direction (Flood `185° S` into river towards AYC / Ebb `005° N` out towards Sandy Hook Bay).
     - **Dual-Model Implementation**:
       - *NOAA CO-OPS API*: Streams live harmonic current predictions from NOAA Station `ACT3886` (*Seabright Bridge, Shrewsbury River*).
       - *Hydraulic Tide-to-Current Math*: Continuous physical hydrodynamic model based on the tidal volume flux (\( v = K \cdot \frac{dh}{dt} \)), momentum phase lag, and astronomical spring/neap scaling.
       - One-click toggle button on the navigation card to switch seamlessly between models.
     - Displays time and countdown to the next Slack Water or Peak current.
   - **Sea Bright Bridge Overhead Clearance**:
     - Live vertical clearance under the bascule draw span based on instantaneous water level (\(\text{Clearance} = 15.0' + (3.64' - h(t))\)).
     - Charted clearance: `15.0 ft at MHW` (Closed) • `18.5 ft at MLW` (Closed) • Unlimited when opened.
     - Headroom trend indicator (`▲` increasing headroom during ebb / `▼` decreasing during flood) and low clearance alert.
   - **Highlands Bridge Overhead Clearance (Route 36)**:
     - Live vertical clearance under the fixed high-level span connecting Highlands and Sandy Hook (\(\text{Clearance} = 65.0' + (4.41' - h_{\text{HL}}(t))\)).
     - Charted clearance: `65.0 ft at MHW` • `69.2 ft at MLW` (Fixed).
     - Live reference to NOAA Station `8531712` (Highlands, NJ).

5. **Sinusoidal Wave & Water Level Gauge**:
   - Visual sine-curve wave monitor depicting current water height percentage for navigating river slips and channels.
   - Real-time indicator bead tracking ebb and flood progress.

6. **Moon Phase & Spring/Neap Tide Calculator**:
   - Calculates astronomical lunar age and illumination percentage.
   - Identifies **Spring Tides** (maximum tidal range during New/Full moon) vs **Neap Tides** (minimum tidal range during Quarter moons).

7. **AYC Appearance Themes**:
   - **AYC Regatta Navy (Clubhouse Official)**: Deep navy blue with gold and crimson accents.
   - **AYC Quarterdeck (Midnight Fleet)**: Deep midnight naval dark mode.
   - **AYC Teak & Brass (Classic)**: Aged yacht deck parchment and polished brass.
   - Quick shift buttons (`-15m`, `+15m`, `-1h`, `+1h`).
   - One-click `"Set NOW as High Tide"` and `"Set NOW as Low Tide"`.
   - Exact custom timestamp calibration entry.

8. **Windows Desktop Conveniences**:
   - **Always on Top (Pin Window)** option.
   - **Slack Water Chime**: Optional gentle double-beep chime when reaching High or Low tide peak.
   - Two color themes: **Classic Brass & Parchment** and **Midnight Marine (Dark Mode)**.
   - Automatically saves all preferences and calibration to `tide_settings.json`.

---

## 🚀 How to Run & Deployment Options

### Deployment Option 1: Standalone Desktop Widget (Windows Desktop Integrated)
Double-click:
`Atlantis_Yacht_Club_Tide_Widget.exe`  *(or run `python widget.py`)*

- **True Circular Transparency**: Floats directly on your desktop wallpaper with frameless circular brass bezel cutouts.
- **Drag Anywhere**: Click and drag from anywhere on the dial to position it anywhere across multiple monitors.
- **Two Integrated Modes**:
  - **Circular Chronometer Gauge**: Minimalist, floating round marine chronometer with live blued hand and AYC burgee.
  - **Dockside Weather HUD Card**: Compact card format showing the dial plus next high/low countdown and live Tempest Station 141221 weather.
- **Right-Click Context Menu**:
  - Switch between Circular Gauge & Dockside HUD Card modes.
  - **Lock Position on Desktop**: Pin in place to prevent accidental dragging.
  - **Always on Top**: Float over other windows or keep on desktop.
  - **Adjust Transparency**: 100%, 95% (Frosted glass), 85%, or 75%.
  - Switch AYC Theme Palettes (Regatta Navy, Quarterdeck, Teak & Brass).
- **Double-Click**: Instantly launches the full Tide Clock & Table application.
- Remembers its exact desktop coordinates `(x, y)` automatically.

---

### Deployment Option 2: Full Desktop Application & Prediction Dashboard
Double-click:
`Atlantis_Yacht_Club_Tide_Clock.exe`  *(or run `python app.py`)*
- Complete dual-pane nautical dashboard: 380px marine chronometer dial on left, interactive NOAA prediction schedule table, water level sine wave visualizer, calibration controls, 3-day forecast, and Tempestwx Station 141221 weather card on right.

---

### Deployment Option 3: Embeddable JavaScript Web Component
A standalone, zero-dependency Web Component is available in the `web/` folder (`web/ayc-tide-clock.js`):
- Encapsulated with **Shadow DOM** to prevent CSS conflicts with host websites.
- Canvas-based Analog Tide Chronometer dial & Water Level visualizer.
- Live NOAA harmonic tide predictions and Tempest Station 141221 weather with 3-day forecast.
- Live bridge vertical clearances & Sea Bright current velocity.

#### Embedding in HTML:
```html
<!-- Include the Web Component Script -->
<script src="https://<your-username>.github.io/<your-repo>/web/ayc-tide-clock.js" defer></script>

<!-- Place the widget anywhere on your website -->
<ayc-tide-clock></ayc-tide-clock>
```

---

## 🧭 How to Calibrate to Your Local Beach or Port

1. Look up today's high tide time for your local station on NOAA or any local tide chart.
2. In the app:
   - Click **File > Enter Custom High Tide Time...**
   - Type in the date and time (e.g., `2026-10-22 08:30`).
   - Or, when high tide occurs at your beach, simply click the `"Set NOW as High Tide"` button!
3. Your tide clock is now calibrated and will track local high and low tides continuously.
