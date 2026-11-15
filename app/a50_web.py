"""A50 Control - the app with the new interface.

The window is drawn with HTML/CSS (web/ folder) inside Microsoft Edge in app mode (no address bar, already on
Windows 10/11). This file is the bridge: a tiny server on 127.0.0.1 only, protected by a random token, that the
window calls to talk to the headset. All the device code (a50_device, tools, profiles, mic test...) is unchanged.
"""
import base64
import glob
import json
import os
import platform
import secrets
import socket
import subprocess
import sys
import tempfile
import threading
import time
import traceback
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse

FROZEN = getattr(sys, "frozen", False)
APP_DIR = os.path.dirname(sys.executable if FROZEN else os.path.abspath(__file__))
RES_DIR = getattr(sys, "_MEIPASS", APP_DIR)
WEB_DIR = os.path.join(RES_DIR, "web")
DATA_DIR = os.path.join(os.environ.get("APPDATA", os.path.expanduser("~")), "A50Control")
os.makedirs(DATA_DIR, exist_ok=True)
ERROR_LOG = os.path.join(DATA_DIR, "a50_control_error.log")
if sys.stderr is None or sys.stdout is None:  # windowed exe / pythonw: keep errors in a file
    sys.stderr = sys.stdout = open(ERROR_LOG, "w", encoding="utf-8")

from a50_device import (A50, APP_NAME, APP_VERSION, DONATE_URL, REPO_URL, SLIDER,  # noqa: E402
                        DeviceError, HeadsetUnavailable, acc_running, find_repair_tool)
import apo  # noqa: E402
import battery  # noqa: E402
import hotkeys  # noqa: E402
import mic_test  # noqa: E402
import profiles as prof  # noqa: E402

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    Image = ImageDraw = ImageFont = None
try:
    import pystray
except Exception:
    pystray = None

SETTINGS_FILE = os.path.join(DATA_DIR, "settings.json")
BACKUP_DIR = os.path.join(DATA_DIR, "backups")
SINGLE_PORT = 47650
RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
GATES = ["Streaming", "Night", "Home", "Tournament"]
DEFAULTS = {"theme": "dark", "colors": {"app": "#00B4FF", "shell": "#1C2029", "hacc": "#00B4FF", "cush": "#0D0F14"},
            "close_to_tray": True, "low_battery": 15, "hotkeys": True}
FW_ROWS = (("tx_mcu", "Base processor", False), ("tx_radio", "Base radio chip", True),
           ("rx_mcu", "Headset processor", False), ("rx_radio", "Headset radio chip", True))
URLS = {"donate": DONATE_URL, "repo": REPO_URL, "apo": apo.DOWNLOAD_URL, "issues": REPO_URL + "/issues"}


# ============================================================================ helpers
def load_settings():
    s = json.loads(json.dumps(DEFAULTS))
    try:
        with open(SETTINGS_FILE, encoding="utf-8") as f:
            raw = json.load(f)
        for k in DEFAULTS:
            if k in raw:
                s[k] = raw[k] if k != "colors" else {**DEFAULTS["colors"], **raw[k]}
    except Exception:
        pass
    return s


def save_settings(s):
    try:
        old = {}
        if os.path.exists(SETTINGS_FILE):
            with open(SETTINGS_FILE, encoding="utf-8") as f:
                old = json.load(f)
        old.update(s)
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(old, f, indent=2)
    except Exception:
        traceback.print_exc()


def tool_module(name):
    if not FROZEN:
        t = find_repair_tool()
        if t and t not in sys.path:
            sys.path.insert(0, t)
    import importlib
    return importlib.import_module(name)


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


def tray_image(pct, charging, accent="#00B4FF"):
    S = 64
    im = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    rgb = lambda h: tuple(int(h.lstrip("#")[i:i + 2], 16) for i in (0, 2, 4)) + (255,)
    col = "#7C8594" if pct is None else "#FF5C5C" if pct <= 15 else "#FFB347" if pct <= 30 else \
        "#3DDC97" if charging else accent
    d.rounded_rectangle([1, 1, S - 2, S - 2], radius=14, fill=(14, 15, 18, 255), outline=rgb(col), width=4)
    if pct is None:
        d.arc([14, 12, 50, 48], 180, 360, fill=rgb(col), width=5)
        d.rounded_rectangle([11, 30, 21, 48], radius=4, fill=rgb(col))
        d.rounded_rectangle([43, 30, 53, 48], radius=4, fill=rgb(col))
        return im
    d.rectangle([9, S - 15, 9 + int((S - 18) * max(0, min(100, pct)) / 100), S - 10], fill=rgb(col))
    text = str(pct)
    font = None
    for name in ("segoeuib.ttf", "arialbd.ttf", "DejaVuSans-Bold.ttf"):
        try:
            font = ImageFont.truetype(name, 30 if len(text) < 3 else 23)
            break
        except Exception:
            pass
    font = font or ImageFont.load_default()
    box = d.textbbox((0, 0), text, font=font)
    w, h = box[2] - box[0], box[3] - box[1]
    d.text(((S - w) / 2 - box[0], (S - 16 - h) / 2 - box[1] + 3), text, font=font, fill=(255, 255, 255, 255))
    return im


