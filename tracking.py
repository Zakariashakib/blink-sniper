"""Camera-independent blink state machine and a non-blocking MediaPipe worker.

Frames stay in memory. Only the latest observation is shared with the UI thread.
All timestamps use the monotonic clock; missing/stale observations cancel blinks.
"""
from dataclasses import dataclass
from pathlib import Path
import math
import statistics
import threading
import time


class BlinkDetector:
    def __init__(self, hold=0.18):
        self.hold = hold
        self.baseline = None
        self.samples = []
        self.reset()

    def reset(self):
        self.closed = False
        self.started = None
        self.open_since = None
        self.armed = False
        self.fired = False
        self.last_time = None
        self.progress = 0.0

    def recalibrate(self):
        self.baseline = None
        self.samples.clear()
        self.reset()

    @property
    def calibration_progress(self):
        return min(1.0, len(self.samples) / 40)

    def update(self, ear, now, blink_score=None):
        if (ear is None or not math.isfinite(ear) or ear <= 0) and (blink_score is None or not math.isfinite(blink_score)):
            self.reset()
            return False
        if self.last_time is not None:
            if now <= self.last_time:
                return False
            if now - self.last_time > 0.25:
                self.reset()
        self.last_time = now
        if self.baseline is None:
            if ear is not None and math.isfinite(ear) and ear > 0:
                self.samples.append(ear)
                if len(self.samples) >= 40:
                    # Upper quartile excludes brief blinks during the open-eye setup.
                    self.baseline = sorted(self.samples)[int(len(self.samples) * .75)]
            return False

        close_limit = self.baseline * .68
        open_limit = self.baseline * .78

        is_closed = False
        is_open = False

        # Neural blendshape detection (MediaPipe 0.0 - 1.0)
        if blink_score is not None and math.isfinite(blink_score):
            if blink_score >= 0.45:
                is_closed = True
            elif blink_score < 0.22:
                is_open = True

        # Geometric EAR detection
        if ear is not None and math.isfinite(ear) and ear > 0:
            if ear < close_limit:
                is_closed = True
            elif ear >= open_limit and not is_closed:
                is_open = True

        if is_open:
            self.closed = False
            self.started = None
            self.fired = False
            self.progress = 0
            if self.open_since is None:
                self.open_since = now
            if now - self.open_since >= .14:
                self.armed = True
        elif is_closed:
            self.closed = True
            self.open_since = None
            if not self.armed:
                return False
            if self.started is None:
                self.started = now
            self.progress = min(1.0, (now - self.started) / self.hold)
            if now - self.started >= self.hold and not self.fired:
                self.fired = True
                self.armed = False
                return True
        return False


def eye_measurements(landmarks, width, height):
    """Pixel-correct two-pair EAR plus iris position relative to eye corners.

    Coordinates are projected onto the eye axis so camera mirroring and modest
    head roll do not invert the gaze mapping. Calibration supplies screen axes.
    """
    def p(i):
        return (landmarks[i].x * width, landmarks[i].y * height)
    ears, gaze = [], []
    for outer, inner, top1, bottom1, top2, bottom2, iris in (
        (33, 133, 160, 144, 158, 153, 468),
        (362, 263, 385, 380, 387, 373, 473),
    ):
        a, b = p(outer), p(inner)
        length = math.dist(a, b)
        if length < 2:
            raise ValueError("Eye landmarks too small")
        ears.append((math.dist(p(top1), p(bottom1)) + math.dist(p(top2), p(bottom2))) / (2 * length))
        axis = ((b[0] - a[0]) / length, (b[1] - a[1]) / length)
        c = p(iris)
        dx, dy = c[0] - (a[0]+b[0])/2, c[1] - (a[1]+b[1])/2
        gaze.append(((dx*axis[0]+dy*axis[1])/length,
                     (-dx*axis[1]+dy*axis[0])/length))
    # Bilateral mean EAR: robust against single-eye camera lighting asymmetry
    avg_ear = sum(ears) / len(ears)
    return avg_ear, tuple(statistics.mean(g[i] for g in gaze) for i in (0, 1))


