"""Microphone tester for A50 Control: live level meter and record/playback, using Windows' built-in winmm.
No extra packages. Records from the "ASTRO A50 Voice" input when it is found, otherwise the default microphone.
Audio stays in memory and is never saved or sent anywhere.
"""
import array
import ctypes
import io
import math
import sys
import threading
import time
import wave

RATE = 16000
CHUNK = 800  # 50 ms

if sys.platform == "win32":
    from ctypes import wintypes

    class WAVEFORMATEX(ctypes.Structure):
        _fields_ = [("wFormatTag", wintypes.WORD), ("nChannels", wintypes.WORD), ("nSamplesPerSec", wintypes.DWORD),
                    ("nAvgBytesPerSec", wintypes.DWORD), ("nBlockAlign", wintypes.WORD),
                    ("wBitsPerSample", wintypes.WORD), ("cbSize", wintypes.WORD)]

    class WAVEHDR(ctypes.Structure):
        pass

    WAVEHDR._fields_ = [("lpData", ctypes.c_void_p), ("dwBufferLength", wintypes.DWORD),
                        ("dwBytesRecorded", wintypes.DWORD), ("dwUser", ctypes.c_size_t),
                        ("dwFlags", wintypes.DWORD), ("dwLoops", wintypes.DWORD),
                        ("lpNext", ctypes.POINTER(WAVEHDR)), ("reserved", ctypes.c_size_t)]

    class WAVEINCAPSW(ctypes.Structure):
        _fields_ = [("wMid", wintypes.WORD), ("wPid", wintypes.WORD), ("vDriverVersion", wintypes.UINT),
                    ("szPname", ctypes.c_wchar * 32), ("dwFormats", wintypes.DWORD),
                    ("wChannels", wintypes.WORD), ("wReserved1", wintypes.WORD)]

    winmm = ctypes.WinDLL("winmm")
    HWAVEIN = ctypes.c_void_p
    winmm.waveInOpen.argtypes = [ctypes.POINTER(HWAVEIN), wintypes.UINT, ctypes.POINTER(WAVEFORMATEX),
                                 ctypes.c_size_t, ctypes.c_size_t, wintypes.DWORD]
    for fn in ("waveInPrepareHeader", "waveInUnprepareHeader", "waveInAddBuffer"):
        getattr(winmm, fn).argtypes = [HWAVEIN, ctypes.POINTER(WAVEHDR), wintypes.UINT]
    for fn in ("waveInStart", "waveInStop", "waveInReset", "waveInClose"):
        getattr(winmm, fn).argtypes = [HWAVEIN]
    winmm.waveInGetDevCapsW.argtypes = [ctypes.c_size_t, ctypes.POINTER(WAVEINCAPSW), wintypes.UINT]

WAVE_MAPPER = 0xFFFFFFFF
WAVE_MAPPED = 0x0004
WHDR_DONE = 0x0001


def input_devices():
    """[(id, name)] of Windows recording devices (names are cut to 31 characters by Windows)."""
    if sys.platform != "win32":
        return []
    out = []
    for i in range(winmm.waveInGetNumDevs()):
        caps = WAVEINCAPSW()
        if winmm.waveInGetDevCapsW(i, ctypes.byref(caps), ctypes.sizeof(caps)) == 0:
            out.append((i, caps.szPname))
    return out


def find_a50():
    for i, name in input_devices():
        if "A50" in name.upper() and "VOICE" in name.upper():
            return i, name
    for i, name in input_devices():
        if "A50" in name.upper() or "ASTRO" in name.upper():
            return i, name
    return None, None


def level_db(samples):
    """(rms dBFS, peak dBFS) of 16-bit samples."""
    if not samples:
        return -90.0, -90.0
    peak = max(abs(min(samples)), abs(max(samples))) / 32768
    rms = math.sqrt(sum(s * s for s in samples) / len(samples)) / 32768
    db = lambda v: max(-90.0, 20 * math.log10(v)) if v > 0 else -90.0
    return db(rms), db(peak)


SPEC_N = 512
SPEC_FREQS = [round(100 * (70 ** (i / 19))) for i in range(20)]  # band centres, 100 Hz .. 7 kHz, log spaced
_win = None
_bands = None


def _fft(x):
    """In-place iterative radix-2 FFT of a list of complex numbers (len = power of two)."""
    n = len(x)
    j = 0
    for i in range(1, n):
        bit = n >> 1
        while j & bit:
            j ^= bit
            bit >>= 1
        j |= bit
        if i < j:
            x[i], x[j] = x[j], x[i]
    size = 2
    while size <= n:
        w = complex(math.cos(-2 * math.pi / size), math.sin(-2 * math.pi / size))
        half = size // 2
        for start in range(0, n, size):
            wk = 1 + 0j
            for k in range(start, start + half):
                t = wk * x[k + half]
                x[k + half] = x[k] - t
                x[k] += t
                wk *= w
        size *= 2
    return x


