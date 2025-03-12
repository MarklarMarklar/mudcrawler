import pygame
import random
import os
import math
import glob
from config import *
from enemy import Enemy, Boss
from asset_manager import get_asset_manager

class ArrowPickup:
    """Arrow pickup item that gives the player additional arrows"""
    def __init__(self, x, y):
        self.x = x
        self.y = y
        # Create a simple arrow shape
        self.size = TILE_SIZE // 2
        self.rect = pygame.Rect(x - self.size//2, y - self.size//2, self.size, self.size)
        self.arrow_amount = 2  # Each pickup gives 2 arrows
        self.collected = False
        self.pulse_timer = 0
        self.asset_manager = get_asset_manager()
        
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
        
    def update(self):
        # Simple animation effect
        self.pulse_timer += 0.1
        
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
                surface.blit(scaled_texture, (self.x - size//2, self.y - size//2))
            else:
                # Draw a simple arrow shape as fallback
                arrow_surf = pygame.Surface((size, size), pygame.SRCALPHA)
                
                # Arrow body (brown with yellowish tip)
                pygame.draw.rect(arrow_surf, (150, 100, 50), (size//4, size//2-2, size//2, 4))
                pygame.draw.polygon(arrow_surf, (255, 215, 0), 
                                  [(size*3//4, size//2-4), (size, size//2), (size*3//4, size//2+4)])
                
                # Add a glow
                glow_surf = pygame.Surface((size*1.5, size*1.5), pygame.SRCALPHA)
                pygame.draw.circle(glow_surf, (255, 255, 150, 50), (size*1.5//2, size*1.5//2), size*1.5//2)
                surface.blit(glow_surf, (self.x - size*1.5//2, self.y - size*1.5//2))
                
                # Draw the arrow
                surface.blit(arrow_surf, (self.x - size//2, self.y - size//2))
        except Exception as e:
            print(f"Error drawing arrow pickup: {e}")

class HealthPickup:
    """Health pickup item that restores player health"""
    def __init__(self, x, y):
        self.x = x
        self.y = y
        # Create a simple heart shape
        self.size = TILE_SIZE // 2
        self.rect = pygame.Rect(x - self.size//2, y - self.size//2, self.size, self.size)
        self.heal_amount = 20  # Flat 20 HP instead of percentage-based healing
        self.collected = False
        self.pulse_timer = 0
        self.asset_manager = get_asset_manager()
        
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
        
    def update(self):
        # Simple animation effect
        self.pulse_timer += 0.1
        
    def draw(self, surface):
        if self.collected:
            return
            
        try:
            # Pulsing effect
            pulse = math.sin(self.pulse_timer) * 0.2 + 0.8
            size = int(self.size * pulse)
            
            # Draw health pickup
            if hasattr(self, 'health_texture') and self.health_texture:
                # Scale the texture based on pulse
                scaled_texture = pygame.transform.scale(self.health_texture, (size, size))
                surface.blit(scaled_texture, (self.x - size//2, self.y - size//2))
                
                # Add a glow effect
                glow_surf = pygame.Surface((size*1.5, size*1.5), pygame.SRCALPHA)
                pygame.draw.circle(glow_surf, (255, 100, 100, 50), (size*1.5//2, size*1.5//2), size*1.5//2)
                surface.blit(glow_surf, (self.x - size*1.5//2, self.y - size*1.5//2))
            else:
                # Fallback to drawing the heart shape
                heart_surf = pygame.Surface((size, size), pygame.SRCALPHA)
                
                # Brighter red in the center fading to darker red
                inner_color = (255, 50, 50)
                outer_color = (180, 0, 0)
                
                # Draw the heart shape
                heart_points = [
                    (size//2, size//5),
                    (size*4//5, size//3),
                    (size*4//5, size*2//3),
                    (size//2, size*4//5),
                    (size//5, size*2//3),
                    (size//5, size//3),
                ]
                pygame.draw.polygon(heart_surf, outer_color, heart_points)
                
                # Add a glow
                glow_surf = pygame.Surface((size*1.5, size*1.5), pygame.SRCALPHA)
                pygame.draw.circle(glow_surf, (255, 100, 100, 50), (size*1.5//2, size*1.5//2), size*1.5//2)
                surface.blit(glow_surf, (self.x - size*1.5//2, self.y - size*1.5//2))
                
                # Draw the heart
                surface.blit(heart_surf, (self.x - size//2, self.y - size//2))
        except Exception as e:
            print(f"Error drawing health pickup: {e}")

class Room:
    """Represents a single room in a dungeon level"""
    def __init__(self, x, y, level_number, room_type='normal'):
        # Position in the level grid (not pixels)
        self.grid_x = x
        self.grid_y = y
        
        # Room properties
        self.level_number = level_number
        self.room_type = room_type  # 'normal', 'start', 'boss', 'treasure'
        self.width = ROOM_WIDTH
        self.height = ROOM_HEIGHT
        self.tiles = []
        self.destroyable_walls = []  # Track destroyable walls
        
        # Doors - each can be True (open) or False (closed/no door)
        self.doors = {
            'north': False,
            'east': False,
            'south': False,
            'west': False
        }
        
        # Enemy spawning
        self.enemies = pygame.sprite.Group()
        self.boss = None
        self.cleared = False  # Room is cleared when all enemies are defeated
        
        # Level exit
        self.has_exit = False
        self.exit_position = None
        
        # Key drop
        self.key_dropped = False
        self.key_position = None
        self.key_picked_up = False  # New flag to track if key was already picked up
        
        # Health pickups
        self.health_pickups = []
        self.arrow_pickups = []
        
        # Generate room layout
        self.generate_room()
        
    def generate_room(self):
        """Generate the room layout based on room type"""
        # Create basic room layout - all walls
        self.tiles = [[1 for x in range(self.width)] for y in range(self.height)]
        self.destroyable_walls = [[False for x in range(self.width)] for y in range(self.height)]
        
        # Create open area with some random walls
        for y in range(1, self.height - 1):
            for x in range(1, self.width - 1):
                # Edges of the room are always floor
                if (x == 1 or x == self.width - 2 or y == 1 or y == self.height - 2):
                    self.tiles[y][x] = 0
                # Inner part has random walls (less chance of walls than before)
                elif random.random() < 0.25:  # 25% chance of wall
                    self.tiles[y][x] = 1
                    
                    # 20% chance that a wall is destroyable
                    if random.random() < 0.2:
                        self.destroyable_walls[y][x] = True
                else:
                    self.tiles[y][x] = 0
                    
        # Add doors based on door configuration
        if self.doors['north']:
            # North door - middle of top wall
            door_x = self.width // 2
            self.tiles[0][door_x] = 2  # Door tile
            # Make sure there's a clear path from the door (2x2 area)
            for y in range(1, 4):  # 3 tiles deep
                for x in range(door_x - 1, door_x + 2):  # 3 tiles wide
                    if 0 <= y < self.height and 0 <= x < self.width:
                        self.tiles[y][x] = 0  # Floor tile
            
        if self.doors['south']:
            # South door - middle of bottom wall
            door_x = self.width // 2
            self.tiles[self.height - 1][door_x] = 2  # Door tile
            # Make sure there's a clear path from the door (2x2 area)
            for y in range(self.height - 4, self.height - 1):  # 3 tiles deep
                for x in range(door_x - 1, door_x + 2):  # 3 tiles wide
                    if 0 <= y < self.height and 0 <= x < self.width:
                        self.tiles[y][x] = 0  # Floor tile
            
        if self.doors['east']:
            # East door - middle of right wall
            door_y = self.height // 2
            self.tiles[door_y][self.width - 1] = 2  # Door tile
            # Make sure there's a clear path from the door (2x2 area)
            for y in range(door_y - 1, door_y + 2):  # 3 tiles high
                for x in range(self.width - 4, self.width - 1):  # 3 tiles deep
                    if 0 <= y < self.height and 0 <= x < self.width:
                        self.tiles[y][x] = 0  # Floor tile
            
        if self.doors['west']:
            # West door - middle of left wall
            door_y = self.height // 2
            self.tiles[door_y][0] = 2  # Door tile
            # Make sure there's a clear path from the door (2x2 area)
            for y in range(door_y - 1, door_y + 2):  # 3 tiles high
                for x in range(1, 4):  # 3 tiles deep
                    if 0 <= y < self.height and 0 <= x < self.width:
                        self.tiles[y][x] = 0  # Floor tile
            
        # Special handling for room types
        if self.room_type == 'start':
            # Start room - make sure center area is clear
            center_x, center_y = self.width // 2, self.height // 2
            for y in range(center_y - 2, center_y + 3):
                for x in range(center_x - 2, center_x + 3):
                    if 0 <= y < self.height and 0 <= x < self.width:
                        self.tiles[y][x] = 0
        elif self.room_type == 'boss':
            # Boss room - large open area with some obstacles
            center_x, center_y = self.width // 2, self.height // 2
            # Clear center area
            for y in range(1, self.height - 1):
                for x in range(1, self.width - 1):
                    self.tiles[y][x] = 0
            
            # Add some random pillars
            for _ in range(4):
                px = random.randint(3, self.width - 4)
                py = random.randint(3, self.height - 4)
                self.tiles[py][px] = 1
                self.tiles[py+1][px] = 1
                self.tiles[py][px+1] = 1
                self.tiles[py+1][px+1] = 1
                
                # 25% chance that pillars are destroyable
                if random.random() < 0.25:
                    self.destroyable_walls[py][px] = True
                    self.destroyable_walls[py+1][px] = True
                    self.destroyable_walls[py][px+1] = True
                    self.destroyable_walls[py+1][px+1] = True
        elif self.room_type == 'treasure':
            # Treasure room - some obstacles with treasure in the middle
            # Clear most areas
            for y in range(1, self.height - 1):
                for x in range(1, self.width - 1):
                    self.tiles[y][x] = 0
                    
            # Add a few walls in corners
            for corner_x, corner_y in [(2, 2), (2, self.height-3), (self.width-3, 2), (self.width-3, self.height-3)]:
                for dy in range(3):
                    for dx in range(3):
                        if random.random() < 0.7:
                            self.tiles[corner_y + dy][corner_x + dx] = 1
                            
                            # 30% chance that walls in treasure rooms are destroyable
                            if random.random() < 0.3:
                                self.destroyable_walls[corner_y + dy][corner_x + dx] = True
        
    def try_destroy_wall(self, x, y):
        """Try to destroy a wall at the given tile position"""
        # Check if position is within bounds
        if not (0 <= y < self.height and 0 <= x < self.width):
            return False
        
        # Check if there's a destroyable wall at this position
        if self.tiles[y][x] == 1 and self.destroyable_walls[y][x]:
            # Destroy the wall
            self.tiles[y][x] = 0
            self.destroyable_walls[y][x] = False
            
            # Determine what kind of pickup to spawn
            pickup_roll = random.random()
            center_x = x * TILE_SIZE + TILE_SIZE // 2
            center_y = y * TILE_SIZE + TILE_SIZE // 2
            
            # 30% chance to spawn a health pickup
            if pickup_roll < 0.3:
                self.health_pickups.append(HealthPickup(center_x, center_y))
                print(f"Health pickup spawned at {center_x}, {center_y} from destroyed wall")
            # 20% chance to spawn an arrow pickup
            elif pickup_roll < 0.5:
                self.arrow_pickups.append(ArrowPickup(center_x, center_y))
                print(f"Arrow pickup spawned at {center_x}, {center_y} from destroyed wall")
                
            return True
        
        # Wall was not destroyed
        return False
        
    def try_pickup_health(self, player_rect):
        """Check if player is touching a health pickup"""
        for pickup in self.health_pickups:
            if not pickup.collected and pickup.rect.colliderect(player_rect):
                pickup.collected = True
                print(f"Health pickup collected")
                return pickup.heal_amount
                
        return 0
        
    def try_pickup_arrows(self, player_rect):
        """Check if player is touching an arrow pickup"""
        arrow_amount = 0
        try:
            for pickup in self.arrow_pickups:
                if not pickup.collected and pickup.rect.colliderect(player_rect):
                    pickup.collected = True
                    print(f"Arrow pickup collected")
                    arrow_amount = pickup.arrow_amount
                    break
        except Exception as e:
            print(f"Error in try_pickup_arrows: {e}")
        return arrow_amount
        
    def spawn_enemies(self, num_enemies, level_instance=None):
        """Spawn enemies in the room based on level number"""
        attempts = 0
        max_attempts = 100  # Prevent infinite loops
        
        for _ in range(num_enemies):
            spawned = False
            attempts = 0
            
            while not spawned and attempts < max_attempts:
                tile_x = random.randint(1, self.width - 2)
                tile_y = random.randint(1, self.height - 2)
                
                # Only spawn on floor tiles away from doors
                if self.tiles[tile_y][tile_x] == 0 and not self.near_door(tile_x, tile_y):
                    enemy = Enemy(tile_x * TILE_SIZE, tile_y * TILE_SIZE, None, self.level_number, level_instance)
                    self.enemies.add(enemy)
                    spawned = True
                
                attempts += 1
                    
    def spawn_boss(self, level_instance=None):
        """Spawn a boss in the room (for boss rooms only)"""
        if self.room_type != 'boss':
            return
            
        # Boss spawns in the center of the room
        center_x = (self.width // 2) * TILE_SIZE
        center_y = (self.height // 2) * TILE_SIZE
        self.boss = Boss(center_x, center_y, self.level_number, level_instance)
        
    def near_door(self, tile_x, tile_y):
        """Check if a tile is near a door"""
        # Check for north door
        if self.doors['north'] and tile_y < 3 and abs(tile_x - self.width // 2) < 2:
            return True
            
        # Check for south door
        if self.doors['south'] and tile_y > self.height - 4 and abs(tile_x - self.width // 2) < 2:
            return True
            
        # Check for east door
        if self.doors['east'] and tile_x > self.width - 4 and abs(tile_y - self.height // 2) < 2:
            return True
            
        # Check for west door
        if self.doors['west'] and tile_x < 3 and abs(tile_y - self.height // 2) < 2:
            return True
            
        return False
        
    def is_valid_spawn_position(self, pixel_x, pixel_y):
        """Check if position is valid for spawning"""
        tile_x = pixel_x // TILE_SIZE
        tile_y = pixel_y // TILE_SIZE
        
        # Check if position is within bounds
        if tile_y < 0 or tile_y >= self.height or tile_x < 0 or tile_x >= self.width:
            return False
            
        # Check if position is a floor tile
        if self.tiles[tile_y][tile_x] != 0:
            return False
            
        # Check distance from enemies
        for enemy in self.enemies:
            dx = enemy.rect.x - pixel_x
            dy = enemy.rect.y - pixel_y
            if (dx * dx + dy * dy) < (TILE_SIZE * 3) * (TILE_SIZE * 3):
                return False
                
        return True
        
    def get_valid_player_position(self):
        """Find a valid position for the player to spawn in this room"""
        # For start room, use center
        if self.room_type == 'start':
            return (self.width // 2) * TILE_SIZE + TILE_SIZE // 2, (self.height // 2) * TILE_SIZE + TILE_SIZE // 2
            
        # For door transitions, place player just inside the appropriate door
        # This will be used when transitioning between rooms
        
        # For new rooms, find any valid floor tile
        for y in range(1, self.height - 1):
            for x in range(1, self.width - 1):
                if self.tiles[y][x] == 0:
                    # Return the center of the tile
                    return x * TILE_SIZE + TILE_SIZE // 2, y * TILE_SIZE + TILE_SIZE // 2
                    
        # Fallback - shouldn't happen
        return (self.width // 2) * TILE_SIZE, (self.height // 2) * TILE_SIZE
        
    def update(self, player):
        """Update entities in the room"""
        # Update enemies
        for enemy in self.enemies:
            enemy.update(player)
        
        # Update boss if present
        if self.boss and self.boss.health > 0:
            self.boss.update(player)
        elif self.boss and self.boss.health <= 0:
            # Boss is defeated, drop the key
            self.drop_key()
            
        # Check for enemy deaths
        for enemy in list(self.enemies):
            if enemy.health <= 0:
                pickup_roll = random.random()
                
                # 10% chance to drop a health pickup when enemy dies
                if pickup_roll < 0.1:
                    self.health_pickups.append(HealthPickup(enemy.rect.centerx, enemy.rect.centery))
                    print(f"Health pickup spawned from defeated enemy at {enemy.rect.centerx}, {enemy.rect.centery}")
                # 8% chance to drop an arrow pickup when enemy dies
                elif pickup_roll < 0.18:
                    self.arrow_pickups.append(ArrowPickup(enemy.rect.centerx, enemy.rect.centery))
                    print(f"Arrow pickup spawned from defeated enemy at {enemy.rect.centerx}, {enemy.rect.centery}")
                    
                enemy.kill()
                
        # Update pickups
        for pickup in self.health_pickups:
            pickup.update()
            
        for pickup in self.arrow_pickups:
            pickup.update()
        
        # Check if room is cleared
        if len(self.enemies) == 0 and (not self.boss or self.boss.health <= 0):
            self.cleared = True
            
    def check_collision(self, rect):
        """Check if a rectangle collides with walls in this room"""
        tile_x1 = max(0, rect.left // TILE_SIZE)
        tile_x2 = min(self.width - 1, rect.right // TILE_SIZE)
        tile_y1 = max(0, rect.top // TILE_SIZE)
        tile_y2 = min(self.height - 1, rect.bottom // TILE_SIZE)
        
        for y in range(tile_y1, tile_y2 + 1):
            for x in range(tile_x1, tile_x2 + 1):
                if 0 <= y < self.height and 0 <= x < self.width:
                    if self.tiles[y][x] == 1:  # Wall tile
                        wall_rect = pygame.Rect(x * TILE_SIZE, y * TILE_SIZE,
                                              TILE_SIZE, TILE_SIZE)
                        if rect.colliderect(wall_rect):
                            return True
        return False
        
    def check_door_collision(self, rect):
        """Check if player is touching a door, return direction if yes"""
        tile_x1 = max(0, rect.left // TILE_SIZE)
        tile_x2 = min(self.width - 1, rect.right // TILE_SIZE)
        tile_y1 = max(0, rect.top // TILE_SIZE)
        tile_y2 = min(self.height - 1, rect.bottom // TILE_SIZE)
        
        for y in range(tile_y1, tile_y2 + 1):
            for x in range(tile_x1, tile_x2 + 1):
                if 0 <= y < self.height and 0 <= x < self.width:
                    if self.tiles[y][x] == 2:  # Door tile
                        door_rect = pygame.Rect(x * TILE_SIZE, y * TILE_SIZE,
                                             TILE_SIZE, TILE_SIZE)
                        if rect.colliderect(door_rect):
                            # Determine which door was touched
                            if y == 0:
                                return 'north'
                            elif y == self.height - 1:
                                return 'south'
                            elif x == 0:
                                return 'west'
                            elif x == self.width - 1:
                                return 'east'
        return None

    def draw(self, surface, tile_images, level):
        """Draw the room and its contents"""
        # Draw tiles
        for y in range(self.height):
            for x in range(self.width):
                tile_x = x * TILE_SIZE
                tile_y = y * TILE_SIZE
                
                if self.tiles[y][x] == 1:  # Wall
                    if self.destroyable_walls[y][x] and level and level.destroyable_wall_textures:
                        # Randomly select a destroyable wall texture if not already cached
                        # We'll use a consistent hash based on the coordinates to keep the same texture
                        # for the same wall tile within a session
                        texture_index = hash(f"{self.grid_x}_{self.grid_y}_{x}_{y}") % len(level.destroyable_wall_textures)
                        destroyable_wall_texture = level.destroyable_wall_textures[texture_index]
                        
                        try:
                            # Load and draw the destroyable wall texture
                            if os.path.exists(destroyable_wall_texture):
                                texture = level.asset_manager.load_image(destroyable_wall_texture, scale=(TILE_SIZE, TILE_SIZE))
                                surface.blit(texture, (tile_x, tile_y))
                            else:
                                # Fallback to regular wall if texture loading fails
                                surface.blit(tile_images['wall'], (tile_x, tile_y))
                        except Exception as e:
                            print(f"Error loading destroyable wall texture: {e}")
                            surface.blit(tile_images['wall'], (tile_x, tile_y))
                    else:
                        # Regular wall
                        surface.blit(tile_images['wall'], (tile_x, tile_y))
                elif self.tiles[y][x] == 2:  # Door
                    surface.blit(tile_images['door'], (tile_x, tile_y))
                elif self.tiles[y][x] == EXIT_DOOR_TILE:  # Exit door
                    surface.blit(tile_images['exit'], (tile_x, tile_y))
                else:  # Floor
                    surface.blit(tile_images['floor'], (tile_x, tile_y))
                    
                # Draw room type indicators
                if self.room_type == 'boss' and x == self.width // 2 and y == 1:
                    # Boss room indicator
                    indicator = pygame.Surface((TILE_SIZE, TILE_SIZE))
                    indicator.fill((255, 0, 0))
                    indicator.set_alpha(50)
                    surface.blit(indicator, (tile_x, tile_y))
                elif self.room_type == 'treasure' and x == self.width // 2 and y == 1:
                    # Treasure room indicator
                    indicator = pygame.Surface((TILE_SIZE, TILE_SIZE))
                    indicator.fill((255, 215, 0))
                    indicator.set_alpha(50)
                    surface.blit(indicator, (tile_x, tile_y))
                    
        # Draw key if dropped
        if self.key_dropped and self.key_position:
            # Draw a more visible key with glow effect
            # First draw a glow effect
            glow_size = TILE_SIZE * 1.5
            # Make the glow pulse based on time
            pulse_factor = 0.5 + 0.5 * abs(math.sin(pygame.time.get_ticks() / 200))
            glow_color = (255, 255, 100, int(150 * pulse_factor))
            glow_surface = pygame.Surface((glow_size, glow_size), pygame.SRCALPHA)
            pygame.draw.circle(glow_surface, glow_color, (glow_size/2, glow_size/2), glow_size/2)
            surface.blit(glow_surface, (self.key_position[0] - glow_size/2, self.key_position[1] - glow_size/2))
            
            # Then draw the key
            key_surface = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
            # Key body
            pygame.draw.rect(key_surface, (255, 215, 0), (TILE_SIZE//4, 0, TILE_SIZE//2, TILE_SIZE//4))
            # Key stem
            pygame.draw.rect(key_surface, (255, 215, 0), (TILE_SIZE//3, TILE_SIZE//4, TILE_SIZE//3, TILE_SIZE//2))
            # Key teeth
            pygame.draw.rect(key_surface, (255, 215, 0), (TILE_SIZE//6, TILE_SIZE//2, TILE_SIZE*2//3, TILE_SIZE//4))
            surface.blit(key_surface, (self.key_position[0] - TILE_SIZE//2, self.key_position[1] - TILE_SIZE//2))
            
            # Show a message for 5 seconds after the key is dropped
            if hasattr(self, 'key_drop_time'):
                time_since_drop = pygame.time.get_ticks() - self.key_drop_time
                if time_since_drop < 5000:  # Show for 5 seconds
                    # Flashing message
                    flash_factor = abs(math.sin(pygame.time.get_ticks() / 250))  # Faster flash
                    if flash_factor > 0.5:  # Only show during the "on" part of the flash
                        font = pygame.font.Font(None, 32)
                        message = font.render("A KEY HAS APPEARED!", True, (255, 255, 0))
                        message_rect = message.get_rect(center=(WINDOW_WIDTH//2, 50))
                        surface.blit(message, message_rect)
                    
        # Draw health pickups
        for pickup in self.health_pickups:
            if not pickup.collected:
                pickup.draw(surface)
                
        # Draw arrow pickups
        for pickup in self.arrow_pickups:
            if not pickup.collected:
                pickup.draw(surface)
                    
        # Draw enemies
        for enemy in self.enemies:
            enemy.draw(surface)
            
        # Draw boss if present
        if self.boss and self.boss.health > 0:
            self.boss.draw(surface)

    def add_exit_door(self):
        """Add an exit door to the room at a random location along a wall"""
        # Choose a random wall position that is not a door or corner
        valid_positions = []
        
        # North wall
        for x in range(2, self.width - 2):
            if x != self.width // 2:  # Skip if there's already a door
                valid_positions.append((x, 0))
                
        # South wall
        for x in range(2, self.width - 2):
            if x != self.width // 2:  # Skip if there's already a door
                valid_positions.append((x, self.height - 1))
                
        # East wall
        for y in range(2, self.height - 2):
            if y != self.height // 2:  # Skip if there's already a door
                valid_positions.append((self.width - 1, y))
                
        # West wall
        for y in range(2, self.height - 2):
            if y != self.height // 2:  # Skip if there's already a door
                valid_positions.append((0, y))
                
        if valid_positions:
            # Pick a random valid position
            exit_x, exit_y = random.choice(valid_positions)
            self.tiles[exit_y][exit_x] = EXIT_DOOR_TILE
            self.has_exit = True
            self.exit_position = (exit_x, exit_y)
            
            # Ensure there's a path to the exit
            if exit_y == 0:  # North wall
                self.tiles[1][exit_x] = 0
            elif exit_y == self.height - 1:  # South wall
                self.tiles[self.height - 2][exit_x] = 0
            elif exit_x == 0:  # West wall
                self.tiles[exit_y][1] = 0
            elif exit_x == self.width - 1:  # East wall
                self.tiles[exit_y][self.width - 2] = 0
                
    def drop_key(self):
        """Drop a key when the boss is defeated"""
        if self.room_type == 'boss' and self.boss and self.boss.health <= 0 and not self.key_dropped and not self.key_picked_up:
            # Place the key where the boss was
            self.key_position = (self.boss.rect.centerx, self.boss.rect.centery)
            self.key_dropped = True
            self.key_drop_time = pygame.time.get_ticks()  # Record when the key was dropped
            print(f"Boss defeated! A key has been dropped at {self.key_position}")
            
    def check_exit_collision(self, rect):
        """Check if player is touching the exit door"""
        if not self.has_exit:
            return False
            
        # Convert exit position to pixels
        exit_x, exit_y = self.exit_position
        exit_rect = pygame.Rect(exit_x * TILE_SIZE, exit_y * TILE_SIZE, TILE_SIZE, TILE_SIZE)
        
        return rect.colliderect(exit_rect)
        
    def check_key_collision(self, rect):
        """Check if player is touching the key"""
        if not self.key_dropped or not self.key_position:
            return False
            
        # Create a rect for the key - make it larger for easier pickup
        key_rect = pygame.Rect(
            self.key_position[0] - TILE_SIZE, 
            self.key_position[1] - TILE_SIZE,
            TILE_SIZE * 2, 
            TILE_SIZE * 2
        )
        
        return rect.colliderect(key_rect)

class Level:
    """Represents an entire dungeon level composed of multiple rooms"""
    def __init__(self, level_number):
        self.level_number = level_number
        
        # Tile textures
        self.asset_manager = get_asset_manager()
        
        # Random texture selection for this level
        self.selected_floor_texture = self.get_random_texture('floor')
        self.selected_wall_texture = self.get_random_texture('walls')
        self.selected_door_texture = self.get_random_texture('doors')
        # Destroyable wall textures will be selected individually per tile
        self.destroyable_wall_textures = self.get_all_destroyable_wall_textures()
        
        # Random enemy texture selection for this level
        self.selected_skeleton_texture = self.get_random_enemy_texture('skeletons')
        self.selected_slime_texture = self.get_random_enemy_texture('slimes')
        
        # Load tile textures
        self.tiles = self.load_tile_textures()
        
        # Level properties
        self.rooms = {}  # Dictionary of rooms indexed by (x,y) grid position
        self.current_room_coords = (0, 0)  # Start at origin
        self.num_rooms = 4 + level_number  # Number of rooms scales with level
        self.max_enemies_per_room = 2 + level_number // 2  # More enemies in later levels
        
        # Level exit properties
        self.exit_room_coords = None
        self.exit_placed = False
        self.completed = False
        self.show_exit_confirmation = False
        self.confirmation_message_timer = 0
        
        # Level progression
        self.has_key = False
        
        # Generate level
        self.generate_level()
        
        # Set current room to start room
        self.current_room_coords = (0, 0)
        
    def get_random_texture(self, texture_type):
        """Get a random texture file from the specified directory"""
        try:
            texture_dir = os.path.join(TILE_SPRITES_PATH, texture_type)
            if not os.path.exists(texture_dir):
                print(f"Texture directory does not exist: {texture_dir}")
                return None
                
            # Get all PNG files in the directory
            texture_files = glob.glob(os.path.join(texture_dir, "*.png"))
            if not texture_files:
                print(f"No texture files found in {texture_dir}")
                return None
                
            # Select a random texture file
            selected_texture = random.choice(texture_files)
            print(f"Selected {texture_type} texture: {os.path.basename(selected_texture)}")
            return selected_texture
        except Exception as e:
            print(f"Error selecting random {texture_type} texture: {e}")
            return None
            
    def get_all_destroyable_wall_textures(self):
        """Get all available destroyable wall textures"""
        try:
            texture_dir = os.path.join(TILE_SPRITES_PATH, "destroyable walls")
            if not os.path.exists(texture_dir):
                print(f"Destroyable walls directory does not exist: {texture_dir}")
                return []
                
            # Get all PNG files in the directory
            texture_files = glob.glob(os.path.join(texture_dir, "*.png"))
            if not texture_files:
                print(f"No destroyable wall texture files found in {texture_dir}")
                return []
                
            print(f"Found {len(texture_files)} destroyable wall textures")
            return texture_files
        except Exception as e:
            print(f"Error getting destroyable wall textures: {e}")
            return []
            
    def get_random_destroyable_wall_texture(self):
        """Select a random destroyable wall texture"""
        if not self.destroyable_wall_textures:
            return None
        return random.choice(self.destroyable_wall_textures)
        
    def get_random_enemy_texture(self, enemy_type):
        """Get a random texture file for the specified enemy type"""
        try:
            texture_dir = os.path.join(ENEMY_SPRITES_PATH, enemy_type)
            if not os.path.exists(texture_dir):
                print(f"Enemy texture directory does not exist: {texture_dir}")
                return None
                
            # Get all PNG files in the directory
            texture_files = glob.glob(os.path.join(texture_dir, "*.png"))
            if not texture_files:
                print(f"No enemy texture files found in {texture_dir}")
                return None
                
            # Select a random texture file
            selected_texture = random.choice(texture_files)
            print(f"Selected {enemy_type} texture: {os.path.basename(selected_texture)}")
            return selected_texture
        except Exception as e:
            print(f"Error selecting random {enemy_type} texture: {e}")
            return None
        
    def load_tile_textures(self):
        """Load tile textures for the level"""
        tiles = {}
        
        # Create default placeholder textures
        # Wall tile placeholder
        wall_tile = pygame.Surface((TILE_SIZE, TILE_SIZE))
        wall_tile.fill((100, 100, 100))  # Gray color
        # Add some texture to the wall
        for i in range(0, TILE_SIZE, 4):
            pygame.draw.line(wall_tile, (80, 80, 80), (i, 0), (i, TILE_SIZE), 1)
        tiles['wall'] = wall_tile
        
        # Destroyable wall placeholder
        destroyable_wall = pygame.Surface((TILE_SIZE, TILE_SIZE))
        destroyable_wall.fill((120, 80, 40))  # Brown color
        # Add cracks to show it's destroyable
        pygame.draw.line(destroyable_wall, (40, 40, 40), (TILE_SIZE//4, TILE_SIZE//4), (3*TILE_SIZE//4, TILE_SIZE//2), 2)
        pygame.draw.line(destroyable_wall, (40, 40, 40), (TILE_SIZE//2, TILE_SIZE//4), (TILE_SIZE//4, 3*TILE_SIZE//4), 2)
        tiles['destroyable_wall'] = destroyable_wall
        
        # Floor tile placeholder
        floor_tile = pygame.Surface((TILE_SIZE, TILE_SIZE))
        floor_tile.fill((200, 200, 200))  # Light gray color
        # Add a simple pattern
        for i in range(0, TILE_SIZE, 8):
            pygame.draw.line(floor_tile, (180, 180, 180), (i, 0), (i, TILE_SIZE), 1)
        for i in range(0, TILE_SIZE, 8):
            pygame.draw.line(floor_tile, (180, 180, 180), (0, i), (TILE_SIZE, i), 1)
        tiles['floor'] = floor_tile
        
        # Door tile placeholder
        door_tile = pygame.Surface((TILE_SIZE, TILE_SIZE))
        door_tile.fill((150, 100, 50))  # Brown color
        # Add door handle
        pygame.draw.circle(door_tile, (100, 80, 30), (TILE_SIZE//4, TILE_SIZE//2), TILE_SIZE//8)
        tiles['door'] = door_tile
        
        # Exit door tile placeholder
        exit_door = pygame.Surface((TILE_SIZE, TILE_SIZE))
        exit_door.fill((50, 150, 50))  # Green color
        # Add exit symbol
        pygame.draw.polygon(exit_door, (255, 255, 255), 
            [(TILE_SIZE//4, TILE_SIZE//4), 
             (TILE_SIZE//2, TILE_SIZE//4), 
             (TILE_SIZE//2, TILE_SIZE//2),
             (3*TILE_SIZE//4, TILE_SIZE//2),
             (TILE_SIZE//2, 3*TILE_SIZE//4),
             (TILE_SIZE//2, TILE_SIZE//2),
             (TILE_SIZE//4, TILE_SIZE//2)])
        tiles['exit'] = exit_door
        
        # Load the selected textures for this level
        try:
            # Load floor texture
            if self.selected_floor_texture and os.path.exists(self.selected_floor_texture):
                tiles['floor'] = self.asset_manager.load_image(self.selected_floor_texture, scale=(TILE_SIZE, TILE_SIZE))
                print(f"Loaded floor texture: {os.path.basename(self.selected_floor_texture)}")
                
            # Load wall texture
            if self.selected_wall_texture and os.path.exists(self.selected_wall_texture):
                tiles['wall'] = self.asset_manager.load_image(self.selected_wall_texture, scale=(TILE_SIZE, TILE_SIZE))
                print(f"Loaded wall texture: {os.path.basename(self.selected_wall_texture)}")
                
            # Load door texture
            if self.selected_door_texture and os.path.exists(self.selected_door_texture):
                tiles['door'] = self.asset_manager.load_image(self.selected_door_texture, scale=(TILE_SIZE, TILE_SIZE))
                print(f"Loaded door texture: {os.path.basename(self.selected_door_texture)}")
                
            # We'll load destroyable wall textures on-the-fly during rendering
                
        except Exception as e:
            print(f"Error loading level textures: {e}")
            
        return tiles
        
    def generate_level(self):
        """Generate a multi-room dungeon level"""
        # Start with a room at the origin (0,0)
        self.rooms[(0, 0)] = Room(0, 0, self.level_number, 'start')
        room_count = 1
        
        # Keep track of available doors to connect more rooms
        available_connections = []
        available_connections.append((0, 0, 'north'))
        available_connections.append((0, 0, 'east'))
        available_connections.append((0, 0, 'south'))
        available_connections.append((0, 0, 'west'))
        
        # Add boss and treasure rooms first to ensure they exist
        boss_added = False
        treasure_added = False
        
        # Keep adding rooms until we have enough or run out of connections
        while room_count < self.num_rooms and available_connections:
            # Pick a random connection
            from_x, from_y, direction = random.choice(available_connections)
            available_connections.remove((from_x, from_y, direction))
            
            # Calculate the new room coordinates
            new_x, new_y = from_x, from_y
            if direction == 'north':
                new_y -= 1
            elif direction == 'south':
                new_y += 1
            elif direction == 'east':
                new_x += 1
            elif direction == 'west':
                new_x -= 1
                
            # Skip if there's already a room at this position
            if (new_x, new_y) in self.rooms:
                continue
                
            # Determine room type
            room_type = 'normal'
            if not boss_added and room_count >= self.num_rooms - 2:
                room_type = 'boss'
                boss_added = True
            elif not treasure_added and room_count >= self.num_rooms // 2:
                room_type = 'treasure'
                treasure_added = True
                
            # Create the new room
            new_room = Room(new_x, new_y, self.level_number, room_type)
            
            # Connect the rooms via doors
            if direction == 'north':
                self.rooms[(from_x, from_y)].doors['north'] = True
                new_room.doors['south'] = True
            elif direction == 'south':
                self.rooms[(from_x, from_y)].doors['south'] = True
                new_room.doors['north'] = True
            elif direction == 'east':
                self.rooms[(from_x, from_y)].doors['east'] = True
                new_room.doors['west'] = True
            elif direction == 'west':
                self.rooms[(from_x, from_y)].doors['west'] = True
                new_room.doors['east'] = True
                
            # Add the new room
            self.rooms[(new_x, new_y)] = new_room
            room_count += 1
            
            # Add possible connections from the new room
            for dir in ['north', 'east', 'south', 'west']:
                if not new_room.doors[dir]:  # Door is not already connected
                    available_connections.append((new_x, new_y, dir))
                    
        # Ensure we have boss and treasure rooms
        if not boss_added:
            # Convert a random room to a boss room
            normal_rooms = [(x, y) for x, y in self.rooms if self.rooms[(x, y)].room_type == 'normal']
            if normal_rooms:
                random_coords = random.choice(normal_rooms)
                self.rooms[random_coords].room_type = 'boss'
        
        if not treasure_added:
            # Convert a random room to a treasure room
            normal_rooms = [(x, y) for x, y in self.rooms if self.rooms[(x, y)].room_type == 'normal']
            if normal_rooms:
                random_coords = random.choice(normal_rooms)
                self.rooms[random_coords].room_type = 'treasure'
                
        # Regenerate the rooms to reflect their type
        for coords, room in self.rooms.items():
            room.generate_room()
            
        # Add enemies to each room (except the start room)
        for coords, room in self.rooms.items():
            if room.room_type == 'start':
                continue
                
            # Determine number of enemies based on room type
            if room.room_type == 'boss':
                room.spawn_boss(self)
                num_enemies = self.max_enemies_per_room // 2  # Fewer regular enemies in boss room
            elif room.room_type == 'treasure':
                num_enemies = self.max_enemies_per_room // 3  # Fewer enemies in treasure room
            else:
                num_enemies = random.randint(1, self.max_enemies_per_room)
                
            room.spawn_enemies(num_enemies, self)
            
        # Update start room doors to make sure they're consistent with connections
        for direction in ['north', 'east', 'south', 'west']:
            self.rooms[(0, 0)].generate_room()
            
        # After all rooms are generated, choose a random room for the exit
        # Exit can be in any room, including the boss room
        exit_room_coords = random.choice(list(self.rooms.keys()))
        self.rooms[exit_room_coords].add_exit_door()
        print(f"Exit door placed in room at {exit_room_coords}")
        
    def get_valid_player_start_position(self):
        """Get a valid position for the player to start in the first room"""
        start_room = self.rooms[(0, 0)]
        return start_room.get_valid_player_position()
        
    def get_player_position_after_door(self, door_direction):
        """
        Get the player's position after going through a door in the given direction.
        Returns the new position (x, y) or None if no valid position.
        """
        try:
            # First determine which room we're transitioning to
            dx, dy = 0, 0
            if door_direction == 'north':
                dy = -1
            elif door_direction == 'south':
                dy = 1
            elif door_direction == 'east':
                dx = 1
            elif door_direction == 'west':
                dx = -1
            
            # Calculate new room coordinates
            new_room_coords = (self.current_room_coords[0] + dx, self.current_room_coords[1] + dy)
            
            # Check if the new room exists
            if new_room_coords not in self.rooms:
                print(f"Room at {new_room_coords} does not exist!")
                return None
            
            # Get the new room
            new_room = self.rooms[new_room_coords]
            
            # Update current room coordinates
            self.current_room_coords = new_room_coords
            
            # Calculate initial entry position based on which door we came through
            if door_direction == 'north':
                # Coming in from the south door
                entry_x = (new_room.width // 2) * TILE_SIZE + TILE_SIZE // 2
                entry_y = (new_room.height - 3) * TILE_SIZE + TILE_SIZE // 2
                
                # Calculate tile coordinates
                tile_x = new_room.width // 2
                tile_y = new_room.height - 3
            elif door_direction == 'south':
                # Coming in from the north door
                entry_x = (new_room.width // 2) * TILE_SIZE + TILE_SIZE // 2
                entry_y = 2 * TILE_SIZE + TILE_SIZE // 2
                
                # Calculate tile coordinates
                tile_x = new_room.width // 2
                tile_y = 2
            elif door_direction == 'east':
                # Coming in from the west door
                entry_x = 2 * TILE_SIZE + TILE_SIZE // 2
                entry_y = (new_room.height // 2) * TILE_SIZE + TILE_SIZE // 2
                
                # Calculate tile coordinates
                tile_x = 2
                tile_y = new_room.height // 2
            elif door_direction == 'west':
                # Coming in from the east door
                entry_x = (new_room.width - 3) * TILE_SIZE + TILE_SIZE // 2
                entry_y = (new_room.height // 2) * TILE_SIZE + TILE_SIZE // 2
                
                # Calculate tile coordinates
                tile_x = new_room.width - 3
                tile_y = new_room.height // 2
            else:
                print(f"Invalid direction: {door_direction}")
                return None
            
            # Check if the initial position is a wall
            if new_room.tiles[tile_y][tile_x] != 0:
                print(f"Warning: Initial entry position is a wall! Finding nearby floor tile...")
                
                # Search for a nearby floor tile
                found_floor = False
                search_radius = 1
                max_search_radius = 5  # Limit search radius to avoid infinite loops
                
                while not found_floor and search_radius <= max_search_radius:
                    # Check tiles in an expanding square around the initial position
                    for y_offset in range(-search_radius, search_radius + 1):
                        for x_offset in range(-search_radius, search_radius + 1):
                            check_x = tile_x + x_offset
                            check_y = tile_y + y_offset
                            
                            # Make sure the position is within bounds
                            if (0 <= check_y < new_room.height and 
                                0 <= check_x < new_room.width and
                                new_room.tiles[check_y][check_x] == 0):  # Floor tile
                                
                                # Found a floor tile, update entry position
                                entry_x = check_x * TILE_SIZE + TILE_SIZE // 2
                                entry_y = check_y * TILE_SIZE + TILE_SIZE // 2
                                found_floor = True
                                print(f"Found valid floor tile at ({check_x}, {check_y})")
                                break
                            
                        if found_floor:
                            break
                    
                    search_radius += 1
                
                if not found_floor:
                    print("Warning: Could not find a valid floor tile near the door!")
                    # Fall back to using the room's get_valid_player_position method
                    entry_x, entry_y = new_room.get_valid_player_position()
                    print(f"Falling back to valid position: ({entry_x}, {entry_y})")
                
            # Clear any weapons or projectiles between rooms
            print(f"Player entered a new room. Any active projectiles should be cleared.")
                
            return (entry_x, entry_y)
        except Exception as e:
            print(f"Error in get_player_position_after_door: {e}")
            # If there's an error, fall back to the room's valid position finder
            try:
                new_room = self.rooms[self.current_room_coords]
                return new_room.get_valid_player_position()
            except:
                return None
        
    def check_door_transition(self, player_rect):
        """Check if player is touching a door to transition to another room"""
        current_room = self.rooms[self.current_room_coords]
        door_direction = current_room.check_door_collision(player_rect)
        
        if door_direction:
            # Check if there's a room in that direction
            new_pos = self.get_player_position_after_door(door_direction)
            if new_pos:
                return door_direction, new_pos
        
        return None, None
        
    def check_key_pickup(self, player_rect):
        """Check if player has picked up the key"""
        if self.has_key:
            return False  # Already have the key
            
        current_room = self.rooms[self.current_room_coords]
        if current_room.check_key_collision(player_rect):
            self.has_key = True
            current_room.key_dropped = False  # Remove the key
            current_room.key_position = None
            current_room.key_picked_up = True  # Mark that the key was picked up
            # Record when the key was picked up for display notification
            self.key_pickup_time = pygame.time.get_ticks()
            print("Key collected! You can now exit the level.")
            return True
            
        return False
        
    def check_exit_use(self, player_rect):
        """Check if player is using the exit door"""
        if self.show_exit_confirmation:
            return False  # Already showing confirmation
            
        current_room = self.rooms[self.current_room_coords]
        if current_room.check_exit_collision(player_rect):
            if self.has_key:
                self.show_exit_confirmation = True
                print("Exit reached! Showing confirmation dialog.")
                return True
            else:
                # Only show the message every 60 frames (roughly 1 second at 60 FPS)
                if pygame.time.get_ticks() % 60 == 0:
                    print("You need a key to use this exit!")
                
        return False
        
    def confirm_exit(self):
        """Confirm exit to next level"""
        self.completed = True
        self.show_exit_confirmation = False
        return True
        
    def cancel_exit(self):
        """Cancel exit confirmation"""
        self.show_exit_confirmation = False
        
    def update(self, player):
        """Update only the current room"""
        current_room = self.rooms[self.current_room_coords]
        current_room.update(player)
        
        # Check if player picked up the key
        self.check_key_pickup(player.hitbox)
        
        # Check exit use (only if not already showing confirmation)
        if not self.show_exit_confirmation:
            self.check_exit_use(player.hitbox)
            
    def check_collision(self, rect):
        """Check collision with walls in the current room only"""
        current_room = self.rooms[self.current_room_coords]
        return current_room.check_collision(rect)
        
    def try_destroy_wall(self, x, y):
        """Try to destroy a wall at the given tile coordinates"""
        current_room = self.rooms[self.current_room_coords]
        return current_room.try_destroy_wall(x, y)
        
    def check_health_pickup(self, player_rect):
        """Check if player is picking up a health item"""
        current_room = self.rooms[self.current_room_coords]
        return current_room.try_pickup_health(player_rect)
        
    def check_arrow_pickup(self, player_rect):
        """Check if player is picking up arrows"""
        try:
            current_room = self.rooms[self.current_room_coords]
            return current_room.try_pickup_arrows(player_rect)
        except Exception as e:
            print(f"Error in check_arrow_pickup: {e}")
            return 0
        
    def draw(self, surface):
        """Draw only the current room"""
        current_room = self.rooms[self.current_room_coords]
        current_room.draw(surface, self.tiles, self)
        
        # Draw mini-map
        self.draw_minimap(surface)
        
        # Draw key pickup notification
        if hasattr(self, 'key_pickup_time'):
            time_since_pickup = pygame.time.get_ticks() - self.key_pickup_time
            if time_since_pickup < 3000:  # Show for 3 seconds
                # Create a notification
                font = pygame.font.Font(None, 36)
                notification = font.render("KEY COLLECTED! Find the exit.", True, (255, 255, 0))
                # Make it pulse
                alpha = int(255 * abs(math.sin(time_since_pickup / 300)))
                notification.set_alpha(alpha)
                notification_rect = notification.get_rect(center=(WINDOW_WIDTH//2, WINDOW_HEIGHT//2 - 100))
                surface.blit(notification, notification_rect)
        
        # Draw key indicator if we have the key
        if self.has_key:
            # Draw key icon with animation
            key_icon_size = TILE_SIZE
            key_bg = pygame.Surface((key_icon_size, key_icon_size), pygame.SRCALPHA)
            # Animate the background glow
            pulse = 0.5 + 0.5 * abs(math.sin(pygame.time.get_ticks() / 200))
            bg_color = (255, 215, 0, int(100 * pulse))
            pygame.draw.circle(key_bg, bg_color, (key_icon_size//2, key_icon_size//2), key_icon_size//2)
            surface.blit(key_bg, (WINDOW_WIDTH - key_icon_size - 5, 5))
            
            # Draw the key icon
            key_icon = pygame.Surface((key_icon_size, key_icon_size), pygame.SRCALPHA)
            # Key body
            pygame.draw.rect(key_icon, (255, 215, 0), (key_icon_size//4, key_icon_size//8, key_icon_size//2, key_icon_size//4))
            # Key stem
            pygame.draw.rect(key_icon, (255, 215, 0), (key_icon_size//3, key_icon_size//3, key_icon_size//3, key_icon_size//2))
            # Key teeth
            pygame.draw.rect(key_icon, (255, 215, 0), (key_icon_size//6, key_icon_size//2, key_icon_size*2//3, key_icon_size//4))
            surface.blit(key_icon, (WINDOW_WIDTH - key_icon_size - 5, 5))
            
            # Add text label
            font = pygame.font.Font(None, 20)
            key_text = font.render("KEY", True, (255, 255, 255))
            surface.blit(key_text, (WINDOW_WIDTH - key_icon_size - 5, key_icon_size + 10))
            
        # Draw exit confirmation if needed
        if self.show_exit_confirmation:
            self.draw_exit_confirmation(surface)
        
    def draw_exit_confirmation(self, surface):
        """Draw confirmation dialog for exiting the level"""
        # Overlay
        overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 128))
        surface.blit(overlay, (0, 0))
        
        # Dialog box - make it wider to fit the text
        dialog_width = 500
        dialog_height = 180
        dialog_x = (WINDOW_WIDTH - dialog_width) // 2
        dialog_y = (WINDOW_HEIGHT - dialog_height) // 2
        
        # Draw dialog background
        pygame.draw.rect(surface, (50, 50, 50), 
                         (dialog_x, dialog_y, dialog_width, dialog_height))
        pygame.draw.rect(surface, WHITE, 
                         (dialog_x, dialog_y, dialog_width, dialog_height), 2)
        
        # Draw text - use a slightly smaller font and ensure it's centered
        font = pygame.font.Font(None, 30)
        text = font.render(EXIT_CONFIRMATION_TEXT, True, WHITE)
        text_rect = text.get_rect(center=(WINDOW_WIDTH//2, WINDOW_HEIGHT//2 - 30))
        surface.blit(text, text_rect)
        
        # Draw buttons - move them down a bit
        yes_text = font.render("Yes", True, WHITE)
        no_text = font.render("No", True, WHITE)
        
        yes_rect = pygame.Rect(dialog_x + dialog_width//4 - 40, dialog_y + 120, 80, 30)
        no_rect = pygame.Rect(dialog_x + dialog_width*3//4 - 40, dialog_y + 120, 80, 30)
        
        pygame.draw.rect(surface, (0, 128, 0), yes_rect)
        pygame.draw.rect(surface, (128, 0, 0), no_rect)
        
        yes_text_rect = yes_text.get_rect(center=yes_rect.center)
        no_text_rect = no_text.get_rect(center=no_rect.center)
        
        surface.blit(yes_text, yes_text_rect)
        surface.blit(no_text, no_text_rect)
        
        # Return button rects for click handling
        return yes_rect, no_rect
        
    def draw_minimap(self, surface):
        """Draw a small map in the corner showing room layout"""
        minimap_size = 10  # Size of each room on the minimap
        minimap_padding = 5
        minimap_x = WINDOW_WIDTH - (minimap_padding + len(self.rooms) * minimap_size)
        minimap_y = minimap_padding
        
        # Calculate bounds for centering
        min_x = min(x for x, y in self.rooms.keys())
        max_x = max(x for x, y in self.rooms.keys())
        min_y = min(y for x, y in self.rooms.keys())
        max_y = max(y for x, y in self.rooms.keys())
        
        width = max_x - min_x + 1
        height = max_y - min_y + 1
        
        # Draw background
        background_rect = pygame.Rect(
            minimap_x - minimap_padding,
            minimap_y - minimap_padding,
            width * minimap_size + 2 * minimap_padding,
            height * minimap_size + 2 * minimap_padding
        )
        pygame.draw.rect(surface, (0, 0, 0, 128), background_rect)
        
        # Draw each room
        for (x, y), room in self.rooms.items():
            # Adjust for minimum coordinates
            adjusted_x = x - min_x
            adjusted_y = y - min_y
            
            # Calculate position
            room_x = minimap_x + adjusted_x * minimap_size
            room_y = minimap_y + adjusted_y * minimap_size
            
            # Choose color based on room type
            if room.room_type == 'start':
                color = (0, 255, 0)  # Green for start
            elif room.room_type == 'boss':
                color = (255, 0, 0)  # Red for boss
            elif room.room_type == 'treasure':
                color = (255, 215, 0)  # Gold for treasure
            else:
                color = (200, 200, 200)  # Gray for normal
                
            # Highlight current room
            if (x, y) == self.current_room_coords:
                # Draw current room marker
                pygame.draw.rect(surface, (255, 255, 255), 
                              (room_x, room_y, minimap_size, minimap_size))
                pygame.draw.rect(surface, color, 
                              (room_x + 1, room_y + 1, minimap_size - 2, minimap_size - 2))
            else:
                pygame.draw.rect(surface, color, 
                              (room_x, room_y, minimap_size, minimap_size))
                
            # Draw connections
            for direction, is_door in room.doors.items():
                if is_door:
                    # Draw a line indicating a connection
                    if direction == 'north' and (x, y - 1) in self.rooms:
                        pygame.draw.line(surface, (255, 255, 255),
                                       (room_x + minimap_size // 2, room_y),
                                       (room_x + minimap_size // 2, room_y - 1))
                    elif direction == 'south' and (x, y + 1) in self.rooms:
                        pygame.draw.line(surface, (255, 255, 255),
                                       (room_x + minimap_size // 2, room_y + minimap_size),
                                       (room_x + minimap_size // 2, room_y + minimap_size + 1))
                    elif direction == 'east' and (x + 1, y) in self.rooms:
                        pygame.draw.line(surface, (255, 255, 255),
                                       (room_x + minimap_size, room_y + minimap_size // 2),
                                       (room_x + minimap_size + 1, room_y + minimap_size // 2))
                    elif direction == 'west' and (x - 1, y) in self.rooms:
                        pygame.draw.line(surface, (255, 255, 255),
                                       (room_x, room_y + minimap_size // 2),
                                       (room_x - 1, room_y + minimap_size // 2)) 