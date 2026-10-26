import pygame
import sys
import random
import time
import math
import cv2

pygame.init()
pygame.mixer.init()

WIDTH, HEIGHT = 1280, 720
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("BLINK SNIPER - Elite Assassin")
clock = pygame.time.Clock()

# ================== COLORS ==================
NEON_GREEN = (0, 255, 150)
NEON_BLUE = (0, 200, 255)
NEON_RED = (255, 50, 80)
NEON_YELLOW = (255, 255, 100)
NEON_PURPLE = (180, 0, 255)
ORANGE = (255, 165, 0)
DARK_BG = (8, 12, 18)
DARK_PANEL = (12, 20, 30)
ACCENT = (0, 255, 150)
WHITE = (255, 255, 255)
GRAY = (120, 130, 140)
WOOD = (60, 40, 25)
WOOD_DARK = (40, 25, 15)

# ================== FONTS ==================
FONT_TITLE = pygame.font.SysFont("Segoe UI", 52, bold=True)
FONT_SUB = pygame.font.SysFont("Segoe UI", 26, bold=True)
FONT_MED = pygame.font.SysFont("Segoe UI", 20, bold=True)
FONT_SMALL = pygame.font.SysFont("Segoe UI", 14)
FONT_TINY = pygame.font.SysFont("Segoe UI", 11)
FONT_HUD = pygame.font.SysFont("Consolas", 28, bold=True)
FONT_HUD_SM = pygame.font.SysFont("Consolas", 14)

# ================== EYE TRACKING ==================
eye_tracking_available = False
face_mesh = None
cap = None
mp_face_mesh = None

def init_eye_tracking():
    global eye_tracking_available, face_mesh, cap, mp_face_mesh
    try:
        import mediapipe as mp
        mp_face_mesh = mp.solutions.face_mesh
        face_mesh = mp_face_mesh.FaceMesh(
            max_num_faces=1,
            refine_landmarks=True,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )
        cap = cv2.VideoCapture(0)
        if cap.isOpened():
            eye_tracking_available = True
            global eye_tracking_enabled
            eye_tracking_enabled = True
            print("Eye tracking initialized!")
        else:
            print("Camera not found")
    except Exception as e:
        print(f"Eye tracking unavailable: {e}")

eye_tracking_enabled = False
EAR_THRESHOLD = 0.22
blink_cooldown = 0
smooth_x = WIDTH // 2
smooth_y = HEIGHT // 2

def get_ear(landmarks):
    left_h = math.dist((landmarks[33].x, landmarks[33].y), (landmarks[133].x, landmarks[133].y))
    left_v = math.dist((landmarks[159].x, landmarks[159].y), (landmarks[145].x, landmarks[145].y))
    left_ear = left_v / left_h if left_h > 0 else 0.3

    right_h = math.dist((landmarks[362].x, landmarks[362].y), (landmarks[263].x, landmarks[263].y))
    right_v = math.dist((landmarks[386].x, landmarks[386].y), (landmarks[374].x, landmarks[374].y))
    right_ear = right_v / right_h if right_h > 0 else 0.3

    return (left_ear + right_ear) / 2

def process_eye_tracking():
    global crosshair_x, crosshair_y, blink_cooldown, smooth_x, smooth_y, cam_frame, face_box
    if not eye_tracking_available:
        return
    ret, frame = cap.read()
    if not ret:
        return
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    
    # Update global cam_frame even if eye tracking is disabled, for HUD display
    cam_frame = cv2.flip(rgb, 1) 
    face_box = None

    if not eye_tracking_enabled:
        return

    results = face_mesh.process(rgb)
    if results.multi_face_landmarks:
        lm = results.multi_face_landmarks[0].landmark
        
        # Calculate bounding box for the mirrored frame
        h, w, _ = frame.shape
        x_min = int(min([l.x for l in lm]) * w)
        x_max = int(max([l.x for l in lm]) * w)
        y_min = int(min([l.y for l in lm]) * h)
        y_max = int(max([l.y for l in lm]) * h)
        # Flip coordinates since cam_frame is flipped
        face_box = (w - x_max, y_min, x_max - x_min, y_max - y_min)

        nose = lm[1]
        head_yaw = (nose.x - 0.5) * 3.0
        eye_y = (lm[159].y + lm[386].y) / 2
        target_x = WIDTH * (0.5 + head_yaw * 0.85 * eye_tracking_sensitivity)
        target_y = HEIGHT * (0.40 + (eye_y - 0.48) * 1.5 * eye_tracking_sensitivity)
        target_x = max(50, min(WIDTH - 50, target_x))
        target_y = max(50, min(HEIGHT - 70, target_y))
        smooth_x += (target_x - smooth_x) * 0.25
        smooth_y += (target_y - smooth_y) * 0.25
        crosshair_x = int(smooth_x)
        crosshair_y = int(smooth_y)
        
        global is_charging, blink_start, charge_level
        ear = get_ear(lm)
        if ear < EAR_THRESHOLD:
            if not is_charging:
                is_charging = True
                blink_start = time.time()
                charge_level = 0
            else:
                charge_level = min(1.0, (time.time() - blink_start) / 0.75)
        else:
            if is_charging:
                is_charging = False
                hold_time = time.time() - blink_start
                if hold_time >= 0.75:
                    shoot(charged=True)
                elif hold_time >= 0.1:
                    shoot(charged=False)
                charge_level = 0

# ================== GAME VARIABLES ==================
current_level = 1
level3_phase = 1
score = 0
shots_fired = 0
hits = 0
health = 4
max_health = 4
combo = 0
max_combo = 0
targets = []
enemies = []
boss = None
girlfriend = None
particles = []
blood_effects = []
enemy_bullets = []
muzzle_flash = []
crosshair_x = WIDTH // 2
crosshair_y = HEIGHT // 2
blink_start = 0
is_charging = False
charge_level = 0
last_shot = 0
game_state = "start"
cam_frame = None
face_box = None
story_text = ""
screen_shake = 0
damage_overlay = 0
global_time_scale = 1.0
hit_marker_time = 0
game_difficulty = "EASY"
eye_tracking_sensitivity = 1.0
kill_feed = []
score_popups = []
wave_timer = 0
background_stars = [(random.randint(0, WIDTH), random.randint(0, HEIGHT), random.randint(1, 3)) for _ in range(80)]

max_shots_level1 = 15
required_hits_level1 = 5
use_mouse_control = True  # Settings: mouse control toggle

# ================== ANIMATION HELPERS ==================
def ease_out(t):
    return 1 - (1 - t) ** 3

def ease_in_out(t):
    return 3 * t * t - 2 * t * t * t

def lerp(a, b, t):
    return a + (b - a) * t

def draw_glow_circle(surface, color, pos, radius, intensity=3):
    r, g, b = color
    for i in range(intensity, 0, -1):
        alpha = max(10, 40 - i * 10)
        s = pygame.Surface((radius * 2 + i * 8, radius * 2 + i * 8), pygame.SRCALPHA)
        pygame.draw.circle(s, (r, g, b, alpha), (radius + i * 4, radius + i * 4), radius + i * 4)
        surface.blit(s, (pos[0] - radius - i * 4, pos[1] - radius - i * 4))

def draw_glow_line(surface, color, start, end, width=2, intensity=2):
    r, g, b = color
    for i in range(intensity, 0, -1):
        alpha = max(20, 50 - i * 15)
        s = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        pygame.draw.line(s, (r, g, b, alpha), start, end, width + i * 2)
        surface.blit(s, (0, 0))
    pygame.draw.line(surface, color, start, end, width)

# ================== CLASSES ==================
class Bullet:
    def __init__(self, x, y, tx, ty, speed=8, color=NEON_YELLOW, radius=3):
        self.x = x
        self.y = y
        angle = math.atan2(ty - y, tx - x)
        self.vx = math.cos(angle) * speed
        self.vy = math.sin(angle) * speed
        self.alive = True
        self.color = color
        self.radius = radius

    def update(self, time_scale=1.0):
        self.x += self.vx * time_scale
        self.y += self.vy * time_scale
        if self.x < 0 or self.x > WIDTH or self.y < 0 or self.y > HEIGHT:
            self.alive = False

    def draw(self):
        pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), self.radius)
        draw_glow_circle(screen, self.color, (int(self.x), int(self.y)), self.radius*2, 2)

class Target:
    def __init__(self, x, y, moving=False):
        self.x = x
        self.y = y
        self.moving = moving
        self.hp = 1
        self.alive = True
        self.spawn_time = time.time()
        self.pulse = 0
        
        if game_difficulty == "EASY":
            self.radius = 40
            self.speed = 0
            self.moving = False
        else:
            self.radius = 28
            self.speed = random.uniform(1.5, 2.5) if moving else 0
        self.dir = random.choice([-1, 1])

    def update(self, time_scale=1.0):
        if self.moving:
            self.x += self.speed * self.dir * time_scale
            if self.x < 180 or self.x > WIDTH - 180:
                self.dir *= -1
        self.pulse = math.sin(time.time() * 3) * 3

    def draw(self):
        age = min(1.0, (time.time() - self.spawn_time) * 3)
        pygame.draw.rect(screen, (30, 30, 35), (self.x - 14, self.y - 46, 28, 76))
        pygame.draw.rect(screen, (50, 50, 55), (self.x - 14, self.y - 46, 28, 76), 2)
        pygame.draw.circle(screen, (40, 40, 45), (int(self.x), int(self.y - 56)), 16)
        pygame.draw.circle(screen, (60, 60, 65), (int(self.x), int(self.y - 56)), 16, 2)
        r = int(self.radius + self.pulse)
        pygame.draw.circle(screen, NEON_RED, (int(self.x), int(self.y - 20)), r, 3)
        pygame.draw.circle(screen, NEON_RED, (int(self.x), int(self.y - 20)), int(r * 0.65), 2)
        pygame.draw.circle(screen, NEON_RED, (int(self.x), int(self.y - 20)), int(r * 0.3), 2)
        draw_glow_circle(screen, NEON_RED, (int(self.x), int(self.y - 20)), 6, 2)