def spectrum(samples):
    """dBFS level of 20 log-spaced bands (100 Hz - 7 kHz) over the last 512 samples. Pure Python, ~2 ms."""
    global _win, _bands
    if _win is None:
        _win = [0.5 - 0.5 * math.cos(2 * math.pi * n / (SPEC_N - 1)) for n in range(SPEC_N)]
        ratio = 70 ** (1 / 19)
        _bands = []
        for f in SPEC_FREQS:
            lo, hi = f / math.sqrt(ratio), f * math.sqrt(ratio)
            b0 = max(1, int(lo * SPEC_N / RATE))
            b1 = max(b0 + 1, int(math.ceil(hi * SPEC_N / RATE)))
            _bands.append((b0, min(b1, SPEC_N // 2)))
    x = list(samples[-SPEC_N:])
    if len(x) < SPEC_N:
        x = [0] * (SPEC_N - len(x)) + x
    X = _fft([complex(a * w, 0) for a, w in zip(x, _win)])
    out = []
    for b0, b1 in _bands:
        peak = max(abs(X[k]) for k in range(b0, b1))
        mag = peak / (SPEC_N / 4) / 32768
        out.append(max(-90.0, 20 * math.log10(mag)) if mag > 0 else -90.0)
    return out


class MicTest:
    """Record from a device in a background thread.
    on_level(rms_db, peak_db) is called about 20 times per second; on_done(pcm_bytes or None, error) at the end."""

    def __init__(self, on_level, on_done, device=None, seconds=None, on_spectrum=None):
        self.on_level, self.on_done, self.on_spectrum = on_level, on_done, on_spectrum
        self.device = WAVE_MAPPER if device is None else device
        self.seconds = seconds
        self._stop = threading.Event()
        self.thread = threading.Thread(target=self._run, daemon=True)

    def start(self):
        self.thread.start()
        return self

    def stop(self):
        self._stop.set()

    def _run(self):
        if sys.platform != "win32":
            self.on_done(None, "Microphone test works on Windows only.")
            return
        fmt = WAVEFORMATEX(1, 1, RATE, RATE * 2, 2, 16, 0)
        h = HWAVEIN()
        rc = winmm.waveInOpen(ctypes.byref(h), self.device, ctypes.byref(fmt), 0, 0, WAVE_MAPPED)
        if rc != 0:
            self.on_done(None, f"Can't open the microphone (error {rc}). Check Windows privacy settings: "
                               "Settings > Privacy > Microphone > let desktop apps use it.")
            return
        bufs, hdrs = [], []
        recorded = bytearray()
        try:
            for _ in range(6):
                b = ctypes.create_string_buffer(CHUNK * 2)
                hd = WAVEHDR()
                hd.lpData = ctypes.cast(b, ctypes.c_void_p)
                hd.dwBufferLength = CHUNK * 2
                winmm.waveInPrepareHeader(h, ctypes.byref(hd), ctypes.sizeof(hd))
                winmm.waveInAddBuffer(h, ctypes.byref(hd), ctypes.sizeof(hd))
                bufs.append(b)
                hdrs.append(hd)
            winmm.waveInStart(h)
            end = time.time() + self.seconds if self.seconds else None
            while not self._stop.is_set() and (end is None or time.time() < end):
                busy = True
                for b, hd in zip(bufs, hdrs):
                    if hd.dwFlags & WHDR_DONE:
                        busy = False
                        data = ctypes.string_at(b, hd.dwBytesRecorded)
                        if self.seconds:
                            recorded += data
                        smp = array.array("h", data[:len(data) // 2 * 2])
                        if self.on_level:
                            self.on_level(*level_db(smp))
                        if self.on_spectrum:
                            self.on_spectrum(spectrum(smp))
                        hd.dwFlags &= ~WHDR_DONE
                        hd.dwBytesRecorded = 0
                        winmm.waveInAddBuffer(h, ctypes.byref(hd), ctypes.sizeof(hd))
                if busy:
                    time.sleep(0.01)
        except Exception as e:  # never leave the device open
            self.on_done(None, str(e))
            return
        finally:
            winmm.waveInReset(h)
            for hd in hdrs:
                winmm.waveInUnprepareHeader(h, ctypes.byref(hd), ctypes.sizeof(hd))
            winmm.waveInClose(h)
        self.on_done(bytes(recorded) if self.seconds else None, None)


def save_wav(path, pcm):
    with wave.open(path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(RATE)
        w.writeframes(pcm)


def play_pcm(pcm):
    """Play 16 kHz mono 16-bit PCM on the default output (blocking)."""
    import winsound
    bio = io.BytesIO()
    with wave.open(bio, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(RATE)
        w.writeframes(pcm)
    winsound.PlaySound(bio.getvalue(), winsound.SND_MEMORY)
