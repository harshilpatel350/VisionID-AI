from __future__ import annotations
from dataclasses import dataclass
import numpy as np

@dataclass
class TrackedFace:
    track_id: int
    bbox: tuple[int, int, int, int]
    frames_seen: int
    last_seen_frame: int
    person_id: int | None = None
    smoothed_mood: str = "neutral"

class FaceTracker:
    def __init__(self, iou_threshold: float = 0.3, max_missing_frames: int = 5):
        self.iou_threshold = iou_threshold
        self.max_missing_frames = max_missing_frames
        self.tracks: list[TrackedFace] = []
        self.next_track_id = 1
        self.current_frame = 0

    def _bbox_iou(self, box1: tuple[int, int, int, int], box2: tuple[int, int, int, int]) -> float:
        xA = max(box1[0], box2[0])
        yA = max(box1[1], box2[1])
        xB = min(box1[2], box2[2])
        yB = min(box1[3], box2[3])
        
        interArea = max(0, xB - xA + 1) * max(0, yB - yA + 1)
        box1Area = (box1[2] - box1[0] + 1) * (box1[3] - box1[1] + 1)
        box2Area = (box2[2] - box2[0] + 1) * (box2[3] - box2[1] + 1)
        
        iou = interArea / float(box1Area + box2Area - interArea + 1e-6)
        return iou

    def update(self, current_bboxes: list[tuple[int, int, int, int]]) -> list[int]:
        """
        Updates the tracker with new bboxes for the current frame.
        Returns a list of track IDs corresponding to the input current_bboxes.
        """
        self.current_frame += 1
        assigned_track_ids = [-1] * len(current_bboxes)
        
        if not self.tracks:
            # First frame or all tracks lost
            for i, bbox in enumerate(current_bboxes):
                self.tracks.append(TrackedFace(self.next_track_id, bbox, 1, self.current_frame))
                assigned_track_ids[i] = self.next_track_id
                self.next_track_id += 1
            return assigned_track_ids

        # Compute IoU matrix
        iou_matrix = np.zeros((len(current_bboxes), len(self.tracks)), dtype=np.float32)
        for i, bbox in enumerate(current_bboxes):
            for j, track in enumerate(self.tracks):
                iou_matrix[i, j] = self._bbox_iou(bbox, track.bbox)

        # Greedy assignment
        matched_det = set()
        matched_trk = set()
        
        # Keep assigning max IoU until below threshold
        while len(matched_det) < len(current_bboxes) and len(matched_trk) < len(self.tracks):
            max_idx = np.unravel_index(np.argmax(iou_matrix, axis=None), iou_matrix.shape)
            max_iou = iou_matrix[max_idx]
            
            if max_iou < self.iou_threshold:
                break
                
            det_idx, trk_idx = max_idx
            if det_idx not in matched_det and trk_idx not in matched_trk:
                # Match found
                assigned_track_ids[det_idx] = self.tracks[trk_idx].track_id
                self.tracks[trk_idx].bbox = current_bboxes[det_idx]
                self.tracks[trk_idx].frames_seen += 1
                self.tracks[trk_idx].last_seen_frame = self.current_frame
                
                matched_det.add(det_idx)
                matched_trk.add(trk_idx)
            
            # Mask out this row and col
            iou_matrix[det_idx, :] = -1
            iou_matrix[:, trk_idx] = -1

        # Create new tracks for unmatched detections
        for i, bbox in enumerate(current_bboxes):
            if i not in matched_det:
                self.tracks.append(TrackedFace(self.next_track_id, bbox, 1, self.current_frame))
                assigned_track_ids[i] = self.next_track_id
                self.next_track_id += 1

        # Prune old tracks
        self.tracks = [t for t in self.tracks if (self.current_frame - t.last_seen_frame) <= self.max_missing_frames]

        return assigned_track_ids
