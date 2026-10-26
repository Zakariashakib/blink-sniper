# Blink Sniper: Game Design & Presentation Document

---

## 1. Simple Explanation

**What is Blink Sniper?**
Imagine playing a video game where you don't need a mouse or a keyboard to shoot. In **Blink Sniper**, your face is the controller. You aim by moving your head, and you pull the trigger by literally blinking your eyes. It is a completely hands-free, 2D sniper action game designed to test your focus, timing, and reflexes using computer vision.

### Intro Speech (30–60 Seconds)
*"Good morning, everyone. How many times have you played a game where clicking a mouse gets boring? Today, I want to introduce you to a game that takes immersion to a whole new level. It's called **Blink Sniper**. In this game, your hands are completely free. The webcam tracks your eyes in real-time. You look at the target to aim, and you literally blink to pull the trigger. It is a story-driven, action-packed sniper game that pushes the boundaries of accessibility and interactive gameplay. Welcome to the future of gaming."*

## 2. Game Running Instructions

টার্মিনালে গেমটি চালু করার জন্য নিচের কমান্ডটি ব্যবহার করুন:

```powershell
python "BLINK SNIPER.py"
```

যদি আপনি ভার্চুয়াল এনভায়রনমেন্টে থাকেন, তবে নিচের কমান্ডটি ব্যবহার করুন:
```powershell
./.venv/Scripts/python.exe "BLINK SNIPER.py"
```

---

## 3. Game Story

**"Only Your Eyes Can Save Her."**

You are an elite, retired sniper. You thought you left the battlefield behind, until a notorious criminal syndicate kidnapped your girlfriend. Now, they are holding her hostage in a heavily guarded fortress. You don't have an army. You only have your sniper rifle, your focus, and your eyes. 

The story is divided into three intense chapters:
*   **Level 1 (The Training Ground):** You dust off your old rifle and recalibrate your aim on a hidden training ground. You must prove to yourself that your eyes are still sharp.
*   **Level 2 (The Enemy Camp):** You infiltrate the outer perimeter of the syndicate's jungle base. Guards are actively patrolling and shooting back. It's a fight for survival.
*   **Level 3 (The Rescue Mission):** The heart of the enemy base. You must breach the facility, clear the heavy guards, and finally face the Boss who is holding your girlfriend hostage. One wrong move, one stray bullet, and you lose everything.

---

## 3. Gameplay Mechanics

Blink Sniper uses a highly innovative control scheme:
*   **Eye Movement Aiming:** The crosshair naturally follows your face/eye movement via webcam tracking.
*   **Blink to Shoot:** A standard blink instantly fires a normal sniper round.
*   **Long Blink (Charged Shot):** Keeping your eyes closed for a fraction of a second charges the sniper rifle, unleashing a devastating shot required to pierce heavy armor or take down bosses.
*   **Mouse Fallback Mode:** An accessible fallback mode allowing players without webcams (or in poor lighting) to play using standard mouse controls.
*   **Difficulty Modes:** 
    *   **Easy Mode:** High health (10 hearts), slower enemies, highly inaccurate enemy fire. Designed for beginners and casual players.
    *   **Medium Mode:** Standard health (3 hearts), aggressive and accurate enemies. Designed for a real challenge.

---

## 4. Level Design

*   **Level 1: Training**
    *   **Goal:** Learn the controls without pressure.
    *   **Environment:** Static and slow-moving target boards. 
    *   **Mechanic:** Shoot 5 targets within a generous shot limit to proceed.
*   **Level 2: Enemy Camp**
    *   **Goal:** Survive an active firefight.
    *   **Environment:** Jungle base with neon accents.
    *   **Mechanic:** Enemies ("Guards" and "Snipers") shoot back. The player must dodge bullets (by taking out enemies quickly) and survive multiple waves.
*   **Level 3: Rescue Mission**
    *   **Goal:** Defeat the Boss and save the hostage.
    *   **Environment:** High-tech indoor combat hall.
    *   **Mechanic:** Progresses in 3 phases. Starts with clearing guards, escalates to heavy armored units, and culminates in a final Boss fight with a hostage mechanic. The Boss must be defeated carefully to avoid hitting the hostage.

---

## 5. UI/UX Design

