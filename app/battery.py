"""Battery history and time estimates for A50 Control.

Readings are stored only when they change, in %APPDATA%\\A50Control\\battery_log.csv (last 30 days),
as: unix_time,percent,charging(0/1). Nothing leaves the PC.
"""
import os
import time

DATA_DIR = os.path.join(os.environ.get("APPDATA", os.path.expanduser("~")), "A50Control")
LOG_FILE = os.path.join(DATA_DIR, "battery_log.csv")
KEEP_DAYS = 30


class BatteryLog:
    def __init__(self, path=LOG_FILE):
        self.path = path
        self.rows = []  # (t, pct, charging)
        self._load()

    def _load(self):
        try:
            with open(self.path, encoding="utf-8") as f:
                for line in f:
                    p = line.strip().split(",")
                    if len(p) == 3:
                        self.rows.append((float(p[0]), int(p[1]), p[2] == "1"))
        except (OSError, ValueError):
            pass
        cut = time.time() - KEEP_DAYS * 86400
        self.rows = [r for r in self.rows if r[0] >= cut]

    def add(self, pct, charging, now=None):
        """Record a reading if it differs from the last one. Returns True if stored."""
        now = now or time.time()
        if self.rows and self.rows[-1][1:] == (pct, charging):
            return False
        self.rows.append((now, int(pct), bool(charging)))
        try:
            os.makedirs(os.path.dirname(self.path), exist_ok=True)
            if len(self.rows) % 200 == 0:  # occasionally rewrite to drop old rows
                cut = now - KEEP_DAYS * 86400
                self.rows = [r for r in self.rows if r[0] >= cut]
                with open(self.path, "w", encoding="utf-8") as f:
                    f.writelines(f"{t:.0f},{p},{int(c)}\n" for t, p, c in self.rows)
            else:
                with open(self.path, "a", encoding="utf-8") as f:
                    f.write(f"{now:.0f},{int(pct)},{int(charging)}\n")
        except OSError:
            pass
        return True

    def _session(self):
        """Readings since the charging state last changed."""
        if not self.rows:
            return []
        state = self.rows[-1][2]
        i = len(self.rows) - 1
        while i > 0 and self.rows[i - 1][2] == state:
            i -= 1
        return self.rows[i:]

    def rate(self):
        """(% per hour, charging) for the current session, or None if there isn't enough data yet."""
        s = self._session()
        if len(s) < 2:
            return None
        (t0, p0, ch), (t1, p1, _) = s[0], s[-1]
        hours = (t1 - t0) / 3600
        delta = (p1 - p0) if ch else (p0 - p1)
        if hours < 0.25 or delta < 3:
            return None
        return delta / hours, ch

    def estimate(self, pct, charging, now=None):
        """Human text like '≈ 6 h 20 min left' / '≈ 45 min to full', or ''."""
        r = self.rate()
        if not r or r[1] != charging or r[0] <= 0:
            return ""
        hours = ((100 - pct) if charging else pct) / r[0]
        if hours > 48:
            return ""
        h, m = int(hours), int(round((hours - int(hours)) * 60 / 5) * 5) % 60
        txt = (f"{h} h {m:02d} min" if h else f"{m} min") if (h or m) else "a few minutes"
        return f"≈ {txt} to full" if charging else f"≈ {txt} left"

    def typical_runtime(self):
        """Average hours for a full 100 → 0 % discharge, from past sessions (None if unknown)."""
        rates, i = [], 0
        rows = self.rows
        while i < len(rows):
            j = i
            while j + 1 < len(rows) and rows[j + 1][2] == rows[i][2]:
                j += 1
            if not rows[i][2]:
                (t0, p0, _), (t1, p1, _) = rows[i], rows[j]
                if (t1 - t0) >= 1800 and p0 - p1 >= 10:
                    rates.append((p0 - p1) / ((t1 - t0) / 3600))
            i = j + 1
        if not rates:
            return None
        return 100 / (sum(rates) / len(rates))

    def history(self, hours=24, now=None):
        now = now or time.time()
        return [r for r in self.rows if r[0] >= now - hours * 3600]
