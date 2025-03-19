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
    def __init__(self, x, y, direction, speed=1.4, damage=25, color=(255, 0, 0), is_orbiting=False, orbit_boss=None, orbit_angle=0, orbit_radius=0, orbit_speed=0, become_stationary=False, stationary_time=0):
        super().__init__()
        self.asset_manager = get_asset_manager()
        
        # For orbiting projectiles, use the ghost sprite instead of a colored ball
        if is_orbiting:
            ghost_path = os.path.join(ENEMY_SPRITES_PATH, "ghost", "ghost.png")
            if os.path.exists(ghost_path):
                # Load and scale the ghost image
                self.image = self.asset_manager.load_image(ghost_path, scale=(TILE_SIZE//1.5, TILE_SIZE//1.5))
                self.original_image = self.image.copy()
            else:
                print(f"Ghost image not found at {ghost_path}, using fallback")
                self.create_projectile_image(color)
        else:
            # Create a regular projectile image for non-orbiting projectiles
            self.create_projectile_image(color)
        
        self.rect = self.image.get_rect()
        self.rect.centerx = x
        self.rect.centery = y
        
        # Movement properties
        self.direction = direction  # Tuple (dx, dy) - normalized direction
        self.speed = speed
        self.damage = damage
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
        self.creation_time = pygame.time.get_ticks()
        self.stationary_duration = 0  # How long to stay stationary (0 = forever)
        
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
            if self.stationary_duration > 0:
                time_as_stationary = current_time - (self.creation_time + self.stationary_time)
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
            # Draw position history for trailing effect
            for i, (x, y, img) in enumerate(reversed(self.position_history)):
                # Calculate alpha (transparency) based on position in history
                # Make the oldest ones more transparent
                alpha = max(30, 150 - (i * 20))
                
                # Create a copy of the sprite with alpha transparency
                ghost_img = img.copy()
                # Set the alpha of the entire surface
                ghost_img.set_alpha(alpha)
                
                # Draw the ghost sprite at the historical position
                surface.blit(ghost_img, (x, y))
        
        # Draw the main projectile
        surface.blit(self.image, self.rect)
        
    def check_collision(self, player_rect):
        """Check if projectile collides with player"""
        if self.rect.colliderect(player_rect):
            # Always return True for collision detection, but let the caller decide whether to destroy
            return True
        return False

class Enemy(pygame.sprite.Sprite):
    def __init__(self, x, y, enemy_type, level, level_instance=None):
        super().__init__()
        self.asset_manager = get_asset_manager()
        self.sound_manager = get_sound_manager()
        self.enemy_data = ENEMY_TYPES[f'level{level}']
        self.level_instance = level_instance
        
        # Animation states and directions
        self.animations = {
            'idle': {},
            'walk': {},
            'attack': {}
        }
        
        # Get the enemy name
        enemy_name = self.enemy_data['name'].lower().replace(' ', '_')
        
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
        
        # Movement
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
            directions = [(0, -1), (1, 0), (0, 1), (-1, 0), (1, 1), (-1, 1), (1, -1), (-1, -1)]
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
            
        # A* algorithm
        open_set = []  # Priority queue of nodes to explore
        closed_set = set()  # Set of explored nodes
        
        # Add start node to open set
        heapq.heappush(open_set, (0, 0, (start_tile_x, start_tile_y, None)))  # (f_score, tiebreaker, (x, y, parent))
        
        # Dict to store g_scores (cost from start to node)
        g_scores = {(start_tile_x, start_tile_y): 0}
        
        # Dict to store f_scores (estimated total cost from start to goal)
        f_scores = {(start_tile_x, start_tile_y): self.manhattan_distance(start_tile_x, start_tile_y, target_tile_x, target_tile_y)}
        
        tiebreaker = 0  # To break ties when f_scores are equal
        
        # Define possible movement directions (4-way)
        directions = [(0, -1), (1, 0), (0, 1), (-1, 0)]  # Up, right, down, left
        
        found_path = False
        max_iterations = 1000  # Prevent infinite loops
        iterations = 0
        
        while open_set and not found_path and iterations < max_iterations:
            iterations += 1
            # Get node with lowest f_score
            _, _, (current_x, current_y, parent) = heapq.heappop(open_set)
            
            # If we've reached the target, reconstruct path
            if (current_x, current_y) == (target_tile_x, target_tile_y):
                found_path = True
                path = []
                
                # Reconstruct path from parents
                while parent is not None:
                    # Convert back to pixel coordinates (center of tile)
                    path.append((parent[0] * TILE_SIZE + TILE_SIZE // 2, 
                                parent[1] * TILE_SIZE + TILE_SIZE // 2))
                    parent = parent[2]
                    
                # The path is from target to start, so reverse it
                path.reverse()
                
                # Add target as final point in path
                path.append((target_tile_x * TILE_SIZE + TILE_SIZE // 2, 
                            target_tile_y * TILE_SIZE + TILE_SIZE // 2))
                
                return path
                
            # Skip if we've already explored this node
            if (current_x, current_y) in closed_set:
                continue
                
            # Add to closed set
            closed_set.add((current_x, current_y))
            
            # Check neighboring tiles
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
                    
                # Calculate tentative g_score
                tentative_g_score = g_scores[(current_x, current_y)] + 1
                
                # If we found a better path to this neighbor, update it
                if (neighbor_x, neighbor_y) not in g_scores or tentative_g_score < g_scores[(neighbor_x, neighbor_y)]:
                    # Update g_score
                    g_scores[(neighbor_x, neighbor_y)] = tentative_g_score
                    
                    # Calculate f_score
                    h_score = self.manhattan_distance(neighbor_x, neighbor_y, target_tile_x, target_tile_y)
                    f_score = tentative_g_score + h_score
                    f_scores[(neighbor_x, neighbor_y)] = f_score
                    
                    # Add to open set
                    tiebreaker += 1
                    heapq.heappush(open_set, (f_score, tiebreaker, (neighbor_x, neighbor_y, (current_x, current_y, parent))))
        
        # If we get here, no path was found
        return []
    
    def manhattan_distance(self, x1, y1, x2, y2):
        """Calculate Manhattan distance between two points"""
        return abs(x1 - x2) + abs(y1 - y2)
    
    def move_towards_player(self, player):
        """Move towards player using pathfinding"""
        # Check if we need to update the path
        target_pos = (player.rect.centerx, player.rect.centery)
        
        # Only update path if:
        # 1. We don't have a path, or
        # 2. The target has moved significantly, or
        # 3. It's time to update the path based on timer, or
        # 4. We've had too many consecutive movement failures
        should_update_path = (
            not self.path or 
            (self.last_target_position and 
              ((abs(self.last_target_position[0] - target_pos[0]) > TILE_SIZE * 2) or 
               (abs(self.last_target_position[1] - target_pos[1]) > TILE_SIZE * 2))) or
             self.path_update_timer >= self.path_update_frequency or
             self.movement_failed_counter >= self.max_movement_failures
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
            
            # Reset timer and counters
            self.path_update_timer = 0
            self.movement_failed_counter = 0
            self.last_target_position = target_pos
        else:
            # Increment timer
            self.path_update_timer += 1
        
        # If we have a path, follow it
        if self.path:
            # Get the next point in the path
            next_point = self.path[0]
            
            # Calculate direction to next point
            dx = next_point[0] - self.rect.centerx
            dy = next_point[1] - self.rect.centery
            distance = math.sqrt(dx * dx + dy * dy)
            
            # If we've reached this point (or close enough), move to the next point
            if distance < self.speed:
                self.path.pop(0)
                # If path is now empty, we're done
                if not self.path:
                    # If we're close to player, stop moving
                    if math.sqrt((player.rect.centerx - self.rect.centerx)**2 + 
                               (player.rect.centery - self.rect.centery)**2) < self.attack_range:
                        self.velocity_x = 0
                        self.velocity_y = 0
                        return
                    # Otherwise, calculate a new path
                    self.path = self.find_path(
                        self.rect.centerx, 
                        self.rect.centery, 
                        player.rect.centerx, 
                        player.rect.centery,
                        player.level
                    )
                    
                    # If we couldn't find a path, use the old method (direct movement)
                    if not self.path:
                        # Old direct movement code
                        dx = player.rect.centerx - self.rect.centerx
                        dy = player.rect.centery - self.rect.centery
                        distance = math.sqrt(dx * dx + dy * dy)
                        
                        if distance > 0:
                            dx = dx / distance
                            dy = dy / distance
                            self.velocity_x = dx * self.speed
                            self.velocity_y = dy * self.speed
                            
                            # Update facing direction based on movement
                            if abs(dx) > abs(dy):
                                self.facing = 'right' if dx > 0 else 'left'
                            else:
                                self.facing = 'down' if dy > 0 else 'up'
                        return
            else:
                # Move towards next point
                if distance > 0:
                    dx = dx / distance
                    dy = dy / distance
                    self.velocity_x = dx * self.speed
                    self.velocity_y = dy * self.speed
                    
                    # Update facing direction based on movement
                    if abs(dx) > abs(dy):
                        self.facing = 'right' if dx > 0 else 'left'
                    else:
                        self.facing = 'down' if dy > 0 else 'up'
        else:
            # If there's no path, fall back to direct movement
            dx = player.rect.centerx - self.rect.centerx
            dy = player.rect.centery - self.rect.centery
            distance = math.sqrt(dx * dx + dy * dy)
            
            if distance > 0:
                dx = dx / distance
                dy = dy / distance
                self.velocity_x = dx * self.speed
                self.velocity_y = dy * self.speed
                
                # Update facing direction based on movement
                if abs(dx) > abs(dy):
                    self.facing = 'right' if dx > 0 else 'left'
                else:
                    self.facing = 'down' if dy > 0 else 'up'

    def can_attack(self):
        current_time = pygame.time.get_ticks()
        return current_time - self.last_attack_time >= self.attack_cooldown
        
    def attack(self, player):
        if self.can_attack():
            self.last_attack_time = pygame.time.get_ticks()
            self.current_state = 'attack'
            self.frame = 0  # Reset animation frame
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
        # Check if in blood puddle state and ready to resurrect
        if self.is_dead:
            current_time = pygame.time.get_ticks()
            
            # If it's time to resurrect
            if current_time >= self.resurrection_time:
                self.resurrect()
            
            # Skip the rest of the update if still in blood puddle state
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
        old_velocity_x = self.velocity_x
        old_velocity_y = self.velocity_y
        
        # Ensure player has level attribute before checking collision
        has_level = hasattr(player, 'level') and player.level is not None
        
        # Try moving horizontally
        self.rect.x += self.velocity_x
        
        # If collision occurs, try with half the velocity
        if has_level and player.level.check_collision(self.rect):
            self.rect = old_rect.copy()
            self.rect.x += self.velocity_x * 0.5  # Try half speed
            
            # If still colliding, revert and mark as movement failure
            if has_level and player.level.check_collision(self.rect):
                self.rect = old_rect.copy()
                self.velocity_x = 0
                
                if self.state == 'chase':
                    self.movement_failed_counter += 1
            else:
                # Half speed worked, reset failure counter
                self.movement_failed_counter = 0
        else:
            # Movement succeeded, reset failure counter
            if old_velocity_x != 0 and self.state == 'chase':
                self.movement_failed_counter = 0
        
        # Now try moving vertically
        self.rect.y += self.velocity_y
        
        # If collision occurs, try with half the velocity
        if has_level and player.level.check_collision(self.rect):
            self.rect.y = old_rect.y  # Revert only Y position
            self.rect.y += self.velocity_y * 0.5  # Try half speed
            
            # If still colliding, revert and mark as movement failure
            if has_level and player.level.check_collision(self.rect):
                self.rect.y = old_rect.y
                self.velocity_y = 0
                
                if self.state == 'chase':
                    self.movement_failed_counter += 1
            else:
                # Half speed worked, reset failure counter
                self.movement_failed_counter = 0
        else:
            # Movement succeeded, reset failure counter
            if old_velocity_y != 0 and self.state == 'chase':
                self.movement_failed_counter = 0
        
        # Keep enemy on screen
        self.rect.clamp_ip(pygame.display.get_surface().get_rect())
        
        # Update animation
        self.animation_time += self.animation_speed
        
        # If the attack animation is done, go back to previous state
        if self.current_state == 'attack' and self.animation_time >= len(self.animations[self.current_state][self.facing]):
            self.current_state = 'idle' if self.state == 'idle' else 'walk'
            self.animation_time = 0
            
        # Calculate current frame
        self.frame = int(self.animation_time) % len(self.animations[self.current_state][self.facing])
        self.image = self.animations[self.current_state][self.facing][self.frame]
        
    def draw(self, surface):
        surface.blit(self.image, self.rect)
        
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

class Boss(Enemy):
    def __init__(self, x, y, level, level_instance=None):
        super().__init__(x, y, None, level, level_instance)
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
        
        # Level 2 boss uses projectiles
        self.projectiles = pygame.sprite.Group()
        self.projectile_cooldown = 0
        self.projectile_cooldown_time = 90  # frames between projectile attacks
        
        # Tracking if Boss 5 has already created its orbiting projectiles
        self.orbiting_projectiles_created = False
        
        # Boss 5 casting mode attributes
        if level == 5:
            self.casting_mode = False
            self.casting_mode_cooldown = 6000  # 6 seconds between casts
            self.casting_mode_duration = 2000  # 2 seconds in casting mode
            self.last_cast_time = 0
            self.cast_complete = False
            self.stationary_projectile_duration = 6000  # How long projectiles stay in place
        
        # Phase system for special attacks
        self.phase = 0  # 0 = normal, 1 = <60% health, 2 = <30% health
        self.last_special_attack_time = 0
        self.special_attack_cooldown = 3000  # 3 seconds between special attacks
        
        # Get boss name
        boss_name = self.enemy_data['name'].lower().replace(' ', '_')
        
        # Load animations for each direction
        for direction in ['down', 'up', 'left', 'right']:
            # Create default colored image with boss name as placeholder
            placeholder = pygame.Surface((TILE_SIZE*1.5, TILE_SIZE*1.5))
            placeholder.fill((150, 0, 0))  # Darker red for bosses
            font = pygame.font.Font(None, 16)
            text = font.render(f"BOSS: {boss_name[:8]}", True, WHITE)
            text_rect = text.get_rect(center=(TILE_SIZE*1.5//2, TILE_SIZE*1.5//2))
            placeholder.blit(text, text_rect)
            
            # Set default animations to placeholder
            self.animations['idle'][direction] = [placeholder]
            self.animations['walk'][direction] = [placeholder]
            self.animations['attack'][direction] = [placeholder]
            self.animations['special'][direction] = [placeholder]
            
            # Set up base path for this boss
            base_path = os.path.join(BOSS_SPRITES_PATH, boss_name)
            
            # First, check for level 1 boss to use boss_1.png
            if level == 1:
                try:
                    # Try to load the new boss_1.png image
                    boss_img_path = os.path.join(BOSS_SPRITES_PATH, "boss_1.png")
                    if os.path.exists(boss_img_path):
                        # Load and scale the image
                        boss_img = self.asset_manager.load_image(boss_img_path, scale=(TILE_SIZE*2, TILE_SIZE*2))
                        
                        # Use this image for all animation states
                        self.animations['idle'][direction] = [boss_img]
                        self.animations['walk'][direction] = [boss_img]
                        self.animations['attack'][direction] = [boss_img]
                        self.animations['special'][direction] = [boss_img]
                        print(f"Using boss_1.png for level 1 boss {direction} animations")
                        continue  # Skip the rest of this iteration
                except Exception as e:
                    print(f"Failed to load boss_1.png for level 1 boss: {e}")
                    # Continue with the normal animation loading
            
            # Check for level 2 boss to use boss_2.png
            elif level == 2:
                try:
                    # Try to load the new boss_2.png image
                    boss_img_path = os.path.join(BOSS_SPRITES_PATH, "boss_2.png")
                    if os.path.exists(boss_img_path):
                        # Load and scale the image
                        boss_img = self.asset_manager.load_image(boss_img_path, scale=(TILE_SIZE*2, TILE_SIZE*2))
                        
                        # Use this image for all animation states
                        self.animations['idle'][direction] = [boss_img]
                        self.animations['walk'][direction] = [boss_img]
                        self.animations['attack'][direction] = [boss_img]
                        self.animations['special'][direction] = [boss_img]
                        print(f"Using boss_2.png for level 2 boss {direction} animations")
                        continue  # Skip the rest of this iteration
                except Exception as e:
                    print(f"Failed to load boss_2.png for level 2 boss: {e}")
                    # Continue with the normal animation loading
            
            # Check for level 3 boss to use boss_3.png
            elif level == 3:
                try:
                    # Try to load the new boss_3.png image
                    boss_img_path = os.path.join(BOSS_SPRITES_PATH, "boss_3.png")
                    if os.path.exists(boss_img_path):
                        # Load and scale the image
                        boss_img = self.asset_manager.load_image(boss_img_path, scale=(TILE_SIZE*2, TILE_SIZE*2))
                        
                        # Use this image for all animation states
                        self.animations['idle'][direction] = [boss_img]
                        self.animations['walk'][direction] = [boss_img]
                        self.animations['attack'][direction] = [boss_img]
                        self.animations['special'][direction] = [boss_img]
                        print(f"Using boss_3.png for level 3 boss {direction} animations")
                        continue  # Skip the rest of this iteration
                except Exception as e:
                    print(f"Failed to load boss_3.png for level 3 boss: {e}")
                    # Continue with the normal animation loading
            
            # Check for level 4 boss to use boss_4.png
            elif level == 4:
                try:
                    # Try to load the new boss_4.png image
                    boss_img_path = os.path.join(BOSS_SPRITES_PATH, "boss_4.png")
                    if os.path.exists(boss_img_path):
                        # Load and scale the image
                        boss_img = self.asset_manager.load_image(boss_img_path, scale=(TILE_SIZE*2.2, TILE_SIZE*2.2))
                        
                        # Use this image for all animation states
                        self.animations['idle'][direction] = [boss_img]
                        self.animations['walk'][direction] = [boss_img]
                        self.animations['attack'][direction] = [boss_img]
                        self.animations['special'][direction] = [boss_img]
                        print(f"Using boss_4.png for level 4 boss {direction} animations")
                        continue  # Skip the rest of this iteration
                except Exception as e:
                    print(f"Failed to load boss_4.png for level 4 boss: {e}")
                    # Continue with the normal animation loading
            
            # Check for level 5 boss to use boss_5.png
            elif level == 5:
                try:
                    # Try to load the new boss_5.png image
                    boss_img_path = os.path.join(BOSS_SPRITES_PATH, "boss_5.png")
                    if os.path.exists(boss_img_path):
                        # Load and scale the image - slightly larger for this boss
                        boss_img = self.asset_manager.load_image(boss_img_path, scale=(TILE_SIZE*2.2, TILE_SIZE*2.2))
                        
                        # Use this image for all animation states
                        self.animations['idle'][direction] = [boss_img]
                        self.animations['walk'][direction] = [boss_img]
                        self.animations['attack'][direction] = [boss_img]
                        self.animations['special'][direction] = [boss_img]
                        print(f"Using boss_5.png for level 5 boss {direction} animations")
                        continue  # Skip the rest of this iteration
                except Exception as e:
                    print(f"Failed to load boss_5.png for level 5 boss: {e}")
                    # Continue with the normal animation loading
            
            # Check for level 6 boss to use boss_6.png
            elif level == 6:
                try:
                    # Try to load the new boss_6.png image
                    boss_img_path = os.path.join(BOSS_SPRITES_PATH, "boss_6.png")
                    if os.path.exists(boss_img_path):
                        # Load and scale the image
                        boss_img = self.asset_manager.load_image(boss_img_path, scale=(TILE_SIZE*2.2, TILE_SIZE*2.2))
                        
                        # Use this image for all animation states
                        self.animations['idle'][direction] = [boss_img]
                        self.animations['walk'][direction] = [boss_img]
                        self.animations['attack'][direction] = [boss_img]
                        self.animations['special'][direction] = [boss_img]
                        print(f"Using boss_6.png for level 6 boss {direction} animations")
                        continue  # Skip the rest of this iteration
                except Exception as e:
                    print(f"Failed to load boss_6.png for level 6 boss: {e}")
                    # Continue with the normal animation loading
            
            # Check for level 7 boss to use boss_7.png
            elif level == 7:
                try:
                    # Try to load the new boss_7.png image
                    boss_img_path = os.path.join(BOSS_SPRITES_PATH, "boss_7.png")
                    if os.path.exists(boss_img_path):
                        # Load and scale the image
                        boss_img = self.asset_manager.load_image(boss_img_path, scale=(TILE_SIZE*2.3, TILE_SIZE*2.3))
                        
                        # Use this image for all animation states
                        self.animations['idle'][direction] = [boss_img]
                        self.animations['walk'][direction] = [boss_img]
                        self.animations['attack'][direction] = [boss_img]
                        self.animations['special'][direction] = [boss_img]
                        print(f"Using boss_7.png for level 7 boss {direction} animations")
                        continue  # Skip the rest of this iteration
                except Exception as e:
                    print(f"Failed to load boss_7.png for level 7 boss: {e}")
                    # Continue with the normal animation loading
            
            # Check for level 8 boss to use boss_8.png
            elif level == 8:
                try:
                    # Try to load the new boss_8.png image
                    boss_img_path = os.path.join(BOSS_SPRITES_PATH, "boss_8.png")
                    if os.path.exists(boss_img_path):
                        # Load and scale the image
                        boss_img = self.asset_manager.load_image(boss_img_path, scale=(TILE_SIZE*2.3, TILE_SIZE*2.3))
                        
                        # Use this image for all animation states
                        self.animations['idle'][direction] = [boss_img]
                        self.animations['walk'][direction] = [boss_img]
                        self.animations['attack'][direction] = [boss_img]
                        self.animations['special'][direction] = [boss_img]
                        print(f"Using boss_8.png for level 8 boss {direction} animations")
                        continue  # Skip the rest of this iteration
                except Exception as e:
                    print(f"Failed to load boss_8.png for level 8 boss: {e}")
                    # Continue with the normal animation loading
            
            # Check for level 9 boss to use boss_9.png
            elif level == 9:
                try:
                    # Try to load the new boss_9.png image
                    boss_img_path = os.path.join(BOSS_SPRITES_PATH, "boss_9.png")
                    if os.path.exists(boss_img_path):
                        # Load and scale the image
                        boss_img = self.asset_manager.load_image(boss_img_path, scale=(TILE_SIZE*2.4, TILE_SIZE*2.4))
                        
                        # Use this image for all animation states
                        self.animations['idle'][direction] = [boss_img]
                        self.animations['walk'][direction] = [boss_img]
                        self.animations['attack'][direction] = [boss_img]
                        self.animations['special'][direction] = [boss_img]
                        print(f"Using boss_9.png for level 9 boss {direction} animations")
                        continue  # Skip the rest of this iteration
                except Exception as e:
                    print(f"Failed to load boss_9.png for level 9 boss: {e}")
                    # Continue with the normal animation loading
            
            # Check for level 10 boss to use boss_10.png
            elif level == 10:
                try:
                    # Try to load the new boss_10.png image
                    boss_img_path = os.path.join(BOSS_SPRITES_PATH, "boss_10.png")
                    if os.path.exists(boss_img_path):
                        # Load and scale the image
                        boss_img = self.asset_manager.load_image(boss_img_path, scale=(TILE_SIZE*2.5, TILE_SIZE*2.5))
                        
                        # Use this image for all animation states
                        self.animations['idle'][direction] = [boss_img]
                        self.animations['walk'][direction] = [boss_img]
                        self.animations['attack'][direction] = [boss_img]
                        self.animations['special'][direction] = [boss_img]
                        print(f"Using boss_10.png for level 10 boss {direction} animations")
                        continue  # Skip the rest of this iteration
                except Exception as e:
                    print(f"Failed to load boss_10.png for level 10 boss: {e}")
                    # Continue with the normal animation loading
            
            # Now try to load actual animations but don't crash if they're missing
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
        
    def move_towards_player(self, player):
        """Move towards player using simplified movement for more reliable chasing"""
        # Calculate direction vector to player
        dx = player.rect.centerx - self.rect.centerx
        dy = player.rect.centery - self.rect.centery
        distance = math.sqrt(dx * dx + dy * dy)
        
        # Always use direct movement for level 2 boss to ensure reliable chasing
        if self.level == 2 or distance < TILE_SIZE * 5:
            # Use direct movement - much more reliable
            if distance > 0:
                dx = dx / distance
                dy = dy / distance
                
                # Set velocity with full speed
                self.velocity_x = dx * self.speed
                self.velocity_y = dy * self.speed
                
                # Update facing direction
                if abs(dx) > abs(dy):
                    self.facing = 'right' if dx > 0 else 'left'
                else:
                    self.facing = 'down' if dy > 0 else 'up'
            return
        
        # For other bosses (or longer distances for non-level-2 bosses), try pathfinding
        target_pos = (player.rect.centerx, player.rect.centery)
        
        # Update path more frequently to avoid getting stuck
        should_update_path = (
            not self.path or 
            self.path_update_timer >= 10 or
            self.movement_failed_counter >= 2 or
            (self.last_target_position and 
             ((abs(self.last_target_position[0] - target_pos[0]) > TILE_SIZE) or 
              (abs(self.last_target_position[1] - target_pos[1]) > TILE_SIZE)))
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
            
            # Reset counters
            self.path_update_timer = 0
            self.movement_failed_counter = 0
            self.last_target_position = target_pos
            
            # If pathfinding fails, use direct movement
            if not self.path and distance > 0:
                dx = dx / distance
                dy = dy / distance
                self.velocity_x = dx * self.speed
                self.velocity_y = dy * self.speed
                
                if abs(dx) > abs(dy):
                    self.facing = 'right' if dx > 0 else 'left'
                else:
                    self.facing = 'down' if dy > 0 else 'up'
                return
        else:
            # Increment timer
            self.path_update_timer += 1
        
        # If no path, use direct movement
        if not self.path:
            if distance > 0:
                dx = dx / distance
                dy = dy / distance
                self.velocity_x = dx * self.speed
                self.velocity_y = dy * self.speed
                
                if abs(dx) > abs(dy):
                    self.facing = 'right' if dx > 0 else 'left'
                else:
                    self.facing = 'down' if dy > 0 else 'up'
            return
        
        # Follow the path if we have one
        next_point = self.path[0]
        
        # Calculate direction to next path point
        dx = next_point[0] - self.rect.centerx
        dy = next_point[1] - self.rect.centery
        point_distance = math.sqrt(dx * dx + dy * dy)
        
        # If we're close enough to this point, move to the next one
        if point_distance < self.speed:
            self.path.pop(0)
            # If no more points, use direct movement
            if not self.path:
                if distance > 0:
                    dx = (player.rect.centerx - self.rect.centerx) / distance
                    dy = (player.rect.centery - self.rect.centery) / distance
                    self.velocity_x = dx * self.speed
                    self.velocity_y = dy * self.speed
                    
                    if abs(dx) > abs(dy):
                        self.facing = 'right' if dx > 0 else 'left'
                    else:
                        self.facing = 'down' if dy > 0 else 'up'
                # Force path recalculation on next update
                self.path_update_timer = 999
                return
            
            # Use the next point in the path
            next_point = self.path[0]
            dx = next_point[0] - self.rect.centerx
            dy = next_point[1] - self.rect.centery
            point_distance = math.sqrt(dx * dx + dy * dy)
        
        # Move toward the next point in the path
        if point_distance > 0:
            dx = dx / point_distance
            dy = dy / point_distance
            self.velocity_x = dx * self.speed
            self.velocity_y = dy * self.speed
            
            if abs(dx) > abs(dy):
                self.facing = 'right' if dx > 0 else 'left'
            else:
                self.facing = 'down' if dy > 0 else 'up'
                
    def take_damage(self, amount):
        """Override the parent take_damage method to make boss aggressive when hit"""
        # Set the has_spotted_player flag to True when boss takes damage
        self.has_spotted_player = True
        
        # Clear any lingering reflected damage to prevent bugs
        if self.level == 4:
            # Always reset reflection when taking damage
            if not self.defensive_mode:
                self.reflected_damage = 0  # Ensure no reflection when not in defensive mode
        
        # Level 4 boss damage reflection during defensive mode
        if self.level == 4 and self.defensive_mode:
            # Get the current game instance to access the player
            # We need to reflect damage, but since we don't have direct access to the player,
            # we'll store the reflected damage amount so the game can apply it later
            self.reflected_damage = amount * 0.5  # Reflect 50% of damage
            print(f"Level 4 boss reflecting {self.reflected_damage} damage!")
            
            # Don't take damage during defensive mode
            return False
            
        # Call the parent method to handle the actual damage
        return super().take_damage(amount)
        
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
                
                # Print for debugging
                print(f"Player dir: ({dx:.2f}, {dy:.2f})")
                print(f"Center: ({center_dx:.2f}, {center_dy:.2f})")
                print(f"Left: ({left_dx:.2f}, {left_dy:.2f})")
                print(f"Right: ({right_dx:.2f}, {right_dy:.2f})")
                
                # Create the projectiles with different colors
                # Center projectile - offset slightly ahead of the others and use brighter color
                center_projectile = BossProjectile(
                    self.rect.centerx + center_dx * 10,  # Offset slightly ahead 
                    self.rect.centery + center_dy * 10, 
                    (center_dx, center_dy), 
                    1.4, 
                    self.damage * 1.5, 
                    color=(20, 150, 255)  # Brighter blue
                )
                
                left_projectile = BossProjectile(
                    self.rect.centerx, 
                    self.rect.centery, 
                    (left_dx, left_dy), 
                    1.4, 
                    self.damage * 1.5, 
                    color=(255, 0, 255)  # Magenta
                )
                
                right_projectile = BossProjectile(
                    self.rect.centerx, 
                    self.rect.centery, 
                    (right_dx, right_dy), 
                    1.4, 
                    self.damage * 1.5, 
                    color=(255, 165, 0)  # Orange
                )
                
                # Add to projectile group
                self.projectiles.add(center_projectile, left_projectile, right_projectile)
                
                return False
                
            # Level 5 boss - create orbiting projectiles when first spotted
            elif self.level == 5 and not self.orbiting_projectiles_created:
                print("Creating orbiting projectiles for Boss 5")
                
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
                    
                    # Color is ignored for orbiting projectiles which use the ghost sprite
                    color = (255, 0, 0)  # Placeholder color
                    
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
                        orbit_speed=0.015  # Angular velocity - reduced by 50%
                    )
                    
                    # Add to projectile group
                    self.projectiles.add(projectile)
                
                return True
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
        # Check if in blood puddle state and ready to resurrect
        if self.is_dead:
            current_time = pygame.time.get_ticks()
            
            # If it's time to resurrect
            if current_time >= self.resurrection_time:
                self.resurrect()
            
            # Skip the rest of the update if still in blood puddle state
            return
            
        # Calculate distance to player
        dx = player.rect.centerx - self.rect.centerx
        dy = player.rect.centery - self.rect.centery
        distance = math.sqrt(dx * dx + dy * dy)
        
        # Current time for cooldown calculations
        current_time = pygame.time.get_ticks()
        
        # Always mark that boss has spotted player if within detection range
        # For level 2 boss, increase detection range substantially
        detection_range = self.detection_range * 2 if self.level == 2 else self.detection_range
        
        if distance <= detection_range:
            # If Boss 5 spots the player for the first time, create orbiting projectiles
            if self.level == 5 and not self.has_spotted_player and not self.orbiting_projectiles_created:
                print("Boss 5 spotted player, creating orbiting projectiles")
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
                    
                    # Play the boss voice when leaving defensive mode
                    voice_file = f"effects/boss_{self.level}_voice"
                    self.sound_manager.play_sound(voice_file)
                    self.last_voice_time = current_time
                        
                    print(f"Level 4 boss leaving defensive mode at time {current_time}!")
        
        # Level 5 boss casting mode logic
        if self.level == 5 and self.has_spotted_player:
            if not self.casting_mode:
                # Check if it's time to activate casting mode
                time_since_last_cast = current_time - self.last_cast_time
                if time_since_last_cast >= self.casting_mode_cooldown:
                    # Activate casting mode
                    self.casting_mode = True
                    self.cast_complete = False
                    self.last_cast_time = current_time
                    print(f"Boss 5 entering casting mode at time {current_time}")
            else:
                # In casting mode
                time_in_casting = current_time - self.last_cast_time
                
                # Fire projectiles when casting starts
                if not self.cast_complete:
                    # Create 4 projectiles in random directions
                    self.cast_projectiles(player)
                    self.cast_complete = True
                
                # Check if casting is complete
                if time_in_casting >= self.casting_mode_duration:
                    # Deactivate casting mode
                    self.casting_mode = False
                    print(f"Boss 5 leaving casting mode at time {current_time}")
        
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
        elif self.has_spotted_player and not (self.level == 4 and self.defensive_mode) and not (self.level == 5 and self.casting_mode):
            # Chase state - always chase once spotted (unless level 4 boss in defensive mode or level 5 boss in casting mode)
            self.state = 'chase'
            self.current_state = 'walk'
            self.move_towards_player(player)
        else:
            # Idle state - stand still until player is spotted or if boss is in defensive/casting mode
            self.state = 'idle'
            self.current_state = 'idle'
            self.velocity_x = 0
            self.velocity_y = 0
        
        # If level 4 boss is in defensive mode or level 5 boss is in casting mode, ensure it doesn't move
        if (self.level == 4 and self.defensive_mode) or (self.level == 5 and self.casting_mode):
            self.velocity_x = 0
            self.velocity_y = 0
            self.state = 'idle'
            self.current_state = 'idle'
        
        # Store old position to handle collisions
        old_rect = self.rect.copy()
        
        # Horizontal movement - simplified with no half-step attempts
        self.rect.x += self.velocity_x
        
        # If collision occurs, try with half the velocity
        if hasattr(player, 'level') and player.level and player.level.check_collision(self.rect):
            self.rect.x = old_rect.x
            # Try to move vertically if horizontal movement is blocked
            if self.velocity_x != 0 and self.velocity_y == 0:
                # Try to move up or down to get around the obstacle
                if random.choice([True, False]):
                    self.velocity_y = self.speed * 0.5
                else:
                    self.velocity_y = -self.speed * 0.5
        
        # Vertical movement - simplified with no half-step attempts
        self.rect.y += self.velocity_y
        if hasattr(player, 'level') and player.level and player.level.check_collision(self.rect):
            # Simply revert if collision occurs
            self.rect.y = old_rect.y
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
        if not (self.level == 4 and self.defensive_mode):
            self.image = self.animations[self.current_state][self.facing][self.frame]
        
        # Update projectiles for level 2 and 5 bosses
        if self.level == 2 or self.level == 5:
            self.projectiles.update()
            
            # Check for collisions with player
            for projectile in self.projectiles:
                if projectile.check_collision(player.hitbox):
                    player.take_damage(projectile.damage)
                    # Only destroy non-orbiting projectiles
                    if not hasattr(projectile, 'is_orbiting') or not projectile.is_orbiting:
                        projectile.kill()
        
        # Handle boss voice sound effect
        if distance <= detection_range:
            if not self.has_seen_player:
                voice_file = f"effects/boss_{self.level}_voice"
                self.sound_manager.play_sound(voice_file)
                self.has_seen_player = True
                self.last_voice_time = current_time
                print(f"Level {self.level} boss spotted player - playing initial voice")
            # Only play the voice on cooldown for bosses other than level 4
            # For level 4 boss, we'll play it when exiting defensive mode instead
            elif self.level != 4 and current_time - self.last_voice_time >= self.voice_cooldown:
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

        # Check health-based special attack for non-level-2 bosses
        if self.level != 2:
            health_percent = self.health / self.enemy_data['health']
            original_attack_range = self.attack_range  # Store original attack range
            
            if health_percent < 0.3:
                self.attack_cooldown = 500
                self.speed = self.enemy_data['speed'] * 1.5
                self.damage = int(self.enemy_data['damage'] * 1.5)
                # Note: we deliberately do NOT increase attack_range here
                self.phase = 2  # High phase for damage calculation
                if random.random() < 0.05:
                    self.special_attack(player)
            elif health_percent < 0.6:
                self.attack_cooldown = 750
                self.speed = self.enemy_data['speed'] * 1.2
                self.damage = int(self.enemy_data['damage'] * 1.2)
                # Note: we deliberately do NOT increase attack_range here
                self.phase = 1  # Medium phase for damage calculation
                if random.random() < 0.03:
                    self.special_attack(player)
            else:
                self.phase = 0  # Base phase
                
            # Safety check to ensure attack range doesn't change
            if self.attack_range != original_attack_range:
                self.attack_range = original_attack_range

    def draw(self, surface):
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
            
            # Draw projectiles for level 2 and 5 bosses
            if self.level == 2 or self.level == 5:
                for projectile in self.projectiles:
                    projectile.draw(surface)
            
            # Draw health bar
            health_bar_width = 50  # Reduced from 60
            health_bar_height = 4  # Reduced from 6
            health_ratio = self.health / self.enemy_data['health']
            
            # Position health bar relative to the visual representation
            health_bar_x = draw_x + (self.image.get_width() - health_bar_width) // 2
            health_bar_y = draw_y - 10  # Moved closer to boss (was -12)
            
            pygame.draw.rect(surface, RED, (health_bar_x, health_bar_y,
                                          health_bar_width, health_bar_height))
            pygame.draw.rect(surface, GREEN, (health_bar_x, health_bar_y,
                                            health_bar_width * health_ratio, health_bar_height)) 

    def cast_projectiles(self, player):
        """Create projectiles that become stationary after a delay for Boss 5"""
        if self.level != 5:
            return
            
        # Create 4 projectiles in random directions
        for i in range(4):
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
                stationary_time=self.casting_mode_duration  # Become stationary after cast completes
            )
            
            # Set the stationary duration to match the cooldown
            projectile.stationary_duration = self.stationary_projectile_duration
            
            # Add to projectile group
            self.projectiles.add(projectile)
            
        print(f"Boss 5 cast 4 projectiles that will become stationary")