The user interface is designed to feel sleek, modern, and tactical.
*   **Color Palette:** Deep dark backgrounds with high-contrast Neon Green, Neon Blue, and Neon Red accents.
*   **HUD (Heads Up Display):**
    *   **Health Bar:** Represented by pixel-art hearts.
    *   **Score & Accuracy:** Live tracking of player performance.
    *   **Charge Bar:** A visual indicator filling up when the player closes their eyes, signaling a charged shot.
*   **Menus:** Solid color, highly legible buttons with smooth hover animations and glowing effects.
*   **Webcam Feed:** A small, transparent PiP (Picture-in-Picture) window showing the facial tracking mesh to help the user stay centered.

---

## 6. Unique Features

*   **Hands-Free Gameplay:** Completely playable without traditional hardware inputs.
*   **Blink-Based Shooting System:** Translating human reflexes (blinking) into direct mechanical actions in-game.
*   **Accessibility-Focused:** A wonderful proof of concept for gamers with motor disabilities who cannot use traditional controllers.
*   **Real-Time Computer Vision:** Uses cutting-edge AI (MediaPipe) running locally to achieve zero-latency eye tracking.

---

## 7. Tech Stack

*   **Engine:** `Python` + `Pygame` (For rendering, audio, and game loop mechanics).
*   **Computer Vision:** `OpenCV` (For webcam capture).
*   **Facial Tracking:** `Google MediaPipe` (For detecting 468 facial landmarks and calculating the precise Eye Aspect Ratio - EAR).
*   **Math & Logic:** Standard Python libraries (`math`, `time`, `random`) for bullet vectors, time dilation, and spawning logic.

---

## 8. Full PRD (Product Requirements Document)

### Project Overview
Blink Sniper is an experimental 2D action game leveraging computer vision to map player facial movements to in-game controls.

### Objectives
1.  Develop a fully functional game using alternative control schemes.
2.  Provide a smooth, bug-free, three-level progression system.
3.  Ensure high accessibility and ease of use.

### Features
*   Facial landmark tracking.
*   Dynamic difficulty scaling.
*   Multi-phase boss fights.
*   Cinematic story transitions.

### Gameplay Systems
*   **Entity System:** Object-oriented design for Bullets, Enemies, and Bosses.
*   **State Machine:** Centralized game states (`menu`, `playing`, `win`, `lose`, `cinematic`).
*   **Hit Detection:** Mathematical distance-based collision detection (`math.dist`).

### Technical Requirements
*   Python 3.x
*   Webcam (720p recommended)
*   Libraries: `pygame`, `opencv-python`, `mediapipe`

### Future Improvements
*   Integration of voice commands for reloading.
*   Online leaderboards.
*   More diverse environments and weapons.

---

## 9. Presentation Script

**Slide 1: Title Slide (Blink Sniper)**
*"Hello everyone. Today I am thrilled to present our project: Blink Sniper. A game where your eyes are your ultimate weapon."*

**Slide 2: The Problem with Traditional Games**
*"We all love gaming, but standard controllers and mice haven't changed in decades. Furthermore, millions of people with physical disabilities find traditional gaming hardware difficult to use. We asked ourselves: How can we make a game completely hands-free?"*

**Slide 3: The Solution (How it Works)**
*"Enter Blink Sniper. Using Python, OpenCV, and AI facial tracking, our game watches your face. You move your head to aim the crosshair, and you simply blink your eyes to shoot. It's incredibly intuitive and feels like magic."*

**Slide 4: The Story**
*"But technology alone isn't enough; we needed a great story. You play as a retired sniper. Criminals have kidnapped your girlfriend, and you must fight through three intense levels—from a training ground to an enemy fortress—to get her back. The stakes are high, and every blink counts."*

**Slide 5: The Gameplay & Levels**
*"The game scales in difficulty. Level 1 teaches you the ropes. Level 2 throws enemies that shoot back at you. Level 3 introduces heavy armor, and a final Boss fight where you must use a 'Charged Shot'—holding your blink for a second—to break his defenses without hitting the hostage."*

**Slide 6: Tech Stack**
*"To build this, we used Pygame for the graphics engine, OpenCV to capture the video feed, and Google's MediaPipe AI to calculate the exact 'Eye Aspect Ratio' in real-time, allowing us to detect blinks instantly."*

**Slide 7: Conclusion**
*"Blink Sniper is more than just a game; it's a proof of concept for the future of accessible, immersive entertainment. Thank you, and I’d now love to show you a quick live demo!"*
