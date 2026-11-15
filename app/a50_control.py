"""
A50 Control - an open-source replacement for ASTRO Command Center (ASTRO A50 Gen 4).

Dark/light UI built with CustomTkinter: icon rail, headset view with selectable colorways (original
drawing) or your own photo, EQ curve with draggable points, microphone, mix, maintenance, settings.
If CustomTkinter is missing, the classic UI is started instead.

Close ASTRO Command Center while using this app. USE AT YOUR OWN RISK.
Not affiliated with ASTRO Gaming or Logitech. No ASTRO/Logitech images or logos are included.
"""
import glob
import profiles as prof
import mic_test
import apo
import battery
import hotkeys
import json
import math
import platform
import socket
import time
import os
import subprocess
import sys
import threading
import importlib
import tkinter as tk
import traceback
import webbrowser
from tkinter import filedialog, messagebox

FROZEN = getattr(sys, "frozen", False)  # True when running as the packaged A50 Control.exe
APP_DIR = os.path.dirname(sys.executable if FROZEN else os.path.abspath(__file__))
_LOG_DIR = os.path.join(os.environ.get("APPDATA", APP_DIR), "A50Control") if FROZEN else APP_DIR
os.makedirs(_LOG_DIR, exist_ok=True)
ERROR_LOG = os.path.join(_LOG_DIR, "a50_control_error.log")
if sys.stderr is None or sys.stdout is None:  # started with pythonw: keep errors in a file
    sys.stderr = sys.stdout = open(ERROR_LOG, "w", encoding="utf-8")

try:
    import customtkinter as ctk
except Exception:  # fall back to the plain tkinter interface
    traceback.print_exc()
    sys.stderr.flush()
    import a50_control_classic
    a50_control_classic.App().mainloop()
    sys.exit(0)

try:
    from PIL import Image, ImageDraw, ImageFont, ImageTk
except ImportError:
    Image = ImageDraw = ImageFont = ImageTk = None

try:
    import pystray  # tray icon (optional)
except Exception:
    pystray = None

from a50_device import (A50, APP_NAME, APP_VERSION, DONATE_URL, EQ_PRESETS, REPO_URL, SLIDER,
                        DeviceError, HeadsetUnavailable, acc_running, find_repair_tool)


def tool_module(name):
    """Import a50_tool / a50_update: bundled inside the .exe, or from ../tool when run from source."""
    if not FROZEN:
        tool = find_repair_tool()
        if tool and tool not in sys.path:
            sys.path.insert(0, tool)
    return importlib.import_module(name)


class _UiWriter:
    """File-like object that forwards print() output to a callback."""
    def __init__(self, cb):
        self.cb = cb

    def write(self, s):
        if s:
            self.cb(s)
        return len(s)

    def flush(self):
        pass

# ------------------------------------------------------------------ look
ACCENTS = {"Cyan": "#00B4FF", "Teal": "#2EC4B6", "Purple": "#8B5CF6",
           "Red": "#FF4D5E", "Orange": "#FF8A3D", "Green": "#3DDC97"}
OK, WARN, BAD = "#3DDC97", "#FFB347", "#FF5C5C"
PAL = {  # (light, dark)
    "bg": ("#EEF0F4", "#0B0C10"),
    "rail": ("#E4E7EC", "#07080B"),
    "card": ("#FFFFFF", "#14161C"),
    "card2": ("#F4F6F9", "#1A1D25"),     # inputs and inner panels
    "border": ("#DCE0E6", "#232733"),
    "shadow": ("#D3D8E0", "#030405"),    # drop shadow under the cards
    "hilite": ("#FFFFFF", "#262B36"),    # 1 px highlight on the top edge of the cards
    "text": ("#111318", "#E8EAEE"),
    "muted": ("#687080", "#808A9A"),
    "track": ("#E3E6EB", "#242832"),
    "hover": ("#E6E9EE", "#1F232C"),
}
COLORWAYS = {  # original drawing styles: band, cup, cushion, ring, detail
    "Drawing - black / grey": ("#2B2E33", "#24272C", "#141619", "#8A9099", "#3A3F46"),
    "Drawing - black / gold": ("#24262B", "#1E2025", "#121316", "#C9A54C", "#3A3F46"),
    "Drawing - black / blue": ("#24262B", "#1E2025", "#121316", "#2F6FDB", "#3A3F46"),
    "Drawing - black / green": ("#24262B", "#1E2025", "#121316", "#3DAA4F", "#3A3F46"),
    "Drawing - white": ("#E6E8EB", "#F1F2F4", "#3A3D42", "#B8BEC6", "#C9CDD3"),
}
GATE_NAMES = ["Streaming", "Night", "Home", "Tournament"]
MIC_EQ_NAMES = ["Preset 0", "Preset 1", "Preset 2"]
DATA_DIR = os.path.join(os.environ.get("APPDATA", os.path.expanduser("~")), "A50Control")
SETTINGS_FILE = os.path.join(DATA_DIR, "settings.json")
USER_HEADSETS = os.path.join(DATA_DIR, "headsets")
APP_HEADSETS = os.path.join(APP_DIR, "headsets")
DEFAULTS = {"appearance": "Dark", "accent": "Cyan", "colorway": "", "photo": "", "sidebar": "expanded",
            "close_to_tray": True, "low_battery": 15, "hotkeys": True}
BACKUP_DIR = os.path.join(DATA_DIR, "backups")
SINGLE_PORT = 47650  # localhost only: lets a second launch bring the running app to the front
RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"


def autostart_command():
    if FROZEN:
        return f'"{sys.executable}" --minimized'
    exe = sys.executable
    pyw = os.path.join(os.path.dirname(exe), "pythonw.exe")
    return f'"{pyw if os.path.exists(pyw) else exe}" "{os.path.abspath(__file__)}" --minimized'


def autostart_enabled():
    try:
        import winreg
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY) as k:
            winreg.QueryValueEx(k, APP_NAME)
        return True
    except Exception:
        return False


def set_autostart(on):
    import winreg
    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY, 0, winreg.KEY_SET_VALUE) as k:
        if on:
            winreg.SetValueEx(k, APP_NAME, 0, winreg.REG_SZ, autostart_command())
        else:
            try:
                winreg.DeleteValue(k, APP_NAME)
            except FileNotFoundError:
                pass


def other_instance_running():
    """If the same version of A50 Control is already running, bring it to the front and return True.
    An older/other version (or any version with --replace) is asked to quit, and this one starts."""
    replace = "--replace" in sys.argv
    try:
        with socket.create_connection(("127.0.0.1", SINGLE_PORT), timeout=0.5) as c:
            c.sendall(f"{'replace' if replace else 'hello'} {APP_VERSION}".encode())
            c.settimeout(3)
            answer = c.recv(16)
    except OSError:
        return False
    if answer == b"shown":
        return True
    for _ in range(30):  # wait up to 6 s for the old one to close
        time.sleep(0.2)
        try:
            socket.create_connection(("127.0.0.1", SINGLE_PORT), timeout=0.3).close()
        except OSError:
            return False
    return True


def headset_images():
    """Your own headset pictures (PNG, ideally with transparent background), by name.
    Kept in %APPDATA%\\A50Control\\headsets - never part of the published project.
    Pictures dropped in app\\headsets are copied there automatically."""
    import shutil
    try:
        os.makedirs(USER_HEADSETS, exist_ok=True)
        if os.path.isdir(APP_HEADSETS):
            for f in os.listdir(APP_HEADSETS):
                if f.lower().endswith(".png") and not os.path.exists(os.path.join(USER_HEADSETS, f)):
                    shutil.copy2(os.path.join(APP_HEADSETS, f), USER_HEADSETS)
    except Exception:
        pass
    found = {}
    for d in (USER_HEADSETS, APP_HEADSETS):
        if os.path.isdir(d):
            for f in sorted(os.listdir(d)):
                if f.lower().endswith(".png"):
                    found.setdefault(os.path.splitext(f)[0], os.path.join(d, f))
    return found


def load_settings():
    s = dict(DEFAULTS)
    try:
        with open(SETTINGS_FILE, encoding="utf-8") as f:
            s.update({k: v for k, v in json.load(f).items() if k in DEFAULTS})
    except Exception:
        pass
    return s


def save_settings(s):
    try:
        os.makedirs(os.path.dirname(SETTINGS_FILE), exist_ok=True)
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(s, f, indent=2)
    except Exception:
        pass


def fmt_freq(f):
    return f"{f / 1000:.1f} kHz" if f >= 1000 else f"{f} Hz"


def mix(a, b, t):
    """Blend two #rrggbb colours: t=0 -> a, t=1 -> b."""
    a, b = a.lstrip("#"), b.lstrip("#")
    ca = [int(a[i:i + 2], 16) for i in (0, 2, 4)]
    cb = [int(b[i:i + 2], 16) for i in (0, 2, 4)]
    return "#" + "".join(f"{round(x + (y - x) * t):02x}" for x, y in zip(ca, cb))


def darker(hex_color, k=0.82):
    h = hex_color.lstrip("#")
    r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
    return "#%02X%02X%02X" % (int(r * k), int(g * k), int(b * k))


def rounded_rect(c, x0, y0, x1, y1, r, **kw):
    pts = [x0 + r, y0, x1 - r, y0, x1, y0, x1, y0 + r, x1, y1 - r, x1, y1, x1 - r, y1,
           x0 + r, y1, x0, y1, x0, y1 - r, x0, y0 + r, x0, y0]
    return c.create_polygon(pts, smooth=True, **kw)


# ------------------------------------------------------------------ icons (drawn at runtime, original line style)
def make_icon(name, color, px=48):
    """Draw a line icon on a 24-unit grid with supersampling."""
    S = 8                      # supersampling
    U = px * S / 24            # 24-unit grid
    im = Image.new("RGBA", (int(24 * U), int(24 * U)), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    w = max(1, int(1.9 * U))
    def P(*pts): return [(x * U, y * U) for x, y in zip(pts[::2], pts[1::2])]
    def B(x0, y0, x1, y1): return [x0 * U, y0 * U, x1 * U, y1 * U]
    def line(*pts): d.line(P(*pts), fill=color, width=w, joint="curve")
    def dot(x, y, r): d.ellipse(B(x - r, y - r, x + r, y + r), fill=color)
    def rrect(x0, y0, x1, y1, r, fill=False):
        d.rounded_rectangle(B(x0, y0, x1, y1), radius=r * U, outline=color, width=w, fill=color if fill else None)
    if name == "headset":
        d.arc(B(4, 3, 20, 21), 180, 360, fill=color, width=w)
        line(4, 12, 4, 14); line(20, 12, 20, 14)
        rrect(2.5, 13, 7.5, 20.5, 2); rrect(16.5, 13, 21.5, 20.5, 2)
    elif name == "eq":
        for x, y in ((6, 15), (12, 8), (18, 13)):
            line(x, 4, x, 20)
            d.ellipse(B(x - 2.4, y - 2.4, x + 2.4, y + 2.4), fill=(0, 0, 0, 0), outline=color, width=w)
            d.ellipse(B(x - 1.2, y - 1.2, x + 1.2, y + 1.2), fill=(0, 0, 0, 0))
    elif name == "mic":
        rrect(9, 3, 15, 14, 3)
        d.arc(B(5.5, 6.5, 18.5, 17.5), 0, 180, fill=color, width=w)
        line(12, 17.5, 12, 21); line(8.5, 21, 15.5, 21)
    elif name == "mix":
        line(4, 8, 19, 8); line(15, 4.5, 19, 8, 15, 11.5)
        line(20, 16, 5, 16); line(9, 12.5, 5, 16, 9, 19.5)
    elif name == "tools":
        d.ellipse(B(12.5, 3, 21, 11.5), outline=color, width=w)
        d.rectangle(B(17.2, 2, 22, 6.8), fill=(0, 0, 0, 0))
        line(14, 10, 4.5, 19.5)
        dot(4.5, 19.5, 1.6)
    elif name == "gear":
        import math
        for k in range(8):
            a = k * math.pi / 4
            line(12 + 6.2 * math.cos(a), 12 + 6.2 * math.sin(a), 12 + 9 * math.cos(a), 12 + 9 * math.sin(a))
        d.ellipse(B(5.8, 5.8, 18.2, 18.2), outline=color, width=w)
        d.ellipse(B(9.3, 9.3, 14.7, 14.7), outline=color, width=w)
    elif name == "menu":
        line(4, 7, 20, 7); line(4, 12, 20, 12); line(4, 17, 20, 17)
    elif name == "chev_l":
        line(15, 5, 8, 12, 15, 19)
    elif name == "chev_r":
        line(9, 5, 16, 12, 9, 19)
    elif name == "battery":
        rrect(2.5, 7, 19.5, 17, 2); d.rectangle(B(20, 10, 22, 14), fill=color)
    elif name == "save":
        rrect(4, 4, 20, 20, 2.5); line(8, 4, 8, 9, 15, 9, 15, 4); rrect(7.5, 13, 16.5, 20, 1)
    elif name == "game":
        d.rounded_rectangle(B(2.5, 7, 21.5, 18.5), radius=5.5 * U, outline=color, width=w)
        line(7.5, 10.5, 7.5, 15); line(5.25, 12.75, 9.75, 12.75)
        dot(15.5, 11.5, 1.3); dot(18, 14, 1.3)
    elif name == "firmware":
        rrect(6, 6, 18, 18, 2)
        for k in (9, 12, 15):
            line(k, 2.5, k, 6); line(k, 18, k, 21.5); line(2.5, k, 6, k); line(18, k, 21.5, k)
        line(12, 15.5, 12, 9); line(9.5, 11.5, 12, 9, 14.5, 11.5)
    elif name == "refresh":
        d.arc(B(4.5, 4.5, 19.5, 19.5), 30, 320, fill=color, width=w)
        line(19.6, 4, 19.6, 9, 14.6, 9)
    return im.resize((px, px), Image.LANCZOS)


def rgba(hex_color):
    h = hex_color.lstrip('#')
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4)) + (255,)


def tray_image(pct, charging, accent):
    """64x64 tray icon: battery percentage with a level bar, or a headset when there is no reading."""
    S = 64
    im = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    col = "#7C8594" if pct is None else BAD if pct <= 15 else WARN if pct <= 30 else OK if charging else accent
    d.rounded_rectangle([1, 1, S - 2, S - 2], radius=14, fill=(14, 15, 18, 255), outline=rgba(col), width=4)
    if pct is None:
        im.alpha_composite(make_icon("headset", rgba(col), 40).resize((40, 40)), (12, 12))
        return im
    d.rectangle([9, S - 15, 9 + int((S - 18) * max(0, min(100, pct)) / 100), S - 10], fill=rgba(col))
    text = str(pct)
    font = None
    if ImageFont:
        for name in ("segoeuib.ttf", "arialbd.ttf", "DejaVuSans-Bold.ttf"):
            try:
                font = ImageFont.truetype(name, 30 if len(text) < 3 else 23)
                break
            except Exception:
                pass
        if font is None:
            font = ImageFont.load_default()
    box = d.textbbox((0, 0), text, font=font)
    w, h = box[2] - box[0], box[3] - box[1]
    d.text(((S - w) / 2 - box[0], (S - 16 - h) / 2 - box[1] + 3), text, font=font, fill=(255, 255, 255, 255))
    return im


# ------------------------------------------------------------------ custom widgets
class ShadowCard(ctk.CTkFrame):
    """A card with a soft drop shadow (bottom/right) and a highlight on its top edge.
    It is created inside a wrapper frame; pack()/grid() place the wrapper, so pages use it like a normal frame."""

    def __init__(self, master, **kw):
        self._wrap = ctk.CTkFrame(master, fg_color=PAL["shadow"], corner_radius=15)
        super().__init__(self._wrap, fg_color=PAL["card"], border_color=PAL["border"], border_width=1,
                         corner_radius=14, **kw)
        ctk.CTkFrame.pack(self, fill="both", expand=True, padx=(0, 2), pady=(0, 3))
        # plain tk frame: CustomTkinter widgets don't accept width/height in place()
        dark = ctk.get_appearance_mode() == "Dark"
        hl = tk.Frame(self, height=1, bd=0, highlightthickness=0, bg=PAL["hilite"][1 if dark else 0])
        hl.place(x=16, y=1, relwidth=1.0, width=-32, height=1)

    def pack(self, *a, **kw):
        return self._wrap.pack(*a, **kw)

    def grid(self, *a, **kw):
        return self._wrap.grid(*a, **kw)

    def place(self, *a, **kw):
        return self._wrap.place(*a, **kw)

    def pack_forget(self):
        return self._wrap.pack_forget()

    def grid_forget(self):
        return self._wrap.grid_forget()


