import pygame
import math
import os
from config import *
from asset_manager import get_asset_manager
from sound_manager import get_sound_manager

class Arrow:
    """Arrow projectile that travels in a straight line"""
    def __init__(self, x, y, direction):
        self.x, self.y = x, y
        self.direction = direction
        self.speed = 8
        self.lifetime = 120  # Max frames the arrow exists for
        self.damage = 2
        
        # Create a rectangle for collision detection - make arrow much larger
        self.size = TILE_SIZE * 1.5  # Increased from TILE_SIZE * 1.0 for better visibility
        self.rect = pygame.Rect(x - self.size//2, y - self.size//2, self.size, self.size)
        
        self.asset_manager = get_asset_manager()
        
        # Try to load arrow texture
        try:
            arrow_path = os.path.join(WEAPON_SPRITES_PATH, "rock.png")
            if os.path.exists(arrow_path):
                self.arrow_texture = self.asset_manager.load_image(arrow_path, scale=(self.size, self.size))
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
        
        # Print debug info occasionally (every 10 frames)
        if hasattr(self, 'frames_alive'):
            self.frames_alive += 1
            if self.frames_alive % 10 == 0:
                print(f"Arrow at ({int(self.x)}, {int(self.y)}) moving {self.direction} - lifetime: {self.lifetime}")
        else:
            self.frames_alive = 1
        
        # Reduce lifetime
        self.lifetime -= 1
        
        # Return True if arrow should be removed
        return self.lifetime <= 0
        
    def draw(self, surface):
        # Safety check - ensure we're only drawing arrows within screen bounds
        if (0 <= self.x < WINDOW_WIDTH and 0 <= self.y < WINDOW_HEIGHT):
            if self.arrow_texture:
                try:
                    # Calculate rotation angle based on direction
                    angle = math.degrees(math.atan2(-self.direction[1], self.direction[0]))
                    rotated_texture = pygame.transform.rotate(self.arrow_texture, angle)
                    # Get the rect of the rotated image to center it correctly
                    rect = rotated_texture.get_rect(center=(self.x, self.y))
                    surface.blit(rotated_texture, rect)
                except Exception as e:
                    print(f"Error drawing arrow texture: {e}")
                    # Use improved fallback rendering
                    self._draw_fallback(surface)
            else:
                # Use improved fallback rendering
                self._draw_fallback(surface)
    
    def _draw_fallback(self, surface):
        """Enhanced fallback rendering for when texture isn't available"""
        # Draw a HUGE, impossible-to-miss arrow
        
        # Draw a circle at the center (much larger for better visibility)
        pygame.draw.circle(surface, (255, 0, 0), (int(self.x), int(self.y)), int(self.size))  # Red outer circle
        pygame.draw.circle(surface, (255, 255, 0), (int(self.x), int(self.y)), int(self.size//1.3))  # Yellow middle
        pygame.draw.circle(surface, (255, 165, 0), (int(self.x), int(self.y)), int(self.size//1.8))  # Orange inner
        
        # Draw the arrow shaft - much thicker
        shaft_length = self.size * 1.5
        end_x = int(self.x - self.direction[0] * shaft_length/2)
        end_y = int(self.y - self.direction[1] * shaft_length/2)
        pygame.draw.line(surface, (139, 69, 19), 
                        (int(self.x), int(self.y)), 
                        (end_x, end_y), 
                        int(self.size//2))  # Much thicker shaft
        
        # Draw the arrow head - much thicker
        head_length = self.size * 1.5
        tip_x = int(self.x + self.direction[0] * head_length/2)
        tip_y = int(self.y + self.direction[1] * head_length/2)
        pygame.draw.line(surface, (255, 0, 0), 
                        (int(self.x), int(self.y)), 
                        (tip_x, tip_y), 
                        int(self.size//1.5))  # Much thicker head
                        
        # Draw a massive glow effect
        glow_surf = pygame.Surface((self.size*5, self.size*5), pygame.SRCALPHA)
        pygame.draw.circle(glow_surf, (255, 255, 0, 128), (self.size*2.5, self.size*2.5), self.size*2)
        surface.blit(glow_surf, (self.x - self.size*2.5, self.y - self.size*2.5))
        
        # Draw a very obvious debug message
        debug_font = pygame.font.Font(None, 36)  # Larger font
        debug_text = debug_font.render("ARROW", True, (255, 255, 255))
        debug_outline = debug_font.render("ARROW", True, (0, 0, 0))
        # Draw black outline
        surface.blit(debug_outline, (self.x + 20 - 1, self.y - 20 - 1))
        surface.blit(debug_outline, (self.x + 20 + 1, self.y - 20 - 1))
        surface.blit(debug_outline, (self.x + 20 - 1, self.y - 20 + 1))
        surface.blit(debug_outline, (self.x + 20 + 1, self.y - 20 + 1))
        # Draw white text
        surface.blit(debug_text, (self.x + 20, self.y - 20))
            
class Sword(pygame.sprite.Sprite):
    def __init__(self, player):
        super().__init__()
        self.asset_manager = get_asset_manager()
        self.player = player
        
        # Create default sword images as placeholders
        self.sword_images = {}
        self.animation_frames = {}  # Store animation frames for each direction
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
        
        # Try to load normal sword texture first, since that's what we want to use
        try:
            # Load the normal_sword.png (which is in the up position)
            normal_sword_path = os.path.join(WEAPON_SPRITES_PATH, "normal_sword.png")
            if os.path.exists(normal_sword_path):
                # Scale based on size ratio between sword and player - aim for ~0.675x player width (10% smaller than previous 0.75x)
                sword_scale_factor = 0.675  # Reduced by 10% from 0.75 to make the sword smaller
                sword_width = int(TILE_SIZE * sword_scale_factor)
                sword_height = int(sword_width * 1.5)  # Keep aspect ratio
                
                # Load the up-facing sword (the default orientation in the image)
                up_sword = self.asset_manager.load_image(normal_sword_path, scale=(sword_width, sword_height))
                self.sword_images['up'] = up_sword
                
                # Create animation frames for up direction with rotation around bottom center
                self.animation_frames['up'] = self._create_animation_frames(up_sword, 'up')
                
                # Rotate for other directions
                # Down: 180 degrees from up
                down_sword = pygame.transform.rotate(up_sword, 180)
                self.sword_images['down'] = down_sword
                self.animation_frames['down'] = self._create_animation_frames(down_sword, 'down')
                
                # Right: 270 degrees from up (90 degrees clockwise)
                right_sword = pygame.transform.rotate(up_sword, 270)
                self.sword_images['right'] = right_sword
                self.animation_frames['right'] = self._create_animation_frames(right_sword, 'right')
                
                # Left: 90 degrees from up (90 degrees counterclockwise)
                left_sword = pygame.transform.rotate(up_sword, 90)
                self.sword_images['left'] = left_sword
                self.animation_frames['left'] = self._create_animation_frames(left_sword, 'left')
                
                print("Successfully loaded normal_sword.png for all directions")
            else:
                print("normal_sword.png not found - using directional images if available")
                # Fall back to checking for direction-specific images
                for direction in ['down', 'up', 'left', 'right']:
                    try:
                        sword_path = os.path.join(WEAPON_SPRITES_PATH, f"sword_{direction}.png")
                        if os.path.exists(sword_path):
                            sword_img = self.asset_manager.load_image(
                                sword_path, scale=(TILE_SIZE, TILE_SIZE//2))
                            self.sword_images[direction] = sword_img
                            self.animation_frames[direction] = self._create_animation_frames(sword_img, direction)
                    except Exception as e:
                        print(f"Failed to load sword_{direction}.png: {e}")
        except Exception as e:
            print(f"Failed to load normal_sword.png: {e}")
            # Fall back to direction-specific images
            for direction in ['down', 'up', 'left', 'right']:
                try:
                    sword_path = os.path.join(WEAPON_SPRITES_PATH, f"sword_{direction}.png")
                    if os.path.exists(sword_path):
                        sword_img = self.asset_manager.load_image(
                            sword_path, scale=(TILE_SIZE, TILE_SIZE//2))
                        self.sword_images[direction] = sword_img
                        self.animation_frames[direction] = self._create_animation_frames(sword_img, direction)
                except Exception as e:
                    print(f"Failed to load sword_{direction}.png: {e}")
        
        # Set initial image and animation frame
        self.image = self.sword_images['right']
        self.rect = self.image.get_rect()
        
        # Attack properties
        self.damage = SWORD_DAMAGE
        self.active = False
        self.animation_time = 200  # milliseconds
        self.start_time = 0
        self.current_frame = 0
        self.total_frames = 4  # Number of animation frames
        
    def _create_animation_frames(self, base_image, direction):
        """Create 4 animation frames by rotating the sword around its handle."""
        frames = []
        
        # Create rotation angles for a smooth swing animation
        # Start at -20 degrees, swing to +20 degrees
        angles = [-20, -6.66, 6.66, 20]
        
        # Find the pivot point based on direction (where the player would hold the sword)
        original_rect = base_image.get_rect()
        
        for angle in angles:
            # Start with a clean rotation surface that's large enough
            # to avoid clipping during rotation
            padding = max(original_rect.width, original_rect.height) * 2
            rotation_surface = pygame.Surface((padding, padding), pygame.SRCALPHA)
            
            # Find the center of the rotation surface
            rotation_center = (padding // 2, padding // 2)
            
            # Calculate the position to place the sword on the rotation surface
            # so that the appropriate edge is at the center of rotation
            if direction == 'up':
                # For up-facing sword, handle is at bottom center
                blit_pos = (rotation_center[0] - original_rect.width // 2, 
                           rotation_center[1] - original_rect.height)
            elif direction == 'down':
                # For down-facing sword, handle is at top center
                blit_pos = (rotation_center[0] - original_rect.width // 2, 
                           rotation_center[1])
            elif direction == 'left':
                # For left-facing sword, handle is at right center
                blit_pos = (rotation_center[0] - original_rect.width, 
                           rotation_center[1] - original_rect.height // 2)
            elif direction == 'right':
                # For right-facing sword, handle is at left center
                blit_pos = (rotation_center[0], 
                           rotation_center[1] - original_rect.height // 2)
            
            # Place the sword on the rotation surface
            rotation_surface.blit(base_image, blit_pos)
            
            # Rotate the entire surface around its center
            rotated = pygame.transform.rotate(rotation_surface, angle)
            
            # Store the rotated frame
            frames.append(rotated)
        
        return frames
        
    def start_attack(self):
        self.active = True
        self.start_time = pygame.time.get_ticks()
        self.current_frame = 0
        
    def update(self):
        if not self.active:
            return
        
        # Calculate frame based on elapsed time
        elapsed_time = pygame.time.get_ticks() - self.start_time
        frame_duration = self.animation_time / self.total_frames
        self.current_frame = min(int(elapsed_time / frame_duration), self.total_frames - 1)
        
        # Update sword position and animation frame based on player facing direction
        if self.player.facing == 'right':
            self.image = self.animation_frames['right'][self.current_frame]
            self.rect = self.image.get_rect()
            # Position closer to player
            self.rect.midleft = self.player.rect.midright
            # Adjust position to be much closer to the player
            offset_x = int((self.rect.width * 0.7))  # Move sword closer by 70% of its width
            self.rect.x -= offset_x
        elif self.player.facing == 'left':
            self.image = self.animation_frames['left'][self.current_frame]
            self.rect = self.image.get_rect()
            self.rect.midright = self.player.rect.midleft
            # Adjust position to be much closer to the player
            offset_x = int((self.rect.width * 0.7))  # Move sword closer by 70% of its width
            self.rect.x += offset_x
        elif self.player.facing == 'up':
            self.image = self.animation_frames['up'][self.current_frame]
            self.rect = self.image.get_rect()
            self.rect.midbottom = self.player.rect.midtop
            # Adjust position to be much closer to the player
            offset_y = int((self.rect.height * 0.7))  # Move sword closer by 70% of its height
            self.rect.y += offset_y
        elif self.player.facing == 'down':
            self.image = self.animation_frames['down'][self.current_frame]
            self.rect = self.image.get_rect()
            self.rect.midtop = self.player.rect.midbottom
            # Adjust position to be much closer to the player
            offset_y = int((self.rect.height * 0.7))  # Move sword closer by 70% of its height
            self.rect.y -= offset_y
        
        # Check if attack animation is finished
        if elapsed_time > self.animation_time:
            self.active = False
            
class Bow:
    """Bow weapon that shoots arrows"""
    def __init__(self, player):
        self.player = player
        self.cooldown = 0
        self.cooldown_time = 15  # Frames between shots
        self.arrows = []
        self.max_arrows = 30
        self.asset_manager = get_asset_manager()
        
        # Try to load bow texture
        try:
            bow_path = os.path.join(WEAPON_SPRITES_PATH, "bow.png")
            if os.path.exists(bow_path):
                self.bow_texture = self.asset_manager.load_image(bow_path, scale=(TILE_SIZE, TILE_SIZE))
        except:
            self.bow_texture = None
        
    def update(self):
        # Update cooldown
        if self.cooldown > 0:
            self.cooldown -= 1
            
        # Update all arrows
        arrows_to_remove = []
        for arrow in self.arrows:
            if arrow.update():
                arrows_to_remove.append(arrow)
                
        # Remove dead arrows
        for arrow in arrows_to_remove:
            self.remove_arrow(arrow)
    
    def add_arrow(self, x, y, direction):
        new_arrow = Arrow(x, y, direction)
        self.arrows.append(new_arrow)
        return new_arrow
        
    def remove_arrow(self, arrow):
        if arrow in self.arrows:
            self.arrows.remove(arrow)
            
    def remove_out_of_bounds_arrows(self):
        arrows_before = len(self.arrows)
        self.arrows = [arrow for arrow in self.arrows 
                      if 0 <= arrow.x < WINDOW_WIDTH and 0 <= arrow.y < WINDOW_HEIGHT]
        arrows_removed = arrows_before - len(self.arrows)
        
        # If arrows were removed, print debug info
        if arrows_removed > 0:
            for arrow in self.arrows:
                if arrow.x < 0 or arrow.x >= WINDOW_WIDTH or arrow.y < 0 or arrow.y >= WINDOW_HEIGHT:
                    pass
        
    def draw(self, surface):
        # Debug message
        print(f"DEBUG: Rendering {len(self.arrows)} arrows")
        
        # Draw each arrow
        for arrow in self.arrows:
            arrow.draw(surface)
        
class WeaponManager:
    """Manages all weapons for the player"""
    def __init__(self, player, destroyable_walls=None, damage_sprites=None):
        self.player = player
        self.sword = Sword(player)
        self.bow = Bow(player)
        self.current_weapon = "sword"  # Default weapon
        self.destroyable_walls = destroyable_walls
        self.damage_sprites = damage_sprites or []
        
        # Create a sprite group for the weapons
        self.weapon_sprites = pygame.sprite.Group()
        self.weapon_sprites.add(self.sword)
        
        # Sound manager for weapon sounds
        self.sound_manager = get_sound_manager()
        
    def update(self):
        # Update all weapons
        self.sword.update()
        self.bow.update()
        
        # Remove arrows that have gone out of bounds
        self.bow.remove_out_of_bounds_arrows()
                
    def draw(self, surface):
        # Draw all weapons
        if self.current_weapon == "sword":
            self.sword.draw(surface)
        # Bow drawing is handled separately in the main render loop
        # to draw arrows on top of everything
            
    def handle_event(self, event):
        # Handle weapon switching
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_1:
                self.current_weapon = "sword"
                print("Switched to sword")
            elif event.key == pygame.K_2:
                self.current_weapon = "bow"
                print("Switched to bow")
        
        # Handle attack with current weapon
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # Left mouse button
                mouse_pos = pygame.mouse.get_pos()
                if self.current_weapon == "sword":
                    self.attack_sword()
                elif self.current_weapon == "bow":
                    self.attack_bow(mouse_pos)
        
    def attack_sword(self):
        # Activate the sword animation
        if not self.sword.active:
            self.sword.start_attack()
            # Play sword attack sound effect
            self.sound_manager.play_sound("sword_attack")
    def attack_bow(self, mouse_pos):
        # Check if player has arrows

        if self.player.arrow_count <= 0:
            return None
            
        # Check cooldown
        if self.bow.cooldown > 0:
            return None
            
        # Calculate direction to mouse
        dx = mouse_pos[0] - self.player.rect.centerx
        dy = mouse_pos[1] - self.player.rect.centery
        distance = math.sqrt(dx*dx + dy*dy)
        
        if distance > 0:
            # Normalize direction
            dx /= distance
            dy /= distance
            
            # Shoot arrow - pass the full mouse_pos to the player
            if self.player.attack_bow(mouse_pos):
                # Only create the arrow if player successfully shot
                arrow = self.bow.add_arrow(self.player.rect.centerx, self.player.rect.centery, (dx, dy))
                # Reset cooldown
                self.bow.cooldown = self.bow.cooldown_time
                
                # For debugging
                print(f"Created arrow at ({self.player.rect.centerx}, {self.player.rect.centery}) moving in direction ({dx}, {dy})")
                
                return arrow
        
        return None
    
    def check_collisions(self, sprite_groups):
        """Check for arrow collisions with various sprite groups"""
        hit_count = 0
        
        for group in sprite_groups:
            for arrow in self.bow.arrows[:]:  # Make a copy to avoid modification during iteration
                collided_sprites = pygame.sprite.spritecollide(arrow, group, dokill=False)
                for sprite in collided_sprites:
                    
                    # Handle damage
                    if hasattr(sprite, 'take_damage'):
                        sprite.take_damage(arrow.damage)
                    
                    # Remove the arrow
                    self.bow.remove_arrow(arrow)
                    hit_count += 1
                    break  # Break after first collision per arrow
        
        return hit_count

    def clear_arrows(self):
        """Clear all arrows from the bow"""
        self.bow.arrows = []
        print("All arrows cleared")