class GazeCalibration:
    TARGETS = ((.5, .5), (.12, .5), (.88, .5), (.5, .18), (.5, .82))

    def __init__(self):
        self.points = []
        self.matrix = None
        self.error = None

    def fit(self, points):
        import numpy as np
        data = np.array(points, dtype=float)
        if data.shape != (5, 2) or not np.all(np.isfinite(data)):
            return False
        # Reject a still iris / closed eyes; do not fabricate a valid calibration.
        if np.ptp(data[:, 0]) < .025 or np.ptp(data[:, 1]) < .012:
            return False
        a = np.column_stack((data, np.ones(5)))
        if np.linalg.matrix_rank(a) < 3:
            return False
        matrix = np.linalg.lstsq(a, np.array(self.TARGETS), rcond=None)[0]
        error = float(np.sqrt(np.mean((a @ matrix - self.TARGETS) ** 2)))
        self.error = error
        if error > .16:
            return False
        self.points = points
        self.matrix = matrix
        return True

    def map(self, gaze):
        import numpy as np
        if self.matrix is None:
            return (.5, .5)
        result = np.array([*gaze, 1.0]) @ self.matrix
        return tuple(float(max(0, min(1, value))) for value in result)


@dataclass(frozen=True)
class Observation:
    timestamp: float = 0
    status: str = "Camera starting..."
    ear: float | None = None
    gaze: tuple | None = None
    nose: tuple | None = None
    preview: object = None
    blink_score: float | None = None


class EyeTracker:
    def __init__(self, camera=0):
        self.camera = camera
        self._observation = Observation()
        self._lock = threading.Lock()
        self._stop = threading.Event()
        self.thread = None

    def start(self):
        if self.thread and self.thread.is_alive():
            return
        self._stop.clear()
        self._publish(Observation(status="Camera starting..."))
        self.thread = threading.Thread(target=self._run, daemon=True, name="eye-tracker")
        self.thread.start()

    def _publish(self, observation):
        with self._lock:
            self._observation = observation

    def latest(self):
        with self._lock:
            return self._observation

    def close(self):
        self._stop.set()
        if self.thread:
            self.thread.join(timeout=2)

    def _run(self):
        camera = model = None
        try:
            import cv2
            import mediapipe as mp
            model_path = Path(__file__).parent / "assets" / "face_landmarker.task"
            if not model_path.exists():
                raise RuntimeError("Model missing: see RUN_GAME.md")
            options = mp.tasks.vision.FaceLandmarkerOptions(
                base_options=mp.tasks.BaseOptions(model_asset_path=str(model_path)),
                running_mode=mp.tasks.vision.RunningMode.VIDEO,
                num_faces=1,
                min_face_detection_confidence=.5,
                min_face_presence_confidence=.5,
                min_tracking_confidence=.5,
                output_face_blendshapes=True,
            )
            model = mp.tasks.vision.FaceLandmarker.create_from_options(options)
            camera = cv2.VideoCapture(self.camera)
            camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            camera.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            if not camera.isOpened():
                raise RuntimeError("Camera unavailable. Check camera permission or device index.")
            last_ms = -1
            while not self._stop.is_set():
                ok, frame = camera.read()
                now = time.monotonic()
                if not ok:
                    self._publish(Observation(now, "Camera frame unavailable"))
                    self._stop.wait(.1)
                    continue
                rgb = cv2.cvtColor(cv2.flip(frame, 1), cv2.COLOR_BGR2RGB)
                stamp = max(last_ms+1, int(now*1000))
                last_ms = stamp
                result = model.detect_for_video(mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb), stamp)
                
                # Check blendshapes for bilateral eye blink
                blink_score = None
                if result.face_blendshapes and len(result.face_blendshapes) > 0:
                    bs = result.face_blendshapes[0]
                    b_left = next((c.score for c in bs if c.category_name in ('eyeBlinkLeft', 'eye_blink_left')), 0.0)
                    b_right = next((c.score for c in bs if c.category_name in ('eyeBlinkRight', 'eye_blink_right')), 0.0)
                    blink_score = min(b_left, b_right)

                preview = cv2.resize(rgb, (192, 144))
                if result.face_landmarks:
                    lm = result.face_landmarks[0]
                    ear, gaze = eye_measurements(lm, rgb.shape[1], rgb.shape[0])
                    # Draw subtle sci-fi tracking markers on preview
                    pw, ph = 192, 144
                    for idx, col in [(1, (126, 229, 192)), (468, (245, 186, 103)), (473, (245, 186, 103))]:
                        px, py = int(lm[idx].x * pw), int(lm[idx].y * ph)
                        cv2.circle(preview, (px, py), 2, col, -1)
                    self._publish(Observation(now, "Face tracked", ear, gaze, (lm[1].x, lm[1].y), preview, blink_score))
                else:
                    self._publish(Observation(now, "Face not found - look toward the camera", preview=preview))
        except Exception as exc:
            self._publish(Observation(time.monotonic(), f"Tracking unavailable: {exc}"))
        finally:
            if camera is not None:
                camera.release()
            if model is not None:
                model.close()
