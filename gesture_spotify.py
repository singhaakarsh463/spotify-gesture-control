import cv2
import mediapipe as mp
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import time
import math
import os
from dotenv import load_dotenv

load_dotenv()

# ─────────────────────────────────────────
#  Spotify Setup
# ─────────────────────────────────────────
auth_manager = SpotifyOAuth(
    client_id=os.getenv("SPOTIPY_CLIENT_ID"),
    client_secret=os.getenv("SPOTIPY_CLIENT_SECRET"),
    redirect_uri="https://127.0.0.1:8888/callback",
    scope="user-modify-playback-state user-read-playback-state",
    open_browser=False
)

# Manual auth flow
token_info = auth_manager.get_cached_token()
if not token_info:
    auth_url = auth_manager.get_authorize_url()
    print("\n🔗 Yeh URL browser mein kholo aur login karo:")
    print(f"\n{auth_url}\n")
    print("Login ke baad browser mein jo URL aaye (127.0.0.1 wala), woh poora copy karke yahan paste karo:")
    response_url = input("URL paste karo: ").strip()
    code = auth_manager.parse_response_code(response_url)
    auth_manager.get_access_token(code)

sp = spotipy.Spotify(auth_manager=auth_manager)

# ─────────────────────────────────────────
#  MediaPipe Setup
# ─────────────────────────────────────────
mp_hands = mp.solutions.hands
mp_draw  = mp.solutions.drawing_utils
hands    = mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=1,
    min_detection_confidence=0.75,
    min_tracking_confidence=0.75
)

# ─────────────────────────────────────────
#  Gesture Detection Helpers
# ─────────────────────────────────────────
def fingers_up(lm):
    """Return list [thumb, index, middle, ring, pinky] — 1=up, 0=down."""
    tips   = [4, 8, 12, 16, 20]
    joints = [3, 6, 10, 14, 18]
    status = []
    # Thumb (compare x instead of y)
    status.append(1 if lm[tips[0]].x < lm[joints[0]].x else 0)
    # Other fingers
    for i in range(1, 5):
        status.append(1 if lm[tips[i]].y < lm[joints[i]].y else 0)
    return status

def hand_center(lm):
    x = sum(p.x for p in lm) / len(lm)
    y = sum(p.y for p in lm) / len(lm)
    return x, y

def detect_gesture(lm, prev_center, frame_w, frame_h):
    """
    Gestures:
      ✋  Open palm (5 fingers up)  → PAUSE / PLAY
      ☝️  Only index up + moving right → NEXT TRACK
      ☝️  Only index up + moving left  → PREV TRACK
      👍  Thumb up                  → VOLUME UP
      👎  Thumb down (fist-like)    → VOLUME DOWN
    """
    f = fingers_up(lm)
    cx, cy = hand_center(lm)

    # Open palm → pause/play
    if sum(f) == 5:
        return "PAUSE_PLAY", cx, cy

    # Only index finger up
    if f[1] == 1 and f[2] == 0 and f[3] == 0 and f[4] == 0:
        if prev_center:
            dx = cx - prev_center[0]
            if abs(dx) > 0.04:           # significant horizontal movement
                return ("NEXT" if dx > 0 else "PREV"), cx, cy
        return None, cx, cy

    # Thumb up (all others down)
    if f[0] == 1 and f[1] == 0 and f[2] == 0 and f[3] == 0 and f[4] == 0:
        return "VOL_UP", cx, cy

    # Fist (all down)
    if sum(f) == 0:
        return "VOL_DOWN", cx, cy

    return None, cx, cy

# ─────────────────────────────────────────
#  Spotify Actions
# ─────────────────────────────────────────
def get_volume():
    try:
        info = sp.current_playback()
        if info and info.get("device"):
            return info["device"]["volume_percent"]
    except:
        pass
    return 50

