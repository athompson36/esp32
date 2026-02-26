"""
Workspace vision: object detection (YOLOv8) and overlay drawing.
Used by the Workspace tab for AI overlay and object detection.
Filters out the workstation mat (large surface) so only objects on top are reported.
Supports segmentation (yolov8n-seg) for irregular shapes; falls back to box-only.
"""
from __future__ import annotations

import threading
from typing import Any

import cv2
import numpy as np

# Lazy-loaded model; cache on first use. _yolo_has_seg True when seg model loaded.
_yolo_model: Any = None
_yolo_has_seg = False
_yolo_lock = threading.Lock()

# Robustness: ignore detections that are likely the workstation mat or background
MIN_CONFIDENCE = 0.15  # Lower so stationary tools (e.g. wrench) still show when confidence is marginal
MAX_BBOX_AREA_FRACTION = 0.35  # Detections covering >35% of frame are treated as mat/desk surface
IGNORE_CLASSES = frozenset({
    "dining table", "bed", "couch", "potted plant",
    "tv", "monitor", "laptop",  # often part of the scene, not "on the mat"
})

# Blue workmat detection (HSV): assume mat is a rectangle in the world, find its quad for perspective correction
WORKMAT_HSV_LOWER = np.array([85, 40, 40])   # blue range (slightly wider for lighting)
WORKMAT_HSV_UPPER = np.array([135, 255, 255])
WORKMAT_MIN_AREA_FRACTION = 0.05  # mat must be at least 5% of frame
WORKMAT_RECT_SIZE = (640, 480)   # size of rectified mat image


def get_workmat_quad(frame_bgr) -> np.ndarray | None:
    """
    Detect the blue workmat as a quadrilateral. Returns 4x2 array of corner points (order: TL, TR, BR, BL)
    or None if not found. Assumes mat is the dominant blue region that looks like a quad.
    """
    if frame_bgr is None or not hasattr(frame_bgr, "shape"):
        return None
    h, w = frame_bgr.shape[:2]
    area_total = h * w
    hsv = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2HSV)
    mask = cv2.inRange(hsv, WORKMAT_HSV_LOWER, WORKMAT_HSV_UPPER)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, np.ones((15, 15), np.uint8))
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, np.ones((5, 5), np.uint8))
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    best_quad = None
    best_area = 0
    for cnt in contours:
        area = cv2.contourArea(cnt)
        if area < area_total * WORKMAT_MIN_AREA_FRACTION:
            continue
        peri = cv2.arcLength(cnt, True)
        approx = cv2.approxPolyDP(cnt, 0.02 * peri, True)
        if len(approx) != 4:
            continue
        pts = np.array(approx, dtype=np.float32).reshape(4, 2)
        if not _is_convex_quad(pts):
            continue
        if area > best_area:
            best_area = area
            best_quad = _order_quad_corners(pts)
    return best_quad


def _is_convex_quad(pts: np.ndarray) -> bool:
    if pts is None or len(pts) != 4:
        return False
    try:
        return cv2.isContourConvex(pts.astype(np.int32))
    except Exception:
        return False


def _order_quad_corners(pts: np.ndarray) -> np.ndarray:
    """Order 4 corners as TL, TR, BR, BL (top-left, top-right, bottom-right, bottom-left)."""
    pts = np.array(pts, dtype=np.float32).reshape(4, 2)
    center = pts.mean(axis=0)
    def angle_key(p):
        return np.arctan2(p[1] - center[1], p[0] - center[0])
    ordered = sorted(pts.tolist(), key=lambda p: angle_key(np.array(p)))
    return np.array(ordered, dtype=np.float32)


def rectify_frame(frame_bgr, quad: np.ndarray) -> tuple[np.ndarray, np.ndarray] | None:
    """
    Warp frame so the workmat quad becomes a rectangle (top-down view).
    Returns (warped_frame, H_inv) so detections in warped space can be mapped back to original.
    H_inv is 3x3; use cv2.perspectiveTransform(pts, H_inv) to map warped -> original.
    """
    if frame_bgr is None or quad is None or len(quad) != 4:
        return None
    try:
        dst = np.array([
            [0, 0],
            [WORKMAT_RECT_SIZE[0], 0],
            [WORKMAT_RECT_SIZE[0], WORKMAT_RECT_SIZE[1]],
            [0, WORKMAT_RECT_SIZE[1]],
        ], dtype=np.float32)
        H, _ = cv2.findHomography(quad, dst)
        if H is None:
            return None
        warped = cv2.warpPerspective(frame_bgr, H, WORKMAT_RECT_SIZE)
        H_inv, _ = cv2.findHomography(dst, quad)
        return warped, H_inv
    except Exception:
        return None


def map_detections_to_original(
    detections: list[dict[str, Any]],
    H_inv: np.ndarray,
    orig_h: int,
    orig_w: int,
) -> list[dict[str, Any]]:
    """Transform detection bboxes and contours from rectified (warped) space to original image coordinates."""
    if H_inv is None or not detections:
        return detections
    out = []
    for d in list(detections):
        d = dict(d)
        bbox = d.get("bbox")
        if bbox and len(bbox) == 4:
            x1, y1, x2, y2 = bbox
            pts_src = np.array([[x1, y1], [x2, y1], [x2, y2], [x1, y2]], dtype=np.float32).reshape(-1, 1, 2)
            pts_orig = cv2.perspectiveTransform(pts_src, H_inv)
            xs = pts_orig[:, 0, 0]
            ys = pts_orig[:, 0, 1]
            d["bbox"] = [int(max(0, xs.min())), int(max(0, ys.min())), int(min(orig_w, xs.max())), int(min(orig_h, ys.max()))]
        contour = d.get("contour")
        if contour and len(contour) >= 3:
            pts_src = np.array(contour, dtype=np.float32).reshape(-1, 1, 2)
            pts_orig = cv2.perspectiveTransform(pts_src, H_inv)
            d["contour"] = np.clip(pts_orig.reshape(-1, 2), 0, [orig_w - 1, orig_h - 1]).astype(np.int32).tolist()
        out.append(d)
    return out


