# Alarm evidence and history

Implementation: alarm saving in [main.py](../main.py); `events()` and `evidence_path()` in [vision_server.py](../vision_server.py).

## Function analysis

| Operation | Current behavior |
| --- | --- |
| Event identity | Local timestamp ID: `alarm_YYYYMMDD_HHMMSS_microseconds` |
| Raw capture | Full-resolution PNG in `TestPic/` |
| Annotated detection | Full-resolution PNG in `Results/` |
| Accepted mask | PNG in `Results/` |
| Write failure | A failed `cv2.imwrite()` raises an error and stops inspection |
| History discovery | Find annotated alarm PNGs, sort by name and return the latest 100; expose only evidence files that exist |
| Evidence lookup | Validate timestamp-shaped ID and allowed kind before constructing a path |
| Offline results | Separate filename convention; repeated runs can overwrite matching output files |

PNG files preserve the detector's image evidence. The UI's Take photo action is different: it downloads a maximum-1280-pixel JPEG preview and does not create a full-resolution alarm record.

## Functional evaluation

Evidence supports diagnosis by showing source pixels, rendered annotations and accepted regions. Tests cover path traversal refusal and alarm delivery before evidence I/O. The history can discover files created before the server started.

Three writes are sequential, not transactional. A failure can leave a partial set; discovery relies on the annotated file, so history does not certify complete evidence. Metadata does not record reference version, detector settings, region count or timezone offset. There is no retention policy, disk-space monitoring, checksum or indexed pagination. Processing every history request scans/sorts matching files even though only 100 are returned.

## Design strategy

Introduce an evidence repository with a manifest written only after the required files are successfully committed. Store UTC timestamps plus local display context, reference/configuration identifiers, dimensions, region summaries and completion status. Write temporary files followed by atomic replacement where supported; define cleanup/recovery for interrupted sets.

Add disk-space checks, storage-failure diagnostics and an explicit retention/archive policy. Retain filenames for backward compatibility and import legacy events as records with unknown provenance. Move to an indexed store only when history volume and query needs justify it.

## Functional evaluation criteria

Inject failures on each file write, interrupt a save and simulate low disk space. Verify that complete, partial and missing evidence are distinguishable; unauthorized paths are refused; legacy records remain accessible; retention does not remove active writes. Measure save latency and storage growth using representative full-resolution images.
