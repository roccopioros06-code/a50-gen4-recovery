"""
a50_tool.py - diagnose and repair tool for the ASTRO A50 Gen 4 (base "Mimas", USB 9886:002C).
Written from scratch; the protocol is documented in ../PROTOCOL.md.

Usage:
    python a50_tool.py info          read versions, battery, status (writes nothing)
    python a50_tool.py fix-base      rewrite the BASE Avnera radio chip    (TX_RADIO, v43)
    python a50_tool.py fix-headset   rewrite the HEADSET Avnera radio chip (RX_RADIO, v43)

Requirements: Windows, Python 3, "python -m pip install pywinusb".
Close ASTRO Command Center first: nothing else may talk to the base while this runs.
USE AT YOUR OWN RISK. Not affiliated with ASTRO Gaming or Logitech.
"""
import glob
import hashlib
import io
import os
import sys
import threading
import time
import zipfile

try:
    import pywinusb.hid as hid
except ImportError:
    sys.exit("Missing library: python -m pip install pywinusb")

VID, PID = 0x9886, 0x002C
QUI = os.path.dirname(os.path.abspath(__file__))
CERCA_AFW = [
    os.path.join(QUI, "*.afw"),
    os.path.join(QUI, "..", "firmware", "*.afw"),
    os.path.expandvars(r"%LOCALAPPDATA%\Astro Gaming\ASTRO Command Center\Astro A50 Wireless (Mimas)\FW\*.afw"),
    r"C:\Program Files (x86)\Astro Gaming\ASTRO Command Center\assets\forced_fw\*.afw",
]
SLAVE_TIMEOUT = 0x01000001

# Update targets (from the internal tables of ACC 1.0.226)
TARGET = {
    "fix-base": dict(
        nome="BASE Avnera (TX_RADIO)", file="mimas/avneratx_v43_27Jun2019_r21.bin",
        md5="6f27ce7304020d501fbe79f9adb8de76", size=65554,
        start=(0x48, b""), data=0x49, prefix=b"", end=(0x4A, b""), reset=(0x01, b""),
        tollera_slave_timeout=False, verifica=(0x55, b"")),
    "fix-headset": dict(
        nome="HEADSET Avnera (RX_RADIO)", file="mimas/avnerarx_v43_27Jun2019_r21.bin",
        md5="a42fc26cd382764bee66e57b72ae7125", size=65562,
        start=(0xF8, b"\x64"), data=0xF9, prefix=b"\x0A", end=(0xFA, b"\x28"), reset=(0x81, b"\x0A"),
        tollera_slave_timeout=True, verifica=(0xD6, b"\x0A")),
}
CHUNK = 32


def log(msg):
    print(time.strftime("%H:%M:%S"), msg, flush=True)


def apri_afw(path):
    raw = bytearray(open(path, "rb").read())
    if raw[:2] == b"AG":          # Astro replaces the "PK" signature of the first zip record with "AG"
        raw[:2] = b"PK"
    return zipfile.ZipFile(io.BytesIO(bytes(raw)))


def carica_immagine(t):
    for pattern in CERCA_AFW:
        for path in sorted(glob.glob(pattern)):
            try:
                img = apri_afw(path).read(t["file"])
            except Exception:
                continue
            if hashlib.md5(img).hexdigest() == t["md5"] and len(img) == t["size"]:
                log(f"Firmware verified (md5 ok) from: {path}")
                return img
    sys.exit(f"Firmware {t['file']} not found or invalid (is ASTRO Command Center installed?). Nothing was written.")


class Base:
    def __init__(self):
        self.dev = None
        for d in hid.HidDeviceFilter(vendor_id=VID, product_id=PID).get_devices():
            d.open()
            if d.hid_caps.usage_page == 0xFF32:
                self.dev = d
                break
            d.close()
        if self.dev is None:
            sys.exit("Base 9886:002C not found (USB connected? mode switch on PC?).")
        self.out_len = self.dev.hid_caps.output_report_byte_length
        self.seq = 0
        self.resp = []
        self.ev = threading.Event()
        self.dev.set_raw_data_handler(self._on_data)

    def _on_data(self, data):
        self.resp.append(list(data))
        self.ev.set()

    def close(self):
        try:
            self.dev.close()
        except Exception:
            pass

    def cmd(self, c, payload=b"", timeout=3.0, accetta_vuota=False):
        """Send a command. Returns (ok, description, error_code, raw_response)."""
        seq = self.seq & 0x03
        self.seq += 1
        pkt = [0x02, c, (len(payload) & 0x3F) | (seq << 6)] + list(payload)
        pkt += [0x00] * (self.out_len - len(pkt))
        self.resp.clear()
        self.ev.clear()
        self.dev.send_output_report(pkt)
        if not self.ev.wait(timeout):
            return False, "timeout", None, None
        r = self.resp[0]
        stato = r[1]
        if stato == 0x02 or (stato == 0x00 and accetta_vuota):
            return True, "ok", None, r
        codice = int.from_bytes(bytes(r[3:7]), "little")
        testo = bytes(b for b in r[7:40] if 32 <= b < 127).decode(errors="ignore")
        return False, f"error 0x{stato:02X} {testo}", codice, r


