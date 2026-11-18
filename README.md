# Vision Detection

Continuously detect foreign objects inside a circular inspection area using a
MindVision camera and a clean reference image. Send a confirmed alarm request
over wired LAN (Modbus TCP) to a Haiwell AC16S0T PLC. PLC ladder logic drives
the buzzer/light output.

## Web dashboard

Product analysis, architecture strategy, and function-by-function evaluations are organized in [docs/README.md](docs/README.md).

The `UI/` dashboard connects through `vision_server.py` for real camera preview, inspection status, alarm evidence, and start/stop/reset controls. Build it once with `pnpm install --frozen-lockfile` and `pnpm build` inside `UI/`, then run `python vision_server.py --plc-config plc_config.json` from the repository root and open http://127.0.0.1:8765. Click **Start inspection** to open the camera. Omit `--plc-config` for camera-only operation. Stop other camera sessions first.

See [UI/README.md](UI/README.md) for setup, development, and operator details.

## Current behavior

- Compares live images against the fixed reference `RefPic/Ref1.png`.
- Confirms an alarm after 3 consecutive positive frames by default.
- Continues monitoring after an alarm; press **R** in preview after 3 clear frames to reset and rearm.
- Saves one evidence set per alarm: raw PNG in `TestPic/`, annotated PNG and mask in `Results/`.
- Updates PLC alarm, heartbeat and vision health in a background thread; reconnects after communication failures.
- Camera, processing or storage failures stop monitoring. PLC logic must handle lost heartbeat/unhealthy vision.

## Setup

1. Install Python, OpenCV and NumPy:

   ```powershell
   python -m pip install opencv-python numpy
   ```

2. For camera mode, install the MindVision Windows SDK and camera driver.
   Match Python/SDK architecture (normally 64-bit). Close the vendor camera
   application before running this project.
3. Capture a clean reference as `RefPic/Ref1.png` using the same camera position,
   resolution, orientation and lighting as live inspection.
4. For PLC operation, connect PC and PLC by Ethernet, configure IP addresses in
   the same subnet, and enable the PLC Modbus TCP server. Set `plc_config.json`
   to the actual connection and reserved memory addresses. If missing, copy
   `plc_config.example.json` first; its IP is only a placeholder.

## Run

Run commands from the project folder.

**Continuous camera inspection with PLC output requests:**

```powershell
python main.py --camera --show --plc-config plc_config.json
```

**Continuous camera inspection without PLC communication:**

```powershell
python main.py --camera --show
```

Stop camera mode with **Q/Esc** in the preview or **Ctrl+C** in the terminal.
Press **R** with the preview focused to reset after `--confirm-frames` consecutive
clear frames. A later detection triggers a new alarm and evidence set.
Omit `--show` to run without preview windows.

**Offline test: process existing images in `TestPic/` once and exit:**

```powershell
python main.py
```

Offline mode saves results in `Results/` and never communicates with the PLC.
Add `--show` to preview each result; press a key to advance. Matching output
filenames are overwritten on repeated offline runs.

## Command parameters

| Parameter | Default | Purpose |
|---|---|---|
| `--camera` | Off | Enable continuous camera inspection |
| `--show` | Off | Display results |
| `--plc-config plc_config.json` | Disabled | Enable PLC communication; requires `--camera` |
| `--camera-index 0` | `0` | Select camera by device index |
| `--sdk-dir "C:\path\to\SDK\x64"` | System DLL lookup | Directory containing `MVCAMSDK_X64.dll` or 32-bit `MVCAMSDK.dll` |
| `--frame-rate 10` | `10` fps | Requested capture rate; actual inspection rate may be lower |
| `--light-frequency 50` | `50` Hz | Anti-flicker frequency: `50` or `60` |
| `--confirm-frames 3` | `3` | Consecutive positive frames required for an alarm |
| `--flip-vertical` | Off | Flip camera frames to match reference orientation |
| `--exposure-us 10000` | Ignored | Legacy option; automatic exposure is enabled |
| `--help` | — | Show command help |

## PLC configuration

Use your PLC's actual IP (currently `192.168.1.111`), port `502`, and unit ID
(currently `1`). Verify these example memory assignments are free in your PLC:

| JSON setting | Example address | PLC function |
|---|---:|---|
| `alarm_coil` | `3072` (M0) | Latched alarm request |
| `heartbeat_coil` | `3073` (M1) | Toggling heartbeat |
| `healthy_coil` | `3074` (M2) | Recent successful inspection |
| `reset_coil` | `3075` (M3) | Operator reset request (verify this bit is free) |

Addresses are zero-based Modbus offsets. PLC ladder must latch the alarm request
and drive the selected output (e.g. Y0), monitor heartbeat changes and vision
health, and handle operator reset. Python does not directly write Y0. Restarting
Python clears its request; it must not automatically reset the PLC alarm latch.

For **R** to reset the PLC latch, reserve M3 for Python and add this reset rung
in HaiwellHappy (adapt M10/M11 to your actual program):

```text
       M3        M0        M2        M11
|-----[ ]-------[/ ]------[ ]-------[/ ]----( RST M10 )---|
```

M11 represents communication fault. Python clears M0 and sets M2 healthy before
raising M3, then lowers M3 after approximately 1 s (or sooner if inspection
becomes stale or a new alarm occurs). Reset is refused when the area is not
clear, the PLC connection is unavailable, or `reset_coil` is not configured.
Pending reset requests are cancelled on communication failure and are not
replayed on reconnection. A Modbus acknowledgment confirms the bit write,
not that M10 or Y0 actually cleared. Fault conditions driving Y0 can keep it ON.

Timing settings in JSON: `timeout` = 1 s per socket operation,
`heartbeat_interval` = 0.5 s between update cycles, and `inspection_timeout` = 5 s
before inspection is considered stale. Configure the PLC watchdog accordingly.
