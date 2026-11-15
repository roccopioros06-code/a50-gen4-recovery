"""Game EQ profiles for A50 Control.

- BUILTIN: ready-made starting points (5 band gains, -7..+7 dB, from the lowest band to the highest).
  They are not official ASTRO/Logitech presets: they follow common EQ practice (cut boomy lows that mask
  footsteps, lift the upper mids where steps, reloads and voices sit) and are meant to be tuned by ear.
- Your own profiles and your edits to built-in ones are kept in %APPDATA%\\A50Control\\profiles.json.
- Game detection: the process names of running programs are compared with each profile's "games" list.
"""
import json
import os
import sys
import time

DATA_DIR = os.path.join(os.environ.get("APPDATA", os.path.expanduser("~")), "A50Control")
PROFILES_FILE = os.path.join(DATA_DIR, "profiles.json")

MINE = "My profiles"
CATEGORIES = ("Competitive FPS", "Racing & sports", "Story & open world", "Music & video", MINE)


def P(pid, name, category, gains, games=(), note="", mic=None):
    """mic: id of a microphone setup to switch to with this profile (None = leave the mic as it is)."""
    return {"id": pid, "name": name, "category": category, "gains": list(gains), "games": list(games), "note": note,
            "mic": mic}


BUILTIN = [
    # ---- competitive shooters: less low end (explosions, engines), more upper mids/highs (footsteps, reloads)
    P("fps", "Footsteps (any FPS)", "Competitive FPS", (-4, -2, 2, 4, 2),
      note="Generic competitive curve: quieter explosions, louder footsteps and reloads.", mic="m_comp"),
    P("cod", "Call of Duty / Warzone", "Competitive FPS", (-3, -2, 2, 4, 3),
      ("cod.exe", "cod24-cod.exe", "cod25-cod.exe", "modernwarfare.exe", "blackopscoldwar.exe"),
      "Tames the heavy low end of CoD so steps cut through gunfire.", mic="m_comp"),
    P("valorant", "Valorant", "Competitive FPS", (-3, -1, 2, 4, 3), ("valorant-win64-shipping.exe",),
      "Clear footsteps and ability cues, keeps voices natural.", mic="m_comp"),
    P("cs2", "Counter-Strike 2", "Competitive FPS", (-4, -2, 1, 4, 3), ("cs2.exe",),
      "Maximum positional detail: steps, defuse and reload sounds.", mic="m_comp"),
    P("siege", "Rainbow Six Siege", "Competitive FPS", (-3, -1, 2, 3, 2),
      ("rainbowsix.exe", "rainbowsix_vulkan.exe", "rainbowsix_be.exe"),
      "Brings out steps and drones through walls and floors.", mic="m_comp"),
    P("apex", "Apex Legends", "Competitive FPS", (-2, -1, 2, 3, 2), ("r5apex.exe", "r5apex_dx12.exe"),
      "Balanced for footsteps without losing the weight of the guns.", mic="m_comp"),
    P("fortnite", "Fortnite", "Competitive FPS", (-2, -1, 2, 4, 2), ("fortniteclient-win64-shipping.exe",),
      "Louder steps, chests and building sounds.", mic="m_comp"),
    P("pubg", "PUBG", "Competitive FPS", (-3, -1, 2, 4, 2), ("tslgame.exe",),
      "Footsteps and vehicle direction at long range.", mic="m_comp"),
    P("overwatch", "Overwatch 2", "Competitive FPS", (-2, 0, 2, 3, 2), ("overwatch.exe",),
      "Clear ability and voice-line cues.", mic="m_comp"),
    P("battlefield", "Battlefield", "Competitive FPS", (1, 0, 1, 3, 2), ("bf6.exe", "bf2042.exe"),
      "Keeps the big battlefield sound, with a little extra detail."),
    # ---- racing and sports
    P("racing", "Racing (sim and arcade)", "Racing & sports", (3, 1, 0, 1, 2),
      ("forzahorizon5.exe", "forzahorizon6.exe", "forzamotorsport7.exe", "acs.exe", "ac2-win64-shipping.exe",
       "assettocorsaevo.exe", "beamng.drive.x64.exe", "f1_25.exe"),
      "Fuller engine and road feel, clear tyre noise."),
    P("sports", "Football and sports", "Racing & sports", (2, 0, 2, 2, 1), ("fc26.exe", "fc25.exe"),
      "Stadium atmosphere with clear commentary."),
    # ---- story / open world
    P("cinematic", "Story and open world", "Story & open world", (3, 1, 0, 1, 2),
      ("gta5.exe", "gta5_enhanced.exe", "cyberpunk2077.exe", "rdr2.exe"),
      "Richer, more cinematic sound for exploring and cutscenes."),
    # ---- media
    P("music", "Music", "Music & video", (3, 1, -1, 1, 3), note="Classic 'V' curve: more bass and sparkle."),
    P("movies", "Movies and series", "Music & video", (4, 1, 0, 1, 2), note="Deeper effects, dialogue stays clear."),
    P("voice", "Voice and podcasts", "Music & video", (-3, -1, 3, 2, 0), note="Voices up front, less rumble."),
    P("flat", "Flat", "Music & video", (0, 0, 0, 0, 0), note="No EQ: the sound as the game or song was mixed."),
]
BUILTIN_IDS = {p["id"] for p in BUILTIN}

