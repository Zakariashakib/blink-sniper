# 🎯 BLINK SNIPER — Eye-Tracking Sniper Action Game

> **"Only Your Eyes Can Save Her."**

**Blink Sniper** is a Python-based 2D sniper action game where you **aim with your head movements** and **shoot by blinking your eyes**. Built with **Pygame**, **OpenCV**, and **Google MediaPipe**, this game is completely **hands-free** — no mouse or keyboard required.

This is also an **accessibility-focused** project designed to make gaming possible for people with physical disabilities.

---

## 🎮 Gameplay Demo

| Feature | Description |
|---|---|
| 🎯 **Aiming** | Move your head to control the crosshair |
| 👁️ **Shooting** | Blink to fire — hold your blink for charged shots |
| 🖱️ **Fallback** | Mouse + Keyboard mode available without webcam |
| 🏆 **3 Levels** | Training → Enemy Camp → Boss Fight + Hostage Rescue |

---

## 🛠️ Tech Stack

| Library | Purpose |
|---|---|
| `Python 3.x` | Core language |
| `Pygame` | Game engine — rendering, audio, game loop |
| `OpenCV (cv2)` | Webcam video capture |
| `MediaPipe` | Google's AI face tracking (468 facial landmarks) |

---

## 🚀 Quick Start

### 1. Clone the repository
```bash
git clone https://github.com/YOUR_USERNAME/blink-sniper.git
cd blink-sniper
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Run the game
```bash
# Full game (all features, all levels)
python "BLINK SNIPER.py"

# Modular version (Level 1 only)
python main.py
```

### Hardware Requirements
- **Python 3.x**
- **Webcam** (720p recommended) — for eye tracking
- Works **without a webcam** too (Mouse Mode)

---

## 🎮 Controls

| Control | Action |
|---|---|
| Head Movement (Eye Tracking) | Move crosshair |
| Blink | Normal shot |
| Long Blink (hold eyes closed) | Charged shot |
| `SPACE` (Hold/Release) | Aim & shoot (Mouse Mode) |
| `Left Click` | Quick shot (Mouse Mode) |
| `E` | Toggle Eye Tracking / Mouse Mode |
| `ESC` | Pause menu |
| `UP/DOWN` | Adjust game speed |

---

## 📖 Story

You are a retired elite sniper. A criminal syndicate has kidnapped your girlfriend. No army, no backup — just your rifle, your focus, and your eyes.

### Level 1: Training Range 🎯
- Learn the controls in a safe environment
- Destroy 5 targets with limited shots
- Player is invincible

### Level 2: Enemy Camp ⚔️
- Active combat against AI enemies (Guards, Snipers, Runners)
- Enemies shoot back and dodge your crosshair
- Survive with 3 health points

### Level 3: Rescue Mission 🏴
- **3 Phases:** Entry Zone → Combat Hall → Boss Fight
- Final boss has a shield (break it with charged shots!)
- **Hostage mechanic** — don't shoot your girlfriend!

---

## 🔬 How Eye Tracking Works

```
Webcam → OpenCV Frame Capture → MediaPipe FaceMesh
→ 468 Landmarks Detected → Nose position moves Crosshair
→ EAR (Eye Aspect Ratio) Calculated → Blink Detected → Shoot!
```

**EAR Formula:**
- EAR < 0.22 → Eyes closed (blink starts)
- Eyes open: hold ≥ 0.75s → **Charged Shot**, hold ≥ 0.1s → **Normal Shot**

---

## 📁 Project Structure

```
BLINK SNIPER/
├── BLINK SNIPER.py          ← Main game (monolithic, all features)
├── main.py                  ← Modular entry point
├── scenes.py                ← Scene Manager, Menu, Level scenes
├── settings.py              ← Global configuration
├── ui.py                    ← Button & HUD classes
├── requirements.txt         ← Python dependencies
└── README.md                ← This file
```

---

## ✨ Key Features

- 🎮 **Fully Hands-Free Gameplay** — play without mouse or keyboard
- 👁️ **Blink-Based Shooting** — natural eye blink as game mechanic
- ♿ **Accessibility Focused** — designed for gamers with physical disabilities
- 🤖 **Real-Time AI** — Google MediaPipe for zero-latency face tracking
- 🎨 **Cinematic Visuals** — neon glow, particles, fog, fireflies, vignette
- ⏱️ **Time Dilation** — slow-motion during charged shots in boss fight
- 🎯 **Dynamic Difficulty** — Easy / Medium modes affect all game entities
- 🏗️ **Dual Architecture** — Monolithic & Modular versions side by side

---

## ⚙️ Difficulty Settings

| Feature | EASY | MEDIUM |
|---|---|---|
| Target Size | Large (40px) | Small (28px) |
| Enemy Speed | ×0.3 | Normal |
| Enemy HP | 1 | 2-6 |
| Boss HP | 5 | 20 |
| Player Health | 10 hearts | 3 hearts |

---

## 📜 License

This project is open source. Feel free to use, modify, and share.

---

## 👤 Author

**Zakaria Shakib**

---

*Built with ❤️ using Python, Pygame, OpenCV & MediaPipe*
