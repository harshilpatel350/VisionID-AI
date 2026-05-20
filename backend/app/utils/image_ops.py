from __future__ import annotations
import cv2
import numpy as np

def decode_image_bytes(image_bytes: bytes) -> np.ndarray | None:
    arr = np.frombuffer(image_bytes, dtype=np.uint8)
    img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    return img

def encode_jpeg(frame: np.ndarray, quality: int = 90) -> bytes:
    ok, buf = cv2.imencode(".jpg", frame, [int(cv2.IMWRITE_JPEG_QUALITY), quality])
    if not ok:
        raise ValueError("Could not encode JPEG")
    return buf.tobytes()

def crop_with_padding(frame: np.ndarray, box: tuple[int, int, int, int], padding: float = 0.15) -> np.ndarray:
    h, w = frame.shape[:2]
    x1, y1, x2, y2 = box
    bw, bh = x2 - x1, y2 - y1
    px, py = int(bw * padding), int(bh * padding)
    nx1, ny1 = max(0, x1 - px), max(0, y1 - py)
    nx2, ny2 = min(w, x2 + px), min(h, y2 + py)
    return frame[ny1:ny2, nx1:nx2]
