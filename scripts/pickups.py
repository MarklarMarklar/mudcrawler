import pygame
import math
import os
import random
from config import *
from asset_manager import get_asset_manager

class BasePickup:
    """Base class for all pickups in the game"""
    def __init__(self, x, y, size=TILE_SIZE // 2):
        self.x = x
        self.y = y
        self.size = size
        self.rect = pygame.Rect(x - self.size//2, y - self.size//2, self.size, self.size)
        self.collected = False
        self.pulse_timer = 0
        self.asset_manager = get_asset_manager()
    
    def update(self):
        """Update the pickup animation"""
        self.pulse_timer += 0.1
    
    def draw(self, surface):
        """Base draw method - should be overridden by subclasses"""
        if self.collected:
            return


class ArrowPickup(BasePickup):
    """Arrow pickup item that gives the player additional arrows"""
    def __init__(self, x, y):
        super().__init__(x, y)
        self.arrow_amount = 2  # Each pickup gives 2 arrows
        
        # Try to load arrow texture
        try:
            arrow_path = os.path.join(WEAPON_SPRITES_PATH, "rock.png")
            if os.path.exists(arrow_path):
                self.arrow_texture = self.asset_manager.load_image(arrow_path, scale=(self.size, self.size))
            else:
                self.arrow_texture = None
        except Exception as e:
            print(f"Failed to load arrow texture: {e}")
            self.arrow_texture = None
        
    def draw(self, surface):
        if self.collected:
            return
            
        try:
            # Pulsing effect
            pulse = math.sin(self.pulse_timer) * 0.2 + 0.8
            size = int(self.size * pulse)
            
            # Draw arrow pickup
            if self.arrow_texture:
                # Scale the texture based on pulse
                scaled_texture = pygame.transform.scale(self.arrow_texture, (size, size))
                # Draw centered at pickup position
                rect = scaled_texture.get_rect(center=(self.x, self.y))
                surface.blit(scaled_texture, rect)
            else:
                # Draw a fallback arrow shape if texture isn't available
                pygame.draw.circle(surface, BLUE, (self.x, self.y), size // 2)
                pygame.draw.polygon(surface, WHITE, [
                    (self.x, self.y - size // 2),
                    (self.x - size // 4, self.y + size // 4),
                    (self.x + size // 4, self.y + size // 4)
                ])
                
            # Add a glow effect
            glow_surf = pygame.Surface((size * 3, size * 3), pygame.SRCALPHA)
            pygame.draw.circle(glow_surf, (*BLUE[:3], 70), (size * 1.5, size * 1.5), size * pulse)
            glow_rect = glow_surf.get_rect(center=(self.x, self.y))
            surface.blit(glow_surf, glow_rect)
        except Exception as e:
            print(f"Error rendering arrow pickup: {e}")


class HealthPickup(BasePickup):
    """Health pickup item that restores player health"""
    def __init__(self, x, y):
        super().__init__(x, y)
        self.heal_amount = 20  # Flat 20 HP instead of percentage-based healing
        
        # Try to load health pickup texture
        try:
            health_path = os.path.join(WEAPON_SPRITES_PATH, "health_pickup.png")
            if os.path.exists(health_path):
                self.health_texture = self.asset_manager.load_image(health_path, scale=(self.size, self.size))
            else:
                self.health_texture = None
        except Exception as e:
            print(f"Failed to load health pickup texture: {e}")
            self.health_texture = None
        
    def draw(self, surface):
        if self.collected:
            return
            
        try:
            # Pulsing effect
            pulse = math.sin(self.pulse_timer) * 0.2 + 0.8
            size = int(self.size * pulse)
            
            # Create a surface for the heart shape
            heart_surf = pygame.Surface((size, size), pygame.SRCALPHA)
            
            # Draw a red heart shape
            heart_color = (255, 0, 0, 200)  # Semi-transparent red
            
            # Draw heart using 2 circles and a triangle
            radius = size // 4
            x_offset = size // 4
            pygame.draw.circle(heart_surf, heart_color, (x_offset, radius), radius)  # Left circle
            pygame.draw.circle(heart_surf, heart_color, (size - x_offset, radius), radius)  # Right circle
            
            # Triangle for bottom of heart
            pygame.draw.polygon(heart_surf, heart_color, [
                (0, radius),
                (size // 2, size),
                (size, radius)
            ])
            
            # Add a glow effect
            glow_surf = pygame.Surface((size * 3, size * 3), pygame.SRCALPHA)
            glow_color = (255, 100, 100, 100)
            pygame.draw.circle(glow_surf, glow_color, (size * 1.5, size * 1.5), size * pulse)
            
            # Blit heart and glow to main surface
            heart_rect = heart_surf.get_rect(center=(self.x, self.y))
            glow_rect = glow_surf.get_rect(center=(self.x, self.y))
            
            surface.blit(glow_surf, glow_rect)
            surface.blit(heart_surf, heart_rect)
        except Exception as e:
            print(f"Error rendering health pickup: {e}")


class KeyPickup(BasePickup):
    """Key pickup that unlocks doors"""
    def __init__(self, x, y):
        super().__init__(x, y)
        
        # Try to load key texture
        try:
            key_path = os.path.join(WEAPON_SPRITES_PATH, "key.png")
            if os.path.exists(key_path):
                self.key_texture = self.asset_manager.load_image(key_path, scale=(self.size, self.size))
            else:
                self.key_texture = None
        except Exception as e:
            print(f"Failed to load key texture: {e}")
            self.key_texture = None
        
    def draw(self, surface):
        if self.collected:
            return
            
        try:
            # Pulsing effect
            pulse = math.sin(self.pulse_timer) * 0.2 + 0.8
            size = int(self.size * pulse)
            
            # Draw key pickup
            if self.key_texture:
                # Scale the texture based on pulse
                scaled_texture = pygame.transform.scale(self.key_texture, (size, size))
                # Draw centered at pickup position
                rect = scaled_texture.get_rect(center=(self.x, self.y))
                surface.blit(scaled_texture, rect)
            else:
                # Draw a fallback key shape if texture isn't available
                # Draw a gold key shape
                pygame.draw.circle(surface, (255, 215, 0), (self.x, self.y - size//4), size//4)  # Key head
                pygame.draw.rect(surface, (255, 215, 0), (self.x - size//8, self.y - size//4, size//4, size//2))  # Key shaft
                
                # Add teeth to the key
                pygame.draw.rect(surface, (255, 215, 0), (self.x, self.y + size//8, size//4, size//8))  # Tooth 1
                
            # Add a glow effect
            glow_surf = pygame.Surface((size * 3, size * 3), pygame.SRCALPHA)
            glow_color = (255, 215, 0, 100)  # Golden glow
            pygame.draw.circle(glow_surf, glow_color, (size * 1.5, size * 1.5), size * pulse)
            glow_rect = glow_surf.get_rect(center=(self.x, self.y))
            surface.blit(glow_surf, glow_rect)
        except Exception as e:
            print(f"Error rendering key pickup: {e}")


class WeaponPickup(BasePickup):
    """Pickup for special weapons like the fire sword"""
    def __init__(self, x, y, weapon_type="fire_sword"):
        super().__init__(x, y)
        self.weapon_type = weapon_type
        
        # Try to load weapon texture
        try:
            if weapon_type == "fire_sword":
                weapon_path = os.path.join(WEAPON_SPRITES_PATH, "fire_sword.png")
            else:
                weapon_path = os.path.join(WEAPON_SPRITES_PATH, f"{weapon_type}.png")
                
            if os.path.exists(weapon_path):
                self.weapon_texture = self.asset_manager.load_image(weapon_path, scale=(self.size, self.size))
            else:
                print(f"{weapon_type} texture does not exist: {weapon_path}")
                self.weapon_texture = None
        except Exception as e:
            print(f"Failed to load {weapon_type} texture: {e}")
            self.weapon_texture = None
        
    def draw(self, surface):
        if self.collected:
            return
            
        try:
            # Pulsing effect
            pulse = math.sin(self.pulse_timer) * 0.2 + 0.8
            size = int(self.size * pulse)
            
            # Draw weapon pickup
            if self.weapon_texture:
                # Scale the texture based on pulse
                scaled_texture = pygame.transform.scale(self.weapon_texture, (size, size))
                # Draw centered at pickup position
                rect = scaled_texture.get_rect(center=(self.x, self.y))
                surface.blit(scaled_texture, rect)
            else:
                # Draw a fallback sword shape if texture isn't available
                if self.weapon_type == "fire_sword":
                    # Draw a red/orange sword
                    pygame.draw.rect(surface, (220, 100, 0), (self.x - size//8, self.y - size//3, size//4, size//1.5))  # Blade
                    pygame.draw.rect(surface, (150, 100, 50), (self.x - size//4, self.y + size//6, size//2, size//6))  # Handle
                    
                    # Add some fire effect
                    fire_colors = [(255, 0, 0), (255, 100, 0), (255, 200, 0)]
                    for i in range(3):
                        offset = random.randint(-2, 2)
                        fire_size = size // (4 + i)
                        pygame.draw.circle(surface, fire_colors[i], 
                                        (self.x + offset, self.y - size//3), 
                                        fire_size * pulse)
                else:
                    # Generic weapon
                    pygame.draw.rect(surface, (200, 200, 200), (self.x - size//8, self.y - size//3, size//4, size//1.5))
                    pygame.draw.rect(surface, (100, 100, 100), (self.x - size//4, self.y + size//6, size//2, size//6))
                
            # Add a glow effect based on weapon type
            glow_surf = pygame.Surface((size * 3, size * 3), pygame.SRCALPHA)
            
            if self.weapon_type == "fire_sword":
                glow_color = (255, 100, 0, 100)  # Orange/red glow for fire sword
            else:
                glow_color = (100, 100, 255, 100)  # Blue glow for other weapons
                
            pygame.draw.circle(glow_surf, glow_color, (size * 1.5, size * 1.5), size * pulse)
            glow_rect = glow_surf.get_rect(center=(self.x, self.y))
            surface.blit(glow_surf, glow_rect)
            
            # Add special effects for specific weapon types
            if self.weapon_type == "fire_sword":
                # Add some floating embers/particles for fire effect
                for _ in range(3):
                    ember_x = self.x + random.randint(-size//2, size//2) 
                    ember_y = self.y - random.randint(0, size//2)
                    ember_size = random.randint(2, 5) * pulse
                    ember_color = random.choice([(255, 0, 0), (255, 100, 0), (255, 200, 0)])
                    pygame.draw.circle(surface, ember_color, (ember_x, ember_y), ember_size)
                    
        except Exception as e:
            print(f"Error rendering {self.weapon_type} pickup: {e}") 