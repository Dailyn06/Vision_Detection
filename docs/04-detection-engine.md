# Reference comparison and detection

Implementation: [detection engine](../vision/detection.py).

## Function analysis

| Function | Inputs and processing | Output |
| --- | --- | --- |
| `disk_mask()` | Image dimensions and optional center/radius globals; defaults to image center and radius 45% of the shorter dimension | Circular uint8 ROI mask and geometry |
| `normalize_reference()` | Sample current/reference grayscale pixels inside the ROI; estimate gain/offset using iterative outlier rejection | Exposure-compensated reference |
| `detection()` | Validate BGR uint8 images and mask; grayscale, blur, normalize, difference, threshold, mask, morphology, contours and minimum-area filtering | Annotated BGR frame, accepted binary mask, integer region count |

Current parameters are `BlurSize=15`, `thresholdValue=25` and `StandardMINArea=1000` pixels. Morphology kernels scale with image dimensions; minimum area remains an absolute pixel value. These are implementation defaults, not validated performance requirements.

## Functional evaluation

The algorithm is explainable and does not require model training. Input validation rejects mismatched geometry, invalid image layouts and invalid mask layout. Exposure normalization helps with global gain/offset changes when most of the ROI remains unchanged.

Accuracy depends on alignment and a representative clean reference. Shadows, glare, focus changes and reference contamination can produce unwanted regions; low-contrast or small objects may be removed by blur, morphology or minimum-area filtering. Normalization assumes enough unchanged pixels and is not geometric registration. Region count is not a calibrated count of physical objects: regions can merge or split.

No dedicated image-quality test suite or labelled performance report was found. Existing orchestration tests mock detector results, so they do not validate comparison accuracy. There is no confidence score or learned class output. Pixel-area thresholds are not physical dimensions without calibration.

## Design strategy

Create an immutable detector configuration with validated ranges, odd positive blur size and ROI bounds. Return structured region geometry/areas alongside the existing rendered outputs. Cache immutable reference preprocessing only after equivalence testing and profiling.

Store configuration and reference identifiers with every alarm. Introduce camera/reference compatibility checks beyond array shape. Change thresholds only against a controlled dataset; avoid tuning solely against the most recent alarm image.

## Functional evaluation criteria

Use known-clean images, labelled foreign-object cases, near-threshold objects, ROI-edge cases and controlled brightness/position variation. Split tuning and acceptance examples. Report event recall, false positives, failure by object category/size and processing-time distribution. Test all-zero/tiny masks, uniform references and invalid inputs. Establish physical size requirements and numerical quality targets with the product owner before claiming production detection performance.
