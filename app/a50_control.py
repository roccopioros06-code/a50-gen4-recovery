"""
A50 Control - an open-source replacement for ASTRO Command Center (ASTRO A50 Gen 4).

Dark/light UI built with CustomTkinter: icon rail, headset view with selectable colorways (original
drawing) or your own photo, EQ curve with draggable points, microphone, mix, maintenance, settings.
If CustomTkinter is missing, the classic UI is started instead.

Close ASTRO Command Center while using this app. USE AT YOUR OWN RISK.
Not affiliated with ASTRO Gaming or Logitech. No ASTRO/Logitech images or logos are included.
"""
import glob
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
    "bg": ("#F3F4F6", "#0E0F12"),
    "rail": ("#E5E7EB", "#08090B"),
    "card": ("#FFFFFF", "#15171C"),
    "border": ("#E2E4E8", "#1F232A"),
    "text": ("#111318", "#E6E8EB"),
    "muted": ("#6B7280", "#7C8594"),
    "track": ("#E5E7EB", "#22262D"),
    "hover": ("#D9DCE1", "#1B1E24"),
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
            "close_to_tray": True, "low_battery": 15}
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
    """5-band EQ as a smooth curve with draggable points (-7..+7 dB)."""

    def __init__(self, master, app, on_change, **kw):
        super().__init__(master, highlightthickness=0, bd=0, height=280, **kw)
        self.app, self.on_change = app, on_change
        self.gains = [0] * 5
        self.freqs = [None] * 5
        self.drag = None
        self.bind("<Configure>", lambda e: self.redraw())
        self.bind("<Button-1>", self._press)
        self.bind("<B1-Motion>", self._move)
        self.bind("<ButtonRelease-1>", self._release)

    def _geom(self):
        w, h = max(self.winfo_width(), 200), max(self.winfo_height(), 120)
        left, right, top, bottom = 56, w - 30, 30, h - 40
        xs = [left + (right - left) * (i + 0.5) / 5 for i in range(5)]
        return w, h, left, right, top, bottom, xs

    def _y(self, g, top, bottom):
        return top + (7 - g) / 14 * (bottom - top)

    def redraw(self):
        self.delete("all")
        w, h, left, right, top, bottom, xs = self._geom()
        acc, muted, track = self.app.accent, self.app.c("muted"), self.app.c("track")
        self.configure(bg=self.app.c("card"))
        for g in (7, 0, -7):
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
        for i, (x, y) in enumerate(pts):
            r = 9 if self.drag == i else 7
            self.create_oval(x - r, y - r, x + r, y + r, fill=self.app.c("card"), outline=acc, width=3)
            self.create_text(x, y - 18, text=f"{self.gains[i]:+d}", fill=self.app.c("text"),
                             font=("Segoe UI", 10, "bold"))
            self.create_text(x, bottom + 22, text=fmt_freq(self.freqs[i]) if self.freqs[i] else f"Band {i + 1}",
                             fill=muted, font=("Segoe UI", 9))

    def set(self, gains=None, freqs=None):
        if gains:
            self.gains = [max(-7, min(7, int(g))) for g in gains]
        if freqs:
            self.freqs = freqs
        self.redraw()

    def _press(self, e):
        *_, top, bottom, xs = self._geom()
        best = min(range(5), key=lambda i: abs(xs[i] - e.x))
        if abs(xs[best] - e.x) < 40:
            self.drag = best
            self._move(e)

    def _move(self, e):
        if self.drag is None:
            return
        *_, top, bottom, xs = self._geom()
        g = round(7 - (e.y - top) / (bottom - top) * 14)
        g = max(-7, min(7, g))
        if True:
            self.gains[self.drag] = g
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
        self._start_tray()          # before build(): the Settings page checks self.tray
        self.build()
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
        f = ctk.CTkFrame(master, fg_color=PAL["card"], border_color=PAL["border"], border_width=1, corner_radius=12)
        if title:
            ctk.CTkLabel(f, text=title.upper(), text_color=PAL["muted"],
                         font=ctk.CTkFont(size=11, weight="bold")).pack(anchor="w", padx=16, pady=(12, 2))
        return f

    def btn(self, master, text, cmd, primary=False, **kw):
        if primary:
            return ctk.CTkButton(master, text=text, command=cmd, fg_color=self.accent, hover_color=darker(self.accent),
                                 text_color="#0B0D10", font=ctk.CTkFont(weight="bold"), corner_radius=8, **kw)
        return ctk.CTkButton(master, text=text, command=cmd, fg_color="transparent", border_width=1,
                             border_color=PAL["border"], text_color=PAL["text"], hover_color=PAL["hover"],
                             corner_radius=8, **kw)

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
                              ("Firmware", self._page_fw),
                              ("Maintenance", self._page_tools), ("Settings", self._page_settings)):
            frame = ctk.CTkScrollableFrame(main, fg_color="transparent")
            builder(frame)
            self.pages[name] = frame
        self.show(self.page)

    NAV = (("Home", "headset"), ("Equalizer", "eq"), ("Microphone", "mic"), ("Mix", "mix"),
           ("Firmware", "firmware"), ("Maintenance", "tools"))

    def _rail(self):
        expanded = self.settings.get("sidebar") == "expanded"
        rail = ctk.CTkFrame(self, width=210 if expanded else 68, corner_radius=0, fg_color=PAL["rail"])
        rail.grid(row=0, column=0, sticky="nsw")
        rail.grid_propagate(False)
        rail.pack_propagate(False)
        top = ctk.CTkFrame(rail, fg_color="transparent")
        top.pack(fill="x", padx=10, pady=(14, 18))
        ctk.CTkButton(top, text="", image=self.icon("menu"), width=44, height=40, corner_radius=10,
                      fg_color="transparent", hover_color=PAL["hover"],
                      command=self._toggle_sidebar).pack(side="left")
        if expanded:
            ctk.CTkLabel(top, text="A50 Control", font=ctk.CTkFont(size=15, weight="bold"),
                         text_color=PAL["text"]).pack(side="left", padx=6)
        self.nav = {}
        for name, ic in self.NAV:
            self._rail_btn(rail, name, ic, expanded).pack(fill="x", padx=10, pady=3)
        self._rail_btn(rail, "Settings", "gear", expanded).pack(side="bottom", fill="x", padx=10, pady=14)

    def _rail_btn(self, rail, name, ic, expanded):
        img = self.icon(ic)
        fallback = {"headset": "🎧", "eq": "≋", "mic": "🎙", "mix": "⇄", "tools": "🛠", "gear": "⚙",
                    "firmware": "⬆"}[ic]
        text = (f"  {name}" if img else f"{fallback}  {name}") if expanded else ("" if img else fallback)
        b = ctk.CTkButton(rail, text=text, image=img, compound="left", anchor="w" if expanded else "center",
                          width=190 if expanded else 48, height=44, corner_radius=10, fg_color="transparent",
                          hover_color=PAL["hover"], text_color=PAL["muted"], font=ctk.CTkFont(size=14),
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
        h = ctk.CTkFrame(main, fg_color="transparent")
        h.grid(row=0, column=0, sticky="ew", padx=26, pady=(18, 6))
        left = ctk.CTkFrame(h, fg_color="transparent")
        left.pack(side="left")
        ctk.CTkLabel(left, text="A 5 0   C O N T R O L", text_color=PAL["muted"],
                     font=ctk.CTkFont(size=11)).pack(anchor="w")
        ctk.CTkLabel(left, text="A50 Wireless Gen 4", font=ctk.CTkFont(size=22, weight="bold"),
                     text_color=PAL["text"]).pack(anchor="w")
        right = ctk.CTkFrame(h, fg_color="transparent")
        right.pack(side="right")
        self.dot = ctk.CTkLabel(right, text="●  Not connected", text_color=BAD)
        self.dot.pack(side="left", padx=10)
        self.hdr_bat = ctk.CTkLabel(right, text=" —" if self.icon("battery") else "🔋 —", image=self.icon("battery"),
                                    compound="left", text_color=PAL["text"], font=ctk.CTkFont(size=13))
        self.hdr_bat.pack(side="left", padx=10)
        self.btn(right, "Reload", self.load_all, width=96, image=self.icon("refresh", size=16),
                 compound="left").pack(side="left", padx=4)
        b = self.btn(right, "Save to headset", self.save, primary=True, width=150)
        b.pack(side="left", padx=4)
        self.status = ctk.CTkLabel(main, text="", text_color=PAL["muted"], anchor="w")
        self.status.grid(row=2, column=0, sticky="ew", padx=28, pady=(0, 8))

    def show(self, name):
        if name not in self.pages:
            name = "Home"
        self.page = name
        for n, f in self.pages.items():
            f.grid_forget()
            b = self.nav[n]
            b.configure(fg_color="transparent", text_color=PAL["muted"])
            if self.icon(b._icon_name):
                b.configure(image=self.icon(b._icon_name))
        self.pages[name].grid(row=1, column=0, sticky="nsew", padx=18)
        b = self.nav[name]
        b.configure(fg_color=PAL["hover"], text_color=self.accent)
        if self.icon(b._icon_name, active=True):
            b.configure(image=self.icon(b._icon_name, active=True))
        if name == "Home":
            self.after(50, self.headset.redraw)
        if name == "Equalizer":
            self.after(50, self.curve.redraw)

    def _title(self, p, text, sub=None):
        ctk.CTkLabel(p, text=text, font=ctk.CTkFont(size=20, weight="bold"), text_color=PAL["text"]).pack(anchor="w", padx=8)
        if sub:
            ctk.CTkLabel(p, text=sub, text_color=PAL["muted"], justify="left").pack(anchor="w", padx=8, pady=(0, 10))

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
                                      selected_hover_color=darker(self.accent), unselected_color=PAL["card"],
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

    def _page_eq(self, p):
        self._title(p, "Equalizer", "Drag the points up or down (-7 to +7 dB). Changes apply when you release.")
        c = self.card(p)
        c.pack(fill="x", padx=8, pady=(0, 10))
        row = ctk.CTkFrame(c, fg_color="transparent")
        row.pack(fill="x", padx=16, pady=12)
        self.preset_seg = self._seg(row, ["Preset 1", "Preset 2", "Preset 3"], self._preset_changed, height=34)
        self.preset_seg.pack(side="left")
        self.pname = ctk.CTkEntry(row, width=170, placeholder_text="Preset name", fg_color=PAL["bg"],
                                  border_color=PAL["border"], text_color=PAL["text"])
        self.pname.pack(side="left", padx=(18, 6))
        self.btn(row, "Rename", self._rename, width=80).pack(side="left")
        self.btn(row, "Flat", self._flat, width=70).pack(side="right")
        c = self.card(p)
        c.pack(fill="both", expand=True, padx=8)
        self.curve = EQCurve(c, self, self._apply_eq)
        self.curve.pack(fill="both", expand=True, padx=10, pady=10)

    def _page_mic(self, p):
        self._title(p, "Microphone", "Mic level, sidetone (hear your own voice) and noise gate.")
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
        ctk.CTkLabel(c, text="Streaming = most open  ·  Tournament = strongest background noise reduction",
                     text_color=PAL["muted"]).pack(anchor="w", padx=16, pady=(0, 12))
        c = self.card(p, "Mic EQ (advanced)")
        c.pack(fill="x", padx=8)
        self.miceq = self._seg(c, MIC_EQ_NAMES, lambda v: self._do(lambda: self.dev.set_mic_eq(MIC_EQ_NAMES.index(v))),
                               height=32)
        self.miceq.pack(anchor="w", padx=16, pady=(6, 14))

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
        om = ctk.CTkOptionMenu(row, values=choices, width=300, fg_color=PAL["bg"], button_color=self.accent,
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
        if self.tray:
            sw = ctk.CTkSwitch(c, text="Keep running in the tray when the window is closed", progress_color=self.accent,
                               text_color=PAL["text"],
                               command=lambda: self._set_quiet("close_to_tray", bool(self.tray_sw.get())))
            sw.select() if self.settings.get("close_to_tray", True) else sw.deselect()
            sw.pack(anchor="w", padx=16, pady=(6, 4))
            self.tray_sw = sw
        sw = ctk.CTkSwitch(c, text="Start with Windows" + (" (in the tray)" if self.tray else ""),
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
                if self.tray else "Tray icon not available: install it with  python -m pip install pystray")
        ctk.CTkLabel(c, text=note, text_color=PAL["muted"]).pack(anchor="w", padx=16, pady=(2, 12))

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
            self.bat_info.configure(text="Charging" if bat[1] else "Not charging")
            self.hdr_bat.configure(text=(" " if self.icon("battery") else "🔋 ") + f"{bat[0]}%" + ("  ⚡" if bat[1] else ""))
        self._update_tray(bat)
        self._check_low_battery(bat)
        if st:
            self.hs_state.configure(text="On the base" if st[0] else "Wireless")
            self.hs_power.configure(text="Headset on" if st[1] else "Headset off")

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
        menu = pystray.Menu(
            M("Open A50 Control", lambda i, it: self.after(0, self._show_window), default=True),
            M(lambda it: self._tray_text(), None, enabled=False),
            pystray.Menu.SEPARATOR,
            M("Start with Windows", lambda i, it: self.after(0, self._toggle_autostart),
              checked=lambda it: autostart_enabled()),
            M("Quit", lambda i, it: self.after(0, self._quit)))
        try:
            self.tray = pystray.Icon("A50Control", tray_image(None, False, self.accent), APP_NAME, menu)
            self.tray.run_detached()
        except Exception:
            traceback.print_exc()
            self.tray = None

    def _tray_text(self):
        b = self._bat_state
        if not b or b == "init":
            return "Headset: not connected"
        return f"Battery: {b[0]}%" + ("  (charging)" if b[1] else "")

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


if __name__ == "__main__":
    if other_instance_running():
        sys.exit(0)
    App().mainloop()
