# Inspection lifecycle and alarm control

Implementation: [main.py](../main.py), `InspectionService` in [vision_server.py](../vision_server.py).

## Function analysis

| Function | Responsibility |
| --- | --- |
| `read_pictures()` | Iterate supported images without loading the entire folder into memory; skip unreadable files |
| `main()` | Offline comparison, optional reference resizing, result saving and optional OpenCV preview; no PLC communication |
| `run_camera()` | Own the live camera loop, validate reference geometry, count positive/clear frames, latch alarms, queue PLC signals, save evidence and handle reset |
| `InspectionService.start()` / `_run()` | Start one worker per service and translate termination/errors into service state |
| `stop()` | Set the cooperative stop event and mark stopping |
| `reset()` / `complete_reset()` | Queue a guarded reset and report its software result; the loop rechecks clear frames before acting |

## State and alarm semantics

The service starts stopped. Start enters connecting; publishing a processed frame enters running. A stop request enters stopping and normal loop exit returns to stopped. An exception enters fault. Stale is a separate freshness flag, not an independent lifecycle state.

`positive_frames` increments on any nonzero region count and otherwise resets. A new latch requires `confirm_frames` consecutive positive frames, default three. Evidence is saved once for that newly confirmed latch. Clear frames do not automatically clear the latch. Reset requires enough consecutive clear frames and, when enabled, PLC readiness. The loop rechecks those conditions when processing the queued request.

The software latch survives stop/start within one service instance. A new Python process starts with a clear software latch. PLC ladder must retain and reset its own state independently.

## Functional evaluation

Confirmation, guarded reset, retriggering and single-worker behavior have automated coverage. Alarm delivery is queued before disk evidence writing. A storage error stops inspection rather than returning a clear result.

The loop mixes image processing, alarm policy, evidence I/O and UI publication. Alarm state exists in the controller and bridge, with direct cross-module field updates. Stop cannot immediately interrupt an in-progress SDK call or processing operation. Frame-based confirmation creates variable wall-clock latency as processing speed changes. Offline reference resizing may produce results that do not represent exact live geometry.

## Design strategy and functional evaluation criteria

Extract one controller as the alarm-state authority, with explicit transition methods and immutable snapshots. Keep transport and rendering outside it. Track command IDs and completion state so a reset that exceeds the HTTP wait can be queried later; the current ten-second reset wait returns a pending message rather than cancellation.

Validate stop during startup/read/processing/save, start after fault, stop/start with a latch, process restart and PLC reset refusal. Assert a single evidence set per latch, no duplicate camera worker and no reset after a new object invalidates clear eligibility. Measure actual alarm/stop latency rather than deriving it from the requested camera FPS.
