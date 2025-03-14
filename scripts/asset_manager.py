import pygame
import os
import sys

# Add the parent directory to the path so we can import config
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import *

class AssetManager:
    def __init__(self):
        self.images = {}
        self.animations = {}
        self.sounds = {}
        
    def load_image(self, path, scale=None, convert_alpha=True):
        """Load an image, cache it, and return it."""
        if path in self.images:
            return self.images[path]
            
        try:
            if convert_alpha:
                image = pygame.image.load(path).convert_alpha()
            else:
                image = pygame.image.load(path).convert()
                
            if scale:
                image = pygame.transform.scale(image, scale)
                
            self.images[path] = image
            return image
        except pygame.error as e:
            print(f"Error loading image {path}: {e}")
            print(f"Full path attempted: {os.path.abspath(path)}")
            print(f"Directory exists? {os.path.exists(os.path.dirname(path))}")
            print(f"File exists? {os.path.exists(path)}")
            
            # Create a colorful placeholder for missing textures
            placeholder = pygame.Surface((TILE_SIZE, TILE_SIZE))
            placeholder.fill((255, 0, 255))  # Magenta for missing textures
            
            # Add a cross pattern to make it obvious it's a missing texture
            pygame.draw.line(placeholder, (0, 0, 0), (0, 0), (TILE_SIZE, TILE_SIZE), 2)
            pygame.draw.line(placeholder, (0, 0, 0), (0, TILE_SIZE), (TILE_SIZE, 0), 2)
            
            self.images[path] = placeholder
            return placeholder
            
    def load_animation(self, folder_path, prefix, num_frames, extension=".png", scale=None):
        """Load a series of images for an animation, cache it, and return it."""
        if folder_path in self.animations:
            return self.animations[folder_path]
            
        frames = []
        for i in range(num_frames):
            filename = f"{prefix}{i}{extension}"
            filepath = os.path.join(folder_path, filename)
            frames.append(self.load_image(filepath, scale=scale))
            
        self.animations[folder_path] = frames
        return frames
        
    def load_tile_set(self, path, tile_width, tile_height):
        """Load a tileset and split it into individual tiles."""
        tileset_image = self.load_image(path)
        width, height = tileset_image.get_size()
        
        tiles = []
        for y in range(0, height, tile_height):
            for x in range(0, width, tile_width):
                rect = pygame.Rect(x, y, tile_width, tile_height)
                tile = tileset_image.subsurface(rect)
                tiles.append(tile)
                
        return tiles
        
    def load_sound(self, path):
        """Load a sound, cache it, and return it."""
        if path in self.sounds:
            return self.sounds[path]
            
        try:
            sound = pygame.mixer.Sound(path)
            self.sounds[path] = sound
            return sound
        except pygame.error as e:
            print(f"Error loading sound {path}: {e}")
            return None

# Create a global instance that can be imported by other modules
asset_manager = AssetManager()

def get_asset_manager():
    """Get the global asset manager instance."""
    return asset_manager 