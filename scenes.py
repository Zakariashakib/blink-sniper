import pygame
from settings import *
from ui import Button, HUD
import math
import random

class SceneManager:
    def __init__(self):
        self.scenes = {}
        self.active_scene = None

    def add_scene(self, name, scene):
        self.scenes[name] = scene

    def set_scene(self, name):
        if name in self.scenes:
            self.active_scene = self.scenes[name]
            self.active_scene.on_enter()

    def handle_event(self, event):
        if self.active_scene:
            self.active_scene.handle_event(event)

    def update(self):
        if self.active_scene:
            self.active_scene.update()

    def draw(self, surface):
        if self.active_scene:
            self.active_scene.draw(surface)

class BaseScene:
    def __init__(self, manager):
        self.manager = manager

    def on_enter(self):
        pass

    def handle_event(self, event):
        pass

    def update(self):
        pass

    def draw(self, surface):
        pass

class MenuScene(BaseScene):
    def __init__(self, manager):
        super().__init__(manager)
        self.buttons = []
        btn_w, btn_h = 300, 60
        start_y = HEIGHT // 2
        
        self.buttons.append(Button(WIDTH//2 - btn_w//2, start_y, btn_w, btn_h, "Start Game"))
        self.buttons.append(Button(WIDTH//2 - btn_w//2, start_y + 80, btn_w, btn_h, "How to Play"))
        self.buttons.append(Button(WIDTH//2 - btn_w//2, start_y + 160, btn_w, btn_h, "Settings"))
        self.buttons.append(Button(WIDTH//2 - btn_w//2, start_y + 240, btn_w, btn_h, "Exit"))
        
        self.title_font = pygame.font.SysFont(FONT_NAME, 80, bold=True)
        self.fade_alpha = 255

    def on_enter(self):
        self.fade_alpha = 255

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for btn in self.buttons:
                if btn.is_hovered:
                    if btn.text == "Start Game":
                        self.manager.set_scene("level1")
                    elif btn.text == "How to Play":
                        self.manager.set_scene("howtoplay")
                    elif btn.text == "Exit":
                        pygame.event.post(pygame.event.Event(pygame.QUIT))

    def update(self):
        mouse_pos = pygame.mouse.get_pos()
        for btn in self.buttons:
            btn.update(mouse_pos)
            
        if self.fade_alpha > 0:
            self.fade_alpha -= 5

    def draw(self, surface):
        surface.fill(BG_COLOR)
        
        # Draw Title
        title_surf = self.title_font.render("BLINK SNIPER", True, NEON_GREEN)
        title_rect = title_surf.get_rect(center=(WIDTH//2, HEIGHT//3 - 50))
        surface.blit(title_surf, title_rect)
        
        for btn in self.buttons:
            btn.draw(surface)
            
        # Draw fade-in overlay
        if self.fade_alpha > 0:
            fade_surf = pygame.Surface((WIDTH, HEIGHT))
            fade_surf.fill(BG_COLOR)
            fade_surf.set_alpha(max(0, self.fade_alpha))
            surface.blit(fade_surf, (0, 0))

class HowToPlayScene(BaseScene):
    def __init__(self, manager):
        super().__init__(manager)
        self.back_btn = Button(WIDTH//2 - 150, HEIGHT - 100, 300, 60, "Back to Menu")
        self.title_font = pygame.font.SysFont(FONT_NAME, 64, bold=True)
        self.heading_font = pygame.font.SysFont(FONT_NAME, 32, bold=True)
        self.text_font = pygame.font.SysFont(FONT_NAME, 24)
        
        self.instructions = [
            ("CONTROLS", [
                "MOUSE MOVE  -  Move crosshair",
                "SPACE (HOLD)  -  Charge blink shot",
                "SPACE (RELEASE)  -  Fire charged shot",
                "E  -  Toggle Eye Tracking / Mouse Mode",
            ]),
            ("HOW TO PLAY", [
                "Hold SPACE to charge your blink ability",
                "Release SPACE to shoot at the crosshair position",
                "Longer charge = bigger explosion radius",
                "Destroy all red targets to complete the level",
            ]),
            ("TIPS", [
                "Aim for the center of targets for best accuracy",
                "Fully charged shots (red ring) hit a larger area",
                "You have 3 health points - don't waste shots!",
                "Eye Tracking mode lets you aim with your eyes",
            ]),
        ]

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.back_btn.is_hovered:
                self.manager.set_scene("menu")
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.manager.set_scene("menu")

    def update(self):
        mouse_pos = pygame.mouse.get_pos()
        self.back_btn.update(mouse_pos)

    def draw(self, surface):
        surface.fill(BG_COLOR)
        
        # Title
        title = self.title_font.render("HOW TO PLAY", True, NEON_GREEN)
        title_rect = title.get_rect(center=(WIDTH//2, 60))
        surface.blit(title, title_rect)
        
        # Draw instructions in columns/rows
        y_offset = 130
        for heading, lines in self.instructions:
            heading_surf = self.heading_font.render(heading, True, WHITE)
            surface.blit(heading_surf, (WIDTH//2 - heading_surf.get_width()//2, y_offset))
            y_offset += 40
            
            for line in lines:
                line_surf = self.text_font.render(line, True, GRAY)
                surface.blit(line_surf, (WIDTH//2 - line_surf.get_width()//2, y_offset))
                y_offset += 30
            
            y_offset += 20
        
        self.back_btn.draw(surface)

class LevelScene(BaseScene):
    def __init__(self, manager, level_data):
        super().__init__(manager)
        self.level_name = level_data['name']
        self.objective = level_data['objective']
        self.total_targets = level_data['targets']
        self.hud = HUD(self.level_name, self.objective)
        
        self.targets_left = self.total_targets
        self.shots_fired = 0
        self.hits = 0
        self.health = 3
        
        self.crosshair_pos = [WIDTH//2, HEIGHT//2]
        self.is_eye_tracking = False
        
        # Blink tracking simulation
        self.blink_start_time = 0
        self.is_blinking = False
        self.charge_level = 0.0
        
        # Simple targets list: [(x, y, radius, alive)]
        self.targets = []
        for _ in range(self.total_targets):
            tx = random.randint(100, WIDTH - 100)
            ty = random.randint(150, HEIGHT - 150)
            self.targets.append([tx, ty, 30, True])
            
        self.font = pygame.font.SysFont(FONT_NAME, 40, bold=True)
        self.game_over = False
        self.flash_alpha = 0

    def on_enter(self):
        pass

    def get_accuracy(self):
        if self.shots_fired == 0:
            return 100
        return int((self.hits / self.shots_fired) * 100)

    def handle_event(self, event):
        if self.game_over:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
                self.manager.set_scene("menu")
            return

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_e:
                self.is_eye_tracking = not self.is_eye_tracking
            elif event.key == pygame.K_SPACE:
                # Simulate blink start
                self.is_blinking = True
                self.blink_start_time = pygame.time.get_ticks()

        elif event.type == pygame.KEYUP:
            if event.key == pygame.K_SPACE and self.is_blinking:
                # Simulate blink end -> shoot
                self.is_blinking = False
                self.shoot()
                self.charge_level = 0.0

    def shoot(self):
        self.shots_fired += 1
        self.flash_alpha = 255 # Screen flash
        
        # Check if charged
        is_charged = self.charge_level >= 0.9
        damage_radius = 50 if is_charged else 20
        
        hit_something = False
        for t in self.targets:
            if t[3]: # if alive
                dist = math.hypot(self.crosshair_pos[0] - t[0], self.crosshair_pos[1] - t[1])
                if dist < t[2] + damage_radius:
                    t[3] = False
                    self.hits += 1
                    self.targets_left -= 1
                    hit_something = True
                    
        if self.targets_left <= 0:
            self.game_over = True

    def update(self):
        if self.game_over:
            return
            
        if not self.is_eye_tracking:
            self.crosshair_pos = list(pygame.mouse.get_pos())
            
        # Update charge level
        if self.is_blinking:
            elapsed = pygame.time.get_ticks() - self.blink_start_time
            # Max charge at 750ms
            self.charge_level = min(1.0, elapsed / 750.0)
            
        if self.flash_alpha > 0:
            self.flash_alpha -= 15

    def draw(self, surface):
        surface.fill(BG_COLOR)
        
        # Draw targets
        for t in self.targets:
            if t[3]:
                pygame.draw.circle(surface, RED, (t[0], t[1]), t[2])
                pygame.draw.circle(surface, WHITE, (t[0], t[1]), t[2] - 5, 2)
                
        # Draw crosshair
        cx, cy = int(self.crosshair_pos[0]), int(self.crosshair_pos[1])
        pygame.draw.line(surface, NEON_GREEN, (cx - 20, cy), (cx + 20, cy), 2)
        pygame.draw.line(surface, NEON_GREEN, (cx, cy - 20), (cx, cy + 20), 2)
        pygame.draw.circle(surface, NEON_GREEN, (cx, cy), 10, 1)
        
        if self.charge_level > 0:
            pygame.draw.circle(surface, (255, 255, 0), (cx, cy), int(20 + self.charge_level * 20), 2)
            
        # Screen flash
        if self.flash_alpha > 0:
            flash_surf = pygame.Surface((WIDTH, HEIGHT))
            flash_surf.fill(WHITE)
            flash_surf.set_alpha(self.flash_alpha)
            surface.blit(flash_surf, (0, 0))
            
        self.hud.draw(surface, self.targets_left, self.total_targets, self.get_accuracy(), self.hits * 100, self.health, self.charge_level, self.is_eye_tracking)
        
        if self.game_over:
            overlay = pygame.Surface((WIDTH, HEIGHT))
            overlay.fill((0, 0, 0))
            overlay.set_alpha(150)
            surface.blit(overlay, (0, 0))
            
            end_text = self.font.render("LEVEL COMPLETE!" if self.targets_left <= 0 else "GAME OVER", True, NEON_GREEN)
            surface.blit(end_text, end_text.get_rect(center=(WIDTH//2, HEIGHT//2 - 50)))
            
            sub_text = self.font.render("Press ENTER to return to Menu", True, WHITE)
            surface.blit(sub_text, sub_text.get_rect(center=(WIDTH//2, HEIGHT//2 + 50)))
