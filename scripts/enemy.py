import pygame
import math
import random
import os
import heapq
from config import *
from asset_manager import get_asset_manager
from sound_manager import get_sound_manager

class BossProjectile(pygame.sprite.Sprite):
    def __init__(self, x, y, direction, speed=1.4, damage=25, color=(255, 0, 0)):
        super().__init__()
        self.asset_manager = get_asset_manager()
        
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
        
        self.rect = self.image.get_rect()
        self.rect.centerx = x
        self.rect.centery = y
        
        # Movement properties
        self.direction = direction  # Tuple (dx, dy) - normalized direction
        self.speed = speed
        self.damage = damage
        self.distance_traveled = 0
        self.max_distance = TILE_SIZE * 10  # Projectiles disappear after traveling this distance
        
        # Add a pulsing effect
        self.pulse_counter = 0
        self.pulse_rate = 0.1
        self.original_image = self.image.copy()
        
    def update(self):
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
            
        # Update pulsing effect
        self.pulse_counter += self.pulse_rate
        scale_factor = 0.9 + 0.2 * abs(math.sin(self.pulse_counter))  # Oscillate between 0.9 and 1.1 size
        
        new_width = int(self.original_image.get_width() * scale_factor)
        new_height = int(self.original_image.get_height() * scale_factor)
        
        # Create a new scaled image for the pulse effect
        self.image = pygame.transform.scale(self.original_image, (new_width, new_height))
        
        # Keep the projectile centered
        old_center = self.rect.center
        self.rect = self.image.get_rect()
        self.rect.center = old_center
        
    def check_collision(self, player_rect):
        """Check if projectile collides with player"""
        if self.rect.colliderect(player_rect):
            return True
        return False

class Enemy(pygame.sprite.Sprite):
    def __init__(self, x, y, enemy_type, level, level_instance=None):
        super().__init__()
        self.asset_manager = get_asset_manager()
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
        self.attack_range = TILE_SIZE * 1.5
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
            # Idle state - enemies don't patrol, they stand still until they see the player
            self.state = 'idle'
            self.current_state = 'idle'
            self.velocity_x = 0
            self.velocity_y = 0
        
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
        
        # Draw health bar
        health_bar_width = 50
        health_bar_height = 5
        health_ratio = self.health / self.enemy_data['health']
        pygame.draw.rect(surface, RED, (self.rect.x, self.rect.y - 10,
                                      health_bar_width, health_bar_height))
        pygame.draw.rect(surface, GREEN, (self.rect.x, self.rect.y - 10,
                                        health_bar_width * health_ratio, health_bar_height))

