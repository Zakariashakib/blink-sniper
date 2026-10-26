import pygame
import sys
from settings import *
from scenes import SceneManager, MenuScene, LevelScene, HowToPlayScene

def main():
    pygame.init()
    pygame.mixer.init()
    
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Blink Sniper")
    clock = pygame.time.Clock()
    
    scene_manager = SceneManager()
    
    # Add scenes
    scene_manager.add_scene("menu", MenuScene(scene_manager))
    scene_manager.add_scene("howtoplay", HowToPlayScene(scene_manager))
    scene_manager.add_scene("level1", LevelScene(scene_manager, {
        "name": "Level 1: Training Range",
        "objective": "Destroy 10 targets. Space to aim/blink.",
        "targets": 10
    }))
    
    # Set initial scene
    scene_manager.set_scene("menu")
    
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            
            scene_manager.handle_event(event)
            
        scene_manager.update()
        
        scene_manager.draw(screen)
        
        pygame.display.flip()
        clock.tick(FPS)
        
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
