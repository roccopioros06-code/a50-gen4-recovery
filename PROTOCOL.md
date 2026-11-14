# ASTRO A50 Gen 4 ("Mimas") - base station USB protocol

Reconstructed from ACC 1.0.226 logs, analysis of its executable, the
[eh-fifty](https://github.com/tdryer/eh-fifty) project and tests on real hardware.
✅ = verified on a real unit.

## USB device

| Mode | VID:PID | Notes |
|---|---|---|
| Normal (app) | `9886:002C` | control HID interface: usage page `0xFF32`, 64-byte reports ✅ |
| Base DFU bootloader | `9886:002A` | only during the base MCU update |

Works with the stock Windows HID driver (e.g. `pywinusb`) ✅.

## Packet format ✅

Request (output report, 64 bytes, zero padded):

```
[0x02] [cmd] [L] [payload ...]
         L = (payload_length & 0x3F) | (seq << 6)      seq = 2-bit counter
```

Response (input report):

```
[0x02] [status] [L] [data ...]
   status: 0x02 = ok, 0x01 = error, 0x00 = no data
   L: data length, top 2 bits echo the request seq
   on error: bytes 3..6 = code (little endian), then ASCII text, e.g. "HID_ERROR_AVNERA_ERROR"
```

Error codes seen: `21` HID_ERROR_AVNERA_ERROR, `0x01000001` HID_ERROR_SLAVE_TIMEOUT (headset unreachable),
`0x01000003` HID_ERROR_SLAVE_COMM_ERROR, `1` HID_ERROR_UNHANDLED_PACKET.

Commands with the high bit set (`0x80`) are forwarded to the headset and carry a leading payload byte (usually `0x0A`).

## Read commands

| Cmd | Payload | Meaning | Example data |
|---|---|---|---|
| `0x03` | - | base info: USB IDs + firmware build date ✅ | `...86 98 2C 00 E6 07 04 14 09 04 27` = 9886:002C, 2022-04-20 09:04:39 |
| `0x55` | - | base Avnera version ✅ | `2B` = 43 |
| `0x54` | - | headset power/dock status ✅ | |
| `0x7C` | - | battery ✅ | bits 0-6 = %, bit 7 = charging (consistent with tests) |
| `0x72` | - | game/voice balance ✅ | |
| `0x83` | `01` | headset info + build date (often times out off-dock) | `...E5 07 0C 06` = 2021-12-06 |
| `0xDA` | `0A` | headset MCU version ✅ | `1C 9C` = 39964 |
| `0xD6` | `0A` | headset Avnera version ✅ | `2B` = 43 |

Settings (EQ, mic, noise gate, sidetone...): see eh-fifty (`0x61` save, `0x62`-`0x7B` get/set).

## Firmware update

`.afw` files are ZIP archives whose first local header signature `PK` was replaced by `AG`.
Restore `PK` to open them. Contents: 4 images + release notes.

| ACC index | Component | File | start / data / end / final |
|---|---|---|---|
| 0 | TX_MCU (base) | `mimastx_v40372_20apr2022.bin` | `0x42` / `0x43` (60 B) / `0x44` / `0x01` - needs RESET_DFU first (PID 002A) |
| 1 | RX_MCU (headset) | `mimasrx_v39964_6dec2021.bin` | `0xF2` / `0xF3` / `0xF4` / `0x81` - needs RESET_DFU first |
| 2 | TX_RADIO (base Avnera) | `avneratx_v43_27Jun2019_r21.bin` | `0x48` / `0x49` (32 B) / `0x4A` / `0x01` ✅ |
| 3 | RX_RADIO (headset Avnera) | `avnerarx_v43_27Jun2019_r21.bin` | `0xF8 [64]` / `0xF9 [0A]+32 B` / `0xFA [28]` / `0x81 [0A]` ✅ |

Verified sequence for the Avnera chips (indices 2 and 3), implemented in `tool/a50_tool.py`:
1. start (wait up to ~15 s for the answer; retry once after 1 s like ACC);
2. every 32-byte block in order, no address (sequential write);
   for the headset a `SLAVE_TIMEOUT` on a data block is tolerated (as ACC does on some hardware revisions);
3. end command, then final command (reset);
4. verify with `0x55` (base) or `0xD6 [0A]` (headset): must answer 43.

The Avnera images are identical in the 2019 and 2022 packages
(MD5 TX `6f27ce7304020d501fbe79f9adb8de76`, RX `a42fc26cd382764bee66e57b72ae7125`).

**Golden rule:** nothing else may talk to the base while writing. ACC 1.0.226 polls the base from its main and
battery threads during updates; the resulting `invalid 'seq'` mix-up is the most likely root cause of failed updates.

### Pairing ("update base station mac" / "update headset mac")

After an update ACC creates a random ID (QUuid) and sends:
- to the base: `0x5B` with 4 bytes;
- to the headset: `0xFC [64]` with 8 more bytes (base + headset IDs).

If the headset part fails, base and headset IDs no longer match (alternating LEDs). Exact byte layout not yet verified.

MCU updates (indices 0 and 1) go through the DFU bootloader and are **not** reconstructed or tested here.

## Known firmware versions (from the official release notes inside the .afw files)

| Date | TX (base) | RX (headset) |
|---|---|---|
| 2018-11-12 | 33074.39 | 33080.39 |
| 2019-07-05 | 35155.43 | 34843.43 |
| 2020-08-02 | 36799.43 | 36179.43 |
| 2021-12-06 | 39933.43 | 39964.43 |
| **2022-04-20 (latest)** | **40372.43** | **39964.43** |

---
Free and open source. If this documentation helped you: [☕ Donate](https://paypal.me/d4rky06) (optional).
