"""
a50_update.py - firmware updater for the ASTRO A50 Gen 4 (base "Mimas", USB 9886:002C), using a LOCAL .afw file.

    python a50_update.py inspect FILE.afw
        Read-only: shows what is inside the .afw and what is installed on your device.

    python a50_update.py update FILE.afw [--only tx_radio,rx_radio,tx_mcu,rx_mcu] [--force] [--experimental]
        Updates only the components whose version differs (or all selected ones with --force).
        tx_mcu / rx_mcu (the main processors) are EXPERIMENTAL and need --experimental.

Get the .afw file yourself (for example from your own ASTRO Command Center installation). This tool never
downloads anything and no ASTRO firmware is distributed with it.

Sequences reconstructed from ASTRO Command Center 1.0.226 (see ../PROTOCOL.md):
  tx_mcu   RESET_DFU 0x02 -> base re-enumerates as 9886:002A (bootloader, usage page 0xFF31, report id 0)
           start 0x42, data 0x43 (60 B), end 0x44, reset 0x01
  tx_radio start 0x48, data 0x49 (32 B), end 0x4A, reset 0x01                                  [tested]
  rx_mcu   RESET_DFU 0x82 [0A] -> headset bootloader (through the base)
           start 0xF2 [64], data 0xF3 [0A]+58 B, end 0xF4 [28], reset 0x81 [0A]
  rx_radio start 0xF8 [64], data 0xF9 [0A]+32 B, end 0xFA [28], reset 0x81 [0A]                 [tested]
Pairing (0x5B / 0xFC) is NOT touched.

Close ASTRO Command Center first. Base on USB in PC mode, headset charged, ON and DOCKED.
USE AT YOUR OWN RISK. Not affiliated with ASTRO Gaming or Logitech.
"""
import io
import os
import re
import sys
import threading
import time
import zipfile

try:
    import pywinusb.hid as hid
except ImportError:
    sys.exit("Missing library: python -m pip install pywinusb")

VID, PID_APP, PID_BOOT = 0x9886, 0x002C, 0x002A
SLAVE_TIMEOUT = 0x01000001
ORDER = ["tx_mcu", "tx_radio", "rx_mcu", "rx_radio"]  # same order as ACC

COMPONENTS = {
    "tx_mcu": dict(label="Base processor (TX_MCU)", pattern=r"mimastx_v(\d+)", afw_key="tm", tested=False,
                   reset_dfu=(0x02, b""), boot_pid=PID_BOOT,
                   start=(0x42, b""), data=0x43, prefix=b"", chunk=60, end=(0x44, b""), final=(0x01, b"")),
    "tx_radio": dict(label="Base radio chip (TX_RADIO)", pattern=r"avneratx_v(\d+)", afw_key="tr", tested=True,
                     reset_dfu=None, start=(0x48, b""), data=0x49, prefix=b"", chunk=32,
                     end=(0x4A, b""), final=(0x01, b"")),
    "rx_mcu": dict(label="Headset processor (RX_MCU)", pattern=r"mimasrx_v(\d+)", afw_key="rm", tested=False,
                   reset_dfu=(0x82, b"\x0A"), start=(0xF2, b"\x64"), data=0xF3, prefix=b"\x0A", chunk=60,
                   end=(0xF4, b"\x28"), final=(0x81, b"\x0A")),
    "rx_radio": dict(label="Headset radio chip (RX_RADIO)", pattern=r"avnerarx_v(\d+)", afw_key="rr", tested=True,
                     reset_dfu=None, start=(0xF8, b"\x64"), data=0xF9, prefix=b"\x0A", chunk=33,
                     end=(0xFA, b"\x28"), final=(0x81, b"\x0A")),
}


def log(msg):
    print(time.strftime("%H:%M:%S"), msg, flush=True)


PROGRESS = None  # optional callback(component, done, total) set by the A50 Control app


def progress(key, done, total):
    if PROGRESS:
        try:
            PROGRESS(key, done, total)
        except Exception:
            pass


# --------------------------------------------------------------------------- .afw
def read_afw(path):
    """Return {component: (version, bytes)} and the release notes text."""
    raw = bytearray(open(path, "rb").read())
    if raw[:2] == b"AG":
        raw[:2] = b"PK"
    z = zipfile.ZipFile(io.BytesIO(bytes(raw)))
    comps, notes = {}, ""
    for name in z.namelist():
        base = os.path.basename(name)
        if base.lower() == "afw_notes.txt":
            notes = z.read(name).decode(errors="replace")
            continue
        for key, c in COMPONENTS.items():
            m = re.match(c["pattern"], base)
            if m:
                comps[key] = (int(m.group(1)), z.read(name))
    return comps, notes