class _Writer:
    def __init__(self, cb):
        self.cb = cb

    def write(self, s):
        if s:
            self.cb(s)
        return len(s)

    def flush(self):
        pass


# ============================================================================ core
class Core:
    def __init__(self):
        self.settings = load_settings()
        self.puser = prof.load_user()
        self.blog = battery.BatteryLog()
        self.dev = None
        self.busy = False
        self.dlock = threading.RLock()       # one logical operation at a time on the device
        self.last = {}                       # last quick status
        self.job = {"name": None, "running": False, "log": [], "progress": {}, "ok": None}
        self.mic = {"running": False, "rms": -90.0, "peak": -90.0, "spec": [-90.0] * 20, "err": None,
                    "phase": "", "files": []}
        self.mic_job = None
        self.auto = None                     # (profile id, exe)
        self.auto_saved = None               # (slot, gains, (mic, sidetone, gate))
        self.hk_prof = -1
        self.hk_mic = -1
        self.low_warned = False
        self.tray = None
        self.hk = None
        self.fw_path = None
        self.fw_comps = {}
        self.fw_notes = ""
        self.quit_event = threading.Event()

    # ---------------------------------------------------------------- device basics
    def get(self, fn, default=None):
        try:
            return fn()
        except DeviceError:
            return default

    def connect(self, quiet=False):
        with self.dlock:
            if self.dev:
                try:
                    self.dev.close()
                except Exception:
                    pass
                self.dev = None
            if quiet and acc_running():
                return False
            try:
                self.dev = A50()
                return True
            except DeviceError:
                self.dev = None
                return False

    def require(self):
        if self.busy:
            raise DeviceError("A firmware or repair job is running")
        if not self.dev and not self.connect(quiet=True):
            raise DeviceError("Base station not connected")
        return self.dev

    def quick(self):
        """Battery and headset state (called by the poller and by the window every few seconds)."""
        st = {"connected": bool(self.dev), "busy": self.busy, "acc": False}
        if self.dev and not self.busy:
            with self.dlock:
                bat = self.get(self.dev.battery)
                hs = self.get(self.dev.headset_status)
                st["preset"] = self.get(self.dev.active_preset)
            if bat:
                st.update(battery=bat[0], charging=bat[1], estimate=self.blog.estimate(bat[0], bat[1]))
                self.blog.add(bat[0], bat[1])
            if hs:
                st.update(docked=hs[0], on=hs[1])
        elif not self.dev:
            st["acc"] = self.last.get("acc", False)  # refreshed by the poller (tasklist is slow)
        st["auto"] = self.auto_label()
        st["job"] = self.job["running"]
        self.last = st
        return st

    def full(self):
        d = self.require()
        with self.dlock:
            info, bmin, hv = self.get(d.base_info), self.get(d.base_minor), self.get(d.headset_version)
            presets = []
            for p in (1, 2, 3):
                presets.append({"p": p, "name": self.get(lambda: d.preset_name(p)) or f"Preset {p}",
                                "gains": self.get(lambda: d.preset_gain(p)) or [0] * 5})
            active = self.get(d.active_preset) or 1
            freqs = []
            for b in range(5):
                r = self.get(lambda b=b: d.preset_band(active, b + 1))
                freqs.append(r[0] if r else None)
            sliders = {k: self.get(lambda i=i: d.slider(i)) for k, i in SLIDER.items()}
            out = {"base": {"major": info[0] if info else None, "build": info[1] if info else None, "radio": bmin},
                   "headset": {"mcu": hv[0] if hv else None, "radio": hv[1] if hv else None},
                   "healthy": bmin == 43 and bool(hv) and hv[1] == 43,
                   "presets": presets, "active": active, "freqs": freqs, "sliders": sliders,
                   "gate": self.get(d.noise_gate), "miceq": self.get(d.mic_eq),
                   "balance": self.get(d.balance), "default_balance": self.get(d.default_balance),
                   "alert": self.get(d.alert_volume)}
        out.update(self.quick())
        return out

    # ---------------------------------------------------------------- settings actions
    def do(self, fn):
        d = self.require()
        with self.dlock:
            try:
                return fn(d)
            except HeadsetUnavailable:
                raise DeviceError("Headset not reachable: turn it on or put it on the base")

    def apply_mic_setup(self, m):
        def f(d):
            d.set_slider(SLIDER["mic"], int(m["mic"]))
            d.set_slider(SLIDER["sidetone"], int(m["sidetone"]))
            d.set_noise_gate(int(m["gate"]))
        self.do(f)

    def apply_profile(self, x):
        def f(d):
            slot = d.active_preset()
            d.set_preset_gain(slot, x["gains"])
            return slot
        slot = self.do(f)
        m = next((s for s in prof.mic_all(self.puser) if s["id"] == x.get("mic")), None)
        if m:
            self.apply_mic_setup(m)
        return slot, m

    # ---------------------------------------------------------------- automatic game switching
    def auto_label(self):
        if not self.puser.get("auto_switch"):
            return {"on": False}
        if self.auto:
            x = next((p for p in prof.all_profiles(self.puser) if p["id"] == self.auto[0]), None)
            return {"on": True, "active": x["name"] if x else self.auto[1], "exe": self.auto[1]}
        return {"on": True, "active": None}

    def auto_switch(self):
        if not self.puser.get("auto_switch") or not self.dev or self.busy:
            return
        try:
            found, exe = prof.match_game(prof.all_profiles(self.puser), prof.running_processes())
        except Exception:
            return
        if found and (not self.auto or self.auto[0] != found["id"]):
            d = self.dev
            with self.dlock:
                slot = self.get(d.active_preset)
                if not slot:
                    return
                if not self.auto_saved:
                    before = self.get(lambda: d.preset_gain(slot))
                    if before is None:
                        return
                    mic = (self.get(lambda: d.slider(SLIDER["mic"])), self.get(lambda: d.slider(SLIDER["sidetone"])),
                           self.get(d.noise_gate))
                    self.auto_saved = (slot, before, mic if None not in mic else None)
            try:
                _, m = self.apply_profile(found)
            except DeviceError:
                return
            self.auto = (found["id"], exe)
            self.notify(f"{found['name']} profile on ({exe})" + (f" · mic: {m['name']}" if m else ""))
        elif not found and self.auto:
            self.auto_restore()

    def auto_restore(self):
        if self.auto_saved and self.dev:
            slot, gains, mic = self.auto_saved
            try:
                self.do(lambda d: d.set_preset_gain(slot, gains))
                if mic:
                    self.apply_mic_setup({"mic": mic[0], "sidetone": mic[1], "gate": mic[2]})
            except DeviceError:
                return
            self.notify("Game closed: your EQ is back")
        self.auto, self.auto_saved = None, None

    # ---------------------------------------------------------------- jobs (firmware update, repair)
    def run_job(self, name, module, argv, before=None):
        if self.busy:
            raise DeviceError("Another job is running")
        backup = self.auto_backup()
        self.busy = True
        with self.dlock:
            if self.dev:
                try:
                    self.dev.close()
                except Exception:
                    pass
                self.dev = None
        self.job = {"name": name, "running": True, "log": [], "progress": {}, "ok": None}
        if backup:
            self.job["log"].append(f"settings backup: {os.path.basename(backup)}\n")

        def work():
            mod = None
            old = sys.argv, sys.stdout, sys.stderr
            sys.argv = [module + ".py"] + argv
            sys.stdout = sys.stderr = _Writer(self.job["log"].append)
            try:
                mod = tool_module(module)
                if hasattr(mod, "PROGRESS"):
                    mod.PROGRESS = lambda k, d, t: self.job["progress"].__setitem__(k, [d, t])
                mod.main()
            except SystemExit as e:
                if e.code not in (None, 0):
                    print(e.code if isinstance(e.code, str) else f"exit code {e.code}")
            except Exception:
                traceback.print_exc()
            finally:
                sys.argv, sys.stdout, sys.stderr = old
                if mod is not None and hasattr(mod, "PROGRESS"):
                    mod.PROGRESS = None
                text = "".join(self.job["log"])
                tail = text[text.rfind("===") if "===" in text else 0:]
                self.job["ok"] = not ("Traceback" in tail or "CHECK" in tail or "error" in tail.lower()[-300:])
                self.job["running"] = False
                self.busy = False
                self.connect()
                self.notify(f"{name} finished" + ("" if self.job["ok"] else ": check the log"))

        threading.Thread(target=work, daemon=True).start()

    def fw_installed(self):
        if not self.dev or self.busy:
            return {}
        d = self.dev
        with self.dlock:
            info, hv = self.get(d.base_info), self.get(d.headset_version)
            return {"tx_mcu": info[0] if info else None, "tx_radio": self.get(d.base_minor),
                    "rx_mcu": hv[0] if hv else None, "rx_radio": hv[1] if hv else None}

    def fw_load(self, path):
        comps, notes = tool_module("a50_update").read_afw(path)
        if not comps:
            raise DeviceError("No A50 Gen 4 (Mimas) firmware in this file")
        self.fw_path, self.fw_comps = path, comps
        first = [l for l in notes.strip().split("\n\n")[0].splitlines() if l.strip("- ")] if notes else []
        self.fw_notes = " · ".join(first[1:4]) if len(first) > 1 else ""
        return self.fw_state()

    def fw_autodetect(self):
        pats = [os.path.expandvars(r"%LOCALAPPDATA%\Astro Gaming\ASTRO Command Center\Astro A50 Wireless (Mimas)\FW\*.afw"),
                r"C:\Program Files (x86)\Astro Gaming\ASTRO Command Center\assets\forced_fw\*.afw"]
        files = [f for p in pats for f in glob.glob(p)]
        return max(files, key=os.path.basename) if files else None

    def fw_state(self, exp=False, force=False):
        inst = self.fw_installed()
        rows = []
        for key, label, tested in FW_ROWS:
            fv = self.fw_comps.get(key, (None,))[0]
            iv = inst.get(key)
            will = fv is not None and (fv != iv or force) and (tested or exp)
            rows.append({"key": key, "label": label, "tested": tested, "file": fv, "installed": iv,
                         "status": "update" if will else ("ok" if fv is not None and fv == iv else
                                                          ("experimental" if not tested and not exp else "none"))})
        return {"file": os.path.basename(self.fw_path) if self.fw_path else None, "notes": self.fw_notes, "rows": rows}

    # ---------------------------------------------------------------- backups and report
    def snapshot_file(self, path):
        with self.dlock:
            snap = self.dev.snapshot()
        data = {"app": APP_NAME, "version": APP_VERSION, "created": time.strftime("%Y-%m-%d %H:%M:%S"), "settings": snap}
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        return data

    def auto_backup(self):
        if not self.dev:
            return None
        try:
            path = os.path.join(BACKUP_DIR, time.strftime("auto_%Y%m%d_%H%M%S.json"))
            self.snapshot_file(path)
            for old in sorted(glob.glob(os.path.join(BACKUP_DIR, "auto_*.json")))[:-10]:
                os.remove(old)
            return path
        except Exception:
            return None

    def report(self):
        L = [f"{APP_NAME} {APP_VERSION} - diagnostic report - {time.strftime('%Y-%m-%d %H:%M:%S')}",
             f"Windows: {platform.platform()} | Python {platform.python_version()} | {'exe' if FROZEN else 'source'} | web UI",
             f"ACC running: {acc_running()} | ACC installed: "
             f"{os.path.isdir(r'C:/Program Files (x86)/Astro Gaming/ASTRO Command Center')}"]
        try:
            import pywinusb.hid as hid
            pids = sorted({f"9886:{x.product_id:04X}" for x in hid.HidDeviceFilter(vendor_id=0x9886).get_devices()})
            L.append("USB devices: " + (", ".join(pids) or "none") + "   (002C = normal, 002A = base stuck in update mode)")
        except Exception as e:
            L.append(f"USB devices: error {e}")
        L += ["", "== Device =="]
        if self.dev and not self.busy:
            d = self.dev
            with self.dlock:
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
        L += ["", "== ASTRO Command Center log (errors only, last 40) =="]
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
        if self.job["log"]:
            L += ["", f"== Last job: {self.job['name']} ==", "".join(self.job["log"])[-6000:]]
        text = "\n".join(L) + "\n"
        home, user = os.path.expanduser("~"), os.environ.get("USERNAME", "")
        text = text.replace(home, "%USERPROFILE%")
        if len(user) > 2:
            text = text.replace(user, "<user>")
        return text

    # ---------------------------------------------------------------- mic test
    def mic_start(self, mode):
        if self.mic["running"]:
            return
        mid, _ = mic_test.find_a50()
        self.mic.update(running=True, err=None, phase=mode, rms=-90.0, peak=-90.0)

        def lvl(r, p):
            self.mic["rms"], self.mic["peak"] = r, p

        def spec(s):
            self.mic["spec"] = s

        def done(pcm, err):
            self.mic_job = None
            self.mic.update(running=False, err=err, rms=-90.0, peak=-90.0)
            if pcm and not err:
                self.mic["phase"] = "playing"
                try:
                    mic_test.play_pcm(pcm)
                except Exception as e:
                    self.mic["err"] = f"Playback failed: {e}"
            self.mic["phase"] = ""

        self.mic_job = mic_test.MicTest(lvl, done, device=mid, seconds=5 if mode == "record" else None,
                                        on_spectrum=spec).start()

    def mic_stop(self):
        if self.mic_job:
            self.mic_job.stop()

    def mic_compare(self):
        if self.mic["running"]:
            raise DeviceError("A mic test is already running")
        self.require()
        folder = os.path.join(DATA_DIR, "mic_compare")
        os.makedirs(folder, exist_ok=True)
        mid, _ = mic_test.find_a50()
        orig = self.get(self.dev.mic_eq)
        self.mic.update(running=True, err=None, files=[])

        def work():
            files = []
            try:
                for i in range(3):
                    self.mic["phase"] = f"Recording with headset preset {i}… keep talking"
                    self.do(lambda d: d.set_mic_eq(i))
                    time.sleep(0.6)
                    box = {}
                    mic_test.MicTest(lambda r, p: self.mic.update(rms=r, peak=p),
                                     lambda pcm, e: box.update(pcm=pcm, err=e), device=mid, seconds=4,
                                     on_spectrum=lambda s: self.mic.__setitem__("spec", s))._run()
                    if box.get("err") or not box.get("pcm"):
                        raise DeviceError(box.get("err") or "Nothing was recorded")
                    path = os.path.join(folder, f"headset_mic_preset_{i}.wav")
                    mic_test.save_wav(path, box["pcm"])
                    files.append((i, box["pcm"]))
                for i, pcm in files:
                    self.mic["phase"] = f"Playing headset preset {i}…"
                    mic_test.play_pcm(pcm)
                    time.sleep(0.4)
                self.mic["phase"] = f"Saved in {folder}"
            except Exception as e:
                self.mic["err"] = str(e)
            finally:
                if orig is not None:
                    try:
                        self.do(lambda d: d.set_mic_eq(orig))
                    except DeviceError:
                        pass
                self.mic.update(running=False, rms=-90.0, peak=-90.0)

        threading.Thread(target=work, daemon=True).start()

    # ---------------------------------------------------------------- tray, notifications, hotkeys
    def notify(self, text):
        if self.tray:
            try:
                self.tray.notify(text, APP_NAME)
            except Exception:
                pass

    def update_tray(self):
        if not self.tray:
            return
        st = self.last
        pct = st.get("battery")
        key = (pct, st.get("charging"), self.settings["colors"]["app"])
        if getattr(self, "_tray_key", None) == key:
            return
        self._tray_key = key
        try:
            self.tray.icon = tray_image(pct, st.get("charging", False), self.settings["colors"]["app"])
            self.tray.title = f"{APP_NAME} · " + (f"{pct}%" + (" charging" if st.get("charging") else "")
                                                   if pct is not None else "not connected")
            self.tray.update_menu()
        except Exception:
            pass

    def tray_text(self):
        st = self.last
        if st.get("battery") is None:
            return "Headset: not connected"
        est = st.get("estimate") or ""
        return f"Battery: {st['battery']}%" + ("  (charging)" if st.get("charging") else "") + (f"  {est}" if est else "")

    def check_low_battery(self):
        st = self.last
        limit = int(self.settings.get("low_battery") or 0)
        if st.get("battery") is None or not limit:
            return
        if st["battery"] <= limit and not st.get("charging"):
            if not self.low_warned:
                self.low_warned = True
                self.notify(f"Headset battery at {st['battery']}%. Put it on the base to charge.")
        elif st.get("charging") or st["battery"] > limit + 5:
            self.low_warned = False

    def hotkey(self, action):
        try:
            if action.startswith("preset"):
                slot = int(action[-1])
                self.do(lambda d: d.set_active_preset(slot))
                name = self.get(lambda: self.dev.preset_name(slot)) or f"Preset {slot}"
                self.notify(f"EQ: {name}")
            elif action == "next_profile":
                allp = prof.all_profiles(self.puser)
                self.hk_prof = (self.hk_prof + 1) % len(allp)
                x = allp[self.hk_prof]
                _, m = self.apply_profile(x)
                self.notify(f"Profile: {x['name']}" + (f" · mic: {m['name']}" if m else ""))
            elif action == "next_mic":
                mics = prof.mic_all(self.puser)
                self.hk_mic = (self.hk_mic + 1) % len(mics)
                self.apply_mic_setup(mics[self.hk_mic])
                self.notify(f"Mic: {mics[self.hk_mic]['name']}")
            elif action == "battery":
                st = self.quick()
                if st.get("battery") is None:
                    self.notify("Battery: headset not reachable")
                else:
                    self.notify(f"Battery {st['battery']}%" + (" (charging)" if st.get("charging") else "")
                                + (f" · {st['estimate']}" if st.get("estimate") else ""))
        except DeviceError as e:
            self.notify(str(e))

    def set_hotkeys(self, on):
        if on and not self.hk:
            try:
                self.hk = hotkeys.Hotkeys(lambda a: threading.Thread(target=self.hotkey, args=(a,), daemon=True).start()).start()
            except Exception:
                traceback.print_exc()
                self.hk = None
        elif not on and self.hk:
            self.hk.stop()
            self.hk = None

    # ---------------------------------------------------------------- background poller
    def poller(self):
        n = 0
        while not self.quit_event.is_set():
            n += 1
            try:
                if not self.busy:
                    if not self.dev and n % 2 == 0:
                        self.connect(quiet=True)
                    if self.dev:
                        self.quick()
                        self.auto_switch()
                    else:
                        self.last = {"connected": False, "busy": False, "acc": acc_running()}
                self.update_tray()
                self.check_low_battery()
            except Exception:
                with self.dlock:
                    if self.dev:
                        try:
                            self.dev.close()
                        except Exception:
                            pass
                        self.dev = None
            self.quit_event.wait(5)


