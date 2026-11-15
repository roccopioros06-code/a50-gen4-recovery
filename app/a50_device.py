"""
a50_device.py - device layer for ASTRO A50 Gen 4 (base "Mimas", USB 9886:002C), shared by the A50 Control GUIs.
Commands based on eh-fifty (https://github.com/tdryer/eh-fifty, MIT) and on traffic recorded from ACC 1.0.226.
USE AT YOUR OWN RISK. Not affiliated with ASTRO Gaming or Logitech.
"""
import os
import queue
import subprocess
import threading
import time

try:
    import pywinusb.hid as hid
except ImportError:
    hid = None

APP_NAME = "A50 Control"
APP_VERSION = "0.3.0"
VID, PID = 0x9886, 0x002C
DONATE_URL = "https://paypal.me/d4rky06"
REPO_URL = "https://github.com/roccopioros06-code/a50-gen4-recovery"

EQ_PRESETS = [1, 2, 3]
NOISE_GATE = [("Streaming", 0), ("Night", 1), ("Home", 2), ("Tournament", 3)]
SLIDER = {"stream_mic": 0, "stream_chat": 1, "stream_game": 2, "stream_aux": 3, "mic": 4, "sidetone": 5}


class DeviceError(Exception):
    pass


class HeadsetUnavailable(DeviceError):
    pass