def do_action(gesture, status_ref):
    try:
        if gesture == "PAUSE_PLAY":
            info = sp.current_playback()
            if info and info["is_playing"]:
                sp.pause_playback()
                status_ref["msg"] = "⏸  Paused"
            else:
                sp.start_playback()
                status_ref["msg"] = "▶  Playing"

        elif gesture == "NEXT":
            sp.next_track()
            status_ref["msg"] = "⏭  Next Track"

        elif gesture == "PREV":
            sp.previous_track()
            status_ref["msg"] = "⏮  Prev Track"

        elif gesture == "VOL_UP":
            vol = min(100, get_volume() + 10)
            sp.volume(vol)
            status_ref["msg"] = f"🔊  Volume {vol}%"

        elif gesture == "VOL_DOWN":
            vol = max(0, get_volume() - 10)
            sp.volume(vol)
            status_ref["msg"] = f"🔉  Volume {vol}%"

    except Exception as e:
        status_ref["msg"] = f"Error: {e}"

# ─────────────────────────────────────────
#  Main Loop
# ─────────────────────────────────────────
def main():
    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH,  1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

    COOLDOWN       = 1.5   # seconds between actions
    last_action    = 0
    prev_center    = None
    status         = {"msg": "Show your hand to begin 🖐"}

    print("\n🎵  Gesture Spotify Controller Started")
    print("────────────────────────────────────────")
    print("  ✋  Open Palm  → Pause / Play")
    print("  ☝️  Swipe Right → Next Track")
    print("  ☝️  Swipe Left  → Prev Track")
    print("  👍  Thumb Up   → Volume +10")
    print("  ✊  Fist        → Volume -10")
    print("  Press Q to quit")
    print("────────────────────────────────────────\n")

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        frame = cv2.flip(frame, 1)
        h, w  = frame.shape[:2]
        rgb   = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        result = hands.process(rgb)

        gesture_detected = None

        if result.multi_hand_landmarks:
            for hand_lm in result.multi_hand_landmarks:
                lm = hand_lm.landmark
                mp_draw.draw_landmarks(frame, hand_lm, mp_hands.HAND_CONNECTIONS,
                    mp_draw.DrawingSpec(color=(0,255,150), thickness=2, circle_radius=4),
                    mp_draw.DrawingSpec(color=(255,255,255), thickness=2))

                now = time.time()
                if now - last_action > COOLDOWN:
                    gesture, cx, cy = detect_gesture(lm, prev_center, w, h)
                    if gesture:
                        gesture_detected = gesture
                        do_action(gesture, status)
                        last_action = now
                        print(f"  {status['msg']}")

                prev_center = hand_center(lm)
        else:
            prev_center = None

        # ── Overlay UI ──────────────────────────────
        overlay = frame.copy()
        cv2.rectangle(overlay, (0, 0), (w, 90), (10, 10, 10), -1)
        cv2.addWeighted(overlay, 0.6, frame, 0.4, 0, frame)

        cv2.putText(frame, "GESTURE SPOTIFY CONTROLLER",
                    (20, 35), cv2.FONT_HERSHEY_DUPLEX, 0.9,
                    (0, 255, 150), 2, cv2.LINE_AA)
        cv2.putText(frame, status["msg"],
                    (20, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.7,
                    (255, 255, 255), 1, cv2.LINE_AA)

        # Cooldown bar
        elapsed = time.time() - last_action
        bar_w   = int(min(elapsed / COOLDOWN, 1.0) * 300)
        cv2.rectangle(frame, (w - 320, 20), (w - 20, 40), (50, 50, 50), -1)
        cv2.rectangle(frame, (w - 320, 20), (w - 320 + bar_w, 40), (0, 220, 100), -1)
        cv2.putText(frame, "ready" if bar_w >= 300 else "wait",
                    (w - 310, 36), cv2.FONT_HERSHEY_SIMPLEX, 0.45,
                    (200, 200, 200), 1)

        cv2.imshow("Gesture Spotify Controller", frame)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
