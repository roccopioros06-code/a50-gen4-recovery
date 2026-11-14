"""
A50 Control (classic look) - an open-source replacement for ASTRO Command Center (ASTRO A50 Gen 4, base "Mimas", USB 9886:002C).

Status, EQ presets, microphone, noise gate, sidetone, game/voice balance, stream port mix,
alert volume, save to device, and safe repair of the Avnera radio chips.

Requirements: Windows, Python 3 (with tkinter, included in the python.org installer), pywinusb.
Close ASTRO Command Center while using this app: only one program may talk to the base.

Device commands based on eh-fifty (https://github.com/tdryer/eh-fifty, MIT) and on traffic
recorded from ACC 1.0.226. USE AT YOUR OWN RISK. Not affiliated with ASTRO Gaming or Logitech.
"""
import os
import subprocess
import sys
import threading
import tkinter as tk
from tkinter import messagebox, ttk

from a50_device import (A50, APP_NAME, APP_VERSION, DONATE_URL, EQ_PRESETS, NOISE_GATE, SLIDER,
                        DeviceError, HeadsetUnavailable, acc_running, find_repair_tool)

# --------------------------------------------------------------------------- GUI
class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(f"{APP_NAME} {APP_VERSION} - ASTRO A50 Gen 4")
        self.geometry("760x560")
        self.minsize(720, 520)
        self.dev = None
        self.loading = False
        self.preset = tk.IntVar(value=1)
        self.status = tk.StringVar(value="Not connected")
        self._build()
        self.after(200, self.connect)
        self.after(5000, self._poll)
        self.protocol("WM_DELETE_WINDOW", self._quit)

    # ---- layout
    def _build(self):
        style = ttk.Style(self)
        try:
            style.theme_use("vista" if os.name == "nt" else "clam")
        except tk.TclError:
            pass

        top = ttk.Frame(self, padding=(10, 8))
        top.pack(fill="x")
        ttk.Label(top, text="ASTRO A50 Gen 4", font=("Segoe UI", 14, "bold")).pack(side="left")
        ttk.Button(top, text="Save to headset", command=self.save).pack(side="right", padx=4)
        ttk.Button(top, text="Reload", command=self.load_all).pack(side="right", padx=4)
        ttk.Button(top, text="Reconnect", command=self.connect).pack(side="right", padx=4)

        nb = ttk.Notebook(self)
        nb.pack(fill="both", expand=True, padx=10)
        self.tab_status = ttk.Frame(nb, padding=12)
        self.tab_eq = ttk.Frame(nb, padding=12)
        self.tab_mic = ttk.Frame(nb, padding=12)
        self.tab_mix = ttk.Frame(nb, padding=12)
        self.tab_tools = ttk.Frame(nb, padding=12)
        for t, name in ((self.tab_status, "Status"), (self.tab_eq, "Equalizer"), (self.tab_mic, "Microphone"),
                        (self.tab_mix, "Mix & alerts"), (self.tab_tools, "Maintenance")):
            nb.add(t, text=name)
        self._build_status()
        self._build_eq()
        self._build_mic()
        self._build_mix()
        self._build_tools()

        bar = ttk.Frame(self, padding=(10, 4))
        bar.pack(fill="x")
        ttk.Label(bar, textvariable=self.status).pack(side="left")
        link = ttk.Label(bar, text="☕ Support the project", foreground="#0a66c2", cursor="hand2")
        link.pack(side="right")
        link.bind("<Button-1>", lambda e: self._open(DONATE_URL))

    def _row(self, parent, r, label):
        ttk.Label(parent, text=label).grid(row=r, column=0, sticky="w", pady=3)
        v = tk.StringVar(value="—")
        ttk.Label(parent, textvariable=v, font=("Segoe UI", 10, "bold")).grid(row=r, column=1, sticky="w", padx=12)
        return v

    def _build_status(self):
        f = self.tab_status
        self.v_battery = self._row(f, 0, "Battery")
        self.pb_battery = ttk.Progressbar(f, length=240, maximum=100)
        self.pb_battery.grid(row=0, column=2, sticky="w")
        self.v_headset = self._row(f, 1, "Headset")
        self.v_base_fw = self._row(f, 2, "Base firmware")
        self.v_head_fw = self._row(f, 3, "Headset firmware")
        self.v_base_build = self._row(f, 4, "Base build")
        self.v_health = self._row(f, 5, "Radio chips")
        ttk.Label(f, text="Changes in the other tabs apply immediately. Press \"Save to headset\" to keep them\n"
                          "after power-off. Close ASTRO Command Center while using this app.",
                  foreground="#555").grid(row=7, column=0, columnspan=3, sticky="w", pady=(18, 0))

    def _build_eq(self):
        f = self.tab_eq
        top = ttk.Frame(f)
        top.pack(fill="x")
        ttk.Label(top, text="Active preset:").pack(side="left")
        self.preset_buttons = {}
        for p in EQ_PRESETS:
            b = ttk.Radiobutton(top, text=f"Preset {p}", value=p, variable=self.preset, command=self._preset_changed)
            b.pack(side="left", padx=6)
            self.preset_buttons[p] = b
        ttk.Label(top, text="   Name:").pack(side="left")
        self.v_pname = tk.StringVar()
        e = ttk.Entry(top, textvariable=self.v_pname, width=16)
        e.pack(side="left", padx=4)
        ttk.Button(top, text="Rename", command=self._rename).pack(side="left")

        bands = ttk.Frame(f, padding=(0, 14))
        bands.pack(fill="both", expand=True)
        self.eq_vars, self.eq_freq = [], []
        for i in range(5):
            col = ttk.Frame(bands)
            col.pack(side="left", expand=True, fill="y")
            v = tk.IntVar(value=0)
            val = ttk.Label(col, text="0 dB")
            val.pack()
            s = tk.Scale(col, from_=7, to=-7, orient="vertical", variable=v, length=220, showvalue=False,
                         command=lambda x, lbl=val: lbl.config(text=f"{int(float(x)):+d} dB"))
            s.pack()
            s.bind("<ButtonRelease-1>", lambda e: self._apply_eq())
            fr = tk.StringVar(value=f"Band {i + 1}")
            ttk.Label(col, textvariable=fr).pack()
            self.eq_vars.append(v)
            self.eq_freq.append(fr)
        ttk.Button(f, text="Flat (all 0 dB)", command=self._flat).pack(anchor="e")

    def _scale(self, parent, r, label, frm, to, cb):
        ttk.Label(parent, text=label).grid(row=r, column=0, sticky="w", pady=6)
        v = tk.IntVar(value=0)
        lbl = ttk.Label(parent, text="—", width=6)
        lbl.grid(row=r, column=2, sticky="w")
        s = ttk.Scale(parent, from_=frm, to=to, orient="horizontal", length=320, variable=v,
                      command=lambda x: lbl.config(text=str(int(float(x)))))
        s.grid(row=r, column=1, padx=10)
        s.bind("<ButtonRelease-1>", lambda e: cb(v.get()))
        return v, lbl

    def _build_mic(self):
        f = self.tab_mic
        self.v_mic, self.l_mic = self._scale(f, 0, "Microphone level", 0, 100,
                                             lambda x: self._do(lambda: self.dev.set_slider(SLIDER["mic"], x)))
        self.v_side, self.l_side = self._scale(f, 1, "Sidetone", 0, 100,
                                               lambda x: self._do(lambda: self.dev.set_slider(SLIDER["sidetone"], x)))
        ttk.Label(f, text="Noise gate").grid(row=2, column=0, sticky="w", pady=(14, 4))
        self.v_gate = tk.IntVar(value=-1)
        g = ttk.Frame(f)
        g.grid(row=2, column=1, sticky="w", pady=(14, 4))
        for name, val in NOISE_GATE:
            ttk.Radiobutton(g, text=name, value=val, variable=self.v_gate,
                            command=lambda: self._do(lambda: self.dev.set_noise_gate(self.v_gate.get()))).pack(side="left", padx=4)
        ttk.Label(f, text="Mic EQ").grid(row=3, column=0, sticky="w", pady=4)
        self.v_miceq = tk.IntVar(value=-1)
        m = ttk.Frame(f)
        m.grid(row=3, column=1, sticky="w")
        for val in (0, 1, 2):
            ttk.Radiobutton(m, text=f"Preset {val}", value=val, variable=self.v_miceq,
                            command=lambda: self._do(lambda: self.dev.set_mic_eq(self.v_miceq.get()))).pack(side="left", padx=4)

    def _build_mix(self):
        f = self.tab_mix
        self.v_bal, self.l_bal = self._scale(f, 0, "Default balance (game ← → voice)", 0, 255,
                                             lambda x: self._do(lambda: self.dev.set_default_balance(x)))
        self.v_cur_bal = self._row(f, 1, "Current balance")
        self.v_alert, self.l_alert = self._scale(f, 2, "Alert volume", 0, 100,
                                                 lambda x: self._do(lambda: self.dev.set_alert_volume(x)))
        ttk.Label(f, text="Stream port mix", font=("Segoe UI", 10, "bold")).grid(row=3, column=0, sticky="w", pady=(16, 4))
        self.stream = {}
        for i, (key, name) in enumerate((("stream_game", "Game"), ("stream_chat", "Chat"),
                                         ("stream_mic", "Mic"), ("stream_aux", "Aux"))):
            self.stream[key] = self._scale(f, 4 + i, f"  {name}", 0, 100,
                                           lambda x, k=key: self._do(lambda: self.dev.set_slider(SLIDER[k], x)))

    def _build_tools(self):
        f = self.tab_tools
        ttk.Label(f, text="Repair the Avnera radio chips after a failed firmware update.\n"
                          "Run Diagnose first. Only repair a chip that is NOT at version 43.\n"
                          "Headset on and docked, base in PC mode, do not unplug anything while it runs.",
                  foreground="#555").pack(anchor="w")
        b = ttk.Frame(f, padding=(0, 10))
        b.pack(fill="x")
        ttk.Button(b, text="Diagnose (read-only)", command=lambda: self._tool("info")).pack(side="left", padx=4)
        ttk.Button(b, text="Fix BASE radio chip", command=lambda: self._tool("fix-base", True)).pack(side="left", padx=4)
        ttk.Button(b, text="Fix HEADSET radio chip", command=lambda: self._tool("fix-headset", True)).pack(side="left", padx=4)
        self.log = tk.Text(f, height=16, font=("Consolas", 9), state="disabled")
        self.log.pack(fill="both", expand=True)

    # ---- device helpers
    def connect(self):
        if self.dev:
            self.dev.close()
            self.dev = None
        if acc_running():
            messagebox.showwarning(APP_NAME, "ASTRO Command Center is running.\n\nClose it (also from the tray icon) "
                                             "before using this app: two programs talking to the base at the same "
                                             "time is what breaks firmware updates.")
        try:
            self.dev = A50()
        except DeviceError as e:
            self.status.set(f"Not connected: {e}")
            return
        self.status.set("Connected")
        self.load_all()

    def _do(self, fn, quiet=False):
        if self.loading:
            return None
        if not self.dev:
            self.status.set("Not connected")
            return None
        try:
            r = fn()
            if not quiet:
                self.status.set("Applied (not saved yet)")
            return True if r is None else r
        except HeadsetUnavailable:
            self.status.set("Headset not reachable (turn it on or dock it)")
        except DeviceError as e:
            self.status.set(f"Error: {e}")
        return None

    def _get(self, fn, default=None):
        try:
            return fn()
        except DeviceError:
            return default

    def load_all(self):
        if not self.dev:
            return
        self.loading = True
        try:
            self._load_status()
            p = self._get(self.dev.active_preset, 1)
            self.preset.set(p if p in EQ_PRESETS else 1)
            for q in EQ_PRESETS:
                name = self._get(lambda q=q: self.dev.preset_name(q))
                if name:
                    self.preset_buttons[q].config(text=name)
            self._load_preset()
            for var, lbl, key in ((self.v_mic, self.l_mic, "mic"), (self.v_side, self.l_side, "sidetone")):
                x = self._get(lambda k=key: self.dev.slider(SLIDER[k]))
                if x is not None:
                    var.set(x)
                    lbl.config(text=str(x))
            self.v_gate.set(self._get(self.dev.noise_gate, -1))
            self.v_miceq.set(self._get(self.dev.mic_eq, -1))
            for var, lbl, fn in ((self.v_bal, self.l_bal, self.dev.default_balance),
                                 (self.v_alert, self.l_alert, self.dev.alert_volume)):
                x = self._get(fn)
                if x is not None:
                    var.set(x)
                    lbl.config(text=str(x))
            for key, (var, lbl) in self.stream.items():
                x = self._get(lambda k=key: self.dev.slider(SLIDER[k]))
                if x is not None:
                    var.set(x)
                    lbl.config(text=str(x))
            self.status.set("Loaded from headset")
        finally:
            self.loading = False

    def _load_status(self):
        d = self.dev
        bat = self._get(d.battery)
        if bat:
            self.v_battery.set(f"{bat[0]}%" + ("  (charging)" if bat[1] else ""))
            self.pb_battery["value"] = bat[0]
        st = self._get(d.headset_status)
        if st:
            self.v_headset.set(("Docked" if st[0] else "Off the base") + (", on" if st[1] else ", off"))
        info = self._get(d.base_info)
        bmin = self._get(d.base_minor)
        if info:
            self.v_base_build.set(info[1])
            self.v_base_fw.set(f"{info[0]}.{bmin}" if bmin is not None else f"{info[0]}.? (radio chip error)")
        hv = self._get(d.headset_version)
        self.v_head_fw.set(f"{hv[0]}.{hv[1]}" if hv else "not reachable")
        cb = self._get(d.balance)
        if cb is not None:
            self.v_cur_bal.set(str(cb))
        problems = []
        if bmin is not None and bmin != 43:
            problems.append(f"base {bmin}")
        if bmin is None:
            problems.append("base error")
        if hv and hv[1] != 43:
            problems.append(f"headset {hv[1]}")
        self.v_health.set("OK (43 / 43)" if not problems and hv else
                          ("Check Maintenance tab: " + ", ".join(problems)) if problems else "headset not reachable")

    def _load_preset(self):
        p = self.preset.get()
        name = self._get(lambda: self.dev.preset_name(p), "")
        self.v_pname.set(name)
        g = self._get(lambda: self.dev.preset_gain(p))
        if g:
            for v, x in zip(self.eq_vars, g):
                v.set(x)
        for i in range(5):
            b = self._get(lambda i=i: self.dev.preset_band(p, i + 1))
            if b:
                fr = b[0]
                self.eq_freq[i].set(f"{fr / 1000:.1f} kHz" if fr >= 1000 else f"{fr} Hz")

    def _preset_changed(self):
        if self.loading:
            return
        p = self.preset.get()
        self._do(lambda: self.dev.set_active_preset(p))
        self.loading = True
        try:
            self._load_preset()
        finally:
            self.loading = False

    def _apply_eq(self):
        p = self.preset.get()
        self._do(lambda: self.dev.set_preset_gain(p, [v.get() for v in self.eq_vars]))

    def _flat(self):
        for v in self.eq_vars:
            v.set(0)
        self._apply_eq()

    def _rename(self):
        p, name = self.preset.get(), self.v_pname.get().strip()
        if name:
            self._do(lambda: self.dev.set_preset_name(p, name))
            self.preset_buttons[p].config(text=name)

    def save(self):
        if self.dev and self._do(self.dev.save_values, quiet=True):
            self.status.set("Saved to headset")

    def _poll(self):
        if self.dev and not self.loading and not self.dev.lock.locked():
            bat = self._get(self.dev.battery)
            if bat:
                self.v_battery.set(f"{bat[0]}%" + ("  (charging)" if bat[1] else ""))
                self.pb_battery["value"] = bat[0]
            st = self._get(self.dev.headset_status)
            if st:
                self.v_headset.set(("Docked" if st[0] else "Off the base") + (", on" if st[1] else ", off"))
        self.after(5000, self._poll)

    # ---- maintenance (runs the tested repair tool in a separate process)
    def _log(self, text):
        self.log.config(state="normal")
        self.log.insert("end", text)
        self.log.see("end")
        self.log.config(state="disabled")

    def _tool(self, action, dangerous=False):
        tool = find_repair_tool()
        if not tool:
            messagebox.showerror(APP_NAME, "tool/a50_tool.py not found next to the app.")
            return
        if dangerous and not messagebox.askyesno(
                APP_NAME, "This rewrites a radio chip of your device with the official firmware.\n\n"
                          "Unofficial, use at your own risk. Only do this if Diagnose shows that chip "
                          "is NOT at version 43.\n\nHeadset on and docked, do not unplug anything.\n\nContinue?"):
            return
        if self.dev:  # release the device: the tool must be the only program talking to the base
            self.dev.close()
            self.dev = None
        self.status.set(f"Running {action}...")
        self._log(f"\n=== {action} ===\n")

        def run():
            try:
                p = subprocess.Popen([sys.executable, "-u", "a50_tool.py", action], cwd=tool,
                                     stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
                                     creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
                for line in p.stdout:
                    self.after(0, self._log, line)
                p.wait()
            except Exception as e:
                self.after(0, self._log, f"error: {e}\n")
            self.after(0, self.connect)

        threading.Thread(target=run, daemon=True).start()

    def _open(self, url):
        import webbrowser
        webbrowser.open(url)

    def _quit(self):
        if self.dev:
            self.dev.close()
        self.destroy()


if __name__ == "__main__":
    App().mainloop()
