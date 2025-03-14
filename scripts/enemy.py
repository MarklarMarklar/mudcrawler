import pygame
import math
import random
import os
import heapq
from config import *
from asset_manager import get_asset_manager
from sound_manager import get_sound_manager

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
                # Continue to next iteration
                if self.path:
                    next_point = self.path[0]
                    dx = next_point[0] - self.rect.centerx
                    dy = next_point[1] - self.rect.centery
                    distance = math.sqrt(dx * dx + dy * dy)
            
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
        
        # Update state based on distance to player
        if distance <= self.attack_range:
            self.state = 'attack'
            self.velocity_x = 0
            self.velocity_y = 0
            self.attack(player)
            self.has_spotted_player = True  # Mark that enemy has spotted player
        elif distance <= self.detection_range or self.has_spotted_player:
            # If within detection range OR has already spotted player, chase
            self.state = 'chase'
            self.current_state = 'walk'
            self.move_towards_player(player)
            
            # Mark that this enemy has spotted the player
            if distance <= self.detection_range:
                self.has_spotted_player = True
        else:
            # When player is out of detection range and hasn't been spotted yet, patrol
            self.state = 'patrol'
            self.patrol()
            
        # Store the old position to revert if collision happens
        old_rect = self.rect.copy()
        old_velocity_x = self.velocity_x
        old_velocity_y = self.velocity_y
        
        # Ensure player has level attribute before checking collision
        has_level = hasattr(player, 'level') and player.level is not None
        
        # Move horizontally first
        self.rect.x += self.velocity_x
        
        # If this would cause a collision, revert the horizontal movement
        if has_level and player.level.check_collision(self.rect):
            # Reset position to before movement
            self.rect = old_rect.copy()
            self.velocity_x = 0  # Reset velocity
            
            # If we're chasing the player, this counts as a movement failure
            if self.state == 'chase':
                self.movement_failed_counter += 1
            
            # If we hit a wall while patrolling, change direction
            if self.state == 'patrol' and not self.is_patrol_paused:
                # Choose a new direction perpendicular to the current one
                if self.patrol_direction in ['left', 'right']:
                    self.patrol_direction = random.choice(['up', 'down'])
                else:
                    self.patrol_direction = random.choice(['left', 'right'])
        else:
            # Movement succeeded, reset failure counter
            if old_velocity_x != 0 and self.state == 'chase':
                self.movement_failed_counter = 0
        
        # Now try to move vertically
        self.rect.y += self.velocity_y
        
        # If this would cause a collision, revert the vertical movement
        if has_level and player.level.check_collision(self.rect):
            # Reset position to before movement
            self.rect = old_rect.copy()
            self.velocity_y = 0  # Reset velocity
            
            # If we're chasing the player, this counts as a movement failure
            if self.state == 'chase':
                self.movement_failed_counter += 1
            
            # If we hit a wall while patrolling, change direction
            if self.state == 'patrol' and not self.is_patrol_paused:
                # Choose a new direction perpendicular to the current one
                if self.patrol_direction in ['up', 'down']:
                    self.patrol_direction = random.choice(['left', 'right'])
                else:
                    self.patrol_direction = random.choice(['up', 'down'])
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
        self.max_phases = 3
        self.special_attack_cooldown = 3000  # 3 seconds
        self.last_special_attack_time = 0
        
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
            
            # Implement unique boss attacks here
            damage_multiplier = 1 + (self.phase * 0.5)  # Damage increases with phase
            return player.take_damage(self.damage * damage_multiplier)
        return False
        
    def move_towards_player(self, player):
        """Move towards player using enhanced pathfinding for boss"""
        # Check if we need to update the path
        target_pos = (player.rect.centerx, player.rect.centery)
        
        # Bosses update their path more frequently and with more aggressive parameters
        should_update_path = (
            not self.path or 
            (self.last_target_position and 
             ((abs(self.last_target_position[0] - target_pos[0]) > TILE_SIZE) or  # More sensitive to player movement
              (abs(self.last_target_position[1] - target_pos[1]) > TILE_SIZE))) or
            self.path_update_timer >= (self.path_update_frequency // 2) or  # Update twice as frequently
            self.movement_failed_counter >= (self.max_movement_failures // 2)  # Less tolerant of failures
        )
        
        if should_update_path and hasattr(player, 'level'):
            # Find path to player with enhanced options for boss
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
                # If path is now empty, recalculate immediately for bosses
                if not self.path:
                    self.path = self.find_path(
                        self.rect.centerx, 
                        self.rect.centery, 
                        player.rect.centerx, 
                        player.rect.centery,
                        player.level
                    )
                    
                    # If we still couldn't find a path, use direct movement
                    if not self.path:
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
                # Continue to next iteration if we have more path points
                if self.path:
                    next_point = self.path[0]
                    dx = next_point[0] - self.rect.centerx
                    dy = next_point[1] - self.rect.centery
                    distance = math.sqrt(dx * dx + dy * dy)
            
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
            # If no path found, try to move directly towards player
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

    def update(self, player):
        # Override the standard update method to prevent patrolling
        
        # Calculate distance to player
        dx = player.rect.centerx - self.rect.centerx
        dy = player.rect.centery - self.rect.centery
        distance = math.sqrt(dx * dx + dy * dy)
        
        # Current time for cooldown calculations
        current_time = pygame.time.get_ticks()
        
        # Update state based on distance to player
        if distance <= self.attack_range:
            # Attack state - same as regular enemies
            self.state = 'attack'
            self.velocity_x = 0
            self.velocity_y = 0
            self.attack(player)
            self.has_spotted_player = True  # Mark that boss has spotted player
        elif distance <= self.detection_range or self.has_spotted_player:
            # Chase state - same as regular enemies
            self.state = 'chase'
            self.current_state = 'walk'
            self.move_towards_player(player)
            
            # Mark that this boss has spotted the player
            if distance <= self.detection_range:
                self.has_spotted_player = True
        else:
            # Idle state - bosses don't patrol, they stand still until they see the player
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
        
        # Keep boss on screen
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
        
        # Handle boss voice sound effect
        if distance <= self.detection_range:
            # Boss has detected the player
            if not self.has_seen_player:
                # First time seeing player, play voice sound
                voice_file = f"effects/boss_{self.level}_voice"
                self.sound_manager.play_sound(voice_file)
                self.has_seen_player = True
                self.last_voice_time = current_time
                print(f"Boss has seen the player! Playing voice sound: {voice_file}")
            elif current_time - self.last_voice_time >= self.voice_cooldown:
                # Repeat the voice sound every 4 seconds
                voice_file = f"effects/boss_{self.level}_voice"
                self.sound_manager.play_sound(voice_file)
                self.last_voice_time = current_time
                print(f"Boss repeating voice sound: {voice_file}")
        
        # Update position history for trailing effect if enabled
        if self.trail_enabled:
            self.trail_frame_counter += 1
            if self.trail_frame_counter >= self.trail_update_rate:
                self.trail_frame_counter = 0
                # Store current position and image
                # Store the visual position (collision rect center adjusted for the visual offset)
                visual_pos_x = self.rect.x - self.visual_offset_x
                visual_pos_y = self.rect.y - self.visual_offset_y
                self.position_history.append({
                    'pos': (visual_pos_x, visual_pos_y),
                    'image': self.image,
                    'frame': self.frame,
                    'state': self.current_state,
                    'facing': self.facing
                })
                # Keep only the most recent positions
                if len(self.position_history) > self.max_trail_length:
                    self.position_history.pop(0)
        
        # Check for special attack conditions based on health percentage
        health_percent = self.health / self.enemy_data['health']
        
        if health_percent < 0.3:
            # Low health - more aggressive, faster, special attacks more often
            self.attack_cooldown = 500  # ms
            self.speed = self.enemy_data['speed'] * 1.5
            self.damage = int(self.enemy_data['damage'] * 1.5)
            
            # Chance to do special attack
            if random.random() < 0.05:
                self.special_attack(player)
        elif health_percent < 0.6:
            # Medium health - somewhat aggressive
            self.attack_cooldown = 750  # ms
            self.speed = self.enemy_data['speed'] * 1.2
            self.damage = int(self.enemy_data['damage'] * 1.2)
            
            # Lower chance for special attack
            if random.random() < 0.03:
                self.special_attack(player)
        
    def draw(self, surface):
        # Draw trailing effect if enabled (for level 1 boss)
        if self.trail_enabled and self.position_history:
            # Draw trails from oldest to newest with increasing opacity
            for i, pos_data in enumerate(self.position_history):
                # Calculate alpha based on position in history (oldest = most transparent)
                alpha = int(((i + 1) / self.max_trail_length) * 180)  # Max alpha of 180 (semi-transparent)
                
                # Get the image for this trail position
                trail_image = pos_data['image']
                
                # Create a copy of the image with adjusted alpha
                ghost_image = trail_image.copy()
                ghost_image.set_alpha(alpha)
                
                # Create a colored trail effect
                if hasattr(self, 'trail_color'):
                    # Create a surface the same size as the trail image
                    colored_surface = pygame.Surface(ghost_image.get_size(), pygame.SRCALPHA)
                    # Fill with the trail color
                    colored_surface.fill((*self.trail_color, alpha))
                    # Apply the colored surface using a mask of the ghost image
                    ghost_image.blit(colored_surface, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
                
                # Draw the ghost image at the historical position (already contains visual offset)
                pos = pos_data['pos']
                surface.blit(ghost_image, pos)
        
        # Calculate draw position (visual position, not collision box)
        draw_pos = (self.rect.x - self.visual_offset_x, self.rect.y - self.visual_offset_y)
        
        # Draw the current image (fully opaque) at the adjusted position
        surface.blit(self.image, draw_pos)
        
        # Draw health bar
        health_bar_width = 60  # Wider than regular enemies
        health_bar_height = 6
        health_ratio = self.health / self.enemy_data['health']
        
        # Position health bar relative to the visual representation
        health_bar_x = draw_pos[0] + (self.image.get_width() - health_bar_width) // 2
        health_bar_y = draw_pos[1] - 12
        
        pygame.draw.rect(surface, RED, (health_bar_x, health_bar_y,
                                      health_bar_width, health_bar_height))
        pygame.draw.rect(surface, GREEN, (health_bar_x, health_bar_y,
                                        health_bar_width * health_ratio, health_bar_height)) 