# --------------------------------------------------------------------------- device
class A50:
    """Minimal, thread-safe transport for the base station control interface (HID usage page 0xFF32)."""

    def __init__(self):
        if hid is None:
            raise DeviceError("Missing library: python -m pip install pywinusb")
        self.dev = None
        for d in hid.HidDeviceFilter(vendor_id=VID, product_id=PID).get_devices():
            d.open()
            if d.hid_caps.usage_page == 0xFF32:
                self.dev = d
                break
            d.close()
        if self.dev is None:
            raise DeviceError("Base station not found. USB connected? Mode switch on PC?")
        self.out_len = self.dev.hid_caps.output_report_byte_length
        self.lock = threading.Lock()
        self.seq = 0
        self.q = queue.Queue()
        self.dev.set_raw_data_handler(lambda data: self.q.put(list(data)))

    def close(self):
        try:
            self.dev.close()
        except Exception:
            pass

    def raw(self, cmd, payload=(), timeout=3.0):
        """Send a request, return (status, data, raw). Responses with a stale seq are discarded."""
        with self.lock:
            seq = self.seq & 3
            self.seq += 1
            payload = list(payload)
            pkt = [0x02, cmd, (len(payload) & 0x3F) | (seq << 6)] + payload
            pkt += [0] * (self.out_len - len(pkt))
            while not self.q.empty():
                self.q.get_nowait()
            self.dev.send_output_report(pkt)
            end = time.time() + timeout
            while True:
                left = end - time.time()
                if left <= 0:
                    raise DeviceError(f"timeout on command 0x{cmd:02X}")
                try:
                    r = self.q.get(timeout=left)
                except queue.Empty:
                    continue
                if len(r) < 3 or r[0] != 0x02:
                    continue
                if r[1] != 0x00 and (r[2] >> 6) != seq:
                    continue  # answer to an older request
                n = min(r[2] & 0x3F, len(r) - 3)
                return r[1], bytes(r[3:3 + n]), r

    def req(self, cmd, payload=(), timeout=3.0):
        status, data, _ = self.raw(cmd, payload, timeout)
        if status == 0x01:
            msg = bytes(b for b in data[4:] if 32 <= b < 127).decode(errors="ignore") or "error"
            if "SLAVE" in msg:
                raise HeadsetUnavailable(msg)
            raise DeviceError(msg)
        return data

    # ---- read
    def base_info(self):
        d = self.req(0x03)
        build = f"{d[8] | d[9] << 8}-{d[10]:02d}-{d[11]:02d}"
        major = int.from_bytes(d[21:25], "little") if len(d) >= 25 else None
        return major, build

    def base_minor(self):
        return self.req(0x55)[0]

    def headset_version(self):
        major = int.from_bytes(self.req(0xDA, [0x0A])[:4], "little")
        minor = self.req(0xD6, [0x0A])[0]
        return major, minor

    def battery(self):
        b = self.req(0x7C)[0]
        return b & 0x7F, bool(b & 0x80)

    def headset_status(self):
        s = self.req(0x54)[0]
        return bool(s & 0x01), bool(s & 0x02)  # docked, on

    def active_preset(self):
        return self.req(0x6C)[0]

    def preset_name(self, p):
        d = self.req(0x6E, [p, 0])
        return bytes(b for b in d[2:] if b).decode(errors="replace")

    def preset_gain(self, p):
        d = self.req(0x69, [p])
        return [g - 12 for g in d[2:7]]

    def preset_band(self, p, band):
        d = self.req(0x70, [p, band])
        bw = int.from_bytes(d[3:5], "little")
        freq = int.from_bytes(d[7:9], "little")
        return freq, bw

    def slider(self, s):
        return self.req(0x68, [s])[2]

    def noise_gate(self):
        return self.req(0x6A)[1]

    def mic_eq(self):
        return self.req(0x7B, [0])[0]

    def balance(self):
        return self.req(0x72)[0]

    def default_balance(self):
        return self.req(0x77, [0])[0]

    def alert_volume(self):
        return self.req(0x7A, [0])[0]

    # ---- write (active values change immediately; save_values() makes them permanent)
    def set_active_preset(self, p):
        self.req(0x67, [p])

    def set_preset_gain(self, p, gains):
        self.req(0x63, [p] + [max(-7, min(7, int(g))) + 12 for g in gains])

    def set_preset_name(self, p, name):
        enc = name.encode()[:20] + b"\x00"
        self.req(0x6D, [p, len(enc)] + list(enc))

    def set_slider(self, s, value):
        self.req(0x62, [s, max(0, min(100, int(value)))])

    def set_noise_gate(self, mode):
        self.req(0x64, [mode])

    def set_mic_eq(self, v):
        self.req(0x71, [v])

    def set_default_balance(self, v):
        self.req(0x73, [max(0, min(255, int(v)))])

    def set_alert_volume(self, v):
        self.req(0x76, [max(0, min(100, int(v)))])

    def save_values(self):
        self.req(0x61, timeout=6.0)

    # ---- backup / restore of all user settings
    def snapshot(self):
        """Every user setting as a JSON-friendly dict. Values that can't be read are left out."""
        def get(fn):
            try:
                return fn()
            except DeviceError:
                return None
        snap = {"active_preset": get(self.active_preset), "presets": {}, "sliders": {},
                "noise_gate": get(self.noise_gate), "mic_eq": get(self.mic_eq),
                "default_balance": get(self.default_balance), "alert_volume": get(self.alert_volume)}
        for p in EQ_PRESETS:
            snap["presets"][str(p)] = {"name": get(lambda: self.preset_name(p)), "gains": get(lambda: self.preset_gain(p))}
        for name, idx in SLIDER.items():
            snap["sliders"][name] = get(lambda: self.slider(idx))
        return snap

    def restore(self, snap):
        """Write a snapshot back (active values only: call save_values() to keep them). Returns failed items."""
        failed = []

        def put(label, fn, *args):
            if any(a is None for a in args):
                return
            try:
                fn(*args)
            except DeviceError:
                failed.append(label)
        for p, d in (snap.get("presets") or {}).items():
            if str(p).isdigit() and int(p) in EQ_PRESETS and isinstance(d, dict):
                if d.get("gains") and len(d["gains"]) == 5:
                    put(f"preset {p} EQ", self.set_preset_gain, int(p), d["gains"])
                if d.get("name"):
                    put(f"preset {p} name", self.set_preset_name, int(p), str(d["name"]))
        for name, v in (snap.get("sliders") or {}).items():
            if name in SLIDER:
                put(name, self.set_slider, SLIDER[name], v)
        put("noise gate", self.set_noise_gate, snap.get("noise_gate"))
        put("mic EQ", self.set_mic_eq, snap.get("mic_eq"))
        put("default balance", self.set_default_balance, snap.get("default_balance"))
        put("alert volume", self.set_alert_volume, snap.get("alert_volume"))
        if snap.get("active_preset") in EQ_PRESETS:
            put("active preset", self.set_active_preset, snap["active_preset"])
        return failed


# --------------------------------------------------------------------------- helpers
def acc_running():
    if os.name != "nt":
        return False
    try:
        out = subprocess.run(["tasklist", "/FI", "IMAGENAME eq ASTRO Command Center.exe"],
                             capture_output=True, timeout=5,
                             creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0)).stdout
        return b"ASTRO Command Center.exe" in out  # bytes: tasklist output is in the console code page
    except Exception:
        return False


def find_repair_tool():
    here = os.path.dirname(os.path.abspath(__file__))
    for cand in (os.path.join(here, "..", "tool"), here):
        if os.path.exists(os.path.join(cand, "a50_tool.py")):
            return os.path.abspath(cand)
    return None