# ---- microphone setups: mic level 0-100, sidetone 0-100, noise gate 0 Streaming / 1 Night / 2 Home / 3 Tournament
MIC_BUILTIN = [
    {"id": "m_chat", "name": "Chat (Discord, party)", "mic": 70, "sidetone": 30, "gate": 2,
     "note": "Natural voice, background noise filtered when you're not talking."},
    {"id": "m_comp", "name": "Competitive", "mic": 65, "sidetone": 40, "gate": 3,
     "note": "Strongest noise gate (keyboard, mouse, fans) and more sidetone so you don't shout."},
    {"id": "m_stream", "name": "Streaming / recording", "mic": 80, "sidetone": 20, "gate": 0,
     "note": "Most open gate: every word and breath gets through. Best in a quiet room."},
    {"id": "m_night", "name": "Late night", "mic": 85, "sidetone": 50, "gate": 1,
     "note": "For speaking quietly: higher level and sidetone, gate tuned for soft voices."},
    {"id": "m_noisy", "name": "Noisy room", "mic": 60, "sidetone": 30, "gate": 3,
     "note": "Lower level and strongest gate for TV, people or fans around you."},
]


def mic_all(user):
    return [dict(m, kind="builtin") for m in MIC_BUILTIN] + [dict(m, kind="mine") for m in user.get("mic_custom", [])]


def mic_put(user, setup):
    m = {"id": setup.get("id") or new_id(), "name": str(setup.get("name") or "My mic setup")[:40],
         "mic": max(0, min(100, int(setup.get("mic", 70)))), "sidetone": max(0, min(100, int(setup.get("sidetone", 30)))),
         "gate": max(0, min(3, int(setup.get("gate", 2)))), "note": str(setup.get("note") or "")[:200]}
    user["mic_custom"] = [x for x in user.get("mic_custom", []) if x["id"] != m["id"]] + [m]
    return m


def mic_remove(user, mid):
    user["mic_custom"] = [x for x in user.get("mic_custom", []) if x["id"] != mid]


def clamp_gains(g):
    g = [max(-7, min(7, int(round(float(x))))) for x in list(g)[:5]]
    return g + [0] * (5 - len(g))


# ------------------------------------------------------------------ storage
def load_user():
    data = {"custom": [], "auto_switch": False, "mic_custom": [], "apo": {}, "apo_custom": []}
    try:
        with open(PROFILES_FILE, encoding="utf-8") as f:
            raw = json.load(f)
        data["auto_switch"] = bool(raw.get("auto_switch", False))
        if isinstance(raw.get("apo"), dict):
            data["apo"] = raw["apo"]
        data["apo_custom"] = [x for x in raw.get("apo_custom", []) if isinstance(x, dict) and x.get("id")]
        for m in raw.get("mic_custom", []):
            if isinstance(m, dict) and m.get("id"):
                mic_put(data, m)
        for p in raw.get("custom", []):
            if isinstance(p, dict) and p.get("id") and p.get("name"):
                data["custom"].append(normalize(p))
    except Exception:
        pass
    return data


def save_user(data):
    os.makedirs(DATA_DIR, exist_ok=True)
    tmp = PROFILES_FILE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    os.replace(tmp, PROFILES_FILE)


def normalize(p):
    """Clean a profile coming from a file."""
    out = {"id": str(p.get("id") or new_id()), "name": str(p.get("name") or "Profile")[:40],
           "category": p.get("category") if p.get("category") in CATEGORIES else MINE,
           "gains": clamp_gains(p.get("gains") or [0] * 5),
           "games": sorted({str(g).strip().lower() for g in (p.get("games") or []) if str(g).strip()}),
           "note": str(p.get("note") or "")[:200],
           "mic": str(p["mic"]) if p.get("mic") else None}
    if p.get("overrides") in BUILTIN_IDS:
        out["overrides"] = p["overrides"]
    return out