# --------------------------------------------------------------------------- transport
class Link:
    """HID link to the base (app mode 002C, usage page 0xFF32, report id 2) or to its bootloader
    (002A, usage page 0xFF31, report id 0)."""

    def __init__(self, pid=PID_APP, wait=0.0):
        end = time.time() + wait
        while True:
            self.dev = None
            for d in hid.HidDeviceFilter(vendor_id=VID, product_id=pid).get_devices():
                try:
                    d.open()
                except Exception:
                    continue
                page = d.hid_caps.usage_page
                if page in (0xFF32, 0xFF31) or (pid == PID_BOOT and page >= 0xFF00):
                    self.dev = d
                    break
                d.close()
            if self.dev or time.time() >= end:
                break
            time.sleep(0.5)
        if self.dev is None:
            raise RuntimeError(f"device 9886:{pid:04X} not found")
        self.page = self.dev.hid_caps.usage_page
        self.rid = 0x02 if self.page == 0xFF32 else 0x00
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

    def cmd(self, c, payload=b"", timeout=5.0, accept_empty=True):
        """Returns (ok, text, error_code, data)."""
        seq = self.seq & 3
        self.seq += 1
        pkt = [self.rid, c, (len(payload) & 0x3F) | (seq << 6)] + list(payload)
        pkt += [0] * (self.out_len - len(pkt))
        self.resp.clear()
        self.ev.clear()
        try:
            self.dev.send_output_report(pkt)
        except Exception as e:
            return False, f"send failed ({e})", None, None
        end = time.time() + timeout
        while True:
            left = end - time.time()
            if left <= 0 or not self.ev.wait(left):
                return False, "timeout", None, None
            self.ev.clear()
            while self.resp:
                r = self.resp.pop(0)
                if len(r) < 3:
                    continue
                status = r[1]
                if status != 0 and (r[2] >> 6) != seq:
                    continue  # stale answer
                n = min(r[2] & 0x3F, len(r) - 3)
                data = bytes(r[3:3 + n])
                if status == 0x02 or (status == 0x00 and accept_empty):
                    return True, "ok", None, data
                code = int.from_bytes(bytes(r[3:7]), "little") if len(r) >= 7 else None
                text = bytes(b for b in r[7:40] if 32 <= b < 127).decode(errors="ignore")
                return False, f"error 0x{status:02X} {text}", code, data


# --------------------------------------------------------------------------- versions
def installed_versions(link):
    v = {}
    ok, _, _, d = link.cmd(0x03, accept_empty=False, timeout=2)
    v["tx_mcu"] = int.from_bytes(d[21:25], "little") if ok and len(d) >= 25 else None
    ok, _, _, d = link.cmd(0x55, accept_empty=False, timeout=2)
    v["tx_radio"] = d[0] if ok and d else None
    ok, _, _, d = link.cmd(0xDA, b"\x0A", accept_empty=False, timeout=3)
    v["rx_mcu"] = int.from_bytes(d[:4], "little") if ok and len(d) >= 4 else None
    ok, _, _, d = link.cmd(0xD6, b"\x0A", accept_empty=False, timeout=3)
    v["rx_radio"] = d[0] if ok and d else None
    return v


# --------------------------------------------------------------------------- flashing
def chunks(data, size, prefixed):
    """Split exactly like ACC: for headset (prefixed) packets a full chunk is size-1, rounded down to even."""
    pos = 0
    while pos < len(data):
        n = min(size, len(data) - pos)
        if prefixed and n == size:
            n -= 1
            if n & 1:
                n -= 1
        yield data[pos:pos + n]
        pos += n


def write_component(link, key, data):
    c = COMPONENTS[key]
    log(f"--- {c['label']}: {len(data)} bytes")
    cmd, pl = c["start"]
    ok, why, _, _ = link.cmd(cmd, pl, timeout=15)
    if not ok:
        log(f"start failed ({why}), retrying in 1 s")
        time.sleep(1)
        ok, why, _, _ = link.cmd(cmd, pl, timeout=15)
    if not ok:
        raise RuntimeError(f"start refused: {why} (nothing written)")
    blocks = list(chunks(data, c["chunk"], bool(c["prefix"])))
    tolerated = 0
    for i, b in enumerate(blocks):
        ok, why, code, _ = link.cmd(c["data"], c["prefix"] + b, timeout=20)
        if not ok and code == SLAVE_TIMEOUT and c["prefix"]:
            tolerated += 1
            ok = True
        if not ok:
            raise RuntimeError(f"aborted at block {i + 1}/{len(blocks)}: {why}")
        if (i + 1) % 20 == 0 or i + 1 == len(blocks):
            progress(key, i + 1, len(blocks))
        if (i + 1) % 500 == 0 or i + 1 == len(blocks):
            log(f"  {i + 1}/{len(blocks)} blocks ({100 * (i + 1) // len(blocks)}%)")
    if tolerated:
        log(f"  SLAVE_TIMEOUT tolerated: {tolerated}")
    cmd, pl = c["end"]
    ok, why, _, _ = link.cmd(cmd, pl, timeout=20)
    log(f"  end: {why}")
    if not ok:
        raise RuntimeError("end command not accepted")
    cmd, pl = c["final"]
    ok, why, _, _ = link.cmd(cmd, pl, timeout=3)
    log(f"  reset: {why} (a timeout here is normal: the device reboots)")


