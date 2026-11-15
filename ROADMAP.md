# Roadmap

Planned updates for **A50 Control** and the recovery tools. Order and contents can change based on feedback.
Ideas and bug reports are welcome in [Issues](https://github.com/roccopioros06-code/a50-gen4-recovery/issues).

Legend: ✅ done · 🔨 in progress · 📋 planned · 🔬 needs research / testers

## v0.1.0 - First release ✅

- ✅ Status: battery, docked/on, base and headset firmware
- ✅ Equalizer (3 presets, 5 bands), microphone, noise gate, sidetone, mix
- ✅ Maintenance: diagnose and repair the Avnera radio chips after a failed ACC update
- ✅ Firmware update from a local `.afw` file (radio chips tested, processors experimental, pairing untouched)
- ✅ Standalone `A50 Control.exe` (no Python needed)

## v0.2.0 - Everyday use ✅

- ✅ **Tray icon** with battery %, low-battery notification (10 / 15 / 20 / 30 %, or off)
- ✅ **Start with Windows** (in the tray) and keep running in the tray when the window is closed
- ✅ **Export diagnostic report**: one file with versions, chip status, USB state and recent ACC errors (Windows user name removed)
- ✅ **Backup / restore settings** (EQ, mic, mix) to a file, automatic backup before every firmware update or repair
- ✅ Firmware page: progress bar per chip, collapsible log
- ✅ Reconnects by itself when the base is unplugged and plugged back

## v0.3.0 - Game profiles and new interface ✅

- ✅ **Profile library** for popular games (CoD / Warzone, Valorant, CS2, Siege, Apex, Fortnite, PUBG, Overwatch,
  Battlefield, racing, sports, open world, music, movies, voice)
- ✅ Every profile can be **edited** (saved as your version, with reset to default) or you can make **your own**
- ✅ **Automatic switching** when a game starts (by program name), previous EQ restored when it closes
- ✅ **Export / import** profiles as files to share them
- ✅ **Microphone quick setups** (Chat, Competitive, Streaming, Late night, Noisy room) plus your own
- ✅ **Mic test**: live level meter with hints, live frequency analyser, record 5 seconds and play back
- ✅ **Game scenes**: a game profile can also switch the microphone setup, restored when the game closes
- ✅ **Keyboard shortcuts** that work in games (EQ preset, next profile, next mic setup, battery)
- ✅ **Battery history**: 24 h chart, time left / to full, typical hours per charge
- ✅ **PC mic EQ** through Equalizer APO: 10 bands, presets, preamp, low cut, your own profiles
- ✅ **New interface**: redesigned from scratch (drag-to-edit EQ curves, drawn headset and base station with live
  preset and battery lights, free colour picker for app, lights, shell and cushions)
- ✅ **Headset mic EQ compare tool**: records you with each of the 3 headset mic presets and plays them back

## v0.4.0 - Microphone, frequencies and languages 📋

- 📋 **Guided Equalizer APO setup** inside the app (download, install, pick the A50 mic, restart) and a check that
  the PC mic EQ is really active on the A50 microphone
- 🔬 **Change the EQ band frequencies and width** (e.g. 80 Hz → 100 Hz; capture the command with the ACC plugin's HID log)
- 📋 **Headset mic EQ presets** with meaningful names instead of "Preset 0/1/2"
- 📋 **Languages**: English, Italian, Portuguese, Spanish
- 📋 **Import ACC EQ files**, so community presets work directly

## v0.5.0 - Pairing repair 🔬

- 🔬 **Re-pair base and headset** (commands `0x5B` / `0xFC` identified, not implemented) for units where both radio
  chips are at 43 but the headset still won't connect
- 🔬 Processors (TX_MCU / RX_MCU) out of "experimental" once confirmed on more units

## v0.6.0 - Polish 📋

- 📋 "New version available" notice (checks this repo's Releases only, never downloads firmware)

## Later / research 🔬

- 🔬 Other models: A50 Gen 3, A40 + MixAmp, A50 X (needs owners willing to share logs)
- 🔬 PlayStation and Xbox base variants: confirm everything works the same
- 🔬 Code signing, so Windows stops showing the SmartScreen warning

## How you can help

- **Test** on your unit (especially PS / Xbox bases) and post the *Diagnose* output in an issue
- **Report bugs** with the diagnostic report (from v0.2.0) or a screenshot
- **Share** EQ presets that work well for you
- ⭐ the repo so others can find it, and if you want, [buy me a coffee](https://paypal.me/d4rky06)
