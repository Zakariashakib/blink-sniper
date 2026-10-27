"""High-fidelity procedural art direction for Blink Sniper.

Cyberpunk midnight atmosphere, detailed articulated cyber-enemies,
tactical sniper optic HUD, holographic drone targets, and vibrant particle systems.
"""
import math
import random
from functools import lru_cache
import pygame

W, H = 1280, 720

# High-contrast tactical cyberpunk palette
BG = (6, 12, 18)
PANEL = (14, 25, 34)
PANEL_ACCENT = (20, 38, 50)
LINE = (38, 62, 74)
LINE_BRIGHT = (60, 95, 110)
TEXT = (240, 248, 255)
MUTED = (130, 160, 172)
MINT = (0, 255, 196)       # High-tech neon mint / cyan
AMBER = (255, 180, 48)     # Warning / charge gold
RED = (255, 64, 96)        # Danger crimson
PURPLE = (180, 110, 255)   # Heavy / boss plasma violet
CYAN = (64, 224, 255)      # Shield / optic cyan


@lru_cache(maxsize=32)
def font(size, bold=False):
    return pygame.font.SysFont('Avenir Next,DejaVu Sans,Arial,Helvetica', size, bold=bold)


def text(surface, value, pos, size=18, color=TEXT, bold=False, anchor='topleft'):
    image = font(size, bold).render(str(value), True, color)
    rect = image.get_rect(**{anchor: pos})
    surface.blit(image, rect)
    return rect


def panel(surface, rect, fill=PANEL, border=LINE, radius=12, glow=False):
    r = pygame.Rect(rect)
    if glow:
        glow_surf = pygame.Surface((r.w + 8, r.h + 8), pygame.SRCALPHA)
        pygame.draw.rect(glow_surf, (*MINT, 35), (0, 0, r.w + 8, r.h + 8), border_radius=radius + 3)
        surface.blit(glow_surf, (r.x - 4, r.y - 4))
    pygame.draw.rect(surface, fill, r, border_radius=radius)
    pygame.draw.rect(surface, border, r, 1, border_radius=radius)


def bar(surface, rect, progress, color=MINT, bg=LINE):
    r = pygame.Rect(rect)
    pygame.draw.rect(surface, bg, r, border_radius=4)
    if progress > 0:
        fill_w = max(4, int(r.w * min(1.0, progress)))
        fill_rect = pygame.Rect(r.x, r.y, fill_w, r.h)
        pygame.draw.rect(surface, color, fill_rect, border_radius=4)
        # Inner highlight sheen
        if r.h >= 6:
            pygame.draw.line(surface, (255, 255, 255, 180), (r.x + 2, r.y + 1), (r.x + fill_w - 2, r.y + 1), 1)


