"""
Tide Dial: Luxury marine tide clock widget.
Clean, stylish, and informative aesthetic inspired by classic marine chronometers
with Atlantis Yacht Club heraldry.
Features high-resolution anti-aliased rendering with supersampled graphics.
"""

import math
import tkinter as tk
from typing import Dict, Any, Optional
from PIL import Image, ImageDraw, ImageTk
from ayc_branding import draw_ayc_burgee


class TideDial(tk.Canvas):
    """
    Renders an authentic, stylish marine tide clock dial.
    - Top (12 o'clock): HIGH TIDE
    - Bottom (6 o'clock): LOW TIDE
    - Right (0-180 deg): FALLING / Ebb (Hours 1, 2, 3, 4, 5)
    - Left (180-360 deg): RISING / Flood (Hours 5, 4, 3, 2, 1)
    - Quarter points: HALF TIDE
    """

    def __init__(self, parent, theme_data: Dict[str, Any], size: int = 400, **kwargs):
        super().__init__(
            parent,
            width=size,
            height=size,
            bg=theme_data["window_bg"],
            highlightthickness=0,
            **kwargs
        )
        self.theme = theme_data
        self.size = size
        self.current_angle = 0.0
        self.current_status = {}
        self._dial_photo: Optional[ImageTk.PhotoImage] = None
        self._cached_dial_key: Optional[str] = None
        
        self.bind("<Configure>", self._on_resize)

    def set_theme(self, theme_data: Dict[str, Any]):
        """Update colors when user toggles themes."""
        self.theme = theme_data
        self.config(bg=self.theme["window_bg"])
        self._dial_photo = None
        self._cached_dial_key = None
        self.redraw()

    def update_tide(self, status: Dict[str, Any]):
        """Update clock hand angle and status text."""
        self.current_status = status
        self.current_angle = status.get("angle_deg", 0.0)
        self.redraw()

    def _on_resize(self, event):
        """Scale dial smoothly with window resizing."""
        new_size = min(event.width, event.height)
        if new_size > 100 and abs(new_size - self.size) > 4:
            self.size = new_size
            self._dial_photo = None
            self.redraw()

    def redraw(self):
        """Draw the refined, high-resolution anti-aliased tide clock dial."""
        self.delete("all")
        
        w = self.winfo_width()
        h = self.winfo_height()
        if w < 50 or h < 50:
            w = self.size
            h = self.size

        cx = w / 2.0
        cy = (h - 26) / 2.0
        radius = min(cx, cy) - 10

        if radius < 60:
            return

        inner_r = radius * 0.885

        # 1. High-resolution anti-aliased Dial Face (Bezel, track, arcs, and pointer)
        self._render_supersampled_dial(cx, cy, radius, inner_r, self.current_angle)

        # 2. Crisp Vector Numerals (Georgia serif numerals)
        self._draw_hour_numbers(cx, cy, inner_r)

        # 3. High Tide / Low Tide / Half Tide Cardinal Labels
        self._draw_cardinals(cx, cy, inner_r)

        # 4. Atlantis Yacht Club Insignia & Burgee
        self._draw_ayc_insignia(cx, cy, inner_r)

        # 5. Clean Status Pill Badge below dial
        self._draw_badge(cx, h - 20, w)

    def _render_supersampled_dial(self, cx: float, cy: float, radius: float, inner_r: float, angle_deg: float):
        """
        Renders the multi-tier metallic bezel, sector arcs, railway track,
        and tapered chronometer pointer hand using 4x supersampled anti-aliasing.
        Eliminates all jagged edges and sawtooth artifacts.
        """
        t = self.theme
        scale = 4
        pad = 6
        target_dim = int(radius * 2 + pad * 2)
        s_dim = target_dim * scale

        im = Image.new("RGBA", (s_dim, s_dim), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)

        s_cx = s_dim / 2.0
        s_cy = s_dim / 2.0
        s_r = radius * scale
        s_inner_r = inner_r * scale

        # --- 1. Metallic Instrument Bezel ---
        # Outer drop shadow
        d.ellipse([s_cx - s_r, s_cy - s_r + 3 * scale, s_cx + s_r, s_cy + s_r + 3 * scale], fill=t["bezel_outer"])
        # Outer bezel rim
        d.ellipse([s_cx - s_r, s_cy - s_r, s_cx + s_r, s_cy + s_r], fill=t["bezel_shadow"])
        # Polished metallic tier
        r2 = s_r * 0.965
        d.ellipse([s_cx - r2, s_cy - r2, s_cx + r2, s_cy + r2], fill=t["bezel_main"])
        # Specular light highlight
        r3 = s_r * 0.935
        d.ellipse([s_cx - r3, s_cy - r3, s_cx + r3, s_cy + r3], fill=t["bezel_light"])
        # Inner step lip
        r4 = s_r * 0.905
        d.ellipse([s_cx - r4, s_cy - r4, s_cx + r4, s_cy + r4], fill=t["bezel_shadow"])

        # Brass mounting rivets at 45° angles
        rivet_r = s_r * 0.95
        for ang in [45, 135, 225, 315]:
            rad = math.radians(ang)
            rx = s_cx + rivet_r * math.cos(rad)
            ry = s_cy + rivet_r * math.sin(rad)
            riv_w = 2.4 * scale
            d.ellipse([rx - riv_w, ry - riv_w, rx + riv_w, ry + riv_w], fill=t["bezel_outer"], outline=t["bezel_light"], width=max(1, int(scale)))

        # --- 2. Dial Face Center ---
        d.ellipse([s_cx - s_inner_r, s_cy - s_inner_r, s_cx + s_inner_r, s_cy + s_inner_r],
                  fill=t["dial_bg"], outline=t["card_border"], width=int(1.5 * scale))

        # --- 3. Ebb & Flood Sector Arcs ---
        arc_r = s_inner_r * 0.95
        # Right half: Falling / Ebb (-90° to +90° in standard PIL arc)
        d.arc([s_cx - arc_r, s_cy - arc_r, s_cx + arc_r, s_cy + arc_r],
              start=-90, end=90, fill=t["falling_color"], width=int(2.5 * scale))
        # Left half: Rising / Flood (+90° to +270° in PIL)
        d.arc([s_cx - arc_r, s_cy - arc_r, s_cx + arc_r, s_cy + arc_r],
              start=90, end=270, fill=t["rising_color"], width=int(2.5 * scale))

        # --- 4. Railway Graduation Track ---
        track_out_r = s_inner_r * 0.94
        track_in_r = s_inner_r * 0.86
        d.ellipse([s_cx - track_out_r, s_cy - track_out_r, s_cx + track_out_r, s_cy + track_out_r],
                  outline=t["dial_ticks_minor"], width=max(1, int(1.0 * scale)))
        d.ellipse([s_cx - track_in_r, s_cy - track_in_r, s_cx + track_in_r, s_cy + track_in_r],
                  outline=t["dial_ticks_minor"], width=max(1, int(1.0 * scale)))

        # 60 division marks around perimeter
        for i in range(60):
            ang_rad = math.radians(i * 6.0 - 90)
            is_hour = (i % 5 == 0)
            is_half = (i % 2.5 == 0) and not is_hour

            if is_hour:
                r_start = track_out_r
                r_end = track_in_r - (s_inner_r * 0.02)
                color = t["dial_ticks_major"]
                w_line = max(2, int(2.2 * scale))
            elif is_half:
                r_start = track_out_r
                r_end = track_in_r + (s_inner_r * 0.015)
                color = t["dial_ticks_major"]
                w_line = max(1, int(1.4 * scale))
            else:
                r_start = track_out_r
                r_end = track_out_r - (s_inner_r * 0.035)
                color = t["dial_ticks_minor"]
                w_line = max(1, int(0.9 * scale))

            x1 = s_cx + r_start * math.cos(ang_rad)
            y1 = s_cy + r_start * math.sin(ang_rad)
            x2 = s_cx + r_end * math.cos(ang_rad)
            y2 = s_cy + r_end * math.sin(ang_rad)
            d.line([(x1, y1), (x2, y2)], fill=color, width=w_line)

        # --- 5. Tapered Marine Chronometer Pointer Hand ---
        hand_rad = math.radians(angle_deg - 90.0)
        hand_len = s_inner_r * 0.86
        cos_a = math.cos(hand_rad)
        sin_a = math.sin(hand_rad)
        perp_x = -sin_a
        perp_y = cos_a

        tip_x = s_cx + hand_len * cos_a
        tip_y = s_cy + hand_len * sin_a

        flare_d = hand_len * 0.72
        flare_w = max(3.0 * scale, hand_len * 0.038)
        fl_x = s_cx + flare_d * cos_a + flare_w * perp_x
        fl_y = s_cy + flare_d * sin_a + flare_w * perp_y
        fr_x = s_cx + flare_d * cos_a - flare_w * perp_x
        fr_y = s_cy + flare_d * sin_a - flare_w * perp_y

        base_w = max(2.0 * scale, hand_len * 0.024)
        bl_x = s_cx + base_w * perp_x
        bl_y = s_cy + base_w * perp_y
        br_x = s_cx - base_w * perp_x
        br_y = s_cy - base_w * perp_y

        poly_left = [(s_cx, s_cy), (bl_x, bl_y), (fl_x, fl_y), (tip_x, tip_y)]
        poly_right = [(s_cx, s_cy), (tip_x, tip_y), (fr_x, fr_y), (br_x, br_y)]

        d.polygon(poly_left, fill=t["hand_main"])
        d.polygon(poly_right, fill=t["hand_highlight"])

        # Counterweight tail & ring
        tail_len = hand_len * 0.26
        cw_center_x = s_cx - (tail_len * 0.65) * cos_a
        cw_center_y = s_cy - (tail_len * 0.65) * sin_a
        cw_radius = max(4.0 * scale, hand_len * 0.055)

        d.ellipse([cw_center_x - cw_radius, cw_center_y - cw_radius, cw_center_x + cw_radius, cw_center_y + cw_radius], fill=t["hand_main"])
        hole_r = cw_radius * 0.48
        d.ellipse([cw_center_x - hole_r, cw_center_y - hole_r, cw_center_x + hole_r, cw_center_y + hole_r], fill=t["dial_bg"])
        d.line([(s_cx, s_cy), (s_cx - tail_len * cos_a, s_cy - tail_len * sin_a)], fill=t["hand_main"], width=int(2.2 * scale))

        # Center Brass Hub Cap
        hub_r = max(5.0 * scale, hand_len * 0.065)
        d.ellipse([s_cx - hub_r, s_cy - hub_r, s_cx + hub_r, s_cy + hub_r], fill=t["bezel_shadow"])
        hub_r2 = hub_r * 0.72
        d.ellipse([s_cx - hub_r2, s_cy - hub_r2, s_cx + hub_r2, s_cy + hub_r2], fill=t["hand_center_pin"])
        hub_r3 = hub_r * 0.32
        d.ellipse([s_cx - hub_r3, s_cy - hub_r3, s_cx + hub_r3, s_cy + hub_r3], fill=t["bezel_main"])

        # Lanczos downsampling to native screen resolution (silky smooth AA)
        final_im = im.resize((target_dim, target_dim), Image.Resampling.LANCZOS)
        self._dial_photo = ImageTk.PhotoImage(final_im)

        # Place onto canvas
        self.create_image(cx, cy, image=self._dial_photo)

    def _draw_hour_numbers(self, cx: float, cy: float, inner_r: float):
        """Draw clean, elegant lunar hour numerals (1-5 and 5-1)."""
        t = self.theme
        num_r = inner_r * 0.77
        font_num = ("Georgia", max(9, int(inner_r * 0.082)), "bold")

        # Falling side (right): Hours 1, 2, 3, 4, 5
        # (30°, 60°, 90°, 120°, 150°)
        for hr in range(1, 6):
            deg = hr * 30.0
            rad = math.radians(deg - 90)
            nx = cx + num_r * math.cos(rad)
            ny = cy + num_r * math.sin(rad)
            self.create_text(nx, ny, text=str(hr), font=font_num, fill=t["dial_text"])

        # Rising side (left): Hours 5, 4, 3, 2, 1
        # (210°, 240°, 270°, 300°, 330°)
        for idx, hr in enumerate([5, 4, 3, 2, 1]):
            deg = 210.0 + (idx * 30.0)
            rad = math.radians(deg - 90)
            nx = cx + num_r * math.cos(rad)
            ny = cy + num_r * math.sin(rad)
            self.create_text(nx, ny, text=str(hr), font=font_num, fill=t["dial_text"])

    def _draw_cardinals(self, cx: float, cy: float, inner_r: float):
        """Draw prominent, stylish cardinal markers: HIGH TIDE, LOW TIDE, HALF TIDE."""
        t = self.theme
        font_cardinal = ("Georgia", max(8, int(inner_r * 0.065)), "bold")
        font_half = ("Segoe UI", max(7, int(inner_r * 0.060)), "bold")

        # Top (12 o'clock): HIGH TIDE
        top_y = cy - inner_r * 0.70
        self.create_text(cx, top_y, text="HIGH TIDE", font=font_cardinal, fill=t["high_tide_label"])
        # Subtle red marker dot at 12 o'clock
        dot_r = max(2.5, inner_r * 0.018)
        dot_y = cy - inner_r * 0.79
        self.create_oval(cx - dot_r, dot_y - dot_r, cx + dot_r, dot_y + dot_r, fill=t["high_tide_label"], outline="")

        # Bottom (6 o'clock): LOW TIDE
        bot_y = cy + inner_r * 0.70
        self.create_text(cx, bot_y, text="LOW TIDE", font=font_cardinal, fill=t["low_tide_label"])
        # Subtle blue marker dot at 6 o'clock
        dot_bot_y = cy + inner_r * 0.79
        self.create_oval(cx - dot_r, dot_bot_y - dot_r, cx + dot_r, dot_bot_y + dot_r, fill=t["low_tide_label"], outline="")

        # 3 o'clock: HALF TIDE (Falling)
        right_x = cx + inner_r * 0.54
        self.create_text(right_x, cy, text="HALF", font=font_half, fill=t["falling_color"], justify=tk.CENTER)

        # 9 o'clock: HALF TIDE (Rising)
        left_x = cx - inner_r * 0.54
        self.create_text(left_x, cy, text="HALF", font=font_half, fill=t["rising_color"], justify=tk.CENTER)

    def _draw_ayc_insignia(self, cx: float, cy: float, inner_r: float):
        """Draw understated, prestigious Atlantis Yacht Club branding with official burgee."""
        t = self.theme

        # Move burgee up into the upper quadrant with plenty of clearance above the text
        burgee_w = 48.0
        burgee_h = 34.0
        burgee_y = (cy - inner_r * 0.47) - burgee_h / 2.0
        draw_ayc_burgee(self, cx - burgee_w / 2.0, burgee_y, burgee_w, burgee_h, prefer_image=True)

        # Clean tracked club title placed cleanly below the burgee
        font_ayc = ("Georgia", max(8, int(inner_r * 0.075)), "bold")
        font_loc = ("Segoe UI", max(6, int(inner_r * 0.055)), "normal")

        self.create_text(cx, cy - inner_r * 0.25, text="ATLANTIS YACHT CLUB", font=font_ayc, fill=t["dial_text"])
        self.create_text(cx, cy - inner_r * 0.17, text="MONMOUTH BEACH, NJ", font=font_loc, fill=t["dial_text_dim"])

        # Subtle cycle note in lower quadrant
        self.create_text(cx, cy + inner_r * 0.28, text="12h 25m TIDE GAUGE", font=font_loc, fill=t["dial_text_dim"])

    def _draw_hand(self, cx: float, cy: float, length: float, angle_deg: float):
        """Draw a slender, elegant marine pointer hand with gold center hub."""
        t = self.theme
        rad = math.radians(angle_deg - 90.0)

        cos_a = math.cos(rad)
        sin_a = math.sin(rad)
        perp_x = -sin_a
        perp_y = cos_a

        # Tip
        tip_x = cx + length * cos_a
        tip_y = cy + length * sin_a

        # Fine pointer diamond flare at 72%
        flare_d = length * 0.72
        flare_w = max(3.0, length * 0.038)
        fl_x = cx + flare_d * cos_a + flare_w * perp_x
        fl_y = cy + flare_d * sin_a + flare_w * perp_y
        fr_x = cx + flare_d * cos_a - flare_w * perp_x
        fr_y = cy + flare_d * sin_a - flare_w * perp_y

        # Slender stem
        base_w = max(2.0, length * 0.024)
        bl_x = cx + base_w * perp_x
        bl_y = cy + base_w * perp_y
        br_x = cx - base_w * perp_x
        br_y = cy - base_w * perp_y

        # Left half (main blued steel / navy)
        poly_left = [cx, cy, bl_x, bl_y, fl_x, fl_y, tip_x, tip_y]
        self.create_polygon(poly_left, fill=t["hand_main"], outline="")

        # Right half (gold / metallic ridge highlight)
        poly_right = [cx, cy, tip_x, tip_y, fr_x, fr_y, br_x, br_y]
        self.create_polygon(poly_right, fill=t["hand_highlight"], outline="")

        # Slender counterweight tail
        tail_len = length * 0.26
        cw_center_x = cx - (tail_len * 0.65) * cos_a
        cw_center_y = cy - (tail_len * 0.65) * sin_a
        cw_radius = max(4.0, length * 0.055)

        # Counterweight ring
        self.create_oval(
            cw_center_x - cw_radius, cw_center_y - cw_radius,
            cw_center_x + cw_radius, cw_center_y + cw_radius,
            fill=t["hand_main"], outline=""
        )
        hole_r = cw_radius * 0.48
        self.create_oval(
            cw_center_x - hole_r, cw_center_y - hole_r,
            cw_center_x + hole_r, cw_center_y + hole_r,
            fill=t["dial_bg"], outline=""
        )
        self.create_line(cx, cy, cx - tail_len * cos_a, cy - tail_len * sin_a, fill=t["hand_main"], width=2)

        # Center Brass Hub Cap (Refined golden jewel cap)
        hub_r = max(5.0, length * 0.065)
        self.create_oval(cx - hub_r, cy - hub_r, cx + hub_r, cy + hub_r, fill=t["bezel_shadow"], outline="")
        hub_r2 = hub_r * 0.72
        self.create_oval(cx - hub_r2, cy - hub_r2, cx + hub_r2, cy + hub_r2, fill=t["hand_center_pin"], outline="")
        hub_r3 = hub_r * 0.32
        self.create_oval(cx - hub_r3, cy - hub_r3, cx + hub_r3, cy + hub_r3, fill=t["bezel_main"], outline="")

    def _draw_badge(self, cx: float, cy: float, w: float):
        """Draw an understated, modern status pill below the dial."""
        t = self.theme
        state = self.current_status.get("state", "CALCULATING")
        countdown = self.current_status.get("countdown_str", "--")
        water_pct = self.current_status.get("water_level_pct", 50.0)

        if state == "HIGH TIDE":
            badge_text = f"HIGH TIDE SLACK WATER ({water_pct:.0f}%)"
            badge_color = t["high_badge_fg"]
            bg_color = t["high_badge_bg"]
        elif state == "LOW TIDE":
            badge_text = f"LOW TIDE SLACK WATER ({water_pct:.0f}%)"
            badge_color = t["low_badge_fg"]
            bg_color = t["low_badge_bg"]
        elif state == "FALLING":
            badge_text = f"▼ EBB • {countdown} to Low Tide ({water_pct:.0f}%)"
            badge_color = t["falling_color"]
            bg_color = t["badge_bg"]
        else: # RISING
            badge_text = f"▲ FLOOD • {countdown} to High Tide ({water_pct:.0f}%)"
            badge_color = t["rising_color"]
            bg_color = t["badge_bg"]

        bw = min(w - 24, 290)
        bh = 22
        bx1 = cx - bw / 2.0
        by1 = cy - bh / 2.0
        bx2 = cx + bw / 2.0
        by2 = cy + bh / 2.0

        self.create_rectangle(bx1, by1, bx2, by2, fill=bg_color, outline=t["card_border"], width=1)
        self.create_text(cx, cy, text=badge_text, font=("Segoe UI", 9, "bold"), fill=badge_color)
