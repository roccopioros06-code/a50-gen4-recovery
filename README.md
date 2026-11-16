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

`a50_tool.py` only writes the two Avnera radio chips, verifies the image MD5 before writing, and never touches the MCUs.
**Do not keep re-running the ACC update** - every attempt is another chance to break pairing.

## A50 Control - replacement app for ACC (`app\`)

An open-source, lightweight alternative to ASTRO Command Center: no login, no Logitech servers.

<p align="center"><img src="docs/screenshots/home.png" alt="A50 Control: Home" width="820"></p>

| Equalizer | Game profiles |
|---|---|
| <img src="docs/screenshots/equalizer.png" alt="Equalizer" width="400"> | <img src="docs/screenshots/profiles.png" alt="Game profiles" width="400"> |
| **Microphone** | **Your colours** |
| <img src="docs/screenshots/microphone.png" alt="Microphone" width="400"> | <img src="docs/screenshots/colors.png" alt="Colours" width="400"> |

- Status: battery, docked/on, base and headset firmware, radio chip health
- Equalizer: 3 presets, 5 bands (-7..+7 dB), rename presets
- Microphone: level, sidetone, noise gate (Streaming / Night / Home / Tournament), mic EQ, **quick setups**
  (Chat, Competitive, Streaming, Late night, Noisy room, or your own) and a **mic test** (live level meter,
  live frequency analyser, record 5 s and play back; audio never leaves your PC)
- **PC mic EQ** (optional, needs the free [Equalizer APO](https://sourceforge.net/projects/equalizerapo/)):
  Razer-style 10-band EQ for your voice with presets (Clear voice, Broadcast, Warm, Less boomy, Softer S,
  Weak mic), preamp and low cut. Only the A50 voice input is touched; your other Equalizer APO settings stay as they are.
- Mix: default game/voice balance, alert volume, stream port mix
- **Save to headset** to keep settings after power-off
- **Firmware**: update the headset from a local `.afw` file (see below)
- Maintenance: Diagnose / Fix radio chips (the tool above, built in)
- **Game profiles**: ready-made EQ curves for popular games (CoD/Warzone, Valorant, CS2, Siege, Apex, Fortnite,
  racing, music...), editable and shareable, with **automatic switching** when a game starts. A profile can
  also switch the **microphone setup** (e.g. Competitive mic for shooters), and everything goes back when the game closes
- **Keyboard shortcuts** that work in games: Ctrl+Alt+1/2/3 EQ preset, Ctrl+Alt+P next profile, Ctrl+Alt+M next mic setup,
  Ctrl+Alt+B battery
- **Battery history**: 24 h chart, time left / time to full, typical hours per charge
- **Tray icon** with the battery level, low-battery alert, start with Windows
- **Backup / restore** of all settings (also automatic before firmware updates)
- **Diagnostic report** to attach when you ask for help
- **Colours**: pick any colour for the app, the headset lights, the shell and the cushions

### Run it

- **Windows app (no Python needed):** download `A50 Control.exe` from the
  [Releases](https://github.com/roccopioros06-code/a50-gen4-recovery/releases) page and double-click it.
  It is not code-signed, so Windows SmartScreen may warn you: *More info* > *Run anyway*.
- **From source:** double-click `app\A50 Control.bat` (installs `pywinusb`, `pillow` and `pystray` if missing; the window needs Microsoft Edge, already on Windows 10/11).
- **Build the .exe yourself:** double-click `app\Build EXE.bat` (uses PyInstaller; output in `app\dist`).

Close ACC first: only one program can talk to the base at a time.

### Firmware update

The **Firmware** page updates the headset like ACC does, but from a file **you provide**:

> [!IMPORTANT]
> **This project does not include or download any firmware.** Get the `.afw` file yourself, for example from your own
> ACC installation (`%LOCALAPPDATA%\Astro Gaming\ASTRO Command Center\Astro A50 Wireless (Mimas)\FW\` or
> `C:\Program Files (x86)\Astro Gaming\ASTRO Command Center\assets\forced_fw\`). The app finds it there automatically,
> or you can pick any `.afw` with *Choose .afw file...*.

- **Guided and split**: one chip at a time, in the safest order (radio chips first, processors last). The next step
  unlocks only after the previous one is **verified** by reading its version back.
- **Safety checks before every step**: ACC closed, base connected, headset docked and answering, battery at least 30%
  (or charging), firmware images intact (the radio chip images are compared with the known official ones), PC on mains power.
- The PC is kept awake while writing, and your settings are backed up before every step.
- It shows the version of each chip in the file and on your device, and only writes what differs.
- **Radio chips** (base TX_RADIO, headset RX_RADIO): tested.
- **Processors** (base TX_MCU, headset RX_MCU): **experimental**, off by default. Each has been rewritten successfully
  on one unit; enable *Include processors (experimental)* to use them.
- Nothing else talks to the base while writing (the cause of ACC's failures), and each chip is retried from the start if a block fails.
- **Pairing is never touched.**

Same thing from the command line: `python tool\a50_update.py inspect FILE.afw` /
`python tool\a50_update.py update FILE.afw [--only tx_radio,rx_radio] [--force] [--experimental]`.

### Look and colours

The window is drawn with HTML/CSS inside **Microsoft Edge in app mode** (already part of Windows 10/11: no address
bar, no extra install). The app itself only listens on `127.0.0.1` with a random port and a secret token, so
nothing outside your PC can reach it.

The Home page shows an **original drawing** of a headset on its base station: the base lights show the active EQ
preset (1/2/3) and the battery level. In *Settings > Colours* you can pick any colour for the app, the headset
lights, the shell and the cushions. No product photos are used or included.

Settings commands are based on [eh-fifty](https://github.com/tdryer/eh-fifty). Early version: feedback and issues welcome. Planned updates: [ROADMAP.md](ROADMAP.md).

Built with the help of an AI assistant (Claude). Every feature was tested on my own A50 Gen 4 before release.
If something doesn't work on yours, please open an issue with the diagnostic report (*Maintenance > Diagnostic report*).

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
