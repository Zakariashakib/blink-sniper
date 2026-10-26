import pygame
from settings import *

class Button:
    def __init__(self, x, y, width, height, text, font_size=40):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.font = pygame.font.SysFont(FONT_NAME, font_size, bold=True)
        self.base_color = DARK_GRAY
        self.hover_color = NEON_GREEN
        self.text_color = WHITE
        self.hovered_text_color = BG_COLOR
        self.is_hovered = False
        
        # For smooth scaling/animation (simplified approach for Pygame)
        self.scale_factor = 1.0
        self.target_scale = 1.0
        self.current_rect = self.rect.copy()

    def update(self, mouse_pos):
        self.is_hovered = self.rect.collidepoint(mouse_pos)
        
        if self.is_hovered:
            self.target_scale = 1.05
        else:
            self.target_scale = 1.0
            
        # Smooth scaling approach
        self.scale_factor += (self.target_scale - self.scale_factor) * 0.2
        
        # Calculate new rect based on scale
        new_w = int(self.rect.width * self.scale_factor)
        new_h = int(self.rect.height * self.scale_factor)
        self.current_rect.width = new_w
        self.current_rect.height = new_h
        self.current_rect.center = self.rect.center

    def draw(self, surface):
        color = self.hover_color if self.is_hovered else self.base_color
        text_col = self.hovered_text_color if self.is_hovered else self.text_color
        
        # Draw button background
        pygame.draw.rect(surface, color, self.current_rect, border_radius=8)
        
        # Draw text
        text_surf = self.font.render(self.text, True, text_col)
        text_rect = text_surf.get_rect(center=self.current_rect.center)
        surface.blit(text_surf, text_rect)

class HUD:
    def __init__(self, level_name, objective):
        self.level_name = level_name
        self.objective = objective
        self.font_large = pygame.font.SysFont(FONT_NAME, 36, bold=True)
        self.font_medium = pygame.font.SysFont(FONT_NAME, 24)
        self.font_small = pygame.font.SysFont(FONT_NAME, 18)
        
    def draw(self, surface, targets_left, total_targets, accuracy, score, health, charge_level, eye_tracking_enabled):
        # Top Left: Level info
        lvl_text = self.font_large.render(self.level_name, True, NEON_GREEN)
        obj_text = self.font_medium.render(self.objective, True, WHITE)
        surface.blit(lvl_text, (20, 20))
        surface.blit(obj_text, (20, 60))
        
        # Top Right: Stats
        stats_text = f"Targets: {targets_left}/{total_targets}   Acc: {accuracy}%   Score: {score}"
        stats_surf = self.font_medium.render(stats_text, True, WHITE)
        surface.blit(stats_surf, (WIDTH - stats_surf.get_width() - 20, 20))
        
        # Eye Tracking Status
        et_color = NEON_GREEN if eye_tracking_enabled else GRAY
        et_text = "Eye Tracking: " + ("ON" if eye_tracking_enabled else "OFF (Mouse Mode)")
        et_surf = self.font_small.render(et_text, True, et_color)
        surface.blit(et_surf, (WIDTH - et_surf.get_width() - 20, 60))
        
        # Bottom Left: Health
        health_text = self.font_medium.render("Health:", True, WHITE)
        surface.blit(health_text, (20, HEIGHT - 50))
        for i in range(3):
            color = RED if i < health else DARK_GRAY
            pygame.draw.circle(surface, color, (120 + i * 40, HEIGHT - 35), 15)
            
        # Bottom Right: Blink Charge Bar
        charge_text = self.font_medium.render("Blink Charge:", True, WHITE)
        surface.blit(charge_text, (WIDTH - 300, HEIGHT - 50))
        
        bar_bg = pygame.Rect(WIDTH - 150, HEIGHT - 50, 130, 20)
        pygame.draw.rect(surface, DARK_GRAY, bar_bg, border_radius=10)
        
        if charge_level > 0:
            bar_fill = pygame.Rect(WIDTH - 150, HEIGHT - 50, int(130 * charge_level), 20)
            if charge_level < 0.5:
                charge_col = NEON_GREEN
            elif charge_level < 0.9:
                charge_col = (255, 255, 0) # Yellow
            else:
                charge_col = RED
            pygame.draw.rect(surface, charge_col, bar_fill, border_radius=10)
