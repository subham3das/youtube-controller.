
import cv2
import mediapipe as mp
import pyautogui
import numpy as np
import time
import webbrowser
from collections import deque

# ── Config ──────────────────────────────────────────────────────────────────
GESTURE_HOLD_TIME   = 0.7   # seconds to hold gesture before triggering
COOLDOWN_TIME        = 1.2   # minimum seconds between ANY two triggers
WINDOW_NAME          = "YouTube Gesture Controller  |  Press Q to quit"
WEBCAM_INDEX         = 0
FLIP_CAMERA          = True  # Mirror the webcam feed (natural feel)

# Smoothing: how many recent frames we look at, and how many of them must
# agree before we consider a gesture "stable". Raising STABILITY_THRESHOLD
# relative to HISTORY_LEN makes the system less twitchy/flicker-prone.
HISTORY_LEN          = 8
STABILITY_THRESHOLD  = 6   # need 6 of the last 8 frames to agree

# Some actions (like opening a browser) are more disruptive than a simple
# key press, so we ask for a slightly longer hold before triggering them.
GESTURE_HOLD_OVERRIDES = {
    "OPEN_YOUTUBE": 1.2,
}

pyautogui.FAILSAFE = False  # Don't crash when mouse hits screen edge

# MediaPipe setup 
mp_hands    = mp.solutions.hands
mp_drawing  = mp.solutions.drawing_utils
mp_styles   = mp.solutions.drawing_styles

# Finger landmark indices 
WRIST       = 0
THUMB_CMC   = 1; THUMB_MCP  = 2; THUMB_IP   = 3; THUMB_TIP  = 4
INDEX_MCP   = 5; INDEX_PIP  = 6; INDEX_DIP  = 7; INDEX_TIP  = 8
MIDDLE_MCP  = 9; MIDDLE_PIP =10; MIDDLE_DIP =11; MIDDLE_TIP =12
RING_MCP    =13; RING_PIP   =14; RING_DIP   =15; RING_TIP   =16
PINKY_MCP   =17; PINKY_PIP  =18; PINKY_DIP  =19; PINKY_TIP  =20


# Helpers 

def lm(landmarks, idx):
    """Return (x, y, z) for a landmark index."""
    p = landmarks[idx]
    return np.array([p.x, p.y, p.z])

def dist(a, b):
    return np.linalg.norm(a - b)

def finger_up(lms, tip, pip):
    """True if the finger tip is above (lower y) the PIP joint."""
    return lms[tip].y < lms[pip].y

def thumb_extended(lms):
    """
    Distance-based thumb check (orientation-agnostic-ish): the thumb is
    considered extended if its tip is meaningfully farther from the pinky
    knuckle than the thumb's own base joint is. This is far more reliable
    than a pure y-coordinate check when the hand is tilted, and it's what
    lets us tell 'fist' apart from 'thumb splayed out' gestures like the
    shaka sign used for Open YouTube.
    """
    tip       = lm(lms, THUMB_TIP)
    mcp       = lm(lms, THUMB_MCP)
    pinky_mcp = lm(lms, PINKY_MCP)
    return dist(tip, pinky_mcp) > dist(mcp, pinky_mcp) * 1.3

def thumb_up_check(lms, handedness):
    """True if thumb tip is clearly above the thumb MCP."""
    tip = lm(lms, THUMB_TIP)
    mcp = lm(lms, THUMB_MCP)
    return tip[1] < mcp[1] - 0.04

def thumb_down_check(lms, handedness):
    """True if thumb tip is clearly below the thumb MCP."""
    tip = lm(lms, THUMB_TIP)
    mcp = lm(lms, THUMB_MCP)
    return tip[1] > mcp[1] + 0.04

def fingers_extended(lms):
    """Return list of booleans [thumb, index, middle, ring, pinky]."""
    extended = [thumb_extended(lms)]
    for tip, pip_ in ((INDEX_TIP, INDEX_PIP),
                       (MIDDLE_TIP, MIDDLE_PIP),
                       (RING_TIP, RING_PIP),
                       (PINKY_TIP, PINKY_PIP)):
        extended.append(lms[tip].y < lms[pip_].y)
    return extended


