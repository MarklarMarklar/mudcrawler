import pygame
import math
import random
import os
import heapq
import glob
from config import *
from asset_manager import get_asset_manager
from sound_manager import get_sound_manager

class BossProjectile(pygame.sprite.Sprite):
    def __init__(self, x, y, direction, speed=1.4, damage=25, color=(255, 0, 0), 
                 is_orbiting=False, orbit_boss=None, orbit_angle=0, orbit_radius=0, orbit_speed=0, 
                 become_stationary=False, stationary_time=0, is_homing=False, boss_level=None,
                 spawn_secondary=False, spawn_time=0):  # Added new parameters
        super().__init__()
        self.x = x
        self.y = y
        self.direction = direction
        self.speed = speed
        self.damage = damage
        self.color = color
        self.is_orbiting = is_orbiting
        self.orbit_boss = orbit_boss
        self.orbit_angle = orbit_angle
        self.orbit_radius = orbit_radius
        self.orbit_speed = orbit_speed
        self.boss_level = boss_level  # Store which boss created this projectile
        
        # Stationary projectile properties (for boss 5)
        self.become_stationary = become_stationary
        self.is_stationary = False
        self.stationary_time = stationary_time
        self.stationary_start_time = 0
        self.stationary_duration = 0  # How long the projectile stays stationary
        
        # Homing projectile properties (for boss 6)
        self.is_homing = is_homing
        self.homing_strength = 0.03  # How quickly to adjust direction (lower = more gradual)
        self.max_homing_time = 3000  # Stop homing after 3 seconds
        self.homing_start_time = pygame.time.get_ticks()
        self.player_target = None  # Will store reference to player
        
        self.asset_manager = get_asset_manager()
        
        # Animation properties for boss 8 projectiles
        self.animation_frames = []
        self.animation_frame_index = 0
        self.animation_speed = 0.1  # How fast to cycle through frames
        self.animation_timer = 0
        
        # For boss 8, use the fire_ball animation for all projectiles
        if boss_level == 8:
            fire_ball_path = os.path.join(BOSS_SPRITES_PATH, "fire_ball.png")
            if os.path.exists(fire_ball_path):
                print(f"Loading fire_ball animation for boss 8 projectile")
                
                # Load the sprite sheet
                sprite_sheet = self.asset_manager.load_image(fire_ball_path)
                
                # Calculate frame width based on 5 frames in the sprite sheet
                frame_width = sprite_sheet.get_width() // 5
                frame_height = sprite_sheet.get_height()
                
                # Determine the appropriate size - 150% of normal size
                projectile_size = int(TILE_SIZE//2 * 2)
                
                # Adjust size for orbiting projectiles (to match others)
                if is_orbiting:
                    # Use the same size for consistency
                    projectile_size = int(TILE_SIZE//1.5 * 1.5)
                
                # Extract individual frames
                for i in range(5):
                    # Create a new surface for each frame
                    frame = pygame.Surface((frame_width, frame_height), pygame.SRCALPHA)
                    # Copy the specific region from the sprite sheet
                    frame.blit(sprite_sheet, (0, 0), (i * frame_width, 0, frame_width, frame_height))
                    
                    # Scale the frame to 150% of the normal size
                    scaled_frame = pygame.transform.scale(frame, (projectile_size, projectile_size))
                    self.animation_frames.append(scaled_frame)
                
                # Set the initial image to the first frame
                self.image = self.animation_frames[0]
                self.original_image = self.image.copy()
                print(f"Created {len(self.animation_frames)} animation frames for boss 8 projectile")
            else:
                print(f"Fire ball image not found at {fire_ball_path}, using fallback")
                self.choose_standard_projectile_image(is_orbiting, color)
        else:
            # Use standard projectile images for other bosses
            self.choose_standard_projectile_image(is_orbiting, color)
        
        self.rect = self.image.get_rect()
        self.rect.centerx = x
        self.rect.centery = y
        
        # Movement properties
        self.distance_traveled = 0
        self.max_distance = TILE_SIZE * 10  # Projectiles disappear after traveling this distance
        
        # Orbiting projectile properties
        self.is_orbiting = is_orbiting
        self.orbit_boss = orbit_boss      # Reference to the boss object
        self.orbit_angle = orbit_angle    # Current angle in radians
        self.orbit_radius = orbit_radius  # Base distance from boss
        self.base_orbit_radius = orbit_radius  # Store the base radius for pulsing effect
        self.orbit_speed = orbit_speed    # Angular speed in radians per update
        self.pulse_time = 0               # Time counter for orbit pulsing
        
        # Stationary projectile properties
        self.become_stationary = become_stationary
        self.stationary_time = stationary_time  # When to become stationary
        self.is_stationary = False
        
        # For Boss 8 floor projectiles, leave creation_time at 0 until activated
        # For all other projectiles, initialize it now
        if not (boss_level == 8 and become_stationary):
            self.creation_time = pygame.time.get_ticks()
        else:
            self.creation_time = 0  # Will be set when activated
            
        self.stationary_duration = 0  # How long to stay stationary (0 = forever)
        
        # Special properties for Boss 8 floor projectiles
        self.is_floor_projectile = boss_level == 8 and become_stationary
        self.is_active = False  # Will be set to True when activated after casting
        self.warning_pulse = 0  # For warning effect during casting
        self.warning_pulse_rate = 0.1
        
        # Trail effect properties
        self.trail_enabled = True
        self.position_history = []
        self.max_trail_length = 8  # Number of previous positions to remember
        self.trail_update_rate = 2  # Update trail every N frames
        self.trail_frame_counter = 0
        
        # For regular projectiles, add a pulsing effect
        if not is_orbiting:
            self.pulse_counter = 0
            self.pulse_rate = 0.1
        else:
            # For ghost projectiles, use a slower pulse rate
            self.pulse_counter = 0
            self.pulse_rate = 0.05
        
        # Secondary projectile properties
        self.spawn_secondary = spawn_secondary
        self.spawn_time = spawn_time
        self.has_spawned = False
    
    def choose_standard_projectile_image(self, is_orbiting, color):
        """Choose the appropriate image for non-boss 8 projectiles"""
        # For orbiting projectiles, use the ghost sprite instead of a colored ball
        if is_orbiting:
            # Use new path for boss 5 orbiting projectiles
            ghost_path = os.path.join(BOSS_SPRITES_PATH, "orbiting_projectile.png")
            
            if os.path.exists(ghost_path):
                # Load and scale the ghost image
                self.image = self.asset_manager.load_image(ghost_path, scale=(TILE_SIZE//1.5, TILE_SIZE//1.5))
                self.original_image = self.image.copy()
            else:
                print(f"Orbiting projectile image not found at {ghost_path}, using fallback")
                # Try old path as fallback
                old_ghost_path = os.path.join(ENEMY_SPRITES_PATH, "ghost", "ghost.png")
                if os.path.exists(old_ghost_path):
                    self.image = self.asset_manager.load_image(old_ghost_path, scale=(TILE_SIZE//1.5, TILE_SIZE//1.5))
                    self.original_image = self.image.copy()
                    print(f"Using fallback ghost texture from {old_ghost_path}")
                else:
                    print(f"Fallback ghost image not found, creating a basic projectile")
                    self.create_projectile_image(color)
        else:
            # For non-orbiting projectiles, use the energy ball texture
            energy_ball_path = os.path.join(BOSS_SPRITES_PATH, "energy_ball.png")
            print(f"Looking for energy ball at: {energy_ball_path}")
            if os.path.exists(energy_ball_path):
                print(f"Energy ball texture found!")
                # Load and scale the energy ball image
                self.image = self.asset_manager.load_image(energy_ball_path, scale=(TILE_SIZE//1.5, TILE_SIZE//1.5))
                self.original_image = self.image.copy()
            else:
                print(f"Energy ball image not found at {energy_ball_path}, using fallback")
                self.create_projectile_image(color)
    
    def create_projectile_image(self, color):
        """Create a colored ball projectile image"""
        # Create the projectile image - make it larger and more visible
        self.image = pygame.Surface((TILE_SIZE//1.5, TILE_SIZE//1.5), pygame.SRCALPHA)
        
        # Store the main color
        self.color = color
        
        # Make lighter versions of the color for the glow effect
        lighter_color = tuple(min(255, c + 100) for c in color) + (180,)
        lightest_color = tuple(min(255, c + 200) for c in color) + (120,)
        
        # Draw a colored circle with a glow effect
        radius = int(TILE_SIZE//3)
        pygame.draw.circle(self.image, color, (radius, radius), radius)  # Main color center
        pygame.draw.circle(self.image, lighter_color, (radius, radius), radius-2)  # Lighter inner
        pygame.draw.circle(self.image, lightest_color, (radius, radius), radius-4)  # Even lighter core
        
        # Store original image for pulsing
        self.original_image = self.image.copy()
    
    def update(self):
        current_time = pygame.time.get_ticks()
        
        # Check if we need to spawn secondary projectiles
        if self.spawn_secondary and not self.has_spawned and current_time - self.creation_time >= self.spawn_time:
            self.spawn_secondary_projectiles()
            self.has_spawned = True
        
        # Update warning pulse for Boss 8 floor projectiles during casting
        if self.is_floor_projectile and self.creation_time == 0:
            self.warning_pulse += self.warning_pulse_rate
            # Pulse will be used in draw method for visual effect
        
        # Update animation for boss 8 projectiles
        if self.boss_level == 8 and self.animation_frames:
            self.animation_timer += self.animation_speed
            if self.animation_timer >= 1:
                self.animation_timer = 0
                self.animation_frame_index = (self.animation_frame_index + 1) % len(self.animation_frames)
                old_center = self.rect.center
                self.image = self.animation_frames[self.animation_frame_index]
                self.rect = self.image.get_rect()
                self.rect.center = old_center
        
        # Update position history for trailing effect
        if self.trail_enabled:
            self.trail_frame_counter += 1
            if self.trail_frame_counter >= self.trail_update_rate:
                self.trail_frame_counter = 0
                # Store both position and current sprite image
                self.position_history.append((
                    self.rect.x, 
                    self.rect.y, 
                    self.image.copy()  # Store a copy of the current sprite
                ))
                
                if len(self.position_history) > self.max_trail_length:
                    self.position_history.pop(0)
        
        # Check if it's time to become stationary
        if self.become_stationary and not self.is_stationary:
            if current_time - self.creation_time >= self.stationary_time:
                self.is_stationary = True
                
        # Handle different movement types
        if self.is_orbiting and self.orbit_boss:
            # Check if boss is still alive
            if not self.orbit_boss or self.orbit_boss.health <= 0:
                self.kill()
                return
                
            # Update orbital position
            old_angle = self.orbit_angle
            self.orbit_angle += self.orbit_speed
            
            # Update pulsing radius
            self.pulse_time += 0.02
            pulse_factor = math.sin(self.pulse_time) * 0.3  # 30% variation in radius
            current_radius = self.base_orbit_radius * (1 + pulse_factor)
            
            # Calculate new position based on boss's current position
            boss_x = self.orbit_boss.rect.centerx
            boss_y = self.orbit_boss.rect.centery
            
            # Calculate position on the orbital circle with pulsing radius
            self.rect.centerx = boss_x + math.cos(self.orbit_angle) * current_radius
            self.rect.centery = boss_y + math.sin(self.orbit_angle) * current_radius
            
            # For ghost sprite, rotate to face movement direction
            if hasattr(self, 'original_image'):
                # Calculate movement direction (tangent to circle)
                movement_angle = self.orbit_angle + math.pi/2  # Tangent is 90° to radius
                
                # Convert to degrees for rotation
                rotation_degrees = math.degrees(movement_angle) % 360
                
                # Make ghost face the right direction
                if rotation_degrees > 90 and rotation_degrees < 270:
                    # Facing left - flip the sprite
                    rotated = pygame.transform.flip(self.original_image, True, False)
                else:
                    # Facing right - use original
                    rotated = self.original_image.copy()
                
                # Update the image with rotation applied
                self.image = rotated
        elif self.is_homing and hasattr(self, 'player_target') and self.player_target:
            # Only home for a limited time
            if current_time - self.homing_start_time < self.max_homing_time:
                # Calculate direction to player
                dx = self.player_target.rect.centerx - self.rect.centerx
                dy = self.player_target.rect.centery - self.rect.centery
                distance = math.sqrt(dx * dx + dy * dy)
                
                if distance > 0:
                    # Normalize
                    target_dx = dx / distance
                    target_dy = dy / distance
                    
                    # Gradually adjust direction toward player
                    self.direction = (
                        self.direction[0] * (1 - self.homing_strength) + target_dx * self.homing_strength,
                        self.direction[1] * (1 - self.homing_strength) + target_dy * self.homing_strength
                    )
                    
                    # Normalize the direction vector
                    direction_length = math.sqrt(self.direction[0]**2 + self.direction[1]**2)
                    if direction_length > 0:
                        self.direction = (
                            self.direction[0] / direction_length,
                            self.direction[1] / direction_length
                        )
            
            # Move the projectile with potentially adjusted direction
            dx = self.direction[0] * self.speed
            dy = self.direction[1] * self.speed
            self.rect.x += dx
            self.rect.y += dy
            
            # Track distance traveled
            self.distance_traveled += math.sqrt(dx*dx + dy*dy)
            
            # Update trail for homing projectiles
            if self.trail_enabled:
                self.trail_frame_counter += 1
                if self.trail_frame_counter >= self.trail_update_rate:
                    self.trail_frame_counter = 0
                    # Store position and image
                    self.position_history.append((
                        self.rect.x, 
                        self.rect.y, 
                        self.image.copy()
                    ))
                    
                    if len(self.position_history) > self.max_trail_length:
                        self.position_history.pop(0)
        elif not self.is_stationary:
            # Regular projectile movement for non-orbiting, non-stationary projectiles
            # Move the projectile
            dx = self.direction[0] * self.speed
            dy = self.direction[1] * self.speed
            self.rect.x += dx
            self.rect.y += dy
            
            # Track distance traveled
            self.distance_traveled += math.sqrt(dx*dx + dy*dy)
            
            # Check if the projectile should be destroyed
            if self.distance_traveled >= self.max_distance:
                self.kill()
        else:
            # Projectile is stationary - check if it should expire
            if self.stationary_duration > 0 and self.creation_time > 0:
                time_as_stationary = current_time - self.creation_time
                if time_as_stationary >= self.stationary_duration:
                    self.kill()
                    return
            
        # Update pulsing effect
        self.pulse_counter += self.pulse_rate
        scale_factor = 0.9 + 0.2 * abs(math.sin(self.pulse_counter))  # Oscillate between 0.9 and 1.1 size
        
        if not self.is_orbiting:
            # Only apply scale pulsing to non-ghost projectiles
            new_width = int(self.original_image.get_width() * scale_factor)
            new_height = int(self.original_image.get_height() * scale_factor)
            
            # Create a new scaled image for the pulse effect
            self.image = pygame.transform.scale(self.original_image, (new_width, new_height))
        
            # Keep the projectile centered
            old_center = self.rect.center
            self.rect = self.image.get_rect()
            self.rect.center = old_center
    
    def draw(self, surface):
        # Draw trailing effect first (under the main sprite)
        if self.trail_enabled and self.position_history:
            # Draw each position in the history
            for i, (x, y, img) in enumerate(self.position_history):
                # Gradually fade out older trail segments
                alpha = int(255 * (i / len(self.position_history)))
                # Create a copy with adjusted alpha
                fade_img = img.copy()
                fade_img.set_alpha(alpha)
                surface.blit(fade_img, (x, y))
        
        # Special rendering for Boss 8 floor projectiles
        if self.is_floor_projectile:
            if self.creation_time == 0:
                # Just draw the main projectile sprite
                surface.blit(self.image, self.rect.topleft)
            else:
                # Just draw the main projectile sprite
                surface.blit(self.image, self.rect.topleft)
        else:
            # Normal projectile rendering
            surface.blit(self.image, self.rect.topleft)
            
            # Draw additional effects for orbiting projectiles
            if self.is_orbiting and hasattr(self, 'orbit_boss') and self.orbit_boss:
                # For boss 8, draw a small flame trail behind orbiting projectiles
                if hasattr(self, 'boss_level') and self.boss_level == 8:
                    # Create a very small flame trail
                    trail_size = int(TILE_SIZE * 0.2)  # Reduced from 0.4
                    trail_surface = pygame.Surface((trail_size * 2, trail_size * 2), pygame.SRCALPHA)
                    
                    # Calculate trail direction (opposite to orbital movement)
                    trail_angle = self.orbit_angle - math.pi  # Opposite direction
                    
                    # Draw the flame trail as a gradient
                    for radius in range(trail_size, 0, -3):  # Larger steps for fewer circles
                        alpha = int(80 * (radius / trail_size))  # Reduced alpha
                        color = (255, 100 + radius % 100, 0, alpha)  # Orange-red
                        
                        # Calculate offset based on angle
                        offset_x = int(math.cos(trail_angle) * (trail_size - radius) * 0.5)
                        offset_y = int(math.sin(trail_angle) * (trail_size - radius) * 0.5)
                        
                        # Draw the flame circle with offset
                        pygame.draw.circle(trail_surface, color, 
                                          (trail_size + offset_x, trail_size + offset_y), radius)
                    
                    # Position the trail behind the projectile
                    trail_x = self.rect.centerx - trail_size
                    trail_y = self.rect.centery - trail_size
                    surface.blit(trail_surface, (trail_x, trail_y))
                    
                    # Draw connection line AFTER the trail but BEFORE the projectile
                    
                # Draw a faint connection line to the boss
                line_start = self.rect.center
                if hasattr(self.orbit_boss, 'rect'):
                    line_end = self.orbit_boss.rect.center
                    
                    # Create a semi-transparent surface for the line
                    line_surface = pygame.Surface((abs(line_start[0] - line_end[0]) + 4, 
                                                 abs(line_start[1] - line_end[1]) + 4), pygame.SRCALPHA)
                    
                    # Adjust coordinates for the line surface
                    local_start = (2, 2)
                    local_end = (line_surface.get_width() - 2, line_surface.get_height() - 2)
                    if line_start[0] > line_end[0]:
                        local_start, local_end = (local_end[0], local_start[1]), (local_start[0], local_end[1])
                    if line_start[1] > line_end[1]:
                        local_start, local_end = (local_start[0], local_end[1]), (local_end[0], local_start[1])
                    
                    # Draw pulsing energy line
                    for i in range(1, 4):
                        alpha = 100 - i * 25
                        width = 5 - i
                        
                        # For boss 8, use orange-red color for the connection line
                        if hasattr(self, 'boss_level') and self.boss_level == 8:
                            line_color = (255, 100, 0, alpha)  # Orange-red for fire
                        else:
                            line_color = (100, 100, 255, alpha)  # Blue for other bosses
                            
                        pygame.draw.line(line_surface, line_color, local_start, local_end, width)
                    
                    # Position and blit the line surface
                    line_x = min(line_start[0], line_end[0]) - 2
                    line_y = min(line_start[1], line_end[1]) - 2
                    surface.blit(line_surface, (line_x, line_y))
                
                # Draw the orbiting projectile on top of all effects
                if hasattr(self, 'boss_level') and self.boss_level == 8:
                    # For boss 8, redraw the projectile to ensure it's on top
                    surface.blit(self.image, self.rect.topleft)
        
        # Add a glowing core to all projectiles
        if not self.is_orbiting:
            # For Boss 8 projectiles, use a smaller core to not obscure the fire animation
            if hasattr(self, 'boss_level') and self.boss_level == 8:
                # No core for boss 8 projectiles
                pass
            else:
                # Create a small white core at the center for extra brightness (original behavior)
                core_size = int(TILE_SIZE // 3)
                core_surface = pygame.Surface((core_size, core_size), pygame.SRCALPHA)
                
                # White core with high alpha
                pygame.draw.circle(core_surface, (255, 255, 255, 200), (core_size // 2, core_size // 2), core_size // 2)
                
                # Draw the core centered in the projectile
                core_x = self.rect.centerx - core_size // 2
                core_y = self.rect.centery - core_size // 2
                surface.blit(core_surface, (core_x, core_y))
    
    def check_collision(self, player_rect):
        """Check if projectile collides with player"""
        # For Boss 8 floor projectiles, check if they've been activated
        if hasattr(self, 'boss_level') and self.boss_level == 8 and self.is_stationary:
            # Only allow damage after casting has been completed
            # During casting, creation_time=0 and projectiles are visible but don't damage
            # After casting completes, creation_time is set to the current time in the boss's update method
            if self.creation_time == 0:
                return False
                
        if self.rect.colliderect(player_rect):
            # Collision detected and projectile is in a damage-dealing state
            return True
        return False

    def spawn_secondary_projectiles(self):
        """Spawn three projectiles in a 360-degree pattern"""
        if not hasattr(self.orbit_boss, 'projectiles'):
            return
            
        # Create 3 projectiles at 120-degree intervals
        for i in range(3):
            angle = (i * 2 * math.pi / 3) + random.uniform(0, math.pi/6)  # Add slight randomness
            dx = math.cos(angle)
            dy = math.sin(angle)
            
            # Create new projectile with same properties but no secondary spawn
            secondary = BossProjectile(
                self.rect.centerx,
                self.rect.centery,
                (dx, dy),
                self.speed,
                self.damage,
                self.color,
                boss_level=self.boss_level,
                spawn_secondary=False  # Prevent infinite spawning
            )
            
            # Add to boss's projectile group
            self.orbit_boss.projectiles.add(secondary)

class Enemy(pygame.sprite.Sprite):
    def __init__(self, x, y, enemy_type, level, level_instance=None):
        super().__init__()
        self.asset_manager = get_asset_manager()
        self.sound_manager = get_sound_manager()
        self.enemy_type = enemy_type
        
        # Handle case where enemy_type directly specifies the level (e.g., 'level9')
        if enemy_type and enemy_type.startswith('level') and enemy_type in ENEMY_TYPES:
            self.enemy_data = ENEMY_TYPES[enemy_type]
            print(f"Using enemy type {enemy_type} directly")
        else:
            # Default to using the level parameter
            self.enemy_data = ENEMY_TYPES[f'level{level}']
        
        # Store level information
        self.level = level
        self.level_instance = level_instance
        
        # Enemy ID for collision tracking
        self.id = id(self)
        
        # Collision avoidance timers and flags
        self.ignore_collision_until = 0  # Time until which to ignore collisions with other enemies
        self.last_enemy_collision_time = 0  # Last time this enemy collided with another
        self.last_collided_with = set()  # Set of IDs of recently collided enemies
        
        # Sprite direction flag (all sprites face right by default)
        self.facing_right = True
        
        # Animation properties
        self.animations = {
            'idle': {'up': [], 'down': [], 'left': [], 'right': []},
            'walk': {'up': [], 'down': [], 'left': [], 'right': []},
            'attack': {'up': [], 'down': [], 'left': [], 'right': []}
        }
        
        # Get the enemy name
        enemy_name = self.enemy_data['name'].lower().replace(' ', '_')
        
        # For level 6 enemies, use wizard sprites and apply to all directions at once
        if level == 6:
            # Create default placeholder first
            placeholder = pygame.Surface((TILE_SIZE, TILE_SIZE))
            placeholder.fill(RED)
            font = pygame.font.Font(None, 16)
            text = font.render("Wizard", True, WHITE)
            text_rect = text.get_rect(center=(TILE_SIZE//2, TILE_SIZE//2))
            placeholder.blit(text, text_rect)
            
            # Initialize all animations with placeholder
            for direction in ['down', 'up', 'left', 'right']:
                self.animations['idle'][direction] = [placeholder]
                self.animations['walk'][direction] = [placeholder]
                self.animations['attack'][direction] = [placeholder]
            
            # Try to load a wizard sprite
            wizard_folder = os.path.join(ENEMY_SPRITES_PATH, "wizard")
            custom_texture_path = None
            
            if os.path.exists(wizard_folder):
                wizard_files = glob.glob(os.path.join(wizard_folder, "*.png"))
                if wizard_files:
                    custom_texture_path = random.choice(wizard_files)
                    print(f"Using wizard texture for level 6 enemy: {os.path.basename(custom_texture_path)}")
            
            # If we found a wizard texture, use it for all directions and states
            if custom_texture_path and os.path.exists(custom_texture_path):
                try:
                    texture = self.asset_manager.load_image(custom_texture_path, scale=(TILE_SIZE, TILE_SIZE))
                    # Use the same texture for all animation states and directions
                    for direction in ['down', 'up', 'left', 'right']:
                        self.animations['idle'][direction] = [texture]
                        self.animations['walk'][direction] = [texture]
                        self.animations['attack'][direction] = [texture]
                    print(f"Successfully loaded wizard texture for level 6 enemy")
                except Exception as e:
                    print(f"Error loading wizard texture: {e}")
        else:
            # Original animation loading for non-level 6 enemies
            # Load animations for each direction
            for direction in ['down', 'up', 'left', 'right']:
                # Create default placeholder first
                placeholder = pygame.Surface((TILE_SIZE, TILE_SIZE))
                placeholder.fill(RED)
                font = pygame.font.Font(None, 16)
                text = font.render(enemy_name[:8], True, WHITE)
                text_rect = text.get_rect(center=(TILE_SIZE//2, TILE_SIZE//2))
                placeholder.blit(text, text_rect)
                
                # Set default animations to placeholder
                self.animations['idle'][direction] = [placeholder]
                self.animations['walk'][direction] = [placeholder]
                self.animations['attack'][direction] = [placeholder]
                
                # Check if we have a specific texture selected for this enemy type in the level
                selected_texture = None
                custom_texture_path = None
                
                if self.level_instance:
                    if enemy_name == 'skeleton':
                        selected_texture = self.level_instance.selected_skeleton_texture
                    elif enemy_name == 'slime':
                        selected_texture = self.level_instance.selected_slime_texture
                    elif enemy_name == 'ghost':
                        selected_texture = self.level_instance.selected_ghost_texture
                    elif enemy_name == 'goblin':
                        selected_texture = self.level_instance.selected_goblin_texture
                    elif enemy_name == 'dark_knight':
                        selected_texture = self.level_instance.selected_knight_texture
                    elif enemy_name == 'wizard' and self.level == 6:
                        selected_texture = self.level_instance.selected_wizard_texture
                    elif enemy_name == 'demon' and self.level == 7:
                        selected_texture = self.level_instance.selected_demon_texture
                    elif enemy_name == 'dragon_spawn' and self.level == 8:
                        selected_texture = self.level_instance.selected_dragon_texture
                    elif enemy_name == 'shadow' and self.level == 9:
                        selected_texture = self.level_instance.selected_shadow_texture
                    elif enemy_name == 'dark_elf' and self.level == 10:
                        selected_texture = self.level_instance.selected_elf_texture
                        
                    if selected_texture:
                        custom_texture_path = selected_texture
                        print(f"Using custom {enemy_name} texture: {os.path.basename(custom_texture_path)}")
                
                # If we have a custom texture, use it
                if custom_texture_path and os.path.exists(custom_texture_path):
                    try:
                        texture = self.asset_manager.load_image(custom_texture_path, scale=(TILE_SIZE, TILE_SIZE))
                        # Use the same texture for all animation states and directions
                        self.animations['idle'][direction] = [texture]
                        self.animations['walk'][direction] = [texture]
                        self.animations['attack'][direction] = [texture]
                        print(f"Successfully loaded custom {enemy_name} texture")
                    except Exception as e:
                        print(f"Error loading custom {enemy_name} texture: {e}")
                else:
                    # Fallback to the regular animation loading logic
                    # Set up base path for this enemy
                    base_path = os.path.join(ENEMY_SPRITES_PATH, enemy_name)
                    
                    # Now try to load actual animations but don't crash if they're missing
                    try:
                        if os.path.exists(base_path):
                            idle_path = os.path.join(base_path, f"idle_{direction}")
                            if os.path.exists(idle_path):
                                self.animations['idle'][direction] = self.asset_manager.load_animation(
                                    idle_path, "idle_", 4, scale=(TILE_SIZE, TILE_SIZE))
                    except Exception as e:
                        print(f"Could not load idle animation for {enemy_name} {direction}: {e}")
                        
                    try:
                        if os.path.exists(base_path):
                            walk_path = os.path.join(base_path, f"walk_{direction}")
                            if os.path.exists(walk_path):
                                self.animations['walk'][direction] = self.asset_manager.load_animation(
                                    walk_path, "walk_", 4, scale=(TILE_SIZE, TILE_SIZE))
                    except Exception as e:
                        print(f"Could not load walk animation for {enemy_name} {direction}: {e}")
                        # Fallback already set above
                        
                    try:
                        if os.path.exists(base_path):
                            attack_path = os.path.join(base_path, f"attack_{direction}")
                            if os.path.exists(attack_path):
                                self.animations['attack'][direction] = self.asset_manager.load_animation(
                                    attack_path, "attack_", 4, scale=(TILE_SIZE, TILE_SIZE))
                    except Exception as e:
                        print(f"Could not load attack animation for {enemy_name} {direction}: {e}")
                        # Fallback already set above
        
        # Animation state
        self.current_state = 'idle'
        self.facing = 'down'  # Default facing direction
        self.frame = 0
        self.animation_speed = 0.15
        self.animation_time = 0
        
        # Set initial image
        self.image = self.animations[self.current_state][self.facing][0]
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        
        # Create a smaller collision rectangle centered within the main rect
        # Reduce size to 40% of original to allow multiple enemies in narrow passages
        collision_width = int(TILE_SIZE * 0.4)
        collision_height = int(TILE_SIZE * 0.4)
        self.collision_rect = pygame.Rect(
            x + (TILE_SIZE - collision_width) // 2,
            y + (TILE_SIZE - collision_height) // 2,
            collision_width,
            collision_height
        )
        
        # Enemy stats
        self.health = self.enemy_data['health']
        self.damage = self.enemy_data['damage']
        self.speed = self.enemy_data['speed']
        self.name = self.enemy_data['name']
        
        # AI behavior
        self.state = 'idle'
        self.detection_range = TILE_SIZE * 5
        self.attack_range = TILE_SIZE * 1
        self.last_attack_time = 0
        self.attack_cooldown = 1000  # 1 second
        self.has_spotted_player = False  # Track if enemy has seen the player
        
        # Pathfinding attributes
        self.path = []  # List of points to follow
        self.path_update_timer = 0
        self.path_update_frequency = 30  # Update path every 30 frames
        self.last_target_position = None  # Last position we pathfound to
        self.movement_failed_counter = 0  # Track consecutive movement failures
        self.max_movement_failures = 5    # After this many failures, recalculate path
        
        # Patrol behavior
        self.patrol_directions = ['up', 'down', 'left', 'right']
        self.patrol_timer = 0
        self.patrol_duration = random.randint(30, 90)  # Random time to move in one direction
        self.patrol_pause_timer = 0
        self.patrol_pause_duration = random.randint(15, 45)  # Random time to pause between movements
        self.patrol_direction = random.choice(self.patrol_directions)
        self.patrol_speed = self.speed * 0.5  # Slower movement during patrol
        self.is_patrolling = True  # Start with patrol active
        self.is_patrol_paused = False
        
        # Movement properties
        self.velocity_x = 0
        self.velocity_y = 0
        
        # Respawn mechanic for level 3 minions
        self.is_dead = False  # Whether the enemy is in "dead" state (blood puddle)
        self.resurrection_time = 0  # When the enemy will resurrect
        self.original_texture = None  # Store the original texture for restoration
        self.blood_puddle_texture = None  # Blood puddle texture when "dead"
        self.max_health = self.health  # Store max health for restoration
        self.resurrection_sound_played = False  # Track if resurrection sound has played
        
        # Damage tracking - prevent multiple hits from same sword swing
        self.has_been_hit_this_swing = False
        
        # Initialize projectile capabilities
        self.projectiles = pygame.sprite.Group()
        self.can_shoot = level == 6  # Only level 6 enemies can shoot
        
        if self.can_shoot:
            self.projectile_cooldown = 6000  # 6 seconds between shots
            self.last_shot_time = random.randint(0, 3000)  # Randomize initial cooldown
            self.projectile_speed = 2.5  # Increased from 1.2 to make projectiles faster
            self.projectile_damage = self.damage * 0.8  # 80% of normal damage
            self.projectile_color = (200, 50, 50)  # Red projectiles
        
        # Enemy state and animation properties
        self.state = 'idle'  # idle, chase, attack, patrol
        self.current_state = 'idle'  # For animation purposes
        self.facing = 'down'  # Initial facing direction
        self.frame = 0
        self.animation_time = 0
        self.animation_speed = 0.2
        
        # Jump attack animation properties
        self.is_jumping = False
        self.jump_start_time = 0
        self.jump_duration = 300  # ms
        self.original_pos = (self.rect.x, self.rect.y)
        self.jump_target_pos = (0, 0)
        self.jump_return_time = 0
        self.jump_progress = 0
    
    def take_damage(self, amount):
        self.health -= amount
        if self.health <= 0:
            self.health = 0
            return True  # Enemy died
        return False
        
    def find_path(self, start_x, start_y, target_x, target_y, level):
        """Find a path from start to target position using A* algorithm"""
        # Convert pixel positions to tile positions
        start_tile_x, start_tile_y = start_x // TILE_SIZE, start_y // TILE_SIZE
        target_tile_x, target_tile_y = target_x // TILE_SIZE, target_y // TILE_SIZE
        
        # Get the current room
        if not hasattr(level, 'rooms') or level.current_room_coords not in level.rooms:
            return []
            
        room = level.rooms[level.current_room_coords]
        
        # Check if target position is valid
        if not (0 <= target_tile_x < room.width and 0 <= target_tile_y < room.height):
            return []
            
        # Check if we're already at the target
        if (start_tile_x, start_tile_y) == (target_tile_x, target_tile_y):
            return []
            
        # Ensure target is not a wall
        if room.tiles[target_tile_y][target_tile_x] == 1:
            # Try to find a nearby floor tile
            directions = [(0, -1), (1, 0), (0, 1), (-1, 0)]  # Only cardinal directions
            for dx, dy in directions:
                new_tx, new_ty = target_tile_x + dx, target_tile_y + dy
                if (0 <= new_tx < room.width and 0 <= new_ty < room.height and 
                    room.tiles[new_ty][new_tx] == 0):
                    # Found valid floor tile near target
                    target_tile_x, target_tile_y = new_tx, new_ty
                    break
            else:
                # No valid floor tile found near target
                return []
            
        # Get all enemies from current room for dynamic obstacle avoidance
        other_enemies = []
        enemy_paths = []
        if level.current_room_coords in level.rooms:
            room = level.rooms[level.current_room_coords]
            other_enemies = [e for e in room.enemies if (e.rect.x // TILE_SIZE, e.rect.y // TILE_SIZE) != (start_tile_x, start_tile_y)]
            
            # Collect current paths that other enemies are following
            for enemy in other_enemies:
                if hasattr(enemy, 'path') and enemy.path:
                    for point in enemy.path:
                        tile_x, tile_y = point[0] // TILE_SIZE, point[1] // TILE_SIZE
                        if 0 <= tile_x < room.width and 0 <= tile_y < room.height:
                            enemy_paths.append((tile_x, tile_y))
        
        # Generate a small offset to target for this specific enemy 
        # This helps create varied paths for multiple enemies
        offset_radius = 3  # Tiles
        if not hasattr(self, 'target_offset'):
            # Only calculate this once per enemy to maintain path stability
            angle = random.uniform(0, 2 * math.pi)
            offset_distance = random.uniform(1, offset_radius)
            self.target_offset = (
                int(math.cos(angle) * offset_distance),
                int(math.sin(angle) * offset_distance)
            )
        
        # Create alternate targets around the original target
        alternate_targets = []
        for dx in range(-offset_radius, offset_radius + 1):
            for dy in range(-offset_radius, offset_radius + 1):
                alt_x, alt_y = target_tile_x + dx, target_tile_y + dy
                if (0 <= alt_x < room.width and 0 <= alt_y < room.height and 
                    room.tiles[alt_y][alt_x] == 0 and  # Must be a floor tile
                    (dx*dx + dy*dy) <= offset_radius*offset_radius):  # Within radius
                    # Calculate distance from original target
                    dist_from_target = math.sqrt(dx*dx + dy*dy)
                    alternate_targets.append(((alt_x, alt_y), dist_from_target))
        
        # Sort by distance from target
        alternate_targets.sort(key=lambda x: x[1])
        
        # Add the original target as the first option
        alternate_targets.insert(0, ((target_tile_x, target_tile_y), 0))
        
        # Try finding a path, first to original target, then to alternates
        # Prioritize targets that aren't already on another enemy's path
        for (alt_target_x, alt_target_y), _ in alternate_targets:
            # Skip if this point is on another enemy's path
            if (alt_target_x, alt_target_y) in enemy_paths and (alt_target_x, alt_target_y) != (target_tile_x, target_tile_y):
                continue
                
            # A* algorithm
            open_set = []  # Priority queue of nodes to explore
            closed_set = set()  # Set of explored nodes
            
            # Add start node to open set
            heapq.heappush(open_set, (0, 0, (start_tile_x, start_tile_y, None)))  # (f_score, tiebreaker, (x, y, parent))
            
            # Dict to store g_scores (cost from start to node)
            g_scores = {(start_tile_x, start_tile_y): 0}
            
            # Dict to store f_scores (estimated total cost from start to goal)
            f_scores = {(start_tile_x, start_tile_y): self.manhattan_distance(start_tile_x, start_tile_y, alt_target_x, alt_target_y)}
            
            # Dict to store parent pointers
            came_from = {}
            
            tiebreaker = 0  # To break ties when f_scores are equal
            
            # Define possible movement directions (only cardinal directions)
            directions = [(0, -1), (1, 0), (0, 1), (-1, 0)]  # Up, right, down, left
            
            found_path = False
            max_iterations = 1000  # Prevent infinite loops
            iterations = 0
            
            while open_set and not found_path and iterations < max_iterations:
                iterations += 1
                
                # Get the node with lowest f_score from open set
                _, _, (current_x, current_y, _) = heapq.heappop(open_set)
                
                # Check if we've reached the goal
                if (current_x, current_y) == (alt_target_x, alt_target_y):
                    found_path = True
                    break
                    
                # Skip if we've already explored this node
                if (current_x, current_y) in closed_set:
                    continue
                    
                # Add to closed set
                closed_set.add((current_x, current_y))
                
                # Consider all neighbors
                for dx, dy in directions:
                    neighbor_x, neighbor_y = current_x + dx, current_y + dy
                    
                    # Skip if out of bounds
                    if not (0 <= neighbor_x < room.width and 0 <= neighbor_y < room.height):
                        continue
                        
                    # Skip if it's a wall tile
                    if room.tiles[neighbor_y][neighbor_x] == 1:
                        continue
                        
                    # Skip if we've already explored this neighbor
                    if (neighbor_x, neighbor_y) in closed_set:
                        continue
                    
                    # Calculate tentative g_score (1 for cardinal directions)
                    tentative_g_score = g_scores[(current_x, current_y)] + 1
                    
                    # Add a small penalty for tiles that have enemies nearby
                    # This encourages finding paths that avoid other enemies when possible
                    enemy_penalty = 0
                    for enemy in other_enemies:
                        enemy_tile_x, enemy_tile_y = enemy.rect.centerx // TILE_SIZE, enemy.rect.centery // TILE_SIZE
                        if abs(enemy_tile_x - neighbor_x) <= 1 and abs(enemy_tile_y - neighbor_y) <= 1:
                            enemy_penalty += 1  # Add penalty for each enemy in adjacent tiles
                    
                    # Add penalty for tiles that are on other enemies' paths
                    path_penalty = 0
                    if (neighbor_x, neighbor_y) in enemy_paths:
                        path_penalty = 2
                    
                    tentative_g_score += enemy_penalty * 0.5 + path_penalty  # Scale the penalty to not overwhelm the pathfinding
                    
                    # If we found a better path to this neighbor, update it
                    if (neighbor_x, neighbor_y) not in g_scores or tentative_g_score < g_scores[(neighbor_x, neighbor_y)]:
                        # Update parent pointer
                        came_from[(neighbor_x, neighbor_y)] = (current_x, current_y)
                        
                        # Update g_score
                        g_scores[(neighbor_x, neighbor_y)] = tentative_g_score
                        
                        # Calculate f_score
                        h_score = self.manhattan_distance(neighbor_x, neighbor_y, alt_target_x, alt_target_y)
                        f_score = tentative_g_score + h_score
                        f_scores[(neighbor_x, neighbor_y)] = f_score
                        
                        # Add to open set
                        tiebreaker += 1
                        heapq.heappush(open_set, (f_score, tiebreaker, (neighbor_x, neighbor_y, (current_x, current_y))))
            
            # If we found a path, reconstruct it
            if found_path:
                path = []
                current = (alt_target_x, alt_target_y)
                
                while current in came_from:
                    # Convert tile position to pixel position (center of tile)
                    pixel_x = current[0] * TILE_SIZE + TILE_SIZE // 2
                    pixel_y = current[1] * TILE_SIZE + TILE_SIZE // 2
                    path.append((pixel_x, pixel_y))
                    
                    current = came_from[current]
                    
                # Reverse path (from start to goal)
                path.reverse()
                
                return path
        
        # If we get here, no path was found
        return []
    
    def manhattan_distance(self, x1, y1, x2, y2):
        """Calculate Manhattan distance between two points"""
        return abs(x1 - x2) + abs(y1 - y2)
    
    def check_line_of_sight(self, start_x, start_y, target_x, target_y, level):
        """Check if there's a clear line of sight between two points"""
        # Convert to tile coordinates
        start_tile_x, start_tile_y = int(start_x // TILE_SIZE), int(start_y // TILE_SIZE)
        target_tile_x, target_tile_y = int(target_x // TILE_SIZE), int(target_y // TILE_SIZE)
        
        # Get current room
        if not hasattr(level, 'rooms') or level.current_room_coords not in level.rooms:
            return False
            
        room = level.rooms[level.current_room_coords]
        
        # Use Bresenham's line algorithm to check for walls along the line
        # This is a simplified version for tile-based checking
        dx = abs(target_tile_x - start_tile_x)
        dy = abs(target_tile_y - start_tile_y)
        sx = 1 if start_tile_x < target_tile_x else -1
        sy = 1 if start_tile_y < target_tile_y else -1
        err = dx - dy
        
        x, y = start_tile_x, start_tile_y
        
        while x != target_tile_x or y != target_tile_y:
            # Check if current tile is a wall
            if (0 <= x < room.width and 0 <= y < room.height and room.tiles[y][x] == 1):
                return False  # Wall detected, no line of sight
            
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x += sx
            if e2 < dx:
                err += dx
                y += sy
                
        return True  # No walls detected, clear line of sight
    
    def move_towards_player(self, player):
        """Move towards player using pathfinding"""
        # Calculate distance to player
        dx = player.rect.centerx - self.rect.centerx
        dy = player.rect.centery - self.rect.centery
        distance = math.sqrt(dx * dx + dy * dy)
        
        # Update facing direction based on horizontal movement
        if dx != 0:
            self.facing_right = dx > 0
        
        # If we're in attack range, stop moving
        if distance <= self.attack_range:
            self.velocity_x = 0
            self.velocity_y = 0
            return
        
        # Get current target position
        target_pos = (player.rect.centerx, player.rect.centery)
        
        # Check for crowd avoidance - if there are multiple enemies nearby, try to spread out
        if hasattr(player, 'level') and player.level.current_room_coords in player.level.rooms:
            room = player.level.rooms[player.level.current_room_coords]
            nearby_enemies = []
            for enemy in room.enemies:
                if enemy != self and self.is_nearby(enemy, TILE_SIZE * 1.5):
                    nearby_enemies.append(enemy)
                    
            # If we have multiple nearby enemies, try to move away from the center of the crowd
            if len(nearby_enemies) >= 2:
                self.avoid_crowd(nearby_enemies)
                return
        
        # Update path if:
        # 1. We don't have a path, or
        # 2. Player has moved significantly (more than 2 tiles), or
        # 3. We've hit too many movement failures
        # 4. The timer for path updates has elapsed
        should_update_path = (
            not self.path or
            self.movement_failed_counter >= 2 or  # Reduced from 3 to 2 to recalculate more quickly when stuck
            self.path_update_timer >= self.path_update_frequency or
            (self.last_target_position and 
             ((abs(self.last_target_position[0] - target_pos[0]) > TILE_SIZE * 2) or 
              (abs(self.last_target_position[1] - target_pos[1]) > TILE_SIZE * 2)))
        )
        
        if should_update_path and hasattr(player, 'level'):
            # Find path to player
            self.path = self.find_path(
                self.rect.centerx,
                self.rect.centery,
                player.rect.centerx,
                player.rect.centery,
                player.level
            )
            
            # Reset movement failure counter if we found a path
            if self.path:
                self.movement_failed_counter = 0
                self.last_target_position = target_pos
                self.path_update_timer = 0
            else:
                # If no path found, increment failure counter
                self.movement_failed_counter += 1
                
                # Initialize wall-following behavior when no path is found
                # This helps enemies navigate around obstacles to reach the player
                
                # Normalize direction to player
                if distance > 0:
                    norm_dx = dx / distance
                    norm_dy = dy / distance
                    
                    # Wall-following algorithm:
                    # 1. Start by trying to move in the direction of the player
                    # 2. If blocked, try moving along the wall by testing perpendicular directions
                    # 3. If all directions are blocked, try moving away temporarily to find new paths
                    
                    # Store directions in order of preference
                    directions_to_try = []
                    
                    # First, try cardinal directions closest to player direction
                    if abs(norm_dx) > abs(norm_dy):
                        # Primarily horizontal
                        primary_dir = ('x', (norm_dx / abs(norm_dx)) * self.speed if norm_dx != 0 else 0)
                        secondary_dir = ('y', (norm_dy / abs(norm_dy)) * self.speed if norm_dy != 0 else 0)
                    else:
                        # Primarily vertical
                        primary_dir = ('y', (norm_dy / abs(norm_dy)) * self.speed if norm_dy != 0 else 0)
                        secondary_dir = ('x', (norm_dx / abs(norm_dx)) * self.speed if norm_dx != 0 else 0)
                    
                    # Add primary direction first (toward player)
                    directions_to_try.append(primary_dir)
                    
                    # Then try perpendicular directions (wall-following)
                    directions_to_try.append(secondary_dir)
                    directions_to_try.append(('y', -secondary_dir[1]) if secondary_dir[0] == 'y' else ('x', -secondary_dir[1]))
                    directions_to_try.append(('x', -primary_dir[1]) if primary_dir[0] == 'x' else ('y', -primary_dir[1]))
                    
                    # Test each direction until we find a valid move
                    for direction in directions_to_try:
                        axis, value = direction
                        
                        # Create test rectangle
                        test_rect = self.rect.copy()
                        if axis == 'x':
                            test_rect.x += value * 2  # Look ahead a bit farther
                        else:
                            test_rect.y += value * 2
                        
                        # Check if this move is valid (no collision with walls)
                        if not (hasattr(player, 'level') and player.level.check_collision(test_rect)):
                            # Found valid move, apply it
                            if axis == 'x':
                                self.velocity_x = value
                                self.velocity_y = 0
                                self.facing = 'right' if value > 0 else 'left'
                            else:
                                self.velocity_x = 0
                                self.velocity_y = value
                                self.facing = 'down' if value > 0 else 'up'
                            break
        else:
            # Increment path update timer
            self.path_update_timer += 1
            
        # If we have a path, follow it
        if self.path:
            # Get the next point to move to
            target_x, target_y = self.path[0]
            
            # Calculate direction to next point
            dx = target_x - self.rect.centerx
            dy = target_y - self.rect.centery
            distance = math.sqrt(dx * dx + dy * dy)
            
            # If we're close enough to this point, remove it and move to the next
            if distance < self.speed:
                self.path.pop(0)
                
                # If we've reached the end of the path, stop moving
                if not self.path:
                    self.velocity_x = 0
                    self.velocity_y = 0
                    return
                    
                # Otherwise, get new target
                target_x, target_y = self.path[0]
                dx = target_x - self.rect.centerx
                dy = target_y - self.rect.centery
                distance = math.sqrt(dx * dx + dy * dy)
            
            # Normalize direction and set velocity
            if distance > 0:
                dx = dx / distance
                dy = dy / distance
                
                self.velocity_x = dx * self.speed
                self.velocity_y = dy * self.speed
                
                # Add a small random jitter to avoid perfect alignment with other enemies
                if random.random() < 0.1:  # 10% chance each frame
                    jitter_x = random.uniform(-0.5, 0.5)
                    jitter_y = random.uniform(-0.5, 0.5)
                    
                    self.velocity_x += jitter_x
                    self.velocity_y += jitter_y
                
                # Update facing direction
                if abs(dx) > abs(dy):
                    self.facing = 'right' if dx > 0 else 'left'
                else:
                    self.facing = 'down' if dy > 0 else 'up'
            else:
                # If distance is zero (unlikely), stop moving
                self.velocity_x = 0
                self.velocity_y = 0
                
    def is_nearby(self, other_enemy, distance_threshold):
        """Check if another enemy is within the specified distance threshold"""
        dx = other_enemy.rect.centerx - self.rect.centerx
        dy = other_enemy.rect.centery - self.rect.centery
        distance = math.sqrt(dx * dx + dy * dy)
        return distance < distance_threshold
        
    def avoid_crowd(self, nearby_enemies):
        """Move away from the center of a crowd of enemies"""
        # Calculate center of the crowd (including this enemy)
        total_x = self.rect.centerx
        total_y = self.rect.centery
        count = 1
        
        for enemy in nearby_enemies:
            total_x += enemy.rect.centerx
            total_y += enemy.rect.centery
            count += 1
            
        center_x = total_x / count
        center_y = total_y / count
        
        # Calculate direction away from center
        dx = self.rect.centerx - center_x
        dy = self.rect.centery - center_y
        distance = math.sqrt(dx * dx + dy * dy)
        
        # If we're already away from center, don't move
        if distance > TILE_SIZE * 2:
            self.velocity_x = 0
            self.velocity_y = 0
            return
            
        # Add a bit of randomization to prevent all enemies from moving the same way
        dx += random.uniform(-0.3, 0.3)
        dy += random.uniform(-0.3, 0.3)
        
        # Recalculate distance after adding randomization
        distance = math.sqrt(dx * dx + dy * dy)
        
        # If we're at the exact center (very unlikely), move in a random direction
        if distance < 0.1:
            angle = random.uniform(0, 2 * math.pi)
            dx = math.cos(angle)
            dy = math.sin(angle)
            distance = 1.0
        
        # Set velocity to move away from center with a slightly faster speed to break the group
        if distance > 0:
            norm_dx = dx / distance
            norm_dy = dy / distance
            
            # Use a slightly higher speed for crowd avoidance
            avoid_speed = self.speed * 1.5
            
            self.velocity_x = norm_dx * avoid_speed
            self.velocity_y = norm_dy * avoid_speed
            
            # Update facing direction
            if abs(norm_dx) > abs(norm_dy):
                self.facing = 'right' if norm_dx > 0 else 'left'
            else:
                self.facing = 'down' if norm_dy > 0 else 'up'

    def can_attack(self):
        current_time = pygame.time.get_ticks()
        return current_time - self.last_attack_time >= self.attack_cooldown
        
    def attack(self, player):
        if self.can_attack():
            # Store current time and mark the start of attack
            current_time = pygame.time.get_ticks()
            self.last_attack_time = current_time
            self.current_state = 'attack'
            self.frame = 0  # Reset animation frame
            
            # Start jump attack animation for normal enemies (not for bosses)
            if not isinstance(self, Boss):
                self.is_jumping = True
                self.jump_start_time = current_time
                self.jump_return_time = 0
                self.original_pos = (self.rect.x, self.rect.y)
                
                # Calculate target position (closer to player)
                dx = player.rect.centerx - self.rect.centerx
                dy = player.rect.centery - self.rect.centery
                distance = math.sqrt(dx * dx + dy * dy)
                
                if distance > 0:
                    # Normalize direction vector
                    dx = dx / distance
                    dy = dy / distance
                    
                    # Jump farther toward the player - 75% of distance or up to 1.5 tiles
                    # This makes the jump more visible and aggressive
                    jump_distance = min(distance * 0.75, TILE_SIZE * 1.5) 
                    self.jump_target_pos = (
                        self.rect.x + dx * jump_distance,
                        self.rect.y + dy * jump_distance
                    )
                    
                    print(f"Enemy jumping to attack: {self.original_pos} -> {self.jump_target_pos}")
            
            # Apply damage to player
            return player.take_damage(self.damage)
        return False
        
    def patrol(self):
        """Move in a random direction for a set time, then pause and choose a new direction"""
        # Update patrol timers
        if self.is_patrol_paused:
            self.patrol_pause_timer += 1
            if self.patrol_pause_timer >= self.patrol_pause_duration:
                # Resume patrolling
                self.is_patrol_paused = False
                self.patrol_timer = 0
                self.patrol_direction = random.choice(self.patrol_directions)
                self.patrol_duration = random.randint(30, 90)
        else:
            self.patrol_timer += 1
            if self.patrol_timer >= self.patrol_duration:
                # Pause patrolling
                self.is_patrol_paused = True
                self.patrol_pause_timer = 0
                self.patrol_pause_duration = random.randint(15, 45)
                
                # Stop movement during pause
                self.velocity_x = 0
                self.velocity_y = 0
                return
                
        # Only move if not paused
        if not self.is_patrol_paused:
            # Set velocity based on patrol direction
            if self.patrol_direction == 'up':
                self.velocity_y = -self.patrol_speed
                self.velocity_x = 0
                self.facing = 'up'
            elif self.patrol_direction == 'down':
                self.velocity_y = self.patrol_speed
                self.velocity_x = 0
                self.facing = 'down'
            elif self.patrol_direction == 'left':
                self.velocity_x = -self.patrol_speed
                self.velocity_y = 0
                self.facing = 'left'
            elif self.patrol_direction == 'right':
                self.velocity_x = self.patrol_speed
                self.velocity_y = 0
                self.facing = 'right'
            
            # Set animation state
            self.current_state = 'walk'
    
    def update(self, player):
        # Get current time at the beginning of the method
        current_time = pygame.time.get_ticks()
        
        # Check if in blood puddle state and ready to resurrect
        if self.is_dead:
            # If it's time to resurrect
            if current_time >= self.resurrection_time:
                self.resurrect()
            
            # Skip the rest of the update if still in blood puddle state
            return
        
        # Handle jump attack animation
        if self.is_jumping:
            # Calculate progress of the jump (0.0 to 1.0)
            if self.jump_return_time == 0:
                # Moving toward player
                elapsed = current_time - self.jump_start_time
                progress = min(1.0, elapsed / (self.jump_duration / 2))
                
                # Interpolate position
                self.rect.x = int(self.original_pos[0] + (self.jump_target_pos[0] - self.original_pos[0]) * progress)
                self.rect.y = int(self.original_pos[1] + (self.jump_target_pos[1] - self.original_pos[1]) * progress)
                
                # If reached the player, start returning
                if progress >= 1.0:
                    self.jump_return_time = current_time
            else:
                # Returning to original position
                elapsed = current_time - self.jump_return_time
                progress = min(1.0, elapsed / (self.jump_duration / 2))
                
                # Interpolate position back to original
                self.rect.x = int(self.jump_target_pos[0] + (self.original_pos[0] - self.jump_target_pos[0]) * progress)
                self.rect.y = int(self.jump_target_pos[1] + (self.original_pos[1] - self.jump_target_pos[1]) * progress)
                
                # If returned to original position, end jump
                if progress >= 1.0:
                    self.is_jumping = False
                    self.rect.x = self.original_pos[0]
                    self.rect.y = self.original_pos[1]
            
            # Update animation
            self.animation_time += self.animation_speed
            self.frame = int(self.animation_time) % len(self.animations[self.current_state][self.facing])
            self.image = self.animations[self.current_state][self.facing][self.frame]
            
            # Update collision rect to match main rect
            self.collision_rect.centerx = self.rect.centerx
            self.collision_rect.centery = self.rect.centery
            
            return
            
        # Calculate distance to player
        dx = player.rect.centerx - self.rect.centerx
        dy = player.rect.centery - self.rect.centery
        distance = math.sqrt(dx * dx + dy * dy)
        
        # Current time for cooldown calculations
        current_time = pygame.time.get_ticks()
        
        # Always mark that enemy has spotted player if within detection range
        if distance <= self.detection_range:
            self.has_spotted_player = True
        
        # Update state based on distance to player
        if distance <= self.attack_range:
            # Attack state - use melee attack
            self.state = 'attack'
            self.velocity_x = 0
            self.velocity_y = 0
            self.attack(player)
        elif self.has_spotted_player:
            # Chase state - chase player once spotted (regardless of current distance)
            self.state = 'chase'
            self.current_state = 'walk'
            self.move_towards_player(player)
        else:
            # Patrol state - patrol around until they spot the player
            self.state = 'patrol'
            self.patrol()
        
        # Store the old position to revert if collision happens
        old_rect = self.rect.copy()
        old_collision_rect = self.collision_rect.copy()
        old_velocity_x = self.velocity_x
        old_velocity_y = self.velocity_y
        
        # Ensure player has level attribute before checking collision
        has_level = hasattr(player, 'level') and player.level is not None
        
        # Get all enemies from current room for collision detection
        other_enemies = []
        if has_level and player.level.current_room_coords in player.level.rooms:
            room = player.level.rooms[player.level.current_room_coords]
            other_enemies = [e for e in room.enemies if e != self]
        
        # Save initial priority values - closer enemies to player get higher priority
        if not hasattr(self, 'movement_priority'):
            self.movement_priority = 0
        
        # Update movement priority based on distance to player and time spent waiting
        player_distance = math.sqrt(dx * dx + dy * dy)
        # Priority increases with proximity to player and time spent waiting
        self.movement_priority = (1000 / (player_distance + 1)) + self.movement_failed_counter
        
        # If stuck for too long, temporarily ignore collisions with other enemies
        if self.movement_failed_counter >= 5:
            # Enable collision ignoring for 500ms
            self.ignore_collision_until = current_time + 500
            
            # Record a longer ignore time for enemies we've recently collided with
            for enemy_id in self.last_collided_with:
                # Try to find the enemy with this ID
                for enemy in other_enemies:
                    if id(enemy) == enemy_id:
                        if hasattr(enemy, 'ignore_collision_until'):
                            enemy.ignore_collision_until = current_time + 500
                        break
        
        # Apply a small random jitter to movement if we're in chase state
        if self.state == 'chase' and self.movement_failed_counter > 0:
            jitter_x = random.uniform(-0.5, 0.5)
            jitter_y = random.uniform(-0.5, 0.5)
            self.velocity_x += jitter_x
            self.velocity_y += jitter_y
        
        # Try moving horizontally first
        if self.velocity_x != 0:
            # Move the main rect
            self.rect.x += self.velocity_x
            # Move the collision rect to stay centered
            self.collision_rect.centerx = self.rect.centerx
            
            # Flag to track if we collided with anything
            collision_detected = False
            wall_collision = False
            enemy_collision = False
            colliding_enemy = None
            
            # Check for collision with walls
            if has_level and player.level.check_collision(self.collision_rect):
                collision_detected = True
                wall_collision = True
            
            # Check for collision with other enemies (if not in collision ignore period)
            if current_time < self.ignore_collision_until:
                # We're in collision ignore period, so no enemy collisions
                pass
            else:
                for enemy in other_enemies:
                    # Skip collision check if the other enemy is also ignoring collisions with us
                    if hasattr(enemy, 'ignore_collision_until') and current_time < enemy.ignore_collision_until:
                        continue
                        
                    if self.collision_rect.colliderect(enemy.collision_rect):
                        # Only count as a collision if the other enemy is stationary or has higher priority
                        if (enemy.velocity_x == 0 and enemy.velocity_y == 0) or \
                           (hasattr(enemy, 'movement_priority') and enemy.movement_priority > self.movement_priority):
                            collision_detected = True
                            enemy_collision = True
                            colliding_enemy = enemy
                            
                            # Record this collision
                            self.last_enemy_collision_time = current_time
                            self.last_collided_with.add(id(enemy))
                            if hasattr(enemy, 'last_collided_with'):
                                enemy.last_collided_with.add(id(self))
                            
                            break
            
            # Revert position if collision detected
            if collision_detected:
                # Revert both rects on collision
                self.rect.x = old_rect.x
                self.collision_rect = old_collision_rect.copy()
                
                if enemy_collision and not wall_collision and self.state == 'chase':
                    # For enemy-to-enemy collisions during chase, try to slide around
                    # Determine which direction to slide (perpendicular to movement)
                    if old_velocity_x != 0:
                        # Calculate perpendicular direction (up or down)
                        # Determine slide direction based on relative positions
                        if colliding_enemy and self.rect.centery > colliding_enemy.rect.centery:
                            # Try to slide down
                            slide_y = 2  # Increased from 1 to make the slide more aggressive
                        else:
                            # Try to slide up
                            slide_y = -2  # Increased from -1 to make the slide more aggressive
                            
                        # Try the slide movement
                        self.rect.y += slide_y
                        self.collision_rect.centery = self.rect.centery
                        
                        # If slide causes collision, revert it
                        if (has_level and player.level.check_collision(self.collision_rect) or
                            any(self.collision_rect.colliderect(e.collision_rect) for e in other_enemies if 
                               current_time >= self.ignore_collision_until and
                               (not hasattr(e, 'ignore_collision_until') or current_time >= e.ignore_collision_until) and
                               ((e.velocity_x == 0 and e.velocity_y == 0) or 
                               (hasattr(e, 'movement_priority') and e.movement_priority > self.movement_priority)))):
                            self.rect.y = old_rect.y
                            self.collision_rect.centery = self.rect.centery
                            
                            # Try sliding in the opposite direction
                            self.rect.y -= slide_y
                            self.collision_rect.centery = self.rect.centery
                            
                            # If that causes collision too, revert everything
                            if (has_level and player.level.check_collision(self.collision_rect) or
                                any(self.collision_rect.colliderect(e.collision_rect) for e in other_enemies if 
                                   current_time >= self.ignore_collision_until and
                                   (not hasattr(e, 'ignore_collision_until') or current_time >= e.ignore_collision_until) and
                                   ((e.velocity_x == 0 and e.velocity_y == 0) or 
                                   (hasattr(e, 'movement_priority') and e.movement_priority > self.movement_priority)))):
                                self.rect.y = old_rect.y
                                self.collision_rect.centery = self.rect.centery
                                self.velocity_x = 0
                                self.movement_failed_counter += 1
                    else:
                        self.velocity_x = 0
                        self.movement_failed_counter += 1
                else:
                    self.velocity_x = 0  # Stop horizontal movement on collision
                    if self.state == 'chase':
                        self.movement_failed_counter += 1
                    
                    # Try to move a small step instead of the full velocity
                    if old_velocity_x != 0:  # Prevent division by zero
                        small_step = old_velocity_x / abs(old_velocity_x) * 1  # Just 1 pixel in direction
                        self.rect.x += small_step
                        self.collision_rect.centerx = self.rect.centerx
                        
                        # Check collision again
                        if (has_level and player.level.check_collision(self.collision_rect) or 
                            any(self.collision_rect.colliderect(enemy.collision_rect) for enemy in other_enemies if 
                               current_time >= self.ignore_collision_until and
                               (not hasattr(enemy, 'ignore_collision_until') or current_time >= enemy.ignore_collision_until) and
                               ((enemy.velocity_x == 0 and enemy.velocity_y == 0) or 
                               (hasattr(enemy, 'movement_priority') and enemy.movement_priority > self.movement_priority)))):
                            # Revert the small step too
                            self.rect.x = old_rect.x
                            self.collision_rect.centerx = self.rect.centerx
            else:
                self.movement_failed_counter = 0

        # Then try moving vertically
        if self.velocity_y != 0:
            # Move the main rect
            self.rect.y += self.velocity_y
            # Move the collision rect to stay centered
            self.collision_rect.centery = self.rect.centery
            
            # Flag to track if we collided with anything
            collision_detected = False
            wall_collision = False
            enemy_collision = False
            colliding_enemy = None
            
            # Check for collision with walls
            if has_level and player.level.check_collision(self.collision_rect):
                collision_detected = True
                wall_collision = True
            
            # Check for collision with other enemies (if not in collision ignore period)
            if current_time < self.ignore_collision_until:
                # We're in collision ignore period, so no enemy collisions
                pass
            else:
                for enemy in other_enemies:
                    # Skip collision check if the other enemy is also ignoring collisions with us
                    if hasattr(enemy, 'ignore_collision_until') and current_time < enemy.ignore_collision_until:
                        continue
                        
                    if self.collision_rect.colliderect(enemy.collision_rect):
                        # Only count as a collision if the other enemy is stationary or has higher priority
                        if (enemy.velocity_x == 0 and enemy.velocity_y == 0) or \
                           (hasattr(enemy, 'movement_priority') and enemy.movement_priority > self.movement_priority):
                            collision_detected = True
                            enemy_collision = True
                            colliding_enemy = enemy
                            
                            # Record this collision
                            self.last_enemy_collision_time = current_time
                            self.last_collided_with.add(id(enemy))
                            if hasattr(enemy, 'last_collided_with'):
                                enemy.last_collided_with.add(id(self))
                                
                            break
            
            # Revert position if collision detected
            if collision_detected:
                # Revert both rects on collision
                self.rect.y = old_rect.y
                self.collision_rect = old_collision_rect.copy()
                
                if enemy_collision and not wall_collision and self.state == 'chase':
                    # For enemy-to-enemy collisions during chase, try to slide around
                    # Determine which direction to slide (perpendicular to movement)
                    if old_velocity_y != 0:
                        # Calculate perpendicular direction (left or right)
                        # Determine slide direction based on relative positions
                        if colliding_enemy and self.rect.centerx > colliding_enemy.rect.centerx:
                            # Try to slide right
                            slide_x = 2  # Increased from 1 to make the slide more aggressive
                        else:
                            # Try to slide left
                            slide_x = -2  # Increased from -1 to make the slide more aggressive
                            
                        # Try the slide movement
                        self.rect.x += slide_x
                        self.collision_rect.centerx = self.rect.centerx
                        
                        # If slide causes collision, revert it
                        if (has_level and player.level.check_collision(self.collision_rect) or
                            any(self.collision_rect.colliderect(e.collision_rect) for e in other_enemies if 
                               current_time >= self.ignore_collision_until and
                               (not hasattr(e, 'ignore_collision_until') or current_time >= e.ignore_collision_until) and
                               ((e.velocity_x == 0 and e.velocity_y == 0) or 
                               (hasattr(e, 'movement_priority') and e.movement_priority > self.movement_priority)))):
                            self.rect.x = old_rect.x
                            self.collision_rect.centerx = self.rect.centerx
                            
                            # Try sliding in the opposite direction
                            self.rect.x -= slide_x
                            self.collision_rect.centerx = self.rect.centerx
                            
                            # If that causes collision too, revert everything
                            if (has_level and player.level.check_collision(self.collision_rect) or
                                any(self.collision_rect.colliderect(e.collision_rect) for e in other_enemies if 
                                   current_time >= self.ignore_collision_until and
                                   (not hasattr(e, 'ignore_collision_until') or current_time >= e.ignore_collision_until) and
                                   ((e.velocity_x == 0 and e.velocity_y == 0) or 
                                   (hasattr(e, 'movement_priority') and e.movement_priority > self.movement_priority)))):
                                self.rect.x = old_rect.x
                                self.collision_rect.centerx = self.rect.centerx
                                self.velocity_y = 0
                                self.movement_failed_counter += 1
                    else:
                        self.velocity_y = 0
                        self.movement_failed_counter += 1
                else:
                    self.velocity_y = 0  # Stop vertical movement on collision
                    if self.state == 'chase':
                        self.movement_failed_counter += 1
                    
                    # Try to move a small step instead of the full velocity
                    if old_velocity_y != 0:  # Prevent division by zero
                        small_step = old_velocity_y / abs(old_velocity_y) * 1  # Just 1 pixel in direction
                        self.rect.y += small_step
                        self.collision_rect.centery = self.rect.centery
                        
                        # Check collision again
                        if (has_level and player.level.check_collision(self.collision_rect) or 
                            any(self.collision_rect.colliderect(enemy.collision_rect) for enemy in other_enemies if 
                               current_time >= self.ignore_collision_until and
                               (not hasattr(enemy, 'ignore_collision_until') or current_time >= enemy.ignore_collision_until) and
                               ((enemy.velocity_x == 0 and enemy.velocity_y == 0) or 
                               (hasattr(enemy, 'movement_priority') and enemy.movement_priority > self.movement_priority)))):
                            # Revert the small step too
                            self.rect.y = old_rect.y
                            self.collision_rect.centery = self.rect.centery
            else:
                self.movement_failed_counter = 0
                
        # In narrow passages, allow temporary overlapping with other enemies
        if self.state == 'chase' and self.movement_failed_counter >= 3:
            # Check if we're in a narrow passage by checking walls on both sides
            test_left = self.rect.copy()
            test_left.x -= TILE_SIZE
            test_right = self.rect.copy()
            test_right.x += TILE_SIZE
            test_up = self.rect.copy()
            test_up.y -= TILE_SIZE
            test_down = self.rect.copy()
            test_down.y += TILE_SIZE
            
            horizontal_narrow = False
            vertical_narrow = False
            
            if has_level:
                # Check horizontal narrow passage (walls on left and right)
                if player.level.check_collision(test_left) and player.level.check_collision(test_right):
                    horizontal_narrow = True
                    
                # Check vertical narrow passage (walls above and below)
                if player.level.check_collision(test_up) and player.level.check_collision(test_down):
                    vertical_narrow = True
            
            # If we're in a narrow passage and blocked by other enemies, allow pushing through
            if horizontal_narrow or vertical_narrow:
                # Make collision box even smaller in narrow passages (40% of tile size)
                old_width = self.collision_rect.width
                old_height = self.collision_rect.height
                
                # Save center position
                center_x = self.collision_rect.centerx
                center_y = self.collision_rect.centery
                
                # Reduce collision box size to 40% of tile size
                self.collision_rect.width = int(TILE_SIZE * 0.4)
                self.collision_rect.height = int(TILE_SIZE * 0.4)
                
                # Re-center the collision rect
                self.collision_rect.centerx = center_x
                self.collision_rect.centery = center_y
                
                # Calculate direction to player
                if distance > 0:
                    normalized_dx = dx / distance
                    normalized_dy = dy / distance
                    
                    # Move towards player, ignoring enemy collisions in narrow passages
                    self.rect.x += normalized_dx * self.speed * 0.5  # Half speed when pushing through
                    self.rect.y += normalized_dy * self.speed * 0.5
                    
                    # Update collision rect position
                    self.collision_rect.centerx = self.rect.centerx
                    self.collision_rect.centery = self.rect.centery
                    
                    # Still check for wall collisions
                    if has_level and player.level.check_collision(self.collision_rect):
                        # Revert if we hit a wall
                        self.rect = old_rect.copy()
                        # Also restore collision rect size and position
                        self.collision_rect.width = old_width
                        self.collision_rect.height = old_height
                        self.collision_rect.centerx = old_collision_rect.centerx
                        self.collision_rect.centery = old_collision_rect.centery
                        
                        self.movement_failed_counter += 1
                    else:
                        # Successfully pushed through
                        self.movement_failed_counter = 0
                        # Keep the smaller collision size for a while
                        self.ignore_collision_until = current_time + 500
        
        # Occasionally make a small random movement to break up potential clusters
        if self.state == 'chase' and self.movement_failed_counter > 0 and random.random() < 0.1:  # Increased from 5% to 10%
            # Try a random direction
            random_dir = random.choice(['up', 'down', 'left', 'right'])
            test_rect = self.rect.copy()
            
            if random_dir == 'up':
                test_rect.y -= 3
            elif random_dir == 'down':
                test_rect.y += 3
            elif random_dir == 'left':
                test_rect.x -= 3
            elif random_dir == 'right':
                test_rect.x += 3
                
            # If this random move doesn't cause collisions with walls, do it
            # But allow it even if it collides with other enemies when we're stuck
            test_collision_rect = self.collision_rect.copy()
            test_collision_rect.centerx = test_rect.centerx
            test_collision_rect.centery = test_rect.centery
            
            wall_collision = has_level and player.level.check_collision(test_collision_rect)
            
            if not wall_collision and self.movement_failed_counter >= 3:
                # When stuck for a while, allow moving even if it creates enemy collisions
                self.rect = test_rect
                self.collision_rect = test_collision_rect
            elif not wall_collision and not any(test_collision_rect.colliderect(enemy.collision_rect) for enemy in other_enemies):
                # Otherwise, only move if it doesn't cause any collisions
                self.rect = test_rect
                self.collision_rect = test_collision_rect
        
        # Clean up old collision records every few seconds
        if current_time - self.last_enemy_collision_time > 3000:  # 3 seconds
            self.last_collided_with.clear()
        
        # Keep enemy on screen
        self.rect.clamp_ip(pygame.display.get_surface().get_rect())
        # Make sure collision rect stays centered after clamping
        self.collision_rect.centerx = self.rect.centerx
        self.collision_rect.centery = self.rect.centery
        
        # Update animation
        self.animation_time += self.animation_speed
        
        # If the attack animation is done, go back to previous state
        if self.current_state == 'attack' and self.animation_time >= len(self.animations[self.current_state][self.facing]):
            self.current_state = 'idle' if self.state == 'idle' else 'walk'
            self.animation_time = 0
            
        # Calculate current frame
        self.frame = int(self.animation_time) % len(self.animations[self.current_state][self.facing])
        self.image = self.animations[self.current_state][self.facing][self.frame]
        
        # Update projectiles for level 6 enemies
        if self.can_shoot:
            # Update existing projectiles
            self.projectiles.update()
            
            # Check for collisions with player
            for projectile in self.projectiles:
                if projectile.check_collision(player.hitbox):
                    player.take_damage(projectile.damage)
                    projectile.kill()
            
            # Try to shoot new projectile
            if self.state != 'dead':
                self.shoot_projectile(player)
        
    def draw(self, surface):
        # Add a motion blur/trail effect when jumping
        if self.is_jumping:
            # Create a faded copy of the sprite
            alpha_sprite = self.image.copy()
            if not self.facing_right:
                alpha_sprite = pygame.transform.flip(alpha_sprite, True, False)
            alpha_sprite.set_alpha(100)  # 100/255 transparency
            
            # Calculate position based on distance from original to current
            blur_positions = []
            
            # Create 3 trail sprites between original and current position
            for i in range(1, 4):
                factor = i / 4.0
                trail_x = self.original_pos[0] * (1 - factor) + self.rect.x * factor
                trail_y = self.original_pos[1] * (1 - factor) + self.rect.y * factor
                blur_positions.append((int(trail_x), int(trail_y)))
            
            # Draw trail sprites
            for pos in blur_positions:
                surface.blit(alpha_sprite, pos)
        
        # Draw the enemy at its current position
        if not self.facing_right and not self.is_dead:  # Don't flip if in blood puddle state
            # Flip the sprite horizontally
            flipped_image = pygame.transform.flip(self.image, True, False)
            surface.blit(flipped_image, self.rect)
        else:
            # Draw normally
            surface.blit(self.image, self.rect)
        
        # Optionally draw collision box for debugging
        # Uncomment this to visualize the collision boxes
        # pygame.draw.rect(surface, (255, 0, 0), self.collision_rect, 1)
        
        # Draw resurrection effects if in blood puddle state
        if self.is_dead:
            current_time = pygame.time.get_ticks()
            
            # Calculate resurrection progress (0 to 1)
            time_left = self.resurrection_time - current_time
            progress = 1.0 - (time_left / 4000.0)  # 4000 = respawn time in ms
            
            # Add resurrection visual effects
            if progress > 0.5:  # Start effects at halfway point
                # Create a pulsing glow effect that grows as resurrection approaches
                pulse_size = TILE_SIZE * (0.3 + 0.7 * progress + 0.2 * math.sin(current_time / 100))
                
                # Create a surface with transparency for the glow
                glow_surface = pygame.Surface((pulse_size * 2, pulse_size * 2), pygame.SRCALPHA)
                
                # Color transitions from dark purple to bright purple based on progress
                alpha = int(40 + 100 * progress)
                glow_color = (100 + int(50 * progress), 0, 180 + int(75 * progress), alpha)
                pygame.draw.circle(glow_surface, glow_color, (pulse_size, pulse_size), pulse_size)
                
                # Blit the glow at the enemy position
                surface.blit(glow_surface, (self.rect.centerx - pulse_size, self.rect.centery - pulse_size))
                
                # Add particle effects as resurrection gets closer
                if random.random() < 0.1 * progress:
                    for _ in range(int(3 * progress)):
                        # Calculate random position around the blood puddle
                        angle = random.uniform(0, math.pi * 2)
                        dist = random.uniform(0, TILE_SIZE * 0.5)
                        spark_x = self.rect.centerx + dist * math.cos(angle)
                        spark_y = self.rect.centery + dist * math.sin(angle)
                        spark_size = random.randint(2, 4)
                        
                        # Draw the spark with a purple color
                        spark_color = (180 + int(75 * progress), 50, 255)
                        pygame.draw.circle(surface, spark_color, (int(spark_x), int(spark_y)), spark_size)
            
            # If just resurrected
            if current_time >= self.resurrection_time and current_time <= self.resurrection_time + 200:
                # Create visual effect for resurrection
                for _ in range(10):  # Increased particles for more dramatic effect
                    offset_x = random.randint(-TILE_SIZE//2, TILE_SIZE//2)
                    offset_y = random.randint(-TILE_SIZE//2, TILE_SIZE//2)
                    size = random.randint(5, 15)
                    pygame.draw.circle(surface, (150, 0, 255), 
                                      (self.rect.centerx + offset_x, self.rect.centery + offset_y), size)
                    
                # Add a larger pulse ring effect
                for radius in range(10, TILE_SIZE, 5):
                    alpha = max(10, 200 - radius * 2)
                    ring_surface = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
                    pygame.draw.circle(ring_surface, (150, 0, 255, alpha), (radius, radius), radius, 2)
                    surface.blit(ring_surface, 
                                 (self.rect.centerx - radius, self.rect.centery - radius))
        
        # Draw health bar only if not in blood puddle state
        health_bar_width = 40  # Reduced from 50
        health_bar_height = 3  # Reduced from 5
        health_ratio = self.health / self.enemy_data['health']
        pygame.draw.rect(surface, RED, (self.rect.x, self.rect.y - 8,  # Moved closer to enemy
                                      health_bar_width, health_bar_height))
        pygame.draw.rect(surface, GREEN, (self.rect.x, self.rect.y - 8,  # Moved closer to enemy
                                        health_bar_width * health_ratio, health_bar_height))
        
        # Draw projectiles for level 6 enemies
        if self.can_shoot and self.projectiles:
            for projectile in self.projectiles:
                projectile.draw(surface)
        
    def enter_blood_puddle_state(self):
        """Enter the blood puddle state for respawnable minions"""
        # Store the original texture (current frame of animation)
        self.original_texture = self.image
        
        # Load a random blood puddle texture
        try:
            blood_dir = os.path.join(TILE_SPRITES_PATH, "blood")
            if os.path.exists(blood_dir):
                blood_files = glob.glob(os.path.join(blood_dir, "*.png"))
                if blood_files:
                    selected_blood = random.choice(blood_files)
                    self.blood_puddle_texture = self.asset_manager.load_image(
                        selected_blood, scale=(TILE_SIZE, TILE_SIZE)
                    )
                    # Set current image to blood puddle
                    self.image = self.blood_puddle_texture
        except Exception as e:
            print(f"Failed to load blood puddle texture: {e}")
            # Fallback - create a simple red circle
            self.blood_puddle_texture = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
            pygame.draw.circle(self.blood_puddle_texture, (120, 0, 0), 
                               (TILE_SIZE//2, TILE_SIZE//2), TILE_SIZE//2)
            self.image = self.blood_puddle_texture
            
        # Mark as dead and set resurrection time (4 seconds from now)
        self.is_dead = True
        self.resurrection_time = pygame.time.get_ticks() + 4000
        # Reset resurrection sound flag
        self.resurrection_sound_played = False
        
    def resurrect(self):
        """Resurrect the minion after the blood puddle state"""
        # Play resurrection sound effect
        try:
            self.sound_manager.play_sound("effects/respawn")
            print("Playing resurrection sound")  # Debug line
        except Exception as e:
            print(f"Error playing resurrection sound: {e}")
            
        # Restore original texture
        if self.original_texture:
            self.image = self.original_texture
            
        # Restore animation state
        self.current_state = 'idle'
        self.facing = 'down'
        self.frame = 0
        self.animation_time = 0
        
        # Restore health to full
        self.health = self.max_health
        
        # No longer dead
        self.is_dead = False
        self.resurrection_time = 0
        self.resurrection_sound_played = False  # Reset sound flag to ensure it plays next time

    def shoot_projectile(self, player):
        """Shoot a projectile at the player (for level 6 enemies)"""
        if not self.can_shoot:
            return False
        
        current_time = pygame.time.get_ticks()
        if current_time - self.last_shot_time < self.projectile_cooldown:
            return False
        
        # Only shoot if player is visible and not too close
        if not self.has_spotted_player:
            return False
            
        # Calculate direction to player
        dx = player.rect.centerx - self.rect.centerx
        dy = player.rect.centery - self.rect.centery
        distance = math.sqrt(dx * dx + dy * dy)
        
        # Don't shoot if player is too close (within melee range)
        if distance <= self.attack_range * 2:
            return False
        
        # Normalize direction
        if distance > 0:
            dx = dx / distance
            dy = dy / distance
        else:
            dx, dy = 0, -1
            
        # Create the projectile
        projectile = BossProjectile(
            self.rect.centerx, 
            self.rect.centery, 
            (dx, dy), 
            self.projectile_speed, 
            self.projectile_damage, 
            self.projectile_color,
            is_homing=True,  # Make the projectile homing
            boss_level=self.level if hasattr(self, 'level') else None  # Pass the boss level if available
        )
        
        # Set the player as the target for homing
        projectile.player_target = player
        
        # Add to projectile group
        self.projectiles.add(projectile)
        
        # Update last shot time
        self.last_shot_time = current_time
        
        # Play sound if available
        if hasattr(self, 'sound_manager'):
            self.sound_manager.play_sound("effects/projectile")
            
        return True

class Boss(Enemy):
    def __init__(self, x, y, level, level_instance=None):
        """Initialize a boss enemy with strong attributes"""
        super().__init__(x, y, None, level, level_instance)
        
        # Make sure the collision rect is properly sized for bosses
        # Bosses need a smaller collision box (50% of sprite size) to navigate better
        self.collision_box_scale = 0.5
        self.collision_rect = pygame.Rect(0, 0, 
                                         int(self.rect.width * self.collision_box_scale),
                                         int(self.rect.height * self.collision_box_scale))
        # Center the collision rect within the image rect
        self.collision_rect.centerx = self.rect.centerx
        self.collision_rect.centery = self.rect.centery
        
        # Flag this as a boss for special collision handling
        self.is_boss = True
        
        # Ensure level_instance is set, critical for Boss 9's egg spawning
        if not self.level_instance and level_instance:
            self.level_instance = level_instance
            print(f"Set level_instance for Boss {level}")
        
        # Ensure is_jumping is False for bosses
        self.is_jumping = False
        
        self.asset_manager = get_asset_manager()
        self.sound_manager = get_sound_manager()
        
        self.enemy_data = BOSS_TYPES[f'level{level}']
        self.level = level  # Explicitly save the level
        
        # Animation states and directions with more frames for bosses
        self.animations = {
            'idle': {},
            'walk': {},
            'attack': {},
            'special': {}  # Special attack animation for bosses
        }
        
        # Boss 9 animation frames
        self.boss9_animation_frames = []
        self.boss9_animation_index = 0
        self.boss9_animation_direction = 1  # 1 for forward, -1 for backward
        self.boss9_animation_timer = 0
        self.boss9_animation_interval = 1750  # Animation plays every 1.75 seconds
        self.boss9_frame_time = 100  # Time between animation frames in ms
        self.boss9_last_frame_time = 0
        self.boss9_is_animating = False
        
        # Boss 9 stealth mode attributes
        self.stealth_mode = False
        self.stealth_cycle_active = False
        self.normal_phase_duration = 10000  # 10 seconds in normal state
        self.stealth_phase_duration = 4000  # 4 seconds in stealth state
        self.stealth_start_time = 0
        self.last_phase_change_time = 0
        self.normal_speed = 0
        self.stealth_speed = 0
        self.stealth_alpha = 128  # 50% transparency (0-255)
        self.stealth_target_x = 0  # Random movement target during stealth
        self.stealth_target_y = 0
        self.stealth_change_direction_timer = 0
        self.stealth_direction_change_interval = 800  # Change direction every 800ms in stealth mode
        
        # Store the original rect which represents the full sprite size
        self.original_rect = self.rect.copy()
        
        # Calculate expected sprite dimensions (typically 2x tile size for bosses)
        expected_width = TILE_SIZE * 2
        expected_height = TILE_SIZE * 2
        
        # Use a smaller hitbox for movement and collision detection
        # Make it ~65% of the visual size (down from 75%)
        small_size = int(TILE_SIZE * 0.65)  # Even smaller for fairness
        
        # Center the hitbox in the sprite
        hitbox_x = self.rect.centerx - small_size // 2
        hitbox_y = self.rect.centery - small_size // 2
        self.rect = pygame.Rect(hitbox_x, hitbox_y, small_size, small_size)
        
        # Visual offset tracks the difference between the rect position and where
        # the sprite is actually drawn
        self.visual_offset_x = (expected_width - small_size) // 2
        self.visual_offset_y = (expected_height - small_size) // 2
        
        # Create a damage hitbox that covers most of the visual sprite
        # Using a size that's 90% of the expected boss sprite dimensions
        damage_width = int(expected_width * 0.9)  # 90% of visual width
        damage_height = int(expected_height * 0.9)  # 90% of visual height
        
        # Create damage hitbox centered properly on the visual sprite
        self.damage_hitbox = pygame.Rect(
            self.rect.centerx - damage_width // 2,
            self.rect.centery - damage_height // 2,
            damage_width,
            damage_height
        )
        
        # Initialize health to the boss-specific value
        self.health = self.enemy_data['health']
        self.max_health = self.health
        
        # Set boss damage directly from configuration
        self.damage = self.enemy_data['damage']
        
        # Use adjusted speeds for bosses
        self.speed = self.enemy_data['speed']
        
        # Adjust attack range to be smaller than player's sword range
        # This allows player to hit boss without getting hit themselves
        self.attack_range = TILE_SIZE * 0.7  # Reduced from 1.0 to 0.7 tiles
        
        # Reduce the detection range for level 1 boss
        # Level 1 boss is faster, so it needs a smaller detection range
        # to give player more time to react
        self.detection_range = TILE_SIZE * (4 if level == 1 else 6)
        
        # Increase attack cooldown to give player more time between attacks
        self.attack_cooldown = 1200  # 1.2 seconds between attacks
        
        # Level 4 boss defensive mode attributes
        self.defensive_mode = False
        self.defensive_mode_cooldown = 8000  # 8 seconds between defensive mode activations
        self.defensive_mode_duration = 3000  # 3 seconds in defensive mode
        self.last_defensive_mode_time = 0
        self.defensive_mode_engaged = False
        self.in_combat = False  # Track if boss has engaged in combat
        self.combat_start_time = 0  # When combat started
        self.last_defensive_sound_time = 0  # Track when defensive sound was last played
        self.reflected_damage = 0  # Track damage to reflect during defensive mode
        
        # Level 4 boss rope mechanic attributes
        self.is_shooting_rope = False
        self.rope_start_time = 0
        self.rope_duration = 1500  # 1.5 seconds to shoot rope
        self.rope_target = None
        self.rope_length = 0
        self.rope_max_length = TILE_SIZE * 20  # Maximum rope length (increased from 8 to 20 tiles)
        self.rope_speed = 10  # Pixels per frame
        self.rope_reached_player = False
        self.rope_pull_speed = 6  # How fast to pull player
        self.is_pulling_player = False
        self.pull_duration = 1000  # 1 second to pull player
        self.pull_start_time = 0
        self.rope_end_pos = None  # Position of the end of the rope
        
        # Level 3 boss defensive mode - active when minions are alive
        if level == 3:
            self.defensive_mode = True  # Start in defensive mode until all minions are dead
            self.defensive_image_level3 = None # No special image for level 3 defensive mode
            print("Level 3 boss initialized with defensive mode active while minions alive")
        
        # Level 7 boss shield mode attributes (based on level 4)
        if level == 7:
            self.defensive_mode = False
            self.defensive_mode_cooldown = 10000  # 10 seconds between shield activations
            self.defensive_mode_duration = 4000   # 4 seconds in shield mode
            self.last_defensive_mode_time = 0
            self.defensive_mode_engaged = False
            self.shield_growth = 0  # Track shield growth from 0 to 1 (0% to 100% additional size)
            self.shield_radius = 0  # Current shield radius for collision detection
            self.shield_damage = self.damage * 0.5  # Shield deals 50% of boss damage per tick
            self.shield_damage_cooldown = 500  # Damage player every 0.5 seconds
            self.last_shield_damage_time = 0
            self.cursed_shield_dropped = False  # Track if a cursed shield has been dropped this cycle
            
            # Death ray attributes for level 7 boss
            self.death_ray = None
            self.has_death_ray = False
            
            # Initialize projectile capabilities for level 7 boss
            self.projectiles = pygame.sprite.Group()
            print("Initialized level 7 boss with projectile capabilities")
        
        # Load defensive state image for level 4 boss
        self.defensive_image = None
        if level == 4:
            try:
                defensive_img_path = os.path.join(BOSS_SPRITES_PATH, "boss_4_def.png")
                if os.path.exists(defensive_img_path):
                    print(f"Loading defensive image from: {defensive_img_path}")
                    self.defensive_image = self.asset_manager.load_image(
                        defensive_img_path, scale=(TILE_SIZE*2.2, TILE_SIZE*2.2))
                    print(f"Loaded defensive image for level 4 boss: {id(self.defensive_image)}")
                else:
                    print(f"Defensive image not found at: {defensive_img_path}")
            except Exception as e:
                print(f"Failed to load defensive image for level 4 boss: {e}")
        
        # Also use defensive image for level 7 boss (or load specific image if available)
        if level == 7:
            try:
                defensive_img_path = os.path.join(BOSS_SPRITES_PATH, "boss_7_def.png")
                if os.path.exists(defensive_img_path):
                    print(f"Loading defensive image from: {defensive_img_path}")
                    self.defensive_image = self.asset_manager.load_image(
                        defensive_img_path, scale=(TILE_SIZE*2.2, TILE_SIZE*2.2))
                    print(f"Loaded defensive image for level 7 boss: {id(self.defensive_image)}")
                else:
                    # Try using level 4 defensive image as fallback
                    defensive_img_path = os.path.join(BOSS_SPRITES_PATH, "boss_4_def.png")
                    if os.path.exists(defensive_img_path):
                        print(f"Using level 4 defensive image for level 7 boss")
                        self.defensive_image = self.asset_manager.load_image(
                            defensive_img_path, scale=(TILE_SIZE*2.2, TILE_SIZE*2.2))
                    else:
                        print(f"Defensive image not found for level 7 boss")
            except Exception as e:
                print(f"Failed to load defensive image for level 7 boss: {e}")
        
        # Load teleportation casting image for level 6 boss
        self.teleport_cast_image = None
        if level == 6:
            try:
                cast_img_path = os.path.join(BOSS_SPRITES_PATH, "boss_6_cast.png")
                if os.path.exists(cast_img_path):
                    print(f"Loading teleport cast image from: {cast_img_path}")
                    self.teleport_cast_image = self.asset_manager.load_image(
                        cast_img_path, scale=(TILE_SIZE*2.2, TILE_SIZE*2.2))
                    print(f"Loaded teleport cast image for level 6 boss: {id(self.teleport_cast_image)}")
                else:
                    print(f"Teleport cast image not found at: {cast_img_path}")
            except Exception as e:
                print(f"Failed to load teleport cast image for level 6 boss: {e}")
        
        # Level 2 boss uses projectiles
        self.projectiles = pygame.sprite.Group()
        self.projectile_cooldown = 0
        self.projectile_cooldown_time = 90  # frames between projectile attacks
        
        # Tracking if Boss 5 has already created its orbiting projectiles
        self.orbiting_projectiles_created = False
        
        # Boss 5 casting mode attributes
        if level == 5 or level == 8:
            self.casting_mode = False
            self.casting_mode_cooldown = 6000  # 6 seconds between casts
            self.casting_mode_duration = 2000  # 2 seconds in casting mode
            self.last_cast_time = 0
            self.cast_complete = False
            self.stationary_projectile_duration = 6000  # How long projectiles stay in place
            
            # Special settings for Boss 8
            if level == 8:
                self.casting_mode_cooldown = 12000  # 12 seconds between casts
                self.casting_mode_duration = 3000   # 3 seconds in casting mode
                self.stationary_projectile_duration = 10000  # 10 seconds lifetime for projectiles
                self.floor_projectiles = []  # Store floor projectiles for activation after casting
        
        # Boss 6 teleportation attributes
        if level == 6:
            self.teleport_cooldown = 6000  # 6 seconds between teleports
            self.teleport_duration = 1500  # 1.5 seconds to disappear and reappear
            self.last_teleport_time = pygame.time.get_ticks()  # Initialize with current time
            self.is_teleporting = False
            self.teleport_start_time = 0
            self.teleport_target_pos = None
            self.teleport_alpha = 255  # For fade effect
            
            # Add casting state attributes
            self.casting_mode = False
            self.casting_mode_duration = 1000  # 1 second casting time
            self.cast_start_time = 0
            
            # Poison trail attributes
            self.poison_trails = pygame.sprite.Group()
            self.last_trail_time = 0
            self.trail_interval = 300  # Create trail every 300ms
            self.trail_size = int(TILE_SIZE * 1.0)  # Increased size of trail segments
            self.trail_damage = self.damage * 0.05  # Trail does 5% of boss damage
        
        # Poison trail attribute for level 9 boss (for the slowing puddle when exiting stealth)
        if self.level == 9:
            self.poison_trails = pygame.sprite.Group()
        
        # Phase system for special attacks
        self.phase = 0  # 0 = normal, 1 = <60% health, 2 = <30% health
        self.last_special_attack_time = 0
        self.special_attack_cooldown = 3000  # 3 seconds between special attacks
        
        # Get boss name
        boss_name = self.enemy_data['name'].lower().replace(' ', '_')
        
        # Create default colored image with boss name as placeholder
        placeholder = pygame.Surface((TILE_SIZE*1.5, TILE_SIZE*1.5))
        placeholder.fill((150, 0, 0))  # Darker red for bosses
        font = pygame.font.Font(None, 16)
        text = font.render(f"BOSS: {boss_name[:8]}", True, WHITE)
        text_rect = text.get_rect(center=(TILE_SIZE*1.5//2, TILE_SIZE*1.5//2))
        placeholder.blit(text, text_rect)
        
        # Initialize with placeholder for all animations and directions
        for anim_type in ['idle', 'walk', 'attack', 'special']:
            self.animations[anim_type] = {
                'down': [placeholder], 
                'up': [placeholder], 
                'left': [placeholder], 
                'right': [placeholder]
            }
        
        # Load boss image based on level - do this only once
        boss_img = None
        boss_img_path = os.path.join(BOSS_SPRITES_PATH, f"boss_{level}.png")
        
        # Determine the scale based on the boss level
        scale_factor = 2.0  # Default scale factor
        if level >= 4 and level <= 6 or level == 8:
            scale_factor = 2.2
        elif level == 7:
            scale_factor = 2.3
        elif level == 9:
            scale_factor = 2.4
        elif level == 10:
            scale_factor = 2.5
        
        # Try to load the boss image
        try:
            if os.path.exists(boss_img_path):
                # For level 9, use our custom texture loader to support animation
                if level == 9:
                    boss_img = self.load_texture(boss_img_path)
                    print(f"Using boss_{level}.png with animation for level {level} boss")
                else:
                    # Load and scale the image
                    boss_img = self.asset_manager.load_image(
                        boss_img_path, 
                        scale=(TILE_SIZE*scale_factor, TILE_SIZE*scale_factor)
                    )
                    print(f"Using boss_{level}.png for level {level} boss animations")
                
                # Use this image for all animation states and directions
                for direction in ['down', 'up', 'left', 'right']:
                    self.animations['idle'][direction] = [boss_img]
                    self.animations['walk'][direction] = [boss_img]
                    self.animations['attack'][direction] = [boss_img]
                    self.animations['special'][direction] = [boss_img]
        except Exception as e:
            print(f"Failed to load boss_{level}.png for level {level} boss: {e}")
            # Continue with the placeholder
        
        # If boss image wasn't loaded, try to load traditional animation files
        if boss_img is None:
            base_path = os.path.join(BOSS_SPRITES_PATH, boss_name)
            
            # Try to load actual animations for each direction
            for direction in ['down', 'up', 'left', 'right']:
                try:
                    if os.path.exists(base_path):
                        idle_path = os.path.join(base_path, f"idle_{direction}")
                        if os.path.exists(idle_path):
                            self.animations['idle'][direction] = self.asset_manager.load_animation(
                                idle_path, "idle_", 4, scale=(TILE_SIZE*1.5, TILE_SIZE*1.5))
                except Exception as e:
                    print(f"Could not load idle animation for boss {boss_name} {direction}: {e}")
                    
                try:
                    if os.path.exists(base_path):
                        walk_path = os.path.join(base_path, f"walk_{direction}")
                        if os.path.exists(walk_path):
                            self.animations['walk'][direction] = self.asset_manager.load_animation(
                                walk_path, "walk_", 4, scale=(TILE_SIZE*1.5, TILE_SIZE*1.5))
                except Exception as e:
                    print(f"Could not load walk animation for boss {boss_name} {direction}: {e}")
                    
                try:
                    if os.path.exists(base_path):
                        attack_path = os.path.join(base_path, f"attack_{direction}")
                        if os.path.exists(attack_path):
                            self.animations['attack'][direction] = self.asset_manager.load_animation(
                                attack_path, "attack_", 4, scale=(TILE_SIZE*1.5, TILE_SIZE*1.5))
                except Exception as e:
                    print(f"Could not load attack animation for boss {boss_name} {direction}: {e}")
                    
                try:
                    if os.path.exists(base_path):
                        special_path = os.path.join(base_path, f"special_{direction}")
                        if os.path.exists(special_path):
                            self.animations['special'][direction] = self.asset_manager.load_animation(
                                special_path, "special_", 6, scale=(TILE_SIZE*1.5, TILE_SIZE*1.5))
                except Exception as e:
                    print(f"Could not load special animation for boss {boss_name} {direction}: {e}")
        
        # Create smaller collision rectangle - MUCH smaller to fit through tight passages
        self.original_rect = self.rect.copy()
        # Create a smaller collision box centered on the boss's position
        # This allows the boss to move through narrower passages
        small_size = int(TILE_SIZE * 0.75)  # Even smaller than before - 75% of a tile
        
        # Calculate the center position
        center_x = self.rect.x + self.rect.width // 2
        center_y = self.rect.y + self.rect.height // 2
        
        # Create a new centered rect with the smaller size
        self.rect = pygame.Rect(0, 0, small_size, small_size)
        self.rect.center = (center_x, center_y)
        
        # Calculate visual offset for drawing
        self.visual_offset_x = (self.animations['idle']['down'][0].get_width() - self.rect.width) // 2
        self.visual_offset_y = (self.animations['idle']['down'][0].get_height() - self.rect.height) // 2
        
        # Set initial state and animation
        self.current_state = 'idle'
        self.facing = 'down'
        self.image = self.animations[self.current_state][self.facing][0]
        self.frame = 0
        self.animation_time = 0
        self.animation_speed = 0.2
        
        # Boss-specific attributes
        self.phase = 1
        # Set max_phases based on level
        if level == 2:
            self.max_phases = 1  # Skeleton Lord only has 1 phase
        elif level == 5:
            self.max_phases = 1  # Level 5 boss also has 1 phase like Skeleton Lord
        else:
            self.max_phases = 3  # Default value for other bosses
            
        self.special_attack_cooldown = 3000  # 3 seconds
        self.last_special_attack_time = 0
        
        # For level 2 and 5 bosses, adjust attack properties
        if level == 2 or level == 5:
            self.attack_range = TILE_SIZE * 1  # Reduced attack range to 1 tile
            self.attack_cooldown = 1500  # 1.5 seconds between attacks
        
        # Position history for trailing effect (used by level 1 boss)
        self.trail_enabled = level in [1, 2]  # Only for level 1 and 2 bosses
        self.position_history = []
        self.max_trail_length = 10  # Number of previous positions to remember
        self.trail_update_rate = 3   # Update every N frames
        self.trail_frame_counter = 0
        
        # Trail color based on level
        self.trail_color = (150, 0, 0) if level == 1 else (0, 150, 150)  # Red for level 1, Cyan for level 2
        
        # Boss 1 blood zone attributes
        if level == 1:
            self.blood_zones = pygame.sprite.Group()
            self.zone_creation_interval = 6000  # Create a zone every 6 seconds
            self.last_zone_creation_time = 0
            self.zone_creation_delay = 2000  # First zone appears after 6 seconds of engagement
            self.combat_start_time = 0
            self.in_combat_with_player = False
            self.zone_damage = self.damage * 0.15  # Each zone does 15% of the boss's damage
            self.zone_size = TILE_SIZE * 4  # 2x2 tiles size (4 tiles total)
        
        # Sound manager for boss voice
        self.sound_manager = get_sound_manager()
        
        # Boss voice related attributes
        self.has_seen_player = False
        self.last_voice_time = 0
        self.voice_cooldown = 4000  # 4 seconds (in milliseconds)
        
        # Resurrection functionality for level 3 boss
        if level == 3:
            self.resurrection_enabled = True
            self.resurrection_cooldown = 4000  # 4 seconds between resurrections
            self.last_resurrection_time = 0
            self.resurrection_in_progress = False
            self.resurrection_target = None
            self.resurrection_animation_time = 0
            print("Level 3 boss initialized with resurrection abilities")
        else:
            self.resurrection_enabled = False
        
        # Boss-specific properties
        self.visual_offset_x = 0  # Visual offset for drawing (not affecting hitbox)
        self.visual_offset_y = 0
        
        # Damage tracking - ensure it's set for bosses too
        self.has_been_hit_this_swing = False
        
        # Boss 9 egg-laying attributes
        if level == 9:
            self.eggs = pygame.sprite.Group()  # Store the eggs
            self.last_egg_time = 0  # Last time an egg was laid
            self.egg_cooldown = 1000  # Minimum time between eggs (1 second)
            self.egg_image = None
            
            # Try to load the egg image
            try:
                egg_path = os.path.join(BOSS_SPRITES_PATH, "boss_9_egg.png")
                if os.path.exists(egg_path):
                    print(f"Loading boss 9 egg image from: {egg_path}")
                    self.egg_image = self.asset_manager.load_image(egg_path, scale=(TILE_SIZE * 0.8, TILE_SIZE * 0.8))
                else:
                    print(f"Boss 9 egg image not found at: {egg_path}")
            except Exception as e:
                print(f"Failed to load egg image for boss 9: {e}")
        
        # Add missing initialization for Boss 9 at the end of the __init__ method
        if self.level == 9:
            # ... existing Boss 9 init code ...
            
            # Variables for consistent egg laying (3 eggs per stealth phase)
            self.eggs_laid_this_phase = 0
            self.egg_laying_times = []
            
        # ... existing code ...
    
    def move_towards_player(self, player):
        """Move towards player using pathfinding"""
        # Special cases for specific bosses
        if self.level == 9 and self.stealth_mode:
            self._move_in_stealth_mode()
            return
            
        if self.level == 6 and self.is_teleporting:
            self.velocity_x = 0
            self.velocity_y = 0
            return
        
        # Use the base Enemy class's movement logic
        super().move_towards_player(player)
        
    def special_attack(self, player):
        current_time = pygame.time.get_ticks()
        if current_time - self.last_special_attack_time >= self.special_attack_cooldown:
            self.last_special_attack_time = current_time
            # Switch to special attack animation
            self.current_state = 'special'
            self.frame = 0  # Reset animation frame
            
            # Level 2 boss has cone projectile attack
            if self.level == 2:
                # Calculate normalized direction vector to player
                dx = player.rect.centerx - self.rect.centerx
                dy = player.rect.centery - self.rect.centery
                length = math.sqrt(dx*dx + dy*dy)
                
                if length > 0:
                    # Normalize
                    dx = dx / length
                    dy = dy / length
                else:
                    # Default direction if player is exactly at the same position
                    dx, dy = 0, -1  # Up
                
                # Create center projectile (directly at player)
                center_dx, center_dy = dx, dy
                
                # Create perpendicular vector for creating the left/right projectiles
                # Perpendicular to (dx, dy) is (-dy, dx) or (dy, -dx)
                perp_dx, perp_dy = -dy, dx
                
                # Calculate rotated vectors for left and right projectiles
                # Left = center rotated slightly towards perpendicular
                # Right = center rotated slightly away from perpendicular
                rotation_factor = 0.5  # Increased from 0.3 to make the spread more obvious
                
                # Left projectile - rotate towards perpendicular
                left_dx = center_dx + perp_dx * rotation_factor
                left_dy = center_dy + perp_dy * rotation_factor
                # Normalize
                left_length = math.sqrt(left_dx*left_dx + left_dy*left_dy)
                left_dx = left_dx / left_length
                left_dy = left_dy / left_length
                
                # Right projectile - rotate away from perpendicular
                right_dx = center_dx - perp_dx * rotation_factor
                right_dy = center_dy - perp_dy * rotation_factor
                # Normalize
                right_length = math.sqrt(right_dx*right_dx + right_dy*right_dy)
                right_dx = right_dx / right_length
                right_dy = right_dy / right_length
                
                # Create the projectiles with different colors
                # Center projectile - offset slightly ahead of the others and use brighter color
                center_projectile = BossProjectile(
                    self.rect.centerx + center_dx * 10,  # Offset slightly ahead 
                    self.rect.centery + center_dy * 10, 
                    (center_dx, center_dy), 
                    1.8, 
                    self.damage * 1.5, 
                    color=(20, 150, 255),  # Brighter blue
                    boss_level=self.level,  # Pass the boss level
                    spawn_secondary=True,  # Enable secondary projectiles
                    spawn_time=2000,  # Spawn after 2 seconds
                    orbit_boss=self  # Pass reference to boss for spawning
                )
                
                left_projectile = BossProjectile(
                    self.rect.centerx, 
                    self.rect.centery, 
                    (left_dx, left_dy), 
                    1.8, 
                    self.damage * 1.5, 
                    color=(255, 0, 255),  # Magenta
                    boss_level=self.level,  # Pass the boss level
                    spawn_secondary=True,  # Enable secondary projectiles
                    spawn_time=2000,  # Spawn after 2 seconds
                    orbit_boss=self  # Pass reference to boss for spawning
                )
                
                right_projectile = BossProjectile(
                    self.rect.centerx, 
                    self.rect.centery, 
                    (right_dx, right_dy), 
                    1.8, 
                    self.damage * 1.5, 
                    color=(255, 165, 0),  # Orange
                    boss_level=self.level,  # Pass the boss level
                    spawn_secondary=True,  # Enable secondary projectiles
                    spawn_time=2000,  # Spawn after 2 seconds
                    orbit_boss=self  # Pass reference to boss for spawning
                )
                
                # Add to projectile group
                self.projectiles.add(center_projectile, left_projectile, right_projectile)
                
                return False
                
            # Level 5 boss - create orbiting projectiles when first spotted
            elif self.level == 5 or self.level == 8:
                print(f"Creating orbiting projectiles for Boss {self.level}")
                
                # Set the flag so we only create these once
                self.orbiting_projectiles_created = True
                
                # Orbit radius - 3 tiles from the boss
                orbit_radius = TILE_SIZE * 3
                
                # Create 3 projectiles with different colors at evenly spaced angles
                num_projectiles = 3
                
                for i in range(num_projectiles):
                    # Distribute projectiles evenly in a circle
                    angle = (i * 2 * math.pi / num_projectiles)
                    
                    # Calculate initial position 3 tiles away from boss
                    spawn_x = self.rect.centerx + math.cos(angle) * orbit_radius
                    spawn_y = self.rect.centery + math.sin(angle) * orbit_radius
                    
                    # For boss 8, use the fire ball animation
                    if self.level == 8:
                        color = (255, 100, 0)  # Orange-red color for fire
                    else:
                        color = (255, 0, 0)  # Red color for boss 5
                    
                    # Create orbiting projectile - reduced damage by 97% to balance the continuous hits
                    projectile = BossProjectile(
                        spawn_x, spawn_y,
                        (0, 0),  # Direction doesn't matter for orbiting projectiles
                        0,       # Speed is not used for orbiting
                        self.damage * 0.03,  # Reduced damage to just 3% of base damage
                        color=color,
                        is_orbiting=True,
                        orbit_boss=self,
                        orbit_angle=angle,
                        orbit_radius=orbit_radius,
                        orbit_speed=0.015,  # Angular velocity - reduced by 50%
                        boss_level=self.level  # Pass the boss level for animated projectiles
                    )
                    
                    # Add to projectile group
                    self.projectiles.add(projectile)
                
                return True
            # Level 6 boss - melee-only special attack
            elif self.level == 6:
                # Check if player is within attack range before applying damage
                dx = player.rect.centerx - self.rect.centerx
                dy = player.rect.centery - self.rect.centery
                distance = math.sqrt(dx * dx + dy * dy)
                
                # Only apply damage if player is within the attack range
                if distance <= self.attack_range * 1.5:  # Slightly increased range for special attack
                    damage_multiplier = 1 + (self.phase * 0.5)  # Damage increases with phase
                    
                    # Create visual effect to show the special attack - blue particles for Boss 6
                    if hasattr(player, 'game') and player.game and hasattr(player.game, 'particle_system'):
                        for _ in range(10):  # Create 10 particles
                            offset_x = random.randint(-10, 10)
                            offset_y = random.randint(-10, 10)
                            player.game.particle_system.create_particle(
                                player.rect.centerx + offset_x,
                                player.rect.centery + offset_y,
                                color=(50, 100, 255),  # Blue tint for Boss 6
                                size=random.randint(3, 8),
                                speed=random.uniform(0.8, 2.0),
                                lifetime=random.randint(20, 35)
                            )
                    
                    return player.take_damage(self.damage * damage_multiplier)
                else:
                    # Player is out of range, special attack misses
                    return False
            else:
                # Other bosses use the original special attack
                # Check if player is within attack range before applying damage
                dx = player.rect.centerx - self.rect.centerx
                dy = player.rect.centery - self.rect.centery
                distance = math.sqrt(dx * dx + dy * dy)
                
                # Only apply damage if player is within the attack range
                if distance <= self.attack_range:
                    damage_multiplier = 1 + (self.phase * 0.5)  # Damage increases with phase
                    
                    # Create visual effect to show the special attack
                    if hasattr(player, 'game') and player.game and hasattr(player.game, 'particle_system'):
                        for _ in range(8):  # Create 8 particles
                            offset_x = random.randint(-10, 10)
                            offset_y = random.randint(-10, 10)
                            player.game.particle_system.create_particle(
                                player.rect.centerx + offset_x,
                                player.rect.centery + offset_y,
                                color=(255, 0, 0),
                                size=random.randint(3, 6),
                                speed=random.uniform(0.5, 1.5),
                                lifetime=random.randint(20, 30)
                            )
                    
                    return player.take_damage(self.damage * damage_multiplier)
                else:
                    # Player is out of range, special attack misses
                    return False
        return False
        
    def update(self, player):
        # Get current time at the beginning of the method
        current_time = pygame.time.get_ticks()
        
        # Check if in blood puddle state and ready to resurrect
        if self.is_dead:
            # Check if resurrection time has arrived
            if current_time >= self.resurrection_time:
                self.resurrect()
            
            # Render blood particles only during the first half of the resurrection timer
            if current_time <= self.resurrection_time - 2000 and random.random() < 0.05:
                offset_x = random.randint(-self.rect.width//2, self.rect.width//2)
                offset_y = random.randint(-self.rect.height//2, self.rect.height//2)
                self.particle_manager.add_particle(
                    particle_type='blood_drop',
                    pos=(self.rect.centerx + offset_x, self.rect.centery + offset_y),
                    velocity=(0, 0.5),
                    direction=random.uniform(0, 360),
                    color=(139, 0, 0),
                    size=random.randint(2, 4),
                    lifetime=random.randint(30, 60)
                )
            
            # Return early since boss is in blood puddle state
            return
        
        # Level 3 boss defensive mode - check if any enemies are alive in the room
        if self.level == 3:
            # Find the room that contains this boss
            room = None
            
            # Try different approaches to find the boss's room
            if hasattr(self, 'level_instance') and self.level_instance:
                # First try with current_room
                if hasattr(self.level_instance, 'current_room'):
                    # Check if the boss is in the current room
                    if self.level_instance.current_room.boss == self:
                        room = self.level_instance.current_room
                
                # If not found, search all rooms
                if room is None and hasattr(self.level_instance, 'rooms'):
                    for coords, r in self.level_instance.rooms.items():
                        if hasattr(r, 'boss') and r.boss == self:
                            room = r
                            break
            
            # Try through player's game if available
            if room is None and hasattr(player, 'game') and hasattr(player.game, 'level'):
                level = player.game.level
                
                # Check current room first
                if hasattr(level, 'current_room') and level.current_room.boss == self:
                    room = level.current_room
                
                # If not found, search all rooms
                if room is None and hasattr(level, 'rooms'):
                    for coords, r in level.rooms.items():
                        if hasattr(r, 'boss') and r.boss == self:
                            room = r
                            break
            
            # Check if we found a room and update defensive mode
            if room and hasattr(room, 'enemies'):
                # Boss is in defensive mode if any enemies are ALIVE (not in blood puddle state)
                # Count only enemies that are not in blood puddle state (not resurrecting)
                alive_enemies = [enemy for enemy in room.enemies if not hasattr(enemy, 'is_dead') or not enemy.is_dead]
                enemies_alive = len(alive_enemies) > 0
                was_defensive = self.defensive_mode
                self.defensive_mode = enemies_alive
                
                # Log state change
                if was_defensive and not self.defensive_mode:
                    print("Level 3 boss dropped defensive mode - all minions defeated!")
                elif not was_defensive and self.defensive_mode:
                    print("Level 3 boss entered defensive mode - minions protecting the boss!")
                    # Play voice when boss enters defensive mode (shield activates)
                    if self.level == 3:
                        voice_file = f"effects/boss_{self.level}_voice"
                        self.sound_manager.play_sound(voice_file)
                        self.last_voice_time = current_time
            else:
                # Failed to find room or enemies - default to no defensive mode
                if self.defensive_mode:
                    self.defensive_mode = False
                    print("Level 3 boss dropped defensive mode - could not find valid room!")
        
        # Update Boss 9 animation
        if self.level == 9:
            # Check if it's time to start a new animation cycle
            if not self.boss9_is_animating and current_time - self.boss9_animation_timer >= self.boss9_animation_interval:
                self.boss9_is_animating = True
                self.boss9_animation_index = 0
                self.boss9_animation_direction = 1
                self.boss9_last_frame_time = current_time
                self.boss9_animation_timer = current_time
            
            # Update animation frame if currently animating
            if self.boss9_is_animating:
                if current_time - self.boss9_last_frame_time >= self.boss9_frame_time:
                    # Update animation index according to direction
                    self.boss9_animation_index += self.boss9_animation_direction
                    
                    # Change direction if at the edges
                    if self.boss9_animation_index >= len(self.boss9_animation_frames) - 1:
                        self.boss9_animation_direction = -1
                    elif self.boss9_animation_index <= 0:
                        # Animation complete, reset to base state
                        if self.boss9_animation_direction == -1:
                            self.boss9_is_animating = False
                            self.boss9_animation_timer = current_time
                    
                    self.boss9_last_frame_time = current_time
                    
            # Handle boss 9 stealth cycle
            if self.level == 9:
                # Calculate distance to player to check engagement
                dx = player.rect.centerx - self.rect.centerx
                dy = player.rect.centery - self.rect.centery
                distance = math.sqrt(dx * dx + dy * dy)
                
                # Activate cycle when player is within detection range
                if not self.stealth_cycle_active and distance <= self.detection_range:
                    self.stealth_cycle_active = True
                    self.last_phase_change_time = current_time
                    self.normal_speed = self.speed  # Store normal speed
                    self.stealth_speed = self.speed * 2.0  # 200% of normal speed (increased from 150%)
                    
                # If cycle is active, manage phase transitions
                if self.stealth_cycle_active:
                    if not self.stealth_mode and current_time - self.last_phase_change_time >= self.normal_phase_duration:
                        # Switch to stealth mode
                        self.stealth_mode = True
                        self.last_phase_change_time = current_time
                        self.speed = self.stealth_speed
                        self.stealth_change_direction_timer = current_time
                        # Set an initial random target for the stealth movement
                        self._set_random_stealth_target(player)
                        print("Boss 9 entered stealth mode!")
                        
                        # Reset egg laying counter for this stealth phase
                        self.eggs_laid_this_phase = 0
                        # Calculate timing for the 3 eggs (at 1/4, 1/2, and 3/4 of stealth duration)
                        self.egg_laying_times = [
                            current_time + (self.stealth_phase_duration * 0.25),
                            current_time + (self.stealth_phase_duration * 0.5),
                            current_time + (self.stealth_phase_duration * 0.75)
                        ]
                        
                        # Play a sound effect for stealth mode
                        if self.sound_manager:
                            self.sound_manager.play_sound('boss_special')
                            
                        # Play stealth mode voice
                        if self.level == 9:
                            self.sound_manager.play_sound("effects/boss_9_voice")
                            self.last_voice_time = current_time
                        
                    elif self.stealth_mode and current_time - self.last_phase_change_time >= self.stealth_phase_duration:
                        # Switch back to normal mode
                        self.stealth_mode = False
                        self.last_phase_change_time = current_time
                        self.speed = self.normal_speed
                        # Clear any path that might have been set during stealth mode
                        self.path = []
                        print("Boss 9 returned to normal mode")
                        
                        # Shoot a fast projectile at the player when exiting stealth mode
                        if player:
                            # Calculate direction to player
                            dx = player.rect.centerx - self.rect.centerx
                            dy = player.rect.centery - self.rect.centery
                            direction = math.atan2(dy, dx)
                            
                            # Create a fast projectile with toxic green color
                            projectile = BossProjectile(
                                self.rect.centerx, 
                                self.rect.centery, 
                                direction, 
                                speed=5.0,  # Very fast projectile
                                damage=20,
                                color=(80, 220, 80),  # Toxic green
                                boss_level=self.level
                            )
                            self.projectiles.add(projectile)
                            
                            # Place a slowing puddle under the player
                            poison_trail = PoisonTrail(
                                player.rect.centerx,
                                player.rect.centery,
                                TILE_SIZE,  # Size of the puddle
                                0 if self.level == 9 else 15,  # No damage for level 9 boss, 15 damage for others
                                creator=self  # Reference to the boss
                            )
                            
                            # Make sure poison_trails attribute exists
                            if not hasattr(self, 'poison_trails'):
                                self.poison_trails = pygame.sprite.Group()
                                
                            self.poison_trails.add(poison_trail)
                            
                            # Play sound effect
                            if self.sound_manager:
                                self.sound_manager.play_sound('boss_special')
                    
                    # During stealth mode, change direction periodically
                    if self.stealth_mode and current_time - self.stealth_change_direction_timer >= self.stealth_direction_change_interval:
                        self._set_random_stealth_target(player)
                        self.stealth_change_direction_timer = current_time
                        
                    # Consistently lay 3 eggs at pre-determined times during stealth phase
                    if self.stealth_mode and self.eggs_laid_this_phase < 3 and len(self.egg_laying_times) > 0:
                        if current_time >= self.egg_laying_times[0]:
                            self._lay_egg()
                            self.eggs_laid_this_phase += 1
                            self.egg_laying_times.pop(0)  # Remove the used timing
                
            # Update existing eggs
            eggs_to_remove = []
            for egg in list(self.eggs):
                try:
                    # Update egg (handles hatching and spawning)
                    egg.update(current_time)
                except Exception as e:
                    print(f"Error updating egg: {e}")
                    eggs_to_remove.append(egg)
                    
                # Eggs are now managed by their own update method
                # The collision with player is still handled here
                if not egg.hatching and egg in self.eggs:  # Only check player collision if not hatching
                    if egg.rect.colliderect(player.hitbox):
                        egg.kill()
                        print("Player destroyed an egg")
                        eggs_to_remove.append(egg)
            
            # Remove any eggs that had errors
            for egg in eggs_to_remove:
                if egg in self.eggs:
                    self.eggs.remove(egg)
        
        # Note: We skip the jump animation check here since bosses don't jump
        # This fixes the double texture loading issue
        
        # Calculate distance to player
        dx = player.rect.centerx - self.rect.centerx
        dy = player.rect.centery - self.rect.centery
        distance = math.sqrt(dx * dx + dy * dy)
        
        # Current time for cooldown calculations
        current_time = pygame.time.get_ticks()
        
        # Always mark that boss has spotted player if within detection range
        # For level 2 boss, increase detection range substantially
        # For level 7 boss, also increase detection range to match level 2
        detection_range = self.detection_range
        if self.level == 2 or self.level == 7:
            detection_range *= 2  # Double the detection range
        
        if distance <= detection_range:
            # If Boss 5 or Boss 8 spots the player for the first time, create orbiting projectiles
            if (self.level == 5 or self.level == 8) and not self.has_spotted_player and not self.orbiting_projectiles_created:
                print(f"Boss {self.level} spotted player, creating orbiting projectiles")
                self.special_attack(player)
            
            self.has_spotted_player = True
            
            # Start combat timer for level 4 boss
            if self.level == 4 and not self.in_combat:
                self.in_combat = True
                self.combat_start_time = current_time
                # Set the initial last_defensive_mode_time to the current time
                # This ensures the boss doesn't immediately enter defensive mode
                self.last_defensive_mode_time = current_time
                print("Level 4 boss engaging in combat - chase phase starting")
                
            # Start combat timer for level 1 boss blood zones
            if self.level == 1 and not self.in_combat_with_player:
                self.in_combat_with_player = True
                self.combat_start_time = current_time
                # Set last zone creation time so first zone appears after the delay
                self.last_zone_creation_time = current_time
                print(f"Level 1 boss engaging in combat - blood zone mechanic activated")
        
        # Level 4 boss defensive mode logic
        if self.level == 4 and self.in_combat:
            # Calculate time since combat started
            if not self.defensive_mode_engaged:
                # Check if it's time to activate defensive mode
                time_since_last_defensive = current_time - self.last_defensive_mode_time
                if time_since_last_defensive >= self.defensive_mode_cooldown:
                    # Activate defensive mode
                    self.defensive_mode_engaged = True
                    self.defensive_mode = True
                    self.last_defensive_mode_time = current_time
                    
                    # Store the current image to restore later
                    self.normal_image = self.image
                    
                    # Switch to defensive image if available
                    if self.defensive_image:
                        self.image = self.defensive_image
                        # Force it to be used immediately
                        print(f"Switching to defensive image: {id(self.defensive_image)}")
                    
                    # Play defensive sound
                    self.sound_manager.play_sound("effects/boss_4_def")
                    print(f"Level 4 boss entering defensive mode at time {current_time}!")
                else:
                    # Debug output to track the defensive mode cooldown
                    if current_time % 1000 < 20:  # Only print once per second approximately
                        print(f"Time until defensive mode: {self.defensive_mode_cooldown - time_since_last_defensive} ms")
            else:
                # Already in defensive mode, check if it's time to deactivate
                time_in_defensive_mode = current_time - self.last_defensive_mode_time
                if time_in_defensive_mode >= self.defensive_mode_duration:
                    # Deactivate defensive mode
                    self.defensive_mode_engaged = False
                    self.defensive_mode = False
                    
                    # Restore normal image
                    if hasattr(self, 'normal_image') and self.normal_image:
                        self.image = self.normal_image
                    
                    # Ensure reflected damage is reset when leaving defensive mode
                    self.reflected_damage = 0
                    
                    # After leaving defensive mode, shoot a rope at the player
                    self.is_shooting_rope = True
                    self.rope_start_time = current_time
                    self.rope_target = player
                    self.rope_length = 0
                    self.rope_reached_player = False
                    self.rope_end_pos = (self.rect.centerx, self.rect.centery)
                    self.is_pulling_player = False
                    print(f"Level 4 boss starting to shoot rope at player at time {current_time}!")
                    
                    # Play the boss voice when leaving defensive mode
                    voice_file = f"effects/boss_{self.level}_voice"
                    self.sound_manager.play_sound(voice_file)
                    self.last_voice_time = current_time
                        
                    print(f"Level 4 boss leaving defensive mode at time {current_time}!")
        
        # Handle rope shooting and player pulling for boss level 4
        if self.level == 4 and self.is_shooting_rope:
            # Calculate rope extension
            time_shooting_rope = current_time - self.rope_start_time
            
            # Update rope end position while it's extending
            if not self.rope_reached_player and not self.is_pulling_player:
                # Calculate direction vector to player
                dx = player.rect.centerx - self.rect.centerx
                dy = player.rect.centery - self.rect.centery
                distance = math.sqrt(dx*dx + dy*dy)
                
                if distance > 0:
                    # Normalize direction
                    dx /= distance
                    dy /= distance
                    
                    # Calculate new rope length but don't exceed max length
                    self.rope_length = min(self.rope_length + self.rope_speed, self.rope_max_length)
                    
                    # Calculate new end position
                    new_x = self.rect.centerx + dx * self.rope_length
                    new_y = self.rect.centery + dy * self.rope_length
                    
                    # Check if there's a clear line of sight to the new position
                    has_line_of_sight = self.check_line_of_sight(
                        self.rect.centerx, self.rect.centery,
                        new_x, new_y,
                        player.level
                    )
                    
                    if has_line_of_sight:
                        # Update rope end position
                        self.rope_end_pos = (new_x, new_y)
                        
                        # Check if rope reached player
                        player_rect = pygame.Rect(player.rect.x, player.rect.y, player.rect.width, player.rect.height)
                        rope_end_rect = pygame.Rect(new_x - 5, new_y - 5, 10, 10)
                        if rope_end_rect.colliderect(player_rect):
                            # Rope reached player, start pulling
                            self.rope_reached_player = True
                            self.is_pulling_player = True
                            self.pull_start_time = current_time
                            print(f"Rope reached player! Starting pull at {current_time}")
                    else:
                        # Hit a wall, stop extending rope
                        print(f"Rope hit a wall at length {self.rope_length}")
                        self.is_shooting_rope = False
            
            # Handle player pulling if rope has reached player
            if self.is_pulling_player:
                time_pulling = current_time - self.pull_start_time
                
                if time_pulling < self.pull_duration:
                    # Calculate pull direction
                    dx = self.rect.centerx - player.rect.x
                    dy = self.rect.centery - player.rect.y
                    distance = math.sqrt(dx*dx + dy*dy)
                    
                    if distance > 0:
                        # Normalize and scale by pull speed
                        dx = dx / distance * self.rope_pull_speed
                        dy = dy / distance * self.rope_pull_speed
                        
                        # Move player toward boss
                        player.rect.x += dx
                        player.rect.y += dy
                        
                        # Keep rope end at player position
                        self.rope_end_pos = (player.rect.centerx, player.rect.centery)
                else:
                    # Pulling complete
                    self.is_pulling_player = False
                    self.is_shooting_rope = False
                    print(f"Finished pulling player at {current_time}")
            
            # End rope shooting after its duration
            if time_shooting_rope > self.rope_duration and not self.is_pulling_player:
                self.is_shooting_rope = False
                print(f"Rope shooting ended at {current_time}")
                
        # Level 5 boss casting mode logic
        if (self.level == 5 or self.level == 8) and self.has_spotted_player:
            if not self.casting_mode:
                # Check if it's time to activate casting mode
                time_since_last_cast = current_time - self.last_cast_time
                if time_since_last_cast >= self.casting_mode_cooldown:
                    # Activate casting mode
                    self.casting_mode = True
                    self.cast_complete = False
                    self.last_cast_time = current_time
                    print(f"Boss {self.level} entering casting mode at time {current_time}")
            else:
                # In casting mode
                time_in_casting = current_time - self.last_cast_time
                
                # Fire projectiles when casting starts
                if not self.cast_complete:
                    # Create projectiles appropriate for this boss level
                    self.cast_projectiles(player)
                    self.cast_complete = True
                
                # Check if casting is complete
                if time_in_casting >= self.casting_mode_duration:
                    # Deactivate casting mode
                    self.casting_mode = False
                    print(f"Boss {self.level} leaving casting mode at time {current_time}")
                    
                    # For Boss 8, activate floor projectiles when casting completes
                    if self.level == 8 and hasattr(self, 'floor_projectiles'):
                        for projectile in self.floor_projectiles:
                            # Set creation time to now for duration tracking
                            projectile.creation_time = current_time
                        print(f"Activated {len(self.floor_projectiles)} floor projectiles for damage")
                        # Clear the list (but not the projectiles themselves)
                        self.floor_projectiles = []
        
        # Boss 6 teleportation logic
        if self.level == 6 and self.has_spotted_player:
            if not self.is_teleporting and not self.casting_mode:
                # Check if it's time to start casting for teleport
                time_since_last_teleport = current_time - self.last_teleport_time
                if time_since_last_teleport >= self.teleport_cooldown:
                    # Start casting mode
                    self.casting_mode = True
                    self.cast_start_time = current_time
                    self.teleport_alpha = 255  # Start fully visible
                    
                    # Store current image to restore later
                    self.normal_image = self.image
                    
                    # Switch to teleport cast image if available
                    if self.teleport_cast_image:
                        self.image = self.teleport_cast_image
                        print(f"Switching to teleport cast image for casting")
                    
                    # Play casting sound
                    self.sound_manager.play_sound("effects/boss_cast")
                    print(f"Boss 6 starting casting at time {current_time}")
            elif self.casting_mode:
                # In casting mode
                time_in_casting = current_time - self.cast_start_time
                
                # Stop movement during casting
                self.velocity_x = 0
                self.velocity_y = 0
                
                # Fade out during casting
                self.teleport_alpha = int(255 * (1 - (time_in_casting / self.casting_mode_duration)))
                
                # Check if casting is complete
                if time_in_casting >= self.casting_mode_duration:
                    # End casting and start teleportation
                    self.casting_mode = False
                    self.is_teleporting = True
                    self.teleport_start_time = current_time
                    self.teleport_alpha = 0  # Start invisible for teleport
                    print(f"Boss 6 casting complete, starting teleportation at time {current_time}")
            elif self.is_teleporting:
                # In teleportation process
                time_in_teleport = current_time - self.teleport_start_time
                
                # First half: stay invisible
                if time_in_teleport < self.teleport_duration / 2:
                    self.teleport_alpha = 0
                    
                    # At the midpoint, set new position
                    if not self.teleport_target_pos:
                        # Find a new position to teleport to
                        new_x = random.randint(TILE_SIZE, (ROOM_WIDTH - 2) * TILE_SIZE)
                        new_y = random.randint(TILE_SIZE, (ROOM_HEIGHT - 2) * TILE_SIZE)
                        self.rect.x = new_x
                        self.rect.y = new_y
                        self.teleport_target_pos = (new_x, new_y)
                # Second half: fade in
                else:
                    self.teleport_alpha = int(255 * ((time_in_teleport - self.teleport_duration/2) / (self.teleport_duration/2)))
                
                # Check if teleportation is complete
                if time_in_teleport >= self.teleport_duration:
                    self.is_teleporting = False
                    self.last_teleport_time = current_time
                    self.teleport_target_pos = None
                    self.teleport_alpha = 255
                    
                    # Restore normal image
                    if hasattr(self, 'normal_image') and self.normal_image:
                        self.image = self.normal_image
                    
                    # Play teleport completion voice
                    if self.level == 6:
                        self.sound_manager.play_sound("effects/boss_6_voice_tele")
                        self.last_voice_time = current_time
                    
                                        # Shoot a projectile at the player when teleportation is complete
                    # Calculate normalized direction vector to player
                    dx = player.rect.centerx - self.rect.centerx
                    dy = player.rect.centery - self.rect.centery
                    length = math.sqrt(dx*dx + dy*dy)
                    
                    if length > 0:
                        # Normalize
                        dx = dx / length
                        dy = dy / length
                        
                        # Create a homing teleport projectile with a unique purple color
                        projectile = BossProjectile(
                            self.rect.centerx, 
                            self.rect.centery, 
                            (dx, dy), 
                            1.6,  # Slightly faster than Boss 2 projectiles
                            self.damage * 1.2,  # 20% more damage than normal
                            color=(160, 32, 240),  # Purple color for teleport projectile
                            is_homing=True,  # Enable homing behavior
                            boss_level=self.level  # Pass the boss level for animated projectiles
                        )
                        
                        # Store reference to player for homing
                        projectile.player_target = player
                        
                        # Enhance the trail effect
                        projectile.trail_enabled = True
                        projectile.max_trail_length = 12  # Longer trail for dramatic effect
                        projectile.trail_update_rate = 1  # Update every frame for smoother trail
                        
                        # Make it hunt the player more aggressively
                        projectile.homing_strength = 0.04  # More aggressive turning
                        projectile.max_homing_time = 5000  # Home for longer (5 seconds)
                        
                        # Increase projectile lifetime
                        projectile.max_distance = TILE_SIZE * 20  # Double the normal distance
                        
                        # Add to projectile group
                        self.projectiles.add(projectile)
                        
                        # Play a sound effect if available
                        self.sound_manager.play_sound("effects/projectile")

                    print(f"Boss 6 teleportation complete at time {current_time}")
        
        # Level 2 boss: use special attack when player is in range but not in melee range
        # (to avoid spamming when in close combat)
        if self.level == 2 and self.has_spotted_player and distance > self.attack_range * 2:
            self.special_attack(player)
        
        # Update state based on distance to player
        if distance <= self.attack_range:
            # Attack state - use melee attack when in range
            self.state = 'attack'
            self.velocity_x = 0
            self.velocity_y = 0
            self.attack(player)
        elif self.has_spotted_player and not (self.level == 4 and self.defensive_mode) and not ((self.level == 5 or self.level == 8) and self.casting_mode) and not (self.level == 6 and (self.casting_mode or self.is_teleporting)):
            # Chase state - always chase once spotted (unless in special state)
            # Don't chase if:
            # - Level 4 boss in defensive mode
            # - Level 5/8 boss in casting mode
            # - Level 6 boss in casting mode or teleporting
            self.state = 'chase'
            self.current_state = 'walk'
            self.move_towards_player(player)
        else:
            # Idle state - stand still during special states
            self.state = 'idle'
            self.current_state = 'idle'
            self.velocity_x = 0
            self.velocity_y = 0
        
        # If level 4 boss is in defensive mode or level 5/8 boss is in casting mode or level 6 boss is casting/teleporting, ensure it doesn't move
        if ((self.level == 4 and self.defensive_mode) or 
            ((self.level == 5 or self.level == 8) and self.casting_mode) or 
            (self.level == 6 and (self.casting_mode or self.is_teleporting))):
            self.velocity_x = 0
            self.velocity_y = 0
            self.state = 'idle'
            self.current_state = 'idle'
        
        # Store old position to handle collisions
        old_rect = self.rect.copy()
        
        # Horizontal movement - simplified with no half-step attempts
        self.rect.x += self.velocity_x
        
        # If collision occurs, try with half the velocity
        if hasattr(player, 'level') and player.level and player.level.check_collision(self.collision_rect, entity=self):
            self.rect.x = old_rect.x
            # Update collision rect to match main rect
            self.collision_rect.centerx = self.rect.centerx
            # Try to move vertically if horizontal movement is blocked
            if self.velocity_x != 0 and self.velocity_y == 0:
                # Try to move up or down to get around the obstacle
                if random.choice([True, False]):
                    self.velocity_y = self.speed * 0.5
                else:
                    self.velocity_y = -self.speed * 0.5
        
        # Vertical movement - simplified with no half-step attempts
        self.rect.y += self.velocity_y
        # Update collision rect position
        self.collision_rect.centery = self.rect.centery
        
        if hasattr(player, 'level') and player.level and player.level.check_collision(self.collision_rect, entity=self):
            # Simply revert if collision occurs
            self.rect.y = old_rect.y
            # Update collision rect to match main rect
            self.collision_rect.centery = self.rect.centery
            # Try to move horizontally if vertical movement is blocked
            if self.velocity_y != 0 and self.velocity_x == 0:
                # Try to move left or right to get around the obstacle
                if random.choice([True, False]):
                    self.velocity_x = self.speed * 0.5
                else:
                    self.velocity_x = -self.speed * 0.5
        
        # Keep boss on screen
        self.rect.clamp_ip(pygame.display.get_surface().get_rect())
        
        # Update the damage hitbox to match the new position of the movement hitbox
        # Position the damage hitbox so it's properly aligned with the visual sprite
        
        # Calculate the expected dimensions based on the current image
        expected_width = self.image.get_width()
        expected_height = self.image.get_height()
        
        # Update visual offset based on current image size
        self.visual_offset_x = (expected_width - self.rect.width) // 2
        self.visual_offset_y = (expected_height - self.rect.height) // 2
        
        # Calculate damage hitbox dimensions (90% of visual sprite)
        damage_width = int(expected_width * 0.9)
        damage_height = int(expected_height * 0.9)
        
        # Position the damage hitbox to properly cover the visual sprite
        self.damage_hitbox.width = damage_width
        self.damage_hitbox.height = damage_height
        self.damage_hitbox.centerx = self.rect.centerx
        self.damage_hitbox.centery = self.rect.centery
        
        # Update animation
        self.animation_time += self.animation_speed
        
        # If attack or special animation is done, go back to previous state
        if (self.current_state == 'attack' or self.current_state == 'special') and self.animation_time >= len(self.animations[self.current_state][self.facing]):
            self.current_state = 'idle' if self.state == 'idle' else 'walk'
            self.animation_time = 0
            
        # Calculate current frame
        self.frame = int(self.animation_time) % len(self.animations[self.current_state][self.facing])
        
        # Only update image from animation frames if not in defensive mode (for level 4 boss)
        # and not in special states for level 6 boss
        if not ((self.level == 4 and self.defensive_mode) or 
                (self.level == 7 and self.defensive_mode) or
                (self.level == 6 and (self.casting_mode or self.is_teleporting) and hasattr(self, 'teleport_cast_image') and self.teleport_cast_image)):
            self.image = self.animations[self.current_state][self.facing][self.frame]
            
        # Apply fade effects for Boss 6
        if self.level == 6 and (self.casting_mode or self.is_teleporting):
            # Create a copy of the image with alpha
            alpha_surface = pygame.Surface(self.image.get_size(), pygame.SRCALPHA)
            alpha_surface.blit(self.image, (0, 0))
            alpha_surface.set_alpha(self.teleport_alpha)
            self.image = alpha_surface
        
        # Apply transparency effect for Boss 9 in stealth mode
        if self.level == 9 and self.stealth_mode:
            # Create a copy of the image with alpha
            alpha_surface = pygame.Surface(self.image.get_size(), pygame.SRCALPHA)
            alpha_surface.blit(self.image, (0, 0))
            alpha_surface.set_alpha(self.stealth_alpha)
            self.image = alpha_surface
            
            # Add ghost-like particle effects for stealth visualization
            if hasattr(self, 'particle_manager') and self.particle_manager and random.random() < 0.15:
                for _ in range(2):
                    offset_x = random.randint(-20, 20)
                    offset_y = random.randint(-20, 20)
                    self.particle_manager.add_particle(
                        particle_type='fade',
                        pos=(self.rect.centerx + offset_x, self.rect.centery + offset_y),
                        velocity=(random.uniform(-0.5, 0.5), random.uniform(-0.5, 0.1)),
                        direction=random.uniform(0, 360),
                        color=(100, 100, 255, 150),  # Blue-purple ghost color
                        size=random.randint(3, 8),
                        lifetime=random.randint(10, 25)
                    )
        
        # Update projectiles for level 2, 5, 6, and 8 bosses
        if self.level in [2, 5, 6, 8]:
            # Update projectiles
            for projectile in self.projectiles:
                projectile.update()
                
                # Check collisions with player for level 2 boss
                if projectile.check_collision(player.hitbox):
                    player.take_damage(projectile.damage)
                    # Only destroy non-orbiting projectiles
                    if not hasattr(projectile, 'is_orbiting') or not projectile.is_orbiting:
                        projectile.kill()
            
            # Remove projectiles that go off screen for level 2 boss
            if self.level == 2:
                screen_rect = pygame.Rect(0, 0, ROOM_WIDTH * TILE_SIZE, ROOM_HEIGHT * TILE_SIZE)
                for projectile in list(self.projectiles):
                    if not screen_rect.colliderect(projectile.rect):
                        projectile.kill()
        
        # Update projectiles for level 7 boss
        if self.level == 7:
            # Update projectiles
            for projectile in self.projectiles:
                projectile.update()
                
                # Check collisions with player
                if projectile.check_collision(player.hitbox):
                    player.take_damage(projectile.damage)
                    projectile.kill()
            
            # Remove projectiles that go off screen
            screen_rect = pygame.Rect(0, 0, ROOM_WIDTH * TILE_SIZE, ROOM_HEIGHT * TILE_SIZE)
            for projectile in list(self.projectiles):
                if not screen_rect.colliderect(projectile.rect):
                    projectile.kill()
        
        # Update blood zones for boss 1
        if self.level == 1 and self.in_combat_with_player:
            # First, update all existing blood zones
            self.blood_zones.update()
            
            # Check if it's time to create a new blood zone
            combat_duration = current_time - self.combat_start_time
            if (combat_duration >= self.zone_creation_delay and 
                current_time - self.last_zone_creation_time >= self.zone_creation_interval):
                
                # Create a blood zone under the player
                blood_zone = BloodZone(
                    player.rect.centerx, 
                    player.rect.centery,
                    self.zone_size,
                    self.zone_damage,
                    creator=self
                )
                self.blood_zones.add(blood_zone)
                self.last_zone_creation_time = current_time
                
                # Create visual effect and play sound
                if hasattr(player, 'game') and player.game and hasattr(player.game, 'particle_system'):
                    for _ in range(10):
                        offset_x = random.randint(-20, 20)
                        offset_y = random.randint(-20, 20)
                        player.game.particle_system.create_particle(
                            player.rect.centerx + offset_x,
                            player.rect.centery + offset_y,
                            color=(220, 0, 0),
                            size=random.randint(3, 7),
                            speed=random.uniform(0.7, 1.8),
                            lifetime=random.randint(25, 40)
                        )
                
                # Play sound effect for blood zone creation
                if self.sound_manager:
                    self.sound_manager.play_sound('boss_special')
                
                print(f"Boss 1 created a blood zone under the player")
            
            # Check collision with player for all blood zones
            for zone in self.blood_zones:
                if zone.check_collision(player.hitbox) and zone.can_damage():
                    # Damage player
                    player.take_damage(zone.damage)
                    
                    # Heal the boss by 5x the damage amount
                    self.health = min(self.max_health, self.health + (zone.damage * 5))
                    
                    # Display healing effect
                    if hasattr(player, 'game') and player.game and hasattr(player.game, 'particle_system'):
                        # Create healing particles that look like blood drops
                        for _ in range(12):  # Create several small drops
                            offset_x = random.randint(-20, 20)
                            offset_y = random.randint(-20, 20)
                            
                            # Red colors for blood drops
                            red_intensity = random.randint(180, 255)
                            particle_color = (
                                red_intensity,         # Strong red component
                                random.randint(0, 30), # Very little green
                                random.randint(0, 30)  # Very little blue
                            )
                            
                            # Upward movement for healing effect
                            upward_velocity = random.uniform(-1.5, -0.3)  # Negative y is upward
                            slight_x_drift = random.uniform(-0.3, 0.3)    # Slight horizontal drift
                            
                            player.game.particle_system.create_particle(
                                self.rect.centerx + offset_x,
                                self.rect.centery + offset_y,
                                color=particle_color,
                                velocity=(slight_x_drift, upward_velocity),
                                size=random.randint(2, 4),  # Smaller particles
                                lifetime=random.randint(20, 35)  # Shorter lifetime
                            )
                    
                    # Display feedback message if possible
                    if hasattr(player, 'game') and hasattr(player.game, 'display_message'):
                        player.game.display_message("Boss healed from blood zone!", (220, 0, 0))
        
        # Handle boss voice sound effect
        if distance <= detection_range:
            if not self.has_seen_player:
                voice_file = f"effects/boss_{self.level}_voice"
                self.sound_manager.play_sound(voice_file)
                self.has_seen_player = True
                self.last_voice_time = current_time
                print(f"Level {self.level} boss spotted player - playing initial voice")
            # Only play the voice on cooldown for bosses other than level 3, 4, 5, 6, 7, 8, and 9
            # For level 4 boss, we'll play it when exiting defensive mode instead
            # For level 3 boss, we play it when entering defensive mode (handled elsewhere)
            # For level 5 boss, we play boss_5_try.wav every 10 seconds
            # For level 6 boss, we play boss_6_voice_tele after teleport (handled elsewhere)
            # For level 7 boss, we play boss_7_voice every 10 seconds
            # For level 8 boss, we play boss_8_voice every 10 seconds
            # For level 9 boss, we play voice when entering stealth mode (handled elsewhere)
            elif self.level == 5 and current_time - self.last_voice_time >= 10000:  # 10 seconds
                self.sound_manager.play_sound("effects/boss_5_try")
                self.last_voice_time = current_time
            elif self.level == 7 and current_time - self.last_voice_time >= 10000:  # 10 seconds
                self.sound_manager.play_sound("effects/boss_7_voice")
                self.last_voice_time = current_time
            elif self.level == 8 and current_time - self.last_voice_time >= 10000:  # 10 seconds
                self.sound_manager.play_sound("effects/boss_8_voice")
                self.last_voice_time = current_time
            elif self.level != 3 and self.level != 4 and self.level != 5 and self.level != 6 and self.level != 7 and self.level != 8 and self.level != 9 and current_time - self.last_voice_time >= self.voice_cooldown:
                voice_file = f"effects/boss_{self.level}_voice"
                self.sound_manager.play_sound(voice_file)
                self.last_voice_time = current_time
        
        # Update position history for trailing effect
        if self.trail_enabled:
            self.trail_frame_counter += 1
            if self.trail_frame_counter >= self.trail_update_rate:
                self.trail_frame_counter = 0
                # Store both position and current sprite image
                self.position_history.append((
                    self.rect.x, 
                    self.rect.y, 
                    self.image.copy()  # Store a copy of the current sprite
                ))
                
                if len(self.position_history) > self.max_trail_length:
                    self.position_history.pop(0)

        # Update Boss 6 poison trails
        if self.level == 6 and self.has_spotted_player:
            # Update existing trails
            self.poison_trails.update()
            
            # Create new trails while moving and not teleporting
            current_time = pygame.time.get_ticks()
            if not self.is_teleporting and self.state == 'chase' and (self.velocity_x != 0 or self.velocity_y != 0):
                if current_time - self.last_trail_time >= self.trail_interval:
                    # Create new trail at current position with reference to the boss
                    new_trail = PoisonTrail(
                        self.rect.centerx, 
                        self.rect.centery, 
                        self.trail_size, 
                        0 if self.level == 9 else 5,  # No damage for level 9 boss, 5 damage for others
                        creator=self  # Pass reference to the boss
                    )
                    self.poison_trails.add(new_trail)
                    self.last_trail_time = current_time
            
            # Check for player collision with trails
            for trail in self.poison_trails:
                if trail.check_collision(player.hitbox):
                    # Apply damage - fixed amount of 5, but only if cooldown allows
                    if hasattr(trail, 'can_damage') and trail.can_damage():
                        player.take_damage(1)  # Reduced to 1 damage per hit
                    
                    # Apply slow effect - simplified direct approach
                    # Store original speed if first time
                    if not hasattr(player, '_original_speed'):
                        player._original_speed = player.speed
                    
                    # Apply the slow effect
                    player.speed = player._original_speed * 0.5
                    
                    # Set the debuff end time
                    player._speed_debuff_end_time = current_time + 2000  # 2 seconds
                    print(f"Player speed reduced to 50% for 2 seconds")
            
            # Check if debuff should be removed - do this every frame
            if hasattr(player, '_original_speed') and hasattr(player, '_speed_debuff_end_time'):
                if current_time >= player._speed_debuff_end_time:
                    # Restore original speed
                    player.speed = player._original_speed
                    # Delete the end time so this only happens once per debuff
                    delattr(player, '_speed_debuff_end_time')
                    print("Player speed restored")
                    
        # Update Boss 9 poison trails
        if self.level == 9 and hasattr(self, 'poison_trails'):
            # Update existing trails
            self.poison_trails.update()
            
            # Check collision with player
            for trail in self.poison_trails:
                if trail.check_collision(player.hitbox):
                    # Apply damage only if cooldown allows
                    if hasattr(trail, 'can_damage') and trail.can_damage():
                        player.take_damage(trail.damage)
                    
                    # Apply slow effect - same mechanism as boss 6
                    # Store original speed if first time
                    if not hasattr(player, '_original_speed'):
                        player._original_speed = player.speed
                    
                    # Apply the slow effect
                    player.speed = player._original_speed * 0.5
                    
                    # Set the debuff end time
                    player._speed_debuff_end_time = current_time + 2000  # 2 seconds
                    print(f"Player speed reduced to 50% for 2 seconds")
        
        
            # Check if debuff should be removed - do this every frame
            if hasattr(player, '_original_speed') and hasattr(player, '_speed_debuff_end_time'):
                if current_time >= player._speed_debuff_end_time:
                    # Restore original speed
                    player.speed = player._original_speed
                    # Delete the end time so this only happens once per debuff
                    delattr(player, '_speed_debuff_end_time')
                    print("Player speed restored")
        
        # Level 7 boss shield mode logic (based on level 4)
        if self.level == 7 and self.has_spotted_player:
            # Use simpler logic than level 4 - just cycle between normal and shield mode
            if not self.defensive_mode_engaged:
                # Check if it's time to activate shield mode
                time_since_last_defensive = current_time - self.last_defensive_mode_time
                if time_since_last_defensive >= self.defensive_mode_cooldown:
                    # Remove death ray when entering shield mode
                    if self.has_death_ray and self.death_ray:
                        self.death_ray.kill()
                        self.death_ray = None
                        self.has_death_ray = False
                        print(f"Level 7 boss destroyed death ray when entering shield mode")
                        
                    # Activate shield mode
                    self.defensive_mode_engaged = True
                    self.defensive_mode = True
                    self.last_defensive_mode_time = current_time
                    self.shield_growth = 0  # Start with original shield size
                    self.cursed_shield_dropped = False  # Reset the flag when entering shield mode
                    
                    # Store the current image to restore later
                    self.normal_image = self.image
                    
                    # Switch to defensive image if available
                    if self.defensive_image:
                        self.image = self.defensive_image
                        # Force it to be used immediately
                        print(f"Switching to defensive image for level 7 boss: {id(self.defensive_image)}")
                    
                    # Play defensive sound
                    if self.level == 7:
                        # Don't play level 4's sound for level 7 boss
                        print(f"Level 7 boss entering shield mode at time {current_time}!")
                    else:
                        self.sound_manager.play_sound("effects/boss_4_def")  # Only for level 4
                    print(f"Level {self.level} boss entering shield mode at time {current_time}!")
                    
                    # Summon homing projectiles at the start of shield mode
                    self.summon_homing_projectiles(player)
                else:
                    # Debug output to track the shield mode cooldown
                    if current_time % 1000 < 20:  # Only print once per second approximately
                        print(f"Time until level 7 shield mode: {self.defensive_mode_cooldown - time_since_last_defensive} ms")
            else:
                # Already in shield mode, check if it's time to deactivate
                time_in_defensive_mode = current_time - self.last_defensive_mode_time
                if time_in_defensive_mode >= self.defensive_mode_duration:
                    # Drop the shield as a stationary cursed area
                    if hasattr(self, 'shield_radius') and self.shield_radius > 0:
                        # Create a cursed shield at the boss's current position
                        cursed_shield = CursedShield(
                            self.rect.centerx,
                            self.rect.centery,
                            self.shield_radius * 2,  # Diameter
                            self.shield_damage  # Same damage as the shield
                        )
                        
                        # Add to player's level if possible
                        if hasattr(player, 'level') and hasattr(player.level, 'cursed_shields'):
                            player.level.cursed_shields.add(cursed_shield)
                        else:
                            # Initialize the cursed_shields group if it doesn't exist
                            if hasattr(player, 'level'):
                                if not hasattr(player.level, 'cursed_shields'):
                                    player.level.cursed_shields = pygame.sprite.Group()
                                player.level.cursed_shields.add(cursed_shield)
                        
                        print(f"Level 7 boss dropped a cursed shield at ({self.rect.centerx}, {self.rect.centery})")
                        self.cursed_shield_dropped = True  # Mark that shield has been dropped
                    
                    # Create death ray after dropping shield
                    if not self.has_death_ray:
                        # Create a death ray that will spin around the boss
                        self.death_ray = DeathRay(
                            self,             # The boss is the origin
                            4,                # 4 tiles length
                            self.damage * 0.3 # 30% of boss damage per hit
                        )
                        self.has_death_ray = True
                        
                        # Add to level if it has sprite groups for tracking
                        if hasattr(player, 'level'):
                            # Initialize death_rays group if it doesn't exist
                            if not hasattr(player.level, 'death_rays'):
                                player.level.death_rays = pygame.sprite.Group()
                            player.level.death_rays.add(self.death_ray)
                        
                        print(f"Level 7 boss created a death ray")
                    
                    # Deactivate shield mode and resume chasing immediately
                    self.defensive_mode_engaged = False
                    self.defensive_mode = False
                    
                    # Restore normal image
                    if hasattr(self, 'normal_image') and self.normal_image:
                        self.image = self.normal_image
                    
                    # Ensure reflected damage is reset when leaving shield mode
                    self.reflected_damage = 0
                    
                    # Play the boss voice when leaving shield mode
                    voice_file = f"effects/boss_4_voice"  # Fallback to level 4 voice
                    # Check if boss 7 voice file exists
                    from config import SOUNDS_PATH
                    import os
                    if os.path.exists(os.path.join(SOUNDS_PATH, f"effects/boss_7_voice.mp3")) or \
                       os.path.exists(os.path.join(SOUNDS_PATH, f"effects/boss_7_voice.wav")):
                        voice_file = f"effects/boss_7_voice"
                    self.sound_manager.play_sound(voice_file)
                    self.last_voice_time = current_time
                        
                    print(f"Level 7 boss leaving shield mode at time {current_time}!")
                else:
                    # Update shield growth during the shield mode (0 to 1 over the duration)
                    self.shield_growth = min(1.0, time_in_defensive_mode / self.defensive_mode_duration)
                    
                    # Calculate shield radius based on growth
                    base_radius = TILE_SIZE * 2  # Base shield size of 2 tiles
                    growth_bonus = TILE_SIZE * 1.5  # Can grow up to 1.5 additional tiles
                    self.shield_radius = base_radius + (growth_bonus * self.shield_growth)
            
            # If in shield mode, check for collisions with the player
            if self.defensive_mode:
                current_time = pygame.time.get_ticks()
                
                # Check if player is colliding with the shield
                if hasattr(self, 'shield_radius') and self.shield_radius > 0:
                    # Calculate distance between boss center and player center
                    dx = player.rect.centerx - self.rect.centerx
                    dy = player.rect.centery - self.rect.centery
                    distance = math.sqrt(dx * dx + dy * dy)
                    
                    # If player is inside shield radius, damage them (with cooldown)
                    if distance < self.shield_radius:
                        # Check cooldown to avoid constant damage
                        if current_time - self.last_shield_damage_time >= self.shield_damage_cooldown:
                            # Damage player
                            player.take_damage(self.shield_damage)
                            self.last_shield_damage_time = current_time
                            
                            # Create visual effect showing shield damage
                            if hasattr(player.level, 'particle_system'):
                                for _ in range(8):  # Create several particles
                                    angle = random.uniform(0, math.pi * 2)
                                    speed = random.uniform(1.0, 2.0)
                                    dx = math.cos(angle) * speed
                                    dy = math.sin(angle) * speed
                                    
                                    player.level.particle_system.create_particle(
                                        player.rect.centerx,
                                        player.rect.centery,
                                        color=(150, 50, 255),  # Purple to match shield
                                        velocity=(dx, dy),
                                        size=random.randint(4, 8),
                                        lifetime=random.randint(20, 30)
                                    )
                            
                            # Display feedback to player
                            if hasattr(player.level, 'game') and hasattr(player.level.game, 'display_message'):
                                player.level.game.display_message("Shield damage!", (150, 50, 255))
            
            # Update death ray for level 7 boss
            if self.level == 7 and self.has_death_ray and self.death_ray:
                self.death_ray.update()
                
                # Check for player collision with death ray
                if self.death_ray.check_collision(player.hitbox) and self.death_ray.can_damage():
                    # Apply damage to player
                    player.take_damage(self.death_ray.damage)
                    
                    # Create visual effect at collision point
                    if hasattr(player.level, 'particle_system'):
                        for _ in range(10):  # Create several particles
                            angle = random.uniform(0, math.pi * 2)
                            speed = random.uniform(1.5, 3.0)
                            dx = math.cos(angle) * speed
                            dy = math.sin(angle) * speed
                            
                            player.level.particle_system.create_particle(
                                player.rect.centerx,
                                player.rect.centery,
                                color=(255, 100, 0),  # Orange-red for ray
                                velocity=(dx, dy),
                                size=random.randint(4, 8),
                                lifetime=random.randint(15, 25)
                            )
                    
                    # Display feedback to player
                    if hasattr(player.level, 'game') and hasattr(player.level.game, 'display_message'):
                        player.level.game.display_message("Death ray hit!", (255, 100, 0))
        
        # Rest of boss update code
        # ... existing code ...
    
    def draw(self, surface):
        # Skip the motion blur/trail effect when jumping (bosses don't jump)
        # This prevents duplicate texture blitting
            
        # Draw trailing effect for level 1 and 2 bosses (BEFORE drawing the main sprite)
        if self.trail_enabled and self.position_history:
            # Draw position history for trailing effect
            for i, (x, y, img) in enumerate(reversed(self.position_history)):
                # Calculate alpha (transparency) based on position in history
                # Make the oldest ones more transparent
                alpha = max(20, 150 - (i * 15))
                
                # Create a copy of the sprite with alpha transparency
                ghost_img = img.copy()
                # Set the alpha of the entire surface
                ghost_img.set_alpha(alpha)
                
                # Draw the ghost sprite at the historical position
                surface.blit(ghost_img, (x - self.visual_offset_x, y - self.visual_offset_y))
                
        # Draw poison trails for Boss 6 BEFORE drawing the boss
        if self.level == 6 and self.poison_trails:
            for trail in self.poison_trails:
                surface.blit(trail.image, trail.rect)
                
        # Draw poison trails for Boss 9 BEFORE drawing the boss
        if self.level == 9 and hasattr(self, 'poison_trails') and self.poison_trails:
            for trail in self.poison_trails:
                surface.blit(trail.image, trail.rect)
                
        # Draw blood zones for Boss 1 BEFORE drawing the boss
        if self.level == 1 and hasattr(self, 'blood_zones') and self.blood_zones:
            for zone in self.blood_zones:
                surface.blit(zone.image, zone.rect)
        
        # Calculate position with visual offset
        draw_x = self.rect.x - self.visual_offset_x
        draw_y = self.rect.y - self.visual_offset_y
        
        # For Boss 9, handle stealth mode and animation
        if self.level == 9:
            if self.boss9_is_animating and self.boss9_animation_frames:
                # Use the current animation frame
                img_to_draw = self.boss9_animation_frames[self.boss9_animation_index].copy()
            else:
                # Use the base image
                img_to_draw = self.image.copy()
                
            # Apply transparency if in stealth mode
            if self.stealth_mode:
                img_to_draw.set_alpha(self.stealth_alpha)
                
                # Add some ghost-like particles for stealth effect
                if random.random() < 0.2:  # 20% chance each frame to spawn particles
                    for _ in range(3):
                        offset_x = random.randint(-20, 20)
                        offset_y = random.randint(-20, 20)
                        size = random.randint(3, 8)
                        
                        # Use bluish-purple particles for stealth effect
                        color = (100, 100, 255, 150)
                        
                        # Create particle at boss's position
                        if hasattr(self, 'particle_manager') and self.particle_manager:
                            self.particle_manager.add_particle(
                                particle_type='fade',
                                pos=(self.rect.centerx + offset_x, self.rect.centery + offset_y),
                                velocity=(random.uniform(-0.5, 0.5), random.uniform(-0.5, 0.1)),
                                direction=random.uniform(0, 360),
                                color=color,
                                size=size,
                                lifetime=random.randint(15, 30)
                            )
            
            # Draw the selected image
            surface.blit(img_to_draw, (draw_x, draw_y))
            
        elif self.level == 3 and self.defensive_mode:
            # First draw the normal image
            surface.blit(self.image, (draw_x, draw_y))
            
            # Create a defensive aura around the boss
            aura_size = max(self.image.get_width(), self.image.get_height()) + 20
            aura_surface = pygame.Surface((aura_size, aura_size), pygame.SRCALPHA)
            
            # Draw multiple layers of the aura with different colors and sizes
            center = (aura_size // 2, aura_size // 2)
            
            # Outer shield ring (blue)
            shield_color = (0, 100, 255, 50)  # Light blue with transparency
            for i in range(3):
                radius = aura_size // 2 - i * 4
                thickness = 3 - i  # Decreasing thickness for inner rings
                pygame.draw.circle(aura_surface, shield_color, center, radius, thickness)
            
            # Pulsing inner shield (more solid)
            pulse_time = pygame.time.get_ticks() / 500  # Control pulse speed
            pulse_radius = aura_size // 3 + (math.sin(pulse_time) * 5)  # Pulsing effect
            pygame.draw.circle(aura_surface, (0, 150, 255, 80), center, pulse_radius, 0)
            
            # Draw the aura centered on the boss
            aura_x = draw_x + (self.image.get_width() - aura_size) // 2
            aura_y = draw_y + (self.image.get_height() - aura_size) // 2
            surface.blit(aura_surface, (aura_x, aura_y))
        
        elif self.level != 9:
            # For non-Boss 9 enemies, draw normally
            surface.blit(self.image, (draw_x, draw_y))
        
        # Draw resurrection effects if in blood puddle state
        if self.is_dead:
            current_time = pygame.time.get_ticks()
            
            # Calculate resurrection progress (0 to 1)
            time_left = self.resurrection_time - current_time
            progress = 1.0 - (time_left / 4000.0)  # 4000 = respawn time in ms
            
            # Add resurrection visual effects
            if progress > 0.5:  # Start effects at halfway point
                # Create a pulsing glow effect that grows as resurrection approaches
                pulse_size = TILE_SIZE * (0.3 + 0.7 * progress + 0.2 * math.sin(current_time / 100))
                
                # Create a surface with transparency for the glow
                glow_surface = pygame.Surface((pulse_size * 2, pulse_size * 2), pygame.SRCALPHA)
                
                # Color transitions from dark purple to bright purple based on progress
                alpha = int(40 + 100 * progress)
                glow_color = (100 + int(50 * progress), 0, 180 + int(75 * progress), alpha)
                pygame.draw.circle(glow_surface, glow_color, (pulse_size, pulse_size), pulse_size)
                
                # Blit the glow at the enemy position
                surface.blit(glow_surface, (self.rect.centerx - pulse_size, self.rect.centery - pulse_size))
                
                # Add particle effects as resurrection gets closer
                if random.random() < 0.1 * progress:
                    for _ in range(int(3 * progress)):
                        # Calculate random position around the blood puddle
                        angle = random.uniform(0, math.pi * 2)
                        dist = random.uniform(0, TILE_SIZE * 0.5)
                        spark_x = self.rect.centerx + dist * math.cos(angle)
                        spark_y = self.rect.centery + dist * math.sin(angle)
                        spark_size = random.randint(2, 4)
                        
                        # Draw the spark with a purple color
                        spark_color = (180 + int(75 * progress), 50, 255)
                        pygame.draw.circle(surface, spark_color, (int(spark_x), int(spark_y)), spark_size)
            
            # If just resurrected
            if current_time >= self.resurrection_time and current_time <= self.resurrection_time + 200:
                # Create visual effect for resurrection
                for _ in range(10):  # Increased particles for more dramatic effect
                    offset_x = random.randint(-TILE_SIZE//2, TILE_SIZE//2)
                    offset_y = random.randint(-TILE_SIZE//2, TILE_SIZE//2)
                    size = random.randint(5, 15)
                    pygame.draw.circle(surface, (150, 0, 255), 
                                      (self.rect.centerx + offset_x, self.rect.centery + offset_y), size)
                    
                # Add a larger pulse ring effect
                for radius in range(10, TILE_SIZE, 5):
                    alpha = max(10, 200 - radius * 2)
                    ring_surface = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
                    pygame.draw.circle(ring_surface, (150, 0, 255, alpha), (radius, radius), radius, 2)
                    surface.blit(ring_surface, 
                                 (self.rect.centerx - radius, self.rect.centery - radius))
            
            # Draw the blood puddle image
            surface.blit(self.image, self.rect)
            
        else:
            # Draw trailing effect for level 1 and 2 bosses (BEFORE drawing the main sprite)
            if self.trail_enabled and self.position_history:
                # Draw position history for trailing effect
                for i, (x, y, img) in enumerate(reversed(self.position_history)):
                    # Calculate alpha (transparency) based on position in history
                    # Make the oldest ones more transparent
                    alpha = max(20, 150 - (i * 15))
                    
                    # Create a copy of the sprite with alpha transparency
                    ghost_img = img.copy()
                    # Set the alpha of the entire surface
                    ghost_img.set_alpha(alpha)
                    
                    # Draw the ghost sprite at the historical position
                    surface.blit(ghost_img, (x - self.visual_offset_x, y - self.visual_offset_y))
            
            # Calculate position with visual offset
            draw_x = self.rect.x - self.visual_offset_x
            draw_y = self.rect.y - self.visual_offset_y
            
            # Draw boss character (drawn AFTER the trail)
            surface.blit(self.image, (draw_x, draw_y))
            
            # Debug: Draw hitboxes to visualize them if in debug mode
            if DEBUG_MODE:
                # Draw movement hitbox in yellow
                pygame.draw.rect(surface, (255, 255, 0), self.rect, 2)
                # Draw damage hitbox in red - draw it at the proper visual position
                pygame.draw.rect(surface, (255, 0, 0), self.damage_hitbox, 2)
            
            # Draw defensive mode effect for level 4 boss
            if self.level == 4 and self.defensive_mode:
                current_time = pygame.time.get_ticks()
                
                # Create a pulsing shield effect
                shield_size = self.image.get_width() * 1.2  # Slightly larger than boss
                shield_pulse = 0.1 * math.sin(current_time / 100)  # Subtle pulsing effect
                shield_radius = int(shield_size / 2 * (1 + shield_pulse))
                
                # Create a transparent surface for the shield
                shield_surface = pygame.Surface((shield_radius * 2, shield_radius * 2), pygame.SRCALPHA)
                
                # Blue shield color with pulsing opacity
                shield_alpha = int(100 + 50 * math.sin(current_time / 150))
                
                # Change shield color if damage was just reflected - make it brighter
                if hasattr(self, 'reflected_damage') and self.reflected_damage > 0:
                    shield_color = (50, 150, 255, shield_alpha + 50)  # Brighter blue shield
                    # Also add an extra outer ring to show reflection
                    reflection_radius = shield_radius + 10
                    pygame.draw.circle(shield_surface, (255, 255, 255, shield_alpha // 2), 
                                      (shield_radius, shield_radius), reflection_radius, 3)
                else:
                    shield_color = (0, 128, 255, shield_alpha)  # Regular blue shield
                
                # Draw shield
                center = (shield_radius, shield_radius)
                pygame.draw.circle(shield_surface, shield_color, center, shield_radius, 5)  # Outline shield
                
                # Draw energy lines within the shield
                for i in range(8):  # 8 energy lines
                    angle = i * math.pi / 4 + current_time / 500  # Rotate over time
                    start_x = center[0] + math.cos(angle) * (shield_radius * 0.3)
                    start_y = center[1] + math.sin(angle) * (shield_radius * 0.3)
                    end_x = center[0] + math.cos(angle) * (shield_radius * 0.9)
                    end_y = center[1] + math.sin(angle) * (shield_radius * 0.9)
                    
                    line_color = (100, 200, 255, shield_alpha)
                    pygame.draw.line(shield_surface, line_color, (start_x, start_y), (end_x, end_y), 2)
                
                # Draw energy particles
                for _ in range(5):  # Add 5 particles
                    angle = random.uniform(0, math.pi * 2)
                    dist = random.uniform(shield_radius * 0.5, shield_radius * 0.9)
                    particle_x = center[0] + math.cos(angle) * dist
                    particle_y = center[1] + math.sin(angle) * dist
                    particle_size = random.randint(2, 4)
                    
                    particle_color = (150, 220, 255, 200)
                    pygame.draw.circle(shield_surface, particle_color, 
                                      (int(particle_x), int(particle_y)), particle_size)
                
                # Position and draw the shield
                shield_x = draw_x + self.image.get_width()//2 - shield_radius
                shield_y = draw_y + self.image.get_height()//2 - shield_radius
                surface.blit(shield_surface, (shield_x, shield_y))
            
            # Draw shield mode effect for level 7 boss (based on level 4)
            if self.level == 7 and self.defensive_mode:
                current_time = pygame.time.get_ticks()
                
                # Create an expanding shield effect (grows to 300% of original size instead of 200%)
                base_shield_size = self.image.get_width() * 1.2  # Base size (same as level 4)
                expansion_factor = 1.0 + (self.shield_growth * 2.0)  # Grows from 1x to 3x (300% growth)
                shield_pulse = 0.1 * math.sin(current_time / 100)  # Subtle pulsing effect
                shield_radius = int(base_shield_size / 2 * expansion_factor * (1 + shield_pulse))
                
                # Store the current shield radius for collision detection
                self.shield_radius = shield_radius
                
                # Create a transparent surface for the shield
                shield_surface = pygame.Surface((shield_radius * 2, shield_radius * 2), pygame.SRCALPHA)
                
                # Purple shield color with pulsing opacity (different from level 4's blue)
                shield_alpha = int(100 + 50 * math.sin(current_time / 150))
                
                # Change shield color if damage was just reflected - make it brighter
                if hasattr(self, 'reflected_damage') and self.reflected_damage > 0:
                    shield_color = (150, 50, 255, shield_alpha + 50)  # Brighter purple shield
                    # Also add an extra outer ring to show reflection
                    reflection_radius = shield_radius + 10
                    pygame.draw.circle(shield_surface, (255, 255, 255, shield_alpha // 2), 
                                      (shield_radius, shield_radius), reflection_radius, 3)
                else:
                    shield_color = (128, 0, 255, shield_alpha)  # Regular purple shield
                
                # Draw shield
                center = (shield_radius, shield_radius)
                pygame.draw.circle(shield_surface, shield_color, center, shield_radius, 5)  # Outline shield
                
                # Draw energy lines within the shield
                for i in range(8):  # 8 energy lines
                    angle = i * math.pi / 4 + current_time / 500  # Rotate over time
                    start_x = center[0] + math.cos(angle) * (shield_radius * 0.3)
                    start_y = center[1] + math.sin(angle) * (shield_radius * 0.3)
                    end_x = center[0] + math.cos(angle) * (shield_radius * 0.9)
                    end_y = center[1] + math.sin(angle) * (shield_radius * 0.9)
                    
                    line_color = (200, 100, 255, shield_alpha)
                    pygame.draw.line(shield_surface, line_color, (start_x, start_y), (end_x, end_y), 2)
                
                # Draw energy particles
                for _ in range(5):  # Add 5 particles
                    angle = random.uniform(0, math.pi * 2)
                    dist = random.uniform(shield_radius * 0.5, shield_radius * 0.9)
                    particle_x = center[0] + math.cos(angle) * dist
                    particle_y = center[1] + math.sin(angle) * dist
                    particle_size = random.randint(2, 4)
                    
                    particle_color = (220, 150, 255, 200)
                    pygame.draw.circle(shield_surface, particle_color, 
                                      (int(particle_x), int(particle_y)), particle_size)
                
                # Position and draw the shield
                shield_x = draw_x + self.image.get_width()//2 - shield_radius
                shield_y = draw_y + self.image.get_height()//2 - shield_radius
                surface.blit(shield_surface, (shield_x, shield_y))
            
            # Draw projectiles for level 2, 5, 6 and 8 bosses
            if self.level in [2, 5, 6, 8] and self.projectiles:
                for projectile in self.projectiles:
                    projectile.draw(surface)
                    
            # Draw projectiles for level 7 boss
            if self.level == 7 and self.projectiles:
                for projectile in self.projectiles:
                    projectile.draw(surface)
            
            # Draw death ray for level 7 boss
            if self.level == 7 and self.has_death_ray and self.death_ray:
                self.death_ray.draw(surface)
        
        # Draw eggs for Boss 9
        if self.level == 9 and self.eggs:
            for egg in self.eggs:
                egg.draw(surface)
        
        # Draw rope for level 4 boss
        if self.level == 4 and self.is_shooting_rope and self.rope_end_pos:
            current_time = pygame.time.get_ticks()
            
            # Get rope start position (boss center)
            rope_start = (self.rect.centerx, self.rect.centery)
            rope_end = self.rope_end_pos
            
            # Calculate rope parameters
            rope_length = math.sqrt((rope_end[0] - rope_start[0])**2 + (rope_end[1] - rope_start[1])**2)
            segments = max(3, int(rope_length / 10))  # One segment every 10 pixels, minimum 3
            
            # Create a semi-transparent surface for the rope
            width = abs(rope_start[0] - rope_end[0]) + 10
            height = abs(rope_start[1] - rope_end[1]) + 10
            rope_surface = pygame.Surface((width, height), pygame.SRCALPHA)
            
            # Determine surface position and local coordinates
            rope_x = min(rope_start[0], rope_end[0]) - 5
            rope_y = min(rope_start[1], rope_end[1]) - 5
            
            # Calculate local coordinates within rope surface
            local_start = (
                rope_start[0] - rope_x,
                rope_start[1] - rope_y
            )
            local_end = (
                rope_end[0] - rope_x,
                rope_end[1] - rope_y
            )
            
            # Draw segments with slight variation for realistic rope effect
            prev_point = local_start
            
            # Use pulsing animation for the rope
            pulse = math.sin(current_time / 100) * 2
            
            # Draw rope with bright to dark blue gradient
            for i in range(1, segments + 1):
                # Calculate straight segment end point
                t = i / segments
                straight_x = local_start[0] + t * (local_end[0] - local_start[0])
                straight_y = local_start[1] + t * (local_end[1] - local_start[1])
                
                # Add slight variation perpendicular to rope direction
                if i < segments:  # Don't modify the end point
                    # Calculate perpendicular vector
                    dx = local_end[0] - local_start[0]
                    dy = local_end[1] - local_start[1]
                    length = math.sqrt(dx*dx + dy*dy)
                    if length > 0:
                        # Normalize and rotate 90 degrees
                        perpendicular_x = -dy / length
                        perpendicular_y = dx / length
                        
                        # Add variation based on segment and time
                        variation = math.sin(i + current_time / 200) * pulse
                        straight_x += perpendicular_x * variation
                        straight_y += perpendicular_y * variation
                
                # Calculate color (gradient from blue to dark blue)
                blue = 255 - int(180 * t)  # Fades from 255 to 75
                segment_color = (50, 150, blue, 255)
                
                # Draw rope segment
                pygame.draw.line(rope_surface, segment_color, prev_point, (straight_x, straight_y), 4)
                prev_point = (straight_x, straight_y)
            
            # Draw energy particles along the rope for visual effect
            for i in range(segments):
                if random.random() < 0.3:  # 30% chance per segment
                    t = (i + random.random()) / segments
                    particle_x = local_start[0] + t * (local_end[0] - local_start[0])
                    particle_y = local_start[1] + t * (local_end[1] - local_start[1])
                    
                    # Calculate color (brighter blue)
                    particle_color = (100, 200, 255, 200)
                    
                    # Draw particle
                    pygame.draw.circle(rope_surface, particle_color, 
                                    (int(particle_x), int(particle_y)), random.randint(2, 4))
            
            # Draw rope end with a hook/claw effect if it has reached the player
            if self.rope_reached_player:
                # Draw a glowing circle at the end
                glow_colors = [
                    (200, 220, 255, 50),  # Outer glow
                    (150, 200, 255, 100),  # Middle glow
                    (100, 180, 255, 200)   # Inner glow
                ]
                
                for i, color in enumerate(glow_colors):
                    radius = 7 - i*2
                    pygame.draw.circle(rope_surface, color, local_end, radius)
            
            # Blit the rope surface onto the main surface
            surface.blit(rope_surface, (rope_x, rope_y))
        
        # Draw shield mode effect for level 7 boss (based on level 4)
        if self.level == 7 and self.defensive_mode:
            current_time = pygame.time.get_ticks()
            
            # Create an expanding shield effect (grows to 300% of original size instead of 200%)
            base_shield_size = self.image.get_width() * 1.2  # Base size (same as level 4)
            expansion_factor = 1.0 + (self.shield_growth * 2.0)  # Grows from 1x to 3x (300% growth)
            shield_pulse = 0.1 * math.sin(current_time / 100)  # Subtle pulsing effect
            shield_radius = int(base_shield_size / 2 * expansion_factor * (1 + shield_pulse))
            
            # Store the current shield radius for collision detection
            self.shield_radius = shield_radius
            
            # Create a transparent surface for the shield
            shield_surface = pygame.Surface((shield_radius * 2, shield_radius * 2), pygame.SRCALPHA)
            
            # Purple shield color with pulsing opacity (different from level 4's blue)
            shield_alpha = int(100 + 50 * math.sin(current_time / 150))
            
            # Change shield color if damage was just reflected - make it brighter
            if hasattr(self, 'reflected_damage') and self.reflected_damage > 0:
                shield_color = (150, 50, 255, shield_alpha + 50)  # Brighter purple shield
                # Also add an extra outer ring to show reflection
                reflection_radius = shield_radius + 10
                pygame.draw.circle(shield_surface, (255, 255, 255, shield_alpha // 2), 
                                  (shield_radius, shield_radius), reflection_radius, 3)
            else:
                shield_color = (128, 0, 255, shield_alpha)  # Regular purple shield
            
            # Draw shield
            center = (shield_radius, shield_radius)
            pygame.draw.circle(shield_surface, shield_color, center, shield_radius, 5)  # Outline shield
            
            # Draw energy lines within the shield
            for i in range(8):  # 8 energy lines
                angle = i * math.pi / 4 + current_time / 500  # Rotate over time
                start_x = center[0] + math.cos(angle) * (shield_radius * 0.3)
                start_y = center[1] + math.sin(angle) * (shield_radius * 0.3)
                end_x = center[0] + math.cos(angle) * (shield_radius * 0.9)
                end_y = center[1] + math.sin(angle) * (shield_radius * 0.9)
                
                line_color = (200, 100, 255, shield_alpha)
                pygame.draw.line(shield_surface, line_color, (start_x, start_y), (end_x, end_y), 2)
            
            # Draw energy particles
            for _ in range(5):  # Add 5 particles
                angle = random.uniform(0, math.pi * 2)
                dist = random.uniform(shield_radius * 0.5, shield_radius * 0.9)
                particle_x = center[0] + math.cos(angle) * dist
                particle_y = center[1] + math.sin(angle) * dist
                particle_size = random.randint(2, 4)
                
                particle_color = (220, 150, 255, 200)
                pygame.draw.circle(shield_surface, particle_color, 
                                  (int(particle_x), int(particle_y)), particle_size)
            
            # Position and draw the shield
            shield_x = draw_x + self.image.get_width()//2 - shield_radius
            shield_y = draw_y + self.image.get_height()//2 - shield_radius
            surface.blit(shield_surface, (shield_x, shield_y))
        
        # Draw projectiles for level 2, 5, 6 and 8 bosses
        if self.level in [2, 5, 6, 8] and self.projectiles:
            for projectile in self.projectiles:
                projectile.draw(surface)
                
        # Draw projectiles for level 7 boss
        if self.level == 7 and self.projectiles:
            for projectile in self.projectiles:
                projectile.draw(surface)
    
    def cast_projectiles(self, player):
        """Create projectiles that become stationary after a delay for Boss 5 and 8"""
        if self.level != 5 and self.level != 8:
            return
            
        # Different behavior for Boss 8
        if self.level == 8:
            # Clear any existing floor projectiles that haven't been activated yet
            self.floor_projectiles = []
            
            # Select random half of the room (top, bottom, left, or right)
            half_type = random.choice(['top', 'bottom', 'left', 'right'])
            
            # Calculate room dimensions in tiles
            room_width_tiles = ROOM_WIDTH
            room_height_tiles = ROOM_HEIGHT
            
            # Determine which tiles to cover based on the selected half
            start_x, end_x = 0, room_width_tiles
            start_y, end_y = 0, room_height_tiles
            
            if half_type == 'top':
                end_y = room_height_tiles // 2
            elif half_type == 'bottom':
                start_y = room_height_tiles // 2
            elif half_type == 'left':
                end_x = room_width_tiles // 2
            elif half_type == 'right':
                start_x = room_width_tiles // 2
            
            print(f"Boss 8 casting on {half_type} half of room: x({start_x}-{end_x}), y({start_y}-{end_y})")
            
            # Place projectiles on each tile in the selected half
            spacing = 2  # Place a projectile every 2 tiles to avoid overcrowding
            
            for y in range(start_y, end_y, spacing):
                for x in range(start_x, end_x, spacing):
                    # Convert tile coordinates to pixel coordinates
                    pixel_x = x * TILE_SIZE + TILE_SIZE // 2
                    pixel_y = y * TILE_SIZE + TILE_SIZE // 2
                    
                    # Create the projectile (inactive until casting completes)
                    projectile = BossProjectile(
                        pixel_x,
                        pixel_y,
                        (0, 0),  # No movement
                        0,  # No speed
                        self.damage * 0.15,  # Increased damage to 15% of boss damage
                        color=(255, 100, 0),  # Orange-red for fire
                        become_stationary=True,
                        stationary_time=0,  # Already stationary
                        boss_level=self.level  # For animation - same as orbiting projectiles
                    )
                    
                    # Set to inactive until casting completes (creation_time=0 disables collision damage)
                    projectile.is_stationary = True
                    
                    # Set the projectile's lifetime
                    projectile.stationary_duration = self.stationary_projectile_duration
                    
                    # Add to our list of floor projectiles to be activated after casting
                    self.floor_projectiles.append(projectile)
                    
                    # Add to sprite group for rendering
                    self.projectiles.add(projectile)
            
            print(f"Boss 8 placed {len(self.floor_projectiles)} floor projectiles")
            return
        
        # Calculate the distance to the player
        dx = player.rect.centerx - self.rect.centerx
        dy = player.rect.centery - self.rect.centery
        distance = math.sqrt(dx * dx + dy * dy)
        
        # Check if health is below 50% and player is within 10 tiles range
        health_percentage = self.health / self.enemy_data['health']
        is_close = distance <= TILE_SIZE * 10
        is_low_health = health_percentage <= 0.5
        
        # Determine number of projectiles to cast
        num_projectiles = 8 if (is_low_health and is_close) else 4
        
        # Log the enhanced attack if applicable
        if num_projectiles > 4:
            print(f"Boss 5 is below 50% health and player is in close range - firing {num_projectiles} projectiles!")
        
        # Original behavior for Boss 5
        # Create projectiles in random directions
        for i in range(num_projectiles):
            # Generate random angle and distance
            angle = random.uniform(0, math.pi * 2)
            distance = random.uniform(TILE_SIZE * 2, TILE_SIZE * 4)
            
            # Calculate direction vector
            dx = math.cos(angle)
            dy = math.sin(angle)
            
            # All cast projectiles should be green
            color = (0, 255, 0)  # Green
            
            # Create projectile at boss position that will travel and then become stationary
            projectile = BossProjectile(
                self.rect.centerx,
                self.rect.centery,
                (dx, dy),
                1.2,  # Slightly slower than regular projectiles
                self.damage * 0.03,  # Very low damage like orbiting projectiles
                color=color,
                become_stationary=True,
                stationary_time=self.casting_mode_duration,  # Become stationary after cast completes
                boss_level=self.level  # Pass the boss level for animated projectiles
            )
            
            # Set the stationary duration to match the cooldown
            projectile.stationary_duration = self.stationary_projectile_duration
            
            # Add to projectile group
            self.projectiles.add(projectile)
            
        print(f"Boss {self.level} cast {num_projectiles} projectiles that will become stationary")

    def summon_homing_projectiles(self, player):
        """Summon homing projectiles that track the player (for level 6 boss)"""
        if self.level != 6:
            return

        print("Boss 6 is summoning homing projectiles!")
        
        # Calculate room dimensions
        room_width = ROOM_WIDTH * TILE_SIZE
        room_height = ROOM_HEIGHT * TILE_SIZE
        
        # Create 5 projectiles at random locations
        for _ in range(5):
            # Generate a random position within the room, avoiding being too close to walls
            margin = TILE_SIZE * 2  # Keep projectiles away from walls
            x = random.randint(margin, room_width - margin)
            y = random.randint(margin, room_height - margin)
            
            # Calculate direction to player
            dx = player.rect.centerx - x
            dy = player.rect.centery - y
            distance = math.sqrt(dx * dx + dy * dy)
            
            # Normalize direction
            if distance > 0:
                dx = dx / distance
                dy = dy / distance
            else:
                dx, dy = 0, -1
            
            # Create the projectile with a purple color to match the boss's shield
            projectile = BossProjectile(
                x, y, 
                (dx, dy), 
                speed=1.5,  # Moderate speed
                damage=self.damage * 0.75,  # 75% of boss's damage
                color=(160, 32, 240),  # Purple color to match the shield
                is_homing=True,  # Make it home in on the player
                boss_level=self.level  # Pass the boss level for animated projectiles
            )
            
            # Configure homing behavior
            projectile.player_target = player
            projectile.homing_strength = 0.04  # More aggressive turning than normal
            projectile.max_homing_time = 8000  # Home for 8 seconds
            
            # Enhance the trail effect for better visibility
            projectile.trail_enabled = True
            projectile.max_trail_length = 12  # Longer trail for dramatic effect
            projectile.trail_update_rate = 1  # Update every frame for smoother trail
            
            # Increase projectile lifetime
            projectile.max_distance = TILE_SIZE * 20  # Longer lifetime
            
            # Add to projectile group
            self.projectiles.add(projectile)
        
        # Play sound effect for summoning
        self.sound_manager.play_sound("effects/boss_cast")

    def attack(self, player):
        """Override the attack method to avoid setting is_jumping to True for bosses"""
        if self.can_attack():
            self.last_attack_time = pygame.time.get_ticks()
            self.current_state = 'attack'
            self.frame = 0  # Reset animation frame
            return player.take_damage(self.damage)
        return False
        
    def move_towards_player(self, player):
        """Move towards player using pathfinding"""
        # Special cases for specific bosses
        if self.level == 9 and self.stealth_mode:
            self._move_in_stealth_mode()
            return
            
        if self.level == 6 and self.is_teleporting:
            self.velocity_x = 0
            self.velocity_y = 0
            return
        
        # Use the base Enemy class's movement logic
        super().move_towards_player(player)
        
    def load_texture(self, image_path):
        """Load boss texture with proper scaling"""
        max_boss_size = (int(TILE_SIZE * 2.2), int(TILE_SIZE * 2.2))
        
        try:
            boss_image = self.asset_manager.load_image(image_path, max_boss_size)
            
            if boss_image:
                # Load animation frames for boss 9
                if self.level == 9:
                    # Store the base image
                    self.base_image = boss_image
                    
                    # Load animation frames
                    base_path = os.path.dirname(image_path)
                    frame1_path = os.path.join(base_path, "boss_9_1.png")
                    frame2_path = os.path.join(base_path, "boss_9_2.png")
                    frame3_path = os.path.join(base_path, "boss_9_3.png")
                    
                    # Check if animation frames exist and load them
                    if all(os.path.exists(path) for path in [frame1_path, frame2_path, frame3_path]):
                        # Load and scale frames to match the base image size
                        frame1 = self.asset_manager.load_image(frame1_path, boss_image.get_size())
                        frame2 = self.asset_manager.load_image(frame2_path, boss_image.get_size())
                        frame3 = self.asset_manager.load_image(frame3_path, boss_image.get_size())
                        
                        # Store animation frames
                        self.boss9_animation_frames = [frame1, frame2, frame3]
                        print(f"Loaded {len(self.boss9_animation_frames)} animation frames for boss 9")
                
                return boss_image
        except Exception as e:
            print(f"Failed to load boss texture: {e}")
        
        # Create a fallback texture instead of using create_enemy_texture
        size = (int(TILE_SIZE * 2.2), int(TILE_SIZE * 2.2))
        fallback = pygame.Surface(size, pygame.SRCALPHA)
        fallback.fill((200, 0, 0, 220))  # Red with some transparency
        
        # Add text with boss level
        font = pygame.font.Font(None, 36)
        text = font.render(f"BOSS {self.level}", True, (255, 255, 255))
        text_rect = text.get_rect(center=(size[0]//2, size[1]//2))
        fallback.blit(text, text_rect)
        
        return fallback

    def _set_random_stealth_target(self, player):
        """Set a random movement target for the boss during stealth mode"""
        # Get the current room size from the level instance
        room_width = TILE_SIZE * 16  # Default room width in tiles
        room_height = TILE_SIZE * 9  # Default room height in tiles
        
        if hasattr(self, 'level_instance') and self.level_instance:
            if hasattr(self.level_instance, 'current_room') and self.level_instance.current_room:
                # Get actual room dimensions if available
                room = self.level_instance.current_room
                if hasattr(room, 'width') and hasattr(room, 'height'):
                    room_width = room.width * TILE_SIZE
                    room_height = room.height * TILE_SIZE
                    
        # Calculate room boundaries with padding
        padding = TILE_SIZE * 2  # Keep 2 tiles away from the edges
        min_x = padding
        max_x = room_width - padding
        min_y = padding
        max_y = room_height - padding
        
        # Choose a random point in the room that's NOT too close to the player
        while True:
            # Generate random positions
            target_x = random.randint(min_x, max_x)
            target_y = random.randint(min_y, max_y)
            
            # Calculate distance to player
            dx = player.rect.centerx - target_x
            dy = player.rect.centery - target_y
            distance = math.sqrt(dx * dx + dy * dy)
            
            # Ensure target is not too close to player (at least 4 tiles away)
            if distance >= TILE_SIZE * 4:
                self.stealth_target_x = target_x
                self.stealth_target_y = target_y
                # Clear any existing path
                self.path = []
                break

    def _move_in_stealth_mode(self):
        """Special movement function for boss 9 in stealth mode"""
        # Calculate direction to the random target
        dx = self.stealth_target_x - self.rect.centerx
        dy = self.stealth_target_y - self.rect.centery
        distance = math.sqrt(dx * dx + dy * dy)
        
        # If we've reached the target (or close enough), stop moving
        if distance < self.speed:
            self.velocity_x = 0
            self.velocity_y = 0
            return
            
        # Move towards the random target - using 8-directional movement for more erratic behavior
        if distance > 0:
            # Normalize direction
            dx = dx / distance
            dy = dy / distance
            
            # Set velocity with some randomness for erratic movement
            rand_factor = 0.3
            dx_rand = dx + random.uniform(-rand_factor, rand_factor)
            dy_rand = dy + random.uniform(-rand_factor, rand_factor)
            
            # Normalize again after adding randomness
            length = math.sqrt(dx_rand * dx_rand + dy_rand * dy_rand)
            if length > 0:
                dx_rand = dx_rand / length
                dy_rand = dy_rand / length
            
            # Set velocity with the randomized direction
            self.velocity_x = dx_rand * self.speed
            self.velocity_y = dy_rand * self.speed
            
            # Update facing direction
            if abs(dx) > abs(dy):
                self.facing = 'right' if dx > 0 else 'left'
            else:
                self.facing = 'down' if dy > 0 else 'up'

    def _lay_egg(self):
        """Lay an egg during Boss 9 stealth mode"""
        if not self.egg_image:
            print("Cannot lay egg: egg_image is not loaded")
            return
            
        # Verify level_instance is available
        if not self.level_instance:
            print("Cannot lay egg: level_instance is None")
            return
            
        # Get the current room from level_instance
        if not hasattr(self.level_instance, 'current_room_coords') or not hasattr(self.level_instance, 'rooms'):
            print("Cannot lay egg: level_instance missing required attributes")
            return
            
        current_room_coords = self.level_instance.current_room_coords
        if current_room_coords not in self.level_instance.rooms:
            print("Cannot lay egg: current_room_coords not in rooms dictionary")
            return
            
        room = self.level_instance.rooms[current_room_coords]
        
        # Convert boss position to tile coordinates
        tile_x = int(self.rect.centerx // TILE_SIZE)
        tile_y = int(self.rect.centery // TILE_SIZE)
        
        # Check if current tile is a floor tile
        if room.tiles[tile_y][tile_x] != 0:  # Not a floor tile
            # Search for nearest floor tile in a 3x3 grid around the boss
            found_valid = False
            for offset_y in range(-1, 2):
                for offset_x in range(-1, 2):
                    test_x = tile_x + offset_x
                    test_y = tile_y + offset_y
                    
                    # Check bounds
                    if 0 <= test_x < room.width and 0 <= test_y < room.height:
                        if room.tiles[test_y][test_x] == 0:  # Found a floor tile
                            tile_x = test_x
                            tile_y = test_y
                            found_valid = True
                            break
                if found_valid:
                    break
            
            if not found_valid:
                print("Cannot lay egg: no valid floor tile found nearby")
                return
        
        # Convert back to pixel coordinates and add small random offset
        egg_x = tile_x * TILE_SIZE + TILE_SIZE // 2 + random.randint(-5, 5)
        egg_y = tile_y * TILE_SIZE + TILE_SIZE // 2 + random.randint(-5, 5)
        
        # Create a new egg object at the position
        egg = BossEgg(
            egg_x,
            egg_y,
            self.egg_image,
            self.level_instance  # Pass level_instance to allow spawning
        )
        
        # Add to egg sprite group
        self.eggs.add(egg)
        print(f"Boss 9 laid an egg at position ({egg_x}, {egg_y}) on floor tile ({tile_x}, {tile_y})")
        
        # Debug: Print the current room from the level_instance
        if hasattr(self.level_instance, 'current_room'):
            print(f"Current room exists: {self.level_instance.current_room}")
        else:
            print("WARNING: level_instance has no current_room attribute")

    def take_damage(self, amount):
        """Override the parent take_damage method to handle boss-specific behavior"""
        # Set the has_spotted_player flag to True when boss takes damage
        self.has_spotted_player = True
        
        # Clear any lingering reflected damage to prevent bugs
        if self.level == 4 or self.level == 7:
            # Always reset reflection when taking damage
            if not self.defensive_mode:
                self.reflected_damage = 0  # Ensure no reflection when not in defensive mode
        
        # Level 3 boss damage immunity during defensive mode (when minions are alive)
        if self.level == 3 and self.defensive_mode:
            # Don't take damage while minions are alive, but don't reflect it either
            print(f"Level 3 boss is in defensive mode - immune to damage!")
            return False
        
        # Level 4 boss damage reflection during defensive mode
        if self.level == 4 and self.defensive_mode:
            # We need to reflect damage, but since we don't have direct access to the player,
            # we'll store the reflected damage amount so the game can apply it later
            self.reflected_damage = amount * 0.5  # Reflect 50% of damage
            print(f"Level 4 boss reflecting {self.reflected_damage} damage!")
            
            # Don't take damage during defensive mode
            return False
            
        # Level 7 boss damage reflection during defensive mode (same as level 4)
        if self.level == 7 and self.defensive_mode:
            # Store the reflected damage amount for the game to apply later
            self.reflected_damage = amount * 0.5  # Reflect 50% of damage
            print(f"Level 7 boss reflecting {self.reflected_damage} damage!")
            
            # Don't take damage during defensive mode
            return False
            
        # Call the parent method to handle the actual damage
        return super().take_damage(amount)

class PoisonTrail(pygame.sprite.Sprite):
    def __init__(self, x, y, size, damage, creator=None):
        super().__init__()
        self.asset_manager = get_asset_manager()
        self.creator = creator  # Store reference to the boss that created this trail
        
        # Create a larger surface to accommodate the glow effect
        glow_size = int(size * 2)  # Larger surface for better glow distribution
        self.image = pygame.Surface((glow_size, glow_size), pygame.SRCALPHA)
        
        # Try to load a random blood puddle texture first
        blood_texture = None
        try:
            blood_dir = os.path.join(TILE_SPRITES_PATH, "blood")
            if os.path.exists(blood_dir):
                blood_files = glob.glob(os.path.join(blood_dir, "*.png"))
                if blood_files:
                    selected_blood = random.choice(blood_files)
                    blood_texture = self.asset_manager.load_image(
                        selected_blood, scale=(size, size)  # Smaller scale for the base texture
                    )
        except Exception as e:
            print(f"Failed to load blood puddle texture for poison trail: {e}")
            blood_texture = None
            
        center_point = (glow_size // 2, glow_size // 2)
            
        if blood_texture:
            # Position the blood texture at the center of our larger surface
            blood_rect = blood_texture.get_rect(center=center_point)
            
            # Create a green overlay to tint the blood texture
            green_overlay = pygame.Surface(blood_texture.get_size(), pygame.SRCALPHA)
            green_overlay.fill((0, 255, 0, 170))  # Semi-transparent green
            
            # Apply the green tint to the blood texture
            tinted_blood = blood_texture.copy()
            tinted_blood.blit(green_overlay, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
            
            # Draw the tinted blood texture on our main surface
            self.image.blit(tinted_blood, blood_rect)
            
            # Create a separate surface for the glow effect
            glow_overlay = pygame.Surface((glow_size, glow_size), pygame.SRCALPHA)
            
            # Draw a smooth gradient glow using multiple circles with decreasing opacity
            for i in range(12):  # More steps for a smoother gradient
                glow_radius = (size // 2) + i * 4  # Gradually increasing radius
                # Decreasing alpha as we move outward
                glow_alpha = max(5, 50 - i * 5)  # Start at 50 alpha, decrease by 5 each step
                # Use softer green glow for poison
                glow_col = (40, 180, 40, glow_alpha)
                pygame.draw.circle(glow_overlay, glow_col, center_point, glow_radius)
            
            # Apply the glow overlay
            self.image.blit(glow_overlay, (0, 0), special_flags=pygame.BLEND_RGBA_ADD)
            
            # Add some toxic bubble details
            for _ in range(6):
                angle = random.uniform(0, math.pi * 2)
                distance = random.uniform(0, size // 4)
                
                dot_x = center_point[0] + int(math.cos(angle) * distance)
                dot_y = center_point[1] + int(math.sin(angle) * distance)
                
                dot_size = random.randint(1, 3)
                bubble_color = (220, 255, 150, 230)  # Yellowish-green for toxic effect
                pygame.draw.circle(self.image, bubble_color, (dot_x, dot_y), dot_size)
        else:
            # Fallback to a manually drawn poison puddle if no texture
            
            # Create a separate surface for the glow effect
            glow_overlay = pygame.Surface((glow_size, glow_size), pygame.SRCALPHA)
            
            # Draw a smooth gradient glow using multiple circles with decreasing opacity
            for i in range(12):  # More steps for a smoother gradient
                glow_radius = (size // 2) + i * 4  # Gradually increasing radius
                # Decreasing alpha as we move outward
                glow_alpha = max(5, 50 - i * 5)  # Start at 50 alpha, decrease by 5 each step
                # Use softer green glow for poison
                glow_col = (40, 180, 40, glow_alpha)
                pygame.draw.circle(glow_overlay, glow_col, center_point, glow_radius)
            
            # Apply the glow overlay
            self.image.blit(glow_overlay, (0, 0))
            
            # Main puddle colors - toxic green
            outer_color = (40, 150, 40, 190)  # Dark toxic green
            main_color = (80, 220, 80, 200)   # Medium toxic green
            inner_color = (150, 255, 150, 220)  # Light toxic green
            
            # Draw the base puddle shape as a circle
            pygame.draw.circle(self.image, outer_color, center_point, size // 2 - 2)
            
            # Draw a smaller inner puddle
            pygame.draw.circle(self.image, main_color, center_point, int(size * 0.4) - 1)
            
            # Draw the toxic center
            pygame.draw.circle(self.image, inner_color, center_point, int(size * 0.25))
            
            # Add some toxic bubble details
            for _ in range(6):
                angle = random.uniform(0, math.pi * 2)
                distance = random.uniform(0, size // 4)
                
                dot_x = center_point[0] + int(math.cos(angle) * distance)
                dot_y = center_point[1] + int(math.sin(angle) * distance)
                
                dot_size = random.randint(1, 3)
                bubble_color = (220, 255, 150, 230)  # Yellowish-green for toxic effect
                pygame.draw.circle(self.image, bubble_color, (dot_x, dot_y), dot_size)
        
        # Create a properly positioned rect
        self.rect = self.image.get_rect(center=(x, y))
        self.true_center = (x, y)  # Store the exact center for accurate positioning
        
        # Add pulsing glow effect
        self.damage = damage
        self.creation_time = pygame.time.get_ticks()
        self.duration = 12000  # 12 seconds lifetime (reduced from 15)
        self.slow_duration = 2000  # 2 seconds slow effect
        self.slow_amount = 0.5  # Reduce speed to 50%
        
        # Add damage cooldown
        self.last_damage_time = 0
        self.damage_cooldown = 1000  # 1 second between damage applications
        
        # Add pulse/glow effect
        self.pulse_time = random.uniform(0, math.pi * 2)  # Random start phase
        self.pulse_speed = 0.08  # Speed of pulsing
        self.base_image = self.image.copy()  # Store the original image for pulsing

    def update(self):
        # Check if the trail should disappear
        if pygame.time.get_ticks() - self.creation_time > self.duration:
            self.kill()
            
        # Update pulse effect
        self.pulse_time += self.pulse_speed
        if self.pulse_time > math.pi * 2:
            self.pulse_time -= math.pi * 2
            
        # Apply pulsing effect by creating a new image with pulsing glow
        pulse_factor = 0.15 * math.sin(self.pulse_time) + 1.0  # Value between 0.85 and 1.15
        
        # Apply the pulse by creating a slightly larger/smaller version of the image
        if hasattr(self, 'base_image'):
            current_size = self.base_image.get_width()
            new_size = int(current_size * pulse_factor)
            self.image = pygame.transform.smoothscale(self.base_image, (new_size, new_size))
            
            # Ensure the rect stays centered at the same position
            old_center = self.rect.center
            self.rect = self.image.get_rect(center=old_center)

    def check_collision(self, rect):
        # Don't collide with the boss that created this trail
        if hasattr(self, 'creator') and self.creator and self.creator.rect == rect:
            return False
        return self.rect.colliderect(rect)
        
    def can_damage(self):
        # Check if the cooldown has elapsed
        current_time = pygame.time.get_ticks()
        if current_time - self.last_damage_time >= self.damage_cooldown:
            self.last_damage_time = current_time
            return True
        return False

class CursedShield(pygame.sprite.Sprite):
    def __init__(self, x, y, size, damage):
        super().__init__()
        self.asset_manager = get_asset_manager()
        self.sound_manager = get_sound_manager()
        
        # Position and size properties
        self.x = x
        self.y = y
        self.size = size
        self.radius = size // 2
        
        # Damage properties
        self.damage = damage
        self.damage_cooldown = 500  # Damage player every 0.5 seconds
        self.last_damage_time = 0
        
        # Duration for the shield to remain active
        self.duration = 18000  # Changed from 8000 to 18000 (18 seconds)
        self.creation_time = pygame.time.get_ticks()
        
        # Create a surface for the shield
        self.image = pygame.Surface((size, size), pygame.SRCALPHA)
        
        # Visual properties
        self.pulse_timer = 0
        self.alpha = 200  # Start fairly visible
        self.fade_timer = 0
        
        # Create the hitbox
        self.rect = pygame.Rect(x - self.radius, y - self.radius, size, size)
        
        # Play sound when created
        self.sound_manager.play_sound("effects/boss_cast")
    
    def update(self):
        """Update the shield state"""
        current_time = pygame.time.get_ticks()
        elapsed_time = current_time - self.creation_time
        
        # Check if the shield should be destroyed
        if elapsed_time >= self.duration:
            self.kill()
            return
        
        # Visual updates - pulsing effect
        self.pulse_timer += 0.1
        pulse_factor = 0.1 * math.sin(self.pulse_timer)
        
        # Fade out as time passes
        remaining_time_pct = 1.0 - (elapsed_time / self.duration)
        self.alpha = int(180 * remaining_time_pct) + 20  # Fade from 200 to 20
    
    def check_collision(self, player_rect):
        """Check if the player is inside the shield area"""
        # Calculate distance between shield center and player center
        dx = player_rect.centerx - self.rect.centerx
        dy = player_rect.centery - self.rect.centery
        distance = math.sqrt(dx * dx + dy * dy)
        
        # If player is inside shield radius, they should take damage
        return distance < self.radius
    
    def can_damage(self):
        """Check if the cooldown has elapsed and the shield can damage again"""
        current_time = pygame.time.get_ticks()
        if current_time - self.last_damage_time >= self.damage_cooldown:
            self.last_damage_time = current_time
            return True
        return False
    
    def draw(self, surface):
        """Draw the shield with visual effects"""
        current_time = pygame.time.get_ticks()
        
        # Create a new surface for this frame with pulse effect
        pulse_surface = pygame.Surface((self.size, self.size), pygame.SRCALPHA)
        
        # Calculate pulse effect
        pulse_size = int(self.size * (1.0 + 0.1 * math.sin(current_time / 100)))
        shield_radius = pulse_size // 2
        
        # Center point
        center = (self.size // 2, self.size // 2)
        
        # Purple shield color with current alpha
        shield_color = (128, 0, 255, self.alpha)
        
        # Draw shield
        pygame.draw.circle(pulse_surface, shield_color, center, shield_radius, 5)  # Outline
        
        # Draw energy lines within the shield
        for i in range(8):
            angle = i * math.pi / 4 + current_time / 500  # Rotate over time
            start_x = center[0] + math.cos(angle) * (shield_radius * 0.3)
            start_y = center[1] + math.sin(angle) * (shield_radius * 0.3)
            end_x = center[0] + math.cos(angle) * (shield_radius * 0.9)
            end_y = center[1] + math.sin(angle) * (shield_radius * 0.9)
            
            line_color = (200, 100, 255, self.alpha)
            pygame.draw.line(pulse_surface, line_color, (start_x, start_y), (end_x, end_y), 2)
        
        # Add a partially filled circle for the inner shield
        inner_color = (128, 0, 255, self.alpha // 4)  # Very transparent
        pygame.draw.circle(pulse_surface, inner_color, center, int(shield_radius * 0.9))
        
        # Draw the shield at its position
        shield_x = self.rect.x
        shield_y = self.rect.y
        surface.blit(pulse_surface, (shield_x, shield_y))

class BossEgg(pygame.sprite.Sprite):
    """Eggs laid by Boss 9 during stealth mode"""
    def __init__(self, x, y, image, level_instance=None):
        super().__init__()
        self.image = image
        self.original_image = image
        self.rect = self.image.get_rect()
        self.rect.centerx = x
        self.rect.centery = y
        
        # Add a slight random offset to make egg placement look more natural
        self.rect.x += random.randint(-5, 5)
        self.rect.y += random.randint(-5, 5)
        
        self.creation_time = pygame.time.get_ticks()
        self.lifetime = 4000  # 4 seconds
        self.hatching = False
        self.hatching_time = 1000  # 1 second to hatch
        self.hatch_start_time = 0
        self.level_instance = level_instance
        
        # Hatching animation state
        self.pulse_size = 1.0
        self.pulse_direction = 0.1
        self.alpha = 255
        
    def update(self, current_time=None):
        """Update egg state, handle hatching animation and enemy spawning"""
        if current_time is None:
            current_time = pygame.time.get_ticks()
            
        # If egg is not yet hatching and lifetime is over, start hatching
        if not self.hatching and current_time - self.creation_time >= self.lifetime:
            self.hatching = True
            self.hatch_start_time = current_time
            print(f"Egg at position ({self.rect.centerx}, {self.rect.centery}) is hatching!")
            
        # If hatching, update the hatching animation
        if self.hatching:
            # Calculate how far we are in the hatching process (0.0 to 1.0)
            hatch_progress = min(1.0, (current_time - self.hatch_start_time) / self.hatching_time)
            
            # Pulse the egg as it hatches
            self.pulse_size += self.pulse_direction
            if self.pulse_size > 1.3 or self.pulse_size < 0.9:
                self.pulse_direction *= -1
                
            # Scale the image for pulsing effect
            w = int(self.original_image.get_width() * self.pulse_size)
            h = int(self.original_image.get_height() * self.pulse_size)
            self.image = pygame.transform.scale(self.original_image, (w, h))
            
            # Update the rectangle to keep the egg centered
            old_center = self.rect.center
            self.rect = self.image.get_rect()
            self.rect.center = old_center
            
            # Fade out as hatching completes
            self.alpha = int(255 * (1 - hatch_progress))
            
            # If hatching is complete, spawn an enemy and remove the egg
            if hatch_progress >= 1.0:
                print(f"Egg hatching complete at position ({self.rect.centerx}, {self.rect.centery})")
                try:
                    # Attempt to spawn the enemy
                    spawn_success = self.spawn_enemy()
                    if spawn_success:
                        print("Enemy successfully spawned from egg")
                    else:
                        print("ERROR: Failed to spawn enemy from egg")
                except Exception as e:
                    print(f"CRITICAL ERROR during spawn_enemy: {e}")
                    import traceback
                    traceback.print_exc()
                finally:
                    # Always remove the egg after hatching completes, regardless of spawn success
                    self.kill()
                    print("Egg removed after hatching")
    
    def spawn_enemy(self):
        """Spawn a level 9 enemy at the egg's location"""
        try:
            print("=== ATTEMPTING TO SPAWN ENEMY FROM EGG ===")
            
            if self.level_instance is None:
                print("ERROR: Cannot spawn enemy - level_instance is None")
                return False
                
            print(f"Level instance exists: {self.level_instance}")
            
            # Get the current room from the level instance
            # The Level class doesn't have a current_room attribute
            # Instead it has a current_room_coords attribute and a rooms dictionary
            if not hasattr(self.level_instance, 'current_room_coords'):
                print("ERROR: level_instance has no current_room_coords attribute")
                return False
                
            if not hasattr(self.level_instance, 'rooms'):
                print("ERROR: level_instance has no rooms attribute")
                return False
                
            # Get the current room using the correct attributes
            current_room_coords = self.level_instance.current_room_coords
            if current_room_coords not in self.level_instance.rooms:
                print(f"ERROR: current_room_coords {current_room_coords} not in rooms dictionary")
                return False
                
            room = self.level_instance.rooms[current_room_coords]
            print(f"Current room found: {room}")
            
            # Create a new enemy at the egg's position
            enemy_x = self.rect.centerx
            enemy_y = self.rect.centery
            
            # Create a new level 9 enemy (Shadow) - explicitly use 'level9' as the type
            print(f"Creating Shadow enemy at position ({enemy_x}, {enemy_y})")
            
            # Directly access the ENEMY_TYPES to check if level9 exists
            from config import ENEMY_TYPES
            if 'level9' in ENEMY_TYPES:
                print(f"level9 enemy type exists in config: {ENEMY_TYPES['level9']}")
            else:
                print("ERROR: level9 enemy type not found in ENEMY_TYPES")
            
            # Create the enemy
            enemy = Enemy(enemy_x, enemy_y, 'level9', 9, self.level_instance)
            print(f"Enemy created successfully with level: {enemy.level}, type: {enemy.enemy_type}")
            
            # Force the enemy to be exactly at the egg position (prevents any automatic adjustments)
            enemy.rect.centerx = enemy_x
            enemy.rect.centery = enemy_y
            
            # Make sure hitbox is aligned with the rect
            if hasattr(enemy, 'hitbox'):
                enemy.hitbox.centerx = enemy_x
                enemy.hitbox.centery = enemy_y
                print("Enemy hitbox positioned")
            else:
                print("Warning: Enemy has no hitbox attribute")
            
            # Set default animation if needed
            if not enemy.animations.get('idle', {}).get('down'):
                print("Creating placeholder textures for enemy")
                # Create a placeholder texture if no animation is loaded
                placeholder = pygame.Surface((TILE_SIZE, TILE_SIZE))
                placeholder.fill((20, 0, 30))  # Dark purple for Shadow
                
                # Add a simple shadow silhouette
                shadow_rect = pygame.Rect(TILE_SIZE//4, TILE_SIZE//4, TILE_SIZE//2, TILE_SIZE//2)
                pygame.draw.ellipse(placeholder, (50, 0, 80), shadow_rect)
                
                # Use this placeholder for all directions and states
                for direction in ['down', 'up', 'left', 'right']:
                    enemy.animations['idle'][direction] = [placeholder]
                    enemy.animations['walk'][direction] = [placeholder]
                    enemy.animations['attack'][direction] = [placeholder]
                print("Placeholder textures created")
            
            # Set current animation
            enemy.current_state = 'idle'
            enemy.facing = 'down'
            enemy.image = enemy.animations[enemy.current_state][enemy.facing][0]
            print("Enemy animation set")
            
            # Add to room's enemy collection
            print(f"Adding enemy to room.enemies (count before: {len(room.enemies)})")
            room.enemies.add(enemy)
            print(f"Enemy added to room.enemies (count after: {len(room.enemies)})")
            
            # Add to level's all_sprites list if it exists (for rendering)
            if hasattr(self.level_instance, 'all_sprites'):
                print("Adding enemy to level_instance.all_sprites")
                self.level_instance.all_sprites.add(enemy)
                print("Enemy added to all_sprites")
            else:
                print("Note: level_instance has no all_sprites attribute")
            
            print(f"Successfully spawned a Shadow enemy at position ({enemy_x}, {enemy_y})")
            
            # Create a visual effect for spawning
            if hasattr(room, 'create_chest_sparkle_burst'):
                room.create_chest_sparkle_burst(enemy_x, enemy_y)
                print("Created sparkle burst effect")
            else:
                print("Note: room has no create_chest_sparkle_burst method")
                
            # Play spawn sound if available
            if hasattr(enemy, 'sound_manager') and enemy.sound_manager:
                try:
                    enemy.sound_manager.play_sound('enemy_spawn')
                    print("Played enemy spawn sound")
                except Exception as sound_error:
                    print(f"Note: Error playing spawn sound: {sound_error}")
                    
            return True  # Successfully spawned
                
        except Exception as e:
            print(f"CRITICAL ERROR spawning enemy from egg: {str(e)}")
            import traceback
            traceback.print_exc()
            return False  # Failed to spawn
    
    def draw(self, surface):
        """Draw the egg with proper alpha for hatching effect"""
        if self.hatching and self.alpha < 255:
            # Create a copy of the image with alpha
            alpha_img = self.image.copy()
            alpha_img.set_alpha(self.alpha)
            surface.blit(alpha_img, self.rect)
        else:
            surface.blit(self.image, self.rect)

class BloodZone(pygame.sprite.Sprite):
    """A blood zone created by boss 1 that damages the player and heals the boss"""
    def __init__(self, x, y, size, damage, creator=None):
        super().__init__()
        self.creation_time = pygame.time.get_ticks()
        self.duration = 18000  # 18 seconds lifetime
        self.damage = damage
        self.creator = creator  # Reference to the boss that created this zone
        
        # Size should be 4 tiles (2x2 grid)
        self.size = size
        
        # Create the image with transparency
        self.image = pygame.Surface((size, size), pygame.SRCALPHA)
        
        # Calculate center point
        center_point = (size // 2, size // 2)
        
        # Add a glowing effect (red mist)
        for i in range(6):
            glow_radius = size // 2 + (5 - i) * 3
            glow_alpha = 15 + i * 10
            glow_col = (150, 0, 0, glow_alpha)  # Red glow for blood
            pygame.draw.circle(self.image, glow_col, center_point, glow_radius)
        
        # Main blood puddle colors - dark red
        outer_color = (120, 0, 0, 190)  # Dark red
        main_color = (180, 0, 0, 200)   # Medium red
        inner_color = (220, 0, 0, 220)  # Lighter red
        
        # Draw the base puddle shape as a circle
        pygame.draw.circle(self.image, outer_color, center_point, size // 2 - 2)
        
        # Draw a smaller inner puddle
        pygame.draw.circle(self.image, main_color, center_point, int(size * 0.4) - 1)
        
        # Draw the blood center
        pygame.draw.circle(self.image, inner_color, center_point, int(size * 0.25))
        
        # Add some blood splatter details
        for _ in range(8):
            angle = random.uniform(0, math.pi * 2)
            distance = random.uniform(0, size // 4)
            
            dot_x = center_point[0] + int(math.cos(angle) * distance)
            dot_y = center_point[1] + int(math.sin(angle) * distance)
            
            dot_size = random.randint(2, 5)
            bubble_color = (220, 0, 0, 230)  # Bright red for blood drops
            pygame.draw.circle(self.image, bubble_color, (dot_x, dot_y), dot_size)
        
        self.rect = self.image.get_rect(center=(x, y))
        self.true_center = (x, y)  # Store the exact center for accurate positioning
        
        # Add damage cooldown
        self.last_damage_time = 0
        self.damage_cooldown = 1000  # 1 second between damage applications
        
        # Add pulse/glow effect
        self.pulse_time = random.uniform(0, math.pi * 2)  # Random start phase
        self.pulse_speed = 0.08  # Speed of pulsing
        
    def update(self):
        # Check if the zone should disappear
        if pygame.time.get_ticks() - self.creation_time > self.duration:
            self.kill()
            return
            
        # Update pulse effect
        self.pulse_time += self.pulse_speed
        if self.pulse_time > math.pi * 2:
            self.pulse_time -= math.pi * 2

    def check_collision(self, rect):
        # Don't collide with the boss that created this zone
        if hasattr(self, 'creator') and self.creator and self.creator.rect == rect:
            return False
        return self.rect.colliderect(rect)
        
    def can_damage(self):
        # Check if the cooldown has elapsed
        current_time = pygame.time.get_ticks()
        if current_time - self.last_damage_time >= self.damage_cooldown:
            self.last_damage_time = current_time
            return True
        return False

class DeathRay(pygame.sprite.Sprite):
    """Death ray that spins around the boss 7 and damages the player"""
    def __init__(self, boss, length, damage):
        super().__init__()
        self.boss = boss
        self.length = length * TILE_SIZE  # Convert tiles to pixels
        self.damage = damage
        self.angle = 0  # Starting angle (in radians)
        self.rotation_speed = 0.02  # Radians per frame
        self.damage_cooldown = 500  # Milliseconds between damage ticks
        self.last_damage_time = 0
        
        # Create ray hitbox (will be updated in update method)
        self.ray_width = 16  # Width of the ray in pixels
        self.rect = pygame.Rect(0, 0, self.length, self.ray_width)
        
        # Create visual properties
        self.ray_color = (255, 60, 0)  # Red-orange color
        self.glow_color = (255, 150, 50, 100)  # Orange glow with transparency
        self.pulse_timer = 0
        self.creation_time = pygame.time.get_ticks()
        
        # Initialize endpoints
        self.start_point = (self.boss.rect.centerx, self.boss.rect.centery)
        self.end_point = (self.boss.rect.centerx + self.length, self.boss.rect.centery)
        
        # Sound effects
        self.sound_manager = get_sound_manager()
        self.sound_played = False
    
    def update(self):
        """Update the death ray position and rotation"""
        current_time = pygame.time.get_ticks()
        
        # Update angle for rotation
        self.angle += self.rotation_speed
        
        # Update the ray endpoints
        start_x = self.boss.rect.centerx
        start_y = self.boss.rect.centery
        end_x = start_x + math.cos(self.angle) * self.length
        end_y = start_y + math.sin(self.angle) * self.length
        
        # Update rectangle for collision detection
        # The rect needs to follow the line from start to end
        min_x = min(start_x, end_x)
        min_y = min(start_y, end_y)
        width = abs(end_x - start_x)
        height = abs(end_y - start_y)
        
        # Ensure the rect has at least a minimum size
        if width < self.ray_width:
            width = self.ray_width
        if height < self.ray_width:
            height = self.ray_width
            
        self.rect = pygame.Rect(min_x, min_y, width, height)
        
        # Store endpoints for drawing
        self.start_point = (start_x, start_y)
        self.end_point = (end_x, end_y)
        
        # Visual pulse effect
        self.pulse_timer += 0.1
        
        # Play sound effect periodically
        if not self.sound_played or current_time - self.sound_played > 3000:  # Every 3 seconds
            try:
                self.sound_manager.play_sound("effects/boss_ray")
            except Exception as e:
                # Sound file might not exist, handle gracefully
                print(f"Note: Could not play death ray sound - {e}")
            self.sound_played = current_time
    
    def check_collision(self, player_rect):
        """Check if the ray line intersects with the player rectangle"""
        # First, quick broad-phase check using rects
        if not self.rect.colliderect(player_rect):
            return False
            
        # Then, more precise check using line-rectangle intersection
        # Calculate the four sides of the player rect
        rect_sides = [
            (player_rect.left, player_rect.top, player_rect.left, player_rect.bottom),  # Left
            (player_rect.left, player_rect.bottom, player_rect.right, player_rect.bottom),  # Bottom
            (player_rect.right, player_rect.bottom, player_rect.right, player_rect.top),  # Right
            (player_rect.right, player_rect.top, player_rect.left, player_rect.top)  # Top
        ]
        
        # Check if the ray line intersects any of the rect sides
        for side in rect_sides:
            if self._line_intersection(self.start_point, self.end_point, (side[0], side[1]), (side[2], side[3])):
                return True
                
        # Also check if the player is very close to the line itself
        return self._point_line_distance(player_rect.center, self.start_point, self.end_point) < self.ray_width
    
    def _line_intersection(self, line1_start, line1_end, line2_start, line2_end):
        """Detect if two line segments intersect"""
        x1, y1 = line1_start
        x2, y2 = line1_end
        x3, y3 = line2_start
        x4, y4 = line2_end
        
        # Calculate determinants
        den = (y4 - y3) * (x2 - x1) - (x4 - x3) * (y2 - y1)
        if den == 0:
            return False  # Lines are parallel
            
        ua = ((x4 - x3) * (y1 - y3) - (y4 - y3) * (x1 - x3)) / den
        ub = ((x2 - x1) * (y1 - y3) - (y2 - y1) * (x1 - x3)) / den
        
        # Check if intersection is within line segments
        return 0 <= ua <= 1 and 0 <= ub <= 1
    
    def _point_line_distance(self, point, line_start, line_end):
        """Calculate distance from a point to a line segment"""
        x, y = point
        x1, y1 = line_start
        x2, y2 = line_end
        
        # Line length squared
        line_length_sq = (x2 - x1)**2 + (y2 - y1)**2
        if line_length_sq == 0:
            return math.sqrt((x - x1)**2 + (y - y1)**2)  # Point to point distance
            
        # Calculate projection ratio
        t = max(0, min(1, ((x - x1) * (x2 - x1) + (y - y1) * (y2 - y1)) / line_length_sq))
        
        # Calculate closest point on line
        proj_x = x1 + t * (x2 - x1)
        proj_y = y1 + t * (y2 - y1)
        
        # Distance from point to closest point on line
        return math.sqrt((x - proj_x)**2 + (y - proj_y)**2)
    
    def can_damage(self):
        """Check if the ray can cause damage (based on cooldown)"""
        current_time = pygame.time.get_ticks()
        if current_time - self.last_damage_time >= self.damage_cooldown:
            self.last_damage_time = current_time
            return True
        return False
    
    def draw(self, surface):
        """Draw the death ray with visual effects"""
        current_time = pygame.time.get_ticks()
        
        # Create glow effect around the ray
        # Draw multiple lines with decreasing width and opacity for glow effect
        for i in range(5, 0, -1):
            # Pulsing effect
            pulse = math.sin(self.pulse_timer) * 0.5 + 0.5
            width = int(i * 2 * (0.7 + 0.3 * pulse))
            alpha = int(150 * (i / 5) * pulse)
            
            glow_color = (255, 150, 50, alpha)
            
            # Draw the glowing line
            pygame.draw.line(
                surface, 
                glow_color, 
                self.start_point, 
                self.end_point, 
                width
            )
        
        # Draw the main ray with core color
        pygame.draw.line(
            surface, 
            self.ray_color, 
            self.start_point, 
            self.end_point, 
            4
        )
        
        # Draw energy particles along the ray
        ray_length = math.sqrt((self.end_point[0] - self.start_point[0])**2 + 
                             (self.end_point[1] - self.start_point[1])**2)
        num_particles = int(ray_length / 20)  # One particle every 20 pixels
        
        for i in range(num_particles):
            if random.random() < 0.3:  # 30% chance for each potential particle
                # Position along ray
                t = random.random()
                particle_x = self.start_point[0] + t * (self.end_point[0] - self.start_point[0])
                particle_y = self.start_point[1] + t * (self.end_point[1] - self.start_point[1])
                
                # Particle size and color
                size = random.randint(2, 4)
                brightness = random.randint(200, 255)
                color = (brightness, brightness // 2, 0)
                
                pygame.draw.circle(
                    surface, 
                    color, 
                    (int(particle_x), int(particle_y)), 
                    size
                )