def write_with_retries(link, key, data, attempts=3):
    """A failed write is restarted from the start command (blocks carry no address, so a single block
    must never be resent)."""
    for n in range(1, attempts + 1):
        try:
            write_component(link, key, data)
            return
        except RuntimeError as e:
            log(f"  attempt {n}/{attempts} failed: {e}")
            if n == attempts:
                raise
            log("  restarting this component from the beginning in 3 s...")
            time.sleep(3)


def update_component(key, data):
    """Runs one component end to end, handling the bootloader switch. Returns a fresh app-mode Link."""
    c = COMPONENTS[key]
    if key == "tx_mcu":
        link = Link(PID_APP)
        log("  rebooting the base into update mode (RESET_DFU)")
        link.cmd(*c["reset_dfu"], timeout=2)
        link.close()
        boot = Link(PID_BOOT, wait=20)
        log(f"  bootloader found (9886:002A, usage page 0x{boot.page:04X})")
        try:
            write_with_retries(boot, key, data)
        finally:
            boot.close()
    else:
        link = Link(PID_APP, wait=10)
        try:
            if c["reset_dfu"]:
                log("  rebooting the headset into update mode (RESET_DFU)")
                link.cmd(*c["reset_dfu"], timeout=3)
                time.sleep(5)
            write_with_retries(link, key, data)
        finally:
            link.close()
    log("  waiting for the device to restart...")
    time.sleep(12)
    return Link(PID_APP, wait=30)


def boot_present():
    return bool(hid.HidDeviceFilter(vendor_id=VID, product_id=PID_BOOT).get_devices())


# --------------------------------------------------------------------------- CLI
def main():
    args = sys.argv[1:]
    if len(args) < 2 or args[0] not in ("inspect", "update"):
        sys.exit(__doc__)
    action, path = args[0], args[1]
    force = "--force" in args
    experimental = "--experimental" in args
    only = None
    if "--only" in args:
        only = [x.strip() for x in args[args.index("--only") + 1].split(",")]
        bad = [x for x in only if x not in COMPONENTS and x != "none"]
        if bad:
            sys.exit(f"unknown component(s): {bad}. Use: {', '.join(ORDER)}")

    comps, notes = read_afw(path)
    first = notes.strip().split("\n\n")[0] if notes else ""
    log(f"File: {os.path.basename(path)}")
    if first:
        log("Release notes (latest entry):\n" + "\n".join("    " + l for l in first.splitlines() if l.strip("-")))

    if boot_present():
        log("NOTE: the base is in update mode (9886:002A) - a previous base update did not finish.")
        if action == "update" and experimental and (only is None or "tx_mcu" in only) and "tx_mcu" in comps:
            log("=== finishing the base processor update ===")
            boot = Link(PID_BOOT)
            log(f"  bootloader found (9886:002A, usage page 0x{boot.page:04X})")
            try:
                write_with_retries(boot, "tx_mcu", comps["tx_mcu"][1])
            finally:
                boot.close()
            log("  waiting for the base to restart...")
            time.sleep(12)
            only = [x for x in (only or []) if x != "tx_mcu"] or ["none"]
        else:
            sys.exit("Run: update FILE.afw --only tx_mcu --experimental  to finish it, or let ACC recover it.")

    link = Link(PID_APP, wait=5)
    inst = installed_versions(link)
    link.close()
    plan = []
    log(f"{'component':32} {'in file':>8} {'installed':>10}  action")
    for key in ORDER:
        if key not in comps:
            continue
        c = COMPONENTS[key]
        fv, iv = comps[key][0], inst.get(key)
        selected = only is None or key in only
        differs = fv != iv
        do = selected and (differs or force)
        if do and not c["tested"] and not experimental:
            act = "SKIP (experimental: add --experimental)"
            do = False
        else:
            act = "UPDATE" if do else ("up to date" if not differs else "skip")
        log(f"{c['label']:32} {fv:>8} {str(iv):>10}  {act}")
        if do:
            plan.append(key)

    if action == "inspect":
        return
    if not plan:
        log("Nothing to do.")
        return
    log("=== UPDATING - do not unplug the base, keep the headset on and docked ===")
    for key in plan:
        link = update_component(key, comps[key][1])
        link.close()
    link = Link(PID_APP, wait=10)
    after = installed_versions(link)
    link.close()
    log("Result:")
    for key in plan:
        fv, av = comps[key][0], after.get(key)
        log(f"  {COMPONENTS[key]['label']:32} expected {fv}, now {av}  {'OK' if fv == av else 'CHECK'}")


if __name__ == "__main__":
    main()