class Boss(Enemy):
    def __init__(self, x, y, level, level_instance=None):
        super().__init__(x, y, None, level, level_instance)
        self.asset_manager = get_asset_manager()
        self.enemy_data = BOSS_TYPES[f'level{level}']
        self.level = level  # Explicitly save the level
        
        # Override stats with boss stats
        self.health = self.enemy_data['health']
        self.damage = self.enemy_data['damage']
        self.speed = self.enemy_data['speed']
        self.name = self.enemy_data['name']
        
        # Animation states and directions (override from Enemy)
        self.animations = {
            'idle': {},
            'walk': {},
            'attack': {},
            'special': {}  # Bosses have special attacks
        }
        
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
        else:
            self.max_phases = 3  # Default value for other bosses
            
        self.special_attack_cooldown = 3000  # 3 seconds
        self.last_special_attack_time = 0
        
        # For level 2 boss, adjust attack properties
        if level == 2:
            self.attack_range = TILE_SIZE * 1  # Reduced attack range to 1 tile
            self.attack_cooldown = 1500  # 1.5 seconds between attacks
        
        # Position history for trailing effect (used by level 1 boss)
        self.trail_enabled = level == 1 or level == 2  # Enable for level 1 and 2 bosses
        self.position_history = []
        self.max_trail_length = 5  # Store 5 previous positions
        self.trail_update_rate = 4  # Update trail every 4 frames
        self.trail_frame_counter = 0
        
        # Set trail color based on level
        self.trail_color = (150, 0, 0) if level == 1 else (0, 150, 150)  # Red for level 1, Cyan for level 2
        
        # Sound manager for boss voice
        self.sound_manager = get_sound_manager()
        
        # Boss voice related attributes
        self.has_seen_player = False
        self.last_voice_time = 0
        self.voice_cooldown = 4000  # 4 seconds (in milliseconds)
        
        # Projectiles for level 2 boss
        self.projectiles = pygame.sprite.Group()
        
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
        # Call the parent method to handle the actual damage
        return super().take_damage(amount)
        
    def special_attack(self, player):
        current_time = pygame.time.get_ticks()
        if current_time - self.last_special_attack_time >= self.special_attack_cooldown:
            self.last_special_attack_time = current_time
            # Switch to special attack animation
            self.current_state = 'special'
            self.frame = 0  # Reset animation frame
            
            # Level 2 boss has projectile attack
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
            else:
                # Other bosses use the original special attack
                damage_multiplier = 1 + (self.phase * 0.5)  # Damage increases with phase
                return player.take_damage(self.damage * damage_multiplier)
        return False
        
    def update(self, player):
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
            self.has_spotted_player = True
        
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
        elif self.has_spotted_player:
            # Chase state - always chase once spotted
            self.state = 'chase'
            self.current_state = 'walk'
            self.move_towards_player(player)
        else:
            # Idle state - stand still until player is spotted
            self.state = 'idle'
            self.current_state = 'idle'
            self.velocity_x = 0
            self.velocity_y = 0
        
        # Store old position to handle collisions
        old_rect = self.rect.copy()
        
        # Horizontal movement - simplified with no half-step attempts
        self.rect.x += self.velocity_x
        if hasattr(player, 'level') and player.level and player.level.check_collision(self.rect):
            # Simply revert if collision occurs
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
        
        # Update animation
        self.animation_time += self.animation_speed
        
        # If attack animation is done, go back to previous state
        if self.current_state == 'attack' and self.animation_time >= len(self.animations[self.current_state][self.facing]):
            self.current_state = 'idle' if self.state == 'idle' else 'walk'
            self.animation_time = 0
            
        # Calculate current frame
        self.frame = int(self.animation_time) % len(self.animations[self.current_state][self.facing])
        self.image = self.animations[self.current_state][self.facing][self.frame]
        
        # Update projectiles
        if self.level == 2:
            self.projectiles.update()
            
            # Check for collisions with player
            for projectile in self.projectiles:
                if projectile.check_collision(player.hitbox):
                    player.take_damage(projectile.damage)
                    projectile.kill()
        
        # Handle boss voice sound effect
        if distance <= detection_range:
            if not self.has_seen_player:
                voice_file = f"effects/boss_{self.level}_voice"
                self.sound_manager.play_sound(voice_file)
                self.has_seen_player = True
                self.last_voice_time = current_time
            elif current_time - self.last_voice_time >= self.voice_cooldown:
                voice_file = f"effects/boss_{self.level}_voice"
                self.sound_manager.play_sound(voice_file)
                self.last_voice_time = current_time
        
        # Update position history for trailing effect
        if self.trail_enabled:
            self.trail_frame_counter += 1
            if self.trail_frame_counter >= self.trail_update_rate:
                self.trail_frame_counter = 0
                visual_pos_x = self.rect.centerx
                visual_pos_y = self.rect.centery
                self.position_history.append((visual_pos_x, visual_pos_y))
                
                if len(self.position_history) > self.max_trail_length:
                    self.position_history.pop(0)
        
        # Check health-based special attack for non-level-2 bosses
        if self.level != 2:
            health_percent = self.health / self.enemy_data['health']
            
            if health_percent < 0.3:
                self.attack_cooldown = 500
                self.speed = self.enemy_data['speed'] * 1.5
                self.damage = int(self.enemy_data['damage'] * 1.5)
                if random.random() < 0.05:
                    self.special_attack(player)
            elif health_percent < 0.6:
                self.attack_cooldown = 750
                self.speed = self.enemy_data['speed'] * 1.2
                self.damage = int(self.enemy_data['damage'] * 1.2)
                if random.random() < 0.03:
                    self.special_attack(player)

    def draw(self, surface):
        # Draw the boss character
        # Calculate position with visual offset
        draw_x = self.rect.x - self.visual_offset_x
        draw_y = self.rect.y - self.visual_offset_y
        
        # Draw boss character
        surface.blit(self.image, (draw_x, draw_y))
        
        # Draw trailing effect for level 1 and 2 bosses
        if self.trail_enabled and self.position_history:
            # Draw position history for trailing effect
            for i, (hist_x, hist_y) in enumerate(reversed(self.position_history)):
                # Calculate size of trail dot based on position in history
                # Make the most recent ones bigger
                size = max(5, 15 - (i * 2))
                
                # Calculate alpha (transparency) based on position in history
                # Make the oldest ones more transparent
                alpha = max(20, 150 - (i * 15))
                
                # Create a surface for the trail dot with alpha channel
                dot_surface = pygame.Surface((size, size), pygame.SRCALPHA)
                
                # Set the color with alpha
                color_with_alpha = (*self.trail_color, alpha)
                
                # Draw the circle on the dot surface
                pygame.draw.circle(dot_surface, color_with_alpha, (size//2, size//2), size//2)
                
                # Blit the dot to the main surface
                surface.blit(dot_surface, (hist_x - size//2, hist_y - size//2))
                
        # Draw projectiles for level 2 boss
        if self.level == 2:
            for projectile in self.projectiles:
                surface.blit(projectile.image, projectile.rect)
                
        # Uncomment to show boss hitbox for debugging
        # pygame.draw.rect(surface, (255, 0, 0), self.rect, 1)
        
        # Draw health bar
        health_bar_width = 60  # Wider than regular enemies
        health_bar_height = 6
        health_ratio = self.health / self.enemy_data['health']
        
        # Position health bar relative to the visual representation
        health_bar_x = draw_x + (self.image.get_width() - health_bar_width) // 2
        health_bar_y = draw_y - 12
        
        pygame.draw.rect(surface, RED, (health_bar_x, health_bar_y,
                                      health_bar_width, health_bar_height))
        pygame.draw.rect(surface, GREEN, (health_bar_x, health_bar_y,
                                        health_bar_width * health_ratio, health_bar_height)) 