# Workspace: Vision as Primary Label (Fix “bird” root cause)

**Date:** 2026-02-26

## Why YOLO says “bird” for a wrench

- YOLOv8 (and our current pipeline) is trained on **COCO**: 80 classes (person, car, bird, keyboard, cell phone, scissors, …).
- COCO has **no** “wrench”, “tool”, “screwdriver”, or “crescent wrench”.
- The model can only choose among those 80. For a wrench at an angle it often picks **“bird”** (elongated shape, head/jaw).
- So the error is **not** bad hardware or a bug: it’s that the detector was never taught to recognize lab tools.

## Options (software vs hardware)

| Option | What | Pros | Cons |
|--------|------|------|------|
| **A. Vision as primary label** | Use YOLO only for “where”; use Vision API for “what”. Show only the vision-derived label. | No new hardware; uses existing API; correctly names tools. | Needs API key; one call per new object (then cache). |
| **B. Fine-tune YOLO on lab tools** | Add “wrench”, “screwdriver”, etc. via fine-tuning on your camera’s images. | Model natively outputs tool names; no per-object API. | Needs labeled data (50–200+ images) and training. |
| **C. Different pretrained model** | Use a model trained on Open Images or a dataset with “Wrench”. | Could get tool classes without training. | Finding a good, runnable model and integrating it. |
| **D. Hardware** | Better camera, top-down mount. | Clearer image can help. | Does **not** add “wrench” to the 80-class set; only helps a bit. |

**Recommendation:** Do **A** now (vision as primary label). Consider **B** later if you want no API dependency and have time to label and train.

## Design: Vision as primary label

- **YOLO:** Used only to get bounding boxes (and optionally contours). We do **not** show YOLO’s class as the final label for tools.
- **Labels we show:** For each detection we have a bbox. We get a label by:
  1. **Cache:** Key = stable id for this “object” (e.g. hash of bbox position/size or of cropped image). If we have a cached label, use it.
  2. **Vision API:** If no cache, call the vision API on the crop; use the returned phrase as the label; cache it.
- So the **only** label the user sees is either “…” / “object” (while loading) or the **vision API response** (e.g. “crescent wrench”). We never display “bird” because we never treat YOLO’s class as the user-facing label for these objects.
- **Fallback:** If no API key or API fails, we can show “object” or a generic “tool” for unknown/suspicious classes instead of “bird”.
- **Existing hacks:** Remove the “replace bird with tool” string hack; the UI simply doesn’t use YOLO’s class as the displayed label when we have (or will have) a vision result.

## Implementation sketch

- Add a **label cache** keyed by something stable (e.g. `(round(cx/20), round(cy/20), area_bucket)` or crop perceptual hash). Value = vision API response.
- In the stream: for each detection, if we have a cached label for this detection’s key, set `d["class"] = cached_label`. Else, queue this detection for one vision call (rate-limited), and when the response arrives, store in cache and set `d["class"]` for the next frame.
- Optionally show “…” for detections that don’t yet have a vision label.
- Remove `WORKSPACE_DEFAULT_REFINEMENTS` and `_workspace_sanitize_bird_label` that only replace the string “bird” with “tool”.