class GradientLine(tk.Canvas):
    """Thin line fading from the accent colour to the background."""

    def __init__(self, master, app, height=2, **kw):
        super().__init__(master, height=height, highlightthickness=0, bd=0, bg=app.c("bg"), **kw)
        self.app, self.h = app, height
        self.bind("<Configure>", lambda e: self.redraw())

    def redraw(self):
        self.delete("all")
        w = max(self.winfo_width(), 10)
        acc, bg, steps = self.app.accent, self.app.c("bg"), 48
        for i in range(steps):
            self.create_rectangle(w * i / steps, 0, w * (i + 1) / steps + 1, self.h, outline="",
                                  fill=mix(acc, bg, i / (steps - 1)))


class HeadsetView(tk.Canvas):
    """Original headset drawing (colorways) or the user's own photo."""

    def __init__(self, master, app, **kw):
        super().__init__(master, highlightthickness=0, bd=0, **kw)
        self.app = app
        self._img = None
        self.bind("<Configure>", lambda e: self.redraw())

    def _glow(self, w, h):
        """Soft radial light behind the headset (concentric ovals, no image library needed)."""
        bg, acc = self.app.c("card"), self.app.accent
        def mix(a, b, t):
            a, b = a.lstrip("#"), b.lstrip("#")
            return "#%02X%02X%02X" % tuple(int(int(a[i:i + 2], 16) * (1 - t) + int(b[i:i + 2], 16) * t) for i in (0, 2, 4))
        top = mix(bg, acc, 0.22 if self.app.dark else 0.12)
        steps = 28
        rx, ry = w * 0.46, h * 0.46
        for k in range(steps, 0, -1):
            t = k / steps
            self.create_oval(w / 2 - rx * t, h / 2 - ry * t, w / 2 + rx * t, h / 2 + ry * t,
                             fill=mix(top, bg, t ** 1.6), outline="")

    def _picture(self, path, w, h):
        box_w, box_h = w * 0.86, h * 0.9
        if Image:
            im = Image.open(path).convert("RGBA")
            k = min(box_w / im.width, box_h / im.height)
            im = im.resize((max(1, int(im.width * k)), max(1, int(im.height * k))), Image.LANCZOS)
            self._img = ImageTk.PhotoImage(im)
        else:
            img = tk.PhotoImage(file=path)
            k = max(1, math.ceil(max(img.width() / box_w, img.height() / box_h)))
            self._img = img.subsample(k) if k > 1 else img
        self.create_image(w / 2, h / 2, image=self._img)

    def redraw(self):
        self.delete("all")
        w, h = max(self.winfo_width(), 50), max(self.winfo_height(), 50)
        self.configure(bg=self.app.c("card"))
        self._glow(w, h)
        choice = self.app.settings.get("colorway", "")
        candidates = []
        if self.app.settings.get("photo"):
            candidates.append(self.app.settings["photo"])
        imgs = self.app.headsets
        if choice in imgs:
            candidates.append(imgs[choice])
        elif not choice and imgs:
            candidates.append(next(iter(imgs.values())))
        for path in candidates:
            if os.path.exists(path):
                try:
                    self._picture(path, w, h)
                    return
                except Exception:
                    pass
        band, cup, cush, ring, detail = COLORWAYS.get(choice, COLORWAYS["Drawing - black / grey"])
        s = min(w / 260, h / 240)
        ox, oy = w / 2 - 130 * s, h / 2 - 118 * s

        def P(x, y):
            return ox + x * s, oy + y * s

        self.create_arc(*P(52, 22), *P(208, 200), start=10, extent=160, style="arc", outline=band, width=16 * s)
        self.create_arc(*P(60, 30), *P(200, 192), start=14, extent=152, style="arc", outline=ring, width=2 * s)
        self.create_line(*P(40, 168), *P(22, 196), *P(56, 214), *P(90, 206), smooth=True, fill=band,
                         width=6 * s, capstyle="round")
        self.create_oval(*P(84, 199), *P(97, 212), fill=ring, outline="")
        for x in (30, 172):
            rounded_rect(self, *P(x, 104), *P(x + 58, 196), 24 * s, fill=cup, outline=detail, width=2)
            rounded_rect(self, *P(x + 9, 118), *P(x + 49, 182), 16 * s, fill=cush, outline="")
            self.create_oval(*P(x + 17, 132), *P(x + 41, 168), outline=ring, width=3 * s)
            self.create_line(*P(x + 29, 104), *P(x + 29, 92), fill=band, width=8 * s, capstyle="round")


class EQCurve(tk.Canvas):
    """EQ as a smooth curve with draggable points: 5 bands, -7..+7 dB by default."""

    def __init__(self, master, app, on_change, bands=5, rng=7, freqs=None, **kw):
        super().__init__(master, highlightthickness=0, bd=0, height=280, **kw)
        self.app, self.on_change = app, on_change
        self.n, self.rng = bands, rng
        self.gains = [0] * bands
        self.freqs = list(freqs) if freqs else [None] * bands
        self.drag = None
        self.bind("<Configure>", lambda e: self.redraw())
        self.bind("<Button-1>", self._press)
        self.bind("<B1-Motion>", self._move)
        self.bind("<ButtonRelease-1>", self._release)

    def _geom(self):
        w, h = max(self.winfo_width(), 200), max(self.winfo_height(), 120)
        left, right, top, bottom = 56, w - 30, 30, h - 40
        xs = [left + (right - left) * (i + 0.5) / self.n for i in range(self.n)]
        return w, h, left, right, top, bottom, xs

    def _y(self, g, top, bottom):
        return top + (self.rng - g) / (2 * self.rng) * (bottom - top)

    def redraw(self):
        self.delete("all")
        w, h, left, right, top, bottom, xs = self._geom()
        acc, muted, track = self.app.accent, self.app.c("muted"), self.app.c("track")
        self.configure(bg=self.app.c("card"))
        for g in (self.rng, 0, -self.rng):
            y = self._y(g, top, bottom)
            self.create_line(left, y, right, y, fill=track, dash=(4, 4) if g else ())
            self.create_text(left - 10, y, text=f"{g:+d} dB" if g else "0", anchor="e", fill=muted,
                             font=("Segoe UI", 9))
        pts = [(x, self._y(g, top, bottom)) for x, g in zip(xs, self.gains)]
        line = [left, pts[0][1]] + [c for p in pts for c in p] + [right, pts[-1][1]]
        fill = [left, bottom] + line + [right, bottom]
        self.create_polygon(fill, smooth=True, fill=darker(acc, 0.35) if self.app.dark else "#EAF6FF",
                            outline="")
        self.create_line(line, smooth=True, fill=acc, width=3)
        small = self.n > 6
        for i, (x, y) in enumerate(pts):
            r = (8 if self.drag == i else 6) if small else (9 if self.drag == i else 7)
            self.create_oval(x - r, y - r, x + r, y + r, fill=self.app.c("card"), outline=acc, width=3)
            self.create_text(x, y - 17, text=f"{self.gains[i]:+d}", fill=self.app.c("text"),
                             font=("Segoe UI", 9 if small else 10, "bold"))
            f = self.freqs[i]
            label = (f"{f // 1000}k" if small and f >= 1000 else fmt_freq(f) if not small else str(f)) if f \
                else f"Band {i + 1}"
            self.create_text(x, bottom + 22, text=label, fill=muted, font=("Segoe UI", 9))

    def set(self, gains=None, freqs=None):
        if gains:
            self.gains = [max(-self.rng, min(self.rng, int(g))) for g in gains][:self.n]
        if freqs:
            self.freqs = freqs
        self.redraw()

    def _press(self, e):
        *_, top, bottom, xs = self._geom()
        best = min(range(self.n), key=lambda i: abs(xs[i] - e.x))
        if abs(xs[best] - e.x) < max(18, min(40, (xs[1] - xs[0]) / 2 if self.n > 1 else 40)):
            self.drag = best
            self._move(e)

    def _move(self, e):
        if self.drag is None:
            return
        *_, top, bottom, xs = self._geom()
        g = round(self.rng - (e.y - top) / (bottom - top) * 2 * self.rng)
        self.gains[self.drag] = max(-self.rng, min(self.rng, g))
        self.redraw()

    def _release(self, e):
        if self.drag is not None:
            self.drag = None
            self.redraw()
            self.on_change(list(self.gains))