def _filter_detections(
    detections: list[dict[str, Any]],
    frame_height: int,
    frame_width: int,
) -> list[dict[str, Any]]:
    """Keep only detections that are likely objects ON the mat (not the mat itself)."""
    if not detections or frame_height <= 0 or frame_width <= 0:
        return detections
    area_total = frame_height * frame_width
    out = []
    for d in detections:
        if d.get("confidence", 0) < MIN_CONFIDENCE:
            continue
        class_name = (d.get("class") or "").strip().lower()
        if class_name in IGNORE_CLASSES:
            continue
        bbox = d.get("bbox")
        if not bbox or len(bbox) != 4:
            continue
        x1, y1, x2, y2 = bbox
        contour = d.get("contour")
        if contour and len(contour) >= 3:
            area = float(cv2.contourArea(np.array(contour, dtype=np.int32)))
        else:
            w = max(0, x2 - x1)
            h = max(0, y2 - y1)
            area = w * h
        if area_total > 0 and (area / area_total) > MAX_BBOX_AREA_FRACTION:
            continue  # too large = likely mat/desk surface
        out.append(d)
    return out


def run_detection(frame_bgr) -> list[dict[str, Any]]:
    """
    Run YOLOv8 on a BGR frame (numpy array). Returns list of detections:
    [{ "class": str, "confidence": float, "bbox": [x1, y1, x2, y2] }, ...].
    Uses yolov8n (nano) on CPU. Lazy-loads model; returns [] if ultralytics/opencv missing.
    """
    try:
        import cv2
    except ImportError:
        return []

    if frame_bgr is None or not hasattr(frame_bgr, "shape"):
        return []

    global _yolo_model, _yolo_has_seg
    with _yolo_lock:
        if _yolo_model is None:
            try:
                from ultralytics import YOLO
                _yolo_model = YOLO("yolov8n-seg.pt")
                _yolo_has_seg = True
            except Exception:
                try:
                    _yolo_model = YOLO("yolov8n.pt")
                    _yolo_has_seg = False
                except Exception:
                    _yolo_model = None
                    return []

    if _yolo_model is None:
        return []

    try:
        # conf=0.15 so stationary objects (e.g. wrench) with marginal confidence are still returned
        results = _yolo_model(frame_bgr, verbose=False, conf=0.15)
    except Exception:
        return []

    h, w = frame_bgr.shape[:2]
    out = []
    for r in results:
        if r.boxes is None:
            continue
        boxes = r.boxes
        names = r.names or {}
        for i in range(len(boxes)):
            xyxy = boxes.xyxy[i]
            conf = float(boxes.conf[i]) if boxes.conf is not None else 0.0
            cls_id = int(boxes.cls[i]) if boxes.cls is not None else 0
            class_name = names.get(cls_id, "unknown")
            det = {
                "class": class_name,
                "confidence": round(conf, 3),
                "bbox": [int(xyxy[0]), int(xyxy[1]), int(xyxy[2]), int(xyxy[3])],
            }
            if _yolo_has_seg and r.masks is not None and hasattr(r.masks, "xy") and i < len(r.masks.xy):
                xy = r.masks.xy[i]
                if xy is not None and hasattr(xy, "__len__") and len(xy) >= 3:
                    pts = np.asarray(xy, dtype=np.int32)
                    pts[:, 0] = np.clip(pts[:, 0], 0, w - 1)
                    pts[:, 1] = np.clip(pts[:, 1], 0, h - 1)
                    det["contour"] = pts.tolist()
            out.append(det)
    return _filter_detections(out, h, w)


def draw_overlay(
    frame_bgr,
    detections: list[dict[str, Any]],
    current_step_index: int | None = None,
    focus_keyword: str | None = None,
):
    """
    Draw bounding boxes and class labels on frame_bgr (in-place).
    If focus_keyword is set, draw matching detection(s) with distinct color/thickness.
    Returns the same frame (modified).
    """
    try:
        import cv2
    except ImportError:
        return frame_bgr

    if frame_bgr is None or not detections:
        return frame_bgr

    for d in detections:
        bbox = d.get("bbox")
        if not bbox or len(bbox) != 4:
            continue
        x1, y1, x2, y2 = bbox
        class_name = d.get("class", "?")
        conf = d.get("confidence", 0)
        label = f"{class_name} {conf:.2f}"

        # Emphasize if this detection matches the current step's focus
        is_focus = (
            focus_keyword
            and focus_keyword.lower() in (class_name or "").lower()
        )
        if is_focus:
            color = (0, 255, 0)  # green
            thickness = 3
        else:
            color = (0, 165, 255)  # orange
            thickness = 2

        contour = d.get("contour")
        if contour and len(contour) >= 3:
            pts = np.array(contour, dtype=np.int32)
            cv2.polylines(frame_bgr, [pts], True, color, thickness)
        else:
            cv2.rectangle(frame_bgr, (x1, y1), (x2, y2), color, thickness)

        (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
        cv2.rectangle(frame_bgr, (x1, y1 - th - 6), (x1 + tw, y1), color, -1)
        cv2.putText(
            frame_bgr, label, (x1, y1 - 4),
            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1,
        )

    return frame_bgr