CORE = Core()


# ============================================================================ HTTP API
def api(name, body):
    c = CORE
    s = c.settings
    if name == "state":
        return c.quick()
    if name == "full":
        return c.full()
    if name == "info":
        return {"name": APP_NAME, "version": APP_VERSION, "settings": s, "autostart": autostart_enabled(),
                "tray": bool(pystray and Image), "hotkeys": [{"key": l, "action": a, "desc": hotkeys.DESCRIPTIONS[a],
                                                              "taken": bool(c.hk and l in c.hk.failed)}
                                                             for a, _, l in hotkeys.SHORTCUTS],
                "gates": GATES}
    if name == "reconnect":
        c.connect()
        return c.quick()
    # ---- device settings
    if name == "set_preset":
        c.do(lambda d: d.set_active_preset(int(body["p"])))
        return c.full()
    if name == "set_gains":
        gains = [max(-7, min(7, int(g))) for g in body["gains"]][:5]
        c.do(lambda d: d.set_preset_gain(int(body["p"]), gains))
        return {"ok": True}
    if name == "rename":
        c.do(lambda d: d.set_preset_name(int(body["p"]), str(body["name"])[:20]))
        return {"ok": True}
    if name == "set_slider":
        c.do(lambda d: d.set_slider(SLIDER[body["name"]], max(0, min(100, int(body["value"])))))
        return {"ok": True}
    if name == "set_gate":
        c.do(lambda d: d.set_noise_gate(int(body["v"])))
        return {"ok": True}
    if name == "set_miceq":
        c.do(lambda d: d.set_mic_eq(int(body["v"])))
        return {"ok": True}
    if name == "set_default_balance":
        c.do(lambda d: d.set_default_balance(int(body["v"])))
        return {"ok": True}
    if name == "set_alert":
        c.do(lambda d: d.set_alert_volume(int(body["v"])))
        return {"ok": True}
    if name == "save":
        c.do(lambda d: d.save_values())
        return {"ok": True}
    # ---- profiles
    if name == "profiles":
        return {"profiles": prof.all_profiles(c.puser), "categories": list(prof.CATEGORIES),
                "mics": prof.mic_all(c.puser), "auto": c.auto_label()}
    if name == "profile_apply":
        slot, m = c.apply_profile(body)
        return {"slot": slot, "mic": m["name"] if m else None}
    if name == "profile_save":
        x = body
        base = next((p for p in prof.all_profiles(c.puser) if p["id"] == x.get("id")), None)
        data = {k: x[k] for k in ("name", "category", "gains", "games", "note", "mic") if k in x}
        if base and base["kind"] == "builtin":
            data.update(id=prof.new_id(), overrides=base["id"], category=base["category"])
        elif base:
            data.update(id=base["id"])
            if base.get("overrides"):
                data["overrides"] = base["overrides"]
        saved = prof.put(c.puser, data)
        prof.save_user(c.puser)
        return {"id": saved["id"]}
    if name == "profile_remove":
        prof.remove(c.puser, body["id"])
        prof.save_user(c.puser)
        return {"ok": True}
    if name == "profile_new":
        p = prof.put(c.puser, {"id": prof.new_id(), "name": body.get("name") or "My profile", "category": prof.MINE,
                               "gains": body.get("gains") or [0] * 5, "games": [], "note": "Made from your current EQ."})
        prof.save_user(c.puser)
        return {"id": p["id"]}
    if name == "profile_import":
        items = []
        raw = json.loads(body["text"])
        tmp = os.path.join(tempfile.gettempdir(), "a50_import.json")
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(raw, f)
        for it in prof.import_file(tmp):
            it["category"] = prof.MINE
            items.append(prof.put(c.puser, it))
        prof.save_user(c.puser)
        return {"count": len(items), "id": items[-1]["id"] if items else None}
    if name == "auto_switch":
        c.puser["auto_switch"] = bool(body["on"])
        prof.save_user(c.puser)
        if not body["on"] and c.auto:
            c.auto_restore()
        return c.auto_label()
    # ---- microphone setups
    if name == "mic_apply":
        c.apply_mic_setup(body)
        return {"ok": True}
    if name == "mic_save":
        m = prof.mic_put(c.puser, body)
        prof.save_user(c.puser)
        return {"id": m["id"]}
    if name == "mic_remove":
        prof.mic_remove(c.puser, body["id"])
        prof.save_user(c.puser)
        return {"ok": True}
    # ---- mic test
    if name == "mic_test":
        if body.get("stop"):
            c.mic_stop()
        else:
            c.mic_start(body.get("mode", "live"))
        return c.mic
    if name == "mic_state":
        return c.mic
    if name == "mic_compare":
        c.mic_compare()
        return c.mic
    # ---- PC mic EQ (Equalizer APO)
    if name == "apo":
        st = c.puser.setdefault("apo", {})
        if not isinstance(st.get("current"), dict):
            st["current"] = dict(apo.PRESETS[0])
        return {"installed": bool(apo.install_dir()), "presets": apo.PRESETS, "custom": c.puser.get("apo_custom", []),
                "current": apo.clean(st["current"]), "enabled": bool(st.get("enabled")), "bands": apo.BANDS}
    if name == "apo_set":
        st = c.puser.setdefault("apo", {})
        if "current" in body:
            st["current"] = apo.clean(body["current"])
        if "enabled" in body:
            st["enabled"] = bool(body["enabled"])
        prof.save_user(c.puser)
        _, dev_name = mic_test.find_a50()
        try:
            apo.write(st.get("current") or apo.PRESETS[0], device=apo.device_pattern(dev_name), enabled=bool(st.get("enabled")))
        except PermissionError:
            raise DeviceError("Windows didn't allow writing to Equalizer APO's folder: start A50 Control once as administrator")
        return {"ok": True}
    if name == "apo_save":
        item = apo.clean(dict(body["current"], id=prof.new_id(), name=body["name"], note="Your mic EQ."))
        c.puser["apo_custom"] = [x for x in c.puser.get("apo_custom", []) if x["id"] != item["id"]] + [item]
        c.puser.setdefault("apo", {})["current"] = item
        prof.save_user(c.puser)
        return item
    if name == "apo_remove":
        c.puser["apo_custom"] = [x for x in c.puser.get("apo_custom", []) if x["id"] != body["id"]]
        prof.save_user(c.puser)
        return {"ok": True}
    if name == "apo_configurator":
        exe = apo.configurator()
        if exe:
            os.startfile(exe)
        return {"ok": bool(exe)}
    # ---- firmware and repair
    if name == "fw_state":
        if not c.fw_comps:
            auto = c.fw_autodetect()
            if auto:
                try:
                    c.fw_load(auto)
                except Exception:
                    pass
        return c.fw_state(bool(body.get("exp")), bool(body.get("force")))
    if name == "fw_upload":
        data = base64.b64decode(body["data"])
        path = os.path.join(tempfile.gettempdir(), "a50_" + os.path.basename(body.get("name") or "firmware.afw"))
        with open(path, "wb") as f:
            f.write(data)
        c.fw_load(path)
        return c.fw_state(bool(body.get("exp")), bool(body.get("force")))
    if name == "fw_update":
        st = c.fw_state(bool(body.get("exp")), bool(body.get("force")))
        plan = [r["key"] for r in st["rows"] if r["status"] == "update"]
        if not plan:
            raise DeviceError("Nothing to update")
        argv = ["update", c.fw_path, "--only", ",".join(plan)]
        if body.get("force"):
            argv.append("--force")
        if any(k in ("tx_mcu", "rx_mcu") for k in plan):
            argv.append("--experimental")
        c.run_job("Firmware update", "a50_update", argv)
        return {"plan": plan}
    if name == "tool":
        action = body["action"]
        if action not in ("info", "fix-base", "fix-headset"):
            raise DeviceError("Unknown action")
        c.run_job({"info": "Diagnose", "fix-base": "Fix base radio chip", "fix-headset": "Fix headset radio chip"}[action],
                  "a50_tool", [action])
        return {"ok": True}
    if name == "job":
        start = int(body.get("from", 0))
        return {"name": c.job["name"], "running": c.job["running"], "ok": c.job["ok"],
                "log": "".join(c.job["log"][start:]), "next": len(c.job["log"]), "progress": c.job["progress"]}
    # ---- backup, report, settings
    if name == "backup":
        c.require()
        return c.snapshot_file(os.path.join(BACKUP_DIR, time.strftime("a50_settings_%Y%m%d_%H%M%S.json")))
    if name == "restore":
        raw = json.loads(body["text"])
        snap = raw.get("settings", raw)
        if not isinstance(snap, dict) or "presets" not in snap:
            raise DeviceError("This is not an A50 Control backup")
        failed = c.do(lambda d: d.restore(snap))
        if body.get("save"):
            c.do(lambda d: d.save_values())
        return {"failed": failed}
    if name == "report":
        return {"text": c.report(), "name": time.strftime("A50_report_%Y%m%d_%H%M.txt")}
    if name == "settings":
        for k, v in body.items():
            if k == "colors" and isinstance(v, dict):
                s["colors"].update({kk: vv for kk, vv in v.items() if kk in DEFAULTS["colors"]})
            elif k in DEFAULTS:
                s[k] = v
        save_settings(s)
        if "hotkeys" in body:
            c.set_hotkeys(bool(body["hotkeys"]))
        c.update_tray()
        return s
    if name == "autostart":
        set_autostart(bool(body["on"]))
        return {"on": autostart_enabled()}
    if name == "battery_history":
        rows = c.blog.history(24)
        return {"rows": rows, "typical": c.blog.typical_runtime(), "now": time.time()}
    if name == "open":
        url = URLS.get(body.get("what"))
        if url:
            webbrowser.open(url)
        elif body.get("what") == "backups":
            os.makedirs(BACKUP_DIR, exist_ok=True)
            os.startfile(BACKUP_DIR)
        elif body.get("what") == "mic_compare":
            os.startfile(os.path.join(DATA_DIR, "mic_compare"))
        return {"ok": True}
    if name == "quit":
        threading.Thread(target=shutdown, daemon=True).start()
        return {"ok": True}
    raise KeyError(name)


