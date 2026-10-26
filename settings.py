# =============================================================================
# settings.py - Blink Sniper Global Configuration
# =============================================================================

# Screen Dimensions
WIDTH = 1280
HEIGHT = 720
FPS = 60

# Colors
BG_COLOR = (12, 18, 28)         # #0C121C - Deep dark blue
BG_DARK = (6, 10, 18)           # Even darker variant
NEON_GREEN = (0, 255, 150)      # #00FF96 - Main accent
NEON_GREEN_DIM = (0, 180, 100)  # Dimmed green
RED = (255, 50, 50)             # Damage / health
ORANGE = (255, 160, 50)         # Warning
YELLOW = (255, 255, 0)          # Charge mid
WHITE = (255, 255, 255)
GRAY = (100, 100, 100)
DARK_GRAY = (30, 35, 45)       # Button base
PANEL_COLOR = (18, 25, 40)     # Panel backgrounds
CROSSHAIR_COLOR = (0, 255, 150)

# Font
FONT_NAME = 'arial'

# Gameplay
CHARGED_SHOT_THRESHOLD = 750   # ms to fully charge
PLAYER_MAX_HEALTH = 3

# Level configs
LEVEL_CONFIGS = {
    "level1": {
        "name": "LEVEL 1: TRAINING RANGE",
        "objective": "Destroy 10 targets with >= 50% accuracy",
        "total_targets": 10,
        "static_targets": 6,
        "moving_targets": 4,
        "bg_brightness": 40,       # Bright outdoor
        "has_enemies": False,
        "player_health": 999,      # Invincible in training
        "next_level": "level2",
        "required_accuracy": 50,
    },
    "level2": {
        "name": "LEVEL 2: ENEMY CAMP",
        "objective": "Eliminate 25 enemies (3 health)",
        "total_targets": 25,
        "static_targets": 0,
        "moving_targets": 0,
        "bg_brightness": 20,       # Dusk
        "has_enemies": True,
        "enemy_types": ["guard", "sniper", "runner"],
        "player_health": 3,
        "next_level": "level3",
        "required_accuracy": 0,
    },
    "level3": {
        "name": "LEVEL 3: RESCUE MISSION",
        "objective": "Defeat 40 enemies + Boss. Save her!",
        "total_targets": 40,
        "static_targets": 0,
        "moving_targets": 0,
        "bg_brightness": 8,        # Dark night
        "has_enemies": True,
        "enemy_types": ["guard", "sniper", "runner"],
        "player_health": 3,
        "next_level": "victory",
        "required_accuracy": 0,
        "has_boss": True,
    },
}
