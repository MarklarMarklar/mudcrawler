import pygame
import os
import sys

# Add the scripts directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), "scripts"))

# Import necessary modules
from config import *
from asset_manager import get_asset_manager

# Initialize Pygame
pygame.init()
screen = pygame.display.set_mode((800, 600))
pygame.display.set_caption("Key Size Test")

# Get asset manager
asset_manager = get_asset_manager()

# Key image path
key_path = os.path.join(ASSET_PATH, "icons/key.png")

# Load key at full size and 50% size
key_full = asset_manager.load_image(key_path, scale=(TILE_SIZE, TILE_SIZE))
key_half = asset_manager.load_image(key_path, scale=(TILE_SIZE//2, TILE_SIZE//2))

print(f"Full size key dimensions: {key_full.get_width()}x{key_full.get_height()}")
print(f"Half size key dimensions: {key_half.get_width()}x{key_half.get_height()}")

# Main loop
running = True
clock = pygame.time.Clock()

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
    
    # Clear screen
    screen.fill((0, 0, 0))
    
    # Draw full size key on left
    screen.blit(key_full, (200, 300))
    
    # Draw half size key on right
    screen.blit(key_half, (500, 300))
    
    # Add labels
    font = pygame.font.SysFont("Arial", 20)
    full_label = font.render("Full Size", True, (255, 255, 255))
    half_label = font.render("Half Size (50%)", True, (255, 255, 255))
    screen.blit(full_label, (170, 250))
    screen.blit(half_label, (470, 250))
    
    # Update display
    pygame.display.flip()
    clock.tick(60)

pygame.quit()
sys.exit() 