def classify_gesture(lms, handedness):
    """
    Returns a gesture string or None.
    Priority: specific multi-finger gestures before simpler ones.
    """
    ext = fingers_extended(lms)
    # ext = [thumb, index, middle, ring, pinky]
    thumb, index, middle, ring, pinky = ext

    fingers_count = sum(ext[1:])  

    t_tip = lm(lms, THUMB_TIP)
    i_tip = lm(lms, INDEX_TIP)
    pinch_dist = dist(t_tip, i_tip)

    if thumb and pinky and not index and not middle and not ring and pinch_dist > 0.08:
        return "OPEN_YOUTUBE"

    # Pinch: thumb tip close to index tip
    if pinch_dist < 0.05:
        return "PINCH"

    # Fist: all fingers closed
    if fingers_count == 0 and not thumb:
        return "FIST"

    # Open hand: all fingers open
    if fingers_count == 4 and thumb:
        return "OPEN_HAND"

    # Rock sign: index + pinky up, middle + ring down, thumb tucked
    if index and not middle and not ring and pinky and not thumb:
        return "ROCK"

    # Thumbs Up: only thumb up, fist otherwise
    if fingers_count == 0 and thumb and thumb_up_check(lms, handedness):
        return "THUMBS_UP"

    # Thumbs Down: only thumb down, fist otherwise
    if fingers_count == 0 and thumb and thumb_down_check(lms, handedness):
        return "THUMBS_DOWN"

    # Three fingers: index + middle + ring
    if index and middle and ring and not pinky:
        return "THREE_FINGERS"

    # Two fingers (peace/V): index + middle only
    if index and middle and not ring and not pinky:
        return "TWO_FINGERS"

    # One finger (pointing up): only index
    if index and not middle and not ring and not pinky:
        return "ONE_FINGER"

    return None


# Action map 

GESTURE_ACTIONS = {
    "FIST":         ("Play / Pause",    lambda: pyautogui.press("space")),
    "THUMBS_UP":    ("Volume Up",       lambda: pyautogui.press("up")),
    "THUMBS_DOWN":  ("Volume Down",     lambda: pyautogui.press("down")),
    "ONE_FINGER":   ("Skip +5s",        lambda: pyautogui.press("right")),
    "TWO_FINGERS":  ("Skip -5s",        lambda: pyautogui.press("left")),
    "OPEN_HAND":    ("Fullscreen",      lambda: pyautogui.press("f")),
    "PINCH":        ("Mute / Unmute",   lambda: pyautogui.press("m")),
    "ROCK":         ("Next Video",      lambda: pyautogui.hotkey("shift", "n")),
    "THREE_FINGERS":("Like Video",      lambda: pyautogui.press("l")),
    "OPEN_YOUTUBE": ("Open YouTube",    lambda: webbrowser.open("https://www.youtube.com")),
}

GESTURE_COLORS = {
    "FIST":         (0,   165, 255),
    "THUMBS_UP":    (0,   255,   0),
    "THUMBS_DOWN":  (0,   0,   255),
    "ONE_FINGER":   (255, 200,   0),
    "TWO_FINGERS":  (255, 100,   0),
    "OPEN_HAND":    (255,   0, 200),
    "PINCH":        (100, 200, 255),
    "ROCK":         (200,   0, 255),
    "THREE_FINGERS":(0,   255, 200),
    "OPEN_YOUTUBE": (0,   215, 255),
}


# Main controller 

class GestureController:
    def __init__(self):
        self.gesture_start_time  = None
        self.current_gesture     = None
        self.last_triggered      = None
        self.last_trigger_time   = 0
        self.last_action_label   = ""
        self.action_display_time = 0
        self.history             = deque(maxlen=HISTORY_LEN)
        # NEUTRAL-GATE: once a gesture fires, no new trigger (same or
        # different gesture) is allowed until the hand passes through
        # "no recognized gesture" first. This is what stops flicker
        # between two similar gestures from firing a burst of
        # conflicting key presses.
        self.awaiting_release    = False

    def update(self, gesture):
        now = time.time()
        self.history.append(gesture)

        # Majority vote to smooth flickering
        counts = {}
        for g in self.history:
            if g:
                counts[g] = counts.get(g, 0) + 1
        stable = max(counts, key=counts.get) if counts else None
        if not stable or counts.get(stable, 0) < STABILITY_THRESHOLD:
            stable = None

        if stable != self.current_gesture:
            self.current_gesture    = stable
            self.gesture_start_time = now if stable else None

        # Hand passed back through neutral -> unlock the gate
        if stable is None:
            self.awaiting_release = False

        hold_time_needed = GESTURE_HOLD_OVERRIDES.get(stable, GESTURE_HOLD_TIME)

        if (stable and
                not self.awaiting_release and
                self.gesture_start_time and
                (now - self.gesture_start_time) >= hold_time_needed and
                (now - self.last_trigger_time) >= COOLDOWN_TIME):
            self._trigger(stable)
            self.last_triggered    = stable
            self.last_trigger_time = now
            self.awaiting_release  = True

    def _trigger(self, gesture):
        if gesture in GESTURE_ACTIONS:
            label, action = GESTURE_ACTIONS[gesture]
            action()
            self.last_action_label   = f"✔ {label}"
            self.action_display_time = time.time()
            print(f"[ACTION] {label}")

    def hold_progress(self):
        """0.0–1.0 fill for the hold progress bar."""
        if not self.current_gesture or not self.gesture_start_time:
            return 0.0
        needed = GESTURE_HOLD_OVERRIDES.get(self.current_gesture, GESTURE_HOLD_TIME)
        elapsed = time.time() - self.gesture_start_time
        return min(elapsed / needed, 1.0)


