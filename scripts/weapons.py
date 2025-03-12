import pygame
import math
import os
from config import *
from asset_manager import get_asset_manager

class Arrow:
    """Arrow projectile that travels in a straight line"""
    def __init__(self, x, y, direction):
        self.x, self.y = x, y
        self.direction = direction
        self.speed = 8
        self.lifetime = 120  # Max frames the arrow exists for
        self.damage = 2
        
        # Create a rectangle for collision detection - make arrow larger
        self.size = TILE_SIZE * 0.75  # Increased from TILE_SIZE // 2
        self.rect = pygame.Rect(x - self.size//2, y - self.size//2, self.size, self.size)
        
        self.asset_manager = get_asset_manager()
        
        # Try to load arrow texture
        try:
            arrow_path = os.path.join(WEAPON_SPRITES_PATH, "rock.png")
            if os.path.exists(arrow_path):
                self.arrow_texture = self.asset_manager.load_image(arrow_path, scale=(self.size, self.size))
                print(f"DEBUG: Arrow created at ({x}, {y}) with direction {direction}")
            else:
                print(f"Arrow texture does not exist: {arrow_path}")
                self.arrow_texture = None
        except Exception as e:
            print(f"Failed to load arrow texture: {e}")
            self.arrow_texture = None
    
    def update(self):
        # Move in the specified direction
        self.x += self.direction[0] * self.speed
        self.y += self.direction[1] * self.speed
        
        # Update rectangle position
        self.rect.x = self.x - self.size//2
        self.rect.y = self.y - self.size//2
        
        # Reduce lifetime
        self.lifetime -= 1
        
        # Return True if arrow should be removed
        return self.lifetime <= 0
        
    def draw(self, surface):
        # Safety check - ensure we're only drawing arrows within screen bounds
        if (0 <= self.x < WINDOW_WIDTH and 0 <= self.y < WINDOW_HEIGHT):
            print(f"DEBUG: Drawing arrow at ({self.x}, {self.y})")
            if self.arrow_texture:
                try:
                    # Calculate rotation angle based on direction
                    angle = math.degrees(math.atan2(-self.direction[1], self.direction[0]))
                    rotated_texture = pygame.transform.rotate(self.arrow_texture, angle)
                    # Get the rect of the rotated image to center it correctly
                    rect = rotated_texture.get_rect(center=(self.x, self.y))
                    surface.blit(rotated_texture, rect)
                    print(f"DEBUG: Drew arrow texture with angle {angle}")
                except Exception as e:
                    print(f"Error drawing arrow texture: {e}")
                    # Use improved fallback rendering
                    self._draw_fallback(surface)
            else:
                # Use improved fallback rendering
                self._draw_fallback(surface)
    
    def _draw_fallback(self, surface):
        """Enhanced fallback rendering for when texture isn't available"""
        # Draw a bigger, more visible arrow
        
        # Draw a circle at the center
        pygame.draw.circle(surface, YELLOW, (int(self.x), int(self.y)), int(self.size//3))
        pygame.draw.circle(surface, BROWN, (int(self.x), int(self.y)), int(self.size//4))
        
        # Draw the arrow shaft
        shaft_length = self.size * 0.8
        end_x = int(self.x - self.direction[0] * shaft_length/2)
        end_y = int(self.y - self.direction[1] * shaft_length/2)
        pygame.draw.line(surface, BROWN, 
                        (int(self.x), int(self.y)), 
                        (end_x, end_y), 
                        int(self.size//6))
        
        # Draw the arrow head
        head_length = self.size * 0.8
        tip_x = int(self.x + self.direction[0] * head_length/2)
        tip_y = int(self.y + self.direction[1] * head_length/2)
        pygame.draw.line(surface, YELLOW, 
                        (int(self.x), int(self.y)), 
                        (tip_x, tip_y), 
                        int(self.size//4))
                        
        # Draw a glow effect
        glow_surf = pygame.Surface((self.size*1.5, self.size*1.5), pygame.SRCALPHA)
        pygame.draw.circle(glow_surf, (255, 255, 0, 50), (self.size*1.5//2, self.size*1.5//2), self.size*1.5//2)
        surface.blit(glow_surf, (self.x - self.size*1.5//2, self.y - self.size*1.5//2))
        
        print(f"DEBUG: Drew enhanced fallback arrow")

class Sword(pygame.sprite.Sprite):
    def __init__(self, player):
        super().__init__()
        self.asset_manager = get_asset_manager()
        self.player = player
        
        # Create default sword images as placeholders
        self.sword_images = {}
        for direction in ['down', 'up', 'left', 'right']:
            # Create a simple sword shape
            sword_img = pygame.Surface([TILE_SIZE, TILE_SIZE // 2], pygame.SRCALPHA)
            if direction in ['left', 'right']:
                # Horizontal sword
                pygame.draw.rect(sword_img, (200, 200, 200), (4, TILE_SIZE//4-2, TILE_SIZE-8, 4))
                # Handle
                pygame.draw.rect(sword_img, (150, 100, 50), (TILE_SIZE//3, TILE_SIZE//4-4, 8, 8))
                # Point
                if direction == 'right':
                    pygame.draw.polygon(sword_img, (220, 220, 220), [(TILE_SIZE-8, TILE_SIZE//4-4), 
                                                                 (TILE_SIZE, TILE_SIZE//4), 
                                                                 (TILE_SIZE-8, TILE_SIZE//4+4)])
                else:
                    pygame.draw.polygon(sword_img, (220, 220, 220), [(8, TILE_SIZE//4-4), 
                                                                 (0, TILE_SIZE//4), 
                                                                 (8, TILE_SIZE//4+4)])
            else:
                # Vertical sword
                pygame.draw.rect(sword_img, (200, 200, 200), (TILE_SIZE//2-2, 4, 4, TILE_SIZE//2-8))
                # Handle
                pygame.draw.rect(sword_img, (150, 100, 50), (TILE_SIZE//2-4, TILE_SIZE//3, 8, 8))
                # Point
                if direction == 'up':
                    pygame.draw.polygon(sword_img, (220, 220, 220), [(TILE_SIZE//2-4, 8), 
                                                                 (TILE_SIZE//2, 0), 
                                                                 (TILE_SIZE//2+4, 8)])
                else:
                    pygame.draw.polygon(sword_img, (220, 220, 220), [(TILE_SIZE//2-4, TILE_SIZE//2-8), 
                                                                 (TILE_SIZE//2, TILE_SIZE//2), 
                                                                 (TILE_SIZE//2+4, TILE_SIZE//2-8)])
                
            self.sword_images[direction] = sword_img
        
        # Now try to load actual sword textures if they exist
        for direction in ['down', 'up', 'left', 'right']:
            try:
                sword_path = os.path.join(WEAPON_SPRITES_PATH, f"sword_{direction}.png")
                if os.path.exists(sword_path):
                    self.sword_images[direction] = self.asset_manager.load_image(
                        sword_path, scale=(TILE_SIZE, TILE_SIZE//2))
            except Exception as e:
                print(f"Failed to load sword_{direction}.png: {e}")
        
        # Set initial image
        self.image = self.sword_images['right']
        self.rect = self.image.get_rect()
        
        # Attack properties
        self.damage = SWORD_DAMAGE
        self.active = False
        self.animation_time = 200  # milliseconds
        self.start_time = 0
        
    def start_attack(self):
        self.active = True
        self.start_time = pygame.time.get_ticks()
        
    def update(self):
        if not self.active:
            return
            
        # Update sword position based on player facing direction
        if self.player.facing == 'right':
            self.image = self.sword_images['right']
            self.rect.midleft = self.player.rect.midright
        elif self.player.facing == 'left':
            self.image = self.sword_images['left']
            self.rect.midright = self.player.rect.midleft
        elif self.player.facing == 'up':
            self.image = self.sword_images['up']
            self.rect.midbottom = self.player.rect.midtop
        elif self.player.facing == 'down':
            self.image = self.sword_images['down']
            self.rect.midtop = self.player.rect.midbottom
            
        # Check if attack animation is finished
        if pygame.time.get_ticks() - self.start_time > self.animation_time:
            self.active = False
            
class Bow:
    def __init__(self):
        self.damage = BOW_DAMAGE
        self.arrows = []  # Store arrow objects in a list
        
    def shoot(self, x, y, direction):
        # Create a new arrow and add it to the list
        try:
            arrow = Arrow(x, y, direction)
            self.arrows.append(arrow)
        except Exception as e:
            print(f"Error creating arrow: {e}")
        
    def update(self):
        # Update arrows and remove those that have expired
        arrows_to_remove = []
        
        for arrow in self.arrows:
            try:
                # If update returns True, arrow should be removed
                if arrow.update():
                    arrows_to_remove.append(arrow)
            except Exception as e:
                print(f"Error updating arrow: {e}")
                arrows_to_remove.append(arrow)
        
        # Remove expired arrows
        for arrow in arrows_to_remove:
            if arrow in self.arrows:
                self.arrows.remove(arrow)
        
    def draw(self, surface):
        # Draw each arrow
        for arrow in self.arrows:
            try:
                arrow.draw(surface)
            except Exception as e:
                print(f"Error drawing arrow: {e}")
                # Remove problematic arrows
                if arrow in self.arrows:
                    self.arrows.remove(arrow)
            
    def get_arrow_rects(self):
        """Return a list of all active arrow rectangles for collision detection"""
        return [arrow.rect for arrow in self.arrows if hasattr(arrow, 'rect')]
        
    def remove_arrow(self, arrow):
        """Remove a specific arrow from the list"""
        if arrow in self.arrows:
            try:
                self.arrows.remove(arrow)
            except Exception as e:
                print(f"Error removing arrow: {e}")
        
class WeaponManager:
    def __init__(self, player):
        self.player = player
        self.sword = Sword(player)
        self.bow = Bow()
        
        # Sprite groups
        self.weapon_sprites = pygame.sprite.Group()
        self.weapon_sprites.add(self.sword)
        
    def update(self):
        # Update sword
        self.sword.update()
        
        # Update bow and arrows
        self.bow.update()
        
        # Remove arrows that go out of bounds
        arrows_to_remove = []
        for arrow in self.bow.arrows:
            try:
                if (arrow.rect.left < 0 or arrow.rect.right > WINDOW_WIDTH or
                    arrow.rect.top < 0 or arrow.rect.bottom > WINDOW_HEIGHT):
                    arrows_to_remove.append(arrow)
            except Exception as e:
                print(f"Error checking arrow bounds: {e}")
                arrows_to_remove.append(arrow)
                
        # Remove arrows safely
        for arrow in arrows_to_remove:
            self.bow.remove_arrow(arrow)
    
    def clear_arrows(self):
        """Clear all arrows when moving between rooms or resetting game state"""
        try:
            # Make a copy of the list to avoid modifying it while iterating
            arrows_to_clear = self.bow.arrows.copy()
            for arrow in arrows_to_clear:
                self.bow.remove_arrow(arrow)
            # Just to be safe, clear the list directly too
            self.bow.arrows = []
            print("All arrows cleared")
        except Exception as e:
            print(f"Error clearing arrows: {e}")
            # Make sure arrows are cleared even if an error occurs
            self.bow.arrows = []
                
    def draw(self, surface):
        # Draw active weapons
        if self.sword.active:
            self.weapon_sprites.draw(surface)
            
        # Draw arrows
        print(f"DEBUG: WeaponManager drawing {len(self.bow.arrows)} arrows")
        self.bow.draw(surface)
        
    def attack_sword(self):
        self.sword.start_attack()
        return self.sword.rect  # Return hitbox for collision detection
        
    def attack_bow(self, mouse_pos):
        # Calculate direction to mouse position
        try:
            # First, check if the player has arrows available
            if self.player.arrow_count <= 0:
                print("Out of arrows!")
                return
                
            print(f"DEBUG: WeaponManager.attack_bow called - Current arrow count: {self.player.arrow_count}")
            print(f"DEBUG: Mouse position: {mouse_pos}, Player position: ({self.player.rect.centerx}, {self.player.rect.centery})")
                
            dx = mouse_pos[0] - self.player.rect.centerx
            dy = mouse_pos[1] - self.player.rect.centery
            distance = math.sqrt(dx * dx + dy * dy)
            
            if distance > 0:
                dx = dx / distance
                dy = dy / distance
                print(f"DEBUG: Normalized direction: ({dx}, {dy})")
                
                # Call the player's attack_bow method to handle cooldown and animation
                result = self.player.attack_bow(mouse_pos)
                if result:
                    # If attack_bow returned a valid direction, shoot the arrow
                    self.bow.shoot(self.player.rect.centerx, self.player.rect.centery, (dx, dy))
                    print(f"Arrow shot! Arrows remaining: {self.player.arrow_count}")
                else:
                    print("DEBUG: Player attack_bow returned None (cooldown or no arrows)")
            else:
                print("DEBUG: Distance is zero, cannot calculate direction")
        except Exception as e:
            print(f"Error in attack_bow: {e}")
            
    def check_arrow_collisions(self, sprite_groups):
        """Check for collisions between arrows and sprite groups"""
        hit_count = 0
        arrows_to_remove = []
        
        for arrow in self.bow.arrows:
            for sprite_group in sprite_groups:
                collision_occurred = False
                for sprite in sprite_group:
                    try:
                        if arrow.rect.colliderect(sprite.rect):
                            # Mark arrow for removal
                            arrows_to_remove.append(arrow)
                            hit_count += 1
                            collision_occurred = True
                            break
                    except Exception as e:
                        print(f"Error in collision detection: {e}")
                        arrows_to_remove.append(arrow)
                        collision_occurred = True
                        break
                        
                if collision_occurred:
                    break
                    
        # Remove all arrows that collided with something
        for arrow in arrows_to_remove:
            self.bow.remove_arrow(arrow)
                
        return hit_count 