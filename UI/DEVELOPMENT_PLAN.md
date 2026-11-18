# UI assessment and next development

Integration update: the dashboard now uses `vision_server.py` and the existing camera loop for live status/preview, operator start/stop/reset and saved alarm evidence. TypeScript and production builds pass; the Python regression suite has 15 passing tests. See [README.md](README.md) for launch instructions. The assessment below records the original prototype; hardware acceptance remains outstanding.

Reviewed: 2026-11-13. Scope: source inspection of `UI/` and the Python integration points. No application behavior changed.

## Current state

`UI/` is a Figma Make export using React 19, TypeScript, Vite 8 and Tailwind CSS 4. It is a standalone dashboard prototype, not yet an operator interface for the Python inspection process.

| Area | Observed behavior |
| --- | --- |
| Application | `src/App.tsx` contains icons, layout, sample records, local control state and synthetic screenshot rendering in one component file. |
| Camera | CSS draws bottles and a conveyor. Camera selection changes a label; it does not select hardware. |
| Capture | Downloads a separately drawn 1280×720 canvas image despite displaying 1920×1080 in the feed. It does not capture camera pixels. |
| Controls | Pause, overlay and automatic rejection change browser state only. Navigation changes selection without rendering another page. Search, alerts, settings and detection-history actions have no implemented behavior. |
| Data | Metrics, detections, confidence, system health, equipment and operator details are hardcoded. The confidence threshold is a decorative track. |
| Styling | `src/index.css` contains the original theme plus a large `.design-v2` override layer and responsive rules. Fonts come from Google Fonts. |
| Build | A lockfile and toolchain pins exist. `build` runs Vite without a separate TypeScript check. No test, lint or typecheck script is defined. |
| Hosting | `vite.config.ts` includes Figma metadata and development plugins. Default server binding is `0.0.0.0:8443`. |

## Integration findings

The actual application detects foreign objects against `RefPic/Ref1.png` inside a circular ROI. `Detection.detection()` returns an annotated image, mask and object count; it does not return model confidence, packaging classifications or inspected-unit counts.

`main.py:run_camera()` owns the camera loop, consecutive-frame confirmation, alarm latch, evidence saving and keyboard reset. `vision/camera/controller.py:MindVisionCamera` owns the native SDK camera. `vision/plc_output.py:PLCAlarmOutput` maintains PLC communications in a background worker. No HTTP or streaming API was found in these integration files.

The next UI must describe this workflow accurately: inspection frames are not production units, a confirmed alarm is not an automatic reject-lane action, and a PLC request does not prove that a physical buzzer/output activated.

## Prioritized work

### 1. Establish a reproducible local baseline

- Provision Node 22 and pnpm 10.34.3 as pinned in `.mise.toml`; verify the installed Node version satisfies locked dependencies.
- Run `pnpm install --frozen-lockfile`, `pnpm exec tsc --noEmit` and `pnpm build` from `UI/`.
- Add a typecheck script; resolve compiler findings before feature development. `replaceAll()` is used while TypeScript targets ES2020 libraries, so check that usage in particular.
- Verify local development availability. `AGENTS.md` describes an already-running Figma server; that statement has not been verified on this Windows checkout.
- Keep Figma-specific tooling until a local build establishes which parts are needed.

Acceptance: clean dependency installation, successful typecheck and production build, and a locally rendered dashboard.

### 2. Make prototype behavior explicit and modular

- Extract layout, camera viewport, inspection controls, status metrics and event history into components without redesigning the dashboard.
- Move sample data behind a clearly labelled demo adapter and define typed service interfaces.
- Replace packaging/model-confidence placeholders with foreign-object count, processed frames, actual inspection FPS, confirmed alarms and explicit connection states. Only show values the service supplies.
- Implement Overview, Detections and Configuration views first; hide unfinished navigation/actions or clearly mark them unavailable.
- Consolidate theme rules incrementally, keeping the existing dark appearance.

Acceptance: demo mode is visibly identified, controls have truthful effects, and components do not assume hardware is online.

### 3. Add a read-only bridge to the inspection service

Proposed design, not an existing API: one Python process owns the camera and inspection engine; a local HTTP service exposes snapshots, bounded preview frames and recent alarm evidence. Do not open a second camera session for the browser. Keep browser delivery out of the inspection-critical loop and drop old preview frames when clients are slow.

| Proposed resource | Purpose |
| --- | --- |
| `GET /api/status` | Inspection state, last successful frame time, alarm latch, reset eligibility, camera availability and separately reported PLC communications state. |
| `GET /api/preview` | Latest bounded-resolution JPEG preview or equivalent stream, with frame ID/time and raw/annotated selection. |
| `GET /api/events` | Paginated confirmed-alarm records and associated evidence identifiers. |
| `GET /api/evidence/:id/:kind` | Validated evidence lookup for raw image, annotation or mask. |

Use explicit `offline`, `connecting`, `running`, `stopped`, `fault` and stale-data presentation. A missing or stale frame must never appear as a clear inspection. Specify timestamps, event IDs, error format and reconnect behavior before wiring components. Serve evidence through validated IDs, not arbitrary filesystem paths. Keep the initial service local; define access controls before exposing control endpoints to a network.

Acceptance: real preview and status reach the UI; disconnects and camera/storage faults produce visible unavailable/fault states; alarm evidence remains accessible after refresh.

### 4. Add acknowledged operator commands

- Route start/stop/reset through the engine owner, with pending, success and refusal responses.
- Preserve the current reset rule: enough consecutive clear frames and the existing PLC reset checks. Refresh state after acknowledgement; do not clear a latch optimistically in React.
- Keep preview pause distinct from stopping inspection and PLC health updates.
- Download the actual captured frame with its real dimensions and timestamp. Distinguish download initiation from confirmed storage on disk.
- Add validated detector/camera configuration only after supported runtime changes are defined. Do not expose a confidence percentage for an algorithm that has no confidence output.

Acceptance: repeated commands do not create duplicate camera workers; reset refusal is visible; hardware state remains authoritative.

### 5. Verify operator workflows

- Add meaningful service tests for alarm confirmation, reset eligibility/refusal, fault reporting and evidence lookup.
- Add UI integration tests for stale/disconnected status, rejected commands and event/evidence loading.
- Check keyboard navigation, focus visibility, narrow-screen navigation labels, semantic event tables, status announcements and reduced-motion behavior. Icon-only mobile navigation currently loses its visible text without explicit button labels.
- Inspect responsive layouts in a browser and verify real frame captures against the displayed frame.

## Validation limits and workspace notes

Node.js, pnpm and mise were not available on PATH during this inspection; `UI/node_modules` is absent. Build, TypeScript and browser behavior remain unverified. No dependencies were installed or hardware commands executed.

The repository already contains unrelated modified/deleted files and untracked Python/PLC work. `UI/` was also untracked at inspection time. Preserve that work and review the UI changes separately before committing.

Recommended next implementation: complete milestone 1, then extract a typed demo adapter and replace misleading placeholder labels before adding the read-only Python bridge.
