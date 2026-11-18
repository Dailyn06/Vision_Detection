# PPTC product analysis and design

Analysis date: 2026-11-16. These documents describe the current source and proposed development strategy. They do not change runtime behavior or certify inspection accuracy or PLC operation.

## Document map

| Function | Document | Main implementation |
| --- | --- | --- |
| Product scope and user value | [Product analysis](01-product-analysis.md) | Whole application |
| Architecture and development sequence | [Design strategy](02-design-strategy.md) | Whole application |
| Camera acquisition and native SDK | [Camera acquisition](03-camera-acquisition.md) | `camera_controller.py`, `mvsdk.py` |
| Image comparison and object regions | [Detection engine](04-detection-engine.md) | `Detection.py` |
| Inspection lifecycle and alarm decisions | [Inspection control](05-inspection-control.md) | `main.py`, `InspectionService` |
| PLC communication and reset requests | [PLC integration](06-plc-integration.md) | `plc_output.py`, PLC JSON configuration |
| Alarm records and image evidence | [Evidence management](07-evidence-management.md) | `main.py`, evidence helpers in `vision_server.py` |
| HTTP API, state and preview delivery | [Application service](08-application-service.md) | `vision_server.py` |
| Operator interaction and visual design | [Operator dashboard](09-operator-dashboard.md) | `UI/src/App.tsx`, `UI/src/index.css` |
| Verification and installation readiness | [Quality and deployment](10-quality-and-deployment.md) | `tests/`, build configuration, launch documentation |

Each document contains function analysis, functional evaluation and a design strategy. Paths in the implementation columns are relative to the repository root. Function tables identify responsibilities and limitations rather than reproducing every line of code.

## How to interpret evaluations

- **Implemented:** visible in the inspected source. This does not imply validation under production conditions.
- **Test-covered:** a relevant automated test exists. Current execution results are recorded in the quality document only when rerun for this review.
- **Needs validation:** requires representative images, timing measurements, browser checks or real equipment.
- **Proposed:** future work, not an available feature.

Use the product document to agree on requirements, the design strategy to sequence work, and the functional documents to implement and review each subsystem. Operating instructions remain in the root README and `UI/README.md`.
