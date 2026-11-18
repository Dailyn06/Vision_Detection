# PLC communication and output requests

Implementation: [PLC output](../vision/plc_output.py), [example configuration](../plc/plc_config.example.json), and [Haiwell project](../plc/DetectionAlarm.gpc). Actual addresses and network settings belong to the site-specific `plc_config.json`.

## Function analysis

| Function/class | Responsibility |
| --- | --- |
| `PLCConfig.__post_init__()` / `load()` | Parse JSON and validate network ranges, distinct coil addresses and positive timing values |
| `ModbusCoilClient._receive()` | Receive an exact byte count despite fragmented TCP reads |
| `write_coil()` | Send Modbus TCP FC05; validate transaction, protocol, unit, length, exception and echoed payload; close failed connections |
| `PLCAlarmOutput.inspection_completed()` | Latch requested alarm state and timestamp successful inspection |
| `request_reset()` | Require a configured reset coil, connected worker and fresh inspection; queue reset |
| `_run()` | Write alarm/health/heartbeat, reconnect after communication failure, sequence reset pulses and clear health during shutdown where possible |
| `__enter__()` / `__exit__()` | Start and request termination of the communication worker |

The example maps alarm, heartbeat, healthy and reset requests to offsets 3072–3075. These offsets require verification against the installed PLC program. Heartbeat toggles between cycles. Healthy depends on the latest successful inspection being newer than `inspection_timeout`.

Reset clears the requested alarm and publishes healthy before raising the reset coil. The pulse is approximately one second, subject to scheduling/network delay; new alarms, stale inspection or communication faults cancel reset activity. Failed pending resets are not replayed on reconnection.

## Functional evaluation

Simulator tests cover fragmented/invalid responses, latch behavior, reconnect, stale health, reset sequencing and pulse expiration. An independent worker reduces the effect of image-processing delays on communication scheduling.

The client writes coils only; it does not read physical output, ladder latch or watchdog state. `connected` reflects successful protocol activity, not complete machine readiness. Socket timeouts and multiple writes make the update cycle longer than `heartbeat_interval` alone. Network writes can occur while the worker holds its lock, delaying status/reset readers. PLC ladder behavior remains an external dependency.

## Design strategy

Publish connection diagnostics and last successful exchange through a snapshot method rather than exposing worker internals to the service. If output feedback is required, define and implement a separate PLC readback contract. Keep requested alarm, acknowledged write and verified physical output as distinct states.

Document a site-approved coil map and watchdog sequence. Treat the example JSON as a template, not a confirmed installation. Validate timing values against measured worst-case update cycles and the actual ladder program.

## Functional evaluation criteria

On equipment, verify alarm latch, watchdog response, stale inspection, network loss/recovery, reset interlocks, new alarm during reset and restart behavior. Record coil requests and actual buzzer/light response separately. Success requires the agreed ladder behavior under those conditions; software simulator results do not establish physical-output acceptance.