def info(base):
    ok, why, _, r = base.cmd(0x03)
    if ok:
        anno, mese, giorno, h, m, s = r[11] | r[12] << 8, r[13], r[14], r[15], r[16], r[17]
        log(f"Base: USB {r[8]:02X}{r[7]:02X}:{r[10]:02X}{r[9]:02X}, build {anno}-{mese:02d}-{giorno:02d} {h:02d}:{m:02d}:{s:02d}")
    else:
        log(f"Base: {why}")
    ok, why, _, r = base.cmd(0x55)
    avb = r[3] if ok else None
    log(f"BASE Avnera:     {'version %d' % avb if ok else why}")
    ok, why, _, r = base.cmd(0x54)
    log(f"Headset status:  {'raw ' + ' '.join('%02X' % b for b in r[3:6]) if ok else why}")
    ok, why, _, r = base.cmd(0x7C)
    if ok:
        log(f"Battery:         {r[3] & 0x7F}%{' (charging)' if r[3] & 0x80 else ''}")
    ok, why, _, r = base.cmd(0x83, b"\x01")
    if ok:
        anno, mese, giorno = r[11] | r[12] << 8, r[13], r[14]
        log(f"Headset: build {anno}-{mese:02d}-{giorno:02d}")
    else:
        log(f"Headset info:    {why} (harmless if the other headset lines are ok)")
    ok, why, _, r = base.cmd(0xDA, b"\x0A")
    log(f"HEADSET MCU:     {'version %d' % int.from_bytes(bytes(r[3:5]), 'little') if ok else why}")
    ok, why, _, r = base.cmd(0xD6, b"\x0A")
    avc = r[3] if ok else None
    log(f"HEADSET Avnera:  {'version %d' % avc if ok else why}")
    if avb != 43:
        log("  -> BASE Avnera not ok: run 'fix-base'")
    if avc != 43:
        log("  -> HEADSET Avnera not ok: run 'fix-headset' (headset on and docked)")
    if avb == 43 and avc == 43:
        log("All good.")
        log("If this tool helped you: https://paypal.me/d4rky06  (optional, thank you!)")


def ripara(base, t):
    img = carica_immagine(t)
    log(f"=== WRITING {t['nome']} - DO NOT UNPLUG ANYTHING ===")
    c, p = t["start"]
    ok, why, _, _ = base.cmd(c, p, timeout=15.0, accetta_vuota=True)
    if not ok:
        log(f"Start failed ({why}), retrying in 1 s")
        time.sleep(1.0)
        ok, why, _, _ = base.cmd(c, p, timeout=15.0, accetta_vuota=True)
    if not ok:
        sys.exit(f"Start failed: {why}. No data written.")
    n = (len(img) + CHUNK - 1) // CHUNK
    tollerati = 0
    for i in range(n):
        blocco = t["prefix"] + img[i * CHUNK:(i + 1) * CHUNK]
        ok, why, codice, _ = base.cmd(t["data"], blocco, timeout=5.0, accetta_vuota=True)
        if not ok and codice == SLAVE_TIMEOUT and t["tollera_slave_timeout"]:
            tollerati += 1
            ok = True
        if not ok:
            sys.exit(f"Aborted at block {i + 1}/{n}: {why}")
        if (i + 1) % 256 == 0 or i + 1 == n:
            log(f"  {i + 1}/{n} blocks ({100 * (i + 1) // n}%)")
    if tollerati:
        log(f"  SLAVE_TIMEOUT tolerated: {tollerati}")
    c, p = t["end"]
    ok, why, _, _ = base.cmd(c, p, timeout=15.0, accetta_vuota=True)
    log(f"End of update: {why}")
    if not ok:
        sys.exit("End command not accepted.")
    c, p = t["reset"]
    ok, why, _, _ = base.cmd(c, p, timeout=3.0, accetta_vuota=True)
    log(f"Reset: {why}")


def main():
    azione = sys.argv[1] if len(sys.argv) > 1 else "info"
    if azione not in ("info",) + tuple(TARGET):
        sys.exit(__doc__)
    base = Base()
    try:
        if azione == "info":
            info(base)
            return
        ripara(base, TARGET[azione])
    finally:
        base.close()
    log("Waiting 15 s for the reboot...")
    time.sleep(15)
    base = Base()
    try:
        info(base)
    finally:
        base.close()


if __name__ == "__main__":
    main()