TOKEN = secrets.token_urlsafe(24)
MIME = {".html": "text/html; charset=utf-8", ".js": "text/javascript; charset=utf-8", ".css": "text/css; charset=utf-8",
        ".svg": "image/svg+xml", ".png": "image/png", ".ico": "image/x-icon", ".woff2": "font/woff2"}


class Handler(BaseHTTPRequestHandler):
    server_version = "A50Control"

    def log_message(self, *a):
        pass

    def _host_ok(self):
        return self.headers.get("Host", "").split(":")[0] in ("127.0.0.1", "localhost")

    def _send(self, code, data, ctype="application/json; charset=utf-8"):
        body = data if isinstance(data, bytes) else json.dumps(data).encode()
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if not self._host_ok():
            return self._send(403, {"error": "forbidden"})
        path = urlparse(self.path).path
        if path in ("/", "/index.html"):
            path = "/index.html"
        rel = os.path.normpath(path.lstrip("/")).replace("\\", "/")
        if rel.startswith("..") or rel.startswith("/"):
            return self._send(404, {"error": "not found"})
        full = os.path.join(WEB_DIR, rel)
        if not os.path.isfile(full):
            return self._send(404, {"error": "not found"})
        with open(full, "rb") as f:
            data = f.read()
        if rel == "index.html":
            data = data.replace(b"__TOKEN__", TOKEN.encode())
        self._send(200, data, MIME.get(os.path.splitext(full)[1], "application/octet-stream"))

    def do_POST(self):
        if not self._host_ok() or self.headers.get("X-Token") != TOKEN:
            return self._send(403, {"error": "forbidden"})
        path = urlparse(self.path).path
        if not path.startswith("/api/"):
            return self._send(404, {"error": "not found"})
        try:
            n = int(self.headers.get("Content-Length", 0))
            body = json.loads(self.rfile.read(n) or b"{}") if n else {}
            self._send(200, {"ok": True, "data": api(path[5:], body)})
        except DeviceError as e:
            self._send(200, {"ok": False, "error": str(e)})
        except KeyError as e:
            self._send(404, {"ok": False, "error": f"unknown: {e}"})
        except Exception as e:
            traceback.print_exc()
            self._send(200, {"ok": False, "error": f"{type(e).__name__}: {e}"})


