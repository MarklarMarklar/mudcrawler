import pygame
import math
import random
import os
from scripts.enemy import Boss, Enemy, BossProjectile
from scripts.asset_manager import get_asset_manager
from scripts.sound_manager import get_sound_manager
from config import TILE_SIZE, BOSS_TYPES, BOSS_SPRITES_PATH

class DarkLord(Boss):
    """
    Level 10 Final Boss implementation with specialized pentagram ritual mechanics,
    ability to summon other bosses, and multiple complex phases.
    """
    def __init__(self, x, y, level_instance=None):
        # Initialize with level 10
        super().__init__(x, y, 10, level_instance)
        
        # Override base stats to ensure they're correct
        self.health = 2000
        self.max_health = self.health
        self.damage = 30
        self.speed = 1
        self.name = "Dark Lord"
        
        # Dark Lord specific attributes
        self.copies = []
        self.pentagram_active = False
        self.pentagram_completion = 0  # 0-100% completion of the ritual
        self.ritual_active = False
        self.introduction_complete = False
        self.introduction_timer = 0
        self.introduction_duration = 5000  # 5 seconds for introduction
        self.ritual_timer = 0
        self.ritual_duration = 15000  # 15 seconds to complete the ritual
        self.pentagram_pulse = 0
        
        # Pentagram summoning mechanics
        self.blinking_copy_index = None
        self.summoned_boss = None
        self.summoning_active = False
        self.blink_interval = 300  # milliseconds between blinks
        self.last_blink_time = 0
        self.blink_state = True  # True = visible, False = invisible
        
        # Pentagram points and visualization
        self.pentagram_points = []
        self.active_pentagram_points = [True, True, True, True, True]  # Track which points have circles
        self.pentagram_center = (0, 0)  # Will be set during pentagram creation
        self.draw_pentagram_circles = True
        self.pentagram_circle_radius = 8
        self.pentagram_circle_color = (200, 0, 100)  # Magenta-ish circles
        self.pentagram_line_color = (180, 0, 80, 120)  # Semi-transparent magenta lines
        self.pentagram_line_width = 2
        self.outer_circle_radius = 0  # Will be calculated based on pentagram size
        self.outer_circle_color = (150, 0, 150, 80)  # Semi-transparent purple
        self.outer_circle_width = 3
        
        # Death zone properties
        self.death_zone_enabled = True 
        self.death_zone_warning_shown = False
        self.last_death_zone_warning_time = 0
        self.death_zone_warning_interval = 1000  # Show warning every 1 second
        
        # Summoned bosses
        self.summoned_bosses = pygame.sprite.Group()
        self.max_summoned_bosses = 2  # Maximum number of bosses summoned at once
        self.boss_summon_cooldown = 20000  # 20 seconds between boss summons
        self.last_boss_summon_time = 0
        
        # Phase tracking
        self.phase_thresholds = [0.8, 0.6, 0.4, 0.2]  # Health percentage thresholds for phase changes
        self.current_phase = 0
        self.phases = [
            "introduction",
            "pentagram_ritual", 
            "minion_summoning",
            "boss_summoning",
            "final_form"
        ]
        self.phase_start_time = pygame.time.get_ticks()
        
        # Ability tracking
        self.available_abilities = []
        self.current_ability = None
        self.ability_cooldown = 8000  # 8 seconds between ability uses
        self.last_ability_time = 0
        
        # Visual effects
        self.particles = []
        self.aura_size = 0
        self.aura_pulse_direction = 1
        self.aura_color = (120, 0, 120)  # Purple aura
        
        # Load specialized images for Dark Lord
        self.load_dark_lord_images()
        
        # Start visible during introduction
        self.visible = True
        
        # Debug attributes
        self.debug_messages = []
        
        # Clear the boss room of normal enemies
        if level_instance and hasattr(level_instance, 'current_room'):
            self.clear_boss_room()
        
    def load_dark_lord_images(self):
        """Load specialized images for the Dark Lord"""
        try:
            # Try to load specific Dark Lord images
            dark_lord_path = os.path.join(BOSS_SPRITES_PATH, "boss_10.png")
            if os.path.exists(dark_lord_path):
                self.image = self.asset_manager.load_image(
                    dark_lord_path, scale=(TILE_SIZE*2.5, TILE_SIZE*2.5)
                )
                print(f"Loaded specialized Dark Lord image: {dark_lord_path}")
                
                # Ensure the image is properly centered on the rect
                self.rect = self.image.get_rect(center=(self.rect.centerx, self.rect.centery))
            
            # Load copy/clone image
            copy_path = os.path.join(BOSS_SPRITES_PATH, "boss_10_copy.png")
            if os.path.exists(copy_path):
                self.copy_image = self.asset_manager.load_image(
                    copy_path, scale=(TILE_SIZE*2, TILE_SIZE*2)
                )
            else:
                # If no specific copy image, use the main image but tinted
                self.copy_image = self.image.copy() if hasattr(self, 'image') else None
            
            # Load final form image
            final_form_path = os.path.join(BOSS_SPRITES_PATH, "boss_10_final.png")
            if os.path.exists(final_form_path):
                self.final_form_image = self.asset_manager.load_image(
                    final_form_path, scale=(TILE_SIZE*3, TILE_SIZE*3)
                )
            
        except Exception as e:
            print(f"Error loading Dark Lord images: {e}")
    
    def start_introduction(self):
        """Begin the boss introduction sequence"""
        self.introduction_timer = pygame.time.get_ticks()
        self.introduction_complete = False
        self.visible = True
        self.state = "idle"
        
        # Play introduction sound
        self.sound_manager.play_sound("effects/boss_10_intro")
        
        # Add debug message
        self.add_debug_message("Dark Lord introduction sequence started")
    
    def complete_introduction(self):
        """Complete the introduction and start the pentagram ritual"""
        self.introduction_complete = True
        self.visible = False  # Main boss disappears
        self.create_pentagram_copies()
        
        # Play ritual begin sound
        self.sound_manager.play_sound("effects/boss_10_ritual")
        
        # Add debug message
        self.add_debug_message("Introduction complete, pentagram ritual started")
    
    def create_pentagram_copies(self):
        """Create 5 copies in pentagram formation"""
        self.copies = []
        self.pentagram_points = []
        self.active_pentagram_points = [True, True, True, True, True]
        
        # Find the center of the room
        if hasattr(self, 'level_instance') and self.level_instance and hasattr(self.level_instance, 'current_room'):
            room = self.level_instance.current_room
            center_x = (room.width // 2) * TILE_SIZE
            center_y = (room.height // 2) * TILE_SIZE
        else:
            # Fallback to position near the boss
            center_x = self.rect.centerx
            center_y = self.rect.centery
        
        # Store the center of the pentagram
        self.pentagram_center = (center_x, center_y)
        
        radius = 4 * TILE_SIZE  # 4 tiles away from center
        # Set outer circle to match exactly with the pentagram points
        self.outer_circle_radius = radius
        
        # Create 5 copies in a pentagram pattern
        # Start angle at -π/2 (90 degrees) so the first copy is at the north position
        start_angle = -math.pi / 2  # North position
        
        for i in range(5):
            angle = start_angle + (2 * math.pi * i) / 5  # Divide the circle into 5 points, starting from north
            target_x = center_x + radius * math.cos(angle)
            target_y = center_y + radius * math.sin(angle)
            
            # Store pentagram point positions
            self.pentagram_points.append((target_x, target_y))
            
            # Create copy at the boss's position and have it move to the target
            new_copy = DarkLordCopy(self.rect.centerx, self.rect.centery, self, i)
            new_copy.target_x = target_x
            new_copy.target_y = target_y
            new_copy.is_moving = True
            new_copy.move_speed = random.uniform(0.08, 0.12)  # Random speed for more natural movement
            
            self.copies.append(new_copy)
        
        self.pentagram_active = True
        self.ritual_timer = pygame.time.get_ticks()
        self.ritual_active = True
        
        # Wait for copies to reach their positions before selecting one to blink
        # We'll set this in the update method after all copies have reached their positions
        self.blinking_copy_index = None
        self.copies_positioned = False
        
        # Add debug message
        self.add_debug_message(f"Created {len(self.copies)} copies for pentagram ritual")
    
    def start_summoning(self):
        """Start the boss summoning process from the blinking copy"""
        self.summoning_active = True
        self.last_blink_time = pygame.time.get_ticks()
        
        # Add debug message
        self.add_debug_message("Started summoning from blinking copy")
        
        # Play summoning sound
        self.sound_manager.play_sound("effects/boss_summon")
    
    def update_blinking_copy(self):
        """Update the blinking copy during summoning"""
        if not self.summoning_active or self.blinking_copy_index is None:
            return
            
        current_time = pygame.time.get_ticks()
        
        # Update blink state
        if current_time - self.last_blink_time > self.blink_interval:
            self.last_blink_time = current_time
            self.blink_state = not self.blink_state
            
            # Update the blinking copy's visibility
            if self.blinking_copy_index < len(self.copies):
                blinking_copy = self.copies[self.blinking_copy_index]
                if self.blink_state:
                    blinking_copy.alpha = blinking_copy.original_alpha
                else:
                    blinking_copy.alpha = 50  # Almost invisible during blink
                
                blinking_copy.image.set_alpha(blinking_copy.alpha)
        
        # Check if it's time to summon the boss
        if self.summoning_active and not self.summoned_boss and current_time - self.ritual_timer > 5000:
            self.summon_level2_boss()
    
    def summon_level2_boss(self):
        """Summon the level 2 boss from the blinking copy"""
        if self.summoned_boss:
            return
            
        if self.blinking_copy_index is None or self.blinking_copy_index >= len(self.copies):
            return
            
        # Get the position of the blinking copy for the effect
        blinking_copy = self.copies[self.blinking_copy_index]
        effect_x = blinking_copy.rect.centerx
        effect_y = blinking_copy.rect.centery
        
        # But spawn the boss at the center of the pentagram/room
        spawn_x = self.pentagram_center[0]
        spawn_y = self.pentagram_center[1]
        
        # Create a level 2 boss with reduced stats
        self.summoned_boss = Boss(spawn_x, spawn_y, 2, self.level_instance)
        
        # Increase health significantly (500% of original health)
        self.summoned_boss.health = self.summoned_boss.health * 1.0  
        self.summoned_boss.max_health = self.summoned_boss.health
        self.summoned_boss.damage = self.summoned_boss.damage * 0.7  # 70% damage
        
        # Remove room boundary restrictions for the summoned boss
        # This replaces the default update method to prevent boundary clamping
        original_update = self.summoned_boss.update
        
        def unrestricted_update(player):
            # Store old position
            old_rect = self.summoned_boss.rect.copy()
            
            # Call the original update method
            result = original_update(player)
            
            # Apply a speed reduction factor to prevent erratic movement
            speed_factor = 0.5  # Reduces speed by half
            
            # Move with reduced velocity
            self.summoned_boss.rect.x += self.summoned_boss.velocity_x * speed_factor
            self.summoned_boss.rect.y += self.summoned_boss.velocity_y * speed_factor
            
            # Check for collisions with walls only
            if (hasattr(player, 'level') and player.level and 
                player.level.check_collision(self.summoned_boss.collision_rect, check_only_walls=True)):
                # If collision with wall, revert position
                self.summoned_boss.rect = old_rect.copy()
                
                # If hitting a wall, try changing direction
                if random.random() < 0.5:
                    self.summoned_boss.velocity_x = -self.summoned_boss.velocity_x
                    self.summoned_boss.velocity_y = -self.summoned_boss.velocity_y
            
            # Update hitboxes with new position
            self.summoned_boss.collision_rect.center = self.summoned_boss.rect.center
            self.summoned_boss.damage_hitbox.center = self.summoned_boss.rect.center
            
            return result
        
        # Replace the summoned boss's update method with our unrestricted version
        self.summoned_boss.update = lambda player: unrestricted_update(player)
        
        # Make sure the hitbox is set up correctly
        self.summoned_boss.damage_hitbox = pygame.Rect(
            self.summoned_boss.rect.centerx - self.summoned_boss.rect.width // 4,
            self.summoned_boss.rect.centery - self.summoned_boss.rect.height // 4,
            self.summoned_boss.rect.width // 2,
            self.summoned_boss.rect.height // 2
        )
        
        # Make sure the boss is visible and active
        self.summoned_boss.visible = True
        self.summoned_boss.active = True
        self.summoned_boss.invulnerable = False
        self.summoned_boss.has_been_hit_this_swing = False
        
        # Give the boss a distinct appearance
        if hasattr(self.summoned_boss, 'image') and self.summoned_boss.image:
            # Add a red tint to indicate it's a summoned version
            red_tint = pygame.Surface(self.summoned_boss.image.get_size()).convert_alpha()
            red_tint.fill((255, 0, 0, 100))  # Semi-transparent red
            temp_img = self.summoned_boss.image.copy()
            temp_img.blit(red_tint, (0, 0))
            self.summoned_boss.image = temp_img
        
        # Add to summoned bosses group
        self.summoned_bosses.add(self.summoned_boss)
        
        # Add to level's enemies list if available to ensure collision detection works
        if self.level_instance and hasattr(self.level_instance, 'current_room'):
            if hasattr(self.level_instance.current_room, 'enemies'):
                self.level_instance.current_room.enemies.append(self.summoned_boss)
            
            # If the room has a bosses list, add it there too
            if hasattr(self.level_instance.current_room, 'bosses'):
                if not self.level_instance.current_room.bosses:
                    self.level_instance.current_room.bosses = []
                self.level_instance.current_room.bosses.append(self.summoned_boss)
        
        # Create summoning effect at the blinking copy position
        self.create_summon_effect(effect_x, effect_y)
        
        # Also create summoning effect at the center where the boss appears
        self.create_summon_effect(spawn_x, spawn_y)
        
        # Add debug message
        self.add_debug_message("Summoned Level 2 boss from blinking copy")
    
    def create_summon_effect(self, x, y):
        """Create visual effect for boss summoning"""
        if hasattr(self, 'particle_manager') and self.particle_manager:
            for _ in range(30):
                angle = random.uniform(0, math.pi * 2)
                distance = random.uniform(0, TILE_SIZE)
                pos_x = x + math.cos(angle) * distance
                pos_y = y + math.sin(angle) * distance
                
                self.particle_manager.add_particle(
                    particle_type='fade',
                    pos=(pos_x, pos_y),
                    velocity=(0, 0),
                    direction=0,
                    color=(150, 50, 200),
                    size=random.randint(4, 10),
                    lifetime=random.randint(20, 40)
                )
    
    def check_summoned_boss_status(self):
        """Check if the summoned boss has been defeated"""
        if not self.summoned_boss:
            return
            
        # Check if the boss has been defeated (health <= 0)
        if self.summoned_boss.health <= 0:
            # Boss was defeated
            self.handle_summoned_boss_defeat()
            self.summoned_bosses.remove(self.summoned_boss)
            self.summoned_boss = None
            return
            
        # Check if the boss is still in the summoned_bosses group
        if self.summoned_boss not in self.summoned_bosses:
            # Boss was removed from group for some other reason
            self.handle_summoned_boss_defeat()
            self.summoned_boss = None
    
    def handle_summoned_boss_defeat(self):
        """Handle the defeat of the summoned boss"""
        if self.blinking_copy_index is None or self.blinking_copy_index >= len(self.copies):
            return
            
        # Get the position of the blinking copy for the explosion effect
        blinking_copy = self.copies[self.blinking_copy_index]
        explosion_x = blinking_copy.rect.centerx
        explosion_y = blinking_copy.rect.centery
        
        # Create explosion effect
        self.create_explosion_effect(explosion_x, explosion_y)
        
        # Mark this pentagram point as inactive (no circle)
        if 0 <= self.blinking_copy_index < len(self.active_pentagram_points):
            self.active_pentagram_points[self.blinking_copy_index] = False
        
        # Remove the blinking copy but keep its pentagram point
        self.copies.pop(self.blinking_copy_index)
        
        # Remove from level's enemies list if it was added
        if self.level_instance and hasattr(self.level_instance, 'current_room') and self.summoned_boss:
            if hasattr(self.level_instance.current_room, 'enemies') and self.summoned_boss in self.level_instance.current_room.enemies:
                self.level_instance.current_room.enemies.remove(self.summoned_boss)
            
            # Remove from bosses list too if it exists
            if hasattr(self.level_instance.current_room, 'bosses') and self.summoned_boss in self.level_instance.current_room.bosses:
                self.level_instance.current_room.bosses.remove(self.summoned_boss)
        
        # Reset blinking copy index
        self.blinking_copy_index = None
        self.summoning_active = False
        
        # Add debug message
        self.add_debug_message("Summoned boss defeated, removed copy from pentagram")
    
    def create_explosion_effect(self, x, y):
        """Create explosion effect when a copy is removed"""
        if hasattr(self, 'particle_manager') and self.particle_manager:
            for _ in range(50):
                angle = random.uniform(0, math.pi * 2)
                speed = random.uniform(1, 5)
                size = random.randint(3, 10)
                lifetime = random.randint(30, 60)
                
                # Calculate velocity based on angle and speed
                vx = math.cos(angle) * speed
                vy = math.sin(angle) * speed
                
                # Add particle with purple/red color
                r = random.randint(150, 255)
                g = random.randint(0, 50)
                b = random.randint(100, 255)
                
                self.particle_manager.add_particle(
                    particle_type='fade',
                    pos=(x, y),
                    velocity=(vx, vy),
                    direction=angle,
                    color=(r, g, b),
                    size=size,
                    lifetime=lifetime
                )
    
    def update_pentagram(self):
        """Update the pentagram ritual progress"""
        if not self.pentagram_active:
            return
            
        current_time = pygame.time.get_ticks()
        
        # Update pentagram pulse effect
        self.pentagram_pulse = (math.sin(current_time / 300) + 1) / 2  # Value between 0 and 1
        
        # Check if all copies have reached their positions
        if not self.copies_positioned:
            all_positioned = True
            for copy in self.copies:
                if copy.is_moving:
                    all_positioned = False
                    break
                    
            if all_positioned:
                self.copies_positioned = True
                # Now select a copy to blink and start summoning
                self.blinking_copy_index = random.randint(0, 4)
                self.copies[self.blinking_copy_index].is_blinking = True
                self.copies[self.blinking_copy_index].will_summon_boss = True
                self.start_summoning()
                self.add_debug_message(f"Copy {self.blinking_copy_index} will summon boss")
                
        # Update blinking copy if in summoning state
        if self.summoning_active and self.blinking_copy_index is not None:
            self.update_blinking_copy()
        
        # Check if summoned boss has been defeated
        self.check_summoned_boss_status()
        
        # Update all copies
        for copy in self.copies:
            copy.update()
    
    def is_player_in_death_zone(self, player):
        """Check if player is inside the death zone circle"""
        if not self.pentagram_active or not self.death_zone_enabled or not player:
            return False
            
        # Calculate distance from player to pentagram center
        dx = player.rect.centerx - self.pentagram_center[0]
        dy = player.rect.centery - self.pentagram_center[1]
        distance = math.sqrt(dx*dx + dy*dy)
        
        # Check if player is inside the circle
        return distance <= self.outer_circle_radius
    
    def apply_death_zone_effect(self, player):
        """Apply the death zone effect to the player - instant death"""
        if not player or not hasattr(player, 'take_damage'):
            return
            
        # Get current time
        current_time = pygame.time.get_ticks()
        
        # Show warning message at intervals for better player feedback
        if (current_time - self.last_death_zone_warning_time > self.death_zone_warning_interval):
            self.last_death_zone_warning_time = current_time
            
            # Display warning message if the game has a display_message function
            if hasattr(player, 'level') and hasattr(player.level, 'game') and hasattr(player.level.game, 'display_message'):
                player.level.game.display_message("DANGER! Pentagram Death Zone!", (255, 0, 0))
        
        # Create visual effects to show the player they're in danger
        if hasattr(self, 'particle_manager') and self.particle_manager:
            # Create particles around player
            for _ in range(5):
                angle = random.uniform(0, math.pi * 2)
                distance = random.uniform(10, 20)
                pos_x = player.rect.centerx + math.cos(angle) * distance
                pos_y = player.rect.centery + math.sin(angle) * distance
                
                self.particle_manager.add_particle(
                    particle_type='fade',
                    pos=(pos_x, pos_y),
                    velocity=(0, 0),
                    direction=0, 
                    color=(255, 0, 0),
                    size=random.randint(4, 8),
                    lifetime=random.randint(10, 20)
                )
        
        # Apply fatal damage to player (9999 should be enough to kill any player)
        player.take_damage(9999)
    
    def update(self, player):
        """Override update method to handle specialized behavior"""
        # Get current time
        current_time = pygame.time.get_ticks()
        
        # Handle introduction phase
        if not self.introduction_complete:
            if not self.introduction_timer:
                self.start_introduction()
            
            elapsed_time = current_time - self.introduction_timer
            if elapsed_time >= self.introduction_duration:
                self.complete_introduction()
            return
        
        # Handle pentagram phase
        if self.pentagram_active:
            self.update_pentagram()
            
            # Check if player is in the death zone and apply effects if they are
            if self.is_player_in_death_zone(player):
                self.apply_death_zone_effect(player)
            
            # Update copies
            for copy in self.copies:
                copy.update(player)
            
            # Update summoned bosses
            for boss in self.summoned_bosses:
                boss.update(player)
                
            return
        
        # Update summoned bosses
        for boss in self.summoned_bosses:
            boss.update(player)
        
        # Remove dead summoned bosses (except the special Level 2 boss tied to a copy)
        for boss in list(self.summoned_bosses):
            if boss.health <= 0 and boss != self.summoned_boss:
                self.summoned_bosses.remove(boss)
        
        # Regular boss logic
        super().update(player)
        
        # Update projectiles if any
        if hasattr(self, 'projectiles') and self.projectiles:
            self.projectiles.update()
            
            # Check collisions with player
            for projectile in self.projectiles:
                if hasattr(projectile, 'check_collision') and projectile.check_collision(player.rect):
                    player.take_damage(projectile.damage)
        
        # Check phase changes based on health percentage
        health_percentage = self.health / self.max_health
        
        # Check if we need to advance phase based on health
        for i, threshold in enumerate(self.phase_thresholds):
            if health_percentage <= threshold and self.current_phase <= i:
                self.advance_phase()
                break
        
        # Random chance to use an ability
        ability_chance = 0.01 + (0.005 * self.current_phase)  # 1% base chance, increasing with phase
        if random.random() < ability_chance:
            self.use_random_ability(player)
    
    def draw(self, surface):
        """Override draw method to handle special visual effects"""
        if not self.visible:
            # Don't draw the main boss if not visible
            pass
        else:
            # Draw aura around boss
            self.draw_aura(surface)
            
            # Draw the main boss
            super().draw(surface)
        
        # Draw the pentagram if active (draw this first so it appears behind everything else)
        if self.pentagram_active:
            self.draw_pentagram(surface)
        
        # Draw copies
        for copy in self.copies:
            copy.draw(surface)
        
        # Draw projectiles if any
        if hasattr(self, 'projectiles') and self.projectiles:
            for projectile in self.projectiles:
                if hasattr(projectile, 'draw'):
                    projectile.draw(surface)
                else:
                    # Fallback if projectile doesn't have draw method
                    surface.blit(projectile.image, projectile.rect)
        
        # Draw summoned bosses
        for boss in self.summoned_bosses:
            boss.draw(surface)
            
            # Draw health bar for summoned boss
            if boss == self.summoned_boss and boss.health > 0:
                # Position the health bar above the boss
                health_bar_width = boss.rect.width
                health_bar_height = 6
                health_percent = boss.health / boss.max_health
                
                # Background (dark red)
                health_bar_bg = pygame.Rect(
                    boss.rect.x, 
                    boss.rect.y - 15, 
                    health_bar_width, 
                    health_bar_height
                )
                pygame.draw.rect(surface, (80, 0, 0), health_bar_bg)
                
                # Foreground (bright red)
                health_bar_fg = pygame.Rect(
                    boss.rect.x, 
                    boss.rect.y - 15, 
                    health_bar_width * health_percent, 
                    health_bar_height
                )
                pygame.draw.rect(surface, (255, 50, 50), health_bar_fg)
                
                # Border
                pygame.draw.rect(surface, (0, 0, 0), health_bar_bg, 1)
        
        # Draw debug messages
        if DEBUG_MODE:
            self.draw_debug_messages(surface, None)
    
    def draw_aura(self, surface, camera=None):
        """Draw an aura around the boss"""
        if not self.visible:
            return
            
        # Calculate aura size based on phase and pulsing
        base_size = TILE_SIZE * (1.5 + self.current_phase * 0.5)  # Size increases with phase
        pulse_amount = math.sin(pygame.time.get_ticks() / 300) * TILE_SIZE * 0.2
        aura_size = base_size + pulse_amount
        
        # Create aura surface with transparency
        aura_surface = pygame.Surface((aura_size * 2, aura_size * 2), pygame.SRCALPHA)
        
        # Draw multiple layers of the aura
        center = (aura_size, aura_size)
        
        # Outer aura rings
        aura_alpha = 30 + self.current_phase * 10  # Alpha increases with phase
        for i in range(5):
            radius = aura_size - i * (aura_size / 10)
            pygame.draw.circle(
                aura_surface, 
                (*self.aura_color, aura_alpha - i * 5), 
                center, 
                radius
            )
        
        # Position the aura centered on the boss
        aura_pos = (
            self.rect.centerx - aura_size,
            self.rect.centery - aura_size
        )
        
        # Draw the aura
        surface.blit(aura_surface, aura_pos)
    
    def draw_pentagram(self, surface):
        """Draw pentagram connecting the copies"""
        if not self.pentagram_points or len(self.pentagram_points) < 5:
            return
            
        # Draw large circle around the entire pentagram
        if self.pentagram_active and self.outer_circle_radius > 0:
            # Pulsing alpha for outer circle - make it more intense and visible
            circle_alpha = int(100 + 80 * self.pentagram_pulse)  # Pulsing alpha between 100-180
            outer_circle_color = list(self.outer_circle_color[:3]) + [circle_alpha]
            
            # Draw the outer circle with slight pulse in size - more intense pulsing
            radius_pulse = self.outer_circle_radius * (0.96 + 0.08 * self.pentagram_pulse)
            pygame.draw.circle(
                surface,
                outer_circle_color,
                (int(self.pentagram_center[0]), int(self.pentagram_center[1])),
                int(radius_pulse),
                self.outer_circle_width
            )
            
            # Draw a fainter, smaller inner circle to enhance the death zone effect
            inner_radius = self.outer_circle_radius * 0.9
            inner_circle_color = (255, 0, 0, 30 + int(50 * self.pentagram_pulse))  # Red with pulsing alpha
            pygame.draw.circle(
                surface,
                inner_circle_color,
                (int(self.pentagram_center[0]), int(self.pentagram_center[1])),
                int(inner_radius),
                2
            )
            
        # Draw lines between points to form a pentagram
        # Draw lines in the order of a pentagram (not just connecting adjacent points)
        pentagram_order = [0, 2, 4, 1, 3, 0]  # Connect points in this order, back to start
        
        # Draw lines with pulsing alpha
        line_alpha = int(100 + 100 * self.pentagram_pulse)  # Pulsing alpha between 100-200
        line_color = list(self.pentagram_line_color[:3]) + [line_alpha]  # RGB + updated alpha
        
        # Draw the pentagram lines
        for i in range(len(pentagram_order) - 1):
            start_idx = pentagram_order[i]
            end_idx = pentagram_order[i+1]
            
            if start_idx < len(self.pentagram_points) and end_idx < len(self.pentagram_points):
                start_pos = self.pentagram_points[start_idx]
                end_pos = self.pentagram_points[end_idx]
                
                pygame.draw.line(
                    surface, 
                    line_color, 
                    start_pos, 
                    end_pos, 
                    self.pentagram_line_width
                )
        
        # Draw circles at each active point of the pentagram
        if self.draw_pentagram_circles:
            for i, point in enumerate(self.pentagram_points):
                # Only draw circles for active points
                if i < len(self.active_pentagram_points) and self.active_pentagram_points[i]:
                    # Pulsing circle size
                    circle_radius = self.pentagram_circle_radius * (0.8 + 0.4 * self.pentagram_pulse)
                    
                    # Draw the circle with glowing effect
                    pygame.draw.circle(
                        surface,
                        self.pentagram_circle_color,
                        (int(point[0]), int(point[1])),
                        int(circle_radius)
                    )
                    
                    # Inner brighter circle
                    pygame.draw.circle(
                        surface,
                        (min(255, self.pentagram_circle_color[0] + 50),
                         min(255, self.pentagram_circle_color[1] + 50),
                         min(255, self.pentagram_circle_color[2] + 50)),
                        (int(point[0]), int(point[1])),
                        int(circle_radius * 0.6)
                    )
    
    def add_debug_message(self, message):
        """Add a debug message to be displayed"""
        if not DEBUG_MODE:
            return
            
        current_time = pygame.time.get_ticks()
        self.debug_messages.append({
            'text': message,
            'time': current_time,
            'duration': 5000  # 5 seconds
        })
        
        # Limit number of messages
        if len(self.debug_messages) > 5:
            self.debug_messages.pop(0)
    
    def draw_debug_messages(self, surface, camera):
        """Draw debug messages"""
        if not DEBUG_MODE or not self.debug_messages:
            return
            
        current_time = pygame.time.get_ticks()
        font = pygame.font.SysFont('Arial', 14)
        
        # Remove expired messages
        self.debug_messages = [msg for msg in self.debug_messages 
                              if current_time - msg['time'] < msg['duration']]
        
        # Draw messages
        for i, msg in enumerate(self.debug_messages):
            text = font.render(msg['text'], True, (255, 255, 255))
            text_rect = text.get_rect(topleft=(10, 10 + i * 20))
            surface.blit(text, text_rect)
    
    def clear_boss_room(self):
        """Clear the boss room of any normal enemies"""
        if not self.level_instance or not hasattr(self.level_instance, 'current_room'):
            return
            
        # Get current room
        room = self.level_instance.current_room
        
        # Remove all normal enemies from the room
        if hasattr(room, 'enemies'):
            # Create a copy of the enemies list to avoid modification during iteration
            enemies_to_remove = [enemy for enemy in room.enemies if not isinstance(enemy, Boss)]
            for enemy in enemies_to_remove:
                if enemy in room.enemies:
                    room.enemies.remove(enemy)
                    
            # Add debug message
            self.add_debug_message(f"Cleared {len(enemies_to_remove)} normal enemies from boss room")

class DarkLordCopy(pygame.sprite.Sprite):
    """A copy/clone of the Dark Lord that participates in the ritual"""
    def __init__(self, x, y, master, index):
        super().__init__()
        self.master = master  # Reference to the main boss
        self.index = index    # Position index (0-4)
        
        # Get image from master or create a default
        if hasattr(master, 'copy_image') and master.copy_image:
            self.original_image = master.copy_image.copy()
        elif hasattr(master, 'image') and master.image:
            self.original_image = master.image.copy()
        else:
            # Create a default image if none is available
            self.original_image = pygame.Surface((TILE_SIZE*2, TILE_SIZE*2), pygame.SRCALPHA)
            pygame.draw.circle(
                self.original_image,
                (150, 0, 200),
                (TILE_SIZE, TILE_SIZE),
                TILE_SIZE
            )
        
        self.image = self.original_image.copy()
        self.rect = self.image.get_rect(center=(x, y))
        
        # Visual properties
        self.alpha = 180  # Slightly transparent
        self.original_alpha = self.alpha
        self.pulsing = True
        self.phase_offset = index * (2 * math.pi / 5)  # Offset the pulse for each copy
        
        # Movement properties
        self.is_moving = False
        self.target_x = x
        self.target_y = y
        self.move_speed = 0.1
        self.x = float(x)
        self.y = float(y)
        
        # Summoning properties
        self.is_blinking = False
        self.will_summon_boss = False
        
        # Particle effects
        self.particles = []
        self.particle_timer = 0
        self.particle_interval = 200  # 200ms between particle effects
        
        # Set initial alpha
        self.image.set_alpha(self.alpha)
    
    def update(self, player=None):
        """Update the copy's state"""
        current_time = pygame.time.get_ticks()
        
        # Handle movement to the target position
        if self.is_moving:
            # Calculate distance to target
            dx = self.target_x - self.x
            dy = self.target_y - self.y
            distance = math.sqrt(dx*dx + dy*dy)
            
            # If we're very close to the target, snap to it
            if distance < 2.0:
                self.x = self.target_x
                self.y = self.target_y
                self.is_moving = False
            else:
                # Move towards the target
                direction_x = dx / distance
                direction_y = dy / distance
                
                # Move with easing (slower as approaching target)
                move_amount = min(distance, self.move_speed * distance)
                self.x += direction_x * move_amount
                self.y += direction_y * move_amount
            
            # Update the rect position
            self.rect.centerx = int(self.x)
            self.rect.centery = int(self.y)
            
            # Add motion trail particles
            if hasattr(self.master, 'particle_manager') and self.master.particle_manager:
                if random.random() < 0.3:  # 30% chance each update
                    particle_x = self.rect.centerx + random.randint(-10, 10)
                    particle_y = self.rect.centery + random.randint(-10, 10)
                    
                    self.master.particle_manager.add_particle(
                        particle_type='fade',
                        pos=(particle_x, particle_y),
                        velocity=(0, 0),
                        direction=0,
                        color=(120, 0, 180),
                        size=random.randint(2, 5),
                        lifetime=random.randint(10, 20)
                    )
        
        # Only apply pulsing if this copy is not the blinking one
        if self.pulsing and not self.is_blinking:
            # Add pulsing effect
            pulse = math.sin((current_time / 500) + self.phase_offset) * 50 + 180
            self.alpha = max(100, min(230, pulse))
            self.image.set_alpha(self.alpha)
        
        # Add occasional particle effects
        if current_time - self.particle_timer > self.particle_interval:
            self.particle_timer = current_time
            
            # Check if master has particle manager
            if hasattr(self.master, 'particle_manager') and self.master.particle_manager:
                # Add more particles for the blinking copy
                particle_count = 4 if self.is_blinking else 2
                
                for _ in range(particle_count):
                    angle = random.uniform(0, math.pi * 2)
                    distance = random.uniform(0, TILE_SIZE)
                    pos_x = self.rect.centerx + math.cos(angle) * distance
                    pos_y = self.rect.centery + math.sin(angle) * distance
                    
                    # Different colors for blinking copy
                    if self.is_blinking:
                        color = (200, 50, 150)  # More reddish for the summoning copy
                    else:
                        color = (150, 0, 200)  # Purple for normal copies
                    
                    self.master.particle_manager.add_particle(
                        particle_type='fade',
                        pos=(pos_x, pos_y),
                        velocity=(0, 0),
                        direction=0,
                        color=color,
                        size=random.randint(2, 5),
                        lifetime=random.randint(10, 20)
                    )
    
    def draw(self, surface):
        """Draw the copy"""
        surface.blit(self.image, self.rect)
        
        # Draw particles
        for particle in self.particles:
            particle.draw(surface)
    
    def destroy(self):
        """Create destruction effect when the copy is removed"""
        if hasattr(self.master, 'particle_manager') and self.master.particle_manager:
            # Create explosive particles
            for _ in range(20):
                angle = random.uniform(0, math.pi * 2)
                speed = random.uniform(1, 3)
                size = random.randint(3, 8)
                lifetime = random.randint(20, 40)
                
                # Calculate velocity based on angle and speed
                vx = math.cos(angle) * speed
                vy = math.sin(angle) * speed
                
                # Add particle with purple color
                self.master.particle_manager.add_particle(
                    particle_type='fade',
                    pos=(self.rect.centerx, self.rect.centery),
                    velocity=(vx, vy),
                    direction=angle,
                    color=(150, 0, 200),
                    size=size,
                    lifetime=lifetime
                )

# Add this constant if not available in config.py
if not 'DEBUG_MODE' in globals():
    DEBUG_MODE = False 