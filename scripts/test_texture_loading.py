import pygame
import os
import sys

# Add the parent directory to the path so we can import config
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import *

def test_texture_loading():
    pygame.init()
    
    # Set up a small display
    screen = pygame.display.set_mode((400, 400))
    pygame.display.set_caption("Texture Loading Test")
    
    # Print paths for debugging
    print(f"Current working directory: {os.getcwd()}")
    print(f"Asset path: {ASSET_PATH}")
    print(f"Player sprites path: {PLAYER_SPRITES_PATH}")
    print(f"Absolute player sprites path: {os.path.abspath(PLAYER_SPRITES_PATH)}")
    
    # List files in the player sprites directory
    print("\nFiles in player sprites directory:")
    if os.path.exists(PLAYER_SPRITES_PATH):
        for file in os.listdir(PLAYER_SPRITES_PATH):
            print(f"  - {file}")
    else:
        print(f"Directory does not exist: {PLAYER_SPRITES_PATH}")
    
    # Try to load each player texture
    print("\nAttempting to load player textures:")
    textures = {}
    for direction in ['down', 'up', 'left', 'right']:
        texture_path = os.path.join(PLAYER_SPRITES_PATH, f"player_{direction}.png")
        print(f"\nTrying to load: {texture_path}")
        print(f"File exists? {os.path.exists(texture_path)}")
        
        try:
            texture = pygame.image.load(texture_path)
            textures[direction] = texture
            print(f"Successfully loaded {direction} texture")
            # Display the texture size
            print(f"Texture size: {texture.get_width()}x{texture.get_height()}")
        except Exception as e:
            print(f"Failed to load {direction} texture: {e}")
    
    # Display loaded textures if any
    if textures:
        running = True
        x, y = 50, 50
        spacing = 100
        
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
            
            screen.fill((0, 0, 0))
            
            # Draw each texture
            for i, (direction, texture) in enumerate(textures.items()):
                pos_x = x + (i % 2) * spacing
                pos_y = y + (i // 2) * spacing
                screen.blit(texture, (pos_x, pos_y))
                
                # Draw direction label
                font = pygame.font.Font(None, 24)
                label = font.render(direction, True, (255, 255, 255))
                screen.blit(label, (pos_x, pos_y + 70))
            
            pygame.display.flip()
            pygame.time.wait(100)
    else:
        print("No textures were loaded successfully.")
        pygame.time.wait(3000)
    
    pygame.quit()

if __name__ == "__main__":
    test_texture_loading() 