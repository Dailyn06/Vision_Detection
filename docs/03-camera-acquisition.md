# Camera acquisition and SDK integration

Implementation: [camera controller](../vision/camera/controller.py), [MindVision SDK bindings](../vision/camera/mvsdk.py).

## Function analysis

| Function | Responsibility |
| --- | --- |
| `find_sdk_directory()` | Prefer an explicit SDK directory; otherwise search standard MindVision Program Files locations for the DLL matching Python bitness |
| `MindVisionCamera.__init__()` | Store camera index, orientation, exposure compatibility option, target rate and lighting frequency |
| `__enter__()` | Validate options, load the SDK, enumerate/open the device, configure image format, exposure, anti-flicker and acquisition, then allocate a native buffer |
| `_check()` | Convert unsuccessful SDK return codes into camera exceptions |
| `read()` | Acquire and process a frame, release the acquisition buffer, optionally flip it, validate layout and return a copied BGR NumPy array |
| `close()` / `__exit__()` | Release the camera handle, aligned memory and DLL-directory registration |
| `mvsdk._Init()` and wrapper functions | Load the vendor library and expose native camera calls and structures |

Automatic exposure is enabled; `exposure_us` is retained as a legacy option rather than applied manually. Unsupported native frame-rate control falls back to software triggering. Monochrome images are converted to BGR so detection has a consistent input contract.

## Functional evaluation

Implemented strengths include explicit resource cleanup, SDK discovery and image-layout validation. Tests cover standard install discovery and the actionable missing-DLL error, not all device acquisition behavior.

Camera selection is by index, which may change when devices are reconnected. A native read has a requested timeout, but overall startup/stop duration is not bounded by an application watchdog. Another process can hold the camera; same-port server exclusivity does not provide a machine-wide device lock. The detector requires geometry/orientation to match the reference.

## Design strategy

Preserve the vendor wrapper as a dependency boundary and keep application policy in the adapter/controller. Add serial-number selection, startup-stage reporting and normalized error categories such as SDK missing, device missing, device busy and frame timeout. Record effective resolution, pixel format and exposure mode with reference metadata.

Evaluate fixed exposure against automatic exposure using the real lighting conditions before changing the default. If native calls can hang beyond accepted stop latency, consider an isolated acquisition process with an explicit recovery policy.

## Functional evaluation criteria

Validate missing/wrong-bit SDK handling, occupied-device behavior, unplug/replug, monochrome/color conversion, orientation, repeated open/close and timeout cleanup. Acceptance requires no leaked camera handle, useful UI errors, correct frame geometry and startup/stop times within agreed limits. Use mocked SDK tests for cleanup branches and real hardware for transport/driver behavior.