class Enemy:
    def __init__(self, x, y, enemy_type="guard"):
        self.x = x
        self.y = y
        self.type = enemy_type
        self.radius = 26
        
        # Advanced AI Configs
        self.dodge_cooldown = time.time()
        
        if enemy_type == "assault":
            self.speed = 2.5
            self.hp = 2
            self.shoot_delay = 1.0
        elif enemy_type == "runner":
            self.speed = 3.2
            self.hp = 2
            self.shoot_delay = 1.2
        elif enemy_type == "sniper":
            self.speed = 0.5
            self.hp = 3
            self.shoot_delay = 3.5
        elif enemy_type == "heavy":
            self.speed = 0.8
            self.hp = 6
            self.shoot_delay = 2.5
        else: # guard
            self.speed = 1.6
            self.hp = 3
            self.shoot_delay = 2.5
            
        if game_difficulty == "EASY":
            self.speed *= 0.3
            self.shoot_delay = random.uniform(2.5, 3.5)
            self.hp = 1
        elif game_difficulty == "MEDIUM":
            self.shoot_delay = random.uniform(0.7, 0.9)
            
        self.max_hp = self.hp
        self.dir = random.choice([-1, 1])
        self.alive = True
        self.last_shot = time.time() + random.uniform(0, 2)
        self.hit_flash = 0
        self.anim_offset = random.uniform(0, 10)
        self.target_locked = False

    def dodge(self):
        if time.time() - self.dodge_cooldown > 3.0:
            self.dodge_cooldown = time.time()
            self.x += random.choice([-80, 80])
            self.x = max(100, min(WIDTH - 100, self.x))

    def update(self, time_scale=1.0):
        t = time.time()
        
        # Dodge logic (if player aiming near them)
        if math.dist((self.x, self.y - 25), (crosshair_x, crosshair_y)) < 60:
            if self.type in ["assault", "runner", "guard"]:
                self.dodge()
        
        # Movement
        if self.type == "runner":
            self.y += self.speed * time_scale
            if self.y > HEIGHT: self.y = -50
        elif self.type == "sniper":
            # Snipers try to stay near edges
            if self.x > WIDTH/2 and self.x < WIDTH - 100: self.x += self.speed * time_scale
            elif self.x <= WIDTH/2 and self.x > 100: self.x -= self.speed * time_scale
        else:
            self.x += self.speed * self.dir * time_scale
            if self.x < 100 or self.x > WIDTH - 100:
                self.dir *= -1

        # Shooting AI
        if t - self.last_shot > self.shoot_delay / max(0.1, time_scale):
            self.last_shot = t
            # Group attack simulation - slight random delay based on type
            bullet_speed = 6 if self.type == "heavy" else 10 if self.type == "sniper" else 8
            b_color = NEON_RED if self.type == "heavy" else NEON_YELLOW
            b_size = 5 if self.type == "heavy" else 3
            
            # Accuracy based on difficulty
            if game_difficulty == "EASY":
                target_x = random.choice([random.randint(-200, 200), random.randint(WIDTH-200, WIDTH+200)]) # Extremely inaccurate
            else:
                target_x = random.randint(200, WIDTH-200) # Normal accuracy
                
            enemy_bullets.append(Bullet(self.x, self.y - 30, target_x, HEIGHT-50, speed=bullet_speed, color=b_color, radius=b_size))
            create_particles(self.x, self.y - 30, b_color, 5)

        if self.hit_flash > 0:
            self.hit_flash -= 1

    def draw(self):
        t = time.time() + self.anim_offset
        x, y = int(self.x), int(self.y)
        bob = math.sin(t * 2) * 2
        flash = self.hit_flash > 0

        # --- Sniper laser warning ---
        if self.type == "sniper" and time.time() - self.last_shot > self.shoot_delay - 1.5:
            draw_glow_line(screen, (255, 0, 0), (x, y-30), (WIDTH//2 + int(math.sin(t*8)*40), HEIGHT), 1, 2)

        # --- Type-specific colors ---
        if self.type == "heavy":
            vest_c = (80, 80, 85) if not flash else WHITE
            pants_c = (50, 50, 55)
            helmet_c = (60, 60, 65)
            bw = 22  # half body width
        elif self.type == "sniper":
            vest_c = (45, 35, 55) if not flash else WHITE
            pants_c = (35, 30, 45)
            helmet_c = (40, 30, 50)
            bw = 14
        elif self.type == "assault":
            vest_c = (120, 40, 35) if not flash else WHITE
            pants_c = (60, 25, 20)
            helmet_c = (80, 30, 25)
            bw = 16
        else:  # guard / runner
            vest_c = (45, 65, 40) if not flash else WHITE
            pants_c = (35, 50, 30)
            helmet_c = (40, 55, 35)
            bw = 15

        by = y - 25 + int(bob)  # body top y
        skin = (200, 160, 130) if not flash else WHITE

        # --- Boots ---
        leg_move = math.sin(t * 3) * 3
        for side in [-1, 1]:
            bx = x + side * (bw // 2 + 2) + int(side * leg_move)
            pygame.draw.rect(screen, (25, 22, 18), (bx - 5, y + 22, 10, 12), border_radius=2)
            pygame.draw.line(screen, pants_c, (x + side * 4, y + 5), (bx, y + 22), max(4, bw // 3))

        # --- Body / Tactical Vest ---
        pygame.draw.rect(screen, vest_c, (x - bw, by, bw * 2, 32), border_radius=4)
        # Vest detail: pockets / pouches
        if self.type == "heavy":
            pygame.draw.rect(screen, (65, 65, 70), (x - bw + 3, by + 16, bw - 3, 10), border_radius=2)
            pygame.draw.rect(screen, (65, 65, 70), (x + 3, by + 16, bw - 3, 10), border_radius=2)
            # Armor plate
            pygame.draw.rect(screen, (90, 90, 95), (x - bw + 4, by + 4, bw * 2 - 8, 12), border_radius=2)
        else:
            pygame.draw.rect(screen, tuple(max(0, c - 12) for c in vest_c), (x - bw + 3, by + 18, 10, 7), border_radius=1)
            pygame.draw.rect(screen, tuple(max(0, c - 12) for c in vest_c), (x + bw - 13, by + 18, 10, 7), border_radius=1)

        # --- Arms + Gun ---
        arm_y = by + 10
        gun_len = 40 if self.type == "sniper" else 30 if self.type == "heavy" else 25
        gun_w = 5 if self.type == "heavy" else 4 if self.type == "sniper" else 3
        # Right arm holding gun
        gun_end_x = x + bw + gun_len
        gun_end_y = arm_y + 3
        pygame.draw.line(screen, tuple(max(0, c - 5) for c in vest_c), (x + bw, arm_y), (x + bw + 8, arm_y + 2), 5)
        # Gun body
        pygame.draw.line(screen, (30, 30, 28), (x + bw + 5, arm_y + 1), (gun_end_x, gun_end_y), gun_w + 1)
        pygame.draw.line(screen, (45, 45, 42), (x + bw + 5, arm_y + 1), (gun_end_x, gun_end_y), gun_w - 1)
        # Gun barrel tip
        pygame.draw.circle(screen, (55, 55, 50), (gun_end_x, gun_end_y), gun_w // 2 + 1)
        # Sniper scope
        if self.type == "sniper":
            pygame.draw.rect(screen, (50, 50, 55), (x + bw + 12, arm_y - 5, 14, 5), border_radius=2)
            # Scope glint
            pygame.draw.circle(screen, (200, 220, 255), (x + bw + 19, arm_y - 3), 2)
        # Left arm
        pygame.draw.line(screen, tuple(max(0, c - 5) for c in vest_c), (x - bw, arm_y), (x - bw - 5, arm_y + 10), 5)

        # --- Head ---
        head_y = by - 12 + int(bob)
        pygame.draw.circle(screen, skin, (x, int(head_y)), 10)

        # --- Helmet / Headgear ---
        if self.type == "sniper":
            # Hood
            pygame.draw.circle(screen, helmet_c, (x, int(head_y - 2)), 12)
            pygame.draw.rect(screen, helmet_c, (x - 10, int(head_y - 2), 20, 8))
        elif self.type == "heavy":
            # Heavy helmet with visor
            pygame.draw.arc(screen, helmet_c, (x - 13, head_y - 15, 26, 22), 0, math.pi, 4)
            pygame.draw.rect(screen, helmet_c, (x - 13, int(head_y - 8), 26, 8))
            pygame.draw.rect(screen, (40, 40, 42), (x - 10, int(head_y - 1), 20, 5), border_radius=1)
        else:
            # Standard helmet
            pygame.draw.arc(screen, helmet_c, (x - 12, head_y - 14, 24, 20), 0, math.pi, 3)
            pygame.draw.rect(screen, helmet_c, (x - 12, int(head_y - 7), 24, 6))

        # --- Eyes / Goggles ---
        if self.type in ["sniper", "assault"]:
            # Tactical goggles with red glow
            pygame.draw.rect(screen, (20, 20, 20), (x - 8, int(head_y - 2), 16, 5), border_radius=2)
            pygame.draw.circle(screen, NEON_RED, (x - 4, int(head_y)), 2)
            pygame.draw.circle(screen, NEON_RED, (x + 4, int(head_y)), 2)
        elif self.type == "heavy":
            # Visor slit glow
            pygame.draw.line(screen, NEON_RED, (x - 6, int(head_y)), (x + 6, int(head_y)), 2)
        else:
            # Normal eyes
            pygame.draw.circle(screen, (20, 20, 20), (x - 3, int(head_y)), 2)
            pygame.draw.circle(screen, (20, 20, 20), (x + 3, int(head_y)), 2)

        # --- Enemy type indicator (small triangle above) ---
        ind_y = int(head_y) - 22
        ind_color = NEON_RED if self.type in ["assault", "heavy"] else NEON_PURPLE if self.type == "sniper" else NEON_YELLOW
        pygame.draw.polygon(screen, ind_color, [(x, ind_y), (x - 5, ind_y - 8), (x + 5, ind_y - 8)])

        # --- HP bar ---
        bar_w = bw * 2 + 10
        hp_ratio = self.hp / self.max_hp
        bar_x = x - bar_w // 2
        bar_y = int(head_y) - 30
        pygame.draw.rect(screen, (15, 15, 15), (bar_x - 1, bar_y - 1, bar_w + 2, 6), border_radius=2)
        pygame.draw.rect(screen, (30, 30, 30), (bar_x, bar_y, bar_w, 4), border_radius=2)
        hp_col = NEON_GREEN if hp_ratio > 0.5 else NEON_YELLOW if hp_ratio > 0.25 else NEON_RED
        pygame.draw.rect(screen, hp_col, (bar_x, bar_y, int(bar_w * hp_ratio), 4), border_radius=2)

class Girlfriend:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.radius = 20
        self.hit_flash = 0

    def update(self, time_scale=1.0):
        # Slight bobbing
        self.x += math.sin(time.time() * 2) * 0.5 * time_scale
        if self.hit_flash > 0: self.hit_flash -= 1

    def draw(self):
        t = time.time()
        head_y = self.y - 40 + math.sin(t * 3) * 2
        # Body (tied to a chair)
        pygame.draw.rect(screen, (60, 40, 40), (self.x - 12, self.y - 20, 24, 40), border_radius=4)
        # Head
        color = (240, 200, 180)
        if self.hit_flash > 0: color = (255, 0, 0)
        pygame.draw.circle(screen, color, (int(self.x), int(head_y)), 12)
        # Hair (blonde)
        pygame.draw.circle(screen, (220, 200, 50), (int(self.x), int(head_y - 2)), 14, draw_top_left=True, draw_top_right=True)
        # Tears
        pygame.draw.line(screen, (100, 150, 255), (self.x - 4, head_y + 4), (self.x - 4, head_y + 8), 2)
        pygame.draw.line(screen, (100, 150, 255), (self.x + 4, head_y + 4), (self.x + 4, head_y + 8), 2)

class Boss:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.radius = 40
        self.max_hp = 5 if game_difficulty == "EASY" else 20
        self.hp = self.max_hp
        self.shield_active = False if game_difficulty == "EASY" else True
        self.last_shot = time.time()
        self.hit_flash = 0
        self.phase_time = time.time()

    def update(self, time_scale=1.0):
        t = time.time()
        self.x += math.sin(t) * 1.5 * time_scale
        
        # Shield toggles
        shield_interval = 8.0 if game_difficulty == "EASY" else 5.0
        if t - self.phase_time > shield_interval:
            self.shield_active = not self.shield_active
            self.phase_time = t
            # In EASY mode, if shield just turned on, turn it off quickly
            if game_difficulty == "EASY" and self.shield_active:
                self.phase_time = t - 6.0 # Leaves it active for only 2 seconds
            
        # Boss shooting logic
        boss_shoot_delay = 3.0 if game_difficulty == "EASY" else 1.5
        if t - self.last_shot > boss_shoot_delay / max(0.1, time_scale):
            self.last_shot = t
            target_x = random.choice([random.randint(-200, 200), random.randint(WIDTH-200, WIDTH+200)]) if game_difficulty == "EASY" else random.randint(300, WIDTH-300)
            enemy_bullets.append(Bullet(self.x, self.y, target_x, HEIGHT-50, speed=12, color=NEON_RED, radius=8))
            create_particles(self.x, self.y, NEON_RED, 10)
            
        if self.hit_flash > 0: self.hit_flash -= 1

    def draw(self):
        t = time.time()
        color = (50, 20, 20)
        if self.hit_flash > 0: color = WHITE
        
        # Boss Body (larger)
        pygame.draw.rect(screen, color, (self.x - 30, self.y - 60, 60, 80), border_radius=8)
        pygame.draw.circle(screen, (200, 150, 130), (int(self.x), int(self.y - 75)), 18)
        pygame.draw.circle(screen, NEON_RED, (int(self.x - 6), int(self.y - 75)), 3)
        pygame.draw.circle(screen, NEON_RED, (int(self.x + 6), int(self.y - 75)), 3)
        
        # Boss Gun
        pygame.draw.rect(screen, (20, 20, 20), (self.x - 10, self.y - 20, 50, 15))
        
        # Boss Shield
        if self.shield_active:
            shield_radius = 60 + math.sin(t*5)*5
            draw_glow_circle(screen, (0, 150, 255), (int(self.x), int(self.y - 20)), int(shield_radius), 2)
            pygame.draw.circle(screen, (0, 200, 255), (int(self.x), int(self.y - 20)), int(shield_radius), 2)
            
        # Boss HP
        pygame.draw.rect(screen, (30, 0, 0), (WIDTH//2 - 200, 20, 400, 15))
        hp_ratio = self.hp / self.max_hp
        pygame.draw.rect(screen, NEON_RED, (WIDTH//2 - 200, 20, int(400 * hp_ratio), 15))
        boss_text = FONT_SUB.render("CRIMINAL LEADER", True, WHITE)
        screen.blit(boss_text, (WIDTH//2 - boss_text.get_width()//2, 40))

# ================== PARTICLES ==================
def create_particles(x, y, color=NEON_GREEN, count=20):
    for _ in range(count):
        angle = random.uniform(0, math.pi * 2)
        speed = random.uniform(2, 12)
        particles.append({
            'x': x, 'y': y,
            'vx': math.cos(angle) * speed,
            'vy': math.sin(angle) * speed,
            'life': random.randint(15, 35),
            'max_life': 35,
            'color': color,
            'size': random.randint(2, 6)
        })

def create_muzzle_flash(x, y):
    for _ in range(8):
        angle = random.uniform(-0.5, 0.5) - math.pi/2
        speed = random.uniform(5, 15)
        muzzle_flash.append({
            'x': x, 'y': y,
            'vx': math.cos(angle) * speed,
            'vy': math.sin(angle) * speed,
            'life': random.randint(3, 8),
            'color': NEON_YELLOW
        })

def add_kill_feed(text, color=NEON_GREEN):
    kill_feed.append({'text': text, 'color': color, 'time': time.time()})
    if len(kill_feed) > 5:
        kill_feed.pop(0)

def add_score_popup(x, y, points, color=NEON_GREEN):
    score_popups.append({'x': x, 'y': y, 'points': points, 'color': color, 'life': 40, 'vy': -2})

# ================== DRAWING FUNCTIONS ==================
# ================== JUNGLE ENVIRONMENT HELPERS ==================
def draw_jungle_tree(surface, x, h, shade=0):
    """Draw a jungle tree silhouette."""
    g = 12 + shade
    trunk_w = 8 + shade // 2
    pygame.draw.rect(surface, (20+shade, 12+shade, 8), (x-trunk_w//2, HEIGHT*0.55-h, trunk_w, h))
    for i in range(3):
        ly = int(HEIGHT*0.55 - h + i*h//3)
        lw = 30 + (2-i)*20 + shade*2
        pygame.draw.polygon(surface, (g+shade, 20+shade*2, g), [(x, ly-15), (x-lw, ly+25), (x+lw, ly+25)])

def draw_watchtower(surface, x, y):
    """Draw a wooden watchtower structure."""
    # Legs
    for lx in [x-30, x+30]:
        pygame.draw.line(surface, WOOD, (lx, y), (lx, y+120), 6)
        pygame.draw.line(surface, WOOD_DARK, (lx, y), (lx, y+120), 2)
    # Cross beams
    pygame.draw.line(surface, WOOD, (x-30, y+40), (x+30, y+80), 4)
    pygame.draw.line(surface, WOOD, (x+30, y+40), (x-30, y+80), 4)
    # Platform
    pygame.draw.rect(surface, WOOD, (x-45, y-5, 90, 10))
    pygame.draw.rect(surface, WOOD_DARK, (x-45, y-5, 90, 10), 2)
    # Railing
    pygame.draw.line(surface, WOOD, (x-45, y-5), (x-45, y-30), 4)
    pygame.draw.line(surface, WOOD, (x+45, y-5), (x+45, y-30), 4)
    pygame.draw.line(surface, WOOD, (x-45, y-30), (x+45, y-30), 3)
    # Roof
    pygame.draw.polygon(surface, (35, 25, 15), [(x-55, y-30), (x, y-55), (x+55, y-30)])

def draw_tent(surface, x, y, w=80, h=50):
    """Draw a military tent."""
    pygame.draw.polygon(surface, (35, 50, 30), [(x, y-h), (x-w//2, y), (x+w//2, y)])
    pygame.draw.polygon(surface, (30, 45, 25), [(x, y-h), (x-w//2, y), (x-w//4, y)])
    pygame.draw.line(surface, (25, 35, 20), (x, y-h), (x, y), 2)
    pygame.draw.line(surface, (40, 55, 35), (x-w//2, y), (x+w//2, y), 2)

def draw_crate(surface, x, y, size=30):
    """Draw a wooden crate with markings."""
    pygame.draw.rect(surface, (70, 55, 35), (x, y, size, size))
    pygame.draw.rect(surface, (50, 35, 20), (x, y, size, size), 2)
    pygame.draw.line(surface, (50, 35, 20), (x, y), (x+size, y+size), 1)
    pygame.draw.line(surface, (50, 35, 20), (x+size, y), (x, y+size), 1)

def draw_campfire(surface, x, y, t):
    """Draw animated campfire with glow."""
    # Glow on ground
    glow_r = int(80 + math.sin(t*4)*15)
    glow_surf = pygame.Surface((glow_r*4, glow_r*2), pygame.SRCALPHA)
    for r in range(glow_r, 0, -5):
        a = max(5, int(25 * r / glow_r))
        pygame.draw.ellipse(glow_surf, (255, 120, 20, a), (glow_r*2-r, glow_r-r//2, r*2, r))
    surface.blit(glow_surf, (x-glow_r*2, y-glow_r//2))
    # Logs
    pygame.draw.line(surface, (50, 30, 15), (x-18, y+5), (x+18, y+5), 5)
    pygame.draw.line(surface, (45, 25, 12), (x-15, y+8), (x+15, y), 4)
    # Flames
    for i in range(6):
        fx = x + math.sin(t*8 + i*1.5) * (8 + i*2)
        fy = y - 5 - i*4 - abs(math.sin(t*6+i))*8
        fs = max(2, 7 - i)
        fc = (255, max(0,200-i*30), max(0,50-i*15))
        pygame.draw.circle(surface, fc, (int(fx), int(fy)), fs)
    # Embers rising
    for i in range(4):
        ex = x + math.sin(t*3+i*2)*20
        ey = y - 30 - ((t*40+i*30)%80)
        ea = max(0, 200 - int(((t*40+i*30)%80)*2.5))
        if ea > 0:
            es = pygame.Surface((4,4), pygame.SRCALPHA)
            pygame.draw.circle(es, (255,180,50,ea), (2,2), 2)
            surface.blit(es, (int(ex), int(ey)))

def draw_fog_layer(surface, t, intensity=40):
    """Draw animated fog/mist overlay."""
    fog = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    for i in range(5):
        fx = int((t * 15 + i * 300) % (WIDTH + 400)) - 200
        fy = int(HEIGHT * 0.4 + math.sin(t*0.5+i)*40 + i*50)
        fw, fh = 350 + i*40, 60 + i*10
        for r in range(3):
            a = max(3, intensity // (r+1))
            pygame.draw.ellipse(fog, (180, 200, 180, a), (fx-r*20, fy-r*5, fw+r*40, fh+r*10))
    surface.blit(fog, (0, 0))

def draw_vignette(surface):
    """Draw dark vignette for cinematic feel."""
    vig = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    for i in range(80):
        a = int(i * 2.5)
        pygame.draw.rect(vig, (0,0,0,a), (0, 0, i, HEIGHT))
        pygame.draw.rect(vig, (0,0,0,a), (WIDTH-i, 0, i, HEIGHT))
        pygame.draw.rect(vig, (0,0,0,a), (0, 0, WIDTH, i//2))
        pygame.draw.rect(vig, (0,0,0,a), (0, HEIGHT-i//2, WIDTH, i//2))
    surface.blit(vig, (0,0))

def draw_fireflies(surface, t):
    """Draw ambient firefly particles."""
    for i in range(12):
        fx = int((200 + i*95 + math.sin(t*0.7+i*1.3)*60) % WIDTH)
        fy = int(250 + math.sin(t*1.1+i*0.9)*80 + i*20)
        brightness = int(120 + math.sin(t*3+i*2)*120)
        if brightness > 100:
            fs = pygame.Surface((8,8), pygame.SRCALPHA)
            pygame.draw.circle(fs, (150, 255, 80, min(255, brightness)), (4,4), 3)
            pygame.draw.circle(fs, (200, 255, 150, min(255, brightness//2)), (4,4), 5)
            surface.blit(fs, (fx-4, fy-4))

def draw_background():
    t = time.time()
    if current_level == 1:
        for y_pos in range(HEIGHT // 2):
            ratio = y_pos / (HEIGHT // 2)
            r = int(lerp(20, 60, ratio))
            g = int(lerp(40, 100, ratio))
            b = int(lerp(80, 160, ratio))
            pygame.draw.line(screen, (r, g, b), (0, y_pos), (WIDTH, y_pos))
        sun_x = int(WIDTH * 0.75 + math.sin(t * 0.2) * 20)
        draw_glow_circle(screen, (255, 200, 80), (sun_x, 80), 30, 4)
        pygame.draw.circle(screen, (255, 220, 100), (sun_x, 80), 25)
        pts = [(0, HEIGHT // 2)]
        for x in range(0, WIDTH + 50, 50):
            h = HEIGHT // 2 - 30 - abs(math.sin(x * 0.008 + 1) * 60)
            pts.append((x, int(h)))
        pts.append((WIDTH, HEIGHT // 2))
        pygame.draw.polygon(screen, (35, 55, 35), pts)
        pygame.draw.rect(screen, (50, 70, 40), (0, HEIGHT // 2, WIDTH, HEIGHT // 2))
    elif current_level == 2:
        screen.fill((10, 15, 25))
        for sx, sy, sz in background_stars:
            br = max(0, min(255, int(150 + math.sin(t * 2 + sx) * 100)))
            pygame.draw.circle(screen, (br, br, min(255, br+20)), (sx, sy), sz)
        pygame.draw.rect(screen, (25, 35, 25), (0, int(HEIGHT*0.55), WIDTH, int(HEIGHT*0.45)))
    else:
        # ===== LEVEL 3: CINEMATIC JUNGLE NIGHT =====
        # Sky gradient (dark blue-black)
        for y_pos in range(int(HEIGHT * 0.55)):
            ratio = y_pos / (HEIGHT * 0.55)
            r = int(lerp(2, 8, ratio))
            g = int(lerp(4, 15, ratio))
            b = int(lerp(12, 22, ratio))
            pygame.draw.line(screen, (r, g, b), (0, y_pos), (WIDTH, y_pos))

        # Stars
        for sx, sy, sz in background_stars:
            br = max(0, min(200, int(80 + math.sin(t*1.5+sx)*70)))
            pygame.draw.circle(screen, (br, br, min(255, br+30)), (sx, sy), sz)

        # Moon
        draw_glow_circle(screen, (140, 160, 180), (100, 60), 25, 3)
        pygame.draw.circle(screen, (180, 200, 220), (100, 60), 18)
        pygame.draw.circle(screen, (4, 8, 16), (108, 55), 14)  # crescent shadow

        # Far tree silhouettes
        for i, xp in enumerate(range(0, WIDTH+80, 70)):
            h = 100 + int(math.sin(i*0.7)*40 + math.sin(i*1.3)*20)
            draw_jungle_tree(screen, xp, h, shade=0)

        # Mid-distance trees (slightly lighter)
        for i, xp in enumerate(range(30, WIDTH+60, 120)):
            h = 80 + int(math.sin(i*1.1)*30)
            draw_jungle_tree(screen, xp, h, shade=5)

        # Ground
        ground_y = int(HEIGHT * 0.55)
        pygame.draw.rect(screen, (18, 25, 15), (0, ground_y, WIDTH, HEIGHT - ground_y))
        # Ground texture lines
        for x in range(0, WIDTH, 15):
            gy = ground_y + random.Random(x).randint(0, 3)
            pygame.draw.line(screen, (22, 30, 18), (x, gy), (x+10, gy), 1)

        # Puddle reflections
        for px in [350, 650, 900]:
            puddle = pygame.Surface((60, 12), pygame.SRCALPHA)
            pygame.draw.ellipse(puddle, (20, 30, 40, 80), (0, 0, 60, 12))
            screen.blit(puddle, (px, ground_y + 15))

        # --- Structures based on phase ---
        if level3_phase == 1:
            # Phase 1: Dark entry, flickering lights
            flicker = random.choice([15, 40, 80]) if random.random() > 0.92 else 10
            for x in range(100, WIDTH, 200):
                draw_glow_circle(screen, (flicker, flicker, flicker//2), (x, ground_y-30), 20, 1)

        elif level3_phase == 2:
            # Phase 2: Full jungle camp
            draw_watchtower(screen, 120, ground_y - 120)
            draw_tent(screen, 300, ground_y, 90, 55)
            draw_tent(screen, WIDTH-250, ground_y, 70, 45)
            draw_crate(screen, 450, ground_y - 30, 30)
            draw_crate(screen, 470, ground_y - 28, 25)
            draw_crate(screen, 800, ground_y - 32, 35)
            # Wooden platform right
            pygame.draw.rect(screen, WOOD, (WIDTH-180, ground_y-15, 120, 8))
            for sx in range(WIDTH-180, WIDTH-60, 30):
                pygame.draw.line(screen, WOOD_DARK, (sx, ground_y-15), (sx, ground_y+5), 4)
            draw_campfire(screen, WIDTH//2, ground_y - 5, t)

        elif level3_phase == 3:
            # Phase 3: Red emergency + all structures
            red_pulse = int(math.sin(t*3)*20 + 30)
            for lx in [150, WIDTH-150]:
                draw_glow_circle(screen, (255, 20, 20), (lx, ground_y-60), 40+red_pulse, 2)
            draw_watchtower(screen, 120, ground_y - 120)
            draw_tent(screen, 300, ground_y, 90, 55)
            draw_crate(screen, 450, ground_y - 30, 30)
            draw_crate(screen, 470, ground_y - 28, 25)
            draw_campfire(screen, WIDTH//2 - 100, ground_y - 5, t)
            # Spotlight on boss area
            spot = pygame.Surface((200, HEIGHT), pygame.SRCALPHA)
            pygame.draw.rect(spot, (255, 200, 100, 8), (0, 0, 200, HEIGHT))
            screen.blit(spot, (WIDTH//2 - 100, 0))

        # Fog overlay
        fog_intensity = 50 if level3_phase == 1 else 30 if level3_phase == 2 else 20
        draw_fog_layer(screen, t, fog_intensity)

        # Fireflies (phases 2 and 3)
        if level3_phase >= 2:
            draw_fireflies(screen, t)

        # Near foliage (foreground leaves at bottom corners)
        for side in [-1, 1]:
            bx = 0 if side == -1 else WIDTH - 80
            for i in range(5):
                lx = bx + i*15 + int(math.sin(t*1.5+i)*5)
                ly = HEIGHT - 30 + i*8
                pygame.draw.polygon(screen, (15, 35+i*3, 12), [(lx, ly), (lx+25, ly-30-i*5), (lx+50, ly)])

        # Vignette
        draw_vignette(screen)

def draw_gun():
    gx = WIDTH - 200
    gy = HEIGHT - 60
    pygame.draw.rect(screen, (50, 50, 55), (gx, gy, 160, 30), border_radius=4)
    pygame.draw.rect(screen, (70, 70, 75), (gx, gy, 160, 30), 2, border_radius=4)
    pygame.draw.rect(screen, (40, 40, 45), (gx + 140, gy + 5, 60, 20))
    pygame.draw.rect(screen, (60, 60, 65), (gx + 140, gy + 5, 60, 20), 2)
    pygame.draw.rect(screen, (60, 60, 70), (gx + 60, gy - 15, 50, 18), border_radius=3)
    pygame.draw.circle(screen, NEON_BLUE, (gx + 85, gy - 6), 6)
    draw_glow_circle(screen, NEON_BLUE, (gx + 85, gy - 6), 4, 2)
    if time.time() - last_shot < 0.08:
        for i in range(5):
            fx = gx + 200 + random.randint(0, 20)
            fy = gy + 15 + random.randint(-10, 10)
            size = random.randint(3, 8)
            pygame.draw.circle(screen, NEON_YELLOW, (fx, fy), size)
            draw_glow_circle(screen, NEON_YELLOW, (fx, fy), size, 2)

def draw_crosshair(time_scale=1.0):
    cx, cy = int(crosshair_x), int(crosshair_y)
    t = time.time()
    
    global hit_marker_time
    is_hit = (t - hit_marker_time < 0.15)
    color = NEON_RED if is_hit else ACCENT
    
    pulse = math.sin(t * 8) * 2
    rotate_angle = t * 2
    
    for i in range(4):
        angle = rotate_angle + i * (math.pi/2)
        start_x = cx + math.cos(angle) * (25 + pulse)
        start_y = cy + math.sin(angle) * (25 + pulse)
        end_x = cx + math.cos(angle + 0.5) * (25 + pulse)
        end_y = cy + math.sin(angle + 0.5) * (25 + pulse)
        pygame.draw.line(screen, color, (start_x, start_y), (end_x, end_y), 3)

    pygame.draw.circle(screen, color, (cx, cy), 8, 2)
    length = 20
    gap = 10
    pygame.draw.line(screen, color, (cx - length - gap, cy), (cx - gap, cy), 2)
    pygame.draw.line(screen, color, (cx + gap, cy), (cx + length + gap, cy), 2)
    pygame.draw.line(screen, WHITE, (cx, cy), (cx, cy), 4)

    if is_hit:
        size = 15
        pygame.draw.line(screen, WHITE, (cx - size, cy - size), (cx + size, cy + size), 3)
        pygame.draw.line(screen, WHITE, (cx + size, cy - size), (cx - size, cy + size), 3)

    if is_charging:
        charge_ratio = min(1.0, charge_level)
        angle_end = (math.pi * 2) * charge_ratio
        rect = (cx - 30, cy - 30, 60, 60)
        pygame.draw.arc(screen, NEON_YELLOW, rect, -math.pi/2, -math.pi/2 + angle_end, 4)

def lerp_color(c1, c2, t):
    return tuple(max(0, min(255, int(lerp(c1[i], c2[i], t)))) for i in range(3))

# ================== GAME LOGIC ==================
def shoot(charged=False):
    global shots_fired, hits, score, last_shot, combo, screen_shake, hit_marker_time, game_state, boss
    if time.time() - last_shot < 0.08:
        return
    last_shot = time.time()
    shots_fired += 1
    create_muzzle_flash(WIDTH - 40, HEIGHT - 45)
    screen_shake = 8 if charged else 2

    hit_radius = 25 if charged else 8
    hit = False

    # Check Hostage (Girlfriend) Hit First!
    if girlfriend:
        if math.dist((girlfriend.x, girlfriend.y - 20), (crosshair_x, crosshair_y)) < (girlfriend.radius + hit_radius):
            girlfriend.hit_flash = 10
            create_particles(girlfriend.x, girlfriend.y, NEON_RED, 50)
            game_state = "lose_hostage"
            return # End immediately

    # Check Targets
    for i, t in enumerate(targets):
        if math.dist((t.x, t.y - 20), (crosshair_x, crosshair_y)) < (t.radius + hit_radius):
            t.hp -= 1
            if t.hp <= 0:
                create_particles(t.x, t.y - 20, NEON_RED, 25)
                points = 250 if charged else 100
                combo += 1
                if combo > 1: points = int(points * (1 + combo * 0.2))
                add_score_popup(t.x, t.y - 40, points)
                add_kill_feed(f"Target eliminated +{points}", NEON_GREEN)
                targets.pop(i)
                hits += 1
                score += points
                hit = True
            break

    # Check Enemies
    if not hit:
        for i, e in enumerate(enemies):
            if math.dist((e.x, e.y - 20), (crosshair_x, crosshair_y)) < (e.radius + hit_radius):
                e.hp -= 1
                e.hit_flash = 5
                if e.hp <= 0:
                    create_particles(e.x, e.y - 20, (255, 100, 100), 30)
                    points = 350 if e.type == "sniper" else 200 if charged else 120
                    combo += 1
                    if combo > 1: points = int(points * (1 + combo * 0.25))
                    add_score_popup(e.x, e.y - 40, points)
                    add_kill_feed(f"{e.type.upper()} eliminated +{points}", NEON_RED)
                    enemies.pop(i)
                    hits += 1
                    score += points
                    hit = True
                break

    # Check Boss
    if boss and not hit:
        if math.dist((boss.x, boss.y - 30), (crosshair_x, crosshair_y)) < (boss.radius + hit_radius):
            if boss.shield_active and not charged:
                add_kill_feed("SHIELD BLOCKED SHOT!", NEON_BLUE)
            else:
                boss.hp -= 3 if charged else 1
                boss.hit_flash = 5
                hit = True
                hit_marker_time = time.time()
                create_particles(boss.x, boss.y, WHITE, 20)
                if boss.hp <= 0:
                    boss = None
                    hit = True
                    game_state = "win_boss"
                    return

    # Warning for missing near hostage
    if not hit and girlfriend:
        if math.dist((girlfriend.x, girlfriend.y - 20), (crosshair_x, crosshair_y)) < 150:
            add_kill_feed("WARNING: TOO CLOSE TO HOSTAGE!", NEON_YELLOW)

    if not hit:
        combo = 0
        score = max(0, score - 15)

def draw_hud():
    t = time.time()
    # === TOP BAR ===
    hud_surf = pygame.Surface((WIDTH, 75), pygame.SRCALPHA)
    pygame.draw.rect(hud_surf, (5, 12, 20, 230), (0, 0, WIDTH, 75))
    pygame.draw.line(hud_surf, ACCENT + (120,), (0, 74), (WIDTH, 74), 2)
    screen.blit(hud_surf, (0, 0))

    # Level info
    level_names = {1: "TRAINING RANGE", 2: "ENEMY CAMP", 3: "RESCUE MISSION"}
    l_label = FONT_TINY.render(f"LEVEL {current_level}", True, GRAY)
    l_name = FONT_SUB.render(level_names.get(current_level, "MISSION"), True, NEON_GREEN if current_level < 3 else NEON_RED)
    l_sub = FONT_TINY.render("Save your girlfriend and eliminate all enemies" if current_level == 3 else "", True, GRAY)
    screen.blit(l_label, (20, 8))
    screen.blit(l_name, (20, 22))
    screen.blit(l_sub, (20, 52))

    # Stats
    remaining = len(targets) + len(enemies) + (1 if boss else 0)
    stats = [
        ("TARGETS", f"{remaining}", 300, WHITE if remaining > 0 else NEON_GREEN),
        ("SCORE", f"{score:,}", 430, NEON_YELLOW),
        ("ACCURACY", f"{int((hits / max(1, shots_fired)) * 100)}%", 580,
         NEON_GREEN if hits / max(1, shots_fired) >= 0.7 else NEON_RED if hits / max(1, shots_fired) < 0.4 else NEON_YELLOW),
    ]
    for label, val, sx, col in stats:
        screen.blit(FONT_TINY.render(label, True, GRAY), (sx, 10))
        screen.blit(FONT_HUD.render(val, True, col), (sx, 26))

    # Health hearts
    screen.blit(FONT_TINY.render("HEALTH", True, GRAY), (780, 10))
    for i in range(max_health):
        hx = 780 + i * 32
        hy = 28
        if i < health:
            pygame.draw.rect(screen, NEON_RED, (hx, hy, 26, 26), border_radius=4)
            pygame.draw.rect(screen, (255, 100, 100), (hx, hy, 26, 26), 2, border_radius=4)
            pygame.draw.circle(screen, (255, 150, 150), (hx + 8, hy + 10), 5)
            pygame.draw.circle(screen, (255, 150, 150), (hx + 18, hy + 10), 5)
            pygame.draw.polygon(screen, (255, 150, 150), [(hx + 3, hy + 12), (hx + 13, hy + 24), (hx + 23, hy + 12)])
        else:
            pygame.draw.rect(screen, (40, 20, 20), (hx, hy, 26, 26), border_radius=4)
            pygame.draw.rect(screen, (60, 30, 30), (hx, hy, 26, 26), 1, border_radius=4)

    # Combo
    if combo > 1:
        c_text = FONT_MED.render(f"x{combo} COMBO", True, NEON_PURPLE)
        screen.blit(c_text, (780, 58))

    # Speed control
    speed_surf = FONT_TINY.render(f"SPEED: {int(global_time_scale * 100)}%  [UP/DOWN]", True, NEON_YELLOW)
    screen.blit(speed_surf, (WIDTH - 180, 58))

    # === HOSTAGE WARNING BANNER (Level 3 Phase 3) ===
    if current_level == 3 and level3_phase == 3:
        pulse = int(math.sin(t * 5) * 50 + 200)
        # Warning box
        warn_w, warn_h = 380, 55
        warn_x = WIDTH // 2 - warn_w // 2
        warn_y = 85
        warn_surf = pygame.Surface((warn_w, warn_h), pygame.SRCALPHA)
        pygame.draw.rect(warn_surf, (80, 10, 10, 200), (0, 0, warn_w, warn_h), border_radius=8)
        pygame.draw.rect(warn_surf, (255, pulse // 2, pulse // 3, 200), (0, 0, warn_w, warn_h), 2, border_radius=8)
        screen.blit(warn_surf, (warn_x, warn_y))
        warn_title = FONT_MED.render("⚠ HOSTAGE IN DANGER", True, (255, pulse, pulse))
        warn_sub = FONT_TINY.render("Be careful! Wrong shot can kill her.", True, (200, 150, 150))
        screen.blit(warn_title, (WIDTH // 2 - warn_title.get_width() // 2, warn_y + 8))
        screen.blit(warn_sub, (WIDTH // 2 - warn_sub.get_width() // 2, warn_y + 32))
        # Heartbeat
        hb_y = warn_y + warn_h + 10
        hb_x = WIDTH // 2 - 50
        pts = [(hb_x, hb_y), (hb_x+20, hb_y), (hb_x+30, hb_y-15), (hb_x+40, hb_y+20),
               (hb_x+50, hb_y), (hb_x+100, hb_y)]
        for i in range(len(pts)-1):
            pygame.draw.line(screen, NEON_RED, pts[i], pts[i+1], 2)

    # === DIFFICULTY DISPLAY (top right under top bar) ===
    diff_text = f"{game_difficulty} MODE"
    diff_color = NEON_GREEN if game_difficulty == "EASY" else NEON_YELLOW
    diff_surf = FONT_SMALL.render(diff_text, True, diff_color)
    screen.blit(diff_surf, (WIDTH - diff_surf.get_width() - 20, 85))

    # === OBJECTIVE PANEL (right side) ===
    if current_level == 3:
        obj_w, obj_h = 180, 70
        obj_x = WIDTH - obj_w - 15
        obj_y = 85
        obj_surf = pygame.Surface((obj_w, obj_h), pygame.SRCALPHA)
        pygame.draw.rect(obj_surf, (10, 20, 15, 200), (0, 0, obj_w, obj_h), border_radius=6)
        pygame.draw.rect(obj_surf, NEON_GREEN + (100,), (0, 0, obj_w, obj_h), 1, border_radius=6)
        screen.blit(obj_surf, (obj_x, obj_y))
        screen.blit(FONT_SMALL.render("OBJECTIVE", True, NEON_GREEN), (obj_x + 10, obj_y + 8))
        phase_obj = {1: "Clear the entry zone", 2: "Eliminate all enemies", 3: "Defeat the boss and\nsave your girlfriend"}
        obj_text = phase_obj.get(level3_phase, "")
        for i, line in enumerate(obj_text.split("\n")):
            screen.blit(FONT_TINY.render(line, True, WHITE), (obj_x + 10, obj_y + 28 + i * 14))

    # === CONTROLS PANEL (left side, lower) ===
    if current_level == 3:
        ctrl_w, ctrl_h = 165, 80
        ctrl_x = 15
        ctrl_y = HEIGHT - ctrl_h - 80
        ctrl_surf = pygame.Surface((ctrl_w, ctrl_h), pygame.SRCALPHA)
        pygame.draw.rect(ctrl_surf, (20, 10, 10, 180), (0, 0, ctrl_w, ctrl_h), border_radius=6)
        pygame.draw.rect(ctrl_surf, NEON_RED + (80,), (0, 0, ctrl_w, ctrl_h), 1, border_radius=6)
        screen.blit(ctrl_surf, (ctrl_x, ctrl_y))
        screen.blit(FONT_SMALL.render("CONTROLS", True, NEON_RED), (ctrl_x + 10, ctrl_y + 6))
        ctrls = ["Move Mouse - Aim", "Click - Shoot", "Hold SPACE - Charged Shot"]
        for i, c in enumerate(ctrls):
            screen.blit(FONT_TINY.render(c, True, WHITE), (ctrl_x + 10, ctrl_y + 25 + i * 16))

    # === KILL FEED ===
    kf_x = WIDTH - 280
    kf_y = 300 if current_level != 3 else 170
    for i, kf in enumerate(kill_feed):
        age = t - kf['time']
        if age < 4:
            kf_surf = FONT_SMALL.render(kf['text'], True, kf['color'])
            screen.blit(kf_surf, (kf_x, kf_y + i * 22))

    # === SCORE POPUPS ===
    for sp in score_popups:
        if sp['life'] > 0:
            sp_surf = FONT_MED.render(f"+{sp['points']}", True, sp['color'])
            screen.blit(sp_surf, (int(sp['x']), int(sp['y'])))

    # === CHARGE SHOT BAR (bottom center) ===
    bar_w = 280
    bar_h = 14
    bar_x = WIDTH // 2 - bar_w // 2
    bar_y = HEIGHT - 55
    charge_ratio = min(1.0, charge_level) if is_charging else 0
    # Background
    pygame.draw.rect(screen, (20, 20, 20), (bar_x - 2, bar_y - 2, bar_w + 4, bar_h + 4), border_radius=6)
    pygame.draw.rect(screen, (35, 35, 35), (bar_x, bar_y, bar_w, bar_h), border_radius=4)
    # Gradient segments
    seg_count = 20
    seg_w = bar_w // seg_count
    filled = int(charge_ratio * seg_count)
    for i in range(filled):
        ratio = i / seg_count
        seg_color = lerp_color(NEON_GREEN, NEON_RED, ratio)
        pygame.draw.rect(screen, seg_color, (bar_x + i * seg_w + 1, bar_y + 1, seg_w - 2, bar_h - 2), border_radius=2)
    # Label
    if is_charging:
        label_text = "CHARGED!" if charge_ratio >= 0.7 else "CHARGE SHOT"
        label_col = NEON_YELLOW if charge_ratio >= 0.7 else GRAY
    else:
        label_text = "CHARGE SHOT"
        label_col = GRAY
    # Crosshair icon
    pygame.draw.circle(screen, GRAY, (bar_x - 20, bar_y + bar_h // 2), 8, 1)
    pygame.draw.circle(screen, GRAY, (bar_x - 20, bar_y + bar_h // 2), 2)
    label_surf = FONT_TINY.render(label_text, True, label_col)
    screen.blit(label_surf, (bar_x, bar_y - 16))
    pct_surf = FONT_TINY.render(f"{int(charge_ratio * 100)}%", True, label_col)
    screen.blit(pct_surf, (bar_x + bar_w + 8, bar_y))
    # Hint
    hint = FONT_TINY.render("BLINK TO SHOOT | Hold Blink for Charged Shot", True, NEON_YELLOW)
    screen.blit(hint, (WIDTH // 2 - hint.get_width() // 2, bar_y + bar_h + 4))

    # === EYE TRACKING STATUS (bottom right) ===
    et_x = WIDTH - 200
    et_y = HEIGHT - 55
    et_surf = pygame.Surface((170, 40), pygame.SRCALPHA)
    pygame.draw.rect(et_surf, (10, 15, 20, 200), (0, 0, 170, 40), border_radius=6)
    pygame.draw.rect(et_surf, NEON_GREEN if eye_tracking_enabled else (100, 100, 100, 60), (0, 0, 170, 40), 2 if eye_tracking_enabled else 1, border_radius=6)
    
    if eye_tracking_enabled:
        pygame.draw.rect(et_surf, NEON_GREEN + (40,), (0, 0, 170, 40), border_radius=6) # Glowing border effect

    screen.blit(et_surf, (et_x, et_y))
    
    if eye_tracking_enabled:
        et_label = FONT_SMALL.render("EYE TRACKING: ON", True, NEON_GREEN)
        dot_col = NEON_GREEN
    else:
        et_label = FONT_SMALL.render("MOUSE MODE", True, WHITE)
        dot_col = NEON_RED
        
    screen.blit(et_label, (et_x + 10, et_y + 10))
    pygame.draw.circle(screen, dot_col, (et_x + 150, et_y + 20), 5)

    # === CAMERA FEED ===
    if eye_tracking_enabled and cam_frame is not None:
        try:
            h, w = cam_frame.shape[:2]
            cam_w, cam_h = 160, 120
            frame_str = cam_frame.tobytes()
            surface = pygame.image.frombuffer(frame_str, (w, h), "RGB")
            surface = pygame.transform.scale(surface, (cam_w, cam_h))
            cam_x = WIDTH - cam_w - 15
            cam_y = HEIGHT - cam_h - 100
            if face_box is not None:
                fx, fy, fw, fh = face_box
                sx = int(fx * cam_w / w)
                sy = int(fy * cam_h / h)
                sw = int(fw * cam_w / w)
                sh = int(fh * cam_h / h)
                pygame.draw.rect(surface, NEON_GREEN, (sx, sy, sw, sh), 2)
            pygame.draw.rect(screen, NEON_GREEN, (cam_x - 2, cam_y - 2, cam_w + 4, cam_h + 4), 2, border_radius=4)
            screen.blit(surface, (cam_x, cam_y))
            
            # Blink Status Text over camera
            if is_charging:
                b_text = "CHARGING!" if charge_level < 0.75 else "CHARGED (BLINKING)"
                b_color = NEON_YELLOW if charge_level < 0.75 else NEON_RED
            else:
                b_text = "NEUTRAL"
                b_color = NEON_GREEN
            
            bg_rect = pygame.Rect(cam_x, cam_y + cam_h - 22, cam_w, 22)
            pygame.draw.rect(screen, (0, 0, 0, 150), bg_rect)
            b_surf = FONT_TINY.render(b_text, True, b_color)
            screen.blit(b_surf, (cam_x + cam_w//2 - b_surf.get_width()//2, cam_y + cam_h - 18))
        except Exception:
            pass

def update_particles(time_scale=1.0):
    for p in particles[:]:
        p['x'] += p['vx'] * time_scale
        p['y'] += p['vy'] * time_scale
        p['vx'] *= 0.92
        p['vy'] *= 0.92
        p['vy'] += 0.15 * time_scale
        p['life'] -= 1 * time_scale
        if p['life'] <= 0:
            particles.remove(p)
        else:
            ratio = p['life'] / p['max_life']
            s = max(1, int(p['size'] * ratio))
            color = tuple(min(255, int(c * ratio)) for c in p['color'])
            pygame.draw.circle(screen, color, (int(p['x']), int(p['y'])), s)

    for mf in muzzle_flash[:]:
        mf['x'] += mf['vx'] * time_scale
        mf['y'] += mf['vy'] * time_scale
        mf['life'] -= 1 * time_scale
        if mf['life'] <= 0:
            muzzle_flash.remove(mf)
        else:
            s = max(1, int(mf['life']))
            pygame.draw.circle(screen, mf['color'], (int(mf['x']), int(mf['y'])), s)

    for sp in score_popups[:]:
        sp['y'] += sp['vy'] * time_scale
        sp['life'] -= 1 * time_scale
        if sp['life'] <= 0:
            score_popups.remove(sp)

def spawn_level(level, phase=1):
    global targets, enemies, boss, girlfriend, health, story_text, max_health, shots_fired, hits, level3_phase
    targets.clear()
    enemies.clear()
    enemy_bullets.clear()
    boss = None
    girlfriend = None
    level3_phase = phase
    
    if phase == 1 and level != 3: # Reset health only on level start
        max_health = 10 if game_difficulty == "EASY" else 3
        health = max_health
        shots_fired = 0
        hits = 0

    if level == 1:
        for i in range(5):
            targets.append(Target(random.randint(200, WIDTH-200), random.randint(180, 480), i > 3))
        story_text = "Training complete! Enemy camp ahead..."
    elif level == 2:
        for i in range(5):
            enemies.append(Enemy(random.randint(150, WIDTH-150), random.randint(100, 300), random.choice(["guard", "sniper"])))
        story_text = "Camp cleared! Final mission: rescue hostage!"
    elif level == 3:
        if phase == 1: # Entry Zone
            show_dialogue("Phase 1: Entry Zone", "Something is wrong...", NEON_BLUE)
            for i in range(3):
                enemies.append(Enemy(random.randint(100, WIDTH-100), random.randint(200, 400), "guard"))
        elif phase == 2: # Combat Hall
            show_dialogue("Phase 2: Combat Hall", "It's an ambush! Take cover!", ORANGE)
            for i in range(5):
                enemies.append(Enemy(random.randint(50, WIDTH-50), random.randint(100, 350), random.choice(["assault", "guard", "sniper"])))
        elif phase == 3: # Final Room
            show_dialogue("Phase 3: The Hostage", "Boss: One wrong move... she dies.", NEON_RED)
            boss = Boss(WIDTH//2, 180)
            girlfriend = Girlfriend(WIDTH//2, 250)
            for i in range(4):
                enemies.append(Enemy(random.randint(100, WIDTH-100), random.randint(100, 300), "heavy"))

def show_dialogue(title_text, sub_text, color=WHITE):
    start = time.time()
    while time.time() - start < 3.0:
        screen.fill(DARK_BG)
        title = FONT_TITLE.render(title_text, True, color)
        sub = FONT_SUB.render(sub_text, True, GRAY)
        screen.blit(title, (WIDTH // 2 - title.get_width() // 2, HEIGHT // 2 - 40))
        screen.blit(sub, (WIDTH // 2 - sub.get_width() // 2, HEIGHT // 2 + 20))
        pygame.display.flip()
        clock.tick(60)

def show_story():
    global current_level
    start = time.time()
    next_level = current_level + 1
    cx = WIDTH // 2
    while True:
        t = time.time() - start
        screen.fill((12, 18, 28))
        for i in range(8):
            y = int(100 + i * 80 + math.sin(t * 2 + i) * 5)
            alpha = int(20 + 10 * math.sin(t + i))
            s = pygame.Surface((WIDTH, 1), pygame.SRCALPHA)
            s.fill((*NEON_GREEN, alpha))
            screen.blit(s, (0, y))
        t_title = FONT_TITLE.render(f"LEVEL {next_level} UNLOCKED", True, NEON_GREEN)
        screen.blit(t_title, (cx - t_title.get_width()//2, 140))
        if next_level == 2:
            l_name = "Enemy Camp — Dusk"
            l_obj = "Watch out for snipers!"
        elif next_level == 3:
            l_name = "Rescue Mission — Night"
            l_obj = "She's in there. One shot. Make it count."
        else:
            l_name = "Next Level"
            l_obj = "Get ready."
        t_sub = FONT_TITLE.render(l_name, True, WHITE)
        screen.blit(t_sub, (cx - t_sub.get_width()//2, 250))
        t_obj = FONT_SUB.render(l_obj, True, GRAY)
        screen.blit(t_obj, (cx - t_obj.get_width()//2, 330))
        pygame.draw.line(screen, (0, 200, 120), (cx-250, 400), (cx+250, 400), 2)
        acc = int((hits / max(1, shots_fired)) * 100) if shots_fired > 0 else 0
        t_stat = FONT_SUB.render(f"Score: {score:,}   Accuracy: {acc}%", True, GRAY)
        screen.blit(t_stat, (cx - t_stat.get_width()//2, 450))
        go_btn = pygame.Rect(cx - 150, 550, 300, 60)
        go_hv = go_btn.collidepoint(pygame.mouse.get_pos())
        draw_button(go_btn, f"GO TO LEVEL {next_level}", ACCENT, go_hv)
        for event in pygame.event.get():
            if event.type == pygame.QUIT: cleanup()
            if event.type == pygame.MOUSEBUTTONDOWN and go_btn.collidepoint(event.pos): return
            if event.type == pygame.KEYDOWN and event.key in [pygame.K_RETURN, pygame.K_SPACE]: return
        pygame.display.flip()
        clock.tick(60)

def show_cinematic_ending():
    global score
    start = time.time()
    # Explosion flash
    for i in range(10):
        screen.fill(WHITE)
        pygame.display.flip()
        clock.tick(20)
    
    # Cinematic text
    dialogue = [
        ("Girlfriend: You came for me...", 2.0),
        ("Hero: I never stopped.", 4.0),
    ]
    
    for text, delay in dialogue:
        d_start = time.time()
        while time.time() - d_start < delay:
            screen.fill((5, 5, 5))
            txt_surf = FONT_TITLE.render(text, True, WHITE)
            screen.blit(txt_surf, (WIDTH // 2 - txt_surf.get_width() // 2, HEIGHT // 2))
            pygame.display.flip()
            clock.tick(60)
            
    show_final_win()

def show_final_win():
    global score
    start = time.time()
    while True:
        t = time.time() - start
        screen.fill(DARK_BG)
        if int(t * 10) % 3 == 0:
            create_particles(random.randint(100, WIDTH-100), random.randint(100, 300), random.choice([NEON_GREEN, NEON_YELLOW, NEON_PURPLE]), 5)
        update_particles()
        glow = int(math.sin(t * 3) * 30 + 225)
        title = FONT_TITLE.render("MISSION COMPLETE!", True, (0, glow, 150))
        screen.blit(title, (WIDTH // 2 - title.get_width() // 2, 140))
        sub = FONT_SUB.render("The hostage has been rescued!", True, WHITE)
        screen.blit(sub, (WIDTH // 2 - sub.get_width() // 2, 220))
        acc = int(hits / max(1, shots_fired) * 100) if shots_fired > 0 else 0
        rank = "S" if acc >= 80 else "A" if acc >= 60 else "B"
        stats = [
            f"Final Score: {score:,}",
            f"Accuracy: {acc}%",
            f"Rank: {rank}",
            f"Max Combo: x{max_combo}"
        ]
        for i, s in enumerate(stats):
            st = FONT_MED.render(s, True, ACCENT)
            screen.blit(st, (WIDTH // 2 - st.get_width() // 2, 300 + i * 35))
        btn = pygame.Rect(WIDTH // 2 - 130, 480, 260, 55)
        btn_hover = btn.collidepoint(pygame.mouse.get_pos())
        pygame.draw.rect(screen, (15, 40, 30) if not btn_hover else (20, 60, 40), btn, border_radius=8)
        pygame.draw.rect(screen, ACCENT, btn, 3, border_radius=8)
        btn_text = FONT_MED.render("PLAY AGAIN", True, ACCENT)
        screen.blit(btn_text, (btn.centerx - btn_text.get_width() // 2, btn.centery - btn_text.get_height() // 2))
        for event in pygame.event.get():
            if event.type == pygame.QUIT: cleanup()
            if event.type == pygame.MOUSEBUTTONDOWN and btn.collidepoint(event.pos): restart_game()
        pygame.display.flip()
        clock.tick(60)

def show_lose(reason="killed"):
    start = time.time()
    while True:
        t = time.time() - start
        screen.fill((20, 8, 8))
        pulse = int(math.sin(t * 4) * 20 + 30)
        pygame.draw.rect(screen, (pulse, 0, 0), (0, 0, WIDTH, HEIGHT))
        title = FONT_TITLE.render("MISSION FAILED", True, NEON_RED)
        screen.blit(title, (WIDTH // 2 - title.get_width() // 2, 180))
        if reason == "hostage":
            sub = FONT_SUB.render("YOU SHOT THE HOSTAGE...", True, (255, 100, 100))
        else:
            sub = FONT_SUB.render("The hostage is still in danger...", True, (200, 150, 150))
        screen.blit(sub, (WIDTH // 2 - sub.get_width() // 2, 260))
        acc = int(hits / max(1, shots_fired) * 100) if shots_fired > 0 else 0
        st = FONT_MED.render(f"Score: {score:,}  |  Accuracy: {acc}%", True, GRAY)
        screen.blit(st, (WIDTH // 2 - st.get_width() // 2, 330))
        btn = pygame.Rect(WIDTH // 2 - 130, 420, 260, 55)
        btn_hover = btn.collidepoint(pygame.mouse.get_pos())
        pygame.draw.rect(screen, (50, 15, 15) if not btn_hover else (70, 20, 20), btn, border_radius=8)
        pygame.draw.rect(screen, NEON_RED, btn, 3, border_radius=8)
        btn_text = FONT_MED.render("TRY AGAIN", True, NEON_RED)
        screen.blit(btn_text, (btn.centerx - btn_text.get_width() // 2, btn.centery - btn_text.get_height() // 2))
        for event in pygame.event.get():
            if event.type == pygame.QUIT: cleanup()
            if event.type == pygame.MOUSEBUTTONDOWN and btn.collidepoint(event.pos): restart_game()
        pygame.display.flip()
        clock.tick(60)

def cleanup():
    if cap: cap.release()
    pygame.quit()
    sys.exit()

def restart_game():
    global score, shots_fired, hits, current_level, health, combo, max_combo, game_state, max_health
    score = 0
    shots_fired = 0
    hits = 0
    current_level = 1
    max_health = 10 if game_difficulty == "EASY" else 3
    health = max_health
    combo = 0
    max_combo = 0
    game_state = "playing"
    game_loop()

def game_loop():
    global current_level, score, shots_fired, hits, health, is_charging, blink_start, last_shot, game_state
    global crosshair_x, crosshair_y, eye_tracking_enabled, charge_level, combo, max_combo, screen_shake
    global damage_overlay, enemy_bullets, level3_phase, screen, global_time_scale
    running = True
    spawn_level(current_level)
    game_state = "playing"
    damage_surf = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)

    while running:
        # Time Dilation logic for Boss final shot
        time_scale = global_time_scale
        if current_level == 3 and level3_phase == 3 and is_charging:
            time_scale = max(0.1, global_time_scale - charge_level) # Slow down time up to 90%
            
        t = time.time()
        shake_x = random.randint(-screen_shake, screen_shake) if screen_shake > 0 else 0
        shake_y = random.randint(-screen_shake, screen_shake) if screen_shake > 0 else 0
        if screen_shake > 0: screen_shake -= 1

        screen.fill(DARK_BG)

        for event in pygame.event.get():
            if event.type == pygame.QUIT: cleanup()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    global_time_scale = min(2.0, global_time_scale + 0.1)
                if event.key == pygame.K_DOWN:
                    global_time_scale = max(0.2, global_time_scale - 0.1)
                if event.key == pygame.K_e and eye_tracking_available:
                    eye_tracking_enabled = not eye_tracking_enabled
                if event.key == pygame.K_ESCAPE:
                    paused = True
                    while paused:
                        screen.fill((0, 0, 0))
                        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
                        overlay.fill((0, 0, 0, 180))
                        screen.blit(overlay, (0, 0))
                        pause_text = FONT_TITLE.render("PAUSED", True, WHITE)
                        screen.blit(pause_text, (WIDTH // 2 - pause_text.get_width() // 2, 200))
                        resume_btn = pygame.Rect(WIDTH//2 - 140, 340, 280, 50)
                        resume_hv = resume_btn.collidepoint(pygame.mouse.get_pos())
                        draw_button(resume_btn, "RESUME [ESC]", NEON_GREEN, resume_hv)
                        exit_btn = pygame.Rect(WIDTH//2 - 140, 420, 280, 50)
                        exit_hv = exit_btn.collidepoint(pygame.mouse.get_pos())
                        draw_button(exit_btn, "EXIT TO MENU", NEON_RED, exit_hv)
                        pygame.display.flip()
                        for pe in pygame.event.get():
                            if pe.type == pygame.QUIT: cleanup()
                            if pe.type == pygame.KEYDOWN:
                                if pe.key == pygame.K_ESCAPE: paused = False
                                if pe.key == pygame.K_q: cleanup()
                            if pe.type == pygame.MOUSEBUTTONDOWN:
                                if resume_btn.collidepoint(pe.pos): paused = False
                                if exit_btn.collidepoint(pe.pos): return
                        clock.tick(30)
                if event.key == pygame.K_SPACE and not eye_tracking_enabled:
                    blink_start = time.time()
                    is_charging = True
                    charge_level = 0
            if event.type == pygame.KEYUP and event.key == pygame.K_SPACE and is_charging:
                is_charging = False
                shoot(charged=charge_level >= 0.7)
                charge_level = 0
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if not eye_tracking_enabled: shoot(charged=False)
            if event.type == pygame.MOUSEMOTION and not eye_tracking_enabled:
                crosshair_x, crosshair_y = event.pos

        if is_charging:
            charge_level = min(1.0, (time.time() - blink_start) / 1.0)

        process_eye_tracking()
        
        # Apply zoom effect during time dilation
        if time_scale < 1.0:
            zoom_surf = pygame.Surface((WIDTH, HEIGHT))
            # Redirect drawing to zoom_surf temporarily
            original_screen = screen
            screen = zoom_surf
        else:
            zoom_surf = None

        draw_background()

        for t_obj in targets[:]:
            t_obj.update(time_scale)
            t_obj.draw()

        for e in enemies[:]:
            e.update(time_scale)
            e.draw()
            if e.y > HEIGHT - 65:
                health -= 1
                damage_overlay = 30
                screen_shake = 10
                enemies.remove(e)
                
        if boss:
            boss.update(time_scale)
            boss.draw()
        if girlfriend:
            girlfriend.update(time_scale)
            girlfriend.draw()

        for b in enemy_bullets[:]:
            b.update(time_scale)
            b.draw()
            if b.y > HEIGHT - 100:
                if abs(b.x - WIDTH//2) < 400:
                    damage = 1
                    health -= damage
                    damage_overlay = 20 if damage == 1 else 40
                    screen_shake = 8
                    enemy_bullets.remove(b)
                elif b.y > HEIGHT:
                    enemy_bullets.remove(b)
            if not b.alive and b in enemy_bullets:
                enemy_bullets.remove(b)

        update_particles(time_scale)
        draw_gun()
        draw_crosshair(time_scale)
        
        # Restore screen if zoomed
        if zoom_surf:
            screen = original_screen
            zoom_factor = 1.0 + (1.0 - time_scale) * 0.1 # Max 10% zoom
            zw, zh = int(WIDTH * zoom_factor), int(HEIGHT * zoom_factor)
            scaled_zoom = pygame.transform.scale(zoom_surf, (zw, zh))
            screen.blit(scaled_zoom, (WIDTH//2 - zw//2, HEIGHT//2 - zh//2))

        draw_hud()

        if damage_overlay > 0:
            damage_surf.fill((255, 0, 0, min(150, damage_overlay * 5)))
            screen.blit(damage_surf, (0, 0))
            damage_overlay -= 1

        if current_level == 1:
            shots_left = max_shots_level1 - shots_fired
            shots_info = FONT_HUD_SM.render(f"SHOTS LEFT: {shots_left}/{max_shots_level1}  |  HITS NEEDED: {max(0, required_hits_level1 - hits)}", True, NEON_YELLOW if shots_left > 3 else NEON_RED)
            screen.blit(shots_info, (WIDTH//2 - shots_info.get_width()//2, 75))
            if shots_fired >= max_shots_level1 and hits < required_hits_level1: game_state = "lose"
            if hits >= required_hits_level1:
                show_story()
                current_level += 1
                spawn_level(current_level)
        else:
            if len(targets) + len(enemies) == 0 and not boss:
                if current_level == 3 and level3_phase < 3:
                    level3_phase += 1
                    spawn_level(3, level3_phase)
                elif current_level == 3 and level3_phase == 3:
                    # All enemies and boss defeated in final phase
                    game_state = "win_boss"
                elif current_level < 3:
                    show_story()
                    current_level += 1
                    spawn_level(current_level)
        
        if health <= 0: game_state = "lose"

        if game_state == "win_boss": show_cinematic_ending(); running = False
        elif game_state == "win": show_final_win(); running = False
        elif game_state == "lose": show_lose(); running = False
        elif game_state == "lose_hostage": show_lose(reason="hostage"); running = False

        if screen_shake > 0:
            final_surf = screen.copy()
            screen.fill((0,0,0))
            screen.blit(final_surf, (shake_x, shake_y))

        pygame.display.flip()
        clock.tick(60)
    cleanup()

def draw_button(rect, text, color, hover=False):
    # Solid filled button with dark text for readability
    if hover:
        fill = tuple(min(255, c + 40) for c in color)
        # Glow effect on hover
        glow_surf = pygame.Surface((rect.width + 16, rect.height + 16), pygame.SRCALPHA)
        pygame.draw.rect(glow_surf, (*color, 60), (0, 0, rect.width + 16, rect.height + 16), border_radius=12)
        screen.blit(glow_surf, (rect.x - 8, rect.y - 8))
    else:
        fill = color
    pygame.draw.rect(screen, fill, rect, border_radius=10)
    # Dark text for contrast
    text_color = (10, 10, 10)
    text_surf = FONT_SUB.render(text, True, text_color)
    screen.blit(text_surf, (rect.centerx - text_surf.get_width() // 2, rect.centery - text_surf.get_height() // 2))

def show_settings():
    global use_mouse_control, eye_tracking_enabled, game_difficulty, eye_tracking_sensitivity
    while True:
        screen.fill((12, 18, 28))
        cx = WIDTH // 2
        title = FONT_TITLE.render("SETTINGS", True, NEON_GREEN)
        screen.blit(title, (cx - title.get_width()//2, 40))
        pygame.draw.line(screen, (0, 200, 120), (cx-200, 100), (cx+200, 100), 1)
        
        # Difficulty Section
        diff_title = FONT_SUB.render("DIFFICULTY", True, WHITE)
        screen.blit(diff_title, (cx - diff_title.get_width()//2, 120))
        
        easy_btn = pygame.Rect(cx - 160, 160, 155, 45)
        easy_hv = easy_btn.collidepoint(pygame.mouse.get_pos())
        e_color = NEON_GREEN if game_difficulty == "EASY" else GRAY
        draw_button(easy_btn, "EASY" + (" [ON]" if game_difficulty == "EASY" else ""), e_color, easy_hv)
        
        med_btn = pygame.Rect(cx + 5, 160, 155, 45)
        med_hv = med_btn.collidepoint(pygame.mouse.get_pos())
        m_color = NEON_YELLOW if game_difficulty == "MEDIUM" else GRAY
        draw_button(med_btn, "MEDIUM" + (" [ON]" if game_difficulty == "MEDIUM" else ""), m_color, med_hv)

        # Control Mode Section
        section = FONT_SUB.render("CONTROL MODE", True, WHITE)
        screen.blit(section, (cx - section.get_width()//2, 230))
        mouse_btn = pygame.Rect(cx - 160, 270, 320, 50)
        mouse_hv = mouse_btn.collidepoint(pygame.mouse.get_pos())
        mouse_active = use_mouse_control and not eye_tracking_enabled
        m_color = NEON_GREEN if mouse_active else GRAY
        draw_button(mouse_btn, "MOUSE CONTROL" + (" [ACTIVE]" if mouse_active else ""), m_color, mouse_hv)
        eye_btn = pygame.Rect(cx - 160, 335, 320, 50)
        eye_hv = eye_btn.collidepoint(pygame.mouse.get_pos())
        e_color = NEON_GREEN if eye_tracking_enabled else GRAY
        et_status = " [ACTIVE]" if eye_tracking_enabled else (" [NO CAMERA]" if not eye_tracking_available else "")
        draw_button(eye_btn, "EYE TRACKING" + et_status, e_color, eye_hv)
        
        # Sensitivity Section
        sens_title = FONT_SUB.render(f"EYE SENSITIVITY: {eye_tracking_sensitivity:.1f}x", True, WHITE)
        screen.blit(sens_title, (cx - sens_title.get_width()//2, 410))
        sens_down = pygame.Rect(cx - 80, 440, 60, 40)
        sd_hv = sens_down.collidepoint(pygame.mouse.get_pos())
        draw_button(sens_down, "-", NEON_GREEN, sd_hv)
        sens_up = pygame.Rect(cx + 20, 440, 60, 40)
        su_hv = sens_up.collidepoint(pygame.mouse.get_pos())
        draw_button(sens_up, "+", NEON_GREEN, su_hv)
        
        info1 = FONT_SMALL.render("Mouse: Aim with mouse, Click or SPACE to shoot", True, GRAY)
        info2 = FONT_SMALL.render("Eye Tracking: Aim with eyes, Blink to shoot", True, GRAY)
        screen.blit(info1, (cx - info1.get_width()//2, 510))
        screen.blit(info2, (cx - info2.get_width()//2, 535))
        back_btn = pygame.Rect(cx - 140, 600, 280, 50)
        back_hv = back_btn.collidepoint(pygame.mouse.get_pos())
        draw_button(back_btn, "BACK TO MENU", NEON_BLUE, back_hv)
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT: cleanup()
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE: return
            if event.type == pygame.MOUSEBUTTONDOWN:
                global health, max_health
                if easy_btn.collidepoint(event.pos): 
                    game_difficulty = "EASY"
                    max_health = 5
                    health = min(health + 2, max_health)
                if med_btn.collidepoint(event.pos): 
                    game_difficulty = "MEDIUM"
                    max_health = 3
                    health = min(health, max_health)
                if sens_down.collidepoint(event.pos): eye_tracking_sensitivity = max(0.5, eye_tracking_sensitivity - 0.1)
                if sens_up.collidepoint(event.pos): eye_tracking_sensitivity = min(3.0, eye_tracking_sensitivity + 0.1)
                if mouse_btn.collidepoint(event.pos):
                    use_mouse_control = True
                    eye_tracking_enabled = False
                if eye_btn.collidepoint(event.pos) and eye_tracking_available:
                    eye_tracking_enabled = True
                    use_mouse_control = False
                if back_btn.collidepoint(event.pos): return
        pygame.display.flip()
        clock.tick(60)

def show_how_to_play():
    while True:
        screen.fill((12, 18, 28))
        cx = WIDTH // 2
        title = FONT_TITLE.render("HOW TO PLAY", True, NEON_GREEN)
        screen.blit(title, (cx - title.get_width()//2, 40))
        pygame.draw.line(screen, (0, 200, 120), (cx-200, 100), (cx+200, 100), 1)
        
        instructions = [
            ("CONTROLS", [
                "MOUSE MOVE  -  Move crosshair / aim",
                "LEFT CLICK  -  Quick shoot (Mouse mode)",
                "HOLD SPACE  -  Charge blink shot",
                "RELEASE SPACE  -  Fire charged shot",
                "E  -  Toggle Eye Tracking / Mouse",
            ]),
            ("HOW TO PLAY", [
                "Hold SPACE to charge your blink ability",
                "A red ring appears around crosshair while charging",
                "Release SPACE to shoot at the crosshair position",
                "Longer charge = bigger blast radius",
                "Destroy all targets / enemies to clear level",
            ]),
            ("TIPS", [
                "Fully charged shots (750ms) deal maximum area damage",
                "Eye Tracking mode: aim with eyes, blink to shoot",
                "Mouse mode: click for instant shot, hold SPACE for charged",
                "Don't shoot the hostage! Aim carefully at enemies only",
            ]),
        ]
        
        y_offset = 130
        for heading, lines in instructions:
            heading_surf = FONT_SUB.render(heading, True, WHITE)
            screen.blit(heading_surf, (cx - heading_surf.get_width()//2, y_offset))
            y_offset += 38
            for line in lines:
                line_surf = FONT_SMALL.render(line, True, GRAY)
                screen.blit(line_surf, (cx - line_surf.get_width()//2, y_offset))
                y_offset += 26
            y_offset += 16
        
        back_btn = pygame.Rect(cx - 140, 620, 280, 50)
        back_hv = back_btn.collidepoint(pygame.mouse.get_pos())
        draw_button(back_btn, "BACK TO MENU", NEON_BLUE, back_hv)
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT: cleanup()
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE: return
            if event.type == pygame.MOUSEBUTTONDOWN:
                if back_btn.collidepoint(event.pos): return
        pygame.display.flip()
        clock.tick(60)

def main():
    global score, shots_fired, hits, current_level, health, combo, max_combo, eye_tracking_enabled, max_health
    score = 0
    shots_fired = 0
    hits = 0
    current_level = 1
    max_health = 10 if game_difficulty == "EASY" else 3
    health = max_health
    combo = 0
    max_combo = 0
    
    init_eye_tracking()
    
    star_time = time.time()
    stars = [(random.randint(0, WIDTH), random.randint(0, HEIGHT), random.uniform(0.5, 2.5), random.uniform(0, math.pi*2)) for _ in range(200)]
    scanline_offset = 0

    while True:
        t = time.time() - star_time
        bg_col = (12, 18, 28)
        screen.fill(bg_col)
        for x, y, size, phase in stars:
            alpha = int(150 + 100 * math.sin(t * 2 + phase))
            alpha = max(0, min(255, alpha))
            s = pygame.Surface((int(size*2+1), int(size*2+1)), pygame.SRCALPHA)
            pygame.draw.circle(s, (200, 220, 255, alpha), (int(size), int(size)), int(size))
            screen.blit(s, (x, y))
        grid_surf = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        for x in range(0, WIDTH, 80): pygame.draw.line(grid_surf, (0, 255, 150, 8), (x, 0), (x, HEIGHT))
        for y in range(0, HEIGHT, 80): pygame.draw.line(grid_surf, (0, 255, 150, 8), (0, y), (WIDTH, y))
        screen.blit(grid_surf, (0, 0))
        cx, cy = WIDTH//2, 220
        glow = pygame.Surface((600, 300), pygame.SRCALPHA)
        for r in range(150, 0, -10):
            alpha = int(r * 0.18)
            pygame.draw.circle(glow, (0, 255, 150, alpha), (300, 150), r)
        screen.blit(glow, (cx-300, cy-150))
        title_y_offset = math.sin(t * 0.7) * 6
        ty = int(180 + title_y_offset)
        for glow_r in [6, 4, 2]:
            big_t = FONT_TITLE.render("BLINK SNIPER", True, (0, 255*glow_r//6, 150*glow_r//6))
            screen.blit(big_t, (cx - big_t.get_width()//2 + random.randint(-glow_r,glow_r)//3, ty + random.randint(-glow_r,glow_r)//3))
        big_t = FONT_TITLE.render("BLINK SNIPER", True, NEON_GREEN)
        screen.blit(big_t, (cx - big_t.get_width()//2, ty))
        subs = FONT_SUB.render('"Only your eyes can save her."', True, GRAY)
        screen.blit(subs, (cx - subs.get_width()//2, ty + 80))
        pygame.draw.line(screen, (0, 200, 120), (cx - 200, ty + 115), (cx + 200, ty + 115), 1)
        btn_y = 370
        start_btn = pygame.Rect(cx - 140, btn_y, 280, 50)
        start_hover = start_btn.collidepoint(pygame.mouse.get_pos())
        draw_button(start_btn, "START GAME", ACCENT, start_hover)
        howto_btn = pygame.Rect(cx - 140, btn_y + 65, 280, 50)
        howto_hover = howto_btn.collidepoint(pygame.mouse.get_pos())
        draw_button(howto_btn, "HOW TO PLAY", NEON_YELLOW, howto_hover)
        settings_btn = pygame.Rect(cx - 140, btn_y + 130, 280, 50)
        settings_hover = settings_btn.collidepoint(pygame.mouse.get_pos())
        draw_button(settings_btn, "SETTINGS", NEON_BLUE, settings_hover)
        exit_btn = pygame.Rect(cx - 140, btn_y + 195, 280, 50)
        exit_hover = exit_btn.collidepoint(pygame.mouse.get_pos())
        draw_button(exit_btn, "EXIT", NEON_RED, exit_hover)
        process_eye_tracking()
        scanline_offset = (scanline_offset + 1) % 4
        scan_surf = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        for y in range(scanline_offset, HEIGHT, 4): pygame.draw.line(scan_surf, (0, 0, 0, 20), (0, y), (WIDTH, y))
        screen.blit(scan_surf, (0, 0))
        for event in pygame.event.get():
            if event.type == pygame.QUIT: cleanup()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if start_btn.collidepoint(event.pos): game_loop()
                if howto_btn.collidepoint(event.pos): show_how_to_play()
                if settings_btn.collidepoint(event.pos): show_settings()
                if exit_btn.collidepoint(event.pos): cleanup()
        pygame.display.flip()
        clock.tick(60)

if __name__ == "__main__":
    main()
