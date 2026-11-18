# Functional evaluation and deployment readiness

Implementation: [tests](../tests/), [UI package scripts](../UI/package.json), [toolchain pins](../UI/.mise.toml), [operating guide](../README.md).

## Function analysis

The quality function establishes which behavior is supported by source review, automated tests, image evaluation and equipment acceptance. Deployment turns a known build and configuration into a repeatable local installation.

| Existing test file | Coverage visible in source | Main gap |
| --- | --- | --- |
| `test_camera_sdk.py` | Standard SDK discovery and actionable missing-DLL error | Real driver/device acquisition and cleanup failures |
| `test_plc_output.py` | Modbus encoding/response handling, alarm latch/reconnect, stale health, reset pulse and orchestration | Installed PLC ladder and physical outputs |
| `test_vision_server.py` | Port exclusivity, stale/reset refusal, worker faults, alarm/reset transitions, selected HTTP access checks and evidence path validation | Browser workflows, slow-client behavior and full restart/stop stress |

Source inventory contains 18 test methods across these files. Existence of a test is not a claim that it has passed in the current environment. This documentation review does not execute the suite or operate equipment. Earlier session results are historical, not a new acceptance run.

## Functional evaluation

The project has useful protocol and lifecycle regressions. It lacks a dedicated detector-quality suite, a documented held-out image benchmark, frontend workflow tests and a sustained hardware acceptance report. Python dependencies are described in setup instructions but are not pinned in a dependency manifest. The UI has a pnpm lockfile and Node/pnpm toolchain declarations; `build` includes TypeScript checking.

Operational issues already observed during development include missing DLL lookup, duplicate/stuck camera owners and corrupted UI special characters. These should become regression scenarios. Current machine or PLC connectivity cannot be inferred from those historical observations.

## Evaluation plan

| Level | Method | Required record |
| --- | --- | --- |
| Software regression | Run the existing suite plus new fault/state tests | Command, environment, commit/build identity and pass/fail output |
| Detector quality | Label clean/foreign-object cases with size, contrast and lighting variation | Dataset version, tuning/held-out split and recall/false-positive results |
| Timing/performance | Profile capture, detection, evidence save, preview encoding and API response | Median/tail latency, actual FPS, CPU/memory and reference resolution |
| Browser acceptance | Exercise operator journeys and accessibility | Browser/version, screenshots and observed outcomes |
| Hardware integration | Test camera contention/unplug, PLC disconnect/reset/watchdog and actual output | Equipment/configuration identity, expected/actual state and witness |
| Sustained operation | Run for the agreed operating period with realistic event volume | Memory/storage trend, faults, reconnects and alarm latency |

Performance, quality and duration thresholds remain product decisions. Agree them before conducting acceptance rather than selecting them after results are known.

## Deployment strategy

1. Record Python architecture, SDK/driver version and camera identity. Pin tested Python packages in a future dependency manifest.
2. Verify the reference and detector configuration match the installed camera geometry and lighting.
3. Review site-specific PLC mapping and watchdog behavior against the actual ladder program.
4. Build the locked UI dependencies; run `python -m unittest discover -s tests -v` and the UI typecheck/build commands.
5. Launch one local `vision_server.py` process. Confirm no CLI/vendor application holds the camera, then perform startup and alarm/reset checks.
6. Archive build/configuration/reference identifiers and an acceptance record. Define rollback to a known application/configuration set; rollback must not imply resetting the PLC latch.

## Proposed release gates

Release only after agreed detector-quality and timing targets pass, evidence survives fault tests, startup/recovery is diagnosable and equipment acceptance confirms the intended PLC/output behavior. Prioritize these gates ahead of multi-camera support, remote access and production analytics.