@lru_cache(maxsize=8)
def landscape(level=1):
    s = pygame.Surface((W, H))
    rng = random.Random(24 + level * 7)

    # 1. Atmospheric sky gradient (cyberpunk night)
    top_col = (4, 9, 15) if level != 3 else (7, 10, 22)
    bot_col = (18, 36, 46) if level == 1 else (32, 28, 48) if level == 2 else (18, 44, 56)
    for y in range(H):
        ratio = min(1.0, y / 530)
        col = tuple(int(top_col[i] + (bot_col[i] - top_col[i]) * ratio) for i in range(3))
        pygame.draw.line(s, col, (0, y), (W, y))

    # 2. Celestial body / moon
    moon_x, moon_y = 1040, 140
    pygame.draw.circle(s, (30, 60, 75), (moon_x, moon_y), 56)
    pygame.draw.circle(s, (140, 180, 190), (moon_x, moon_y), 44)
    pygame.draw.circle(s, (185, 220, 228), (moon_x - 3, moon_y - 3), 40)
    # Moon craters / digital rings
    pygame.draw.circle(s, (160, 195, 205), (moon_x + 12, moon_y - 10), 10)
    pygame.draw.circle(s, (150, 185, 195), (moon_x - 14, moon_y + 12), 14)
    pygame.draw.circle(s, (0, 255, 196), (moon_x, moon_y), 58, 1)

    # 3. Distant mountain / skyline silhouettes
    for layer in range(3):
        base = 310 + layer * 46
        col = [(15, 28, 38), (18, 36, 47), (12, 24, 32)][layer]
        if level == 3:  # City skyline with rooftops
            pts = [(0, H)]
            cx = 0
            while cx < W:
                bw = rng.randint(45, 95)
                bh = rng.randint(120, 260) - layer * 35
                pts.extend([(cx, H - bh), (cx + bw, H - bh)])
                cx += bw
            pts.append((W, H))
            pygame.draw.polygon(s, col, pts)
        else:  # Mountains & industrial rigs
            pts = [(0, H)] + [(x, base - rng.randint(15, 95)) for x in range(0, W + 81, 75)] + [(W, H)]
            pygame.draw.polygon(s, col, pts)

    # 4. Level-specific industrial architecture
    if level == 1:
        # Firing range barriers & holographic target posts
        for x, y, width, height in [(80, 360, 170, 96), (920, 340, 220, 116), (1110, 375, 150, 81)]:
            pygame.draw.rect(s, (22, 42, 54), (x, y, width, height))
            pygame.draw.line(s, MINT, (x, y), (x + width, y), 2)
            for xx in range(x + 14, x + width - 10, 26):
                pygame.draw.rect(s, (45, 80, 95), (xx, y + 16, 8, 4))
        # Range distance marker signs
        for rx, label in [(280, '100M'), (510, '200M'), (750, '300M'), (1000, '400M')]:
            pygame.draw.line(s, LINE, (rx, 440), (rx, 456), 2)
            text(s, label, (rx, 440), 9, MUTED, bold=True, anchor='midbottom')
    elif level == 2:
        # Desert outpost watchtowers & comms array
        pygame.draw.rect(s, (24, 40, 48), (910, 310, 220, 146))
        pygame.draw.line(s, AMBER, (910, 310), (1130, 310), 2)
        # Comms antenna tower with blinking beacon
        pygame.draw.line(s, (50, 78, 88), (1020, 170), (1020, 310), 4)
        for ay in (205, 240, 275):
            pygame.draw.line(s, (50, 78, 88), (1000, ay), (1040, ay), 2)
        pygame.draw.circle(s, RED, (1020, 170), 4)
    elif level == 3:
        # Cyber-city rooftops with glowing neon signs
        for bx, by, bw, bh in [(60, 310, 190, 146), (880, 290, 240, 166)]:
            pygame.draw.rect(s, (20, 34, 46), (bx, by, bw, bh))
            pygame.draw.line(s, CYAN, (bx, by), (bx + bw, by), 2)
            # Glowing window matrix
            for wy in range(by + 16, by + bh - 20, 22):
                for wx in range(bx + 16, bx + bw - 16, 24):
                    if rng.random() > 0.35:
                        pygame.draw.rect(s, (40, 85, 110), (wx, wy, 10, 8))

    # 5. Tactical Ground / Floor with perspective grid
    pygame.draw.rect(s, (10, 20, 28), (0, 456, W, 264))
    # Horizontal depth lines
    for y in [468, 484, 508, 540, 584, 642, 715]:
        pygame.draw.line(s, (22, 42, 54), (0, y), (W, y), 1)
    # Perspective grid lines radiating from horizon center
    for x in range(-900, 2200, 160):
        pygame.draw.line(s, (20, 38, 48), (640 + (x - 640) * 0.12, 456), (x, 720), 1)

    # 6. Tactical cover crates
    for x, y, width in [(60, 480, 110), (1080, 500, 140), (220, 550, 86), (820, 530, 105)]:
        pygame.draw.rect(s, (28, 48, 60), (x, y, width, 52), border_radius=4)
        pygame.draw.rect(s, (48, 78, 95), (x, y, width, 52), 1, border_radius=4)
        pygame.draw.line(s, (20, 35, 45), (x + 8, y + 10), (x + width - 8, y + 42), 2)
        pygame.draw.line(s, (20, 35, 45), (x + 8, y + 42), (x + width - 8, y + 10), 2)
        # Glowing status LED on crate
        pygame.draw.circle(s, MINT, (x + 12, y + 12), 2)

    # Horizon accent line
    pygame.draw.line(s, (45, 80, 95), (0, 456), (W, 456), 2)
    return s