_seq = [0]


def new_id():
    _seq[0] += 1
    return f"u{int(time.time() * 1000)}{_seq[0]:03d}"


def all_profiles(user):
    """Built-in profiles (replaced by your edited copy when there is one), then your own."""
    edits = {p["overrides"]: p for p in user["custom"] if p.get("overrides")}
    out = []
    for b in BUILTIN:
        if b["id"] in edits:
            out.append(dict(edits[b["id"]], kind="edited"))
        else:
            out.append(dict(b, kind="builtin"))
    out += [dict(p, kind="mine") for p in user["custom"] if not p.get("overrides")]
    return out


def put(user, profile):
    """Add or replace one of your profiles (an edit of a built-in one is stored with 'overrides')."""
    p = normalize(profile)
    user["custom"] = [c for c in user["custom"] if c["id"] != p["id"]
                      and not (p.get("overrides") and c.get("overrides") == p["overrides"])]
    user["custom"].append(p)
    return p


def remove(user, pid):
    user["custom"] = [c for c in user["custom"] if c["id"] != pid]


def export_file(path, profiles):
    data = {"a50control_profiles": 1, "profiles": [
        {k: p[k] for k in ("name", "category", "gains", "games", "note", "mic") if k in p} for p in profiles]}
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def import_file(path):
    with open(path, encoding="utf-8") as f:
        raw = json.load(f)
    items = raw.get("profiles") if isinstance(raw, dict) and "profiles" in raw else (
        raw if isinstance(raw, list) else [raw])
    out = []
    for i, p in enumerate(items):
        if isinstance(p, dict) and isinstance(p.get("gains"), list):
            q = normalize(dict(p, id=new_id() + str(i)))
            q.pop("overrides", None)
            out.append(q)
    if not out:
        raise ValueError("no profiles found in this file")
    return out


# ------------------------------------------------------------------ game detection
def running_processes():
    """Lower-case executable names of running processes (Windows; empty elsewhere)."""
    if sys.platform != "win32":
        return set()
    import ctypes
    from ctypes import wintypes

    class PROCESSENTRY32W(ctypes.Structure):
        _fields_ = [("dwSize", wintypes.DWORD), ("cntUsage", wintypes.DWORD), ("th32ProcessID", wintypes.DWORD),
                    ("th32DefaultHeapID", ctypes.c_size_t), ("th32ModuleID", wintypes.DWORD),
                    ("cntThreads", wintypes.DWORD), ("th32ParentProcessID", wintypes.DWORD),
                    ("pcPriClassBase", ctypes.c_long), ("dwFlags", wintypes.DWORD),
                    ("szExeFile", ctypes.c_wchar * 260)]

    k32 = ctypes.WinDLL("kernel32", use_last_error=True)
    k32.CreateToolhelp32Snapshot.restype = wintypes.HANDLE
    k32.CreateToolhelp32Snapshot.argtypes = [wintypes.DWORD, wintypes.DWORD]
    k32.Process32FirstW.argtypes = [wintypes.HANDLE, ctypes.POINTER(PROCESSENTRY32W)]
    k32.Process32NextW.argtypes = [wintypes.HANDLE, ctypes.POINTER(PROCESSENTRY32W)]
    k32.CloseHandle.argtypes = [wintypes.HANDLE]
    snap = k32.CreateToolhelp32Snapshot(0x2, 0)  # TH32CS_SNAPPROCESS
    if not snap or snap == ctypes.c_void_p(-1).value:
        return set()
    names = set()
    try:
        e = PROCESSENTRY32W()
        e.dwSize = ctypes.sizeof(PROCESSENTRY32W)
        ok = k32.Process32FirstW(snap, ctypes.byref(e))
        while ok:
            names.add(e.szExeFile.lower())
            ok = k32.Process32NextW(snap, ctypes.byref(e))
    finally:
        k32.CloseHandle(snap)
    return names


def match_game(profiles, running):
    """The profile for a running game, if any. Your own profiles win over built-in ones."""
    order = sorted(profiles, key=lambda p: {"mine": 0, "edited": 1}.get(p.get("kind"), 2))
    for p in order:
        for g in p.get("games", []):
            if g in running:
                return p, g
    return None, None