# ------------------------------------------------------------------ app
class App(ctk.CTk):
    def __init__(self):
        self.settings = load_settings()
        self.headsets = headset_images()
        ctk.set_appearance_mode(self.settings["appearance"])
        super().__init__()
        self.title(f"{APP_NAME} {APP_VERSION}")
        ico = os.path.join(getattr(sys, "_MEIPASS", APP_DIR), "a50_control.ico")
        if os.path.exists(ico):
            try:
                self.iconbitmap(ico)
                self.after(250, lambda: self.iconbitmap(ico))  # CustomTkinter resets it shortly after start
            except tk.TclError:
                pass
        self.geometry("1100x720")
        self.minsize(980, 640)
        self.dev = None
        self.loading = False
        self._timers = {}
        self.preset_map = {}
        self.page = "Home"
        self.busy = False          # a firmware/repair job owns the device: no polling or reconnecting
        self.tray = None
        self._bat_state = "init"
        self._low_warned = False
        self._tray_note = False
        self._poll_n = 0
        self.puser = prof.load_user()
        self.blog = battery.BatteryLog()
        self._hk_prof = -1
        self._hk_mic = -1
        self.psel = None              # selected profile id on the Profiles page
        self._auto = None             # (profile id, exe) applied automatically
        self._auto_saved = None       # (preset slot, gains) to put back when the game closes
        self.tray_ok = bool(pystray and Image)   # the Settings page only needs to know it's possible
        self.hk = None
        if self.settings.get("hotkeys", True):
            self._start_hotkeys()                # before build(): Settings lists shortcuts taken by other apps
        self.build()
        self._start_tray()          # after build(): a crash while building must not leave an orphan tray icon
        self._listen_single_instance()
        if "--minimized" in sys.argv:
            self.withdraw() if self.tray else self.iconify()
        self.after(200, lambda: self.connect(quiet="--minimized" in sys.argv))
        self.after(5000, self._poll)
        self.protocol("WM_DELETE_WINDOW", self._close)

    # ---- theme helpers
    @property
    def dark(self):
        return ctk.get_appearance_mode() == "Dark"

    @property
    def accent(self):
        return ACCENTS.get(self.settings["accent"], ACCENTS["Cyan"])

    def c(self, key):
        return PAL[key][1] if self.dark else PAL[key][0]

    def card(self, master, title=None):
        f = ShadowCard(master)
        if title:
            row = ctk.CTkFrame(f, fg_color="transparent")
            row.pack(anchor="w", padx=16, pady=(14, 4))
            ctk.CTkFrame(row, width=3, height=14, corner_radius=2, fg_color=self.accent).pack(side="left", padx=(0, 8))
            ctk.CTkLabel(row, text=title.upper(), text_color=PAL["muted"],
                         font=ctk.CTkFont(size=11, weight="bold")).pack(side="left")
        return f

    def tint(self, t=0.16):
        """The accent colour blended into the card colour (selected items, chips)."""
        return mix(self.c("card"), self.accent, t)

    def btn(self, master, text, cmd, primary=False, **kw):
        kw.setdefault("height", 34)
        if primary:
            return ctk.CTkButton(master, text=text, command=cmd, fg_color=self.accent, hover_color=darker(self.accent),
                                 text_color="#0B0D10", font=ctk.CTkFont(weight="bold"), corner_radius=10,
                                 border_width=1, border_color=mix(self.accent, "#FFFFFF", 0.25), **kw)
        return ctk.CTkButton(master, text=text, command=cmd, fg_color=PAL["card2"], border_width=1,
                             border_color=PAL["border"], text_color=PAL["text"], hover_color=PAL["hover"],
                             corner_radius=10, **kw)

    def icon(self, name, active=False, size=22):
        """CTkImage for light/dark mode; accent-colored when active. None if Pillow is missing."""
        if not Image:
            return None
        key = (name, active, size, self.accent)
        cache = self.__dict__.setdefault("_icons", {})
        if key not in cache:
            if active:
                light = dark = make_icon(name, rgba(self.accent), size * 2)
            else:
                light = make_icon(name, rgba(PAL["muted"][0]), size * 2)
                dark = make_icon(name, rgba(PAL["muted"][1]), size * 2)
            cache[key] = ctk.CTkImage(light_image=light, dark_image=dark, size=(size, size))
        return cache[key]

    # ---- build / rebuild (used when theme or accent change)
    def build(self):
        for w in self.winfo_children():
            w.destroy()
        self.configure(fg_color=PAL["bg"])
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self._rail()
        main = ctk.CTkFrame(self, fg_color="transparent")
        main.grid(row=0, column=1, sticky="nsew")
        main.grid_columnconfigure(0, weight=1)
        main.grid_rowconfigure(1, weight=1)
        self._header(main)
        self.body = main
        self.pages = {}
        for name, builder in (("Home", self._page_home), ("Equalizer", self._page_eq),
                              ("Microphone", self._page_mic), ("Mix", self._page_mix),
                              ("Firmware", self._page_fw), ("Profiles", self._page_profiles),
                              ("Maintenance", self._page_tools), ("Settings", self._page_settings)):
            frame = ctk.CTkScrollableFrame(main, fg_color="transparent")
            builder(frame)
            self.pages[name] = frame
        self.show(self.page)

    NAV = (("Home", "headset"), ("Equalizer", "eq"), ("Profiles", "game"), ("Microphone", "mic"), ("Mix", "mix"),
           ("Firmware", "firmware"), ("Maintenance", "tools"))

    def _rail(self):
        expanded = self.settings.get("sidebar") == "expanded"
        rail = ctk.CTkFrame(self, width=214 if expanded else 72, corner_radius=0, fg_color=PAL["rail"])
        rail.grid(row=0, column=0, sticky="nsw")
        rail.grid_propagate(False)
        rail.pack_propagate(False)
        ctk.CTkFrame(rail, width=1, corner_radius=0, fg_color=PAL["border"]).place(relx=1.0, x=-1, y=0, relheight=1.0)
        top = ctk.CTkFrame(rail, fg_color="transparent")
        top.pack(fill="x", padx=10, pady=(14, 6))
        ctk.CTkButton(top, text="", image=self.icon("menu"), width=44, height=40, corner_radius=10,
                      fg_color="transparent", hover_color=PAL["hover"],
                      command=self._toggle_sidebar).pack(side="left")
        if expanded:
            brand = ctk.CTkFrame(top, fg_color="transparent")
            brand.pack(side="left", padx=4)
            ctk.CTkLabel(brand, text="A50 Control", font=ctk.CTkFont(size=15, weight="bold"),
                         text_color=PAL["text"]).pack(anchor="w")
            ctk.CTkLabel(brand, text=f"v{APP_VERSION} · open source", font=ctk.CTkFont(size=10),
                         text_color=PAL["muted"]).pack(anchor="w")
        ctk.CTkFrame(rail, height=1, corner_radius=0, fg_color=PAL["border"]).pack(fill="x", padx=14, pady=(8, 12))
        self.nav = {}
        for name, ic in self.NAV:
            self._rail_btn(rail, name, ic, expanded).pack(fill="x", padx=10, pady=3)
        self._rail_btn(rail, "Settings", "gear", expanded).pack(side="bottom", fill="x", padx=10, pady=14)

    def _rail_btn(self, rail, name, ic, expanded):
        img = self.icon(ic)
        fallback = {"headset": "🎧", "eq": "≋", "mic": "🎙", "mix": "⇄", "tools": "🛠", "gear": "⚙",
                    "firmware": "⬆", "game": "🎮"}[ic]
        text = (f"  {name}" if img else f"{fallback}  {name}") if expanded else ("" if img else fallback)
        b = ctk.CTkButton(rail, text=text, image=img, compound="left", anchor="w" if expanded else "center",
                          width=192 if expanded else 50, height=44, corner_radius=12, fg_color="transparent",
                          hover_color=PAL["hover"], text_color=PAL["muted"], font=ctk.CTkFont(size=14),
                          border_width=1, border_color=PAL["rail"],
                          command=lambda n=name: self.show(n))
        b._icon_name = ic
        self.nav[name] = b
        return b

    def _toggle_sidebar(self):
        self.settings["sidebar"] = "collapsed" if self.settings.get("sidebar") == "expanded" else "expanded"
        save_settings(self.settings)
        self.build()
        self.after(50, self.load_all)

    def _header(self, main):
        wrap = ctk.CTkFrame(main, fg_color="transparent")
        wrap.grid(row=0, column=0, sticky="ew", padx=26, pady=(18, 8))
        h = ctk.CTkFrame(wrap, fg_color="transparent")
        h.pack(fill="x")
        left = ctk.CTkFrame(h, fg_color="transparent")
        left.pack(side="left")
        ctk.CTkLabel(left, text="A 5 0   C O N T R O L", text_color=self.accent,
                     font=ctk.CTkFont(size=11, weight="bold")).pack(anchor="w")
        ctk.CTkLabel(left, text="A50 Wireless Gen 4", font=ctk.CTkFont(size=24, weight="bold"),
                     text_color=PAL["text"]).pack(anchor="w")
        right = ctk.CTkFrame(h, fg_color="transparent")
        right.pack(side="right")

        def chip(master):
            c = ctk.CTkFrame(master, fg_color=PAL["card2"], border_color=PAL["border"], border_width=1,
                             corner_radius=16, height=34)
            c.pack(side="left", padx=4)
            return c
        self.dot = ctk.CTkLabel(chip(right), text="●  Not connected", text_color=BAD, font=ctk.CTkFont(size=13))
        self.dot.pack(padx=14, pady=4)
        self.hdr_bat = ctk.CTkLabel(chip(right), text=" —" if self.icon("battery") else "🔋 —",
                                    image=self.icon("battery"), compound="left", text_color=PAL["text"],
                                    font=ctk.CTkFont(size=13, weight="bold"))
        self.hdr_bat.pack(padx=12, pady=4)
        ctk.CTkFrame(right, width=10, fg_color="transparent").pack(side="left")
        self.btn(right, "Reload", self.load_all, width=96, image=self.icon("refresh", size=16),
                 compound="left").pack(side="left", padx=4)
        b = self.btn(right, "Save to headset", self.save, primary=True, width=156)
        b.pack(side="left", padx=4)
        GradientLine(wrap, self, height=2).pack(fill="x", pady=(14, 0))
        self.status = ctk.CTkLabel(main, text="", text_color=PAL["muted"], anchor="w")
        self.status.grid(row=2, column=0, sticky="ew", padx=28, pady=(0, 8))

    def show(self, name):
        if name not in self.pages:
            name = "Home"
        self.page = name
        for n, f in self.pages.items():
            f.grid_forget()
            b = self.nav[n]
            b.configure(fg_color="transparent", text_color=PAL["muted"], border_color=PAL["rail"],
                        font=ctk.CTkFont(size=14))
            if self.icon(b._icon_name):
                b.configure(image=self.icon(b._icon_name))
        self.pages[name].grid(row=1, column=0, sticky="nsew", padx=18)
        b = self.nav[name]
        b.configure(fg_color=mix(self.c("rail"), self.accent, 0.14), text_color=self.accent,
                    border_color=mix(self.c("rail"), self.accent, 0.35), font=ctk.CTkFont(size=14, weight="bold"))
        if self.icon(b._icon_name, active=True):
            b.configure(image=self.icon(b._icon_name, active=True))
        if name == "Home":
            self.after(50, self.headset.redraw)
        if name == "Equalizer":
            self.after(50, self.curve.redraw)

    TITLE_ICONS = {"Equalizer": "eq", "Game profiles": "game", "Microphone": "mic", "Mix and alerts": "mix",
                   "Firmware update": "firmware", "Maintenance": "tools", "Settings": "gear"}

    def _title(self, p, text, sub=None):
        row = ctk.CTkFrame(p, fg_color="transparent")
        row.pack(anchor="w", fill="x", padx=8, pady=(4, 12))
        ic = self.TITLE_ICONS.get(text) or next((v for k, v in self.TITLE_ICONS.items() if text.startswith(k)), None)
        img = self.icon(ic, active=True, size=22) if ic else None
        if img:
            ctk.CTkLabel(row, text="", image=img, width=44, height=44, corner_radius=12,
                         fg_color=self.tint(0.18)).pack(side="left", padx=(0, 12))
        col = ctk.CTkFrame(row, fg_color="transparent")
        col.pack(side="left", fill="x", expand=True)
        ctk.CTkLabel(col, text=text, font=ctk.CTkFont(size=22, weight="bold"), text_color=PAL["text"]).pack(anchor="w")
        if sub:
            ctk.CTkLabel(col, text=sub, text_color=PAL["muted"], justify="left", wraplength=820).pack(anchor="w")

    def _slider_row(self, card, label, frm, to, key, apply):
        row = ctk.CTkFrame(card, fg_color="transparent")
        row.pack(fill="x", padx=16, pady=8)
        ctk.CTkLabel(row, text=label, width=190, anchor="w", text_color=PAL["text"]).pack(side="left")
        val = ctk.CTkLabel(row, text="—", width=44, anchor="e", font=ctk.CTkFont(weight="bold"), text_color=PAL["text"])
        val.pack(side="right")
        s = ctk.CTkSlider(row, from_=frm, to=to, number_of_steps=to - frm, button_color=self.accent,
                          button_hover_color=darker(self.accent), progress_color=self.accent, fg_color=PAL["track"],
                          command=lambda x: (val.configure(text=str(int(x))), self._later(key, lambda: apply(int(s.get())))))
        s.pack(side="left", fill="x", expand=True, padx=12)
        return s, val

    def _seg(self, master, values, cmd, **kw):
        return ctk.CTkSegmentedButton(master, values=values, command=cmd, selected_color=self.accent,
                                      selected_hover_color=darker(self.accent), unselected_color=PAL["card2"],
                                      fg_color=PAL["card2"], corner_radius=10,
                                      unselected_hover_color=PAL["hover"], text_color=PAL["text"], **kw)

    # ---- pages
    def _page_home(self, p):
        top = ctk.CTkFrame(p, fg_color="transparent")
        top.pack(fill="both", expand=True)
        top.grid_columnconfigure(0, weight=3)
        top.grid_columnconfigure(1, weight=2)
        hv = self.card(top)
        hv.grid(row=0, column=0, sticky="nsew", padx=8, pady=8)
        self.headset = HeadsetView(hv, self, height=380)
        self.headset.pack(fill="both", expand=True, padx=10, pady=(10, 0))
        pick = ctk.CTkFrame(hv, fg_color="transparent")
        pick.pack(pady=(4, 12))
        ctk.CTkButton(pick, text="" if self.icon("chev_l") else "‹", image=self.icon("chev_l"), width=36, height=32,
                      corner_radius=8, fg_color="transparent", hover_color=PAL["hover"], text_color=PAL["text"],
                      command=lambda: self._cycle_model(-1)).pack(side="left")
        self.model_lbl = ctk.CTkLabel(pick, text="", width=260, text_color=PAL["text"],
                                      font=ctk.CTkFont(size=13, weight="bold"))
        self.model_lbl.pack(side="left", padx=6)
        ctk.CTkButton(pick, text="" if self.icon("chev_r") else "›", image=self.icon("chev_r"), width=36, height=32,
                      corner_radius=8, fg_color="transparent", hover_color=PAL["hover"], text_color=PAL["text"],
                      command=lambda: self._cycle_model(1)).pack(side="left")
        self._update_model_label()

        side = ctk.CTkFrame(top, fg_color="transparent")
        side.grid(row=0, column=1, sticky="nsew", pady=8)
        c = self.card(side, "Battery")
        c.pack(fill="x", padx=8, pady=(0, 8))
        self.bat_pct = ctk.CTkLabel(c, text="—", font=ctk.CTkFont(size=40, weight="bold"), text_color=PAL["text"])
        self.bat_pct.pack(anchor="w", padx=16)
        self.bat_bar = ctk.CTkProgressBar(c, height=6, progress_color=self.accent, fg_color=PAL["track"])
        self.bat_bar.set(0)
        self.bat_bar.pack(fill="x", padx=16)
        self.bat_info = ctk.CTkLabel(c, text="", text_color=PAL["muted"])
        self.bat_info.pack(anchor="w", padx=16, pady=(4, 12))

        c = self.card(side, "Headset")
        c.pack(fill="x", padx=8, pady=8)
        self.hs_state = ctk.CTkLabel(c, text="—", font=ctk.CTkFont(size=18, weight="bold"), text_color=PAL["text"])
        self.hs_state.pack(anchor="w", padx=16)
        self.hs_power = ctk.CTkLabel(c, text="", text_color=PAL["muted"])
        self.hs_power.pack(anchor="w", padx=16, pady=(0, 12))

        c = self.card(side, "Firmware")
        c.pack(fill="x", padx=8, pady=8)
        self.fw_lbl = ctk.CTkLabel(c, text="—", text_color=PAL["text"], justify="left")
        self.fw_lbl.pack(anchor="w", padx=16)
        self.health = ctk.CTkLabel(c, text="", font=ctk.CTkFont(weight="bold"))
        self.health.pack(anchor="w", padx=16, pady=(4, 12))

        c = self.card(p, "Battery history (24 h)")
        c.pack(fill="x", padx=8, pady=(4, 8))
        self.bat_chart = tk.Canvas(c, height=130, highlightthickness=0, bd=0, bg=self.c("card"))
        self.bat_chart.pack(fill="x", padx=12, pady=(2, 4))
        self.bat_chart.bind("<Configure>", lambda e: self._draw_bat_chart())
        self.bat_typ = ctk.CTkLabel(c, text="", text_color=PAL["muted"])
        self.bat_typ.pack(anchor="w", padx=16, pady=(0, 10))

    def _page_eq(self, p):
        self._title(p, "Equalizer", "Drag the points up or down (-7 to +7 dB). Changes apply when you release.")
        c = self.card(p)
        c.pack(fill="x", padx=8, pady=(0, 10))
        row = ctk.CTkFrame(c, fg_color="transparent")
        row.pack(fill="x", padx=16, pady=12)
        self.preset_seg = self._seg(row, ["Preset 1", "Preset 2", "Preset 3"], self._preset_changed, height=34)
        self.preset_seg.pack(side="left")
        self.pname = ctk.CTkEntry(row, width=170, placeholder_text="Preset name", fg_color=PAL["card2"],
                                  border_color=PAL["border"], text_color=PAL["text"])
        self.pname.pack(side="left", padx=(18, 6))
        self.btn(row, "Rename", self._rename, width=80).pack(side="left")
        self.btn(row, "Flat", self._flat, width=70).pack(side="right")
        c = self.card(p)
        c.pack(fill="both", expand=True, padx=8)
        self.curve = EQCurve(c, self, self._apply_eq)
        self.curve.pack(fill="both", expand=True, padx=10, pady=10)

    def _page_mic(self, p):
        self._title(p, "Microphone", "Quick setups, mic level, sidetone (hear your own voice), noise gate and a mic test.")
        c = self.card(p, "Quick setups")
        c.pack(fill="x", padx=8, pady=(0, 10))
        self.mic_grid = ctk.CTkFrame(c, fg_color="transparent")
        self.mic_grid.pack(fill="x", padx=12, pady=(4, 2))
        self.mic_note = ctk.CTkLabel(c, text="Pick a setup: it's applied right away (use Save to headset to keep it).",
                                     text_color=PAL["muted"], wraplength=760, justify="left")
        self.mic_note.pack(anchor="w", padx=16, pady=(2, 4))
        row = ctk.CTkFrame(c, fg_color="transparent")
        row.pack(anchor="w", padx=16, pady=(0, 12))
        self.btn(row, "Save current as…", self._mic_save, width=140).pack(side="left", padx=(0, 6))
        self.mic_del = self.btn(row, "Delete", self._mic_delete, width=80)
        self.mic_del.pack(side="left")
        self.mic_sel = None
        self._mic_fill()

        c = self.card(p, "Levels")
        c.pack(fill="x", padx=8, pady=(0, 10))
        self.mic = self._slider_row(c, "Microphone level", 0, 100, "mic",
                                    lambda x: self._do(lambda: self.dev.set_slider(SLIDER["mic"], x)))
        self.side = self._slider_row(c, "Sidetone", 0, 100, "side",
                                     lambda x: self._do(lambda: self.dev.set_slider(SLIDER["sidetone"], x)))
        ctk.CTkFrame(c, height=6, fg_color="transparent").pack()
        c = self.card(p, "Noise gate")
        c.pack(fill="x", padx=8, pady=(0, 10))
        self.gate = self._seg(c, GATE_NAMES, lambda v: self._do(lambda: self.dev.set_noise_gate(GATE_NAMES.index(v))),
                              height=36)
        self.gate.pack(anchor="w", padx=16, pady=(6, 4))
        ctk.CTkLabel(c, text="Streaming = most open  ·  Night = soft voices  ·  Home = balanced  ·  "
                             "Tournament = strongest background noise reduction",
                     text_color=PAL["muted"]).pack(anchor="w", padx=16, pady=(0, 12))

        c = self.card(p, "Mic test")
        c.pack(fill="x", padx=8, pady=(0, 10))
        self.mt_dev = ctk.CTkLabel(c, text="", text_color=PAL["muted"])
        self.mt_dev.pack(anchor="w", padx=16, pady=(4, 2))
        self.mt_meter = tk.Canvas(c, height=30, highlightthickness=0, bd=0, bg=self.c("card"))
        self.mt_meter.pack(fill="x", padx=16, pady=(4, 2))
        self.mt_meter.bind("<Configure>", lambda e: self._mt_draw())
        self.mt_spec = tk.Canvas(c, height=110, highlightthickness=0, bd=0, bg=self.c("card"))
        self.mt_spec.pack(fill="x", padx=16, pady=(6, 2))
        self.mt_spec.bind("<Configure>", lambda e: self._mt_draw_spec())
        self.mt_specv = [-90.0] * len(mic_test.SPEC_FREQS)
        self.mt_hint = ctk.CTkLabel(c, text="Speak normally: the bar should stay in the green zone. When you stop "
                                            "talking, the noise gate should bring it down.",
                                    text_color=PAL["muted"], wraplength=760, justify="left")
        self.mt_hint.pack(anchor="w", padx=16, pady=(2, 4))
        row = ctk.CTkFrame(c, fg_color="transparent")
        row.pack(anchor="w", padx=16, pady=(2, 14))
        self.mt_live = self.btn(row, "Start live test", self._mt_toggle, primary=True, width=140)
        self.mt_live.pack(side="left", padx=(0, 6))
        self.mt_rec = self.btn(row, "Record 5 s and play back", self._mt_record, width=190)
        self.mt_rec.pack(side="left", padx=(0, 6))
        self.mt_cmp = self.btn(row, "Compare headset mic presets", self._mt_compare, width=210)
        self.mt_cmp.pack(side="left")
        self.mt_job, self.mt_level, self.mt_peaks = None, (-90.0, -90.0), []
        self._mt_device()

        c = self.card(p, "Headset mic EQ")
        c.pack(fill="x", padx=8, pady=(0, 10))
        self.miceq = self._seg(c, MIC_EQ_NAMES, lambda v: self._do(lambda: self.dev.set_mic_eq(MIC_EQ_NAMES.index(v))),
                               height=32)
        self.miceq.pack(anchor="w", padx=16, pady=(6, 4))
        ctk.CTkLabel(c, text="Built into the headset: works on PC and consoles. Use 'Compare headset mic presets' "
                             "above to hear the difference.", text_color=PAL["muted"], wraplength=760,
                     justify="left").pack(anchor="w", padx=16, pady=(0, 12))
        self._page_apo(p)

    # ---- mic quick setups
    def _mic_fill(self):
        for w in self.mic_grid.winfo_children():
            w.destroy()
        self.mic_btns = {}
        for i, m in enumerate(prof.mic_all(self.puser)):
            bt = ctk.CTkButton(self.mic_grid, text=m["name"] + ("  ★" if m["kind"] == "mine" else ""), height=34,
                               corner_radius=10, fg_color=PAL["card2"], hover_color=PAL["hover"],
                               text_color=PAL["text"], border_width=1, border_color=PAL["border"],
                               command=lambda m=m: self._mic_apply(m))
            bt.grid(row=i // 3, column=i % 3, sticky="ew", padx=4, pady=4)
            self.mic_btns[m["id"]] = bt
        for col in range(3):
            self.mic_grid.grid_columnconfigure(col, weight=1)
        self._mic_mark()

    def _mic_mark(self):
        sel = darker(self.accent, 0.35) if self.dark else "#DDF1FF"
        for i, bt in self.mic_btns.items():
            bt.configure(fg_color=sel if i == self.mic_sel else PAL["card2"],
                         border_color=self.accent if i == self.mic_sel else PAL["border"])
        m = next((x for x in prof.mic_all(self.puser) if x["id"] == self.mic_sel), None)
        self.mic_del.configure(state="normal" if m and m["kind"] == "mine" else "disabled")

    def _mic_apply(self, m, quiet=False):
        if not self.dev:
            self._set_status("Not connected", ok=False)
            return
        ok = self._do(lambda: (self.dev.set_slider(SLIDER["mic"], m["mic"]),
                               self.dev.set_slider(SLIDER["sidetone"], m["sidetone"]),
                               self.dev.set_noise_gate(m["gate"])), quiet=True)
        if not ok:
            return
        self.loading = True
        try:
            self._set_slider(self.mic, m["mic"])
            self._set_slider(self.side, m["sidetone"])
            self.gate.set(GATE_NAMES[m["gate"]])
        finally:
            self.loading = False
        self.mic_sel = m["id"]
        try:
            self._mic_mark()
            self.mic_note.configure(text=f"{m['name']}: mic {m['mic']} · sidetone {m['sidetone']} · "
                                         f"{GATE_NAMES[m['gate']]} gate. {m.get('note', '')}")
        except (AttributeError, tk.TclError):
            pass
        if not quiet:
            self._set_status(f"Mic setup '{m['name']}' applied · not saved yet")

    def _mic_save(self):
        name = ctk.CTkInputDialog(text="Name for this mic setup:", title=APP_NAME).get_input()
        if not name or not name.strip():
            return
        try:
            m = prof.mic_put(self.puser, {"name": name.strip(), "mic": int(self.mic[0].get()),
                                          "sidetone": int(self.side[0].get()),
                                          "gate": GATE_NAMES.index(self.gate.get()) if self.gate.get() in GATE_NAMES else 2,
                                          "note": "Your setup."})
        except (ValueError, tk.TclError):
            return
        self._psave()
        self.mic_sel = m["id"]
        self._mic_fill()
        self._set_status(f"✔ Mic setup '{m['name']}' saved")

    def _mic_delete(self):
        m = next((x for x in prof.mic_all(self.puser) if x["id"] == self.mic_sel), None)
        if m and m["kind"] == "mine" and messagebox.askyesno(APP_NAME, f"Delete the mic setup '{m['name']}'?"):
            prof.mic_remove(self.puser, m["id"])
            self._psave()
            self.mic_sel = None
            self._mic_fill()

    # ---- PC mic EQ (Equalizer APO)
    def _apo_state(self):
        st = self.puser.setdefault("apo", {})
        if not isinstance(st.get("current"), dict):
            st["current"] = dict(apo.PRESETS[0])
        st["current"] = apo.clean(st["current"])
        return st

    def _apo_all(self):
        return [dict(x, kind="builtin") for x in apo.PRESETS] + \
               [dict(apo.clean(x), kind="mine") for x in self.puser.get("apo_custom", [])]

    def _page_apo(self, p):
        c = self.card(p, "PC mic EQ (advanced)")
        c.pack(fill="x", padx=8)
        st = self._apo_state()
        self.apo_dir = apo.install_dir()
        info = ctk.CTkFrame(c, fg_color="transparent")
        info.pack(fill="x", padx=16, pady=(4, 2))
        if self.apo_dir:
            text = ("10-band EQ for your voice, processed on this PC by Equalizer APO (works in Discord, games, "
                    "OBS…). In Equalizer APO's Configurator, tick only the A50 Voice microphone under "
                    "'Capture devices', then restart Windows once.")
        else:
            text = ("Needs Equalizer APO, a free open-source audio tool, to process your voice on this PC like "
                    "Razer Synapse does. Install it, tick only the A50 Voice microphone under 'Capture devices' "
                    "in its Configurator, restart Windows, then reopen this page.")
        ctk.CTkLabel(info, text=text, text_color=PAL["muted"], wraplength=600, justify="left").pack(side="left")
        if self.apo_dir:
            self.btn(info, "Open Configurator", lambda: self._apo_open_cfg(), width=150).pack(side="right")
        else:
            self.btn(info, "Get Equalizer APO", lambda: webbrowser.open(apo.DOWNLOAD_URL), primary=True,
                     width=150).pack(side="right")
            return
        self.apo_sw = ctk.CTkSwitch(c, text="Use PC mic EQ", progress_color=self.accent, text_color=PAL["text"],
                                    command=self._apo_toggled)
        self.apo_sw.select() if st.get("enabled") else self.apo_sw.deselect()
        self.apo_sw.pack(anchor="w", padx=16, pady=(8, 4))
        self.apo_grid = ctk.CTkFrame(c, fg_color="transparent")
        self.apo_grid.pack(fill="x", padx=12, pady=(2, 2))
        self.apo_note = ctk.CTkLabel(c, text="", text_color=PAL["muted"], wraplength=760, justify="left")
        self.apo_note.pack(anchor="w", padx=16)
        self.apo_curve = EQCurve(c, self, self._apo_curve_changed, bands=10, rng=apo.RANGE, freqs=apo.BANDS)
        self.apo_curve.configure(height=220)
        self.apo_curve.pack(fill="x", padx=8, pady=(4, 0))
        row = ctk.CTkFrame(c, fg_color="transparent")
        row.pack(fill="x", padx=16, pady=(2, 4))
        ctk.CTkLabel(row, text="Preamp", width=70, anchor="w", text_color=PAL["text"]).pack(side="left")
        self.apo_pre_val = ctk.CTkLabel(row, text="0 dB", width=50, text_color=PAL["text"])
        self.apo_pre = ctk.CTkSlider(row, from_=-12, to=12, number_of_steps=24, width=200, button_color=self.accent,
                                     button_hover_color=darker(self.accent), progress_color=self.accent,
                                     fg_color=PAL["track"], command=self._apo_pre_changed)
        self.apo_pre.pack(side="left")
        self.apo_pre_val.pack(side="left", padx=(6, 24))
        ctk.CTkLabel(row, text="Low cut", text_color=PAL["text"]).pack(side="left", padx=(0, 8))
        self.apo_hp = self._seg(row, ["Off", "60 Hz", "80 Hz", "100 Hz", "120 Hz"], self._apo_hp_changed)
        self.apo_hp.pack(side="left")
        row = ctk.CTkFrame(c, fg_color="transparent")
        row.pack(anchor="w", padx=16, pady=(6, 14))
        self.btn(row, "Save as…", self._apo_save, width=100).pack(side="left", padx=(0, 6))
        self.apo_del = self.btn(row, "Delete", self._apo_delete, width=80)
        self.apo_del.pack(side="left")
        self._apo_fill()
        self._apo_show(st["current"])

    def _apo_open_cfg(self):
        exe = apo.configurator()
        if exe:
            try:
                os.startfile(exe)
            except OSError as e:
                messagebox.showerror(APP_NAME, f"Can't open the Configurator.\n\n{e}")

    def _apo_fill(self):
        for w in self.apo_grid.winfo_children():
            w.destroy()
        self.apo_btns = {}
        for i, m in enumerate(self._apo_all()):
            bt = ctk.CTkButton(self.apo_grid, text=m["name"] + ("  ★" if m["kind"] == "mine" else ""), height=32,
                               corner_radius=10, fg_color=PAL["card2"], hover_color=PAL["hover"], text_color=PAL["text"],
                               border_width=1, border_color=PAL["border"], command=lambda m=m: self._apo_pick(m))
            bt.grid(row=i // 4, column=i % 4, sticky="ew", padx=4, pady=4)
            self.apo_btns[m["id"]] = bt
        for col in range(4):
            self.apo_grid.grid_columnconfigure(col, weight=1)

    def _apo_show(self, cur):
        sel = darker(self.accent, 0.35) if self.dark else "#DDF1FF"
        for i, bt in self.apo_btns.items():
            bt.configure(fg_color=sel if i == cur["id"] else PAL["card2"],
                         border_color=self.accent if i == cur["id"] else PAL["border"])
        self.apo_curve.set(cur["gains"])
        self.apo_pre.set(cur["preamp"])
        self.apo_pre_val.configure(text=f"{cur['preamp']:+d} dB")
        self.apo_hp.set(f"{cur['hp']} Hz" if cur["hp"] else "Off")
        self.apo_note.configure(text=cur.get("note") or "")
        mine = any(x["id"] == cur["id"] and x["kind"] == "mine" for x in self._apo_all())
        self.apo_del.configure(state="normal" if mine else "disabled")

    def _apo_pick(self, m):
        st = self._apo_state()
        st["current"] = apo.clean(m)
        self._apo_show(st["current"])
        self._apo_apply()

    def _apo_edited(self):
        """A manual change turns the current profile into an unsaved custom one."""
        cur = self._apo_state()["current"]
        if not cur["id"].startswith("edit"):
            cur.update(id="edit", name=cur["name"] + " (edited)", note="Edited: use 'Save as…' to keep it.")
        self._apo_show(cur)
        self._later("apo", self._apo_apply)

    def _apo_curve_changed(self, gains):
        self._apo_state()["current"]["gains"] = list(gains)
        self._apo_edited()

    def _apo_pre_changed(self, v):
        self._apo_state()["current"]["preamp"] = int(round(v))
        self.apo_pre_val.configure(text=f"{int(round(v)):+d} dB")
        self._apo_edited()

    def _apo_hp_changed(self, v):
        self._apo_state()["current"]["hp"] = 0 if v == "Off" else int(v.split()[0])
        self._apo_edited()

    def _apo_toggled(self):
        self._apo_state()["enabled"] = bool(self.apo_sw.get())
        self._apo_apply()

    def _apo_apply(self):
        st = self._apo_state()
        self._psave()
        try:
            _, name = mic_test.find_a50()
        except Exception:
            name = None
        try:
            apo.write(st["current"], device=apo.device_pattern(name), enabled=bool(st.get("enabled")))
        except PermissionError:
            messagebox.showerror(APP_NAME, "Windows didn't allow writing to Equalizer APO's config folder.\n\n"
                                           "Start A50 Control once with right-click > Run as administrator and "
                                           "change the mic EQ again.")
            return
        except OSError as e:
            self._set_status(f"PC mic EQ: {e}", ok=False)
            return
        self._set_status("PC mic EQ " + (f"on: {st['current']['name']}" if st.get("enabled") else "off"))

    def _apo_save(self):
        name = ctk.CTkInputDialog(text="Name for this mic EQ:", title=APP_NAME).get_input()
        if not name or not name.strip():
            return
        st = self._apo_state()
        item = apo.clean(dict(st["current"], id=prof.new_id(), name=name.strip(), note="Your mic EQ."))
        self.puser["apo_custom"] = [x for x in self.puser.get("apo_custom", []) if x["id"] != item["id"]] + [item]
        st["current"] = dict(item)
        self._psave()
        self._apo_fill()
        self._apo_show(st["current"])
        self._set_status(f"✔ Mic EQ '{item['name']}' saved")

    def _apo_delete(self):
        cur = self._apo_state()["current"]
        if not messagebox.askyesno(APP_NAME, f"Delete the mic EQ '{cur['name']}'?"):
            return
        self.puser["apo_custom"] = [x for x in self.puser.get("apo_custom", []) if x["id"] != cur["id"]]
        self._apo_pick(apo.PRESETS[0])
        self._apo_fill()
        self._apo_show(self._apo_state()["current"])

    # ---- compare the headset's built-in mic EQ presets
    def _mt_compare(self):
        if self.mt_job or not self.dev:
            if not self.dev:
                self._set_status("Not connected", ok=False)
            return
        folder = os.path.join(DATA_DIR, "mic_compare")
        if not messagebox.askokcancel(APP_NAME, "The app will switch the headset mic EQ to Preset 0, 1 and 2 and "
                                                "record 4 seconds with each.\n\nAfter you press OK, keep talking "
                                                "normally (read something aloud) for about 15 seconds.\n\n"
                                                f"The recordings stay on this PC:\n{folder}"):
            return
        os.makedirs(folder, exist_ok=True)
        self._mt_device()
        orig = self._get(self.dev.mic_eq)
        for b in (self.mt_live, self.mt_rec, self.mt_cmp):
            b.configure(state="disabled")
        self.mt_job = mic_test.MicTest(None, None)  # placeholder: blocks the other tests

        def work():
            files, err = [], None
            for i in range(len(MIC_EQ_NAMES)):
                self.after(0, lambda i=i: self.mt_hint.configure(
                    text=f"Recording with headset preset {i}… keep talking", text_color=WARN))
                try:
                    self.dev.set_mic_eq(i)
                except DeviceError as e:
                    err = f"Can't change the headset mic EQ: {e}"
                    break
                time.sleep(0.6)
                box = {}
                mic_test.MicTest(self._mt_on_level, lambda pcm, e: box.update(pcm=pcm, err=e),
                                 device=self.mt_id, seconds=4, on_spectrum=self._mt_on_spec)._run()
                if box.get("err") or not box.get("pcm"):
                    err = box.get("err") or "Nothing was recorded."
                    break
                path = os.path.join(folder, f"headset_mic_preset_{i}.wav")
                mic_test.save_wav(path, box["pcm"])
                files.append((i, path, box["pcm"]))
            if orig is not None:
                try:
                    self.dev.set_mic_eq(orig)
                except DeviceError:
                    pass
            self.after(0, self._mt_compare_done, files, err, folder)

        threading.Thread(target=work, daemon=True).start()

    def _mt_compare_done(self, files, err, folder):
        self.mt_job = None
        self.mt_level = (-90.0, -90.0)
        try:
            self._mt_draw()
            for b in (self.mt_live, self.mt_rec, self.mt_cmp):
                b.configure(state="normal")
        except tk.TclError:
            return
        if err:
            self.mt_hint.configure(text=err, text_color=BAD)
            return
        self.mt_hint.configure(text=f"Saved {len(files)} recordings in {folder}", text_color=OK)
        if messagebox.askyesno(APP_NAME, "Done. Play the three recordings now (Preset 0, 1, 2)?"):
            for b in (self.mt_live, self.mt_rec, self.mt_cmp):
                b.configure(state="disabled")

            def play():
                for i, _, pcm in files:
                    self.after(0, lambda i=i: self.mt_hint.configure(text=f"Playing headset preset {i}…",
                                                                     text_color=self.accent))
                    try:
                        mic_test.play_pcm(pcm)
                    except Exception:
                        break
                    time.sleep(0.4)
                self.after(0, lambda: ([b.configure(state="normal") for b in (self.mt_live, self.mt_rec, self.mt_cmp)],
                                       self.mt_hint.configure(text=f"Recordings saved in {folder}", text_color=OK)))

            threading.Thread(target=play, daemon=True).start()

    # ---- mic tester
    def _mt_device(self):
        try:
            self.mt_id, name = mic_test.find_a50()
        except Exception:
            self.mt_id, name = None, None
        self.mt_dev.configure(text=f"Recording from: {name}" if name else
                              "A50 voice input not found: using the default Windows microphone.")

    def _mt_draw(self):
        cv = self.mt_meter
        try:
            cv.delete("all")
            w, h = max(cv.winfo_width(), 100), 30
        except tk.TclError:
            return
        x = lambda db: (max(-60.0, min(0.0, db)) + 60) / 60 * w
        cv.configure(bg=self.c("card"))
        cv.create_rectangle(0, 6, w, h - 6, fill=self.c("track"), outline="")
        cv.create_rectangle(x(-30), 6, x(-6), h - 6, fill=darker(OK, 0.3), outline="")
        cv.create_rectangle(x(-6), 6, w, h - 6, fill=darker(BAD, 0.3), outline="")
        rms, peak = self.mt_level
        col = BAD if peak > -3 else OK if rms > -30 else self.accent
        cv.create_rectangle(0, 9, x(rms), h - 9, fill=col, outline="")
        cv.create_line(x(peak), 3, x(peak), h - 3, fill=self.c("text"), width=2)
        for db in (-48, -36, -24, -12):
            cv.create_text(x(db), h - 1, text=str(db), fill=self.c("muted"), font=("Segoe UI", 7), anchor="s")

    def _mt_on_spec(self, bands):
        self.after(0, self._mt_spec_show, bands)

    def _mt_spec_show(self, bands):
        # fast attack, slow release, like a real analyser
        self.mt_specv = [b if b > v else max(b, v - 3) for b, v in zip(bands, self.mt_specv)]
        self._mt_draw_spec()

    def _mt_draw_spec(self):
        cv = getattr(self, "mt_spec", None)
        if cv is None:
            return
        try:
            cv.delete("all")
            w, h = max(cv.winfo_width(), 100), 110
        except tk.TclError:
            return
        cv.configure(bg=self.c("card"))
        n = len(self.mt_specv)
        gap, bw = 3, (w - 3 * (n - 1)) / n
        base = h - 16
        for i, v in enumerate(self.mt_specv):
            frac = (max(-70.0, min(-10.0, v)) + 70) / 60
            x0 = i * (bw + gap)
            cv.create_rectangle(x0, 4, x0 + bw, base, fill=self.c("track"), outline="")
            if frac > 0:
                cv.create_rectangle(x0, base - frac * (base - 4), x0 + bw, base,
                                    fill=WARN if frac > 0.9 else self.accent, outline="")
        for i, f in enumerate(mic_test.SPEC_FREQS):
            if i % 4 == 0 or i == n - 1:
                cv.create_text(i * (bw + gap) + bw / 2, h - 2, text=f"{f // 1000}k" if f >= 1000 else str(f),
                               fill=self.c("muted"), font=("Segoe UI", 8), anchor="s")
        cv.create_text(2, 2, text="Bass", fill=self.c("muted"), font=("Segoe UI", 8), anchor="nw")
        cv.create_text(w / 2, 2, text="Voice body · clarity", fill=self.c("muted"), font=("Segoe UI", 8), anchor="n")
        cv.create_text(w - 2, 2, text="Sibilance", fill=self.c("muted"), font=("Segoe UI", 8), anchor="ne")

    def _mt_on_level(self, rms, peak):
        self.after(0, self._mt_show, rms, peak)

    def _mt_show(self, rms, peak):
        self.mt_level = (rms, peak)
        self.mt_peaks = (self.mt_peaks + [peak])[-30:]  # last 1.5 s
        best = max(self.mt_peaks)
        if best < -45:
            hint, col = "Can't hear you: is the mic boom down (flipped up = muted)? Try a higher mic level.", WARN
        elif best < -28:
            hint, col = f"Quiet ({best:.0f} dB peak): raise the mic level a little.", WARN
        elif best <= -3:
            hint, col = f"Good level ({best:.0f} dB peak).", OK
        else:
            hint, col = "Too loud, the voice is clipping: lower the mic level.", BAD
        try:
            self.mt_hint.configure(text=hint, text_color=col)
        except tk.TclError:
            return
        self._mt_draw()

    def _mt_toggle(self):
        if self.mt_job:
            self.mt_job.stop()
            return
        self._mt_device()
        self.mt_peaks = []
        self.mt_job = mic_test.MicTest(self._mt_on_level, lambda pcm, err: self.after(0, self._mt_end, None, err),
                                       device=self.mt_id, on_spectrum=self._mt_on_spec).start()
        self.mt_live.configure(text="Stop")
        self.mt_rec.configure(state="disabled")

    def _mt_record(self):
        if self.mt_job:
            return
        self._mt_device()
        self.mt_peaks = []
        self.mt_job = mic_test.MicTest(self._mt_on_level, lambda pcm, err: self.after(0, self._mt_end, pcm, err),
                                       device=self.mt_id, seconds=5, on_spectrum=self._mt_on_spec).start()
        self.mt_rec.configure(text="Recording… speak now", state="disabled")
        self.mt_live.configure(state="disabled")

    def _mt_end(self, pcm, err):
        self.mt_job = None
        try:
            self.mt_live.configure(text="Start live test", state="normal")
            self.mt_rec.configure(text="Record 5 s and play back", state="normal")
            self.mt_level = (-90.0, -90.0)
            self._mt_draw()
        except tk.TclError:
            return
        if err:
            self.mt_hint.configure(text=err, text_color=BAD)
            return
        if pcm:
            self.mt_rec.configure(text="Playing back…", state="disabled")
            self.mt_live.configure(state="disabled")

            def play():
                try:
                    mic_test.play_pcm(pcm)
                except Exception as e:
                    self.after(0, lambda: self.mt_hint.configure(text=f"Playback failed: {e}", text_color=BAD))
                self.after(0, lambda: (self.mt_rec.configure(text="Record 5 s and play back", state="normal"),
                                       self.mt_live.configure(state="normal")))

            threading.Thread(target=play, daemon=True).start()

    def _page_mix(self, p):
        self._title(p, "Mix and alerts", "Game/voice balance, alert volume and the stream port output mix.")
        c = self.card(p, "Balance")
        c.pack(fill="x", padx=8, pady=(0, 10))
        self.bal = self._slider_row(c, "Default (game ← → voice)", 0, 255, "bal",
                                    lambda x: self._do(lambda: self.dev.set_default_balance(x)))
        self.curbal = ctk.CTkLabel(c, text="", text_color=PAL["muted"])
        self.curbal.pack(anchor="w", padx=16, pady=(0, 10))
        c = self.card(p, "Alerts")
        c.pack(fill="x", padx=8, pady=(0, 10))
        self.alert = self._slider_row(c, "Alert volume", 0, 100, "alert",
                                      lambda x: self._do(lambda: self.dev.set_alert_volume(x)))
        ctk.CTkFrame(c, height=6, fg_color="transparent").pack()
        c = self.card(p, "Stream port mix")
        c.pack(fill="x", padx=8)
        self.stream = {}
        for key, name in (("stream_game", "Game"), ("stream_chat", "Chat"), ("stream_mic", "Mic"), ("stream_aux", "Aux")):
            self.stream[key] = self._slider_row(c, name, 0, 100, key,
                                                lambda x, k=key: self._do(lambda: self.dev.set_slider(SLIDER[k], x)))
        ctk.CTkFrame(c, height=6, fg_color="transparent").pack()

    # ---- game profiles page
    def _profiles(self):
        return prof.all_profiles(self.puser)

    def _page_profiles(self, p):
        self._title(p, "Game profiles", "Ready-made EQ curves for popular games. Apply one as it is, or tune it "
                                        "and save it as yours.")
        c = self.card(p)
        c.pack(fill="x", padx=8, pady=(0, 10))
        row = ctk.CTkFrame(c, fg_color="transparent")
        row.pack(fill="x", padx=16, pady=(12, 4))
        self.auto_sw2 = ctk.CTkSwitch(row, text="Switch profile automatically when a game starts",
                                      progress_color=self.accent, text_color=PAL["text"], command=self._auto_toggled)
        self.auto_sw2.select() if self.puser.get("auto_switch") else self.auto_sw2.deselect()
        self.auto_sw2.pack(side="left")
        self.auto_lbl = ctk.CTkLabel(row, text="", text_color=PAL["muted"])
        self.auto_lbl.pack(side="right")
        ctk.CTkLabel(c, text="When the game closes, your previous EQ comes back. Works while the app runs (also "
                             "in the tray). Profiles set the level of the 5 bands; the band frequencies stay "
                             "as they are on your headset.", text_color=PAL["muted"], wraplength=780,
                     justify="left").pack(anchor="w", padx=16, pady=(0, 12))
        self._auto_label()

        body = ctk.CTkFrame(p, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=8)
        body.grid_columnconfigure(1, weight=1)
        body.grid_rowconfigure(0, weight=1)
        self.plist = ctk.CTkScrollableFrame(body, width=240, height=470, fg_color=PAL["card"], corner_radius=14,
                                            border_width=1, border_color=PAL["border"])
        self.plist.grid(row=0, column=0, sticky="nsw", padx=(0, 10))
        det = self.card(body)
        det.grid(row=0, column=1, sticky="nsew")
        top = ctk.CTkFrame(det, fg_color="transparent")
        top.pack(fill="x", padx=16, pady=(12, 0))
        self.pd_name = ctk.CTkEntry(top, width=260, fg_color=PAL["card2"], border_color=PAL["border"],
                                    text_color=PAL["text"], font=ctk.CTkFont(size=15, weight="bold"))
        self.pd_name.pack(side="left")
        self.pd_kind = ctk.CTkLabel(top, text="", text_color=PAL["muted"])
        self.pd_kind.pack(side="left", padx=10)
        self.pd_note = ctk.CTkLabel(det, text="", text_color=PAL["muted"], wraplength=560, justify="left")
        self.pd_note.pack(anchor="w", padx=16, pady=(6, 0))
        self.pd_curve = EQCurve(det, self, self._pd_changed)
        self.pd_curve.configure(height=210)
        self.pd_curve.pack(fill="x", padx=8, pady=(4, 0))
        ctk.CTkLabel(det, text="Games that switch to this profile (program names, one per line)",
                     text_color=PAL["muted"]).pack(anchor="w", padx=16, pady=(4, 2))
        grow = ctk.CTkFrame(det, fg_color="transparent")
        grow.pack(fill="x", padx=16)
        self.pd_games = ctk.CTkTextbox(grow, height=64, fg_color=PAL["card2"], text_color=PAL["text"],
                                       border_color=PAL["border"], border_width=1,
                                       font=ctk.CTkFont(family="Consolas", size=12))
        self.pd_games.pack(side="left", fill="x", expand=True)
        self.btn(grow, "Add game…", self._pd_add_game, width=100).pack(side="left", padx=(8, 0), anchor="n")
        mrow = ctk.CTkFrame(det, fg_color="transparent")
        mrow.pack(fill="x", padx=16, pady=(8, 0))
        ctk.CTkLabel(mrow, text="Microphone with this profile", text_color=PAL["text"]).pack(side="left")
        self.pd_mic = ctk.CTkOptionMenu(mrow, values=self._mic_choice_names(), width=230, fg_color=PAL["card2"],
                                        button_color=self.accent, button_hover_color=darker(self.accent),
                                        text_color=PAL["text"], dropdown_fg_color=PAL["card"],
                                        dropdown_text_color=PAL["text"])
        self.pd_mic.pack(side="left", padx=10)
        b = ctk.CTkFrame(det, fg_color="transparent")
        b.pack(fill="x", padx=16, pady=(10, 14))
        self.btn(b, "Apply to headset", self._pd_apply, primary=True, width=140).pack(side="left", padx=(0, 6))
        self.btn(b, "Save", self._pd_save, width=80).pack(side="left", padx=(0, 6))
        self.pd_reset = self.btn(b, "Reset", self._pd_reset, width=80)
        self.pd_reset.pack(side="left", padx=(0, 6))
        self.btn(b, "New", self._pd_new, width=64).pack(side="left", padx=(0, 6))
        self.btn(b, "Import…", self._pd_import, width=80).pack(side="right")
        self.btn(b, "Export…", self._pd_export, width=80).pack(side="right", padx=(0, 6))
        self._plist_fill()
        first = self.psel or self._profiles()[0]["id"]
        self.after(60, lambda: self._pd_show(first))

    def _plist_fill(self):
        for w in self.plist.winfo_children():
            w.destroy()
        self.pbtns = {}
        allp = self._profiles()
        for cat in prof.CATEGORIES:
            items = [x for x in allp if x["category"] == cat]
            if not items:
                continue
            ctk.CTkLabel(self.plist, text=cat.upper(), text_color=PAL["muted"],
                         font=ctk.CTkFont(size=11, weight="bold")).pack(anchor="w", padx=8, pady=(10, 2))
            for x in items:
                mark = {"edited": "  ✎", "mine": "  ★"}.get(x["kind"], "")
                bt = ctk.CTkButton(self.plist, text=x["name"] + mark, anchor="w", height=30, corner_radius=8,
                                   fg_color="transparent", hover_color=PAL["hover"], text_color=PAL["text"],
                                   command=lambda i=x["id"]: self._pd_show(i))
                bt.pack(fill="x", padx=4, pady=1)
                self.pbtns[x["id"]] = bt

    def _pd_get(self, pid):
        return next((x for x in self._profiles() if x["id"] == pid), None)

    def _pd_show(self, pid):
        x = self._pd_get(pid) or self._profiles()[0]
        self.psel = x["id"]
        sel = darker(self.accent, 0.35) if self.dark else "#DDF1FF"
        for i, bt in self.pbtns.items():
            try:
                bt.configure(fg_color=sel if i == x["id"] else "transparent")
            except tk.TclError:
                pass
        self.pd_name.delete(0, "end")
        self.pd_name.insert(0, x["name"])
        self.pd_kind.configure(text={"builtin": "Ready-made", "edited": "Ready-made · edited by you",
                                     "mine": "Your profile"}[x["kind"]])
        self.pd_note.configure(text=x.get("note") or "")
        self.pd_gains = list(x["gains"])
        freqs = self.curve.freqs if getattr(self, "curve", None) else None
        self.pd_curve.set(self.pd_gains, freqs if freqs and all(freqs) else None)
        self.pd_games.delete("1.0", "end")
        self.pd_games.insert("1.0", "\n".join(x.get("games", [])))
        self.pd_mic.configure(values=self._mic_choice_names())
        self.pd_mic.set(self._mic_name(x.get("mic")))
        self.pd_reset.configure(text="Delete" if x["kind"] == "mine" else "Reset",
                                state="disabled" if x["kind"] == "builtin" else "normal")

    def _pd_changed(self, gains):
        self.pd_gains = list(gains)

    def _pd_current(self):
        x = self._pd_get(self.psel)
        games = [g.strip().lower() for g in self.pd_games.get("1.0", "end").splitlines() if g.strip()]
        return x, {"name": self.pd_name.get().strip() or x["name"], "category": x["category"],
                   "gains": list(self.pd_gains), "games": games, "note": x.get("note", ""),
                   "mic": self._mic_id(self.pd_mic.get())}

    def _pd_add_game(self):
        path = filedialog.askopenfilename(title="Choose the game's .exe", filetypes=[("Programs", "*.exe")])
        if path:
            name = os.path.basename(path).lower()
            txt = self.pd_games.get("1.0", "end").strip()
            if name not in txt.lower().split():
                self.pd_games.delete("1.0", "end")
                self.pd_games.insert("1.0", (txt + "\n" if txt else "") + name)

    def _apply_gains(self, gains, label):
        """Write gains to the active EQ preset (kept until power-off unless you 'Save to headset')."""
        slot = self._get(self.dev.active_preset) if self.dev else None
        if not slot:
            self._set_status("Not connected", ok=False)
            return False
        if self._do(lambda: self.dev.set_preset_gain(slot, gains), quiet=True):
            self._set_status(f"{label} applied to preset {slot} · not saved yet")
            try:
                if self.preset_map.get(self.preset_seg.get()) == slot:
                    self.curve.set(gains)
            except (AttributeError, tk.TclError):
                pass
            return True
        return False

    def _pd_apply(self):
        x, cur = self._pd_current()
        if self._apply_gains(cur["gains"], f"'{cur['name']}'"):
            self._apply_scene_mic(cur)

    # mic setup helpers shared by profiles, auto-switch and shortcuts
    NO_MIC = "Don't change"

    def _mic_choice_names(self):
        return [self.NO_MIC] + [m["name"] for m in prof.mic_all(self.puser)]

    def _mic_name(self, mid):
        return next((m["name"] for m in prof.mic_all(self.puser) if m["id"] == mid), self.NO_MIC)

    def _mic_id(self, name):
        return next((m["id"] for m in prof.mic_all(self.puser) if m["name"] == name), None)

    def _apply_scene_mic(self, profile):
        m = next((x for x in prof.mic_all(self.puser) if x["id"] == profile.get("mic")), None)
        if m:
            self._mic_apply(m)
        return m

    def _pd_save(self):
        x, cur = self._pd_current()
        if x["kind"] == "builtin":
            cur.update(id=prof.new_id(), overrides=x["id"])
        else:
            cur["id"] = x["id"]
            if x.get("overrides"):
                cur["overrides"] = x["overrides"]
        saved = prof.put(self.puser, cur)
        self._psave()
        self._plist_fill()
        self._pd_show(saved["id"])
        self._set_status(f"✔ Profile '{saved['name']}' saved")

    def _pd_reset(self):
        x = self._pd_get(self.psel)
        if x["kind"] == "edited":
            if not messagebox.askyesno(APP_NAME, f"Put '{x['name']}' back to the ready-made version?"):
                return
            prof.remove(self.puser, x["id"])
            self._psave()
            self._plist_fill()
            self._pd_show(x["overrides"])
        elif x["kind"] == "mine":
            if not messagebox.askyesno(APP_NAME, f"Delete your profile '{x['name']}'?"):
                return
            prof.remove(self.puser, x["id"])
            self._psave()
            self._plist_fill()
            self._pd_show(self._profiles()[0]["id"])

    def _pd_new(self):
        gains = list(self.curve.gains) if getattr(self, "curve", None) else [0] * 5
        p = prof.put(self.puser, {"id": prof.new_id(), "name": "My profile", "category": prof.MINE,
                                  "gains": gains, "games": [], "note": "Made from your current EQ."})
        self._psave()
        self._plist_fill()
        self._pd_show(p["id"])
        self.pd_name.focus_set()
        self.pd_name.select_range(0, "end")

    def _pd_export(self):
        x, cur = self._pd_current()
        safe = "".join(ch for ch in cur["name"] if ch not in '\\/:*?"<>|')
        path = filedialog.asksaveasfilename(title="Export profile", defaultextension=".json",
                                            initialfile=f"{safe}.a50profile.json",
                                            filetypes=[("A50 Control profile", "*.json")])
        if path:
            try:
                prof.export_file(path, [cur])
                self._set_status(f"✔ Exported: {os.path.basename(path)}")
            except Exception as e:
                messagebox.showerror(APP_NAME, f"Export failed.\n\n{e}")

    def _pd_import(self):
        path = filedialog.askopenfilename(title="Import profiles",
                                          filetypes=[("A50 Control profile", "*.json"), ("All files", "*.*")])
        if not path:
            return
        try:
            items = prof.import_file(path)
        except Exception as e:
            messagebox.showerror(APP_NAME, f"This file can't be imported.\n\n{e}")
            return
        for it in items:
            it["category"] = prof.MINE
            prof.put(self.puser, it)
        self._psave()
        self._plist_fill()
        self._pd_show(items[-1]["id"])
        self._set_status(f"✔ Imported {len(items)} profile(s)")

    def _psave(self):
        try:
            prof.save_user(self.puser)
        except Exception as e:
            messagebox.showerror(APP_NAME, f"Could not save your profiles.\n\n{e}")

    # ---- automatic switching
    def _auto_toggled(self):
        on = bool(self.auto_sw2.get())
        self.puser["auto_switch"] = on
        self._psave()
        if not on and self._auto:
            self._auto_restore()
        self._auto_label()

    def _auto_label(self):
        try:
            if not self.puser.get("auto_switch"):
                self.auto_lbl.configure(text="Off", text_color=PAL["muted"])
            elif self._auto:
                x = self._pd_get(self._auto[0])
                self.auto_lbl.configure(text=f"🎮  {x['name'] if x else self._auto[1]} active", text_color=OK)
            else:
                self.auto_lbl.configure(text="Waiting for a game…", text_color=PAL["muted"])
        except (AttributeError, tk.TclError):
            pass

    def _auto_switch(self):
        if not self.puser.get("auto_switch"):
            return
        try:
            found, exe = prof.match_game(self._profiles(), prof.running_processes())
        except Exception:
            return
        if found and (not self._auto or self._auto[0] != found["id"]):
            slot = self._get(self.dev.active_preset)
            if not slot:
                return
            if not self._auto_saved:
                before = self._get(lambda: self.dev.preset_gain(slot))
                if before is None:
                    return
                d = self.dev
                mic = (self._get(lambda: d.slider(SLIDER["mic"])), self._get(lambda: d.slider(SLIDER["sidetone"])),
                       self._get(d.noise_gate))
                self._auto_saved = (slot, before, mic if None not in mic else None)
            if self._apply_gains(found["gains"], f"'{found['name']}'"):
                m = self._apply_scene_mic(found)
                self._auto = (found["id"], exe)
                self._notify(f"{found['name']} profile on ({exe})" + (f" · mic: {m['name']}" if m else ""))
                self._auto_label()
        elif not found and self._auto:
            self._auto_restore()

    def _auto_restore(self):
        if self._auto_saved and self.dev:
            slot, gains, mic = self._auto_saved
            if not self._do(lambda: self.dev.set_preset_gain(slot, gains), quiet=True):
                return  # headset not reachable: try again at the next poll
            if mic:
                self._mic_apply({"id": None, "name": "previous", "mic": mic[0], "sidetone": mic[1], "gate": mic[2]},
                                quiet=True)
            self._notify("Game closed: your EQ is back")
            self._set_status("Game closed: EQ restored")
            try:
                if self.preset_map.get(self.preset_seg.get()) == slot:
                    self.curve.set(gains)
            except (AttributeError, tk.TclError):
                pass
        self._auto, self._auto_saved = None, None
        self._auto_label()

    # ---- firmware update page
    FW_ROWS = (("tx_mcu", "Base processor", False), ("tx_radio", "Base radio chip", True),
               ("rx_mcu", "Headset processor", False), ("rx_radio", "Headset radio chip", True))

    def _page_fw(self, p):
        self._title(p, "Firmware update", "Update your headset from a firmware file on your PC (.afw).")
        c = self.card(p)
        c.pack(fill="x", padx=8, pady=(0, 10))
        ctk.CTkLabel(c, text="⚠  Before you start", font=ctk.CTkFont(size=14, weight="bold"), text_color=WARN
                     ).pack(anchor="w", padx=16, pady=(12, 2))
        ctk.CTkLabel(c, justify="left", wraplength=760, text_color=PAL["text"], text=(
            "• Get the .afw firmware file yourself, for example from your own ASTRO Command Center installation. "
            "This app never downloads firmware and does not include any.\n"
            "• Unofficial tool, use at your own risk. Base on USB in PC mode, headset charged, ON and docked. "
            "Do not unplug anything while it runs.\n"
            "• Radio chips: tested. Processors: tested on one unit, marked experimental. Pairing is never touched.")
                     ).pack(anchor="w", padx=16, pady=(0, 12))

        c = self.card(p)
        c.pack(fill="x", padx=8, pady=(0, 10))
        row = ctk.CTkFrame(c, fg_color="transparent")
        row.pack(fill="x", padx=16, pady=(12, 6))
        self.btn(row, "Choose .afw file…", self._fw_choose, width=150).pack(side="left")
        self.fw_file = ctk.CTkLabel(row, text="No file selected", text_color=PAL["muted"], anchor="w")
        self.fw_file.pack(side="left", padx=12)
        self.fw_notes = ctk.CTkLabel(c, text="", text_color=PAL["muted"], justify="left", anchor="w")
        self.fw_notes.pack(anchor="w", padx=16)
        grid = ctk.CTkFrame(c, fg_color="transparent")
        grid.pack(fill="x", padx=16, pady=(8, 6))
        for col, head in enumerate(("Component", "In file", "Installed", "Status", "Progress")):
            ctk.CTkLabel(grid, text=head.upper(), text_color=PAL["muted"], font=ctk.CTkFont(size=11, weight="bold"),
                         anchor="w", width=(220 if col == 0 else 110)).grid(row=0, column=col, sticky="w", pady=(0, 4))
        self.fw_cells, self.fw_bars = {}, {}
        for r, (key, label, tested) in enumerate(self.FW_ROWS, start=1):
            ctk.CTkLabel(grid, text=label + ("" if tested else "  (experimental)"), anchor="w", width=220,
                         text_color=PAL["text"]).grid(row=r, column=0, sticky="w", pady=2)
            cells = []
            for col in (1, 2, 3):
                l = ctk.CTkLabel(grid, text="—", anchor="w", width=110, text_color=PAL["text"])
                l.grid(row=r, column=col, sticky="w")
                cells.append(l)
            self.fw_cells[key] = cells
            bar = ctk.CTkProgressBar(grid, width=150, height=8, progress_color=self.accent, fg_color=PAL["track"])
            bar.set(0)
            bar.grid(row=r, column=4, sticky="w", padx=(0, 8))
            self.fw_bars[key] = bar
        opts = ctk.CTkFrame(c, fg_color="transparent")
        opts.pack(fill="x", padx=16, pady=(8, 4))
        self.fw_exp = ctk.CTkCheckBox(opts, text="Include processors (experimental)", fg_color=self.accent,
                                      hover_color=darker(self.accent), text_color=PAL["text"],
                                      command=self._fw_refresh)
        self.fw_exp.pack(side="left")
        self.fw_force = ctk.CTkCheckBox(opts, text="Rewrite even if already up to date", fg_color=self.accent,
                                        hover_color=darker(self.accent), text_color=PAL["text"],
                                        command=self._fw_refresh)
        self.fw_force.pack(side="left", padx=20)
        row = ctk.CTkFrame(c, fg_color="transparent")
        row.pack(fill="x", padx=16, pady=(6, 14))
        self.fw_btn = self.btn(row, "Update", self._fw_update, primary=True, width=140)
        self.fw_btn.pack(side="left")
        self.fw_summary = ctk.CTkLabel(row, text="", text_color=PAL["muted"])
        self.fw_summary.pack(side="left", padx=12)
        self.fw_log_btn = ctk.CTkButton(row, text="Show log ▾", width=110, fg_color="transparent",
                                        hover_color=PAL["hover"], text_color=PAL["muted"],
                                        command=lambda: self._fw_toggle_log())
        self.fw_log_btn.pack(side="right")
        self.fw_log = ctk.CTkTextbox(p, height=220, font=ctk.CTkFont(family="Consolas", size=12), corner_radius=12,
                                     fg_color=PAL["card"], text_color=PAL["text"], border_color=PAL["border"],
                                     border_width=1)
        self.fw_log.configure(state="disabled")
        self.fw_log_shown = False
        self.fw_path = None
        self.fw_comps = {}
        auto = self._fw_autodetect()
        if auto:
            self.after(300, lambda: self._fw_load(auto))

    def _fw_toggle_log(self, show=None):
        show = (not self.fw_log_shown) if show is None else show
        if show and not self.fw_log_shown:
            self.fw_log.pack(fill="both", expand=True, padx=8)
        elif not show and self.fw_log_shown:
            self.fw_log.pack_forget()
        self.fw_log_shown = show
        self.fw_log_btn.configure(text="Hide log ▴" if show else "Show log ▾")

    def _fw_progress(self, key, done, total):
        try:
            self.fw_bars[key].set(done / total)
            self.fw_cells[key][2].configure(text=f"writing {100 * done // total}%", text_color=self.accent)
        except (KeyError, tk.TclError):
            pass

    def _fw_autodetect(self):
        import glob
        pats = [os.path.expandvars(r"%LOCALAPPDATA%\Astro Gaming\ASTRO Command Center\Astro A50 Wireless (Mimas)\FW\*.afw"),
                r"C:\Program Files (x86)\Astro Gaming\ASTRO Command Center\assets\forced_fw\*.afw"]
        files = [f for p in pats for f in glob.glob(p)]
        return max(files, key=lambda f: os.path.basename(f)) if files else None

    def _fw_choose(self):
        path = filedialog.askopenfilename(title="Choose an A50 Gen 4 firmware file",
                                          filetypes=[("ASTRO firmware", "*.afw"), ("All files", "*.*")])
        if path:
            self._fw_load(path)

    def _fw_module(self):
        return tool_module("a50_update")

    def run_inline(self, module, argv, out, done):
        """Run a tool's main() inside the app (no Python needed), streaming its output to `out`."""
        self.busy = True

        def finish():
            self.busy = False
            done()

        def work():
            old = sys.argv, sys.stdout, sys.stderr
            sys.argv = [module + ".py"] + argv
            sys.stdout = sys.stderr = _UiWriter(lambda t: self.after(0, out, t))
            try:
                tool_module(module).main()
            except SystemExit as e:
                if e.code not in (None, 0):
                    print(e.code if isinstance(e.code, str) else f"exit code {e.code}")
            except Exception:
                traceback.print_exc()
            finally:
                sys.argv, sys.stdout, sys.stderr = old
                self.after(0, finish)

        threading.Thread(target=work, daemon=True).start()

    def _fw_load(self, path):
        try:
            comps, notes = self._fw_module().read_afw(path)
        except Exception as e:
            messagebox.showerror(APP_NAME, f"This is not a valid A50 Gen 4 firmware file.\n\n{e}")
            return
        if not comps:
            messagebox.showerror(APP_NAME, "No A50 Gen 4 (Mimas) firmware found in this file.")
            return
        self.fw_path, self.fw_comps = path, comps
        self.fw_file.configure(text=os.path.basename(path), text_color=PAL["text"])
        first = [l for l in notes.strip().split("\n\n")[0].splitlines() if l.strip("- ")] if notes else []
        self.fw_notes.configure(text="Release: " + " · ".join(first[1:4]) if len(first) > 1 else "")
        self._fw_refresh()

    def _fw_installed(self):
        if not self.dev:
            return {}
        d = self.dev
        info = self._get(d.base_info)
        hv = self._get(d.headset_version)
        return {"tx_mcu": info[0] if info else None, "tx_radio": self._get(d.base_minor),
                "rx_mcu": hv[0] if hv else None, "rx_radio": hv[1] if hv else None}

    def _fw_plan(self):
        inst, plan = self._fw_installed(), []
        exp, force = bool(self.fw_exp.get()), bool(self.fw_force.get())
        for key, label, tested in self.FW_ROWS:
            if key not in self.fw_comps:
                continue
            fv, iv = self.fw_comps[key][0], inst.get(key)
            if (fv != iv or force) and (tested or exp):
                plan.append(key)
        return inst, plan

    def _fw_refresh(self):
        if not self.fw_comps:
            return
        inst, plan = self._fw_plan()
        for key, label, tested in self.FW_ROWS:
            cells = self.fw_cells[key]
            fv = self.fw_comps.get(key, (None,))[0]
            iv = inst.get(key)
            cells[0].configure(text=str(fv) if fv is not None else "—")
            cells[1].configure(text=str(iv) if iv is not None else "?")
            if key in plan:
                cells[2].configure(text="will update", text_color=self.accent)
            elif fv is not None and fv == iv:
                cells[2].configure(text="up to date", text_color=OK)
            elif not tested and not self.fw_exp.get():
                cells[2].configure(text="experimental", text_color=WARN)
            else:
                cells[2].configure(text="—", text_color=PAL["muted"])
        self.fw_summary.configure(text=f"{len(plan)} component(s) to update" if plan else "Nothing to update")

    def _fw_log_add(self, text):
        try:
            self.fw_log.configure(state="normal")
            self.fw_log.insert("end", text)
            self.fw_log.see("end")
            self.fw_log.configure(state="disabled")
        except tk.TclError:
            pass

    def _fw_update(self):
        if not self.fw_path:
            messagebox.showinfo(APP_NAME, "Choose a .afw firmware file first.")
            return
        inst, plan = self._fw_plan()
        if not plan:
            messagebox.showinfo(APP_NAME, "Nothing to update.")
            return
        names = "\n".join("  • " + label for key, label, _ in self.FW_ROWS if key in plan)
        exp = any(k in ("tx_mcu", "rx_mcu") for k in plan)
        if not messagebox.askyesno(APP_NAME, f"These components will be written:\n\n{names}\n\n"
                                   + ("Includes EXPERIMENTAL processor updates.\n\n" if exp else "")
                                   + "Unofficial tool, use at your own risk. Base in PC mode, headset ON and docked, "
                                     "do not unplug anything.\n\nContinue?"):
            return
        backup = self._auto_backup()
        args = ["update", self.fw_path, "--only", ",".join(plan)]
        if self.fw_force.get():
            args.append("--force")
        if exp:
            args.append("--experimental")
        if self.dev:
            self.dev.close()
            self.dev = None
        self.dot.configure(text="●  Updating", text_color=WARN)
        self.fw_btn.configure(state="disabled")
        self._fw_log_add("\n=== update ===\n")
        if backup:
            self._fw_log_add(f"settings backup: {os.path.basename(backup)}\n")
        for key in plan:
            self.fw_bars[key].set(0)
            self.fw_cells[key][2].configure(text="waiting", text_color=PAL["muted"])
        self.fw_plan_running = plan
        try:
            self._fw_module().PROGRESS = lambda k, d, t: self.after(0, self._fw_progress, k, d, t)
        except Exception:
            pass

        self.run_inline("a50_update", args, self._fw_log_add, self._fw_done)

    def _fw_done(self):
        try:
            self._fw_module().PROGRESS = None
        except Exception:
            pass
        try:
            self.fw_btn.configure(state="normal")
            text = self.fw_log.get("1.0", "end")
            last = text[text.rfind("=== update ==="):]
            bad = ("Traceback" in last or "CHECK" in last
                   or ("Result:" not in last and "Nothing to do" not in last))
        except tk.TclError:
            bad = False
        self.connect()
        self._fw_refresh()
        if bad:
            self._fw_toggle_log(True)
            self._notify("Firmware update finished with problems: check the log.")
            messagebox.showwarning(APP_NAME, "The update reported a problem. Check the log, and export a report from "
                                             "Maintenance if you need help. Don't unplug the base.")
        else:
            self._notify("Firmware update finished.")
            self._set_status("✔ Firmware update finished")

    def _page_tools(self, p):
        self._title(p, "Maintenance", "Repair the Avnera radio chips after a failed firmware update.\n"
                                      "Run Diagnose first. Only repair a chip that is NOT at version 43.")
        c = self.card(p)
        c.pack(fill="x", padx=8, pady=(0, 10))
        row = ctk.CTkFrame(c, fg_color="transparent")
        row.pack(fill="x", padx=16, pady=12)
        self.btn(row, "Diagnose (read-only)", lambda: self._tool("info"), primary=True).pack(side="left", padx=(0, 8))
        self.btn(row, "Export report…", self._report, width=130).pack(side="left", padx=(0, 8))
        for text, action in (("Fix BASE radio chip", "fix-base"), ("Fix HEADSET radio chip", "fix-headset")):
            ctk.CTkButton(row, text=text, fg_color="transparent", border_width=1, border_color=WARN, text_color=WARN,
                          hover_color=PAL["hover"], corner_radius=8,
                          command=lambda a=action: self._tool(a, True)).pack(side="left", padx=8)
        self.log = ctk.CTkTextbox(p, height=320, font=ctk.CTkFont(family="Consolas", size=12), corner_radius=12,
                                  fg_color=PAL["card"], text_color=PAL["text"], border_color=PAL["border"],
                                  border_width=1)
        self.log.pack(fill="both", expand=True, padx=8)
        self.log.configure(state="disabled")

    def _page_settings(self, p):
        self._title(p, "Settings")
        c = self.card(p, "Appearance")
        c.pack(fill="x", padx=8, pady=(0, 10))
        seg = self._seg(c, ["Dark", "Light", "System"], lambda v: self._set("appearance", v), height=34)
        seg.set(self.settings["appearance"])
        seg.pack(anchor="w", padx=16, pady=(6, 14))

        c = self.card(p, "Accent color")
        c.pack(fill="x", padx=8, pady=(0, 10))
        row = ctk.CTkFrame(c, fg_color="transparent")
        row.pack(anchor="w", padx=16, pady=(6, 14))
        for name, col in ACCENTS.items():
            sel = name == self.settings["accent"]
            ctk.CTkButton(row, text="✓" if sel else "", width=38, height=38, corner_radius=19, fg_color=col,
                          hover_color=darker(col), text_color="#0B0D10", border_width=3 if sel else 0,
                          border_color=PAL["text"], command=lambda n=name: self._set("accent", n)).pack(side="left", padx=5)

        c = self.card(p, "Headset look")
        c.pack(fill="x", padx=8, pady=(0, 10))
        row = ctk.CTkFrame(c, fg_color="transparent")
        row.pack(fill="x", padx=16, pady=(6, 6))
        ctk.CTkLabel(row, text="Model / color", width=120, anchor="w", text_color=PAL["text"]).pack(side="left")
        choices = list(self.headsets) + list(COLORWAYS)
        om = ctk.CTkOptionMenu(row, values=choices, width=300, fg_color=PAL["card2"], button_color=self.accent,
                               button_hover_color=darker(self.accent), text_color=PAL["text"],
                               command=lambda v: self._set("colorway", v))
        current = self._current_model()
        om.set(current)
        self.model_menu = om
        om.pack(side="left")
        row = ctk.CTkFrame(c, fg_color="transparent")
        row.pack(fill="x", padx=16, pady=(6, 4))
        ctk.CTkLabel(row, text="Your own photo", width=120, anchor="w", text_color=PAL["text"]).pack(side="left")
        self.btn(row, "Choose photo…", self._choose_photo, width=130).pack(side="left", padx=(0, 6))
        self.btn(row, "Use drawing", lambda: self._set("photo", ""), width=110).pack(side="left")
        note = ("Pictures in %APPDATA%\\A50Control\\headsets appear in the list above (PNG, transparent background). "
                "They stay on your PC."
                if Image else "Install Pillow to use a photo: python -m pip install pillow")
        ctk.CTkLabel(c, text=note, text_color=PAL["muted"]).pack(anchor="w", padx=16, pady=(0, 12))

        c = self.card(p, "Background")
        c.pack(fill="x", padx=8, pady=(0, 10))
        if self.tray_ok:
            sw = ctk.CTkSwitch(c, text="Keep running in the tray when the window is closed", progress_color=self.accent,
                               text_color=PAL["text"],
                               command=lambda: self._set_quiet("close_to_tray", bool(self.tray_sw.get())))
            sw.select() if self.settings.get("close_to_tray", True) else sw.deselect()
            sw.pack(anchor="w", padx=16, pady=(6, 4))
            self.tray_sw = sw
        sw = ctk.CTkSwitch(c, text="Start with Windows" + (" (in the tray)" if self.tray_ok else ""),
                           progress_color=self.accent, text_color=PAL["text"], command=self._toggle_autostart)
        sw.select() if autostart_enabled() else sw.deselect()
        sw.pack(anchor="w", padx=16, pady=4)
        self.auto_sw = sw
        row = ctk.CTkFrame(c, fg_color="transparent")
        row.pack(fill="x", padx=16, pady=(6, 4))
        ctk.CTkLabel(row, text="Low battery alert", width=140, anchor="w", text_color=PAL["text"]).pack(side="left")
        opts = ["Off", "10%", "15%", "20%", "30%"]
        seg = self._seg(row, opts, lambda v: self._set_quiet("low_battery", 0 if v == "Off" else int(v[:-1])))
        lb = int(self.settings.get("low_battery") or 0)
        seg.set(f"{lb}%" if f"{lb}%" in opts else "Off")
        seg.pack(side="left")
        note = ("The tray icon shows the battery level. Right-click it to open or quit the app."
                if self.tray_ok else "Tray icon not available: install it with  python -m pip install pystray")
        ctk.CTkLabel(c, text=note, text_color=PAL["muted"]).pack(anchor="w", padx=16, pady=(2, 12))

        c = self.card(p, "Keyboard shortcuts")
        c.pack(fill="x", padx=8, pady=(0, 10))
        sw = ctk.CTkSwitch(c, text="Use keyboard shortcuts (they work in games too)", progress_color=self.accent,
                           text_color=PAL["text"], command=lambda: self._hotkeys_toggled(bool(self.hk_sw.get())))
        sw.select() if self.settings.get("hotkeys", True) else sw.deselect()
        sw.pack(anchor="w", padx=16, pady=(6, 6))
        self.hk_sw = sw
        grid = ctk.CTkFrame(c, fg_color="transparent")
        grid.pack(anchor="w", padx=16, pady=(0, 6))
        failed = self.hk.failed if self.hk else []
        for r, (name, _, label) in enumerate(hotkeys.SHORTCUTS):
            ctk.CTkLabel(grid, text=label, width=140, anchor="w", font=ctk.CTkFont(family="Consolas", size=12),
                         text_color=PAL["text"]).grid(row=r, column=0, sticky="w")
            ctk.CTkLabel(grid, text=hotkeys.DESCRIPTIONS[name] + ("   (used by another program)" if label in failed else ""),
                         anchor="w", text_color=WARN if label in failed else PAL["muted"]).grid(row=r, column=1, sticky="w")
        ctk.CTkLabel(c, text="A notification confirms each change.", text_color=PAL["muted"]
                     ).pack(anchor="w", padx=16, pady=(0, 12))

        c = self.card(p, "Backup")
        c.pack(fill="x", padx=8, pady=(0, 10))
        row = ctk.CTkFrame(c, fg_color="transparent")
        row.pack(anchor="w", padx=16, pady=(6, 6))
        self.btn(row, "Back up settings…", self._backup, width=150).pack(side="left", padx=(0, 6))
        self.btn(row, "Restore…", self._restore, width=110).pack(side="left", padx=(0, 6))
        self.btn(row, "Open backups folder", lambda: (os.makedirs(BACKUP_DIR, exist_ok=True),
                                                      os.startfile(BACKUP_DIR)), width=160).pack(side="left")
        ctk.CTkLabel(c, text="EQ presets and names, microphone, noise gate, mix. A backup is also made "
                             "automatically before every firmware update or repair (last 10 kept).",
                     text_color=PAL["muted"], wraplength=760, justify="left").pack(anchor="w", padx=16, pady=(0, 12))

        c = self.card(p, "About")
        c.pack(fill="x", padx=8)
        ctk.CTkLabel(c, text=f"{APP_NAME} {APP_VERSION} · open source (MIT) · not affiliated with ASTRO Gaming or "
                             f"Logitech", text_color=PAL["muted"]).pack(anchor="w", padx=16)
        row = ctk.CTkFrame(c, fg_color="transparent")
        row.pack(anchor="w", padx=16, pady=(6, 14))
        self.btn(row, "Project page", lambda: webbrowser.open(REPO_URL), width=120).pack(side="left", padx=(0, 6))
        self.btn(row, "☕ Support the project", lambda: webbrowser.open(DONATE_URL), primary=True,
                 width=180).pack(side="left")

    # ---- headset model picker
    def _models(self):
        return list(self.headsets) + list(COLORWAYS)

    def _current_model(self):
        models = self._models()
        c = self.settings.get("colorway")
        return c if c in models else models[0]

    def _update_model_label(self):
        name = "Your photo" if self.settings.get("photo") else self._current_model()
        self.model_lbl.configure(text=name.replace("Drawing - ", "Drawing · ").replace(" - ", " · "))

    def _cycle_model(self, step):
        models = self._models()
        i = models.index(self._current_model())
        self.settings["colorway"] = models[(i + step) % len(models)]
        self.settings["photo"] = ""
        save_settings(self.settings)
        self._update_model_label()
        self.headset.redraw()
        if getattr(self, "model_menu", None):
            self.model_menu.set(self.settings["colorway"])

    # ---- settings actions
    def _set(self, key, value):
        self.settings[key] = value
        save_settings(self.settings)
        if key == "appearance":
            ctk.set_appearance_mode(value)
        self.build()
        self.after(50, self.load_all)

    def _choose_photo(self):
        if not Image:
            messagebox.showinfo(APP_NAME, "To use a photo, install Pillow:\n\npython -m pip install pillow")
            return
        path = filedialog.askopenfilename(title="Choose a photo of your headset",
                                          filetypes=[("Images", "*.png *.jpg *.jpeg *.webp *.bmp"), ("All files", "*.*")])
        if path:
            self._set("photo", path)

    # ---- device helpers
    def _later(self, key, fn, delay=300):
        if self.loading:
            return
        if key in self._timers:
            self.after_cancel(self._timers[key])
        self._timers[key] = self.after(delay, fn)

    def _set_status(self, text, ok=True):
        self.status.configure(text=text, text_color=PAL["muted"] if ok else WARN)

    def connect(self, quiet=False):
        if self.dev:
            self.dev.close()
            self.dev = None
        if quiet and acc_running():
            return  # never fight ACC for the device in the background
        if not quiet and acc_running():
            messagebox.showwarning(APP_NAME, "ASTRO Command Center is running.\n\nClose it (also from the tray "
                                             "icon) first: two programs talking to the base at the same time is "
                                             "what breaks firmware updates.")
        try:
            self.dev = A50()
        except DeviceError as e:
            self.dot.configure(text="●  Not connected", text_color=BAD)
            self._set_status(str(e), ok=False)
            self._update_tray(None)
            return
        self.dot.configure(text="●  Connected", text_color=OK)
        self.load_all()

    def _do(self, fn, quiet=False):
        if self.loading:
            return None
        if not self.dev:
            self._set_status("Not connected", ok=False)
            return None
        try:
            r = fn()
            if not quiet:
                self._set_status("Applied · not saved yet")
            return True if r is None else r
        except HeadsetUnavailable:
            self._set_status("Headset not reachable: turn it on or dock it", ok=False)
        except DeviceError as e:
            self._set_status(f"Error: {e}", ok=False)
        return None

    def _get(self, fn, default=None):
        try:
            return fn()
        except DeviceError:
            return default

    def _set_slider(self, pair, value):
        if value is None:
            return
        s, lbl = pair
        s.set(value)
        lbl.configure(text=str(value))

    def load_all(self):
        if not self.dev:
            return
        self.loading = True
        try:
            d = self.dev
            self._load_status()
            names = [self._get(lambda q=q: d.preset_name(q)) or f"Preset {q}" for q in EQ_PRESETS]
            self.preset_map = {n: q for n, q in zip(names, EQ_PRESETS)}
            self.preset_seg.configure(values=names)
            active = self._get(d.active_preset, 1)
            self.preset_seg.set(names[EQ_PRESETS.index(active)] if active in EQ_PRESETS else names[0])
            self._load_preset()
            self._set_slider(self.mic, self._get(lambda: d.slider(SLIDER["mic"])))
            self._set_slider(self.side, self._get(lambda: d.slider(SLIDER["sidetone"])))
            g = self._get(d.noise_gate)
            if g is not None and 0 <= g < len(GATE_NAMES):
                self.gate.set(GATE_NAMES[g])
            m = self._get(d.mic_eq)
            if m is not None and 0 <= m < len(MIC_EQ_NAMES):
                self.miceq.set(MIC_EQ_NAMES[m])
            self._set_slider(self.bal, self._get(d.default_balance))
            self._set_slider(self.alert, self._get(d.alert_volume))
            for key, pair in self.stream.items():
                self._set_slider(pair, self._get(lambda k=key: d.slider(SLIDER[k])))
            if getattr(self, "fw_comps", None):
                self._fw_refresh()
            self._set_status("Loaded from headset")
        finally:
            self.loading = False

    def _show_battery(self, bat, st):
        if bat:
            col = BAD if bat[0] <= 15 else WARN if bat[0] <= 30 else self.accent
            self.bat_pct.configure(text=f"{bat[0]}%")
            self.bat_bar.set(bat[0] / 100)
            self.bat_bar.configure(progress_color=col)
            if self.blog.add(bat[0], bat[1]):
                self._draw_bat_chart()
            est = self.blog.estimate(bat[0], bat[1])
            self.bat_info.configure(text=("Charging" if bat[1] else "Not charging") + (f"  ·  {est}" if est else ""))
            self.hdr_bat.configure(text=(" " if self.icon("battery") else "🔋 ") + f"{bat[0]}%" + ("  ⚡" if bat[1] else ""))
        self._update_tray(bat)
        self._check_low_battery(bat)
        if st:
            self.hs_state.configure(text="On the base" if st[0] else "Wireless")
            self.hs_power.configure(text="Headset on" if st[1] else "Headset off")

    def _draw_bat_chart(self):
        cv = getattr(self, "bat_chart", None)
        if cv is None:
            return
        try:
            cv.delete("all")
            w, h = max(cv.winfo_width(), 200), 130
        except tk.TclError:
            return
        cv.configure(bg=self.c("card"))
        left, right, top, bottom = 40, w - 10, 8, h - 20
        now = time.time()
        X = lambda t: left + (right - left) * (1 - (now - t) / 86400)
        Y = lambda pct: bottom - (bottom - top) * pct / 100
        for pct in (0, 50, 100):
            cv.create_line(left, Y(pct), right, Y(pct), fill=self.c("track"), dash=(3, 3) if pct == 50 else ())
            cv.create_text(left - 6, Y(pct), text=f"{pct}%", anchor="e", fill=self.c("muted"), font=("Segoe UI", 8))
        for hrs in (24, 18, 12, 6, 0):
            cv.create_text(X(now - hrs * 3600), h - 4, text="now" if hrs == 0 else f"-{hrs}h", anchor="s",
                           fill=self.c("muted"), font=("Segoe UI", 8))
        rows = self.blog.history(24)
        if len(rows) < 2:
            cv.create_text((left + right) / 2, (top + bottom) / 2, fill=self.c("muted"), font=("Segoe UI", 10),
                           text="The chart fills in as you use the headset (readings stay on this PC).")
        else:
            pts = rows + [(now, rows[-1][1], rows[-1][2])]
            for (t0, p0, c0), (t1, p1, _) in zip(pts, pts[1:]):
                cv.create_line(X(t0), Y(p0), X(t1), Y(p1), fill=OK if c0 else self.accent, width=2)
        typ = self.blog.typical_runtime()
        try:
            self.bat_typ.configure(text=("Typical full charge: ≈ " + (f"{typ:.0f} h" if typ >= 2 else f"{typ * 60:.0f} min")
                                         + " of use.  " if typ else "") + "Green = charging.")
        except tk.TclError:
            pass

    def _load_status(self):
        d = self.dev
        self._show_battery(self._get(d.battery), self._get(d.headset_status))
        info, bmin, hv = self._get(d.base_info), self._get(d.base_minor), self._get(d.headset_version)
        base = f"{info[0]}.{bmin}" if info and bmin is not None else (f"{info[0]}.?" if info else "—")
        head = f"{hv[0]}.{hv[1]}" if hv else "not reachable"
        self.fw_lbl.configure(text=f"Base station   {base}\nHeadset          {head}" +
                                   (f"\nBase build       {info[1]}" if info else ""))
        cb = self._get(d.balance)
        if cb is not None:
            self.curbal.configure(text=f"Current balance: {cb}  (changes with the headset buttons)")
        if bmin == 43 and hv and hv[1] == 43:
            self.health.configure(text="✔  Radio chips OK (43 / 43)", text_color=OK)
        elif bmin is None or bmin != 43 or (hv and hv[1] != 43):
            self.health.configure(text="⚠  Radio chip problem: open Maintenance", text_color=WARN)
        else:
            self.health.configure(text="Headset not reachable", text_color=PAL["muted"])

    def _load_preset(self):
        name = self.preset_seg.get()
        p = self.preset_map.get(name, 1)
        self.pname.delete(0, "end")
        self.pname.insert(0, name)
        gains = self._get(lambda: self.dev.preset_gain(p))
        freqs = []
        for i in range(5):
            b = self._get(lambda i=i: self.dev.preset_band(p, i + 1))
            freqs.append(b[0] if b else None)
        self.curve.set(gains, freqs)

    def _preset_changed(self, name):
        if self.loading:
            return
        p = self.preset_map.get(name, 1)
        self._do(lambda: self.dev.set_active_preset(p))
        self.loading = True
        try:
            self._load_preset()
        finally:
            self.loading = False

    def _apply_eq(self, gains):
        p = self.preset_map.get(self.preset_seg.get(), 1)
        self._do(lambda: self.dev.set_preset_gain(p, gains))

    def _flat(self):
        self.curve.set([0] * 5)
        self._apply_eq([0] * 5)

    def _rename(self):
        old = self.preset_seg.get()
        p = self.preset_map.get(old, 1)
        name = self.pname.get().strip()[:20]
        if name and name != old and self._do(lambda: self.dev.set_preset_name(p, name)):
            self.preset_map = {(name if n == old else n): q for n, q in self.preset_map.items()}
            self.preset_seg.configure(values=list(self.preset_map))
            self.preset_seg.set(name)

    def save(self):
        if self.dev and self._do(self.dev.save_values, quiet=True):
            self._set_status("✔ Saved to headset")

    def _poll(self):
        self._poll_n += 1
        try:
            if self.busy:
                pass
            elif self.dev and not self.loading and not self.dev.lock.locked():
                self._show_battery(self._get(self.dev.battery), self._get(self.dev.headset_status))
                self._auto_switch()
            elif not self.dev and self._poll_n % 2 == 0:
                self.connect(quiet=True)  # base unplugged/replugged, or ACC closed
        except tk.TclError:
            pass
        except Exception:  # base unplugged: drop the handle, reconnect later
            if self.dev:
                self.dev.close()
                self.dev = None
            try:
                self.dot.configure(text="●  Not connected", text_color=BAD)
            except tk.TclError:
                pass
            self._update_tray(None)
        self.after(5000, self._poll)

    # ---- tray, background and single instance
    def _listen_single_instance(self):
        try:
            srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            srv.bind(("127.0.0.1", SINGLE_PORT))
            srv.listen(2)
        except OSError:
            return
        self._srv = srv

        def serve():
            while True:
                try:
                    c, _ = srv.accept()
                except OSError:
                    break
                try:
                    c.settimeout(2)
                    msg = c.recv(64).decode(errors="ignore").split()
                    leave = bool(msg) and (msg[0] == "replace" or (len(msg) > 1 and msg[1] != APP_VERSION))
                    if leave and not self.busy:
                        c.sendall(b"bye")
                        self.after(0, self._quit)
                    else:
                        c.sendall(b"shown")
                        self.after(0, self._show_window)
                except OSError:
                    pass
                finally:
                    c.close()

        threading.Thread(target=serve, daemon=True).start()

    def _start_tray(self):
        if not (pystray and Image):
            return
        M = pystray.MenuItem

        def ui(fn):
            def call(icon, item):
                try:
                    self.after(0, fn)
                except Exception:  # the window is gone: don't stay alive as an orphan tray icon
                    hard_exit(icon)
            return call

        menu = pystray.Menu(
            M("Open A50 Control", ui(self._show_window), default=True),
            M(lambda it: self._tray_text(), None, enabled=False),
            pystray.Menu.SEPARATOR,
            M("Start with Windows", ui(self._toggle_autostart), checked=lambda it: autostart_enabled()),
            M("Quit", ui(self._quit)))
        try:
            self.tray = pystray.Icon("A50Control", tray_image(None, False, self.accent), APP_NAME, menu)
            self.tray.run_detached()
        except Exception:
            traceback.print_exc()
            self.tray = None

    def _start_hotkeys(self):
        try:
            self.hk = hotkeys.Hotkeys(lambda a: self.after(0, self._hotkey, a)).start()
        except Exception:
            traceback.print_exc()
            self.hk = None

    def _hotkeys_toggled(self, on):
        self._set_quiet("hotkeys", on)
        if on and not self.hk:
            self._start_hotkeys()
        elif not on and self.hk:
            self.hk.stop()
            self.hk = None

    def _hotkey(self, action):
        if not self.dev or self.busy:
            self._notify("Headset not connected")
            return
        if action.startswith("preset"):
            slot = int(action[-1])
            if self._do(lambda: self.dev.set_active_preset(slot), quiet=True):
                name = next((n for n, q in getattr(self, "preset_map", {}).items() if q == slot), f"Preset {slot}")
                try:
                    self.loading = True
                    self.preset_seg.set(name)
                    self._load_preset()
                except (AttributeError, tk.TclError):
                    pass
                finally:
                    self.loading = False
                self._notify(f"EQ: {name}")
        elif action == "next_profile":
            allp = self._profiles()
            self._hk_prof = (self._hk_prof + 1) % len(allp)
            x = allp[self._hk_prof]
            if self._apply_gains(x["gains"], f"'{x['name']}'"):
                m = self._apply_scene_mic(x)
                self._notify(f"Profile: {x['name']}" + (f" · mic: {m['name']}" if m else ""))
        elif action == "next_mic":
            mics = prof.mic_all(self.puser)
            self._hk_mic = (self._hk_mic + 1) % len(mics)
            self._mic_apply(mics[self._hk_mic])
            self._notify(f"Mic: {mics[self._hk_mic]['name']}")
        elif action == "battery":
            bat = self._get(self.dev.battery)
            if bat:
                est = self.blog.estimate(bat[0], bat[1])
                self._notify(f"Battery {bat[0]}%" + (" (charging)" if bat[1] else "") + (f" · {est}" if est else ""))
            else:
                self._notify("Battery: headset not reachable")

    def _tray_text(self):
        b = self._bat_state
        if not b or b == "init":
            return "Headset: not connected"
        est = self.blog.estimate(b[0], b[1])
        return f"Battery: {b[0]}%" + ("  (charging)" if b[1] else "") + (f"  {est}" if est else "")

    def _update_tray(self, bat):
        state = (bat[0], bat[1]) if bat else None
        if not self.tray or state == self._bat_state:
            self._bat_state = state
            return
        self._bat_state = state
        try:
            self.tray.icon = tray_image(bat[0] if bat else None, bat[1] if bat else False, self.accent)
            self.tray.title = f"{APP_NAME} · " + (f"{bat[0]}%" + (" charging" if bat[1] else "")
                                                   if bat else "not connected")
            self.tray.update_menu()
        except Exception:
            pass

    def _check_low_battery(self, bat):
        limit = int(self.settings.get("low_battery") or 0)
        if not bat or not limit:
            return
        if bat[0] <= limit and not bat[1]:
            if not self._low_warned:
                self._low_warned = True
                self._notify(f"Headset battery at {bat[0]}%. Put it on the base to charge.")
        elif bat[1] or bat[0] > limit + 5:
            self._low_warned = False

    def _notify(self, text):
        if self.tray:
            try:
                self.tray.notify(text, APP_NAME)
            except Exception:
                pass

    def _show_window(self):
        self.deiconify()
        self.state("normal")
        self.lift()
        self.attributes("-topmost", True)
        self.after(200, lambda: self.attributes("-topmost", False))
        self.focus_force()

    def _close(self):
        if self.tray and self.settings.get("close_to_tray", True) and not self.busy:
            self.withdraw()
            if not self._tray_note:
                self._tray_note = True
                self._notify("Still running in the tray. Right-click the icon to quit.")
        elif self.busy:
            messagebox.showwarning(APP_NAME, "A firmware or repair job is running. Wait until it finishes.")
        else:
            self._quit()

    def _toggle_autostart(self):
        try:
            set_autostart(not autostart_enabled())
        except Exception as e:
            messagebox.showerror(APP_NAME, f"Could not change the Windows startup setting.\n\n{e}")
        if self.tray:
            self.tray.update_menu()
        if getattr(self, "auto_sw", None):
            try:
                self.auto_sw.select() if autostart_enabled() else self.auto_sw.deselect()
            except tk.TclError:
                pass

    def _set_quiet(self, key, value):
        """Save a setting that doesn't need the interface to be rebuilt."""
        self.settings[key] = value
        save_settings(self.settings)

    # ---- backup / restore
    def _snapshot_to(self, path):
        data = {"app": APP_NAME, "version": APP_VERSION, "created": time.strftime("%Y-%m-%d %H:%M:%S"),
                "settings": self.dev.snapshot()}
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    def _auto_backup(self):
        """Saved before every firmware/repair job. Keeps the last 10."""
        if not self.dev:
            return None
        try:
            path = os.path.join(BACKUP_DIR, time.strftime("auto_%Y%m%d_%H%M%S.json"))
            self._snapshot_to(path)
            for old in sorted(glob.glob(os.path.join(BACKUP_DIR, "auto_*.json")))[:-10]:
                os.remove(old)
            return path
        except Exception:
            return None

    def _backup(self):
        if not self.dev:
            messagebox.showinfo(APP_NAME, "Connect the base station first.")
            return
        os.makedirs(BACKUP_DIR, exist_ok=True)
        path = filedialog.asksaveasfilename(title="Save settings backup", defaultextension=".json",
                                            initialdir=BACKUP_DIR, initialfile=time.strftime("a50_settings_%Y%m%d.json"),
                                            filetypes=[("A50 Control backup", "*.json")])
        if not path:
            return
        try:
            self._snapshot_to(path)
            self._set_status(f"✔ Backup saved: {os.path.basename(path)}")
        except Exception as e:
            messagebox.showerror(APP_NAME, f"Backup failed.\n\n{e}")

    def _restore(self):
        if not self.dev:
            messagebox.showinfo(APP_NAME, "Connect the base station first.")
            return
        os.makedirs(BACKUP_DIR, exist_ok=True)
        path = filedialog.askopenfilename(title="Restore settings backup", initialdir=BACKUP_DIR,
                                          filetypes=[("A50 Control backup", "*.json"), ("All files", "*.*")])
        if not path:
            return
        try:
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
            snap = data.get("settings", data)
            if not isinstance(snap, dict) or "presets" not in snap:
                raise ValueError("not an A50 Control backup")
        except Exception as e:
            messagebox.showerror(APP_NAME, f"This file can't be restored.\n\n{e}")
            return
        when = data.get("created", "unknown date")
        if not messagebox.askyesno(APP_NAME, f"Restore settings from\n{os.path.basename(path)} ({when})?\n\n"
                                             "Your current EQ, microphone and mix settings will be replaced."):
            return
        try:
            failed = self.dev.restore(snap)
        except DeviceError as e:
            messagebox.showerror(APP_NAME, f"Restore failed.\n\n{e}")
            return
        self.load_all()
        note = f"\n\nNot restored: {', '.join(failed)}" if failed else ""
        if messagebox.askyesno(APP_NAME, f"Settings restored.{note}\n\nSave them to the headset now, so they "
                                         "stay after power-off?"):
            self.save()

    # ---- diagnostic report
    def _report(self):
        path = filedialog.asksaveasfilename(
            title="Save diagnostic report", defaultextension=".txt",
            initialdir=os.path.join(os.path.expanduser("~"), "Desktop"),
            initialfile=time.strftime("A50_report_%Y%m%d_%H%M.txt"), filetypes=[("Text file", "*.txt")])
        if not path:
            return
        L = []
        L.append(f"{APP_NAME} {APP_VERSION} - diagnostic report - {time.strftime('%Y-%m-%d %H:%M:%S')}")
        L.append(f"Windows: {platform.platform()} | Python {platform.python_version()} | "
                 f"{'exe' if FROZEN else 'source'}")
        L.append(f"ACC running: {acc_running()} | ACC installed: "
                 f"{os.path.isdir(r'C:\Program Files (x86)\Astro Gaming\ASTRO Command Center')}")
        try:
            import pywinusb.hid as hid
            pids = sorted({f"9886:{x.product_id:04X}" for x in hid.HidDeviceFilter(vendor_id=0x9886).get_devices()})
            L.append("USB devices: " + (", ".join(pids) or "none") + "   (002C = normal, 002A = base stuck in update mode)")
        except Exception as e:
            L.append(f"USB devices: error {e}")
        L.append("")
        L.append("== Device ==")
        if self.dev:
            d = self.dev
            for label, fn in (("Base processor (version, build)", d.base_info), ("Base radio chip", d.base_minor),
                              ("Headset (processor, radio chip)", d.headset_version),
                              ("Battery (%, charging)", d.battery), ("Headset (docked, on)", d.headset_status)):
                try:
                    v = fn()
                except DeviceError as e:
                    v = f"error: {e}"
                L.append(f"{label}: {v}")
        else:
            L.append("Base station not connected" + (" (job running)" if self.busy else ""))
        L.append("")
        L.append("== ASTRO Command Center log (errors only, last 40) ==")
        logdir = os.path.expandvars(r"%LOCALAPPDATA%\Astro Gaming\ASTRO Command Center\Logs")
        files = [f for f in glob.glob(os.path.join(logdir, "*")) if os.path.isfile(f)
                 and "acc_guard" not in os.path.basename(f).lower()]
        if files:
            last = max(files, key=os.path.getmtime)
            L.append(f"File: {os.path.basename(last)}")
            try:
                with open(last, encoding="utf-8", errors="replace") as f:
                    rows = f.read().splitlines()
                errs = [r for r in rows if any(k in r for k in ("ERROR", "Error", "error", "invalid", "TIMEOUT"))]
                L.extend(errs[-40:] or ["(no errors found)"])
            except Exception as e:
                L.append(f"(can't read: {e})")
        else:
            L.append("(no ACC log found)")
        for title, box in (("Maintenance log", getattr(self, "log", None)), ("Firmware log", getattr(self, "fw_log", None))):
            try:
                text = box.get("1.0", "end").strip() if box else ""
            except tk.TclError:
                text = ""
            if text:
                L.extend(["", f"== {title} ==", text[-6000:]])
        report = "\n".join(L)
        home, user = os.path.expanduser("~"), os.environ.get("USERNAME", "")
        report = report.replace(home, "%USERPROFILE%")
        if len(user) > 2:
            report = report.replace(user, "<user>")
        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write(report + "\n")
        except Exception as e:
            messagebox.showerror(APP_NAME, f"Could not save the report.\n\n{e}")
            return
        if messagebox.askyesno(APP_NAME, "Report saved. Attach it to a GitHub issue or a Reddit message when you "
                                         "ask for help (your Windows user name is removed).\n\nOpen the folder?"):
            try:
                os.startfile(os.path.dirname(path))
            except Exception:
                pass

    # ---- maintenance
    def _log(self, text):
        try:
            self.log.configure(state="normal")
            self.log.insert("end", text)
            self.log.see("end")
            self.log.configure(state="disabled")
        except tk.TclError:
            pass

    def _tool(self, action, dangerous=False):
        if dangerous and not messagebox.askyesno(
                APP_NAME, "This rewrites a radio chip of your device with the official firmware.\n\n"
                          "Unofficial, use at your own risk. Only do this if Diagnose shows that chip "
                          "is NOT at version 43.\n\nHeadset on and docked, do not unplug anything.\n\nContinue?"):
            return
        backup = self._auto_backup() if dangerous else None
        if self.dev:
            self.dev.close()
            self.dev = None
        self.dot.configure(text="●  Busy", text_color=WARN)
        self._log(f"\n=== {action} ===\n")
        if backup:
            self._log(f"settings backup: {os.path.basename(backup)}\n")

        self.run_inline("a50_tool", [action], self._log, self.connect)

    def _quit(self):
        if self.busy:
            messagebox.showwarning(APP_NAME, "A firmware or repair job is running. Wait until it finishes.")
            self._show_window()
            return
        if self._auto:
            self._auto_restore()  # don't leave a game profile on the headset
        if getattr(self, "hk", None):
            self.hk.stop()
        if getattr(self, "mt_job", None):
            self.mt_job.stop()
        if self.tray:
            try:
                self.tray.stop()
            except Exception:
                pass
        if getattr(self, "_srv", None):
            try:
                self._srv.close()
            except OSError:
                pass
        if self.dev:
            self.dev.close()
        self.destroy()


def hard_exit(icon=None, code=0):
    """Stop the tray icon and end the process, whatever threads are still running."""
    try:
        if icon:
            icon.stop()
    except Exception:
        pass
    try:
        sys.stdout.flush()
        sys.stderr.flush()
    except Exception:
        pass
    os._exit(code)


if __name__ == "__main__":
    if other_instance_running():
        sys.exit(0)
    app = None
    try:
        app = App()
        app.mainloop()
    except Exception:
        traceback.print_exc()
        try:
            messagebox.showerror(APP_NAME, "A50 Control stopped because of an error.\n\n"
                                 + traceback.format_exc(limit=3) + f"\nDetails: {ERROR_LOG}")
        except Exception:
            pass
        hard_exit(getattr(app, "tray", None), 1)
    hard_exit(getattr(app, "tray", None), 0)
