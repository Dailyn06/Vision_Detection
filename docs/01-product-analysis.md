# Product analysis

## Purpose and product boundary

PPTC is a local industrial vision application for detecting visible foreign-object regions inside a circular inspection area. It compares MindVision camera frames with a fixed clean reference, confirms repeated detections, stores alarm evidence and sends optional alarm/health requests to a Haiwell PLC. A browser dashboard provides operator control and visibility.

The product's value is a shorter path from an abnormal image to an actionable alarm and reviewable evidence. Its suitability depends on stable camera geometry, lighting, reference quality and validated detector settings.

## Function analysis

| User | Job | Required product behavior |
| --- | --- | --- |
| Operator | Start monitoring and identify faults | Clear inspection state, real preview and useful startup errors |
| Operator | Investigate an alarm and rearm | Raw/annotated/mask evidence, clear-frame eligibility and acknowledged reset request |
| Controls technician | Integrate the PLC | Explicit coil mapping, heartbeat/health semantics and separate physical-output verification |
| Vision technician | Tune detection | Controlled reference acquisition, ROI definition and repeatable evaluation images |
| Maintenance/developer | Restore service | Single camera owner, reproducible setup, diagnostics and regression tests |

The normal journey is: prepare a clean reference and equipment; start one service; open the dashboard; start inspection; review any confirmed alarm; remove the cause; reset after enough clear frames; verify the PLC/output state separately.

Current scope includes single-camera inspection, offline folder comparison, one alarm latch, local web control and recent saved alarm evidence. Multi-camera orchestration, defect classification, calibrated confidence scores, unit counting, automatic reject-lane control, user accounts and remote hosting are not implemented.

## Functional evaluation

| Capability | Assessment | Evidence or limitation |
| --- | --- | --- |
| Real-time operator visibility | Implemented; needs timing validation | Real camera preview and service status; no guaranteed frame rate |
| Repeat-detection alarm confirmation | Implemented and test-covered | Consecutive positive frames reduce isolated triggers; they do not establish measured detection accuracy |
| Evidence review | Implemented with limitations | Three PNG kinds; no transactional event manifest or retention policy |
| PLC alarm requests | Implemented and test-covered using a simulator | Acknowledged writes do not prove the buzzer/light changed |
| Recovery | Partially implemented | Reconnect and guarded reset exist; startup diagnostics and bounded stop behavior need improvement |
| Production effectiveness | Needs validation | No labelled acceptance dataset, measured false-alarm rate or sustained performance report |

Inspection frames must not be presented as production units. A missing frame is unavailable inspection, not a clear result. Detector annotations can say ALARM on an individual positive frame before the consecutive-frame latch has confirmed a system alarm.

## Product design strategy

Prioritize trustworthy status and repeatable detection before adding analytics or additional screens. Define the smallest relevant object, acceptable lighting/position variation, operating hours, required alarm latency and allowed false-alarm rate with the owner of the process. These are open requirements, not values inferred from the current constants.

Measure success using labelled-event recall, false alarms per operating hour, end-to-end alarm latency, inspection availability, startup success rate and time needed to diagnose a fault. Set numerical acceptance thresholds before production acceptance. Count alarms and frames separately; avoid displaying a pass-rate percentage without a defined inspected-unit trigger.

The release decision should require an accepted detection dataset, a sustained equipment run, evidence integrity checks and witnessed PLC ladder/output tests. A passing software test suite alone is insufficient for that decision.
