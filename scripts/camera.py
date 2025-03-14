import pygame
from config import *

class Camera:
    def __init__(self, width, height):
        # Camera dimensions (same as window dimensions)
        self.width = width
        self.height = height
        
        # Camera position (top-left corner in world coordinates)
        self.x = 0
        self.y = 0
        
        # Zoom factor (2.0 = 200% zoom)
        self.zoom = 2.0
        
        # Effective view dimensions (adjusted for zoom)
        self.view_width = self.width / self.zoom
        self.view_height = self.height / self.zoom
    
    def update(self, target_x, target_y):
        """Update camera position to follow a target"""
        # Calculate center of viewport
        self.x = target_x - self.view_width / 2
        self.y = target_y - self.view_height / 2
        
        # Ensure camera doesn't go out of bounds of the current room
        room_width_pixels = ROOM_WIDTH * TILE_SIZE
        room_height_pixels = ROOM_HEIGHT * TILE_SIZE
        
        # If room is smaller than view, center the view
        if room_width_pixels < self.view_width:
            self.x = (room_width_pixels - self.view_width) / 2
        else:
            # Otherwise, clamp camera position
            self.x = max(0, min(self.x, room_width_pixels - self.view_width))
            
        if room_height_pixels < self.view_height:
            self.y = (room_height_pixels - self.view_height) / 2
        else:
            self.y = max(0, min(self.y, room_height_pixels - self.view_height))
    
    def apply(self, rect):
        """Convert world coordinates to screen coordinates"""
        # Apply zoom and offset
        screen_rect = pygame.Rect(
            (rect.x - self.x) * self.zoom,
            (rect.y - self.y) * self.zoom,
            rect.width * self.zoom,
            rect.height * self.zoom
        )
        return screen_rect
    
    def apply_pos(self, x, y):
        """Convert world coordinates to screen coordinates"""
        screen_x = (x - self.x) * self.zoom
        screen_y = (y - self.y) * self.zoom
        return (screen_x, screen_y)
    
    def apply_surface(self, surface):
        """Scale a surface according to zoom factor"""
        width = int(surface.get_width() * self.zoom)
        height = int(surface.get_height() * self.zoom)
        return pygame.transform.scale(surface, (width, height))
        
    def center_on_point(self, x, y):
        """Center the camera view on a specific point in world coordinates"""
        # Calculate position to center the view on the specified point
        self.x = x - self.view_width / 2
        self.y = y - self.view_height / 2
        
        # Ensure camera doesn't go out of bounds of the current room
        room_width_pixels = ROOM_WIDTH * TILE_SIZE
        room_height_pixels = ROOM_HEIGHT * TILE_SIZE
        
        # If room is smaller than view, center the view
        if room_width_pixels < self.view_width:
            self.x = (room_width_pixels - self.view_width) / 2
        else:
            # Otherwise, clamp camera position
            self.x = max(0, min(self.x, room_width_pixels - self.view_width))
            
        if room_height_pixels < self.view_height:
            self.y = (room_height_pixels - self.view_height) / 2
        else:
            self.y = max(0, min(self.y, room_height_pixels - self.view_height))
            
        # Ensure coordinates are integers to avoid subsurface issues
        self.x = int(self.x)
        self.y = int(self.y) 