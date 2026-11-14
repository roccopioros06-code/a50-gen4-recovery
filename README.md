# a50-gen4-recovery

Recovery tool for **ASTRO A50 Gen 4** (2019, base station "Mimas", USB `9886:002C`) units that look
"bricked" after a firmware update through ASTRO Command Center (ACC).

> [!WARNING]
> **No guarantees. Use at your own risk.** This is an unofficial, reverse-engineered tool, not affiliated
> with ASTRO Gaming or Logitech. It writes firmware to your device. It has been tested on **one** unit
> (Windows 11, ACC 1.0.226: base `40372.43`, headset `39964.43`). It may not work on yours, and in the worst
> case it can leave your headset in a worse state. Using it may void any remaining warranty.
> If your device is still under warranty, contact Logitech support first.

☕ **Free tool. If it saved your headset, you can [buy me a coffee](https://paypal.me/d4rky06).** Totally optional.

## Will this fix my headset?

Run **1 - Diagnose** first: it is read-only and tells you which case you are in.

| Situation | Fixed by this tool? |
|---|---|
| A50 **Gen 4** after a failed ACC update: base `0x55` error / `HID_ERROR_AVNERA_ERROR`, or headset shown as `xxxxx.0` | ✅ Yes, that's what it's for |
| Base LEDs alternating **and** diagnose shows an Avnera chip not at 43 | ✅ Yes |
| Both Avnera chips at 43 but headset still won't connect (pairing only) | ❌ Not yet (pairing commands identified, not implemented) |
| Base stuck in bootloader (`9886:002A`), base or headset MCU damaged | ❌ No |
| Dead battery, charging port/contacts, physical damage, base not seen by the PC at all | ❌ No, hardware |
| A50 Gen 3, Gen 5, A50 X, A40, A20 | ❌ No, different hardware/protocol |

## Symptoms

- Base station LEDs keep alternating (1&3 / 2&4) instead of showing the battery
- ACC no longer detects the device; its log (`%LOCALAPPDATA%\Astro Gaming\ASTRO Command Center\Logs`) shows
  `cmd: 0x55 ... HID_ERROR_AVNERA_ERROR` and `device [x9886:x2C] is invalid after initialization`
- ACC shows the headset firmware as `xxxxx.0` (e.g. `39964.0`) and keeps asking to update
- `HID_ERROR_SLAVE_TIMEOUT` in the ACC log during the `RX_RADIO` step

## Cause

A Gen 4 update writes four chips: base MCU, base Avnera radio (TX_RADIO), headset MCU, headset Avnera radio (RX_RADIO).

1. The headset radio is written *through the base*. If that link times out, ACC aborts halfway
   (it only tolerates the timeout on some hardware revisions) and leaves the chip empty: version `.0`.
2. After every update ACC writes a **new random pairing code** to the base, then to the headset.
   If the headset part fails, base and headset no longer match: alternating LEDs.
3. During the update ACC keeps polling the base from other threads (battery, status...), mixing packets
   into the update (`invalid 'seq'` errors). On the unit this was developed on, the base Avnera chip
   died on the first cold power-on after the failed update.

The firmware is fine; the way it is written is not. Rewriting the Avnera chips with nothing else
talking to the base fixes it.

## Fix

Requirements: Windows, [Python 3](https://www.python.org/downloads/), ACC installed
(the official firmware is taken from `C:\Program Files (x86)\Astro Gaming\ASTRO Command Center\assets\forced_fw\*.afw`
or from ACC's download folder - **no ASTRO files are distributed here**).

1. Base on USB, mode switch on **PC**, headset **on and docked**, ACC closed.
2. Double-click `tool\run.bat` (installs `pywinusb` if missing; uses the standard Windows HID driver, no driver changes).
3. **1 - Diagnose** (read-only). It tells you which Avnera chip is not at version 43.
4. **2 - Fix BASE** and/or **3 - Fix HEADSET**. About 1 minute each. Do not unplug anything.
5. Unplug the base for 30 s, plug it back, diagnose again: both Avnera chips must report **43**.
6. Test wireless audio and mic with the headset off the dock.

🎉 **Did it work?** Please leave a ⭐ on the repo so others can find it, and if you want, [support the project](https://paypal.me/d4rky06).

Command line: `python a50_tool.py info | fix-base | fix-headset`.

The tool only writes the two Avnera radio chips, verifies the image MD5 before writing, and never touches the MCUs.
**Do not keep re-running the ACC update** - every attempt is another chance to break pairing.

## Optional: ACC plugin (`plugin\`)

A drop-in `HID.DLL` for ACC 1.0.226. It forwards everything to the real Windows `hid.dll` and patches ACC
**in memory only** (delete the DLL to go back to stock):

- logs every HID packet to `Logs\acc_guard_hid.log`
- blocks other ACC threads from talking to the base while firmware or pairing is being written
- makes ACC always tolerate headset `SLAVE_TIMEOUT` on data blocks (only if ACC's bytes match 1.0.226)

Install: right-click `plugin\install.bat` > *Run as administrator*. Remove: `plugin\uninstall.bat`.
Source and build instructions in `plugin\acc_guard.c`.

## Protocol

See [PROTOCOL.md](PROTOCOL.md). Basic commands thanks to [eh-fifty](https://github.com/tdryer/eh-fifty).

## Support the project

This tool is and will stay **free**. If it saved your headset and you want to say thanks:
**[☕ Donate](https://paypal.me/d4rky06)**. Donations are entirely optional, buy no support or warranty, and don't change the
"use at your own risk" terms above.

## License

MIT - see [LICENSE](LICENSE).
