"""Blink Sniper: one accessible entry point, three missions, eyes-first controls."""
import argparse
from dataclasses import dataclass
import math
import os
from pathlib import Path
import random
import statistics
import time
import pygame
from tracking import BlinkDetector, EyeTracker, GazeCalibration, Observation
import visuals as v
import audio


@dataclass
class Enemy:
    x: float
    y: float
    kind: str = 'guard'
    hp: int = 1
    max_hp: int = 1
    age: float = 0
    phase: float = 0
    direction: int = 1
    flash: float = 0
    recoil: float = 0
    dying: float = 0
    warning: float = 0
    attack: float = 8
    origin: float = 0

    def __post_init__(self):
        self.origin = self.x
        self.max_hp = self.hp


class Game:
    def __init__(self, camera=True, camera_index=0):
        pygame.init()
        self.screen = pygame.display.set_mode((v.W, v.H))
        pygame.display.set_caption('BLINK SNIPER / Hands-Free Optical Combat')
        self.clock = pygame.time.Clock()
        self.running = True
        self.state = 'menu'
        self.previous_state = 'menu'
        self.t = 0
        self.entered = 0
        self.mode = 'eyes' if camera else 'mouse'
        self.aim_mode = 'iris'
        self.difficulty = 'RELAXED'
        self.reduced_motion = False
        self.speed = 1.0
        self.detector = BlinkDetector()
        self.gaze = GazeCalibration()
        self.tracker = EyeTracker(camera_index)
        self.observation = Observation(status='Mouse mode / camera off')
        self.last_observation = 0
        self.valid_face = False
        self.blink = False
        self.aim = pygame.Vector2(v.W / 2, v.H / 2)
        self.raw_aim = self.aim.copy()
        self.head_center = (.5, .5)
        self.buttons = []
        self.scan_index = 0
        self.scan_timer = 0
        self.scan_locked = None
        self.dwell_key = None
        self.dwell = 0
        self.level = 1
        self.health = 5
        self.max_health = 5
        self.score = 0
        self.shots = 0
        self.hits = 0
        self.combo = 0
        self.kills = 0
        self.total = 5
        self.entities = []
        self.effects = []
        self.popups = []
        self.hit_flash = 0
        self.damage = 0
        self.shot_flash = 0
        self.charging = None
        self.last_shot = -1
        self.shake = 0.0
        self.message = ''
        self.message_until = 0
        self.cal_index = 0
        self.cal_timer = 0
        self.cal_samples = []
        self.cal_points = []
        self.cal_wait = 0
        self.cal_resume = False
        self.focused = True
        self.session_time = 0
        self.preview_stamp = -1
        self.preview_surface = None
        if camera:
            self.tracker.start()

    def change(self, state):
        self.state = state
        self.entered = self.t
        self.scan_index = 0
        self.scan_timer = 0
        self.scan_locked = None
        self.dwell = 0
        self.dwell_key = None
        self.detector.reset()
        self.charging = None
        self.blink = False
        self.buttons = []

    def notify(self, message):
        self.message = message
        self.message_until = self.t + 3

    def start_calibration(self):
        if self.state not in ('calibration', 'calibration_done', 'calibration_failed'):
            self.cal_resume = self.state in ('playing', 'paused') or (self.state == 'settings' and self.previous_state == 'paused')
        if self.mode != 'eyes':
            self.mode = 'eyes'
            self.tracker.start()
        self.cal_index = 0
        self.cal_timer = 0
        self.cal_wait = 0
        self.cal_samples = []
        self.cal_points = []
        self.detector.recalibrate()
        self.change('calibration')

    def start_game(self):
        self.level = 1
        self.score = 0
        self.shots = self.hits = self.combo = 0
        self.max_health = 8 if self.difficulty == 'RELAXED' else 4
        self.health = self.max_health
        if self.detector.baseline is None:
            self.detector.baseline = 0.28
        self.spawn()
        self.change('playing')

    def spawn(self):
        self.entities = []
        self.effects = []
        self.popups = []
        self.kills = 0
        self.session_time = 0
        self.charging = None
        self.detector.reset()
        positions = [(280, 315), (510, 400), (750, 310), (1000, 410), (630, 245)]
        kinds = ['target'] * 5 if self.level == 1 else ['guard', 'runner', 'sniper', 'guard', 'heavy'] if self.level == 2 else ['heavy', 'sniper', 'boss', 'runner', 'guard']
        self.total = len(kinds)
        for i, (kind, (x, y)) in enumerate(zip(kinds, positions)):
            hp = 6 if kind == 'boss' else 2 if kind == 'heavy' else 1
            if self.difficulty == 'STANDARD' and kind not in ('target', 'boss'):
                hp += 1
            self.entities.append(Enemy(x, y, kind, hp, phase=i * 1.7, attack=7 + i * 1.5))

    def tracking(self, dt):
        self.blink = False
        if self.mode != 'eyes':
            self.valid_face = False
            return False
        obs = self.tracker.latest()
        self.observation = obs
        self.valid_face = obs.ear is not None and time.monotonic() - obs.timestamp < .3
        if not self.valid_face or not self.focused:
            self.detector.reset()
            self.scan_locked = None
            self.dwell = 0
            return False
        fresh = obs.timestamp != self.last_observation
        if fresh:
            self.last_observation = obs.timestamp
            was_closed = self.detector.closed
            self.blink = self.detector.update(obs.ear, obs.timestamp, getattr(obs, 'blink_score', None))
            if self.detector.closed and not was_closed:
                self.scan_locked = self.scan_index
                audio.play('blink')
            if not self.detector.closed:
                self.scan_locked = None
            if not self.detector.closed and (self.detector.baseline or obs.nose):
                if self.aim_mode == 'iris' and self.gaze.matrix is not None:
                    nx, ny = self.gaze.map(obs.gaze)
                elif obs.nose:
                    # Robust, frictionless head-pose aiming
                    nx = .5 + (obs.nose[0] - self.head_center[0]) * 4
                    ny = .5 + (obs.nose[1] - self.head_center[1]) * 5
                else:
                    nx = ny = .5
                self.raw_aim.update(max(24, min(v.W - 24, nx * v.W)), max(24, min(v.H - 24, ny * v.H)))
        # Freeze the last open-eye aim throughout closure, including the shot frame.
        if not self.detector.closed:
            self.aim += (self.raw_aim - self.aim) * (1 - math.exp(-dt * 12))
        return fresh

    @property
    def ready(self):
        return self.mode == 'mouse' or (self.valid_face and self.detector.baseline is not None and (self.aim_mode == 'head' or self.gaze.matrix is not None or getattr(self.observation, 'nose', None) is not None))

    def calibration_update(self, dt, fresh):
        self.cal_wait += dt
        if self.cal_wait > 35:
            self.change('calibration_failed')
            return
        if not self.valid_face or self.detector.baseline is None or self.detector.closed:
            self.cal_timer = 0
            self.cal_samples = []
            return
        self.cal_timer += dt
        if fresh and self.cal_timer > .8:
            self.cal_samples.append(self.observation.gaze)
        if self.cal_timer >= 2.2 and len(self.cal_samples) >= 12:
            self.cal_points.append(tuple(statistics.median(p[i] for p in self.cal_samples) for i in (0, 1)))
            self.cal_index += 1
            self.cal_timer = 0
            self.cal_wait = 0
            self.cal_samples = []
            if self.cal_index == 5:
                if self.gaze.fit(self.cal_points):
                    self.head_center = self.observation.nose
                    self.change('calibration_done')
                else:
                    self.change('calibration_failed')

    def shoot(self, charged=False):
        if self.state != 'playing' or not self.ready or self.t - self.last_shot < .22:
            return
        self.last_shot = self.t
        self.shots += 1
        self.shot_flash = .2
        self.shake = 8.0 if charged else 5.0
        audio.play('railgun' if charged else 'shot')

        point = self.aim.copy()
        # Hostage protection
        if self.level == 3 and point.distance_to((1050, 270)) < 42:
            self.change('hostage_lost')
            return
        candidates = [e for e in self.entities if e.dying <= 0 and point.distance_to((e.x, e.y)) < (68 if e.kind == 'boss' else 46)]
        hit = min(candidates, key=lambda e: point.distance_to((e.x, e.y))) if candidates else None
        if hit:
            self.hits += 1
            self.combo += 1
            self.hit_flash = .22
            # Headshot multiplier (upper 35% of silhouette)
            is_headshot = point.y < (hit.y - 12) and hit.kind != 'target'
            dmg = (6 if charged else 2) if is_headshot else (3 if charged else 1)
            hit.hp -= dmg
            hit.flash = .18
            base_score = 100 + min(5, self.combo) * 20
            score_gain = base_score + (100 if is_headshot else 0)
            self.score += score_gain

            if is_headshot:
                audio.play('headshot')
                self.popups.append([hit.x, hit.y - 45, f'HEADSHOT +{score_gain}', 1.2])
            elif hit.hp <= 0:
                audio.play('kill')
                self.popups.append([hit.x, hit.y - 32, 'TARGET DOWN' if hit.kind == 'target' else 'ELIMINATED', 1.0])
            else:
                audio.play('hit')
                self.popups.append([hit.x, hit.y - 32, 'ARMOR HIT', .65])

            if hit.hp <= 0:
                hit.dying = .45
                self.kills += 1
                self.burst(hit.x, hit.y, v.MINT if hit.kind == 'target' else v.AMBER, 26)
            else:
                self.burst(hit.x, hit.y, v.AMBER, 14)
        else:
            self.combo = 0
            self.burst(point.x, point.y, v.MUTED, 8)

    def burst(self, x, y, color, count):
        for _ in range(count):
            angle = random.uniform(0, math.tau)
            speed = random.uniform(50, 200)
            self.effects.append([x, y, math.cos(angle) * speed, math.sin(angle) * speed, .65, color])

    def play_update(self, dt):
        if not self.ready or (self.mode == 'eyes' and not self.detector.armed and self.detector.started is None):
            return
        self.session_time += dt
        sim = dt * self.speed
        for e in self.entities[:]:
            e.age += sim
            e.flash = max(0, e.flash - dt)
            e.recoil = max(0, e.recoil - dt)
            if e.dying > 0:
                e.dying -= dt
                if e.dying <= 0:
                    self.entities.remove(e)
                continue
            if e.kind != 'target':
                amplitude = 48 if e.kind == 'runner' else 23 if e.kind == 'boss' else 18
                rate = 1.7 if e.kind == 'runner' else .55
                if not self.detector.closed:
                    e.x = e.origin + math.sin(self.session_time * rate + e.phase) * amplitude
                e.attack -= sim
                e.warning = max(0, 1 - e.attack / 1.5)
                if e.attack <= 0:
                    e.attack = (9 if self.difficulty == 'RELAXED' else 5) + random.uniform(0, 2)
                    e.recoil = .18
                    self.health -= 1
                    self.damage = .35
                    self.shake = 7.0
                    audio.play('alarm')
                    self.burst(e.x + 35, e.y, v.AMBER, 6)
                    if self.health <= 0:
                        self.change('lost')
                        return
        if not self.entities:
            self.change('won' if self.level == 3 else 'complete')

    def update(self, dt):
        self.t += dt
        fresh = self.tracking(dt)
        self.hit_flash = max(0, self.hit_flash - dt)
        self.damage = max(0, self.damage - dt)
        self.shot_flash = max(0, self.shot_flash - dt)
        if self.shake > 0:
            self.shake = max(0.0, self.shake - dt * 16.0)

        for p in self.effects[:]:
            p[0] += p[2] * dt
            p[1] += p[3] * dt
            p[3] += 180 * dt
            p[4] -= dt
            if p[4] <= 0:
                self.effects.remove(p)
        for p in self.popups[:]:
            p[1] -= dt * 26
            p[3] -= dt
            if p[3] <= 0:
                self.popups.remove(p)
        if self.state == 'calibration':
            self.calibration_update(dt, fresh)
        elif self.state == 'playing':
            if self.mode == 'eyes' and self.ready and not self.detector.closed:
                # Gentle assist magnetically guides to the nearest enemy weak point
                targets = [e for e in self.entities if e.dying <= 0 and self.raw_aim.distance_to((e.x, e.y)) < 75]
                if targets:
                    target = min(targets, key=lambda e: self.raw_aim.distance_to((e.x, e.y)))
                    self.aim += (pygame.Vector2(target.x, target.y) - self.aim) * (1 - math.exp(-dt * 9))
            if self.blink:
                self.shoot()
            self.play_update(dt)

    def action(self, key):
        audio.play('ui')
        if key == 'quit':
            self.running = False
        elif key == 'menu':
            self.change('menu')
        elif key == 'start':
            if self.mode == 'eyes' and self.detector.baseline is None and self.observation.nose is None:
                self.start_calibration()
            else:
                self.start_game()
        elif key == 'calibrate':
            self.start_calibration()
        elif key == 'deploy':
            if self.state == 'calibration_done' and self.cal_resume:
                self.change('playing')
            else:
                self.start_game()
        elif key == 'resume':
            self.change('playing')
        elif key == 'pause':
            self.change('paused')
        elif key == 'next':
            self.level += 1
            self.health = min(self.max_health, self.health + 2)
            self.spawn()
            self.change('playing')
        elif key == 'settings':
            self.previous_state = self.state
            self.change('settings')
        elif key == 'back':
            self.change(self.previous_state)
        elif key == 'help':
            self.change('help')
        elif key == 'difficulty':
            self.difficulty = 'STANDARD' if self.difficulty == 'RELAXED' else 'RELAXED'
        elif key == 'motion':
            self.reduced_motion = not self.reduced_motion
        elif key == 'hold':
            durations = [.12, .14, .18, .26, .35]
            index = min(range(len(durations)), key=lambda i: abs(durations[i] - self.detector.hold))
            self.detector.hold = durations[(index + 1) % len(durations)]
        elif key == 'mode':
            self.mode = 'mouse' if self.mode == 'eyes' else 'eyes'
            self.detector.reset()
            if self.mode == 'eyes':
                self.tracker.start()
            else:
                self.tracker.close()
        elif key == 'aim':
            self.aim_mode = 'head' if self.aim_mode == 'iris' else 'iris'
            if self.observation.nose:
                self.head_center = self.observation.nose
            self.detector.reset()
        elif key == 'head':
            self.aim_mode = 'head'
            if self.observation.nose:
                self.head_center = self.observation.nose
            self.change('menu')
        elif key == 'retry_camera':
            self.mode = 'eyes'
            self.tracker.start()

    def button(self, key, label, rect, primary=False, subtitle=None):
        r = pygame.Rect(rect)
        pointer = self.aim if self.mode == 'eyes' else pygame.mouse.get_pos()
        hovered = r.collidepoint(pointer)
        index = len(self.buttons)
        scanned = self.mode == 'eyes' and self.state != 'playing' and index == self.scan_index
        active = hovered if self.mode == 'mouse' or self.state == 'playing' else scanned
        self.buttons.append((key, r))
        fill = v.MINT if primary else (24, 46, 56) if active else v.PANEL
        border = v.MINT if active or primary else v.LINE
        v.panel(self.screen, r, fill, border, 10, glow=active or primary)
        color = v.BG if primary else v.TEXT
        v.text(self.screen, label, (r.x + 20, r.centery - (8 if subtitle else 0)), 18, color, True, 'midleft')
        v.text(self.screen, '>' if not scanned else '●', (r.right - 22, r.centery), 18, color, False, 'center')
        if subtitle:
            v.text(self.screen, subtitle, (r.x + 20, r.centery + 17), 12, v.BG if primary else v.MUTED, anchor='midleft')
        if scanned:
            v.bar(self.screen, (r.x + 8, r.bottom - 5, r.w - 16, 3), self.scan_timer / 2.7, v.BG if primary else v.MINT)
        if self.dwell_key == key and self.dwell:
            v.bar(self.screen, (r.x + 8, r.bottom - 5, r.w - 16, 4), self.dwell / 1.3, v.AMBER)

    def menu_input(self, dt):
        if self.state == 'calibration' or self.mode != 'eyes' or not self.valid_face or self.detector.baseline is None or not self.buttons:
            return
        if self.state != 'playing':
            self.scan_index %= len(self.buttons)
            if not self.detector.closed:
                self.scan_timer += dt
                if self.scan_timer >= 2.7:
                    self.scan_timer = 0
                    self.scan_index = (self.scan_index + 1) % len(self.buttons)
                    audio.play('ui')
            if self.blink and self.t - self.entered > .4:
                index = self.scan_locked if self.scan_locked is not None else self.scan_index
                self.action(self.buttons[index % len(self.buttons)][0])
        elif not self.detector.closed:
            key = next((key for key, r in self.buttons if r.collidepoint(self.aim)), None)
            if key == self.dwell_key:
                self.dwell += dt
            else:
                self.dwell_key = key
                self.dwell = 0
            if key and self.dwell >= 1.3:
                self.action(key)

    def events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.WINDOWFOCUSLOST:
                self.focused = False
                if self.state == 'playing':
                    self.change('paused')
            elif event.type == pygame.WINDOWFOCUSGAINED:
                self.focused = True
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.action('pause' if self.state == 'playing' else 'resume' if self.state == 'paused' else 'menu')
                elif event.key == pygame.K_e:
                    self.action('mode')
                elif event.key == pygame.K_c:
                    self.start_calibration()
                elif event.key == pygame.K_UP:
                    self.speed = min(1.5, self.speed + .1)
                elif event.key == pygame.K_DOWN:
                    self.speed = max(.4, self.speed - .1)
                elif event.key == pygame.K_SPACE and self.state == 'playing' and self.mode == 'mouse':
                    if self.charging is None:
                        self.charging = self.t
                elif event.key in (pygame.K_RETURN, pygame.K_SPACE) and self.buttons and self.state != 'playing':
                    self.action(self.buttons[self.scan_index % len(self.buttons)][0])
                elif event.key == pygame.K_TAB and self.buttons:
                    self.scan_index = (self.scan_index + 1) % len(self.buttons)
                    audio.play('ui')
            elif event.type == pygame.KEYUP and event.key == pygame.K_SPACE and self.charging is not None:
                self.shoot(self.t - self.charging >= .75)
                self.charging = None
            elif event.type == pygame.MOUSEMOTION and self.mode == 'mouse':
                self.aim.update(event.pos)
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                key = next((key for key, r in self.buttons if r.collidepoint(event.pos)), None)
                if key:
                    self.action(key)
                elif self.state == 'playing' and self.mode == 'mouse':
                    self.aim.update(event.pos)
                    self.shoot()

    def camera_card(self, x, y, large=True):
        w = 340 if large else 240
        h = 232 if large else 130
        v.panel(self.screen, (x, y, w, h), glow=self.valid_face)
        obs = self.observation
        v.text(self.screen, 'OPTICAL VISION LINK', (x + 18, y + 15), 11, v.MUTED, True)
        color = v.MINT if self.valid_face else v.AMBER
        pygame.draw.circle(self.screen, color, (x + w - 22, y + 23), 5)
        if obs.preview is not None:
            if self.preview_stamp != obs.timestamp:
                self.preview_stamp = obs.timestamp
                self.preview_surface = pygame.surfarray.make_surface(obs.preview.swapaxes(0, 1))
            size = (160, 120) if large else (100, 75)
            image = pygame.transform.smoothscale(self.preview_surface, size)
            self.screen.blit(image, (x + 18, y + 43))
            pygame.draw.rect(self.screen, v.MINT if self.valid_face else v.LINE, (x + 18, y + 43, *size), 1)
        else:
            v.text(self.screen, 'CAM', (x + 62, y + 78), 22, v.MUTED, True, 'center')
            v.text(self.screen, 'NO SIGNAL', (x + 62, y + 101), 10, v.MUTED, anchor='center')
        tx = x + 198 if large else x + 134
        v.text(self.screen, 'EYES' if self.mode == 'eyes' else 'MOUSE', (tx, y + 47), 16, color, True)
        status_txt = 'CLOSED' if self.detector.closed else 'TRACKING' if self.valid_face else 'OFFLINE'
        v.text(self.screen, status_txt, (tx, y + 74), 12, v.MINT if status_txt == 'TRACKING' else v.AMBER if status_txt == 'CLOSED' else v.MUTED)
        if self.detector.baseline:
            ratio = (obs.ear or 0) / self.detector.baseline
            v.bar(self.screen, (tx, y + 102, w - (tx - x) - 18, 5), min(1, ratio))
            v.text(self.screen, f'{int(self.detector.hold * 1000)} ms hold', (tx, y + 116), 11, v.MUTED)
        if large:
            status = 'Camera off / mouse fallback ready' if self.mode == 'mouse' else 'Eyes open to track / ready' if self.valid_face else 'Checking camera access or lighting...'
            v.text(self.screen, status, (x + 18, y + 182), 12, color)
            v.text(self.screen, 'Hands-Free Precision Mode Active', (x + 18, y + 204), 11, v.MUTED)

    def footer(self):
        pygame.draw.line(self.screen, v.LINE, (48, 671), (1232, 671))
        hint = 'BLINK BRIEFLY TO SELECT HIGHLIGHTED BUTTON' if self.mode == 'eyes' else 'MOUSE AIM  /  LEFT-CLICK TO FIRE  /  HOLD SPACE TO CHARGE'
        v.text(self.screen, hint, (48, 690), 12, v.MUTED, True, 'midleft')
        v.text(self.screen, 'E  TOGGLE MODE     ESC  BACK / PAUSE', (1232, 690), 12, v.MUTED, anchor='midright')

    def draw_menu(self):
        v.background(self.screen, self.t, reduced=self.reduced_motion)
        shade = pygame.Surface((v.W, v.H), pygame.SRCALPHA)
        pygame.draw.rect(shade, (5, 12, 18, 225), (0, 0, 640, v.H))
        self.screen.blit(shade, (0, 0))
        v.text(self.screen, 'ACCESSIBLE HANDS-FREE PRECISION GAMING', (64, 46), 12, v.MINT, True)
        v.text(self.screen, 'BLINK', (60, 110), 84, v.TEXT, True)
        v.text(self.screen, 'SNIPER', (60, 192), 84, v.MINT, True)
        v.text(self.screen, 'Your eyes. Your aim. Your mission.', (66, 304), 22, v.TEXT)
        v.text(self.screen, 'Look to aim. Close both eyes briefly to take the shot.', (66, 342), 15, v.MUTED)
        self.button('start', 'START MISSION', (64, 396, 440, 66), True, 'Hands-free optical combat / Instant entry')
        self.button('help', 'HOW TO PLAY', (64, 480, 212, 52))
        self.button('settings', 'SETTINGS', (292, 480, 212, 52))
        self.button('quit', 'EXIT', (64, 550, 440, 48))

        # Right side: Interactive targeting optic circle
        cx, cy = 935, 290
        pygame.draw.circle(self.screen, (16, 32, 42), (cx, cy), 164)
        pygame.draw.circle(self.screen, v.LINE_BRIGHT, (cx, cy), 164, 2)
        pygame.draw.circle(self.screen, (40, 75, 85), (cx, cy), 146, 1)
        for angle in range(0, 360, 15):
            a = math.radians(angle)
            r = 152
            pygame.draw.line(self.screen, v.MUTED, (cx + math.cos(a) * r, cy + math.sin(a) * r), (cx + math.cos(a) * (r + 6), cy + math.sin(a) * (r + 6)), 1)
        demo = Enemy(cx, cy + 12, 'sniper', age=2, phase=1)
        v.enemy(self.screen, demo, self.t, self.reduced_motion)
        v.reticle(self.screen, (cx, cy + 12))
        v.text(self.screen, 'TACTICAL OPTICAL TARGETING', (cx, 104), 11, v.AMBER, True, 'center')
        self.camera_card(765, 410)
        self.footer()

    def draw_play(self):
        # Apply camera shake offset during combat
        sx, sy = 0, 0
        if self.shake > 0 and not self.reduced_motion:
            sx = int(math.sin(self.t * 40) * self.shake)
            sy = int(math.cos(self.t * 45) * self.shake)

        combat_surf = self.screen if (sx == 0 and sy == 0) else pygame.Surface((v.W, v.H))
        v.background(combat_surf, self.t, self.level, self.reduced_motion)

        for e in sorted(self.entities, key=lambda item: item.y):
            v.enemy(combat_surf, e, self.session_time, self.reduced_motion)

        if self.level == 3:
            # VIP Hostage with personal blue forcefield dome
            hx, hy = 1050, 270
            pygame.draw.circle(combat_surf, (20, 50, 70), (hx, hy), 26)
            pygame.draw.circle(combat_surf, v.CYAN, (hx, hy), 26, 2)
            pygame.draw.circle(combat_surf, v.TEXT, (hx, hy - 14), 9)
            pygame.draw.rect(combat_surf, (190, 205, 180), (hx - 12, hy - 4, 24, 28), border_radius=4)
            v.text(combat_surf, 'VIP PROTECT', (hx, hy - 36), 11, v.CYAN, True, 'center')

        for x, y, vx, vy, life, color in self.effects:
            pygame.draw.line(combat_surf, color, (x, y), (x - vx * .025, y - vy * .025), max(1, int(life * 5)))

        for x, y, label, life in self.popups:
            col = v.AMBER if 'HEADSHOT' in label else v.MINT if 'DOWN' in label else v.TEXT
            v.text(combat_surf, label, (x, y), 13, col, True, 'center')

        if self.shot_flash > 0 and not self.reduced_motion:
            # Supersonic glowing tracer line from bottom corner
            pygame.draw.line(combat_surf, (200, 255, 230), (v.W - 140, v.H - 90), self.aim, 2)

        if combat_surf is not self.screen:
            self.screen.blit(combat_surf, (sx, sy))

        # Scope Vignette & Optic Lens Ring
        vignette_surf = pygame.Surface((v.W, v.H), pygame.SRCALPHA)
        pygame.draw.rect(vignette_surf, (2, 8, 14, 55), (0, 0, v.W, v.H))
        self.screen.blit(vignette_surf, (0, 0))

        # Top Tactical HUD Bar
        v.panel(self.screen, (24, 20, 1232, 78), glow=True)
        v.text(self.screen, f'0{self.level}', (46, 32), 38, v.MINT, True)
        title = ['TRAINING RANGE', 'ENEMY OUTPOST', 'HOSTAGE RESCUE'][self.level - 1]
        v.text(self.screen, title, (114, 34), 18, v.TEXT, True)
        subtitle = 'Destroy all targets' if self.level == 1 else 'Protect the marked civilian / eliminate threats' if self.level == 3 else 'Counter-snipe outposts / Watch for laser warnings'
        v.text(self.screen, subtitle, (114, 62), 13, v.MUTED)
        v.text(self.screen, f'{self.kills:02} / {self.total:02}', (700, 37), 26, v.TEXT, True)
        v.text(self.screen, 'ELIMINATED', (700, 68), 10, v.MUTED)
        v.text(self.screen, f'{self.score:05}', (855, 37), 26, v.TEXT, True)
        v.text(self.screen, 'SCORE', (855, 68), 10, v.MUTED)
        self.button('pause', 'PAUSE', (1080, 34, 154, 50))

        # Bottom Optical Status HUD
        v.panel(self.screen, (24, 584, 1232, 114), glow=True)
        v.text(self.screen, 'SUIT INTEGRITY', (48, 601), 11, v.MUTED, True)
        for i in range(self.max_health):
            col = v.MINT if i < self.health else v.LINE
            pygame.draw.rect(self.screen, col, (48 + i * 24, 628, 18, 8), border_radius=2)
        v.text(self.screen, 'TRAINING (NO DMG)' if self.level == 1 else f'DIFFICULTY: {self.difficulty}', (48, 654), 11, v.MUTED)

        v.text(self.screen, 'PRECISION ACCURACY', (290, 601), 11, v.MUTED, True)
        v.text(self.screen, f'{round(self.hits / max(1, self.shots) * 100):02}%', (290, 622), 26, v.TEXT, True)
        v.text(self.screen, f'{self.shots} ROUNDS FIRED', (290, 656), 10, v.MUTED)

        # Central BLINK TRIGGER Gauge
        v.text(self.screen, 'BLINK TRIGGER (HANDS-FREE)' if self.mode == 'eyes' else 'MANUAL TRIGGER', (476, 601), 11, v.MUTED, True)
        progress = self.detector.progress if self.mode == 'eyes' else min(1, (self.t - self.charging) / .75) if self.charging is not None else 0
        v.bar(self.screen, (476, 631, 230, 8), progress, v.AMBER)
        status_label = 'HOLDING BLINK / FIRING' if self.detector.closed else 'CLOSE EYES TO SHOOT' if self.mode == 'eyes' else 'CLICK / HOLD SPACE'
        v.text(self.screen, status_label, (476, 654), 12, v.AMBER if self.detector.closed else v.MUTED, bold=self.detector.closed)

        # Vision Link / Optic Mode
        v.text(self.screen, 'OPTICAL TRACKING' if self.mode == 'eyes' else 'MOUSE BACKUP', (770, 601), 11, v.MUTED, True)
        v.text(self.screen, 'ACTIVE' if self.ready else 'WAITING FOR FACE', (770, 624), 20, v.MINT if self.ready else v.AMBER, True)
        v.text(self.screen, 'HEAD-POSE + ASSIST' if self.mode == 'eyes' else 'INPUT: MOUSE', (770, 654), 10, v.MUTED)

        v.text(self.screen, f'{self.speed:.1f}x', (1124, 618), 28, v.TEXT, True, 'center')
        v.text(self.screen, 'SIM SPEED', (1124, 652), 10, v.MUTED, anchor='center')

        # Sniper Reticle
        v.reticle(self.screen, self.aim, progress, self.hit_flash, self.detector.closed)

        # Red flash on damage
        if self.damage > 0:
            dmg_surf = pygame.Surface((v.W, v.H), pygame.SRCALPHA)
            pygame.draw.rect(dmg_surf, (*v.RED, int(self.damage * 255)), (0, 0, v.W, v.H), 6)
            self.screen.blit(dmg_surf, (0, 0))

    def draw_calibration(self):
        self.screen.fill(v.BG)
        v.text(self.screen, 'OPTICAL CALIBRATION', (48, 35), 14, v.MINT, True)
        v.text(self.screen, 'Keep your head comfortable. Follow the glowing dot with your eyes.', (640, 77), 22, v.TEXT, True, 'center')
        if self.detector.baseline is None:
            target = (640, 330)
            label = 'Keep your eyes naturally OPEN to calibrate baseline'
            progress = self.detector.calibration_progress
        else:
            nx, ny = GazeCalibration.TARGETS[min(4, self.cal_index)]
            target = (int(nx * v.W), int(ny * v.H))
            label = f'Look directly at the optic dot ({self.cal_index + 1} of 5)'
            progress = min(1, self.cal_timer / 2.2)
        pulse = 0 if self.reduced_motion else math.sin(self.t * 3.5) * 5
        pygame.draw.circle(self.screen, v.LINE, target, int(36 + pulse), 1)
        pygame.draw.circle(self.screen, v.MINT, target, 16, 2)
        pygame.draw.circle(self.screen, v.TEXT, target, 5)
        if progress > 0:
            pygame.draw.arc(self.screen, v.AMBER, (*[c - 28 for c in target], 56, 56), -math.pi / 2, -math.pi / 2 + math.tau * progress, 3)
        v.text(self.screen, label, (640, 646), 20, v.TEXT, True, 'center')
        status_msg = 'Tracking active: Follow the dot' if self.valid_face else self.observation.status[:100]
        v.text(self.screen, status_msg, (640, 690), 13, v.MUTED, anchor='center')
        self.button('menu', 'CANCEL', (1070, 646, 164, 46))

    def draw_settings(self):
        self.screen.fill(v.BG)
        v.text(self.screen, 'TACTICAL CONFIGURATION', (64, 48), 13, v.MINT, True)
        v.text(self.screen, 'Accessibility Controls', (64, 85), 46, v.TEXT, True)
        specs = [
            ('mode', f'CONTROL MODE / {self.mode.upper()}', 'Hands-free eye/head tracking or optional mouse'),
            ('aim', f'AIMING ENGINE / {"IRIS TRACKING" if self.aim_mode == "iris" else "HEAD MOVEMENT"}', 'Switch between fine iris gaze and comfortable head tilt'),
            ('hold', f'BLINK HOLD TIME / {int(self.detector.hold * 1000)} ms', 'Blink duration required to shoot (120 / 140 / 180 / 260 / 350 ms)'),
            ('difficulty', f'DIFFICULTY / {self.difficulty}', 'Relaxed gives more armor integrity and slower enemy attacks'),
            ('motion', f'REDUCED MOTION / {"ON" if self.reduced_motion else "OFF"}', 'Disable camera recoil shake, screen pulse, and character bob')
        ]
        for i, (key, label, sub) in enumerate(specs):
            self.button(key, label, (64, 168 + i * 78, 650, 66), subtitle=sub)
        self.camera_card(824, 168)
        self.button('calibrate', 'RECALIBRATE VISION', (824, 420, 340, 54))
        self.button('retry_camera', 'RECONNECT CAMERA', (824, 492, 340, 54))
        self.button('back', 'SAVE & RETURN', (64, 592, 650, 54), True)
        self.footer()

    def draw_overlay(self):
        v.background(self.screen, self.t, reduced=self.reduced_motion)
        shade = pygame.Surface((v.W, v.H), pygame.SRCALPHA)
        shade.fill((4, 12, 18, 220))
        self.screen.blit(shade, (0, 0))
        titles = {
            'paused': ('MISSION PAUSED', 'Take your time. Your tactical status is saved.'),
            'complete': ('SECTOR SECURED', 'All targets neutralized. Next mission is ready.'),
            'won': ('CAMPAIGN COMPLETE', 'All sectors cleared. Civilian secured. Outstanding precision.'),
            'lost': ('MISSION FAILED', 'Armor depleted. Settle in and try again.'),
            'hostage_lost': ('CIVILIAN DOWN', 'Protect the marked friendly VIP. Try the mission again.'),
            'calibration_done': ('VISION CALIBRATED', 'Look to aim. Close both eyes briefly to shoot.'),
            'calibration_failed': ('CALIBRATION TIMEOUT', 'Use comfortable head aiming or adjust lighting.'),
            'help': ('HANDS-FREE FIELD MANUAL', 'No hands required. Your eyes are your sniper optic.')
        }
        title, subtitle = titles.get(self.state, ('TACTICAL STATUS', 'Proceed when ready.'))
        v.text(self.screen, 'BLINK SNIPER / ACCESSIBLE PRECISION', (640, 80), 12, v.MINT, True, 'center')
        v.text(self.screen, title, (640, 138), 38, v.TEXT, True, 'center')
        v.text(self.screen, subtitle, (640, 190), 18, v.MUTED, anchor='center')
        choices = []
        if self.state == 'help':
            for i, (a, b) in enumerate([
                ('01 / LOOK TO AIM', 'Move your head or eyes gently. The reticle follows your gaze.'),
                ('02 / BLINK TO SHOOT', 'Close both eyes for 140ms. A subtle beep confirms, then fires.'),
                ('03 / HANDS-FREE MENUS', 'Buttons highlight automatically. Close your eyes to select.'),
                ('04 / PAUSE & REST', 'Look at PAUSE for 1.3 seconds or press ESC to take a break.')
            ]):
                v.text(self.screen, a, (220, 245 + i * 68), 14, v.MINT, True)
                v.text(self.screen, b, (220, 269 + i * 68), 16, v.TEXT)
            choices = [('menu', 'BACK TO MENU')]
        elif self.state == 'calibration_failed':
            v.text(self.screen, 'Head-pose aiming works automatically without 5-point calibration.', (640, 260), 16, v.TEXT, anchor='center')
            v.text(self.screen, 'You can start missions immediately with comfortable head tracking.', (640, 290), 15, v.MUTED, anchor='center')
            choices = [('head', 'USE COMFORTABLE HEAD AIM'), ('calibrate', 'TRY CALIBRATION AGAIN'), ('menu', 'BACK TO MENU')]
        elif self.state == 'calibration_done':
            choices = [('deploy', 'RESUME MISSION' if self.cal_resume else 'START MISSION'), ('calibrate', 'CALIBRATE AGAIN'), ('menu', 'BACK TO MENU')]
        elif self.state == 'paused':
            choices = [('resume', 'RESUME MISSION'), ('settings', 'SETTINGS'), ('menu', 'EXIT TO MENU')]
        elif self.state == 'complete':
            choices = [('next', 'PROCEED TO NEXT MISSION'), ('menu', 'BACK TO MENU')]
        else:
            choices = [('deploy', 'PLAY AGAIN'), ('settings', 'SETTINGS'), ('menu', 'BACK TO MENU')]

        if self.state in ('complete', 'won', 'lost', 'hostage_lost'):
            for x, a, b in [(410, 'FINAL SCORE', f'{self.score:05}'), (640, 'ACCURACY', f'{round(self.hits / max(1, self.shots) * 100)}%'), (870, 'TOTAL SHOTS', str(self.shots))]:
                v.text(self.screen, a, (x, 265), 12, v.MUTED, anchor='center')
                v.text(self.screen, b, (x, 305), 36, v.MINT, True, 'center')
        start = 580 if self.state == 'help' else 370
        for i, (key, label) in enumerate(choices):
            self.button(key, label, (420, start + i * 74, 440, 58), i == 0)
        self.footer()

    def draw(self):
        self.buttons = []
        if self.state == 'menu':
            self.draw_menu()
        elif self.state == 'playing':
            self.draw_play()
        elif self.state == 'settings':
            self.draw_settings()
        elif self.state == 'calibration':
            self.draw_calibration()
        else:
            self.draw_overlay()
        if self.message_until > self.t:
            v.panel(self.screen, (290, 109, 700, 50))
            v.text(self.screen, self.message, (640, 134), 16, v.AMBER, anchor='center')

    def run(self):
        try:
            while self.running:
                dt = min(.05, self.clock.tick(60) / 1000)
                self.events()
                self.update(dt)
                self.draw()
                self.menu_input(dt)
                pygame.display.flip()
        finally:
            self.tracker.close()
            pygame.quit()


def main():
    parser = argparse.ArgumentParser(description='Blink Sniper / eyes-first accessible sniper game')
    parser.add_argument('--no-camera', action='store_true', help='Start in mouse mode without opening the camera')
    parser.add_argument('--camera', type=int, default=0, help='Camera device index')
    parser.add_argument('--preview', type=Path, help='Render screenshots headlessly into this directory')
    args = parser.parse_args()
    if args.preview:
        os.environ['SDL_VIDEODRIVER'] = 'dummy'
        os.environ['SDL_AUDIODRIVER'] = 'dummy'
    game = Game(not args.no_camera and not args.preview, args.camera)
    if args.preview:
        args.preview.mkdir(parents=True, exist_ok=True)
        game.t = 4
        for state in ('menu', 'playing', 'settings', 'calibration', 'help', 'complete'):
            game.state = state
            if state == 'playing':
                game.level = 2
                game.spawn()
                for e in game.entities:
                    e.age = 2
            game.draw()
            pygame.image.save(game.screen, str(args.preview / f'{state}.png'))
        game.tracker.close()
        pygame.quit()
    else:
        game.run()


if __name__ == '__main__':
    main()
