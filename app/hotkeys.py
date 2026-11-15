"""Global keyboard shortcuts for A50 Control (work in games too), using the Windows RegisterHotKey API.

Shortcuts (Ctrl + Alt + key):
  1 / 2 / 3  EQ preset 1 / 2 / 3
  P          next game profile
  M          next microphone setup
  B          battery level (notification)
"""
import sys
import threading

MOD_ALT, MOD_CONTROL, MOD_NOREPEAT = 0x0001, 0x0002, 0x4000
WM_HOTKEY, WM_QUIT = 0x0312, 0x0012

SHORTCUTS = [  # (action, virtual key, label)
    ("preset1", 0x31, "Ctrl + Alt + 1"),
    ("preset2", 0x32, "Ctrl + Alt + 2"),
    ("preset3", 0x33, "Ctrl + Alt + 3"),
    ("next_profile", 0x50, "Ctrl + Alt + P"),
    ("next_mic", 0x4D, "Ctrl + Alt + M"),
    ("battery", 0x42, "Ctrl + Alt + B"),
]
DESCRIPTIONS = {"preset1": "EQ preset 1", "preset2": "EQ preset 2", "preset3": "EQ preset 3",
                "next_profile": "Next game profile", "next_mic": "Next microphone setup",
                "battery": "Show battery level"}


class Hotkeys:
    """Registers the shortcuts on a background thread; on_action(name) is called from that thread."""

    def __init__(self, on_action):
        self.on_action = on_action
        self.tid = None
        self.failed = []  # labels already used by another program
        self.ready = threading.Event()
        self.thread = None

    def start(self):
        if sys.platform != "win32":
            return self
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()
        self.ready.wait(2)
        return self

    def stop(self):
        if self.tid:
            import ctypes
            ctypes.windll.user32.PostThreadMessageW(self.tid, WM_QUIT, 0, 0)
            self.tid = None

    def _run(self):
        import ctypes
        from ctypes import wintypes
        user32, kernel32 = ctypes.windll.user32, ctypes.windll.kernel32
        user32.RegisterHotKey.argtypes = [wintypes.HWND, ctypes.c_int, wintypes.UINT, wintypes.UINT]
        self.tid = kernel32.GetCurrentThreadId()
        ids = {}
        for i, (name, vk, label) in enumerate(SHORTCUTS, start=1):
            if user32.RegisterHotKey(None, i, MOD_CONTROL | MOD_ALT | MOD_NOREPEAT, vk):
                ids[i] = name
            else:
                self.failed.append(label)
        self.ready.set()
        msg = wintypes.MSG()
        try:
            while user32.GetMessageW(ctypes.byref(msg), None, 0, 0) > 0:
                if msg.message == WM_HOTKEY and msg.wParam in ids:
                    try:
                        self.on_action(ids[msg.wParam])
                    except Exception:
                        pass
        finally:
            for i in ids:
                user32.UnregisterHotKey(None, i)
