import pygame
import math
import os
from config import *
from asset_manager import get_asset_manager
from sound_manager import get_sound_manager

class Player(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.asset_manager = get_asset_manager()
        self.sound_manager = get_sound_manager()
        
        # Game instance will be set from main.py
        self.game = None
        
        # Load player animations from sprite sheet
        self.animations = {
            'idle': {},
            'walk': {},
            'attack': {},
            'dead': {}  # Add dead animation state
        }
        
        # Death animation variables
        self.is_dead = False
        self.death_animation_complete = False
        self.death_time = 0
        
        # Trailing effect for dodge - use a similar implementation to boss
        self.trailing_enabled = False  # Flag to indicate if trailing effect is active
        self.trail_start_time = 0      # When the trail effect started
        self.trail_duration = 500      # How long trail lasts in milliseconds (increased from 150ms)
        self.trail_positions = []      # List of positions for trail images
        
        # Initialize dodge cooldown tracking
        self.last_dodge_time = 0       # Initialize to 0 so dodge is available immediately
        
        # Load the sprite sheet
        sprite_sheet_path = os.path.join(PLAYER_SPRITES_PATH, "my_character_guides.png")
        if os.path.exists(sprite_sheet_path):
            try:
                self.sprite_sheet = self.asset_manager.load_image(sprite_sheet_path)
                print(f"Successfully loaded sprite sheet: {sprite_sheet_path}")
                
                # Extract frames from the sprite sheet
                self.extract_sprites_from_sheet()
            except Exception as e:
                print(f"Error loading sprite sheet: {sprite_sheet_path}")
                print(f"Exception: {e}")
                # Initialize with placeholders if sprite sheet fails to load
                self.init_placeholders()
        else:
            print(f"Sprite sheet does not exist: {sprite_sheet_path}")
            # Initialize with placeholders if sprite sheet doesn't exist
            self.init_placeholders()
            
        # Load death animation from separate image
        try:
            death_image_path = os.path.join(PLAYER_SPRITES_PATH, "player_dies.png")
            if os.path.exists(death_image_path):
                death_image = self.asset_manager.load_image(death_image_path, scale=(TILE_SIZE, TILE_SIZE))
                # Add death image to all directions for simplicity
                for direction in ['down', 'up', 'left', 'right']:
                    self.animations['dead'][direction] = [death_image]
                print(f"Successfully loaded death animation: {death_image_path}")
            else:
                print(f"Death animation not found: {death_image_path}")
                # Use placeholder for death animation
                placeholder = pygame.Surface((TILE_SIZE, TILE_SIZE))
                placeholder.fill((200, 0, 0))  # Red placeholder
                for direction in ['down', 'up', 'left', 'right']:
                    self.animations['dead'][direction] = [placeholder]
        except Exception as e:
            print(f"Error loading death animation: {e}")
            # Use placeholder for death animation if loading fails
            placeholder = pygame.Surface((TILE_SIZE, TILE_SIZE))
            placeholder.fill((200, 0, 0))  # Red placeholder
            for direction in ['down', 'up', 'left', 'right']:
                self.animations['dead'][direction] = [placeholder]
        
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
        
        # Create a smaller collision rect for better movement through narrow passages
        # Make it 60% of the original size, centered within the sprite
        hitbox_width = int(TILE_SIZE * 0.6)
        hitbox_height = int(TILE_SIZE * 0.6)
        hitbox_x = x + (TILE_SIZE - hitbox_width) // 2
        hitbox_y = y + (TILE_SIZE - hitbox_height) // 2
        self.hitbox = pygame.Rect(hitbox_x, hitbox_y, hitbox_width, hitbox_height)
        
        # Player stats
        self.health = PLAYER_START_HEALTH
        self.speed = PLAYER_SPEED
        self.arrow_count = 10  # Start with 10 arrows
        self.max_arrows = 10  # Maximum arrows the player can carry
        
        # Weapon cooldowns
        self.sword_cooldown = 0
        self.bow_cooldown = 0
        self.last_attack_time = pygame.time.get_ticks()
        
        # Walking sound management
        self.last_movement_state = 'idle'  # Track the previous movement state
        self.walk_sound_channel = None     # Track the sound channel for walking
        
        # Movement
        self.velocity_x = 0
        self.velocity_y = 0
    
    def init_placeholders(self):
        """Initialize placeholder graphics if sprite sheet can't be loaded"""
        for direction in ['down', 'up', 'left', 'right']:
            # Create default colored placeholder
            placeholder = pygame.Surface((TILE_SIZE, TILE_SIZE))
            placeholder.fill(BLUE)
            
            # Add directional indicator
            indicator_color = WHITE
            indicator_size = TILE_SIZE // 3
            if direction == 'up':
                pygame.draw.polygon(placeholder, indicator_color, 
                                   [(TILE_SIZE//2, TILE_SIZE//4), 
                                    (TILE_SIZE//2 - indicator_size//2, TILE_SIZE//2),
                                    (TILE_SIZE//2 + indicator_size//2, TILE_SIZE//2)])
            elif direction == 'down':
                pygame.draw.polygon(placeholder, indicator_color, 
                                   [(TILE_SIZE//2, TILE_SIZE*3//4), 
                                    (TILE_SIZE//2 - indicator_size//2, TILE_SIZE//2),
                                    (TILE_SIZE//2 + indicator_size//2, TILE_SIZE//2)])
            elif direction == 'left':
                pygame.draw.polygon(placeholder, indicator_color, 
                                   [(TILE_SIZE//4, TILE_SIZE//2), 
                                    (TILE_SIZE//2, TILE_SIZE//2 - indicator_size//2),
                                    (TILE_SIZE//2, TILE_SIZE//2 + indicator_size//2)])
            elif direction == 'right':
                pygame.draw.polygon(placeholder, indicator_color, 
                                   [(TILE_SIZE*3//4, TILE_SIZE//2), 
                                    (TILE_SIZE//2, TILE_SIZE//2 - indicator_size//2),
                                    (TILE_SIZE//2, TILE_SIZE//2 + indicator_size//2)])
            
            # Use placeholders for all animation states
            self.animations['idle'][direction] = [placeholder]
            self.animations['walk'][direction] = [placeholder]
            self.animations['attack'][direction] = [placeholder]
    
    def extract_sprites_from_sheet(self):
        """Extract all sprites from the sprite sheet"""
        # Actual sprite size (without guide lines)
        sprite_width = 15  # Width of each sprite in the sheet
        sprite_height = 22  # Height of each sprite in the sheet
        
        # Account for the green guide lines between sprites
        # The horizontal and vertical spacing between sprites
        h_spacing = 1  # 1 pixel green line between columns
        v_spacing = 1  # 1 pixel green line between rows
        
        # Mapping of rows in the sprite sheet to animation directions
        # Updated to match the correct order:
        # 1. player down (row 0)
        # 2. player right (row 1)
        # 3. player up (row 2)
        # 4. player left (row 3)
        # 5. player attack down (row 4)
        # 6. player attack up (row 5)
        # 7. player attack right (row 6)
        # 8. player attack left (row 7)
        direction_map = {
            0: ('walk', 'down'),
            1: ('walk', 'right'),
            2: ('walk', 'up'),
            3: ('walk', 'left'),
            4: ('attack', 'down'),
            5: ('attack', 'up'),
            6: ('attack', 'right'),
            7: ('attack', 'left')
        }
        
        # Number of frames per animation
        frames_per_row = 4
        
        # Extract each sprite from the sheet
        for row, (animation_type, direction) in direction_map.items():
            frames = []
            for col in range(frames_per_row):
                # Calculate position in the sprite sheet, accounting for guide lines
                # Skip the initial green line (1px) and add spacing for each subsequent sprite
                x = 1 + col * (sprite_width + h_spacing)
                y = 1 + row * (sprite_height + v_spacing)
                
                # Create a new surface for this sprite
                sprite = pygame.Surface((sprite_width, sprite_height), pygame.SRCALPHA)
                
                # Copy the sprite from the sheet
                sprite.blit(self.sprite_sheet, (0, 0), (x, y, sprite_width, sprite_height))
                
                # Scale to tile size if needed
                if sprite_width != TILE_SIZE or sprite_height != TILE_SIZE:
                    sprite = pygame.transform.scale(sprite, (TILE_SIZE, TILE_SIZE))
                
                frames.append(sprite)
            
            # Store the frames in the animations dictionary
            self.animations[animation_type][direction] = frames
            
            # Also use the first frame of walk animation for idle
            if animation_type == 'walk':
                self.animations['idle'][direction] = [frames[0]]
        
    def move(self, keys):
        self.velocity_x = 0
        self.velocity_y = 0
        
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.velocity_x = -self.speed
            self.facing = 'left'
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.velocity_x = self.speed
            self.facing = 'right'
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            self.velocity_y = -self.speed
            self.facing = 'up'
        if keys[pygame.K_DOWN] or keys[pygame.K_s]:
            self.velocity_y = self.speed
            self.facing = 'down'
            
        # Update animation state based on movement
        previous_state = self.current_state
        if self.velocity_x == 0 and self.velocity_y == 0:
            self.current_state = 'idle'
        else:
            self.current_state = 'walk'
            
        # Handle walk sound state transitions - only play sounds if player is alive
        if self.health > 0:
            if previous_state == 'idle' and self.current_state == 'walk':
                # Player started walking - play the new shorter walking sound and loop it
                self.walk_sound_channel = self.sound_manager.play_sound("effects/walk", loop=-1)
            elif previous_state == 'walk' and self.current_state == 'idle':
                # Player stopped walking - stop sound
                self.sound_manager.stop_sound_channel(self.walk_sound_channel)
                self.walk_sound_channel = None
        elif self.walk_sound_channel is not None:
            # Player is dead but sound is still playing - stop it
            self.sound_manager.stop_sound_channel(self.walk_sound_channel)
            self.walk_sound_channel = None
            
        # Normalize diagonal movement
        if self.velocity_x != 0 and self.velocity_y != 0:
            self.velocity_x /= math.sqrt(2)
            self.velocity_y /= math.sqrt(2)
            
    def dodge(self):
        """Perform a quick dodge (jump) in the direction the player is facing"""
        # Check if player is dead
        if self.is_dead:
            return False
            
        # Get the current time for cooldown checks
        current_time = pygame.time.get_ticks()
        
        # Add cooldown to prevent dodge spam
        if hasattr(self, 'last_dodge_time') and current_time - self.last_dodge_time < 1500:  # 1500ms cooldown
            return False
            
        # Set the last dodge time
        self.last_dodge_time = current_time
        
        # Calculate dodge distance (1 tile)
        dodge_distance = TILE_SIZE
        
        # Calculate target position based on facing direction
        target_x = self.rect.x
        target_y = self.rect.y
        
        if self.facing == 'right':
            target_x += dodge_distance
        elif self.facing == 'left':
            target_x -= dodge_distance
        elif self.facing == 'down':
            target_y += dodge_distance
        elif self.facing == 'up':
            target_y -= dodge_distance
            
        # Store original position
        original_x = self.rect.x
        original_y = self.rect.y
        original_hitbox_x = self.hitbox.x
        original_hitbox_y = self.hitbox.y
        
        # Enable trailing effect and store the trail positions
        self.trailing_enabled = True
        self.trail_start_time = current_time
        
        # Store the exact positions where ghost images should appear
        self.trail_positions = []
        
        # Calculate positions for ghost images based on starting position and dodge direction
        if self.facing == 'right':
            # When dodging right, distribute ghosts from arrival position back to starting position
            # First ghost (i=0) at the farthest point from arrival, last ghost (i=3) at arrival position
            for i in range(4):
                fraction = i / 3  # 0/3, 1/3, 2/3, 3/3 (0, 0.33, 0.67, 1)
                # Interpolate between original position and target position
                ghost_x = original_x + (target_x - original_x) * fraction
                # Add slight offset for better visibility (reduced by 50%)
                offset = 2 + (3-i) * 8  # 26, 18, 10, 2 pixels
                ghost_x -= offset
                self.trail_positions.append((ghost_x, original_y))
        elif self.facing == 'left':
            # When dodging left, distribute ghosts from arrival position back to starting position
            for i in range(4):
                fraction = i / 3  # 0/3, 1/3, 2/3, 3/3 (0, 0.33, 0.67, 1)
                # Interpolate between original position and target position
                ghost_x = original_x + (target_x - original_x) * fraction
                # Add slight offset for better visibility (reduced by 50%)
                offset = 2 + (3-i) * 8  # 26, 18, 10, 2 pixels
                ghost_x += offset
                self.trail_positions.append((ghost_x, original_y))
        elif self.facing == 'down':
            # When dodging down, distribute ghosts from arrival position back to starting position
            for i in range(4):
                fraction = i / 3  # 0/3, 1/3, 2/3, 3/3 (0, 0.33, 0.67, 1)
                # Interpolate between original position and target position
                ghost_y = original_y + (target_y - original_y) * fraction
                # Add slight offset for better visibility (reduced by 50%)
                offset = 2 + (3-i) * 8  # 26, 18, 10, 2 pixels
                ghost_y -= offset
                self.trail_positions.append((original_x, ghost_y))
        elif self.facing == 'up':
            # When dodging up, distribute ghosts from arrival position back to starting position
            for i in range(4):
                fraction = i / 3  # 0/3, 1/3, 2/3, 3/3 (0, 0.33, 0.67, 1)
                # Interpolate between original position and target position
                ghost_y = original_y + (target_y - original_y) * fraction
                # Add slight offset for better visibility (reduced by 50%)
                offset = 2 + (3-i) * 8  # 26, 18, 10, 2 pixels
                ghost_y += offset
                self.trail_positions.append((original_x, ghost_y))
        
        # Move to target position
        self.rect.x = target_x
        self.rect.y = target_y
        
        # Update hitbox position
        self.hitbox.centerx = self.rect.centerx
        self.hitbox.centery = self.rect.centery
        
        # Check for collision
        if self.game and hasattr(self.game, 'level') and self.game.level:
            if self.game.level.check_collision(self.hitbox):
                # Collision detected, revert to original position
                self.rect.x = original_x
                self.rect.y = original_y
                self.hitbox.x = original_hitbox_x
                self.hitbox.y = original_hitbox_y
                
                # Try to dodge only up to the wall
                if self.facing == 'right':
                    # Find the closest wall on the right
                    for test_x in range(original_x + 1, target_x + 1):
                        self.rect.x = test_x
                        self.hitbox.centerx = self.rect.centerx
                        if self.game.level.check_collision(self.hitbox):
                            # Go back one pixel to be just before the wall
                            self.rect.x = test_x - 1
                            self.hitbox.centerx = self.rect.centerx
                            break
                elif self.facing == 'left':
                    # Find the closest wall on the left
                    for test_x in range(original_x - 1, target_x - 1, -1):
                        self.rect.x = test_x
                        self.hitbox.centerx = self.rect.centerx
                        if self.game.level.check_collision(self.hitbox):
                            # Go back one pixel to be just before the wall
                            self.rect.x = test_x + 1
                            self.hitbox.centerx = self.rect.centerx
                            break
                elif self.facing == 'down':
                    # Find the closest wall below
                    for test_y in range(original_y + 1, target_y + 1):
                        self.rect.y = test_y
                        self.hitbox.centery = self.rect.centery
                        if self.game.level.check_collision(self.hitbox):
                            # Go back one pixel to be just before the wall
                            self.rect.y = test_y - 1
                            self.hitbox.centery = self.rect.centery
                            break
                elif self.facing == 'up':
                    # Find the closest wall above
                    for test_y in range(original_y - 1, target_y - 1, -1):
                        self.rect.y = test_y
                        self.hitbox.centery = self.rect.centery
                        if self.game.level.check_collision(self.hitbox):
                            # Go back one pixel to be just before the wall
                            self.rect.y = test_y + 1
                            self.hitbox.centery = self.rect.centery
                            break
        
        # Play dodge sound if available
        self.sound_manager.play_sound("effects/dodge")
        
        # Keep player on screen
        screen_rect = pygame.display.get_surface().get_rect()
        self.rect.clamp_ip(screen_rect)
        self.hitbox.centerx = self.rect.centerx
        self.hitbox.centery = self.rect.centery
        
        return True
        
    def attack_sword(self):
        current_time = pygame.time.get_ticks()
        if current_time - self.last_attack_time >= SWORD_COOLDOWN:
            self.last_attack_time = current_time
            self.current_state = 'attack'
            self.frame = 0  # Reset animation frame
            self.animation_time = 0  # Reset animation time
            
            # Create sword hitbox based on facing direction with 30% increased range (15% + 15%)
            attack_size = int(TILE_SIZE * 1.32)  # 32% larger than normal tile size (1.15 * 1.15 ≈ 1.32)
            
            # Check if this is a fire sword attack and adjust range if needed
            if hasattr(self, 'game') and self.game and hasattr(self.game, 'weapon_manager') and self.game.weapon_manager.has_fire_sword:
                # Make fire sword 20% larger range than normal sword
                attack_size = int(attack_size * 1.2)
                
            hitbox = pygame.Rect(self.rect.x, self.rect.y, attack_size, attack_size)
            if self.facing == 'right':
                hitbox.x += TILE_SIZE
            elif self.facing == 'left':
                hitbox.x -= TILE_SIZE
            elif self.facing == 'up':
                hitbox.y -= TILE_SIZE
            elif self.facing == 'down':
                hitbox.y += TILE_SIZE
            return hitbox
        return None
        
    def attack_bow(self, mouse_pos):
        # Check if player has arrows available
        if self.arrow_count <= 0:
            return False
            
        # Check attack cooldown
        current_time = pygame.time.get_ticks()
        if current_time - self.last_attack_time < self.bow_cooldown:
            return False
            
        # Update attack time and state
        self.last_attack_time = current_time
        self.current_state = 'attack'
        self.frame = 0  # Reset animation frame
        self.animation_time = 0  # Reset animation time
        
        # Decrement arrow count when shooting
        self.arrow_count -= 1
        
        # Calculate direction vector to mouse position (for animation only)
        dx = mouse_pos[0] - self.rect.centerx
        dy = mouse_pos[1] - self.rect.centery
        distance = math.sqrt(dx * dx + dy * dy)
        if distance > 0:
            dx = dx / distance
            dy = dy / distance
            
            # Update facing direction based on mouse position
            if abs(dx) > abs(dy):
                self.facing = 'right' if dx > 0 else 'left'
            else:
                self.facing = 'down' if dy > 0 else 'up'
        
        # Return True to indicate that the arrow was successfully shot
        return True
        
    def set_game(self, game):
        """Set the game instance for particle creation"""
        self.game = game
        
    def take_damage(self, amount):
        # Don't take damage if already dead
        if self.is_dead:
            return False
            
        self.health -= amount
        
        # Play damage sound effect
        self.sound_manager.play_sound("effects/player_dmg")
        
        # Trigger screen shake if game instance is available
        if self.game and hasattr(self.game, 'trigger_screen_shake'):
            # Scale shake amount based on damage
            shake_amount = min(12, 5 + amount)
            shake_duration = min(20, 10 + amount * 2)
            self.game.trigger_screen_shake(amount=shake_amount, duration=shake_duration)
        
        # Create blood particles effect if game instance is available
        if self.game and hasattr(self.game, 'particle_system'):
            # Create blood splatter particles at player position
            self.game.particle_system.create_blood_splash(
                self.rect.centerx,
                self.rect.centery,
                amount=max(5, int(amount * 3))  # Scale particles by damage amount
            )
            
            # Create additional directional particles based on facing direction
            if self.facing == 'left':
                offset_x = -10
                offset_y = 0
            elif self.facing == 'right':
                offset_x = 10
                offset_y = 0
            elif self.facing == 'up':
                offset_x = 0
                offset_y = -10
            else:  # down
                offset_x = 0
                offset_y = 10
                
            # Add some particles in the direction player is facing
            self.game.particle_system.create_blood_splash(
                self.rect.centerx + offset_x,
                self.rect.centery + offset_y,
                amount=3
            )
        
        if self.health <= 0:
            self.health = 0
            self._die()
            return True  # Player died
        return False
        
    def _die(self):
        """Handle player death sequence"""
        if not self.is_dead:  # Only do this once
            self.is_dead = True
            self.death_time = pygame.time.get_ticks()
            self.current_state = 'dead'
            self.animation_time = 0
            self.frame = 0
            
            # Play death sound if available
            self.sound_manager.play_sound("effects/player_dies")
            
            # Create a big blood splatter
            if self.game and hasattr(self.game, 'particle_system'):
                # Create a large blood splash centered on the player
                self.game.particle_system.create_blood_splash(
                    self.rect.centerx, 
                    self.rect.centery,
                    amount=50  # Increased from 30 to 50 for more dramatic initial effect
                )
                
                # Create directional blood splashes in all 4 directions
                offsets = [(20, 0), (-20, 0), (0, 20), (0, -20)]
                for offset_x, offset_y in offsets:
                    self.game.particle_system.create_blood_splash(
                        self.rect.centerx + offset_x,
                        self.rect.centery + offset_y,
                        amount=10  # Increased from 5 to 10
                    )
                
                # Initial blood pool effect
                self.game.particle_system.create_blood_pool(
                    self.rect.centerx,
                    self.rect.centery,
                    amount=10,
                    size_range=(6, 12)
                )
            
            # Stop any playing walking sounds when the player dies
            if self.walk_sound_channel is not None:
                self.sound_manager.stop_sound_channel(self.walk_sound_channel)
                self.walk_sound_channel = None
        
    def heal(self, amount):
        self.health = min(self.health + amount, PLAYER_START_HEALTH)
        
    def update(self):
        # Update position if not dead
        if not self.is_dead:
            self.rect.x += self.velocity_x
            self.rect.y += self.velocity_y
            
            # Update hitbox position to follow the sprite
            self.hitbox.centerx = self.rect.centerx
            self.hitbox.centery = self.rect.centery
            
            # Keep player on screen
            self.rect.clamp_ip(pygame.display.get_surface().get_rect())
        elif not self.death_animation_complete:
            # Check if death animation should be complete (after 4 seconds)
            # This is longer to allow for the zoom effect to complete
            current_time = pygame.time.get_ticks()
            if current_time - self.death_time > 4000:  # 4 seconds
                self.death_animation_complete = True
        
        # Update trailing effect (for dodge)
        current_time = pygame.time.get_ticks()
        if self.trailing_enabled:
            # Check if trail effect has expired
            if current_time - self.trail_start_time > self.trail_duration:
                self.trailing_enabled = False
        
        # Update animation
        self._update_animation()
    
    def _update_animation(self):
        """Update the animation state and frame"""
        # Update animation time
        self.animation_time += self.animation_speed
        
        # If the attack animation is done, go back to idle
        if self.current_state == 'attack' and self.animation_time >= len(self.animations[self.current_state][self.facing]):
            self.current_state = 'idle'
            self.animation_time = 0
            
        # Calculate current frame
        self.frame = int(self.animation_time) % len(self.animations[self.current_state][self.facing])
        self.image = self.animations[self.current_state][self.facing][self.frame]
    
    def update_x(self):
        """Update player position on X axis only"""
        # Update X position
        self.rect.x += self.velocity_x
        
        # Update hitbox X position to follow the sprite
        self.hitbox.centerx = self.rect.centerx
        
        # Keep player on screen (X axis)
        screen_rect = pygame.display.get_surface().get_rect()
        if self.rect.left < screen_rect.left:
            self.rect.left = screen_rect.left
            self.hitbox.centerx = self.rect.centerx
        elif self.rect.right > screen_rect.right:
            self.rect.right = screen_rect.right
            self.hitbox.centerx = self.rect.centerx
        
        # Update animation
        self._update_animation()
    
    def update_y(self):
        """Update player position on Y axis only"""
        # Update Y position
        self.rect.y += self.velocity_y
        
        # Update hitbox Y position to follow the sprite
        self.hitbox.centery = self.rect.centery
        
        # Keep player on screen (Y axis)
        screen_rect = pygame.display.get_surface().get_rect()
        if self.rect.top < screen_rect.top:
            self.rect.top = screen_rect.top
            self.hitbox.centery = self.rect.centery
        elif self.rect.bottom > screen_rect.bottom:
            self.rect.bottom = screen_rect.bottom
            self.hitbox.centery = self.rect.centery
        
        # No need to update animation here, it's already done in update_x if both are called
        # But if only moving on Y axis, we still need to update animation
        if self.velocity_x == 0:
            self._update_animation()
    
    def add_arrows(self, amount):
        """Add arrows to the player's inventory, up to the maximum"""
        self.arrow_count = min(self.arrow_count + amount, self.max_arrows)
        return amount
    
    def draw(self, surface):
        # Draw trail effect if enabled (much simpler implementation)
        if self.trailing_enabled:
            current_time = pygame.time.get_ticks()
            time_in_effect = current_time - self.trail_start_time
            
            # Only draw trails during the effect duration
            if time_in_effect < self.trail_duration:
                # Draw ghost images with decreasing opacity and staggered disappearance
                for i, (ghost_x, ghost_y) in enumerate(self.trail_positions):
                    # Calculate a staggered duration for each ghost image
                    # Furthest ghost (i=0) disappears first, closest ghost (i=3) disappears last
                    staggered_duration = self.trail_duration * (0.7 + (i * 0.1))  # 70%, 80%, 90%, 100% of total duration
                    
                    # Skip this ghost image if its staggered time has expired
                    if time_in_effect > staggered_duration:
                        continue
                        
                    # Calculate alpha based on remaining time (fade out)
                    # Each ghost fades relative to its own duration
                    alpha_factor = 1.0 - (time_in_effect / staggered_duration)
                    alpha_factor = alpha_factor * alpha_factor  # Quadratic falloff for faster fade
                    
                    ghost_img = self.image.copy().convert_alpha()
                    
                    # Calculate alpha for this trail image (further back = more transparent)
                    # Base alpha decreases with distance
                    base_alpha = 90 - i * 15  # 90, 75, 60, 45 - decreasing transparency
                    trail_alpha = int(base_alpha * alpha_factor)
                    ghost_img.set_alpha(trail_alpha)
                    
                    # Draw ghost image at its fixed position
                    surface.blit(ghost_img, (ghost_x, ghost_y))
        
        # Then draw the player
        surface.blit(self.image, self.rect)
        
        # Draw dodge cooldown indicator (small blue bar above player's head)
        if hasattr(self, 'last_dodge_time'):
            current_time = pygame.time.get_ticks()
            cooldown_time = 1500  # 1.5 seconds cooldown (same as in dodge method)
            time_since_dodge = current_time - self.last_dodge_time
            
            if time_since_dodge < cooldown_time:
                # Calculate remaining cooldown as a percentage
                cooldown_remaining = 1 - (time_since_dodge / cooldown_time)
                
                # Bar dimensions
                bar_width = 20
                bar_height = 3
                
                # Position bar above player's head
                bar_x = self.rect.centerx - bar_width / 2
                bar_y = self.rect.y - 5  # 5 pixels above player
                
                # Draw background of bar (darker blue)
                pygame.draw.rect(surface, (0, 0, 100), (bar_x, bar_y, bar_width, bar_height))
                
                # Draw the filled portion of the bar (brighter blue)
                filled_width = bar_width * cooldown_remaining
                pygame.draw.rect(surface, (0, 100, 255), (bar_x, bar_y, filled_width, bar_height))
        
        # Uncomment to debug hitbox visualization
        # pygame.draw.rect(surface, (0, 255, 0), self.hitbox, 1)
        
        # Health bar removed - already displayed in HUD 