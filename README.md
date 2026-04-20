# 🎵 Gesture Spotify Controller

Control Spotify with your hand gestures using your laptop webcam!

---

## Gestures

| Gesture | Action |
|---------|--------|
| ✋ Open Palm (5 fingers) | Pause / Play |
| ☝️ Index finger → swipe RIGHT | Next Track |
| ☝️ Index finger → swipe LEFT | Previous Track |
| 👍 Thumb Up | Volume +10% |
| ✊ Fist (all fingers down) | Volume -10% |

---

## Setup (Step by Step)

### Step 1 — Install Python
Make sure Python 3.9+ is installed:
```
python --version
```

### Step 2 — Install dependencies
```bash
pip install -r requirements.txt
```

### Step 3 — Create Spotify App

1. Go to https://developer.spotify.com/dashboard
2. Log in with your Spotify account
3. Click **"Create App"**
4. Fill in:
   - App name: `Gesture Controller` (anything)
   - Redirect URI: `http://localhost:8888/callback`
5. Click **Settings** → copy your **Client ID** and **Client Secret**

### Step 4 — Add credentials to .env

Open the `.env` file and fill in:
```
SPOTIPY_CLIENT_ID=paste_your_client_id
SPOTIPY_CLIENT_SECRET=paste_your_client_secret
SPOTIPY_REDIRECT_URI=http://localhost:8888/callback
```

### Step 5 — Run!

```bash
python gesture_spotify.py
```

On first run, a browser window will open asking you to log in to Spotify
and authorize the app. Do that once — after that it remembers you.

> ⚠️ **Important**: Spotify must already be playing on some device
> (phone, laptop, etc.) for playback controls to work.

---

## Troubleshooting

**"No active device found"**
→ Open Spotify on your phone or laptop and start playing something first.

**Gestures not detecting well**
→ Make sure your hand is clearly visible, good lighting, plain background.

**Volume not changing**
→ Some free Spotify accounts don't support volume API. Try next/prev instead.

---

## How it works

```
Webcam → MediaPipe (hand landmarks) → Gesture Logic → Spotipy → Spotify API
```

MediaPipe detects 21 hand landmarks in real-time.
We check which fingers are up/down and track hand movement to classify gestures.
Spotipy sends commands to Spotify's Web API.

---

Made with ❤️ using OpenCV + MediaPipe + Spotipy
