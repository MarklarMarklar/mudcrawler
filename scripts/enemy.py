import pygame
import math
import random
import os
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
        
        # Movement
        self.velocity_x = 0
        self.velocity_y = 0
        
    def take_damage(self, amount):
        self.health -= amount
        if self.health <= 0:
            self.health = 0
            return True  # Enemy died
        return False
        
    def move_towards_player(self, player):
        # Calculate direction vector to player
        dx = player.rect.centerx - self.rect.centerx
        dy = player.rect.centery - self.rect.centery
        distance = math.sqrt(dx * dx + dy * dy)
        
        if distance > 0:
            # Normalize direction
            dx = dx / distance
            dy = dy / distance
            
            # Set velocity
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
        elif distance <= self.detection_range:
            self.state = 'chase'
            self.current_state = 'walk'
            self.move_towards_player(player)
        else:
            self.state = 'idle'
            self.current_state = 'idle'
            self.velocity_x = 0
            self.velocity_y = 0
            
        # Store the old position to revert if collision happens
        old_rect = self.rect.copy()
        
        # Move horizontally first
        self.rect.x += self.velocity_x
        
        # If this would cause a collision, revert the horizontal movement
        if hasattr(player, 'level') and player.level.check_collision(self.rect):
            self.rect = old_rect.copy()
        
        # Now try to move vertically
        self.rect.y += self.velocity_y
        
        # If this would cause a collision, revert the vertical movement
        if hasattr(player, 'level') and player.level.check_collision(self.rect):
            self.rect = old_rect.copy()
        
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
        
        # Set initial image
        self.image = self.animations[self.current_state][self.facing][0]
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        
        # Boss-specific attributes
        self.phase = 1
        self.max_phases = 3
        self.special_attack_cooldown = 3000  # 3 seconds
        self.last_special_attack_time = 0
        
        # Position history for trailing effect (used by level 1 boss)
        self.trail_enabled = level == 1  # Only enable for level 1 boss
        self.position_history = []
        self.max_trail_length = 5  # Store 5 previous positions
        self.trail_update_rate = 4  # Update trail every 4 frames
        self.trail_frame_counter = 0
        
        # Sound manager for boss voice
        self.sound_manager = get_sound_manager()
        
        # Boss voice related attributes
        self.has_seen_player = False
        self.last_voice_time = 0
        self.voice_cooldown = 4000  # 4 seconds (in milliseconds)
        
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
        
    def update(self, player):
        # Call the parent update method to handle basic movement and attacks
        super().update(player)
        
        # Calculate distance to player (needed for voice effect)
        dx = player.rect.centerx - self.rect.centerx
        dy = player.rect.centery - self.rect.centery
        distance = math.sqrt(dx * dx + dy * dy)
        
        # Current time for cooldown calculations
        current_time = pygame.time.get_ticks()
        
        # Handle boss voice sound effect
        if distance <= self.detection_range:
            # Boss has detected the player
            if not self.has_seen_player:
                # First time seeing player, play voice sound
                self.sound_manager.play_sound("effects/boss_1_voice")
                self.has_seen_player = True
                self.last_voice_time = current_time
                print("Boss has seen the player! Playing voice sound.")
            elif current_time - self.last_voice_time >= self.voice_cooldown:
                # Repeat the voice sound every 4 seconds
                self.sound_manager.play_sound("effects/boss_1_voice")
                self.last_voice_time = current_time
                print("Boss repeating voice sound.")
        
        # Update position history for trailing effect if enabled
        if self.trail_enabled:
            self.trail_frame_counter += 1
            if self.trail_frame_counter >= self.trail_update_rate:
                self.trail_frame_counter = 0
                # Store current position and image
                self.position_history.append({
                    'pos': (self.rect.x, self.rect.y),
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
                
                # Draw the ghost image at the historical position
                surface.blit(ghost_image, pos_data['pos'])
        
        # Draw the current image (fully opaque)
        surface.blit(self.image, self.rect)
        
        # Draw health bar
        health_bar_width = 60  # Wider than regular enemies
        health_bar_height = 6
        health_ratio = self.health / self.enemy_data['health']
        pygame.draw.rect(surface, RED, (self.rect.x, self.rect.y - 12,
                                      health_bar_width, health_bar_height))
        pygame.draw.rect(surface, GREEN, (self.rect.x, self.rect.y - 12,
                                        health_bar_width * health_ratio, health_bar_height)) 