# ── Drawing helpers ──────────────────────────────────────────────────────────

def draw_overlay(frame, controller, gesture):
    h, w = frame.shape[:2]
    color = GESTURE_COLORS.get(gesture, (200, 200, 200)) if gesture else (80, 80, 80)

    # Semi-transparent top bar
    overlay = frame.copy()
    cv2.rectangle(overlay, (0, 0), (w, 60), (20, 20, 20), -1)
    cv2.addWeighted(overlay, 0.6, frame, 0.4, 0, frame)

    label = gesture.replace("_", " ") if gesture else "No gesture"
    if controller.awaiting_release and gesture:
        label += "  (release to re-trigger)"
    cv2.putText(frame, label, (14, 38),
                cv2.FONT_HERSHEY_SIMPLEX, 1.0, color, 2, cv2.LINE_AA)

    # Hold progress bar
    progress = controller.hold_progress()
    bar_w = int((w - 28) * progress)
    cv2.rectangle(frame, (14, 48), (w - 14, 56), (50, 50, 50), -1)
    if bar_w > 0:
        cv2.rectangle(frame, (14, 48), (14 + bar_w, 56), color, -1)

    # Last action flash (2 s)
    if time.time() - controller.action_display_time < 2.0:
        cv2.putText(frame, controller.last_action_label, (14, h - 18),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 120), 2, cv2.LINE_AA)

    # Cheat-sheet (bottom-right)
    sheet = [
        "✊  Fist       → Play/Pause",
        "👍  Thumb Up   → Vol+",
        "👎  Thumb Down → Vol-",
        "☝   1 Finger   → +5s",
        "✌   2 Fingers  → -5s",
        "🖐   Open Hand  → Fullscreen",
        "🤙  Pinch      → Mute",
        "🤘  Rock       → Next",
        "🖖  3 Fingers  → Like",
        "🤙  Shaka      → Open YouTube",
    ]
    for i, line in enumerate(sheet):
        y = h - (len(sheet) - i) * 22 - 10
        cv2.putText(frame, line, (w - 340, y),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.45, (180, 180, 180), 1, cv2.LINE_AA)

    return frame


# ── Entry point ───────────────────────────────────────────────────────────────

def main():
    print(__doc__)
    print("Starting webcam… Make sure YouTube is open and the browser is focused.")
    print("Press Q in the camera window to quit.\n")

    cap = cv2.VideoCapture(WEBCAM_INDEX)
    if not cap.isOpened():
        print("ERROR: Could not open webcam. Check WEBCAM_INDEX in the script.")
        return

    controller = GestureController()

    with mp_hands.Hands(
        model_complexity         = 1,
        max_num_hands            = 1,
        min_detection_confidence = 0.7,
        min_tracking_confidence  = 0.6,
    ) as hands:

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            if FLIP_CAMERA:
                frame = cv2.flip(frame, 1)

            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            rgb.flags.writeable = False
            results = hands.process(rgb)
            rgb.flags.writeable = True
            frame = cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)

            gesture = None
            if results.multi_hand_landmarks:
                for hand_lms, hand_info in zip(
                        results.multi_hand_landmarks,
                        results.multi_handedness):

                    # Draw skeleton
                    mp_drawing.draw_landmarks(
                        frame, hand_lms,
                        mp_hands.HAND_CONNECTIONS,
                        mp_styles.get_default_hand_landmarks_style(),
                        mp_styles.get_default_hand_connections_style(),
                    )

                    handedness = hand_info.classification[0].label
                    gesture = classify_gesture(hand_lms.landmark, handedness)

            controller.update(gesture)
            frame = draw_overlay(frame, controller, gesture)

            cv2.imshow(WINDOW_NAME, frame)
            key = cv2.waitKey(1) & 0xFF
            if key == ord("q") or key == ord("Q"):
                break

    cap.release()
    cv2.destroyAllWindows()
    print("Gesture controller stopped.")


if __name__ == "__main__":
    main()