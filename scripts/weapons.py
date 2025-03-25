import os
import pygame
import random
import math
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
        self.sound_manager = get_sound_manager()
        self.player = player
        
        # Create default sword images as placeholders
        self.sword_images = {}
        self.animation_frames = {}  # Store animation frames for each direction
        
        # Fire sword images and animations
        self.fire_sword_images = {}
        self.fire_animation_frames = {}
        
        # Lightning sword images and animations
        self.lightning_sword_images = {}
        self.lightning_animation_frames = {}
        
        # Track sword type
        self.is_fire_sword = False
        self.is_lightning_sword = False
        
        self.flame_particles = []
        self.lightning_particles = []
        
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
                sword_scale_factor = 0.675
                sword_width = int(TILE_SIZE * sword_scale_factor)
                sword_height = int(sword_width * 1.5)  # Height is 1.5x the width
                
                up_sword = self.asset_manager.load_image(normal_sword_path, scale=(sword_width, sword_height))
                
                # Store the base up-facing sword
                self.sword_images['up'] = up_sword
                self.animation_frames['up'] = self._create_animation_frames(up_sword, 'up')
                
                # Create rotated versions for other directions
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
                print("Using simple sword graphics - normal_sword.png not found")
                # We'll use the simple shapes defined above if the PNG isn't available
                
                # Create animation frames for each direction
                for direction in ['down', 'up', 'left', 'right']:
                    self.animation_frames[direction] = self._create_animation_frames(self.sword_images[direction], direction)
        except Exception as e:
            print(f"Error loading normal sword: {e}")
            # Still create animation frames for the simple shapes
            for direction in ['down', 'up', 'left', 'right']:
                self.animation_frames[direction] = self._create_animation_frames(self.sword_images[direction], direction)
                
        # Try to load sword graphics for each direction separately
        # This is a fallback if the normal_sword.png isn't available or doesn't load properly
        for direction in ['down', 'up', 'left', 'right']:
            try:
                sword_path = os.path.join(WEAPON_SPRITES_PATH, f"sword_{direction}.png")
                if os.path.exists(sword_path):
                    # Use the same scale factor for consistency
                    sword_scale_factor = 0.675
                    sword_width = int(TILE_SIZE * sword_scale_factor)
                    sword_height = int(sword_width * 1.5)
                    
                    # Load and scale the specific direction image
                    sword_img = self.asset_manager.load_image(
                        sword_path, scale=(TILE_SIZE, TILE_SIZE//2))
                    self.sword_images[direction] = sword_img
                    self.animation_frames[direction] = self._create_animation_frames(sword_img, direction)
            except Exception as e:
                print(f"Failed to load sword_{direction}.png: {e}")
                
        # Load fire sword images and create animation frames
        self._load_fire_sword_images()
        
        # Load lightning sword images and create animation frames
        self._load_lightning_sword_images()
        
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
        
    def _load_fire_sword_images(self):
        """Load the fire sword images and create animation frames for all directions"""
        try:
            # Load the fire_sword.png (which is in the up position)
            fire_sword_path = os.path.join(WEAPON_SPRITES_PATH, "fire_sword.png")
            if os.path.exists(fire_sword_path):
                # Use the same scale as the normal sword
                sword_scale_factor = 0.675
                sword_width = int(TILE_SIZE * sword_scale_factor)
                sword_height = int(sword_width * 1.5)
                
                # Load the up-facing fire sword
                up_fire_sword = self.asset_manager.load_image(fire_sword_path, scale=(sword_width, sword_height))
                self.fire_sword_images['up'] = up_fire_sword
                
                # Create animation frames for up direction
                self.fire_animation_frames['up'] = self._create_animation_frames(up_fire_sword, 'up')
                
                # Rotate for other directions
                # Down: 180 degrees from up
                down_fire_sword = pygame.transform.rotate(up_fire_sword, 180)
                self.fire_sword_images['down'] = down_fire_sword
                self.fire_animation_frames['down'] = self._create_animation_frames(down_fire_sword, 'down')
                
                # Right: 270 degrees from up (90 degrees clockwise)
                right_fire_sword = pygame.transform.rotate(up_fire_sword, 270)
                self.fire_sword_images['right'] = right_fire_sword
                self.fire_animation_frames['right'] = self._create_animation_frames(right_fire_sword, 'right')
                
                # Left: 90 degrees from up (90 degrees counterclockwise)
                left_fire_sword = pygame.transform.rotate(up_fire_sword, 90)
                self.fire_sword_images['left'] = left_fire_sword
                self.fire_animation_frames['left'] = self._create_animation_frames(left_fire_sword, 'left')
                
                print("Successfully loaded fire_sword.png for all directions")
            else:
                print("fire_sword.png not found - using normal sword images for fire sword")
                # Use normal sword images as fallback
                self.fire_sword_images = self.sword_images.copy()
                self.fire_animation_frames = self.animation_frames.copy()
        except Exception as e:
            print(f"Failed to load fire_sword.png: {e}")
            # Use normal sword images as fallback
            self.fire_sword_images = self.sword_images.copy()
            self.fire_animation_frames = self.animation_frames.copy()
        
    def _load_lightning_sword_images(self):
        """Load the lightning sword images and create animation frames for all directions"""
        try:
            # Load the lightning_sword.png (which is in the up position)
            lightning_sword_path = os.path.join(WEAPON_SPRITES_PATH, "lightning_sword.png")
            if os.path.exists(lightning_sword_path):
                # Use the same scale as the normal sword
                sword_scale_factor = 0.675
                sword_width = int(TILE_SIZE * sword_scale_factor)
                sword_height = int(sword_width * 1.5)
                
                # Load the up-facing lightning sword
                up_lightning_sword = self.asset_manager.load_image(lightning_sword_path, scale=(sword_width, sword_height))
                self.lightning_sword_images['up'] = up_lightning_sword
                
                # Create animation frames for up direction
                self.lightning_animation_frames['up'] = self._create_animation_frames(up_lightning_sword, 'up')
                
                # Rotate for other directions
                # Down: 180 degrees from up
                down_lightning_sword = pygame.transform.rotate(up_lightning_sword, 180)
                self.lightning_sword_images['down'] = down_lightning_sword
                self.lightning_animation_frames['down'] = self._create_animation_frames(down_lightning_sword, 'down')
                
                # Right: 270 degrees from up (90 degrees clockwise)
                right_lightning_sword = pygame.transform.rotate(up_lightning_sword, 270)
                self.lightning_sword_images['right'] = right_lightning_sword
                self.lightning_animation_frames['right'] = self._create_animation_frames(right_lightning_sword, 'right')
                
                # Left: 90 degrees from up (90 degrees counterclockwise)
                left_lightning_sword = pygame.transform.rotate(up_lightning_sword, 90)
                self.lightning_sword_images['left'] = left_lightning_sword
                self.lightning_animation_frames['left'] = self._create_animation_frames(left_lightning_sword, 'left')
                
                print("Successfully loaded lightning_sword.png for all directions")
            else:
                print("lightning_sword.png not found - using normal sword images for lightning sword")
                # Use normal sword images as fallback
                self.lightning_sword_images = self.sword_images.copy()
        except Exception as e:
            print(f"Failed to load lightning_sword.png: {e}")
            # Use normal sword images as fallback
            self.lightning_sword_images = self.sword_images.copy()
        
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
        
    def set_fire_sword(self, enabled=True):
        """Enable or disable fire sword effect"""
        # Toggle fire mode
        self.is_fire_sword = enabled
        
        # Disable lightning sword mode if fire sword mode is enabled
        if enabled:
            self.is_lightning_sword = False
            
        # Make sure we have fire sword images if enabling
        if enabled and not self.fire_sword_images:
            self._load_fire_sword_images()
            
    def set_lightning_sword(self, enabled=True):
        """Enable or disable lightning sword effect"""
        # Toggle lightning mode
        self.is_lightning_sword = enabled
        
        # Disable fire sword mode if lightning sword mode is enabled
        if enabled:
            self.is_fire_sword = False
            
        # Make sure we have lightning sword images if enabling
        if enabled and not self.lightning_sword_images:
            self._load_lightning_sword_images()
            
    def update_flame_particles(self):
        """Update flame particles for fire sword effect"""
        # Only update if fire sword is active
        if not self.is_fire_sword:
            self.flame_particles = []
            return
            
        # Remove expired particles
        self.flame_particles = [p for p in self.flame_particles if p['lifetime'] > 0]
        
        # Add new particles when needed
        if len(self.flame_particles) < 10 and random.random() < 0.4:  # 40% chance each frame
            # Get the tip position of the sword based on player's facing direction
            if self.player.facing == 'right':
                tip_x = self.player.rect.centerx + TILE_SIZE // 2
                tip_y = self.player.rect.centery
            elif self.player.facing == 'left':
                tip_x = self.player.rect.centerx - TILE_SIZE // 2
                tip_y = self.player.rect.centery
            elif self.player.facing == 'up':
                tip_x = self.player.rect.centerx
                tip_y = self.player.rect.top - TILE_SIZE // 4
            else:  # down
                tip_x = self.player.rect.centerx
                tip_y = self.player.rect.bottom + TILE_SIZE // 4
                
            # Create a new fire particle
            new_particle = {
                'x': tip_x + random.randint(-5, 5),
                'y': tip_y + random.randint(-5, 5),
                'color': (255, random.randint(100, 200), 0),  # Orange-yellow color
                'size': random.randint(2, 6),
                'lifetime': random.randint(10, 30),
                'speed_x': random.uniform(-0.5, 0.5),
                'speed_y': random.uniform(-1.0, -0.2)  # Fire particles move upward
            }
            self.flame_particles.append(new_particle)
            
        # Update existing particles
        for particle in self.flame_particles:
            # Move the particle
            particle['x'] += particle['speed_x']
            particle['y'] += particle['speed_y']
            
            # Decrease lifetime
            particle['lifetime'] -= 1
        
    def update_lightning_particles(self):
        """Update lightning particles for lightning sword effect"""
        # Only update if lightning sword is active
        if not self.is_lightning_sword:
            self.lightning_particles = []
            return
            
        # Remove expired particles
        self.lightning_particles = [p for p in self.lightning_particles if p['lifetime'] > 0]
        
        # ALWAYS generate a lightning strike when the sword is active
        if self.active:
            # Clear existing particles to prevent overlap and ensure new lightning is visible
            self.lightning_particles = [p for p in self.lightning_particles if not 'points' in p]
            
            # Add multiple lightning beams for a more dramatic effect
            num_beams = 3  # Always create 3 beams per swing
            
            for _ in range(num_beams):
                # Get the tip position of the sword based on player's facing direction
                # Calculate beam start point (sword tip)
                if self.player.facing == 'right':
                    start_x = self.rect.right
                    start_y = self.rect.centery
                    beam_length = TILE_SIZE * 4  # Even longer beam
                    beam_direction = (1, 0)
                elif self.player.facing == 'left':
                    start_x = self.rect.left
                    start_y = self.rect.centery
                    beam_length = TILE_SIZE * 4  # Even longer beam
                    beam_direction = (-1, 0)
                elif self.player.facing == 'up':
                    start_x = self.rect.centerx
                    start_y = self.rect.top
                    beam_length = TILE_SIZE * 4  # Even longer beam
                    beam_direction = (0, -1)
                else:  # down
                    start_x = self.rect.centerx
                    start_y = self.rect.bottom
                    beam_length = TILE_SIZE * 4  # Even longer beam
                    beam_direction = (0, 1)
                    
                # Generate a lightning beam with many segments for extreme zigzag
                segments = random.randint(8, 12)  # More segments for extreme zigzagging
                segment_length = beam_length / segments
                
                points = [(start_x, start_y)]
                current_x, current_y = start_x, start_y
                
                # Create extreme zigzag pattern for the beam
                for i in range(segments):
                    # Calculate next point with extreme randomness for zigzag appearance
                    # Alternate direction of jitter to create zigzag pattern
                    zigzag_multiplier = 1 if i % 2 == 0 else -1
                    
                    if beam_direction[1] != 0:  # Vertical beam
                        jitter_x = random.randint(25, 40) * zigzag_multiplier  # Exaggerated horizontal zigzag
                        jitter_y = 0
                    else:  # Horizontal beam
                        jitter_x = 0
                        jitter_y = random.randint(25, 40) * zigzag_multiplier  # Exaggerated vertical zigzag
                    
                    next_x = current_x + (beam_direction[0] * segment_length) + jitter_x
                    next_y = current_y + (beam_direction[1] * segment_length) + jitter_y
                    
                    points.append((next_x, next_y))
                    current_x, current_y = next_x, next_y
                
                # Create a new lightning beam with multiple segments - bright blue color
                new_particle = {
                    'points': points,
                    'color': (50, 120, 255),  # Even more blue color for lightning
                    'thickness': random.randint(4, 8),  # Thicker beam
                    'lifetime': random.randint(15, 20),  # Longer lifetime so it's visible
                    'start_time': pygame.time.get_ticks(),
                    'beam_direction': beam_direction,
                    'is_main_beam': True  # Mark as main beam
                }
                self.lightning_particles.append(new_particle)
                
                # Add secondary beams that branch off from random points on the main beam
                for i in range(random.randint(2, 4)):  # 2-4 branches per main beam
                    if len(points) < 2:
                        continue
                        
                    # Choose a random point on the main beam to branch from
                    branch_start_idx = random.randint(0, len(points) - 2)
                    branch_start_x = points[branch_start_idx][0]
                    branch_start_y = points[branch_start_idx][1]
                    
                    # Create a short zigzag branch
                    branch_points = [(branch_start_x, branch_start_y)]
                    branch_segments = random.randint(3, 5)
                    branch_length = TILE_SIZE * 1.5
                    segment_length = branch_length / branch_segments
                    
                    # Random direction for branch
                    branch_angle = random.uniform(0, 2 * math.pi)
                    branch_direction = (math.cos(branch_angle), math.sin(branch_angle))
                    
                    current_x, current_y = branch_start_x, branch_start_y
                    
                    for j in range(branch_segments):
                        # Alternate zigzag pattern
                        zigzag_multiplier = 1 if j % 2 == 0 else -1
                        
                        # Add some perpendicular jitter for zigzag effect
                        perp_x = -branch_direction[1] * random.randint(10, 20) * zigzag_multiplier
                        perp_y = branch_direction[0] * random.randint(10, 20) * zigzag_multiplier
                        
                        next_x = current_x + (branch_direction[0] * segment_length) + perp_x
                        next_y = current_y + (branch_direction[1] * segment_length) + perp_y
                        
                        branch_points.append((next_x, next_y))
                        current_x, current_y = next_x, next_y
                    
                    # Add branch as a separate particle
                    branch_particle = {
                        'points': branch_points,
                        'color': (100, 150, 255),  # Slightly different blue
                        'thickness': random.randint(2, 4),  # Thinner than main beam
                        'lifetime': random.randint(10, 15),  # Shorter than main beam
                        'start_time': pygame.time.get_ticks(),
                        'beam_direction': branch_direction,
                        'is_main_beam': False  # Mark as branch
                    }
                    self.lightning_particles.append(branch_particle)
        
        # Update existing particles
        for particle in self.lightning_particles:
            # For beam particles, we don't need to move them, just decrease lifetime
            if 'points' in particle:
                particle['lifetime'] -= 1
            else:
                # For ambient discharge particles
                particle['x'] += particle['speed_x'] + random.uniform(-0.3, 0.3)
                particle['y'] += particle['speed_y'] + random.uniform(-0.3, 0.3)
                particle['lifetime'] -= 1
        
    def draw_flame_particles(self, surface):
        """Draw flame particles for fire sword effect"""
        if not self.is_fire_sword:
            return
            
        for particle in self.flame_particles:
            size = int(particle['size'])
            if size <= 0:
                continue
                
            # Add glow effect
            glow_size = size * 3
            glow_surf = pygame.Surface((glow_size, glow_size), pygame.SRCALPHA)
            glow_color = (*particle['color'][:3], 50)  # Semi-transparent
            pygame.draw.circle(glow_surf, glow_color, (glow_size//2, glow_size//2), glow_size//2)
            surface.blit(glow_surf, (particle['x'] - glow_size//2, particle['y'] - glow_size//2))
            
            # Draw actual particle
            pygame.draw.circle(surface, particle['color'], (int(particle['x']), int(particle['y'])), size)
        
    def draw_lightning_particles(self, surface):
        """Draw lightning particles for lightning sword effect"""
        if not self.lightning_particles:
            return
            
        for particle in self.lightning_particles:
            if 'points' in particle:  # This is a beam particle
                # Draw the main beam segments
                points = particle['points']
                thickness = particle['thickness']
                color = particle['color']
                
                # Draw a glow behind the lightning for better visibility
                if particle.get('is_main_beam', False):
                    glow_color = (color[0], color[1], color[2], 50)  # Semi-transparent
                    glow_thickness = thickness * 3
                    
                    for i in range(len(points) - 1):
                        # Create a surface for the glow
                        line_length = int(math.sqrt((points[i+1][0] - points[i][0])**2 + 
                                                   (points[i+1][1] - points[i][1])**2))
                        
                        # Draw the glowing backdrop for more visibility
                        pygame.draw.line(
                            surface, 
                            glow_color,
                            (int(points[i][0]), int(points[i][1])),
                            (int(points[i+1][0]), int(points[i+1][1])),
                            glow_thickness
                        )
                
                # Draw each segment of the beam
                for i in range(len(points) - 1):
                    pygame.draw.line(
                        surface, 
                        color,
                        (int(points[i][0]), int(points[i][1])),
                        (int(points[i+1][0]), int(points[i+1][1])),
                        thickness
                    )
                    
                # Draw a glowing effect for the beam
                for i in range(len(points) - 1):
                    # Draw a thinner, brighter line on top
                    pygame.draw.line(
                        surface, 
                        (200, 220, 255),  # Bright blue-white for inner glow
                        (int(points[i][0]), int(points[i][1])),
                        (int(points[i+1][0]), int(points[i+1][1])),
                        max(1, thickness // 2)
                    )
                    
                    # Draw an even thinner white center for extra brightness
                    pygame.draw.line(
                        surface, 
                        (255, 255, 255),  # Pure white for center
                        (int(points[i][0]), int(points[i][1])),
                        (int(points[i+1][0]), int(points[i+1][1])),
                        max(1, thickness // 3)
                    )
                    
                # Draw small sparks at each point junction for extra effect
                for point in points:
                    spark_size = random.randint(1, 3)
                    pygame.draw.circle(
                        surface,
                        (200, 220, 255),  # Bright blue-white
                        (int(point[0]), int(point[1])),
                        spark_size
                    )
                    
            else:  # This is an ambient discharge particle (small sparks)
                # Draw a small spark
                size = int(particle['size'])
                if size <= 0:
                    continue
                
                # Draw the spark as a small circle
                pygame.draw.circle(
                    surface, 
                    particle['color'], 
                    (int(particle['x']), int(particle['y'])), 
                    size
                )
                
                # Add a small glow effect
                glow_size = size * 2
                glow_surf = pygame.Surface((glow_size * 2, glow_size * 2), pygame.SRCALPHA)
                glow_color = (*particle['color'][:3], 100)  # Semi-transparent
                pygame.draw.circle(glow_surf, glow_color, (glow_size, glow_size), glow_size)
                surface.blit(glow_surf, (particle['x'] - glow_size, particle['y'] - glow_size))
        
    def update(self):
        """Update the sword state"""
        if not self.active:
            return
        
        current_time = pygame.time.get_ticks()
        # Calculate frame based on elapsed time
        elapsed = current_time - self.start_time
        
        if elapsed > self.animation_time:
            # Animation complete
            self.active = False
            return
            
        # Calculate current frame number (0-3) based on elapsed time
        frame_progress = elapsed / self.animation_time
        self.current_frame = int(frame_progress * self.total_frames)
        
        # Update sword position and frame
        self.update_position()
        
        # Update flame particles for fire sword
        self.update_flame_particles()
        
        # Update lightning particles for lightning sword
        self.update_lightning_particles()
        
    def draw(self, surface):
        """Draw the sword and any effects"""
        if not self.active:
            # Draw flame particles even when sword is inactive for fire sword
            if self.is_fire_sword:
                self.draw_flame_particles(surface)
            # Draw lightning particles even when sword is inactive for lightning sword
            if self.is_lightning_sword:
                self.draw_lightning_particles(surface)
            return
            
        # Get appropriate animation frames based on sword type
        if self.is_fire_sword:
            animation_frames = self.fire_animation_frames
        elif self.is_lightning_sword:
            animation_frames = self.lightning_animation_frames
        else:
            animation_frames = self.animation_frames
            
        # Get the current frame for the current direction
        frames = animation_frames.get(self.player.facing, [])
        if not frames or self.current_frame >= len(frames):
            return  # No frames to draw or invalid frame
            
        # Get the current frame image
        frame_img = frames[min(self.current_frame, len(frames)-1)]
        
        # Blit the current frame at the sword's position
        surface.blit(frame_img, self.rect)
        
        # Draw flame particles for fire sword
        if self.is_fire_sword:
            self.draw_flame_particles(surface)
            
        # Draw lightning particles for lightning sword
        if self.is_lightning_sword:
            self.draw_lightning_particles(surface)
        
    def update_position(self):
        """Update sword position and animation frame based on player facing direction"""
        # Use the appropriate animation frames based on sword type
        if self.is_lightning_sword:
            animation_frames = self.lightning_animation_frames
        elif self.is_fire_sword:
            animation_frames = self.fire_animation_frames
        else:
            animation_frames = self.animation_frames
        
        if self.player.facing == 'right':
            self.image = animation_frames['right'][self.current_frame]
            self.rect = self.image.get_rect()
            # Position closer to player
            self.rect.midleft = self.player.rect.midright
            # Adjust position to be much closer to the player
            offset_x = int((self.rect.width * 0.7))  # Move sword closer by 70% of its width
            self.rect.x -= offset_x
        elif self.player.facing == 'left':
            self.image = animation_frames['left'][self.current_frame]
            self.rect = self.image.get_rect()
            self.rect.midright = self.player.rect.midleft
            # Adjust position to be much closer to the player
            offset_x = int((self.rect.width * 0.7))  # Move sword closer by 70% of its width
            self.rect.x += offset_x
        elif self.player.facing == 'up':
            self.image = animation_frames['up'][self.current_frame]
            self.rect = self.image.get_rect()
            self.rect.midbottom = self.player.rect.midtop
            # Adjust position to be much closer to the player
            offset_y = int((self.rect.height * 0.7))  # Move sword closer by 70% of its height
            self.rect.y += offset_y
        elif self.player.facing == 'down':
            self.image = animation_frames['down'][self.current_frame]
            self.rect = self.image.get_rect()
            self.rect.midtop = self.player.rect.midbottom
            # Adjust position to be much closer to the player
            offset_y = int((self.rect.height * 0.7))  # Move sword closer by 70% of its height
            self.rect.y -= offset_y
    
    def activate(self):
        """Activate the sword attack animation"""
        if not self.active:
            self.active = True
            self.start_time = pygame.time.get_ticks()
            self.current_frame = 0
            self.update_position()
        
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
        self.sound_manager = get_sound_manager()
        self.sword = Sword(player)
        self.bow = Bow(player)
        self.current_weapon = "sword"  # Default weapon
        self.destroyable_walls = destroyable_walls
        self.damage_sprites = damage_sprites or []
        
        # Create a sprite group for the weapons
        self.weapon_sprites = pygame.sprite.Group()
        self.weapon_sprites.add(self.sword)
        
        # Track special sword types
        self.has_fire_sword = False
        self.has_lightning_sword = False
        
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
        
    def enable_fire_sword(self):
        """Enable fire sword for the player"""
        self.has_fire_sword = True
        self.has_lightning_sword = False  # Turn off lightning sword if fire sword is enabled
        self.sword.set_fire_sword(True)
        
    def enable_lightning_sword(self):
        """Enable lightning sword for the player"""
        self.has_lightning_sword = True
        self.has_fire_sword = False  # Turn off fire sword if lightning sword is enabled
        self.sword.set_lightning_sword(True)
        
    def attack_sword(self):
        """Attack with sword and play sound effect"""
        sword_hitbox = self.player.attack_sword()
        if sword_hitbox:
            self.sword.activate()
            
            # Play appropriate sword sound
            if self.has_fire_sword:
                self.sound_manager.play_sound("effects/fire_sword")
            elif self.has_lightning_sword:
                self.sound_manager.play_sound("effects/lightning_sword")
            else:
                self.sound_manager.play_sound("effects/sword_attack")
            
            # Return the hitbox for collision detection
            return sword_hitbox
        return None
    
    def attack_bow(self, mouse_pos):
        # Check if player has arrows
        if self.player.arrow_count <= 0:
            return None
            
        # Check cooldown
        if self.bow.cooldown > 0:
            return None
            
        # Calculate direction directly from mouse position for precise aiming
        mouse_dx = mouse_pos[0] - self.player.rect.centerx
        mouse_dy = mouse_pos[1] - self.player.rect.centery
        distance = math.sqrt(mouse_dx*mouse_dx + mouse_dy*mouse_dy)
        
        # Default to right if mouse is exactly on player (extremely rare case)
        dx, dy = 1, 0
        
        # Use direct mouse vector for precise aiming
        if distance > 0:
            dx = mouse_dx / distance
            dy = mouse_dy / distance
        
        # Shoot arrow - pass the mouse_pos to the player as legacy parameter
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
        """Remove all arrows when warping between levels or resetting the game"""
        if hasattr(self, 'bow') and self.bow:
            self.bow.arrows = []
            print("Cleared all arrows")