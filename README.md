# Vision Detection

Detect foreign objects inside a circular inspection area using a MindVision
camera and a clean reference image. Use the web dashboard to view live inspection,
control the camera, and review alarm evidence. For automated signaling, the
system can send confirmed alarm requests over Modbus TCP to a Haiwell AC16S0T
PLC. PLC ladder logic drives the buzzer and light.

**[Open the dashboard on this computer](http://127.0.0.1:8765)** after starting
`python vision_server.py`. For a fresh checkout, follow the
[dashboard setup](#web-dashboard).

## Current behavior

- Compares live images against the fixed reference `RefPic/Ref1.png`.
- Confirms an alarm after three consecutive positive frames by default.
- Continues monitoring after an alarm. After three consecutive clear frames by default, use **Reset alarm** in the dashboard or press **R** in the CLI preview to rearm.
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
4. For PLC operation, connect the PC and PLC by Ethernet, configure IP addresses
   in the same subnet, and enable the PLC Modbus TCP server. If you do not have a
   local configuration, create one from the example and set the PLC connection
   and reserved coil addresses.

   ```powershell
   Copy-Item plc/plc_config.example.json plc_config.json
   ```

## Web dashboard

Install Node.js 22 and pnpm 10.34.3. From the repository root, build the UI and
start the local Python service.

```powershell
cd UI
pnpm install --frozen-lockfile
pnpm build
cd ..
python vision_server.py
```

Open <http://127.0.0.1:8765> and click **Start inspection**. Close any other
camera session first. To enable PLC output, launch the service with
`python vision_server.py --plc-config plc_config.json`. Press **Ctrl+C** in the
terminal to stop the service.

- **Overview** shows raw or annotated camera preview, inspection status, and
  start, stop, and reset controls. **Take photo** downloads the displayed JPEG
  preview.
- **Detections** lists up to 100 recent alarms and links to the available
  full-resolution raw image, annotated image, and mask.
- **Configuration** displays launch settings. Run `python vision_server.py --help`
  to see options such as `--camera-index`, `--sdk-dir`, and `--port`.

See [UI/README.md](UI/README.md) for operator behavior and frontend development.

## Command-line inspection

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

## CLI parameters

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

Set `host`, `port`, and `unit_id` in `plc_config.json` to match your PLC. The
[example configuration](plc/plc_config.example.json) uses port `502` and unit ID
`1`. Verify that these example memory assignments are available in your PLC.

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

To let **Reset alarm** in the dashboard or **R** in the CLI preview reset the
PLC latch, reserve M3 for Python. Add this reset rung in HaiwellHappy and adapt
M10 and M11 to your program.

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

## Test results

Software checks run on November 18, 2026.

| Check | Result |
|---|---|
| Python regression suite | 18 passed across SDK discovery, PLC communication, and the dashboard service |
| UI production build | TypeScript checks and Vite build passed |
| Local dashboard HTTP check | Page, JavaScript bundle, status, and six saved alarm records returned HTTP `200` |
| Offline detector run | Eight images processed and 16 output PNGs produced |

The offline run compared the checked-in inputs against `RefPic/Ref1.png`.

Example:
<img src="Results\alarm_20261030_164803_396378_detection.png" alt="Foreign Object Detected Demo" width="520">

These checks cover the software and saved inputs. Live camera acquisition and
physical PLC outputs require hardware verification.

Run the Python regression tests from the repository root.

```powershell
python -B -m unittest discover -s tests -v
```

## Project structure

| Part | Location | Contents |
|---|---|---|
| Launch commands | [`main.py`](main.py), [`vision_server.py`](vision_server.py) | CLI inspection and local dashboard service |
| Dashboard | [`UI/`](UI/) | React interface and Vite build |
| Camera | [`vision/camera/`](vision/camera/) | MindVision controller and native SDK bindings |
| Detection | [`vision/detection.py`](vision/detection.py) | Circular inspection area, image comparison, and region labeling |
| PLC | [`vision/plc_output.py`](vision/plc_output.py), [`plc/`](plc/) | Modbus client, configuration example, and Haiwell ladder project |
| Inspection images | [`RefPic/`](RefPic/), [`TestPic/`](TestPic/), [`Results/`](Results/) | Reference image, offline inputs and raw captures, annotated results and masks |
| Verification | [`tests/`](tests/) | Python regression suite |
| Documentation | [`docs/`](docs/README.md) | Architecture and component guides |