def background(surface, t, level=1, reduced=False):
    surface.blit(landscape(level), (0, 0))

    if not reduced:
        # Sweeping military searchlight in sky
        if level in (2, 3):
            beam_surf = pygame.Surface((W, H), pygame.SRCALPHA)
            sweep_angle = math.sin(t * 0.6) * 0.45
            center_x = 1020 if level == 2 else 980
            center_y = 310 if level == 2 else 290
            target_x = center_x + math.sin(sweep_angle) * 700
            target_y = center_y - math.cos(sweep_angle) * 500
            # Beam cone polygon
            perp_x = -math.cos(sweep_angle) * 65
            perp_y = -math.sin(sweep_angle) * 65
            pts = [
                (center_x, center_y),
                (int(target_x + perp_x), int(target_y + perp_y)),
                (int(target_x - perp_x), int(target_y - perp_y)),
            ]
            pygame.draw.polygon(beam_surf, (*CYAN, 14), pts)
            surface.blit(beam_surf, (0, 0))

        # Floating ambient cyber-dust embers
        for i in range(28):
            x = (i * 193 + t * (9 + i % 5)) % W
            y = 170 + (i * 73) % 400 + math.sin(t * 0.45 + i) * 10
            col = (0, 255, 196) if i % 4 == 0 else (120, 160, 180)
            pygame.draw.circle(surface, col, (int(x), int(y)), 1 if i % 3 != 0 else 2)


