# 🎮 YouTube Gesture Controller

Control **YouTube entirely with hand gestures** using your webcam—no mouse required (except for searching videos manually). This project uses **OpenCV**, **MediaPipe**, and **PyAutoGUI** to recognize hand gestures in real time and translate them into YouTube keyboard shortcuts for a seamless, touch-free experience.

Perfect for watching videos from a distance, presentations, accessibility use cases, or simply experimenting with computer vision.

---

## ✨ Features

* 🎥 Real-time hand tracking with **MediaPipe**
* 🖐️ Multiple gesture recognition
* ⚡ Instant YouTube keyboard control
* 🛡️ Gesture hold detection to reduce accidental triggers
* 🔄 Cooldown system to prevent repeated actions
* 💻 Lightweight and easy to set up

---

## 🎯 Supported Gestures

| Gesture                  | Action                  |
| ------------------------ | ----------------------- |
| ✊ Fist                   | Play / Pause            |
| 👍 Thumbs Up             | Volume Up               |
| 👎 Thumbs Down           | Volume Down             |
| ☝️ One Finger Up         | Skip Forward 5 Seconds  |
| ✌️ Two Fingers Up        | Skip Backward 5 Seconds |
| 🖐️ Open Hand            | Toggle Fullscreen       |
| 🤏 Pinch (Thumb + Index) | Mute / Unmute           |
| 🤘 Rock Sign             | Next Video              |
| 🤞 Three Fingers Up      | Like Video              |
| 🤙 Shaka / Call Me       | Open YouTube.com        |

---

## 🛠️ Installation

```bash
git clone https://github.com/yourusername/youtube-gesture-controller.git

cd youtube-gesture-controller

pip install opencv-python mediapipe pyautogui numpy
```

---

## ▶️ Run

```bash
python main.py
```

---

## 📌 How It Works

* Your webcam continuously tracks your hand.
* MediaPipe detects hand landmarks.
* The program identifies predefined gestures.
* Holding a gesture for about **0.7 seconds** triggers the corresponding YouTube action.
* Opening YouTube requires a **1.2-second hold** to avoid accidental launches.
* You must return to a neutral hand position before another gesture is accepted, preventing duplicate or conflicting actions.

---

## 🧰 Tech Stack

* Python
* OpenCV
* MediaPipe
* PyAutoGUI
* NumPy

---

## 💡 Use Cases

* Hands-free YouTube control
* Accessibility assistance
* Smart TV / monitor control
* Computer vision learning
* Gesture recognition projects
* Fun AI experiments

---

## ⚠️ Requirements

* Python 3.9+
* A working webcam
* Google Chrome (or any browser with YouTube open)
* Good lighting for reliable hand detection

---

## 🤝 Contributing

Contributions, feature requests, and bug reports are welcome! Feel free to fork the repository and submit a pull request.

---

## ⭐ Support

If you found this project useful, consider giving it a **⭐ Star** on GitHub. It helps others discover the project and motivates future improvements.