# ============================================================================ window (Edge app mode)
WINDOW_TITLE = APP_NAME
URL = None


def edge_path():
    cands = [os.path.expandvars(r"%ProgramFiles(x86)%\Microsoft\Edge\Application\msedge.exe"),
             os.path.expandvars(r"%ProgramFiles%\Microsoft\Edge\Application\msedge.exe"),
             os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\Edge\Application\msedge.exe")]
    try:
        import winreg
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,
                            r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\msedge.exe") as k:
            cands.insert(0, winreg.QueryValueEx(k, "")[0])
    except Exception:
        pass
    return next((p for p in cands if p and os.path.isfile(p)), None)


def find_window():
    if sys.platform != "win32":
        return 0
    import ctypes
    return ctypes.windll.user32.FindWindowW(None, WINDOW_TITLE)


def show_window():
    hwnd = find_window()
    if hwnd:
        import ctypes
        u = ctypes.windll.user32
        u.ShowWindow(hwnd, 9)  # SW_RESTORE
        u.SetForegroundWindow(hwnd)
        return
    edge = edge_path()
    if edge:
        subprocess.Popen([edge, f"--app={URL}", f"--user-data-dir={os.path.join(DATA_DIR, 'window')}",
                          "--window-size=1320,900", "--no-first-run", "--no-default-browser-check",
                          "--disable-features=Translate,msEdgeSidebarV2,msUndersideButton", "--disable-sync",
                          "--disable-extensions"], creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    else:
        webbrowser.open(URL)


def window_watch():
    """Without a tray icon, closing the window closes the app."""
    seen = False
    while not CORE.quit_event.is_set():
        hwnd = find_window()
        if hwnd:
            seen = True
        elif seen and not (CORE.tray and CORE.settings.get("close_to_tray", True)):
            shutdown()
            return
        elif seen:
            if not getattr(CORE, "_tray_note", False):
                CORE._tray_note = True
                CORE.notify("Still running in the tray. Right-click the icon to quit.")
            seen = False
        CORE.quit_event.wait(1.5)


# ============================================================================ single instance
def listen_single(srv):
    while True:
        try:
            c, _ = srv.accept()
        except OSError:
            break
        try:
            c.settimeout(2)
            msg = c.recv(64).decode(errors="ignore").split()
            leave = bool(msg) and (msg[0] == "replace" or (len(msg) > 1 and msg[1] != APP_VERSION))
            if leave and not CORE.busy:
                c.sendall(b"bye")
                threading.Thread(target=shutdown, daemon=True).start()
            else:
                c.sendall(b"shown")
                show_window()
        except OSError:
            pass
        finally:
            c.close()


def other_instance_running():
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
    for _ in range(30):
        time.sleep(0.2)
        try:
            socket.create_connection(("127.0.0.1", SINGLE_PORT), timeout=0.3).close()
        except OSError:
            return False
    return True


def shutdown():
    if CORE.busy:
        CORE.notify("A firmware or repair job is running: wait until it finishes.")
        return
    CORE.quit_event.set()
    try:
        hwnd = find_window()
        if hwnd:
            import ctypes
            ctypes.windll.user32.PostMessageW(hwnd, 0x0010, 0, 0)  # WM_CLOSE: close the window too
    except Exception:
        pass
    try:
        if CORE.auto:
            CORE.auto_restore()
        CORE.mic_stop()
        if CORE.hk:
            CORE.hk.stop()
        if CORE.tray:
            CORE.tray.stop()
        if CORE.dev:
            CORE.dev.close()
    except Exception:
        pass
    try:
        sys.stdout.flush()
    except Exception:
        pass
    os._exit(0)


def start_tray():
    if not (pystray and Image):
        return
    M = pystray.MenuItem
    menu = pystray.Menu(
        M("Open A50 Control", lambda i, it: show_window(), default=True),
        M(lambda it: CORE.tray_text(), None, enabled=False),
        pystray.Menu.SEPARATOR,
        M("Start with Windows", lambda i, it: set_autostart(not autostart_enabled()), checked=lambda it: autostart_enabled()),
        M("Quit", lambda i, it: shutdown()))
    try:
        CORE.tray = pystray.Icon("A50Control", tray_image(None, False), APP_NAME, menu)
        CORE.tray.run_detached()
    except Exception:
        traceback.print_exc()
        CORE.tray = None


def main():
    global URL
    if other_instance_running():
        return
    try:
        single = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        single.bind(("127.0.0.1", SINGLE_PORT))
        single.listen(2)
        threading.Thread(target=listen_single, args=(single,), daemon=True).start()
    except OSError:
        pass
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    URL = f"http://127.0.0.1:{httpd.server_address[1]}/"
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    CORE.connect(quiet="--minimized" in sys.argv)
    start_tray()
    if CORE.settings.get("hotkeys", True):
        CORE.set_hotkeys(True)
    threading.Thread(target=CORE.poller, daemon=True).start()
    if "--minimized" not in sys.argv:
        show_window()
    threading.Thread(target=window_watch, daemon=True).start()
    if "--no-window-test" in sys.argv:   # used by the self-test
        print(URL, TOKEN, flush=True)
    CORE.quit_event.wait()


if __name__ == "__main__":
    try:
        main()
    except Exception:
        traceback.print_exc()
        os._exit(1)
