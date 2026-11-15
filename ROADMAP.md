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

## v0.2.0 - Everyday use 📋

- 📋 **Tray icon** with battery %, low-battery notification (e.g. below 15 %)
- 📋 **Start with Windows** and minimize to tray instead of closing
- 📋 **Export diagnostic report**: one file with versions, chip status and recent ACC errors, to attach to an issue
- 📋 **Backup / restore settings** (EQ, mic, mix) to a file, automatic backup before every firmware update
- 📋 Firmware page: progress bar per chip, collapsible log

## v0.3.0 - Game profiles 📋🔬

- 🔬 **Write EQ band frequency and bandwidth** (capture the command with the ACC plugin's HID log)
- 📋 **Import / export ACC EQ files**, so community presets work directly
- 📋 **Profile library** for popular games (Warzone / CoD, Valorant, CS2, Fortnite, Apex, Siege, racing, music, movies)
- 📋 **Automatic profile switching** when a game starts (by process name), back to the previous one when it closes
- 📋 Share your own profiles as files

## v0.4.0 - Pairing repair 🔬

- 🔬 **Re-pair base and headset** (commands `0x5B` / `0xFC` identified, not implemented) for units where both radio
  chips are at 43 but the headset still won't connect
- 🔬 Processors (TX_MCU / RX_MCU) out of "experimental" once confirmed on more units

## v0.5.0 - Polish 📋

- 📋 Languages: English, Italian, Portuguese, Spanish
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
