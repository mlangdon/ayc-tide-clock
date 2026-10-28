"""
Atlantis Yacht Club (AYC) Branding & Graphics Module
Official information, colors, vector burgee, and image loader for:
Atlantis Yacht Club
66 River Avenue, Monmouth Beach, NJ 07750
Established 1961 • atlantisyachtclub.org
Coordinates: 40°20'12.7"N 73°58'42.7"W
"""

import os
import sys
import math
import tkinter as tk
from typing import Dict, Any, Optional

def _get_base_dir() -> str:
    """Returns directory containing asset files, supporting both frozen exe and script."""
    if hasattr(sys, "_MEIPASS"):
        return sys._MEIPASS
    return os.path.dirname(os.path.abspath(__file__))

_BASE_DIR = _get_base_dir()
BURGEE_IMAGE_PATH = os.path.join(_BASE_DIR, "ayc_burgee.png")
BURGEE_MEDIUM_PATH = os.path.join(_BASE_DIR, "ayc_burgee_medium.png")
BURGEE_SMALL_PATH = os.path.join(_BASE_DIR, "ayc_burgee_small.png")
BURGEE_ICON_PATH = os.path.join(_BASE_DIR, "ayc_burgee_icon.png")

AYC_INFO = {
    "name": "Atlantis Yacht Club",
    "short_name": "AYC",
    "tagline": "Private Boating & Cruising Club • Est. 1961",
    "address": "66 River Avenue, Monmouth Beach, NJ 07750",
    "waterway": "Shrewsbury River & Atlantic Coastal Waters",
    "coordinates": "40°20'12.7\"N 73°58'42.7\"W",
    "noaa_station": "8531804 (Sea Bright / Shrewsbury River, NJ)",
    "website": "www.atlantisyachtclub.org",
    "established": 1961
}

# Image cache to prevent garbage collection in Tkinter
_IMAGE_CACHE: Dict[str, tk.PhotoImage] = {}


def get_burgee_image(size: str = "medium") -> Optional[tk.PhotoImage]:
    """
    Returns a cached Tkinter PhotoImage of the official high-resolution Atlantis Yacht Club burgee.
    - 'icon': 48 x 48 (title bar / taskbar)
    - 'medium': 52 x 36 (clock dial face)
    - 'small': 44 x 31 (dashboard header card)
    - 'full': 1016 x 717 (master high-res)
    """
    global _IMAGE_CACHE
    if size in _IMAGE_CACHE:
        return _IMAGE_CACHE[size]

    path_map = {
        "icon": BURGEE_ICON_PATH,
        "medium": BURGEE_MEDIUM_PATH,
        "small": BURGEE_SMALL_PATH,
        "full": BURGEE_IMAGE_PATH
    }

    target_path = path_map.get(size, BURGEE_MEDIUM_PATH)

    if os.path.exists(target_path):
        try:
            img = tk.PhotoImage(file=target_path)
            _IMAGE_CACHE[size] = img
            return img
        except Exception:
            pass

    # Fallback to master if specific file missing
    if os.path.exists(BURGEE_IMAGE_PATH):
        try:
            full_img = tk.PhotoImage(file=BURGEE_IMAGE_PATH)
            _IMAGE_CACHE["full"] = full_img
            _IMAGE_CACHE["medium"] = full_img.subsample(20, 20)
            _IMAGE_CACHE["small"] = full_img.subsample(24, 24)
            _IMAGE_CACHE["icon"] = full_img.subsample(22, 22)
            return _IMAGE_CACHE.get(size, _IMAGE_CACHE["medium"])
        except Exception:
            pass

    return None


def draw_ayc_burgee(canvas: tk.Canvas, x: float, y: float, w: float, h: float, with_mast: bool = False, prefer_image: bool = True):
    """
    Renders the official Atlantis Yacht Club burgee.
    - Uses the high-resolution, anti-aliased image asset when available.
    - Otherwise renders high-precision vector graphics matching the exact geometry:
      Red chevron border (>), inner white line, vertical white crossbar,
      and royal navy blue fields.
    """
    if prefer_image:
        if w <= 46 or h <= 33:
            img = get_burgee_image("small")
        elif w <= 70 or h <= 50:
            img = get_burgee_image("medium")
        else:
            img = get_burgee_image("full")

        if img is not None:
            canvas.create_image(x + w / 2.0, y + h / 2.0, image=img)
            return

    # Vector fallback matching exact uploaded burgee heraldry:
    # Outer legs: Red chevron pointing right
    # Inner: White outline, Navy Blue field, and Vertical White bar (forming letter 'A' on its side)
    hx = x
    top_y = y
    bot_y = y + h
    fly_x = x + w
    fly_y = y + h / 2.0

    # Red chevron border
    red_thick = max(3.0, h * 0.16)
    canvas.create_line(hx, top_y + red_thick / 2.0, fly_x, fly_y, fill="#ED1C24", width=red_thick, capstyle=tk.PROJECTING)
    canvas.create_line(hx, bot_y - red_thick / 2.0, fly_x, fly_y, fill="#ED1C24", width=red_thick, capstyle=tk.PROJECTING)

    # White inner stripe
    white_thick = max(1.5, h * 0.07)
    white_inset = red_thick * 0.8
    canvas.create_line(hx, top_y + white_inset, fly_x - white_inset * 1.5, fly_y, fill="#FFFFFF", width=white_thick)
    canvas.create_line(hx, bot_y - white_inset, fly_x - white_inset * 1.5, fly_y, fill="#FFFFFF", width=white_thick)

    # Blue interior field
    # Left trapezoid (from hoist to crossbar)
    bar_x = hx + w * 0.42
    bar_w = max(2.5, w * 0.08)

    inner_top_y1 = top_y + white_inset + white_thick
    inner_bot_y1 = bot_y - white_inset - white_thick
    ratio_bar = (bar_x - hx) / max(1.0, (fly_x - hx))
    bar_top_y = inner_top_y1 + (fly_y - inner_top_y1) * ratio_bar
    bar_bot_y = inner_bot_y1 + (fly_y - inner_bot_y1) * ratio_bar

    # Draw left blue trapezoid
    poly_left_blue = [hx, inner_top_y1, bar_x, bar_top_y, bar_x, bar_bot_y, hx, inner_bot_y1]
    canvas.create_polygon(poly_left_blue, fill="#000080", outline="")

    # Draw vertical white crossbar
    canvas.create_line(bar_x + bar_w / 2.0, bar_top_y, bar_x + bar_w / 2.0, bar_bot_y, fill="#FFFFFF", width=bar_w)

    # Draw right blue triangle (from crossbar to apex)
    right_blue_start_x = bar_x + bar_w
    ratio_r = (right_blue_start_x - hx) / max(1.0, (fly_x - hx))
    r_top_y = inner_top_y1 + (fly_y - inner_top_y1) * ratio_r
    r_bot_y = inner_bot_y1 + (fly_y - inner_bot_y1) * ratio_r
    tip_inner_x = fly_x - white_inset * 2.0

    poly_right_blue = [right_blue_start_x, r_top_y, tip_inner_x, fly_y, right_blue_start_x, r_bot_y]
    canvas.create_polygon(poly_right_blue, fill="#000080", outline="")
