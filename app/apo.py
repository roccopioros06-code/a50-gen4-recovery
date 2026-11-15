"""PC microphone EQ through Equalizer APO (free, open source: https://sourceforge.net/projects/equalizerapo/).

A50 Control writes its own file, A50Control_mic.txt, in Equalizer APO's config folder and adds one
"Include:" line to config.txt. Nothing else in your Equalizer APO setup is changed. The filters only apply to
the A50 voice input (Device + Stage: capture), and Equalizer APO reloads them by itself within a second.
"""
import os
import re

INCLUDE_NAME = "A50Control_mic.txt"
DOWNLOAD_URL = "https://sourceforge.net/projects/equalizerapo/"
BANDS = (31, 62, 125, 250, 500, 1000, 2000, 4000, 8000, 16000)
RANGE = 12  # dB per band
HP_CHOICES = (0, 60, 80, 100, 120)


def M(pid, name, gains, preamp=0, hp=80, note=""):
    return {"id": pid, "name": name, "gains": list(gains), "preamp": preamp, "hp": hp, "note": note}


#                                31  62 125 250 500 1k  2k  4k  8k 16k
PRESETS = [
    M("a_clear", "Clear voice", (0, 0, -1, -2, -1, 0, 2, 3, 1, 0), -3, 80,
      "Less muddiness, more presence: easier to understand in game chat."),
    M("a_broadcast", "Broadcast", (0, 2, 3, 1, -2, 0, 1, 2, 2, 1), -4, 70,
      "Fuller, 'radio' voice for streaming and recording."),
    M("a_warm", "Warm voice", (0, 1, 3, 2, 0, 0, 1, 1, 0, 0), -3, 60,
      "Adds body to thin or high-pitched voices."),
    M("a_boomy", "Less boomy / nasal", (0, 0, -2, -4, -2, -2, 1, 2, 1, 0), 0, 100,
      "Cuts the low rumble and the boxy, nasal tone."),
    M("a_sibilance", "Softer S sounds", (0, 0, 0, 0, 0, 0, 1, 0, -4, -2), 0, 80,
      "Tames harsh 's' and 'sh' sounds."),
    M("a_weak", "Weak or distant mic", (0, 0, 0, -1, 0, 2, 4, 4, 2, 0), 4, 90,
      "More level and clarity when you sound far away or quiet."),
    M("a_flat", "Flat (no EQ)", (0,) * 10, 0, 0, "Equalizer APO passes your mic through unchanged."),
]


def clean(p):
    return {"id": str(p.get("id") or "custom"), "name": str(p.get("name") or "My mic EQ")[:40],
            "gains": [max(-RANGE, min(RANGE, int(round(float(g))))) for g in (list(p.get("gains") or []) + [0] * 10)[:10]],
            "preamp": max(-12, min(12, int(round(float(p.get("preamp", 0)))))),
            "hp": int(p.get("hp", 0)) if int(p.get("hp", 0)) in HP_CHOICES else 0,
            "note": str(p.get("note") or "")[:200]}


def install_dir():
    """Equalizer APO's folder, or None if it isn't installed."""
    paths = []
    try:
        import winreg
        for view in (winreg.KEY_WOW64_64KEY, winreg.KEY_WOW64_32KEY):
            try:
                with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\EqualizerAPO", 0,
                                    winreg.KEY_READ | view) as k:
                    paths.append(winreg.QueryValueEx(k, "InstallPath")[0])
            except OSError:
                pass
    except ImportError:
        pass
    paths += [os.path.expandvars(r"%ProgramFiles%\EqualizerAPO"), r"C:\Program Files\EqualizerAPO"]
    for p in paths:
        if p and os.path.isfile(os.path.join(p, "config", "config.txt")):
            return p
    return None


def device_pattern(input_name):
    """'Microfono (ASTRO A50 Voice)' -> 'ASTRO A50 Voice'. Falls back to 'A50 Voice'."""
    m = re.search(r"\(([^)]*A50[^)]*)\)", input_name or "", re.I)
    return m.group(1).strip() if m else "A50 Voice"


def render(preset, device="A50 Voice"):
    p = clean(preset)
    lines = ["# Written by A50 Control: mic EQ for the A50 voice input. Changes here are overwritten.",
             f"# Profile: {p['name']}",
             f"Device: {device}",
             "Stage: capture",
             f"Preamp: {p['preamp']} dB"]
    if p["hp"]:
        lines.append(f"Filter: ON HP Fc {p['hp']} Hz")
    lines.append("GraphicEQ: " + "; ".join(f"{f} {g}" for f, g in zip(BANDS, p["gains"])))
    lines.append("Device: all")  # anything after this file in config.txt applies as before
    return "\n".join(lines) + "\n"


def write(preset, device="A50 Voice", enabled=True):
    """Write the mic EQ (or an empty file when disabled) and make sure config.txt includes it.
    Raises OSError (e.g. PermissionError) if Equalizer APO's config folder can't be written."""
    base = install_dir()
    if not base:
        raise FileNotFoundError("Equalizer APO is not installed")
    cfg = os.path.join(base, "config")
    body = render(preset, device) if enabled and preset else \
        "# Written by A50 Control: mic EQ is off.\n"
    with open(os.path.join(cfg, INCLUDE_NAME), "w", encoding="utf-8") as f:
        f.write(body)
    main = os.path.join(cfg, "config.txt")
    with open(main, encoding="utf-8", errors="replace") as f:
        text = f.read()
    if INCLUDE_NAME.lower() not in text.lower():
        with open(main, "a", encoding="utf-8") as f:
            f.write(("" if text.endswith("\n") or not text else "\n") + f"Include: {INCLUDE_NAME}\n")
    return os.path.join(cfg, INCLUDE_NAME)


def configurator():
    base = install_dir()
    exe = os.path.join(base, "Configurator.exe") if base else None
    return exe if exe and os.path.isfile(exe) else None
