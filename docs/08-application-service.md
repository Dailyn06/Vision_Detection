# Application service and API

Implementation: [vision_server.py](../vision_server.py).

## Function analysis

| Function | Responsibility |
| --- | --- |
| `VisionHTTPServer.server_bind()` | Reserve one local TCP port exclusively on supported Windows systems |
| `InspectionService.publish()` | Encode raw/annotated previews, update frame counters, freshness, region count and camera dimensions; return a queued reset request |
| `status()` | Produce lifecycle/alarm/PLC state and calculate reset eligibility and five-second staleness |
| `image()` | Reject unavailable/stale inspection and return the cached JPEG |
| `make_handler()` | Route API requests and serve the built UI |
| `Handler.respond()` | Send content type, length, no-store and nosniff headers |
| Service `main()` | Validate launch options, bind localhost, serve requests and request orderly shutdown |

| Endpoint | Contract |
| --- | --- |
| `GET /api/status` | Current service snapshot; FPS is the reciprocal interval between publications, not a rolling average |
| `GET /api/preview?kind=raw|annotated` | Latest JPEG, maximum width 1280 pixels, quality parameter 80 |
| `GET /api/events` | Up to 100 recent discovered alarm records |
| `GET /api/evidence/:id/:kind` | Available raw, detection or mask PNG |
| `POST /api/start` | Accept a start request; success does not mean camera startup has completed |
| `POST /api/stop` | Request cooperative termination |
| `POST /api/reset` | Queue guarded reset, wait up to ten seconds and return completion or pending message |

## Functional evaluation

Local binding, command Host/Origin checks, a required control header, validated evidence paths and duplicate-port checks support the current local-use model. Automated tests exercise selected routes, rejected command access, stale image refusal and worker faults.

This is a standard-library threaded server, without login, durable command history or remote-deployment controls. Read endpoints do not use the command-origin checks. Static fallback serves the HTML shell for missing non-API files, which can obscure missing-asset errors. Client disconnections may raise write exceptions. Preview encoding occurs synchronously in the inspection worker, and frame metadata is fetched separately from JPEGs.

## Design strategy

Define versioned response schemas and stable error codes with startup-stage detail. Add frame IDs/time to preview responses so clients can correlate them with state. Give queued commands IDs and a completion-query contract. Expose lifecycle transitions without implying that start acceptance means monitoring is active.

Separate service state snapshots from camera/PLC internals. Consider a bounded preview encoder only after profiling; drop old preview work rather than queueing every frame. Unify UI and PLC freshness configuration where appropriate while preserving their different meanings. Add bounded diagnostic logs for faults and command outcomes.

## Functional evaluation criteria

Check simultaneous clients, repeated commands, lost connections, invalid paths/kinds, slow readers and slow PLC responses. Verify no stale image is labelled live, client count does not create additional camera workers and API failures remain intelligible. Keep network exposure out of scope until authentication, permissions and deployment design are specified.
