# Operator dashboard and interaction design

Implementation: [App.tsx](../UI/src/App.tsx), [index.css](../UI/src/index.css), [Vite configuration](../UI/vite.config.ts).

## Function analysis

| Function/area | Responsibility |
| --- | --- |
| `Icon()` | Render local SVG symbols with decorative icons hidden from assistive technology |
| Status/history effect | Fetch service status and events sequentially, then wait one second; each request has a four-second timeout |
| Preview effect | Fetch the selected preview, update/revoke browser object URLs, then wait 200 ms; stop on unavailable inspection |
| `command()` | Submit start/stop/reset and display acknowledged service results or errors |
| `capture()` | Download the current preview JPEG and explain its size limit |
| Overview | Present inspection metrics, real preview, controls and PLC state |
| Detections | Present saved alarms and available evidence links |
| Configuration | Display selected launch options; runtime editing is not implemented |
| Global styles | Apply the dark PPTC dashboard theme, responsive layout, focus states and reduced-motion overrides |

The resolution label uses an explicit Unicode escape for the multiplication sign. Camera dimensions represent source resolution; the displayed/downloaded preview may be smaller. Frame counters are service-session counters, not inspected-unit totals.

## Functional evaluation

The UI reflects backend state instead of fabricating hardware operation. Labels explain reset requirements and the difference between PLC communication and physical output. Navigation has explicit accessible names; status messages use a live region.

Status and history share one error path: a history failure can mark the whole service disconnected despite a successful status response. Commands and manual capture lack the polling requests' explicit timeout. A sticky message or prior error can take precedence over the alarm explanation in the shared status banner. Several unavailable-value strings remain literal question marks. The component combines network logic and all views, and CSS retains older theme rules beneath overrides. No browser automation tests were found.

## Design strategy

Keep the existing visual identity while making alarm, inspection fault, PLC outage and service disconnection separate persistent indicators. Show unknown values as “Unavailable” or a deliberate placeholder. Distinguish pending start/stop/reset from completed actions. Make preview resolution versus source resolution clear next to capture controls.

Extract service hooks and small components for the camera panel, operator controls, status summary and evidence history. Track status/history errors separately and apply explicit command timeout/pending behavior. Consolidate styles incrementally after screenshots establish the intended appearance. Preserve encoded special characters to avoid repeating the resolution-label corruption.

## Functional evaluation criteria

Test running, stale, connecting, stopping, fault, disconnected and alarm-latched views. Verify reset refusal, long-running commands, history failure, capture failure and reconnect behavior. Check keyboard operation, focus, narrow screens, readable contrast and announcements with real browser tooling. Acceptance requires that an operator cannot confuse a stale/unknown result with a clear inspection.