def enemy(surface, entity, t, reduced=False):
    x, y = entity.x, entity.y
    age = entity.age
    spawn = min(1.0, age / 0.4)
    # Spawn drop-in with damping
    y += ((1.0 - spawn) ** 3) * 45
    bob = 0 if reduced else math.sin(t * 2.4 + entity.phase) * 3
    y += bob

    color = {
        'guard': MINT,
        'sniper': AMBER,
        'runner': RED,
        'heavy': PURPLE,
        'boss': RED,
    }.get(entity.kind, MINT)

    # -------------------------------------------------------------
    # 1. PRACTICE TARGET (Holographic Cyber Drone)
    # -------------------------------------------------------------
    if entity.kind == 'target':
        # Shadow
        pygame.draw.ellipse(surface, (0, 0, 0, 90), (x - 38, y + 48, 76, 14))
        # Thruster particle beam
        thruster_len = 16 + math.sin(t * 12 + entity.phase) * 6
        pygame.draw.line(surface, CYAN, (x, y + 26), (x, y + 26 + thruster_len), 3)
        pygame.draw.line(surface, (255, 255, 255), (x, y + 26), (x, y + 26 + thruster_len * 0.5), 1)

        # Rotating outer holographic ring
        spin = t * 2.5
        ring_r = 38
        for a_deg in (0, 60, 120, 180, 240, 300):
            rad = math.radians(a_deg + spin * 35)
            px = x + math.cos(rad) * ring_r
            py = y + math.sin(rad) * (ring_r * 0.45)
            pygame.draw.circle(surface, MINT if entity.flash <= 0 else (255, 255, 255), (int(px), int(py)), 3)

        # Concentric Bullseye Rings
        pygame.draw.circle(surface, (18, 38, 46), (int(x), int(y)), 32)
        pygame.draw.circle(surface, AMBER if entity.flash <= 0 else (255, 255, 255), (int(x), int(y)), 32, 2)
        pygame.draw.circle(surface, (28, 54, 64), (int(x), int(y)), 22)
        pygame.draw.circle(surface, RED if entity.flash <= 0 else (255, 255, 255), (int(x), int(y)), 14)
        pygame.draw.circle(surface, (255, 255, 255), (int(x), int(y)), 5)

        # Drone side stabilizers
        for side in (-1, 1):
            pygame.draw.line(surface, (60, 95, 110), (x + side * 32, y), (x + side * 46, y - 6), 3)
            pygame.draw.circle(surface, CYAN, (int(x + side * 46), int(y - 6)), 3)

        text(surface, 'TARGET DRONE', (x, y + 54), 11, MUTED, bold=True, anchor='center')
        return

    # -------------------------------------------------------------
    # 2. ARTICULATED CYBER-WARRIORS & MECHS
    # -------------------------------------------------------------
    scale = 1.6 if entity.kind == 'boss' else 1.25 if entity.kind == 'heavy' else 1.05
    art = pygame.Surface((180, 200), pygame.SRCALPHA)
    cx, cy = 90, 95

    # Armor Flash / Dying Alpha
    armor_base = (245, 255, 255) if entity.flash > 0 else (55, 78, 88)
    armor_dark = (255, 255, 255) if entity.flash > 0 else (22, 36, 44)
    armor_highlight = (255, 255, 255) if entity.flash > 0 else (80, 115, 128)

    # Dynamic leg stride animation
    is_runner = entity.kind == 'runner'
    stride_speed = 8.5 if is_runner else 3.2
    stride = 0 if reduced else math.sin(t * stride_speed + entity.phase) * (11 if is_runner else 6)

    # Ground shadow
    pygame.draw.ellipse(art, (0, 0, 0, 140), (36, 160, 108, 18))

    # Articulated Legs & Tactical Boots
    for side in (-1, 1):
        leg_stride = side * stride
        hip = (cx + side * 14, cy + 12)
        knee = (cx + side * 20 + leg_stride * 0.5, cy + 38)
        foot = (cx + side * 24 + leg_stride, cy + 68)

        # Thigh & Shin armor
        pygame.draw.line(art, armor_dark, hip, knee, 13)
        pygame.draw.line(art, armor_base, knee, foot, 9)
        # Knee joint cap
        pygame.draw.circle(art, color, (int(knee[0]), int(knee[1])), 5)
        # Tactical Boot
        pygame.draw.line(art, (16, 26, 32), (foot[0] - 8, foot[1]), (foot[0] + 9, foot[1]), 8)
        pygame.draw.line(art, armor_highlight, (foot[0] - 6, foot[1] - 2), (foot[0] + 6, foot[1] - 2), 2)

    # Torso & Core Armor
    torso_pts = [(cx - 28, cy - 35), (cx + 28, cy - 35), (cx + 22, cy + 14), (cx - 22, cy + 14)]
    pygame.draw.polygon(art, armor_dark, torso_pts)
    pygame.draw.polygon(art, armor_base, [(cx - 24, cy - 33), (cx + 24, cy - 33), (cx + 18, cy + 10), (cx - 18, cy + 10)])
    # Chest reactor core badge
    pygame.draw.circle(art, color, (cx, cy - 14), 7 if entity.kind != 'boss' else 12)
    pygame.draw.circle(art, (255, 255, 255), (cx, cy - 14), 3 if entity.kind != 'boss' else 6)

    # Shoulders (Pauldrons)
    for side in (-1, 1):
        shoulder_x = cx + side * 34
        shoulder_y = cy - 28
        pygame.draw.circle(art, armor_base, (int(shoulder_x), int(shoulder_y)), 11)
        pygame.draw.circle(art, color, (int(shoulder_x), int(shoulder_y)), 4)
        # Arm
        elbow = (shoulder_x + side * 3, shoulder_y + 24)
        hand = (shoulder_x + side * 5, shoulder_y + 44)
        pygame.draw.line(art, armor_dark, (shoulder_x, shoulder_y), elbow, 9)
        pygame.draw.line(art, armor_base, elbow, hand, 7)

    # Cybernetic Helmet & Visor
    helmet_rect = pygame.Rect(cx - 18, cy - 65, 36, 28)
    pygame.draw.rect(art, armor_base, helmet_rect, border_radius=8)
    pygame.draw.rect(art, armor_dark, (cx - 15, cy - 54, 30, 12), border_radius=3)
    # Glowing animated Visor
    visor_glow = math.sin(t * 5 + entity.phase) * 2
    pygame.draw.line(art, color, (cx - 13, cy - 48), (cx + 13, cy - 48), int(4 + max(0, visor_glow)))
    pygame.draw.line(art, (255, 255, 255), (cx - 8, cy - 48), (cx + 8, cy - 48), 1)

    # Weapons & Type-Specific Gear
    recoil_shift = max(0, 1 - entity.recoil / 0.18) * 6 if entity.recoil > 0 else 0
    gun_x = cx + 8 - int(recoil_shift)
    gun_y = cy - 6

    if entity.kind == 'sniper':
        # Long-barrel sniper rifle with scope
        pygame.draw.rect(art, (14, 22, 28), (gun_x, gun_y, 64, 8), border_radius=2)
        pygame.draw.rect(art, (70, 95, 105), (gun_x + 38, gun_y - 4, 18, 5), border_radius=2)
        # Long barrel + suppressor
        pygame.draw.line(art, (120, 150, 160), (gun_x + 64, gun_y + 4), (gun_x + 76, gun_y + 4), 3)
        # Ghillie camo cowl
        pygame.draw.polygon(art, (40, 58, 48), [(cx - 24, cy - 62), (cx + 24, cy - 62), (cx + 32, cy - 35), (cx - 32, cy - 35)])
    elif entity.kind == 'runner':
        # Dual blade / compact SMGs & aerodynamic thrusters
        pygame.draw.rect(art, (18, 28, 34), (gun_x, gun_y + 2, 38, 7), border_radius=2)
        # Thruster exhaust trail
        pygame.draw.circle(art, AMBER, (cx - 22, cy - 10), 4)
        pygame.draw.circle(art, RED, (cx - 22, cy - 8), 2)
    elif entity.kind in ('heavy', 'boss'):
        # Riot Shield / Hex-barrier generator in off-hand
        shield_pts = [(cx - 44, cy - 30), (cx - 26, cy - 30), (cx - 26, cy + 42), (cx - 44, cy + 35)]
        pygame.draw.polygon(art, (28, 48, 62), shield_pts)
        pygame.draw.polygon(art, color, shield_pts, 2)
        # Heavy rotary autocannon
        pygame.draw.rect(art, (16, 26, 32), (gun_x, gun_y - 4, 58, 14), border_radius=3)
        for by_off in (-2, 2):
            pygame.draw.line(art, (100, 130, 145), (gun_x + 58, gun_y + 3 + by_off), (gun_x + 72, gun_y + 3 + by_off), 3)

    # Muzzle flash during recoil
    if entity.recoil > 0:
        pygame.draw.polygon(art, AMBER, [(gun_x + 66, gun_y - 2), (gun_x + 88, gun_y + 4), (gun_x + 66, gun_y + 10)])
        pygame.draw.circle(art, (255, 255, 255), (gun_x + 68, gun_y + 4), 4)

    # Dying Disintegration Animation
    if entity.dying > 0:
        alpha_factor = max(0.0, entity.dying / 0.45)
        art.set_alpha(int(255 * alpha_factor))
        art = pygame.transform.rotate(art, (0.45 - entity.dying) * 90 * entity.direction)

    # Scale and Blit
    final_w = int(art.get_width() * scale * max(0.1, spawn))
    final_h = int(art.get_height() * scale * max(0.1, spawn))
    art = pygame.transform.smoothscale(art, (final_w, final_h))
    dest_rect = art.get_rect(center=(int(x), int(y)))
    surface.blit(art, dest_rect)

    # -------------------------------------------------------------
    # 3. OVERHEAD STATUS & ACTIVE THREAT LOCK-ON
    # -------------------------------------------------------------
    if entity.dying <= 0:
        top_y = y - 72 * scale
        text(surface, entity.kind.upper(), (x, top_y - 14), 11, color, bold=True, anchor='center')
        # Segmented health bar
        bar_w = int(54 * scale)
        bar(surface, (x - bar_w // 2, top_y, bar_w, 4), entity.hp / entity.max_hp, color)

        # Active Sniper Targeting Laser Beam!
        if entity.kind == 'sniper':
            laser_alpha = int(120 + math.sin(t * 10) * 80)
            laser_col = (*AMBER, laser_alpha) if entity.warning > 0.4 else (*RED, 80)
            laser_surf = pygame.Surface((W, H), pygame.SRCALPHA)
            # Beam from rifle to bottom edge towards player
            pygame.draw.line(laser_surf, laser_col, (x + 35, y - 6), (x - 220, H), 2 if entity.warning > 0.4 else 1)
            surface.blit(laser_surf, (0, 0))

        # Warning / Lock-On Threat Indicator
        if entity.warning > 0:
            warn_r = int(50 * scale)
            # Spinning danger brackets
            pygame.draw.arc(surface, AMBER, (x - warn_r, y - warn_r, warn_r * 2, warn_r * 2),
                            -math.pi / 2, -math.pi / 2 + math.tau * entity.warning, 3)
            # Threat icon
            if entity.warning > 0.65:
                text(surface, '! THREAT !', (x, top_y - 28), 10, RED, bold=True, anchor='center')


def reticle(surface, position, progress=0, hit=0, locked=False):
    """High-tech sniper optic crosshair with animated blink-charge HUD."""
    x, y = map(int, position)
    color = AMBER if locked else MINT
    radius = 24 + int(hit * 18)

    # 1. Outer tactical milliradian ring
    pygame.draw.circle(surface, (12, 28, 36), (x, y), radius + 10, 4)
    pygame.draw.circle(surface, LINE_BRIGHT, (x, y), radius + 10, 1)

    # Milliradian tick marks
    for a_deg in (0, 45, 90, 135, 180, 225, 270, 315):
        rad = math.radians(a_deg)
        p1 = (x + math.cos(rad) * (radius + 6), y + math.sin(rad) * (radius + 6))
        p2 = (x + math.cos(rad) * (radius + 12), y + math.sin(rad) * (radius + 12))
        pygame.draw.line(surface, MUTED, p1, p2, 1)

    # 2. Precision Corner Brackets
    b_len = 10
    for sx, sy in [(-1, -1), (-1, 1), (1, -1), (1, 1)]:
        pygame.draw.line(surface, color, (x + sx * radius, y + sy * b_len), (x + sx * radius, y + sy * radius), 2)
        pygame.draw.line(surface, color, (x + sx * b_len, y + sy * radius), (x + sx * radius, y + sy * radius), 2)

    # 3. Illuminated Center Dot & Hairlines
    pygame.draw.circle(surface, color, (x, y), 2)
    pygame.draw.line(surface, color, (x - 6, y), (x + 6, y), 1)
    pygame.draw.line(surface, color, (x, y - 6), (x, y + 6), 1)

    # 4. Animated Blink Charge Progress Ring
    if progress > 0:
        charge_r = radius + 18
        pygame.draw.circle(surface, (25, 45, 55), (x, y), charge_r, 2)
        pygame.draw.arc(surface, AMBER, (x - charge_r, y - charge_r, charge_r * 2, charge_r * 2),
                        -math.pi / 2, -math.pi / 2 + math.tau * progress, 4)
        # Charging HUD text
        pct = int(progress * 100)
        text(surface, f"EYES CLOSED {pct}%", (x, y + charge_r + 8), 10, AMBER, bold=True, anchor='midtop')

    # 5. Hit Marker ('X' Flash)
    if hit > 0:
        hm_col = (255, 255, 255)
        for sx, sy in [(-1, -1), (-1, 1), (1, -1), (1, 1)]:
            pygame.draw.line(surface, hm_col, (x + sx * 7, y + sy * 7), (x + sx * 16, y + sy * 16), 3)
