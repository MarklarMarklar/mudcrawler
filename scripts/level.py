import pygame
import random
import os
import math
import glob
from config import *
from enemy import Enemy, Boss
from asset_manager import get_asset_manager
from pickups import ArrowPickup, HealthPickup, KeyPickup, WeaponPickup

class BloodPuddle:
    """Blood puddle that appears when monsters die"""
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.size = TILE_SIZE
        self.rect = pygame.Rect(x - self.size//2, y - self.size//2, self.size, self.size)
        self.asset_manager = get_asset_manager()
        self.texture = None
        
        # Try to load a random blood puddle texture
        try:
            blood_dir = os.path.join(TILE_SPRITES_PATH, "blood")
            if os.path.exists(blood_dir):
                blood_files = glob.glob(os.path.join(blood_dir, "*.png"))
                if blood_files:
                    selected_blood = random.choice(blood_files)
                    self.texture = self.asset_manager.load_image(selected_blood, scale=(self.size, self.size))
                    print(f"Selected blood puddle: {os.path.basename(selected_blood)}")
        except Exception as e:
            print(f"Failed to load blood puddle texture: {e}")
            self.texture = None
    
    def draw(self, surface):
        """Draw the blood puddle to the surface"""
        if self.texture:
            # Slightly randomize position for more natural look
            rect = self.texture.get_rect(center=(self.x, self.y))
            surface.blit(self.texture, rect)
        else:
            # Fallback rendering if texture isn't available
            pygame.draw.circle(surface, (120, 0, 0), (self.x, self.y), self.size // 2)

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
        
        # Weapon pickups (including fire sword)
        self.weapon_pickups = []
        
        # Track if fire sword has been dropped from boss
        self.fire_sword_dropped = False
        
        # Blood puddles
        self.blood_puddles = []
        
        # Special flags for fire sword chest
        self.fire_sword_chest_x = None
        self.fire_sword_chest_y = None
        self.has_fire_sword_chest = False
        
        # Generate room layout
        self.generate_room()
        
    def generate_room(self):
        """Generate the room layout based on room type"""
        # Create basic room layout - all walls
        self.tiles = [[1 for x in range(self.width)] for y in range(self.height)]
        self.destroyable_walls = [[False for x in range(self.width)] for y in range(self.height)]
        
        # Room center for symmetry
        center_x, center_y = self.width // 2, self.height // 2
        
        # Create open area
        for y in range(1, self.height - 1):
            for x in range(1, self.width - 1):
                # Edges of the room are always floor
                if (x == 1 or x == self.width - 2 or y == 1 or y == self.height - 2):
                    self.tiles[y][x] = 0
                else:
                    # Default to floor
                    self.tiles[y][x] = 0
        
        # Apply symmetric wall patterns based on room type
        if self.room_type == 'normal':
            # Pick a symmetric pattern for the room based on grid coordinates
            # Use both coordinates to create more variety
            pattern_seed = (abs(self.grid_x) * 3 + abs(self.grid_y) * 7) % 9
            
            if pattern_seed == 0:
                # Cross pattern with openings
                for y in range(2, self.height - 2):
                    for x in range(2, self.width - 2):
                        # Create a cross pattern in the middle
                        if (x == center_x or y == center_y) and not (
                            # Leave openings at the cardinal directions for passage
                            (x == center_x and (abs(y - center_y) < 3)) or
                            (y == center_y and (abs(x - center_x) < 3))
                        ):
                            self.tiles[y][x] = 1
                    
                        # Add some additional symmetric walls for density
                        elif (x == center_x - 4 or x == center_x + 4) and (5 < y < self.height - 6):
                            self.tiles[y][x] = 1
                        elif (y == center_y - 4 or y == center_y + 4) and (5 < x < self.width - 6):
                            self.tiles[y][x] = 1
                
            elif pattern_seed == 1:
                # Four symmetric corner rooms with central chamber
                # Define the corner rooms
                room_width = (self.width - 6) // 2
                room_height = (self.height - 6) // 2
                
                # Create walls to separate rooms
                for x in range(2, self.width - 2):
                    if abs(x - center_x) > 2:  # Leave opening in center
                        self.tiles[center_y][x] = 1  # Horizontal wall
                
                for y in range(2, self.height - 2):
                    if abs(y - center_y) > 2:  # Leave opening in center
                        self.tiles[y][center_x] = 1  # Vertical wall
                
                # Add some decorative walls in corner rooms (reflective symmetry)
                for corner_offset_y in [-1, 1]:
                    for corner_offset_x in [-1, 1]:
                        offset_y = center_y + corner_offset_y * (room_height // 2 + 2)
                        offset_x = center_x + corner_offset_x * (room_width // 2 + 2)
                        
                        # Add a 3x3 pattern in each corner room
                        for y_rel in range(-1, 2):
                            for x_rel in range(-1, 2):
                                # Skip center to allow passage
                                if not (x_rel == 0 and y_rel == 0):
                                    self.tiles[offset_y + y_rel][offset_x + x_rel] = 1
                
            elif pattern_seed == 2:
                # Diamond pattern
                # Make diamond pattern with clear center
                diamond_radius = min(center_x, center_y) - 3
                for y in range(2, self.height - 2):
                    for x in range(2, self.width - 2):
                        # Manhattan distance for diamond shape
                        distance = abs(x - center_x) + abs(y - center_y)
                        # Create diamond outline
                        if distance == diamond_radius:
                            self.tiles[y][x] = 1
                        # Add smaller inner diamond for more walls
                        elif distance == diamond_radius // 2 and diamond_radius > 6:
                            self.tiles[y][x] = 1
                
            elif pattern_seed == 3:
                # Pillar pattern with symmetrical pillars
                pillar_offsets = [
                    (center_x // 2, center_y // 2),
                    (center_x + center_x // 2, center_y // 2),
                    (center_x // 2, center_y + center_y // 2),
                    (center_x + center_x // 2, center_y + center_y // 2)
                ]
                
                # Add pillars
                for px, py in pillar_offsets:
                    self.tiles[py][px] = 1
                    self.tiles[py+1][px] = 1
                    self.tiles[py][px+1] = 1
                    self.tiles[py+1][px+1] = 1
                    
                # Add centered walls between pillars
                if center_x > 5 and center_y > 5:
                    # Horizontal connecting walls
                    for x in range(pillar_offsets[0][0] + 2, pillar_offsets[1][0]):
                        if (x - pillar_offsets[0][0]) % 3 != 0:  # Leave gaps for passage
                            self.tiles[pillar_offsets[0][1]][x] = 1
                            self.tiles[pillar_offsets[2][1]][x] = 1
                    
                    # Vertical connecting walls
                    for y in range(pillar_offsets[0][1] + 2, pillar_offsets[2][1]):
                        if (y - pillar_offsets[0][1]) % 3 != 0:  # Leave gaps for passage
                            self.tiles[y][pillar_offsets[0][0]] = 1
                            self.tiles[y][pillar_offsets[1][0]] = 1
                
            elif pattern_seed == 4:
                # Maze-like symmetric pattern
                for offset_y in range(3, center_y, 3):
                    # Horizontal walls with gaps
                    for x in range(3, self.width - 3):
                        # Skip position if it would block a passage
                        if (x - 3) % 6 != 0:
                            # Apply to both sides symmetrically
                            self.tiles[center_y - offset_y][x] = 1
                            self.tiles[center_y + offset_y][x] = 1
                
                for offset_x in range(3, center_x, 3):
                    # Vertical walls with gaps
                    for y in range(3, self.height - 3):
                        # Skip position if it would block a passage
                        if (y - 3) % 6 != 0:
                            # Apply to both sides symmetrically
                            self.tiles[y][center_x - offset_x] = 1
                            self.tiles[y][center_x + offset_x] = 1
            
            elif pattern_seed == 5:
                # Concentric circles pattern
                for y in range(2, self.height - 2):
                    for x in range(2, self.width - 2):
                        # Euclidean distance for circle shape
                        distance = math.sqrt((x - center_x)**2 + (y - center_y)**2)
                        # Create walls at specific radii
                        if int(distance) % 5 == 0 and distance > 3:
                            self.tiles[y][x] = 1
            
            elif pattern_seed == 6:
                # Checkerboard pattern with symmetric larger squares
                square_size = 3
                for y in range(3, self.height - 3, square_size):
                    for x in range(3, self.width - 3, square_size):
                        # Create symmetric pattern relative to center
                        if ((x // square_size) + (y // square_size)) % 2 == 0:
                            # Create a square of walls
                            for dy in range(square_size - 1):
                                for dx in range(square_size - 1):
                                    if 0 <= y + dy < self.height and 0 <= x + dx < self.width:
                                        self.tiles[y + dy][x + dx] = 1
            
            elif pattern_seed == 7:
                # Spiral pattern
                max_radius = min(center_x, center_y) - 3
                angles = [0, 90, 180, 270]  # Four arms for symmetry
                
                for radius in range(3, max_radius, 2):
                    for angle in angles:
                        # Convert polar coordinates to cartesian
                        rad_angle = math.radians(angle)
                        x = int(center_x + radius * math.cos(rad_angle))
                        y = int(center_y + radius * math.sin(rad_angle))
                        
                        # Make sure we're in bounds
                        if (2 <= x < self.width - 2 and 2 <= y < self.height - 2):
                            # Create a 2x2 wall segment
                            self.tiles[y][x] = 1
                            if y+1 < self.height - 2:
                                self.tiles[y+1][x] = 1
                            if x+1 < self.width - 2:
                                self.tiles[y][x+1] = 1
                            if y+1 < self.height - 2 and x+1 < self.width - 2:
                                self.tiles[y+1][x+1] = 1
            
            else:  # pattern_seed == 8
                # Symmetric "rooms connected by hallways"
                # Create four symmetrically placed rooms
                room_positions = [
                    (center_x - center_x//2, center_y - center_y//2),
                    (center_x + center_x//2, center_y - center_y//2),
                    (center_x - center_x//2, center_y + center_y//2),
                    (center_x + center_x//2, center_y + center_y//2)
                ]
                
                room_size = 5
                
                # Create room boundaries
                for room_x, room_y in room_positions:
                    for y in range(room_y - room_size//2, room_y + room_size//2 + 1):
                        for x in range(room_x - room_size//2, room_x + room_size//2 + 1):
                            if (x == room_x - room_size//2 or x == room_x + room_size//2 or
                                y == room_y - room_size//2 or y == room_y + room_size//2):
                                if 0 <= y < self.height and 0 <= x < self.width:
                                    self.tiles[y][x] = 1
                
                # Connect rooms with hallways (leaving openings in room walls)
                # Horizontal hallways
                for x in range(room_positions[0][0] + room_size//2 + 1, room_positions[1][0] - room_size//2):
                    self.tiles[center_y - center_y//2 - 1][x] = 1
                    self.tiles[center_y - center_y//2 + 1][x] = 1
                    self.tiles[center_y + center_y//2 - 1][x] = 1
                    self.tiles[center_y + center_y//2 + 1][x] = 1
                
                # Vertical hallways
                for y in range(room_positions[0][1] + room_size//2 + 1, room_positions[2][1] - room_size//2):
                    self.tiles[y][center_x - center_x//2 - 1] = 1
                    self.tiles[y][center_x - center_x//2 + 1] = 1
                    self.tiles[y][center_x + center_x//2 - 1] = 1
                    self.tiles[y][center_x + center_x//2 + 1] = 1
        
        elif self.room_type == 'start':
            # Start room - make sure center area is clear
            for y in range(center_y - 2, center_y + 3):
                for x in range(center_x - 2, center_x + 3):
                    if 0 <= y < self.height and 0 <= x < self.width:
                        self.tiles[y][x] = 0
            
            # Add some symmetric decorative walls near edges
            for offset in range(3, min(center_x, center_y) - 2, 4):
                # Top and bottom walls
                for x_offset in range(-2, 3):
                    if x_offset != 0:  # Skip the center for passage
                        x = center_x + x_offset
                        self.tiles[center_y - offset][x] = 1
                        self.tiles[center_y + offset][x] = 1
                
                # Left and right walls
                for y_offset in range(-2, 3):
                    if y_offset != 0:  # Skip the center for passage
                        y = center_y + y_offset
                        self.tiles[y][center_x - offset] = 1
                        self.tiles[y][center_x + offset] = 1
        
        elif self.room_type == 'boss':
            # Boss room with symmetric design
            # Clear center area - make it larger to ensure boss has room to move
            clear_radius = 5
            for y in range(center_y - clear_radius, center_y + clear_radius + 1):
                for x in range(center_x - clear_radius, center_x + clear_radius + 1):
                    if 0 <= y < self.height and 0 <= x < self.width:
                        self.tiles[y][x] = 0  # Set to floor
            
            # Add symmetric pillars at the corners
            pillar_distance = clear_radius + 1
            pillar_positions = [
                (center_x - pillar_distance, center_y - pillar_distance),
                (center_x + pillar_distance, center_y - pillar_distance),
                (center_x - pillar_distance, center_y + pillar_distance),
                (center_x + pillar_distance, center_y + pillar_distance)
            ]
            
            for px, py in pillar_positions:
                if (0 < px < self.width - 1 and 0 < py < self.height - 1 and
                    px + 1 < self.width - 1 and py + 1 < self.height - 1):
                    # Create 2x2 pillar
                    self.tiles[py][px] = 1
                    self.tiles[py+1][px] = 1
                    self.tiles[py][px+1] = 1
                    self.tiles[py+1][px+1] = 1
            
            # Add some additional decorative walls along edges of the boss arena
            edge_distance = clear_radius + 2
            for offset in range(-edge_distance, edge_distance + 1, 4):
                # Only place at specific intervals (skip some positions)
                if offset != 0 and abs(offset) != edge_distance:
                    # Top and bottom edges
                    if 3 <= center_y + offset < self.height - 3:
                        self.tiles[center_y + offset][center_x - edge_distance] = 1
                        self.tiles[center_y + offset][center_x + edge_distance] = 1
                    
                    # Left and right edges
                    if 3 <= center_x + offset < self.width - 3:
                        self.tiles[center_y - edge_distance][center_x + offset] = 1
                        self.tiles[center_y + edge_distance][center_x + offset] = 1
        
        elif self.room_type == 'treasure':
            # Treasure room - symmetric layout
            # Clear most areas first
            for y in range(1, self.height - 1):
                for x in range(1, self.width - 1):
                    self.tiles[y][x] = 0
            
            # Add symmetric corner structures
            corner_positions = [
                (2, 2),                       # Top-left
                (2, self.height - 5),         # Bottom-left
                (self.width - 5, 2),          # Top-right
                (self.width - 5, self.height - 5)  # Bottom-right
            ]
            
            for corner_x, corner_y in corner_positions:
                # Create L-shaped corner structures
                for i in range(3):
                    # Horizontal walls
                    self.tiles[corner_y][corner_x + i] = 1
                    # Vertical walls
                    self.tiles[corner_y + i][corner_x] = 1
            
            # Add a symmetric central structure - like a small room with openings
            central_room_size = 5
            for y in range(center_y - central_room_size//2, center_y + central_room_size//2 + 1):
                for x in range(center_x - central_room_size//2, center_x + central_room_size//2 + 1):
                    # Only create walls at the edges of this central structure
                    if (x == center_x - central_room_size//2 or x == center_x + central_room_size//2 or
                        y == center_y - central_room_size//2 or y == center_y + central_room_size//2):
                        # But leave openings at the cardinal directions
                        if not ((x == center_x and (y == center_y - central_room_size//2 or y == center_y + central_room_size//2)) or
                                (y == center_y and (x == center_x - central_room_size//2 or x == center_x + central_room_size//2))):
                            self.tiles[y][x] = 1
                    
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
            
        # ADD DESTROYABLE WALLS (TREASURE CHESTS) SEPARATELY
        self._place_destroyable_walls()
        
    def _place_destroyable_walls(self):
        """Place destroyable walls (treasure chests) in the room"""
        # Destroyable walls should be separate from normal walls
        # They represent actual treasure chests placed in the environment
        
        max_chests = 0
        
        if self.room_type == 'normal':
            # Normal rooms have few treasure chests
            max_chests = 2
        elif self.room_type == 'boss':
            # Boss rooms have a medium number of chests
            max_chests = 3
        elif self.room_type == 'treasure':
            # Treasure rooms have more chests
            max_chests = 4
        elif self.room_type == 'start':
            # Start rooms have very few chests
            max_chests = 1
        
        # Adjust based on level number (higher levels have slightly more chests)
        level_bonus = min(1, self.level_number // 4)  # Capped at 1 extra chest
        max_chests += level_bonus
        
        # Find valid floor positions for placing chests
        valid_positions = []
        for y in range(2, self.height - 2):
            for x in range(2, self.width - 2):
                # Only consider floor tiles that aren't near doors
                if self.tiles[y][x] == 0 and not self._is_near_door(x, y):
                    # Make sure the position doesn't block critical paths
                    if not self._blocks_path(x, y):
                        valid_positions.append((x, y))
        
        # If no valid positions, we can't place any chests
        if not valid_positions:
            return
        
        # Place chests based on room type
        chests_placed = 0
        
        if self.room_type == 'boss':
            # Place chests near the boss arena perimeter
            center_x, center_y = self.width // 2, self.height // 2
            arena_radius = 6  # Slightly larger than clear_radius from boss room generation
            
            # Filter positions that are at the perimeter of the boss arena
            perimeter_positions = [
                pos for pos in valid_positions 
                if abs(math.sqrt((pos[0] - center_x)**2 + (pos[1] - center_y)**2) - arena_radius) < 2
            ]
            
            # Try to place in symmetric positions
            if perimeter_positions:
                # Sort by angle from center for symmetric placement
                perimeter_positions.sort(key=lambda pos: math.atan2(pos[1] - center_y, pos[0] - center_x))
                
                # Take evenly spaced positions for symmetry
                if len(perimeter_positions) >= max_chests:
                    step = len(perimeter_positions) // max_chests
                    for i in range(0, min(max_chests, len(perimeter_positions)), 1):
                        index = (i * step) % len(perimeter_positions)
                        x, y = perimeter_positions[index]
                        self._place_chest(x, y)
                        chests_placed += 1
                else:
                    # Not enough positions for perfect symmetry, place what we can
                    for pos in perimeter_positions[:max_chests]:
                        x, y = pos
                        self._place_chest(x, y)
                        chests_placed += 1
        
        elif self.room_type == 'treasure':
            # For treasure rooms, place chests in strategic locations
            center_x, center_y = self.width // 2, self.height // 2
            
            # Potential chest locations in a treasure room
            # Try central area first (but not the exact center)
            central_positions = [
                pos for pos in valid_positions
                if 2 < abs(pos[0] - center_x) + abs(pos[1] - center_y) < 6
            ]
            
            # Place symmetrically in central area
            if central_positions and chests_placed < max_chests:
                # Try to get pairs of symmetric positions
                symmetric_pairs = []
                for i, pos1 in enumerate(central_positions):
                    for pos2 in central_positions[i+1:]:
                        # Check if points are symmetric about the center
                        if (abs((pos1[0] - center_x) + (pos2[0] - center_x)) < 2 and
                            abs((pos1[1] - center_y) + (pos2[1] - center_y)) < 2):
                            symmetric_pairs.append((pos1, pos2))
                
                # Place symmetric pairs first
                for pair in symmetric_pairs:
                    if chests_placed + 2 <= max_chests:
                        for pos in pair:
                            x, y = pos
                            self._place_chest(x, y)
                            chests_placed += 1
                    else:
                        break
            
            # If we still need more, place in corners
            if chests_placed < max_chests:
                corner_zones = [
                    # Top-left
                    [(x, y) for x, y in valid_positions if x < center_x - 4 and y < center_y - 4],
                    # Top-right
                    [(x, y) for x, y in valid_positions if x > center_x + 4 and y < center_y - 4],
                    # Bottom-left
                    [(x, y) for x, y in valid_positions if x < center_x - 4 and y > center_y + 4],
                    # Bottom-right
                    [(x, y) for x, y in valid_positions if x > center_x + 4 and y > center_y + 4]
                ]
                
                # Try to place one chest in each corner if possible
                for corner in corner_zones:
                    if corner and chests_placed < max_chests:
                        pos = random.choice(corner)
                        self._place_chest(pos[0], pos[1])
                        chests_placed += 1
        
        else:  # 'normal' and 'start' rooms
            # For normal and start rooms, place chests in interesting locations
            
            # Find positions along walls but not next to doors
            wall_adjacent_positions = [
                pos for pos in valid_positions
                if self._is_adjacent_to_wall(pos[0], pos[1]) and not self._is_near_door(pos[0], pos[1])
            ]
            
            # If we found good wall-adjacent positions, use those
            if wall_adjacent_positions and len(wall_adjacent_positions) >= max_chests:
                random.shuffle(wall_adjacent_positions)
                for i in range(max_chests):
                    x, y = wall_adjacent_positions[i]
                    self._place_chest(x, y)
                    chests_placed += 1
            else:
                # Otherwise fall back to any valid position
                random.shuffle(valid_positions)
                for i in range(min(max_chests, len(valid_positions))):
                    x, y = valid_positions[i]
                    self._place_chest(x, y)
                    chests_placed += 1
    
    def _place_chest(self, x, y):
        """Place a chest at the specified position"""
        # Convert the floor tile to a wall
        self.tiles[y][x] = 1
        # Mark it as destroyable
        self.destroyable_walls[y][x] = True
        
    def _is_adjacent_to_wall(self, x, y):
        """Check if a position is adjacent to a wall but not a door"""
        for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
            check_x, check_y = x + dx, y + dy
            if (0 <= check_y < self.height and 0 <= check_x < self.width and
                self.tiles[check_y][check_x] == 1):  # Wall tile
                return True
        return False
    
    def _blocks_path(self, x, y):
        """Check if placing a chest at this position would block an important path"""
        # Count floor tiles around this position
        floor_count = 0
        for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0), (1, 1), (1, -1), (-1, 1), (-1, -1)]:
            check_x, check_y = x + dx, y + dy
            if (0 <= check_y < self.height and 0 <= check_x < self.width and
                self.tiles[check_y][check_x] == 0):  # Floor tile
                floor_count += 1
        
        # Check if this position is in a narrow corridor (has few adjacent floor tiles)
        # or if it's near the center of the room
        center_x, center_y = self.width // 2, self.height // 2
        near_center = abs(x - center_x) < 3 and abs(y - center_y) < 3
        
        # Blocking a path if it's in a narrow corridor (2-3 floor tiles around) 
        # or very near the center
        return (2 <= floor_count <= 3) or near_center
    
    def _is_near_door(self, x, y):
        """Check if a position is near a door"""
        # Check surrounding 5x5 area for door tiles
        for dy in range(-2, 3):
            for dx in range(-2, 3):
                check_x, check_y = x + dx, y + dy
                if (0 <= check_y < self.height and 0 <= check_x < self.width and
                    self.tiles[check_y][check_x] == 2):  # Door tile
                    return True
        return False
        
    def try_destroy_wall(self, x, y):
        """Try to destroy a wall at the given tile position"""
        # Check if position is within bounds
        if not (0 <= y < self.height and 0 <= x < self.width):
            print(f"Room: Wall position {x},{y} is out of bounds")
            return False
        
        # Add debug output
        print(f"Room: Checking wall at {x},{y}: tile={self.tiles[y][x]}, destroyable={self.destroyable_walls[y][x] if self.tiles[y][x] == 1 else 'N/A'}")
        
        # Check if there's a destroyable wall at this position
        if self.tiles[y][x] == 1 and self.destroyable_walls[y][x]:
            print(f"Room: Found destroyable wall at {x},{y}")
            # Destroy the wall
            self.tiles[y][x] = 0
            self.destroyable_walls[y][x] = False
            
            # Check if this is the special fire sword chest
            if self.has_fire_sword_chest and x == self.fire_sword_chest_x and y == self.fire_sword_chest_y:
                # This is the fire sword chest - spawn the fire sword with a larger scale
                center_x = x * TILE_SIZE + TILE_SIZE // 2
                center_y = y * TILE_SIZE + TILE_SIZE // 2
                
                # Create a fire sword pickup with a 50% larger scale
                fire_sword = WeaponPickup(center_x, center_y, "fire_sword", scale=1.5)
                self.weapon_pickups.append(fire_sword)
                
                print(f"Room: Fire sword chest destroyed! Fire sword spawned at {center_x}, {center_y}")
                return True
            
            # Regular destroyable wall - normal loot drop logic
            pickup_roll = random.random()
            center_x = x * TILE_SIZE + TILE_SIZE // 2
            center_y = y * TILE_SIZE + TILE_SIZE // 2
            
            # 30% chance to spawn a health pickup
            if pickup_roll < 0.3:
                self.health_pickups.append(HealthPickup(center_x, center_y))
                print(f"Room: Health pickup spawned at {center_x}, {center_y} from destroyed wall")
            # 20% chance to spawn an arrow pickup
            elif pickup_roll < 0.5:
                self.arrow_pickups.append(ArrowPickup(center_x, center_y))
                print(f"Room: Arrow pickup spawned at {center_x}, {center_y} from destroyed wall")
            
            print(f"Room: Successfully destroyed wall at {x},{y}")
            return True
        else:
            print(f"Room: No destroyable wall at {x},{y}")
            # Only return true if we actually destroyed a wall
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
            
        # Try to place boss in the center first
        center_x = (self.width // 2) * TILE_SIZE
        center_y = (self.height // 2) * TILE_SIZE
        
        # Check if center position is valid (not a wall)
        if self.is_valid_spawn_position(center_x, center_y):
            self.boss = Boss(center_x, center_y, self.level_number, level_instance)
            print(f"Boss spawned at center position ({center_x}, {center_y})")
            return
            
        # If center is not valid, search for a valid position
        print("Center position is not valid for boss. Searching for valid position...")
        
        # Search in expanding circles around the center
        for radius in range(1, min(self.width, self.height) // 2):
            # Try positions in a square around the center
            for offset_y in range(-radius, radius + 1):
                for offset_x in range(-radius, radius + 1):
                    # Skip positions not on the edge of the square
                    if abs(offset_x) != radius and abs(offset_y) != radius:
                        continue
                        
                    test_x = center_x + offset_x * TILE_SIZE
                    test_y = center_y + offset_y * TILE_SIZE
                    
                    if self.is_valid_spawn_position(test_x, test_y):
                        self.boss = Boss(test_x, test_y, self.level_number, level_instance)
                        print(f"Boss spawned at alternative position ({test_x}, {test_y})")
                        return
        
        # If we got here, we couldn't find a valid position
        # As a last resort, try every floor tile in the room
        for y in range(1, self.height - 1):
            for x in range(1, self.width - 1):
                if self.tiles[y][x] == 0:  # Floor tile
                    pixel_x = x * TILE_SIZE
                    pixel_y = y * TILE_SIZE
                    
                    if self.is_valid_spawn_position(pixel_x, pixel_y):
                        self.boss = Boss(pixel_x, pixel_y, self.level_number, level_instance)
                        print(f"Boss spawned at fallback position ({pixel_x}, {pixel_y})")
                        return
                        
        # If we still can't find a position, log an error
        print("ERROR: Could not find a valid position for boss spawn!")
        
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
            # Create blood puddle at boss location
            if not hasattr(self, 'boss_blood_created') or not self.boss_blood_created:
                # Create a larger blood puddle for the boss (by adding multiple puddles)
                for _ in range(3):
                    offset_x = random.randint(-TILE_SIZE//2, TILE_SIZE//2)
                    offset_y = random.randint(-TILE_SIZE//2, TILE_SIZE//2)
                    self.blood_puddles.append(BloodPuddle(self.boss.rect.centerx + offset_x, self.boss.rect.centery + offset_y))
                self.boss_blood_created = True
                
            # Boss is defeated, drop the key
            self.drop_key()
            
            # For level 2 boss, drop the fire sword
            if self.level_number == 2:
                self.drop_fire_sword()
            
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
                # 2% chance to drop a fire sword in levels 2+
                elif pickup_roll < 0.20 and self.level_number >= 2:
                    self.weapon_pickups.append(WeaponPickup(enemy.rect.centerx, enemy.rect.centery, "fire_sword"))
                    print(f"Room: Fire sword spawned from defeated enemy at {enemy.rect.centerx}, {enemy.rect.centery}")
                    
                # Always create a blood puddle when an enemy dies
                self.blood_puddles.append(BloodPuddle(enemy.rect.centerx, enemy.rect.centery))
                
                enemy.kill()
                
        # Update pickups
        for pickup in self.health_pickups:
            pickup.update()
            
        for pickup in self.arrow_pickups:
            pickup.update()
            
        for pickup in self.weapon_pickups:
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
        # Store exit door positions for later glow drawing
        exit_door_positions = []
        
        # Draw tiles
        for y in range(self.height):
            for x in range(self.width):
                tile_x = x * TILE_SIZE
                tile_y = y * TILE_SIZE
                
                if self.tiles[y][x] == 1:  # Wall
                    if self.destroyable_walls[y][x] and level and level.destroyable_wall_textures:
                        # Check if this is the special fire sword chest
                        is_fire_sword_chest = self.has_fire_sword_chest and x == self.fire_sword_chest_x and y == self.fire_sword_chest_y
                        
                        # Randomly select a destroyable wall texture if not already cached
                        # We'll use a consistent hash based on the coordinates to keep the same texture
                        # for the same wall tile within a session
                        texture_index = hash(f"{self.grid_x}_{self.grid_y}_{x}_{y}") % len(level.destroyable_wall_textures)
                        destroyable_wall_texture = level.destroyable_wall_textures[texture_index]
                        
                        try:
                            # Load and draw the destroyable wall texture
                            if os.path.exists(destroyable_wall_texture):
                                if is_fire_sword_chest:
                                    # Scale up by 150% for fire sword chest
                                    scaled_size = int(TILE_SIZE * 1.5)
                                    texture = level.asset_manager.load_image(destroyable_wall_texture, scale=(scaled_size, scaled_size))
                                    # Draw centered at the tile position
                                    offset = (scaled_size - TILE_SIZE) // 2
                                    surface.blit(texture, (tile_x - offset, tile_y - offset))
                                else:
                                    # Regular destroyable wall
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
                    # Store position to draw glow later on top of everything
                    exit_door_positions.append((x, y))
                    
                    # Determine which exit door sprite to use based on whether player has the key
                    exit_key = 'exit_open' if level.has_key else 'exit'
                    
                    # Draw only the door now, glow will be added later
                    surface.blit(tile_images[exit_key], (tile_x, tile_y))
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
                    
        # Draw blood puddles
        for puddle in self.blood_puddles:
            puddle.draw(surface)
            
        # Draw health pickups
        for pickup in self.health_pickups:
            if not pickup.collected:
                pickup.draw(surface)
                
        # Draw arrow pickups
        for pickup in self.arrow_pickups:
            if not pickup.collected:
                pickup.draw(surface)
                
        # Draw weapon pickups
        for pickup in self.weapon_pickups:
            if not pickup.collected:
                pickup.draw(surface)
                    
        # Draw enemies
        for enemy in self.enemies:
            enemy.draw(surface)
            
        # Draw boss if present
        if self.boss and self.boss.health > 0:
            self.boss.draw(surface)
        
        # Finally, draw exit door glows on top of everything else
        for x, y in exit_door_positions:
            tile_x = x * TILE_SIZE
            tile_y = y * TILE_SIZE
            
            # Only draw the glow if the player has the key
            if level.has_key:
                # Use the open door glow
                exit_glow_key = 'exit_open_glow'
                
                if exit_glow_key in tile_images:
                    # Create pulsating effect using sine wave
                    pulse = abs(math.sin(pygame.time.get_ticks() / 400))  # Slightly faster pulsing
                    
                    # Make the glow larger and more intense for better visibility
                    glow_size_modifier = 1.2 + pulse * 0.3  # Varies between 1.2x and 1.5x
                    
                    # Original glow surface
                    original_glow = tile_images[exit_glow_key]
                    glow_width = int(original_glow.get_width() * glow_size_modifier)
                    glow_height = int(original_glow.get_height() * glow_size_modifier)
                    
                    # Scale the glow based on pulse
                    try:
                        glow_surface = pygame.transform.scale(original_glow, (glow_width, glow_height))
                    except Exception:
                        # Fallback if scaling fails
                        glow_surface = original_glow.copy()
                    
                    # Adjust alpha based on pulse for pulsating effect
                    alpha_min = 150
                    alpha_range = 105
                    glow_surface.set_alpha(int(alpha_min + alpha_range * pulse))
                    
                    # Center the glow on the exit door
                    glow_x = tile_x + TILE_SIZE // 2 - glow_surface.get_width() // 2
                    glow_y = tile_y + TILE_SIZE // 2 - glow_surface.get_height() // 2
                    
                    surface.blit(glow_surface, (glow_x, glow_y))

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
            
    def drop_fire_sword(self):
        """Drop a fire sword when the level 2 boss is defeated"""
        if self.room_type == 'boss' and self.boss and self.boss.health <= 0 and self.level_number == 2 and not self.fire_sword_dropped:
            # Instead of dropping the fire sword directly, create a treasure chest in the middle of the room
            
            # Calculate the center of the room in tile coordinates
            center_x = self.width // 2
            center_y = self.height // 2
            
            # Mark this position as a destroyable wall (treasure chest)
            self.tiles[center_y][center_x] = 1  # Wall tile
            self.destroyable_walls[center_y][center_x] = True  # Destroyable
            
            # Store the position of this special chest
            self.fire_sword_chest_x = center_x
            self.fire_sword_chest_y = center_y
            self.has_fire_sword_chest = True
            self.fire_sword_dropped = True
            
            print(f"Level 2 boss defeated! A treasure chest has appeared in the center of the room at {center_x}, {center_y}")
            
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

    def try_pickup_weapon(self, player_rect):
        """Check if player is touching a weapon pickup"""
        for pickup in self.weapon_pickups:
            if not pickup.collected and pickup.rect.colliderect(player_rect):
                pickup.collected = True
                print(f"Weapon pickup collected: {pickup.weapon_type}")
                return pickup.weapon_type
        return None

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
        
        # Add ghost texture selection for level 3
        self.selected_ghost_texture = None
        if level_number == 3:
            self.selected_ghost_texture = self.get_random_enemy_texture('ghost')
        
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
        
        # Notification system
        self.notification_text = None
        self.notification_color = (255, 255, 0)  # Default yellow
        self.notification_time = 0
        self.notification_duration = 0
        
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
        
        # Exit door tile placeholder - this will be overridden by custom sprite
        exit_door = pygame.Surface((TILE_SIZE, TILE_SIZE))
        exit_door.fill((50, 150, 50))
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
        
        # Exit door open placeholder (for when player has key)
        exit_door_open = exit_door.copy()
        exit_door_open.fill((50, 200, 50))  # Brighter green
        # Add different exit symbol
        pygame.draw.polygon(exit_door_open, (255, 255, 255), 
            [(TILE_SIZE//4, TILE_SIZE//4), 
             (3*TILE_SIZE//4, TILE_SIZE//4),
             (TILE_SIZE//2, 3*TILE_SIZE//4)])
        tiles['exit_open'] = exit_door_open
        
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
            
            # Load custom exit door texture
            exit_door_path = os.path.join(TILE_SPRITES_PATH, "doors/exit/exit_door.png")
            if os.path.exists(exit_door_path):
                tiles['exit'] = self.asset_manager.load_image(exit_door_path, scale=(TILE_SIZE, TILE_SIZE))
                print(f"Loaded exit door texture: exit_door.png")
            
            # Load open exit door texture
            exit_door_open_path = os.path.join(TILE_SPRITES_PATH, "doors/exit/exit_door_open.png")
            if os.path.exists(exit_door_open_path):
                tiles['exit_open'] = self.asset_manager.load_image(exit_door_open_path, scale=(TILE_SIZE, TILE_SIZE))
                print(f"Loaded open exit door texture: exit_door_open.png")
                
            # Create glowing version of the exit door
            if "exit" in tiles:
                # Create a copy of the exit door with a glow effect
                exit_glow = tiles['exit'].copy()
                # Yellow/white glow surface
                glow_surf = pygame.Surface((TILE_SIZE + 8, TILE_SIZE + 8), pygame.SRCALPHA)
                pygame.draw.circle(glow_surf, (255, 255, 100, 128), (TILE_SIZE // 2 + 4, TILE_SIZE // 2 + 4), TILE_SIZE // 2 + 4)
                # Store the glowing version
                tiles['exit_glow'] = glow_surf
            
            # Create glowing version of the open exit door
            if "exit_open" in tiles:
                # Create a copy of the open exit door with a glow effect
                exit_open_glow = tiles['exit_open'].copy()
                # Brighter glow for open door
                glow_surf = pygame.Surface((TILE_SIZE + 12, TILE_SIZE + 12), pygame.SRCALPHA)
                pygame.draw.circle(glow_surf, (255, 255, 0, 150), (TILE_SIZE // 2 + 6, TILE_SIZE // 2 + 6), TILE_SIZE // 2 + 6)
                # Store the glowing version
                tiles['exit_open_glow'] = glow_surf
                
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
        print(f"Level: Trying to destroy wall at {x},{y} in room {self.current_room_coords}")
        current_room = self.rooms[self.current_room_coords]
        result = current_room.try_destroy_wall(x, y)
        print(f"Result of wall destruction: {result}")
        return result
        
    def check_health_pickup(self, player_rect):
        """Check if player is touching a health pickup in the current room"""
        if self.current_room_coords in self.rooms:
            room = self.rooms[self.current_room_coords]
            return room.try_pickup_health(player_rect)
        return 0
        
    def check_arrow_pickup(self, player_rect):
        """Check if player is touching an arrow pickup in the current room"""
        if self.current_room_coords in self.rooms:
            room = self.rooms[self.current_room_coords]
            return room.try_pickup_arrows(player_rect)
        return 0
        
    def check_weapon_pickup(self, player_rect):
        """Check if player is touching a weapon pickup in the current room"""
        if self.current_room_coords in self.rooms:
            room = self.rooms[self.current_room_coords]
            return room.try_pickup_weapon(player_rect)
        return None
        
    def draw(self, surface):
        """Draw only the current room"""
        if self.current_room_coords in self.rooms:
            room = self.rooms[self.current_room_coords]
            room.draw(surface, self.tiles, self)
            
            # Draw notification if active
            if self.notification_text:
                current_time = pygame.time.get_ticks()
                time_elapsed = current_time - self.notification_time
                
                if time_elapsed < self.notification_duration:
                    # Create pulsing effect
                    pulse = 0.7 + 0.3 * abs(math.sin(time_elapsed / 200))
                    
                    try:
                        # Try to use a nice font
                        font_path = os.path.join(ASSET_PATH, "fonts/PixelatedEleganceRegular-ovyAA.ttf")
                        font = pygame.font.Font(font_path, 28)
                    except:
                        # Fallback to system font
                        font = pygame.font.Font(None, 32)
                        
                    # Create text surface
                    text = font.render(self.notification_text, True, self.notification_color)
                    text_rect = text.get_rect(center=(WINDOW_WIDTH//2, 80))
                    
                    # Create background for better readability
                    bg_rect = text_rect.inflate(40, 20)
                    bg_surf = pygame.Surface((bg_rect.width, bg_rect.height), pygame.SRCALPHA)
                    pygame.draw.rect(bg_surf, (0, 0, 0, 180), bg_surf.get_rect(), 0, 10)
                    surface.blit(bg_surf, bg_rect)
                    
                    # Apply pulse effect to text
                    if pulse < 1.0:
                        # Scale alpha based on pulse
                        alpha = int(255 * pulse)
                        alpha_surf = pygame.Surface(text.get_size(), pygame.SRCALPHA)
                        alpha_surf.fill((255, 255, 255, alpha))
                        text.blit(alpha_surf, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
                    
                    # Draw the text
                    surface.blit(text, text_rect)
                else:
                    # Clear notification after duration expires
                    self.notification_text = None
        
    def draw_exit_confirmation(self, surface):
        """Draw confirmation dialog when trying to exit level"""
        # This dialog should be drawn directly on the screen, not affected by camera zoom
        
        # Darken the screen
        overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))  # Semi-transparent black
        surface.blit(overlay, (0, 0))
        
        # Create the dialog box with rounded corners
        dialog_width = 400
        dialog_height = 200
        dialog_x = (WINDOW_WIDTH - dialog_width) // 2
        dialog_y = (WINDOW_HEIGHT - dialog_height) // 2
        
        dialog_rect = pygame.Rect(dialog_x, dialog_y, dialog_width, dialog_height)
        
        # Draw a rounded rectangle for the dialog
        dialog_surface = pygame.Surface((dialog_width, dialog_height), pygame.SRCALPHA)
        dialog_surface.fill((0, 0, 0, 0))  # Transparent
        
        # Dialog background color
        dialog_bg_color = (80, 50, 30, 230)  # Dark brown with transparency
        dialog_border_color = (255, 255, 0)  # Yellow border to match menu buttons
        
        # Draw dialog with rounded corners (similar to button style)
        pygame.draw.rect(dialog_surface, dialog_bg_color, pygame.Rect(0, 0, dialog_width, dialog_height), 0, 15)
        pygame.draw.rect(dialog_surface, dialog_border_color, pygame.Rect(0, 0, dialog_width, dialog_height), 3, 15)
        
        surface.blit(dialog_surface, dialog_rect)
        
        # Load the pixelated font
        font_path = os.path.join(ASSET_PATH, "fonts/PixelatedEleganceRegular-ovyAA.ttf")
        if os.path.exists(font_path):
            font = pygame.font.Font(font_path, 30)  # Reduced from 36 to 30
            small_font = pygame.font.Font(font_path, 28)  # Reduced from 30 to 28
        else:
            font = pygame.font.Font(None, 30)  # Reduced from 36 to 30
            small_font = pygame.font.Font(None, 28)  # Reduced from 30 to 28
        
        # Dialog text with pixelated font
        text = font.render("Exit to next level?", True, (255, 245, 225))
        text_rect = text.get_rect(center=(WINDOW_WIDTH // 2, dialog_y + 65))  # Adjusted from 60 to 65
        surface.blit(text, text_rect)
        
        # Buttons
        button_width = 120
        button_height = 50
        button_spacing = 40
        
        # Yes button with rounded corners
        yes_rect = pygame.Rect(
            dialog_x + (dialog_width // 2) - button_width - (button_spacing // 2),
            dialog_y + dialog_height - 70,
            button_width,
            button_height
        )
        
        # Create button surfaces with rounded corners
        yes_surface = pygame.Surface((button_width, button_height), pygame.SRCALPHA)
        yes_surface.fill((0, 0, 0, 0))  # Transparent
        
        # Button colors - matching menu buttons
        yes_color = (80, 50, 30, 230)  # Dark background
        yes_border = (255, 255, 0)     # Yellow border
        
        # Draw rounded rectangle for YES button
        pygame.draw.rect(yes_surface, yes_color, pygame.Rect(0, 0, button_width, button_height), 0, 10)
        pygame.draw.rect(yes_surface, yes_border, pygame.Rect(0, 0, button_width, button_height), 3, 10)
        
        surface.blit(yes_surface, yes_rect)
        
        # Text with slight shadow for better readability
        yes_text_shadow = small_font.render("YES", True, (0, 0, 0, 180))
        yes_text = small_font.render("YES", True, (255, 245, 225))  # Same color as menu buttons
        
        yes_text_rect = yes_text.get_rect(center=yes_rect.center)
        yes_shadow_rect = yes_text_rect.copy()
        yes_shadow_rect.x += 2
        yes_shadow_rect.y += 2
        
        surface.blit(yes_text_shadow, yes_shadow_rect)
        surface.blit(yes_text, yes_text_rect)
        
        # No button with rounded corners
        no_rect = pygame.Rect(
            dialog_x + (dialog_width // 2) + (button_spacing // 2),
            dialog_y + dialog_height - 70,
            button_width,
            button_height
        )
        
        # Create no button surface
        no_surface = pygame.Surface((button_width, button_height), pygame.SRCALPHA)
        no_surface.fill((0, 0, 0, 0))  # Transparent
        
        # Button colors
        no_color = (80, 50, 30, 230)  # Dark background
        no_border = (255, 255, 0)     # Yellow border
        
        # Draw rounded rectangle for NO button
        pygame.draw.rect(no_surface, no_color, pygame.Rect(0, 0, button_width, button_height), 0, 10)
        pygame.draw.rect(no_surface, no_border, pygame.Rect(0, 0, button_width, button_height), 3, 10)
        
        surface.blit(no_surface, no_rect)
        
        # Text with slight shadow
        no_text_shadow = small_font.render("NO", True, (0, 0, 0, 180))
        no_text = small_font.render("NO", True, (255, 245, 225))  # Same color as menu buttons
        
        no_text_rect = no_text.get_rect(center=no_rect.center)
        no_shadow_rect = no_text_rect.copy()
        no_shadow_rect.x += 2
        no_shadow_rect.y += 2
        
        surface.blit(no_text_shadow, no_shadow_rect)
        surface.blit(no_text, no_text_rect)
        
        # Return button rects for click handling
        return yes_rect, no_rect 

    def show_notification(self, message, color=(255, 255, 0), duration=3000):
        """Show a notification message"""
        self.notification_text = message
        self.notification_color = color
        self.notification_time = pygame.time.get_ticks()
        self.notification_duration = duration
        print(f"Showing notification: {message}")