import pygame
import math
import random
import os
import types
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
        
        # Make the boss invulnerable at the start
        self.invulnerable = True
        
        # Dark Lord specific attributes
        self.copies = []
        self.pentagram_active = False
        self.pentagram_completion = 0  # 0-100% completion of the ritual
        self.ritual_active = False
        self.introduction_complete = False
        self.introduction_timer = 0
        self.introduction_duration = 3000  # 5 seconds for introduction
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
        
        # Death ray attributes
        self.phase = 1  # Start with phase 1
        self.death_rays_active = False
        self.death_ray_length = 5 * TILE_SIZE  # 5 tiles
        self.death_ray_current_length = 0  # Current length during growth
        self.death_ray_growth_active = False
        self.death_ray_growth_speed = 0.1  # Tiles per update
        self.death_ray_growth_start_time = 0
        self.death_ray_width = 2  # Reduced from 10 to 2 pixels to match pentagram line width
        self.death_ray_angle = 0  # Starting angle (will be rotated)
        self.death_ray_rotation_speed = 0.0002  # Radians per millisecond
        self.base_ray_rotation_speed = 0.0002  # Store the base rotation speed for reference
        self.death_ray_damage = 30  # Damage per hit
        self.death_ray_hit_cooldown = 500  # ms between hits
        self.death_ray_last_hit_time = 0
        self.death_ray_color = (255, 0, 0, 200)  # Red with some transparency
        self.death_ray_spin_active = False  # Only start spinning after growth
        self.rays_fully_grown_time = 0  # When rays reached full length
        self.rays_fully_grown_delay = 3000  # 3 seconds delay before summoning boss
        self.active_death_rays = [True, True, True, True, True]  # Track which death rays are active (separate from pentagram points)
        
        # Pentagram points and visualization
        self.pentagram_points = []
        self.active_pentagram_points = [True, True, True, True, True]  # Track which points have circles
        self.pentagram_center = (0, 0)  # Will be set during pentagram creation
        self.draw_pentagram_circles = True
        self.pentagram_circle_radius = 8
        self.pentagram_circle_color = (200, 0, 100)  # Magenta-ish circles
        self.pentagram_line_color = (180, 0, 80, 120)  # Semi-transparent magenta lines
        self.pentagram_line_width = 2
        self.outer_circle_radius = 4 * TILE_SIZE  # Fixed radius of 4 tiles
        self.current_outer_circle_radius = 0  # Current radius during growth animation
        self.circle_growth_active = False  # Whether circle is growing
        self.circle_growth_start_time = 0  # When the growth animation started
        self.circle_growth_duration = 3000  # 3 seconds for growth
        self.outer_circle_color = (150, 0, 150, 80)  # Semi-transparent purple
        self.outer_circle_width = 3
        # Base rotation speed for pentagram effects
        self.base_pentagram_rotation_speed = 0.0002  # Radians per millisecond
        self.pentagram_rotation_speed = 0.0002  # Current rotation speed (can be adjusted)
        
        # New timing for sequence of events
        self.post_intro_delay = 1000  # 1 second delay after introduction before circle starts growing
        self.post_intro_timer = 0
        self.pentagram_creation_pending = False  # Flag to track when to create pentagram after circle grows
        self.pentagram_creation_progress = 0  # Track progress of creation sequence
        
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
        self.ability_cooldown = 6000  # 6 seconds between ability uses (changed from 8 to 6 sec)
        self.last_ability_time = 0
        self.ability_sequence_state = 'rope'  # Starts with rope ability
        self.post_rope_timer = 0  # Timer for delay after rope ability
        self.post_rope_delay = 1000  # 1-second delay after rope ability
        self.post_charge_timer = 0  # Timer for delay after charge ability
        self.post_charge_delay = 500  # 0.5-second delay after charge ability
        
        # Projectile attack properties
        self.projectile_attack_active = False
        self.projectiles = pygame.sprite.Group()  # Group to store all active projectiles
        self.projectile_damage = 20  # Base damage for projectiles
        self.projectile_speed = 1.3  # Speed of projectiles (reduced from 3.0)
        self.projectile_color = (200, 50, 200)  # Purple color for projectiles
        self.projectile_split_time = 1500  # Time in ms before projectiles split (2 seconds)
        
        # Visual effects
        self.particles = []
        self.aura_size = 0
        self.aura_pulse_direction = 1
        self.aura_color = (120, 0, 120)  # Purple aura
        
        # Pentagram color pulsing
        self.color_pulse_timer = 0
        self.color_pulse_duration = 1500  # 1.5 seconds for a full red-orange-red cycle (twice as fast)
        self.color_red = (255, 0, 0)
        self.color_orange = (255, 140, 0)  # Orange instead of yellow
        self.current_color = self.color_red
        
        # Load specialized images for Dark Lord
        self.load_dark_lord_images()
        
        # Start visible during introduction
        self.visible = True
        
        # Debug attributes
        self.debug_messages = []
        self.debug_enabled = DEBUG_MODE  # Initialize debug_enabled based on DEBUG_MODE
        
        # Clear the boss room of normal enemies
        if level_instance and hasattr(level_instance, 'current_room'):
            self.clear_boss_room()
        
        # Thunder effect attributes
        self.thunder_enabled = True
        self.thunder_interval_min = 5000  # 5 seconds minimum between thunder
        self.thunder_interval_max = 8000  # 8 seconds maximum between thunder
        self.next_thunder_time = pygame.time.get_ticks() + random.randint(self.thunder_interval_min, self.thunder_interval_max)
        self.thunder_flash_active = False
        self.thunder_flash_start_time = 0
        self.thunder_flash_duration = 150  # Flash lasts 150ms
        self.thunder_flash_alpha = 0  # Current opacity of the flash
        
        # Multiple flashes for thunder effect
        self.thunder_flashes = []  # Sequence of flashes with timing and intensity
        self.current_flash_index = 0
        
        # Tracking for defeated copies/bosses
        self.defeated_copies_count = 0
        
        # Mini death zones
        self.mini_death_zones = []  # List of (x, y, end_time) tuples
        self.mini_death_zone_radius = TILE_SIZE // 2  # 1 tile diameter
        self.mini_death_zone_duration = 6000  # 6 seconds
        self.mini_death_zone_damage = 50  # Damage per hit
        self.last_mini_zone_hit_time = 0
        self.mini_zone_hit_cooldown = 500  # ms between hits
        self.mini_zone_lightning_blinks = {}  # Tracking lightning visibility for each zone
        
        # Load lightning image
        self.lightning_image = None
        try:
            lightning_path = os.path.join("assets", "characters", "bosses", "lightning.png")
            if os.path.exists(lightning_path):
                self.lightning_image = pygame.image.load(lightning_path).convert_alpha()
                # Scale to appropriate size (approx 1.5 tiles)
                lightning_size = int(TILE_SIZE * 1.5)
                self.lightning_image = pygame.transform.scale(self.lightning_image, (lightning_size, lightning_size))
                self.add_debug_message("Lightning image loaded successfully")
            else:
                self.add_debug_message(f"Lightning image not found at: {lightning_path}")
        except Exception as e:
            self.add_debug_message(f"Error loading lightning image: {str(e)}")
    
        # Final phase transition
        self.final_phase_active = False
        self.final_phase_start_time = 0
        self.pentagram_fade_active = False
        self.pentagram_fade_start_time = 0
        self.pentagram_fade_duration = 3000  # 3 seconds to fade out (same as growth)
        self.chase_delay = 2000  # 2 second delay before chasing in final phase
    
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
        """Complete the introduction and prepare for pentagram ritual"""
        self.introduction_complete = True
        self.visible = True  # Keep the boss visible during the delay period
        
        # Find the center of the room for the pentagram
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
        
        # Start post-introduction delay timer
        self.post_intro_timer = pygame.time.get_ticks()
        self.pentagram_creation_pending = True
        
        # Add debug message
        self.add_debug_message("Introduction complete, preparing for pentagram ritual")
    
    def create_pentagram_copies(self):
        """Create 5 copies in pentagram formation"""
        self.copies = []
        self.pentagram_points = []
        # Make sure all 5 points are active at creation
        self.active_pentagram_points = [True, True, True, True, True]
        
        # The center was already set in complete_introduction
        
        # Create 5 copies in a pentagram pattern
        # Start angle at -π/2 (90 degrees) so the first copy is at the north position
        start_angle = -math.pi / 2  # North position
        
        for i in range(5):
            angle = start_angle + (2 * math.pi * i) / 5  # Divide the circle into 5 points, starting from north
            target_x = self.pentagram_center[0] + self.outer_circle_radius * math.cos(angle)
            target_y = self.pentagram_center[1] + self.outer_circle_radius * math.sin(angle)
            
            # Store pentagram point positions
            self.pentagram_points.append((target_x, target_y))
            
            # Create copy at the boss's position and have it move to the target
            new_copy = DarkLordCopy(self.rect.centerx, self.rect.centery, self, i)
            new_copy.target_x = target_x
            new_copy.target_y = target_y
            new_copy.is_moving = True
            new_copy.move_speed = random.uniform(0.04, 0.06)  # Half speed for easier understanding (original was 0.08-0.12)
            
            self.copies.append(new_copy)
        
        self.pentagram_active = True
        self.ritual_timer = pygame.time.get_ticks()
        self.ritual_active = True
        self.visible = False  # Main boss disappears now that copies are created
        
        # Rotation properties
        self.rotation_active = False  # Will be set to True when copies are positioned
        self.rotation_speed = 0.0005  # Slow CCW rotation in radians per millisecond
        self.rotation_angle = 0  # Current rotation angle
        self.last_rotation_time = 0  # Last time the rotation was updated

        # Wait for copies to reach their positions before selecting one to blink
        # We'll set this in the update method after all copies have reached their positions
        self.blinking_copy_index = None
        self.copies_positioned = False
        
        # Play ritual begin sound
        self.sound_manager.play_sound("effects/boss_10_ritual")
        
        # Add debug message
        self.add_debug_message(f"Created {len(self.copies)} copies for pentagram ritual")
    
    def start_summoning(self):
        """Start the boss summoning process from the blinking copy"""
        self.summoning_active = True
        self.last_blink_time = pygame.time.get_ticks()
        self.ritual_timer = pygame.time.get_ticks()  # Set the ritual timer at the start of summoning
        
        # Add debug message
        phase_text = f"phase {self.phase}" if self.phase > 0 else "initial phase"
        self.add_debug_message(f"Started summoning from blinking copy in {phase_text}")
        
        # Play summoning sound
        self.sound_manager.play_sound("effects/boss_10_summon")
    
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
            self.add_debug_message(f"Summoning boss after {(current_time - self.ritual_timer)/1000:.1f} seconds of blinking")
            self.summon_level2_boss()
    
    def summon_level2_boss(self):
        """Summon the boss from the blinking copy - based on the current phase"""
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
        
        # Select boss level based on current phase
        if self.phase == 4:
            boss_level = 7  # Phase 4 summons level 7 boss
        elif self.phase == 3:
            boss_level = 6  # Phase 3 summons level 6 boss
        elif self.phase == 2:
            boss_level = 4  # Phase 2 summons level 4 boss (Goblin King)
        else:
            boss_level = 2  # Phase 1 summons level 2 boss
        
        # Create the boss with the appropriate level
        self.summoned_boss = Boss(spawn_x, spawn_y, boss_level, self.level_instance)
        
        # Add debug message about which boss was summoned
        boss_name = "Level 2 Boss" if boss_level == 2 else "Goblin King (Level 4)" if boss_level == 4 else "Level 6 Boss" if boss_level == 6 else "Level 7 Boss"
        self.add_debug_message(f"Summoned {boss_name}")
        
        # Set stats based on the boss level
        if boss_level == 7:
            # Level 7 boss modifications - keep the same pattern
            self.summoned_boss.health = self.summoned_boss.health * 0.7  # 70% health
            self.summoned_boss.max_health = self.summoned_boss.health
            self.summoned_boss.damage = self.summoned_boss.damage * 0.5  # 50% damage
        elif boss_level == 6:
            # Level 6 boss modifications
            self.summoned_boss.health = self.summoned_boss.health * 0.7  # 70% health
            self.summoned_boss.max_health = self.summoned_boss.health
            self.summoned_boss.damage = self.summoned_boss.damage * 0.5  # 50% damage
        elif boss_level == 4:
            # Goblin King stats modifications
            self.summoned_boss.health = self.summoned_boss.health * 0.8  # 80% health 
            self.summoned_boss.max_health = self.summoned_boss.health
            self.summoned_boss.damage = self.summoned_boss.damage * 0.6  # 60% damage
        else:
            # Level 2 boss stats
            self.summoned_boss.health = self.summoned_boss.health * 1.0  
            self.summoned_boss.max_health = self.summoned_boss.health
            self.summoned_boss.damage = self.summoned_boss.damage * 0.7  # 70% damage
        
        # Make sure the boss immediately starts chasing the player
        if hasattr(self.summoned_boss, 'has_spotted_player'):
            self.summoned_boss.has_spotted_player = True
            
        # If the boss has a state machine, set it to chase mode immediately
        if hasattr(self.summoned_boss, 'state') and hasattr(self.summoned_boss, 'STATE_CHASE'):
            self.summoned_boss.state = self.summoned_boss.STATE_CHASE
            self.add_debug_message(f"{boss_name} starting in chase mode")
            
        # Make sure chase timer is set
        if hasattr(self.summoned_boss, 'chase_start_time'):
            self.summoned_boss.chase_start_time = pygame.time.get_ticks()
            
        # If the boss has a first_spotted flag, mark as already spotted
        if hasattr(self.summoned_boss, 'first_spotted'):
            self.summoned_boss.first_spotted = True
        
        # Store the original shoot_projectile method
        original_shoot_projectile = self.summoned_boss.shoot_projectile
        
        # Override the shoot_projectile method to create faster projectiles
        def enhanced_shoot_projectile(player):
            if not self.summoned_boss.can_shoot:
                return False
            
            current_time = pygame.time.get_ticks()
            if current_time - self.summoned_boss.last_shot_time < self.summoned_boss.projectile_cooldown:
                return False
            
            # Only shoot if player is visible and not too close
            if not self.summoned_boss.has_spotted_player:
                return False
                
            # Calculate direction to player
            dx = player.rect.centerx - self.summoned_boss.rect.centerx
            dy = player.rect.centery - self.summoned_boss.rect.centery
            distance = math.sqrt(dx * dx + dy * dy)
            
            # Don't shoot if player is too close (within melee range)
            if distance <= self.summoned_boss.attack_range * 2:
                return False
            
            # Normalize direction
            if distance > 0:
                dx = dx / distance
                dy = dy / distance
            else:
                dx, dy = 0, -1
                
            # Create the projectile with higher speed
            projectile = BossProjectile(
                self.summoned_boss.rect.centerx, 
                self.summoned_boss.rect.centery, 
                (dx, dy), 
                speed=2.5,  # Increased from default 1.4 to 3.0
                damage=self.summoned_boss.projectile_damage, 
                color=self.summoned_boss.projectile_color,
                is_homing=True,  # Make the projectile homing
                boss_level=self.summoned_boss.level,
                spawn_secondary=True,  # Enable projectile splitting
                spawn_time=1500,  # Split after 1.5 seconds
                orbit_boss=self.summoned_boss  # Add reference to the boss for spawning
            )
            
            # Set the player as the target for homing
            projectile.player_target = player
            
            # Add to projectile group
            self.summoned_boss.projectiles.add(projectile)
            
            # Update last shot time
            self.summoned_boss.last_shot_time = current_time
            
            # Play sound if available
            if hasattr(self.summoned_boss, 'sound_manager'):
                self.summoned_boss.sound_manager.play_sound("effects/projectile")
                
            return True
        
        # Replace the shoot_projectile method
        self.summoned_boss.shoot_projectile = enhanced_shoot_projectile
        
        # Similarly, override the special_attack method to create faster projectiles in the special attack
        original_special_attack = self.summoned_boss.special_attack
        
        def enhanced_special_attack(player):
            current_time = pygame.time.get_ticks()
            if current_time - self.summoned_boss.last_special_attack_time >= self.summoned_boss.special_attack_cooldown:
                self.summoned_boss.last_special_attack_time = current_time
                
                # Create different special attacks based on boss level
                if self.summoned_boss.level == 2 or self.summoned_boss.level == 4:
                    # Calculate direction to player
                    dx = player.rect.centerx - self.summoned_boss.rect.centerx
                    dy = player.rect.centery - self.summoned_boss.rect.centery
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
                    perp_dx, perp_dy = -dy, dx
                    
                    # Calculate rotated vectors for left and right projectiles
                    rotation_factor = 0.5
                    
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
                    
                    # Create the projectiles with different colors and faster speed
                    # Center projectile
                    center_projectile = BossProjectile(
                        self.summoned_boss.rect.centerx + center_dx * 10,
                        self.summoned_boss.rect.centery + center_dy * 10,
                        (center_dx, center_dy),
                        speed=2.5,  # Increased from default 1.4 to 3.0
                        damage=self.summoned_boss.damage * 1.0,
                        color=(20, 150, 255),  # Brighter blue
                        boss_level=self.summoned_boss.level,
                        spawn_secondary=True,  # Enable projectile splitting
                        spawn_time=1500,  # Split after 1.5 seconds
                        orbit_boss=self.summoned_boss  # Add reference to the boss for spawning
                    )
                    
                    # Left projectile
                    left_projectile = BossProjectile(
                        self.summoned_boss.rect.centerx,
                        self.summoned_boss.rect.centery,
                        (left_dx, left_dy),
                        speed=2.5,  # Increased from default 1.4 to 3.0
                        damage=self.summoned_boss.damage * 1.0,
                        color=(255, 0, 255),  # Magenta
                        boss_level=self.summoned_boss.level,
                        spawn_secondary=True,  # Enable projectile splitting
                        spawn_time=1500,  # Split after 1.5 seconds
                        orbit_boss=self.summoned_boss  # Add reference to the boss for spawning
                    )
                    
                    # Right projectile
                    right_projectile = BossProjectile(
                        self.summoned_boss.rect.centerx,
                        self.summoned_boss.rect.centery,
                        (right_dx, right_dy),
                        speed=2.5,  # Increased from default 1.4 to 3.0
                        damage=self.summoned_boss.damage * 1.0,
                        color=(255, 165, 0),  # Orange
                        boss_level=self.summoned_boss.level,
                        spawn_secondary=True,  # Enable projectile splitting
                        spawn_time=1500,  # Split after 1.5 seconds
                        orbit_boss=self.summoned_boss  # Add reference to the boss for spawning
                    )
                    
                    # Add to projectile group
                    self.summoned_boss.projectiles.add(center_projectile, left_projectile, right_projectile)
                    
                    # Switch to special attack animation
                    self.summoned_boss.current_state = 'special'
                    self.summoned_boss.frame = 0  # Reset animation frame
                    return True
                
                # For other boss levels, use the original method
                return original_special_attack(player)
            return False
        
        # Replace the special_attack method
        self.summoned_boss.special_attack = lambda player: enhanced_special_attack(player)
        
        # Remove room boundary restrictions for the summoned boss
        # This replaces the default update method to prevent boundary clamping
        original_update = self.summoned_boss.update
        
        def unrestricted_update(player):
            # Store old position
            old_rect = self.summoned_boss.rect.copy()
            
            # Call the original update method
            result = original_update(player)
            
            # Apply a speed reduction factor to prevent erratic movement
            speed_factor = 0.1  # Reduced by 20% from 0.4
            
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
        
        # Clean up level 7 boss death ray if present
        if self.summoned_boss and self.summoned_boss.level == 7:
            # Clean up death ray if it exists
            if hasattr(self.summoned_boss, 'death_ray') and self.summoned_boss.death_ray:
                self.summoned_boss.death_ray.kill()
                self.summoned_boss.death_ray = None
                self.summoned_boss.has_death_ray = False
                self.add_debug_message("Level 7 boss death ray removed")
                
            # Also clean up from level's death_rays group if it exists
            if self.level_instance and hasattr(self.level_instance, 'death_rays'):
                self.level_instance.death_rays.empty()
                self.add_debug_message("Cleared all death rays from level group")
        
        # Check if player has a speed debuff from poison puddle (particularly from level 6 boss)
        # and remove it if present
        if self.level_instance and hasattr(self.level_instance, 'player'):
            player = self.level_instance.player
            if player and hasattr(player, '_original_speed'):
                player.speed = player._original_speed
                if hasattr(player, '_speed_debuff_end_time'):
                    delattr(player, '_speed_debuff_end_time')
                print("Speed debuff removed because summoned boss died")
        
        # Mark this pentagram point as inactive (no circle)
        if 0 <= self.blinking_copy_index < len(self.active_pentagram_points):
            self.active_pentagram_points[self.blinking_copy_index] = False
            # Important: Do NOT deactivate the death ray - keep it active even when copy is destroyed
            # self.active_death_rays[self.blinking_copy_index] = False  -- Removed this line
        
        # Add debug message to confirm rays are maintained
        self.add_debug_message(f"Keeping all 5 death rays active even after copy {self.blinking_copy_index} destroyed")
        
        # Remove the blinking copy but keep its pentagram point
        self.copies.pop(self.blinking_copy_index)
        
        # Remove from level's enemies list if it was added
        if self.level_instance and hasattr(self.level_instance, 'current_room') and self.summoned_boss:
            if hasattr(self.level_instance.current_room, 'enemies') and self.summoned_boss in self.level_instance.current_room.enemies:
                self.level_instance.current_room.enemies.remove(self.summoned_boss)
            
            # Remove from bosses list too if it exists
            if hasattr(self.level_instance.current_room, 'bosses') and self.summoned_boss in self.level_instance.current_room.bosses:
                self.level_instance.current_room.bosses.remove(self.summoned_boss)
        
        # Increment defeated copies counter
        self.defeated_copies_count += 1
        
        # Progress to phase 2 if this was the first defeated boss
        if self.defeated_copies_count == 1:
            self.phase = 2
            
            # Start the death ray growth phase
            self.activate_death_rays()
            
            # Reset any pending summoning state
            self.summoning_active = False
            self.rays_fully_grown_time = 0
            
            # Select another copy to blink for the next phase, but don't start summoning yet
            # We'll start the summoning after the death rays have grown to full size
            if len(self.copies) > 0:
                # Find a valid index that's not already been used
                valid_indices = [i for i in range(len(self.copies))]
                if valid_indices:
                    self.blinking_copy_index = random.choice(valid_indices)
                    self.copies[self.blinking_copy_index].is_blinking = True
                    self.copies[self.blinking_copy_index].will_summon_boss = True
                    
                    # Don't start summoning immediately - this will be triggered after rays grow
                    self.add_debug_message(f"Phase 2: Copy {self.blinking_copy_index} selected for next summoning")
                    
        # Progress to phase 3 if this was the second defeated boss
        elif self.defeated_copies_count == 2:
            self.phase = 3
            self.add_debug_message("Phase 3: Spawning mini death zones and preparing Level 6 boss")
            
            # Create initial mini death zones for phase 3
            self.create_mini_death_zones()
            
            # Reset any pending summoning state
            self.summoning_active = False
            
            # Select another copy to blink for the next phase
            if len(self.copies) > 0:
                # Find a valid index that's not already been used
                valid_indices = [i for i in range(len(self.copies))]
                if valid_indices:
                    self.blinking_copy_index = random.choice(valid_indices)
                    self.copies[self.blinking_copy_index].is_blinking = True
                    self.copies[self.blinking_copy_index].will_summon_boss = True
                    
                    # Reset the rays_fully_grown_time to use for the third boss delay timer
                    # This parallels how we use this timer for the second boss
                    self.rays_fully_grown_time = pygame.time.get_ticks()
                    self.add_debug_message(f"Phase 3: Copy {self.blinking_copy_index} will summon Level 6 boss after delay")
                
        # Progress to phase 4 if this was the third defeated boss
        elif self.defeated_copies_count == 3:
            self.phase = 4
            self.add_debug_message("Phase 4: Increasing rotation speeds and preparing Level 7 boss")
            
            # Increase death ray rotation speed by 20%
            self.death_ray_rotation_speed = self.base_ray_rotation_speed * 1.2
            # Increase pentagram rotation speed by 20%
            self.pentagram_rotation_speed = self.base_pentagram_rotation_speed * 1.2
            
            # Add debug message about the increased speeds
            self.add_debug_message(f"Rotation speeds increased by 20% for phase 4")
            
            # Reset any pending summoning state
            self.summoning_active = False
            
            # Select another copy to blink for the next phase
            if len(self.copies) > 0:
                # Find a valid index that's not already been used
                valid_indices = [i for i in range(len(self.copies))]
                if valid_indices:
                    self.blinking_copy_index = random.choice(valid_indices)
                    self.copies[self.blinking_copy_index].is_blinking = True
                    self.copies[self.blinking_copy_index].will_summon_boss = True
                    
                    # Reset the rays_fully_grown_time to use for the fourth boss delay timer
                    # This parallels how we use this timer for previous bosses
                    self.rays_fully_grown_time = pygame.time.get_ticks()
                    self.add_debug_message(f"Phase 4: Copy {self.blinking_copy_index} will summon Level 7 boss after delay")
                
        # Final phase transition after the fourth boss is defeated
        elif self.defeated_copies_count == 4:
            self.phase = 5
            self.add_debug_message("Phase 5: Final form - Dark Lord reveals himself!")
            
            # Reset any pending summoning state
            self.summoning_active = False
            
            # Start the final phase transition
            self.start_final_phase_transition()
            
        # Reset blinking copy index if not entering a new phase
        else:
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
    
    def activate_death_rays(self):
        """Activate the death rays for phase 2"""
        self.death_rays_active = True
        self.death_ray_angle = 0
        self.death_ray_growth_active = True
        self.death_ray_current_length = 0
        self.death_ray_spin_active = False  # Don't start spinning yet
        self.death_ray_growth_start_time = pygame.time.get_ticks()
        self.death_ray_last_hit_time = pygame.time.get_ticks()
        self.last_ray_spin_time = pygame.time.get_ticks()
        
        # Make sure all pentagram points have rays at activation
        # This ensures all 5 rays are active, regardless of current active_pentagram_points state
        for i in range(5):
            self.active_pentagram_points[i] = True
            self.active_death_rays[i] = True  # Initialize all death rays as active
        
        # Play death ray activation sound
        self.sound_manager.play_sound("effects/boss_10_rays")
        
        # Add debug message
        self.add_debug_message("Phase 2: Death rays growth started!")
    
    def update_death_rays(self, current_time, player):
        """Update the death rays rotation and check for collisions"""
        if not self.death_rays_active:
            return
        
        # Handle growth phase
        if self.death_ray_growth_active:
            # Calculate growth based on time
            elapsed = current_time - self.death_ray_growth_start_time
            growth_factor = min(1.0, elapsed / 5000)  # 5 seconds to grow to full size
            self.death_ray_current_length = self.death_ray_length * growth_factor
            
            # Calculate blinking effect during growth phase (fast blink rate)
            # Blinks faster as the ray grows (starting with slower blinks)
            blink_rate = 200 - int(150 * growth_factor)  # 200ms to 50ms blink rate as ray grows
            self.ray_visible = (elapsed // blink_rate) % 2 == 0  # Alternates between true/false
            
            # Check if growth is complete
            if growth_factor >= 1.0:
                self.death_ray_growth_active = False
                self.death_ray_current_length = self.death_ray_length
                self.death_ray_spin_active = True
                self.death_ray_angle = 0  # Start spinning from the current position (no angle offset)
                self.rays_fully_grown_time = current_time
                self.last_ray_spin_time = current_time  # Reset spin time counter
                self.ray_visible = True  # Make sure rays are visible after growth
                self.add_debug_message("Death rays fully grown, spinning active")
                
                # Important: Do NOT start summoning here! Wait for the delay to pass
        else:
            # Always visible when not in growth phase
            self.ray_visible = True
        
        # Handle delay after rays are fully grown before summoning boss in phase 2
        # OR handle delay after second boss defeated before summoning third boss in phase 3
        if self.rays_fully_grown_time > 0 and not self.summoning_active:
            elapsed_since_growth = current_time - self.rays_fully_grown_time
            
            # Only start summoning after the delay has passed
            if elapsed_since_growth >= self.rays_fully_grown_delay:
                if self.blinking_copy_index is not None:
                    # For any phase where we're waiting to summon
                    self.start_summoning()
                    
                    # Debug message based on phase
                    if self.phase == 2:
                        self.add_debug_message("Starting Level 4 boss summoning after delay")
                    elif self.phase == 3:
                        self.add_debug_message("Starting Level 6 boss summoning after delay")
                    elif self.phase == 4:
                        self.add_debug_message("Starting Level 7 boss summoning after delay")
                    else:
                        self.add_debug_message(f"Starting boss summoning after delay in phase {self.phase}")
        
        # Calculate time delta for spin (only if spinning is active)
        if self.death_ray_spin_active:
            spin_delta = current_time - self.last_ray_spin_time
            self.last_ray_spin_time = current_time
            
            # Update ray base spin (this is separate from the orbital rotation)
            self.death_ray_angle += self.death_ray_rotation_speed * spin_delta
        
        # Check if player is hit by any of the five death rays
        if player and current_time - self.death_ray_last_hit_time > self.death_ray_hit_cooldown:
            if self.is_player_hit_by_ray(player):
                # Apply damage
                player.take_damage(self.death_ray_damage)
                self.death_ray_last_hit_time = current_time
                
                # Create hit effect
                self.create_ray_hit_effect(player.rect.centerx, player.rect.centery)
                
                # Add debug message
                self.add_debug_message("Player hit by death ray!")
    
    def is_player_hit_by_ray(self, player):
        """Check if the player is hit by any of the death rays"""
        # Get player position
        player_x = player.rect.centerx
        player_y = player.rect.centery
        
        # Skip collision check if rays are still growing
        if self.death_ray_growth_active or self.death_ray_current_length <= 0:
            return False
            
        # Test each ray individually by calculating its exact path
        for i in range(5):  # 5 rays, one at each pentagram point
            # Skip ray if the death ray is inactive
            if i >= len(self.active_death_rays) or not self.active_death_rays[i]:
                continue
                
            # Use the EXACT SAME MATH as in draw_death_rays to ensure consistency
            # Get the pentagram point as the ray's start position
            if i < len(self.pentagram_points):
                start_x, start_y = self.pentagram_points[i]
                
                # Calculate the angle for this ray based on the ray's base spin
                # and the angle to the pentagram center
                center_x, center_y = self.pentagram_center
                base_angle = math.atan2(start_y - center_y, start_x - center_x)
                
                # Add the spin angle if spinning is active
                ray_angle = base_angle
                if self.death_ray_spin_active:
                    ray_angle += self.death_ray_angle
                
                # Calculate the end point of the ray
                ray_length = self.death_ray_current_length
                end_x = start_x + math.cos(ray_angle) * ray_length
                end_y = start_y + math.sin(ray_angle) * ray_length
                
                # Now check if player is close to the line segment from start to end
                # Using line-point distance formula
                line_length = math.sqrt((end_x - start_x)**2 + (end_y - start_y)**2)
                
                # Avoid division by zero
                if line_length == 0:
                    continue
                    
                # Calculate normalized direction vector
                dir_x = (end_x - start_x) / line_length
                dir_y = (end_y - start_y) / line_length
                
                # Calculate vector from start to player
                to_player_x = player_x - start_x
                to_player_y = player_y - start_y
                
                # Project player position onto the ray
                projection = to_player_x * dir_x + to_player_y * dir_y
                
                # Player is behind the start point or beyond end point
                if projection < 0 or projection > line_length:
                    continue
                    
                # Calculate closest point on line to player
                closest_x = start_x + dir_x * projection
                closest_y = start_y + dir_y * projection
                
                # Calculate distance from player to closest point
                distance = math.sqrt((player_x - closest_x)**2 + (player_y - closest_y)**2)
                
                # If distance is less than half the ray width, player is hit
                if distance <= self.death_ray_width / 2 + player.rect.width / 4:
                    return True
                    
        return False
        
    def create_ray_hit_effect(self, x, y):
        """Create visual effect for player being hit by death ray"""
        if hasattr(self, 'particle_manager') and self.particle_manager:
            for _ in range(20):
                angle = random.uniform(0, math.pi * 2)
                speed = random.uniform(0.5, 2.5)
                size = random.randint(3, 7)
                lifetime = random.randint(20, 40)
                
                # Calculate velocity
                vx = math.cos(angle) * speed
                vy = math.sin(angle) * speed
                
                # Add red particles
                self.particle_manager.add_particle(
                    particle_type='fade',
                    pos=(x, y),
                    velocity=(vx, vy),
                    direction=angle,
                    color=(255, 0, 0),
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
        
        # Update color pulsing from red to orange and back
        self.color_pulse_timer = (current_time % self.color_pulse_duration) / self.color_pulse_duration
        pulse_factor = (math.sin(self.color_pulse_timer * 2 * math.pi) + 1) / 2  # 0 to 1 value
        
        # Interpolate between red and orange based on pulse factor
        self.current_color = (
            self.color_red[0],  # Red channel stays 255
            int(self.color_red[1] + (self.color_orange[1] - self.color_red[1]) * pulse_factor),  # Green channel pulses
            int(self.color_red[2] + (self.color_orange[2] - self.color_red[2]) * pulse_factor)   # Blue channel pulses
        )
        
        # Handle outer circle growth animation
        if self.circle_growth_active:
            elapsed = current_time - self.circle_growth_start_time
            growth_progress = min(1.0, elapsed / self.circle_growth_duration)  # 0.0 to 1.0 over duration
            self.current_outer_circle_radius = self.outer_circle_radius * growth_progress
            
            # When circle has grown completely, it stays at full size
            if growth_progress >= 1.0:
                self.circle_growth_active = False
                self.current_outer_circle_radius = self.outer_circle_radius
        
        # Use pentagram rotation speed in phase 4 for floating circles or other effects
        # This is commented out since we don't currently have floating effects
        # but could be used for additional visual embellishments
        # rotation_amount = current_time * self.pentagram_rotation_speed
        
        # Check if all copies have reached their positions
        if not self.copies_positioned:
            all_positioned = True
            for copy in self.copies:
                if copy.is_moving:
                    all_positioned = False
                    break
                    
            if all_positioned:
                self.copies_positioned = True
                self.rotation_active = True
                self.last_rotation_time = current_time
                # Now select a copy to blink and start summoning
                self.blinking_copy_index = random.randint(0, 4)
                self.copies[self.blinking_copy_index].is_blinking = True
                self.copies[self.blinking_copy_index].will_summon_boss = True
                self.start_summoning()
                self.add_debug_message(f"Copy {self.blinking_copy_index} will summon boss")
        
        # Handle rotation after copies are positioned
        if self.rotation_active:
            # Calculate time delta
            delta_time = current_time - self.last_rotation_time
            self.last_rotation_time = current_time
            
            # Update rotation angle (negative for CCW)
            self.rotation_angle -= self.rotation_speed * delta_time
            
            # Calculate new positions for the pentagram points
            for i in range(5):
                # Now always rotate ALL copies, including the blinking one
                # Get the base angle for this point (2π/5 * i, plus the initial -π/2)
                base_angle = -math.pi / 2 + (2 * math.pi * i) / 5
                
                # Apply the current rotation
                angle = base_angle + self.rotation_angle
                
                # Calculate the new position
                new_x = self.pentagram_center[0] + self.outer_circle_radius * math.cos(angle)
                new_y = self.pentagram_center[1] + self.outer_circle_radius * math.sin(angle)
                
                # Update the pentagram point and the copy's position
                self.pentagram_points[i] = (new_x, new_y)
                
                # Update the copy's position if it still exists
                if i < len(self.copies) and self.copies[i] is not None:
                    self.copies[i].rect.centerx = new_x
                    self.copies[i].rect.centery = new_y
                    
            # Update death rays if they're active
            if self.death_rays_active:
                self.update_death_rays(current_time, None)  # We'll pass the player in the main update method
        
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
        
        # Update projectiles if any
        if hasattr(self, 'projectiles') and self.projectiles:
            self.projectiles.update()
            
            # Check collisions with player
            for projectile in self.projectiles:
                if hasattr(projectile, 'check_collision') and projectile.check_collision(player.rect):
                    player.take_damage(self.projectile_damage)
        
        # Check summoned boss status - this runs every frame
        if self.summoned_boss:
            # Check if the boss has been defeated
            if self.summoned_boss.health <= 0:
                # Before removing the boss, check if player has a speed debuff and remove it
                # This catches the case when the level 6 boss dies while player is slowed
                if hasattr(player, '_original_speed'):
                    player.speed = player._original_speed
                    if hasattr(player, '_speed_debuff_end_time'):
                        delattr(player, '_speed_debuff_end_time')
                    print("Speed debuff removed because summoned boss died (direct check)")
                    
                # Now handle normal boss defeat
                self.check_summoned_boss_status()
            else:
                # Just check status normally if boss is still alive
                self.check_summoned_boss_status()
        
        # Check if it's time for thunder effect
        if self.thunder_enabled and current_time >= self.next_thunder_time:
            self.trigger_thunder_effect()
            self.next_thunder_time = current_time + random.randint(self.thunder_interval_min, self.thunder_interval_max)
        
        # Update thunder flash effect if active
        if self.thunder_flash_active:
            self.update_thunder_flash(current_time)
        
        # Handle final phase transition
        if self.final_phase_active:
            self.update_final_phase_transition(current_time)
            
            # If in final phase (pentagram is gone), revert to normal boss behavior
            if not self.pentagram_active and self.visible:
                # Run regular boss update, but only if we're ready to chase
                chase_elapsed = current_time - self.chase_start_time
                if chase_elapsed >= self.chase_delay:
                    # Don't update position if an ability is active
                    ability_active = (hasattr(self, 'rope_cone_active') and self.rope_cone_active) or \
                                    (hasattr(self, 'charge_active') and self.charge_active)
                    if not ability_active:
                        super().update(player)
                
                # Update projectiles if any
                if hasattr(self, 'projectiles') and self.projectiles:
                    self.projectiles.update()
                    
                    # Check collisions with player
                    for projectile in self.projectiles:
                        if hasattr(projectile, 'check_collision') and projectile.check_collision(player.rect):
                            player.take_damage(self.projectile_damage)
                
                # Check mini death zones
                self.check_mini_death_zones(player)
                
                # Clean up expired mini death zones
                self.update_mini_death_zones(current_time)
                
                # Check for using abilities in phase 5
                if self.phase == 5 and self.visible:
                    # Check if in "wait_for_charge" state and delay has passed
                    if self.ability_sequence_state == 'wait_for_charge':
                        # Check if rope ability has ended
                        if not (hasattr(self, 'rope_cone_active') and self.rope_cone_active):
                            # If post-rope timer not started, start it
                            if self.post_rope_timer == 0:
                                self.post_rope_timer = current_time
                            
                            # Check if delay has passed
                            if current_time - self.post_rope_timer >= self.post_rope_delay:
                                # Reset timer and change state to charge
                                self.post_rope_timer = 0
                                self.ability_sequence_state = 'charge'
                                # Force ability use immediately
                                self.use_random_ability(player)
                    
                    # Check if in "wait_for_projectile" state and delay has passed
                    elif self.ability_sequence_state == 'wait_for_projectile':
                        # Check if charge ability has ended
                        if not (hasattr(self, 'charge_active') and self.charge_active):
                            # If post-charge timer not started, start it
                            if self.post_charge_timer == 0:
                                self.post_charge_timer = current_time
                            
                            # Check if delay has passed
                            if current_time - self.post_charge_timer >= self.post_charge_delay:
                                # Reset timer and change state to projectile
                                self.post_charge_timer = 0
                                self.ability_sequence_state = 'projectile'
                                # Force ability use immediately
                                self.use_random_ability(player)
                    
                    # Check if cooldown has passed for starting rope ability
                    elif self.ability_sequence_state == 'rope' and current_time - self.last_ability_time >= self.ability_cooldown:
                        # Don't start new ability if one is already running
                        ability_active = (hasattr(self, 'rope_cone_active') and self.rope_cone_active) or \
                                        (hasattr(self, 'charge_active') and self.charge_active)
                        if not ability_active:
                            self.use_random_ability(player)
                
                # Update rope cone ability if active
                if hasattr(self, 'rope_cone_active') and self.rope_cone_active:
                    self.update_rope_cone_ability(current_time, player)
                
                # Update charge ability if active
                if hasattr(self, 'charge_active') and self.charge_active:
                    self.update_charge_ability(current_time, player)
                
                return
            
        # Handle introduction phase
        if not self.introduction_complete:
            if not self.introduction_timer:
                self.start_introduction()
            
            elapsed_time = current_time - self.introduction_timer
            if elapsed_time >= self.introduction_duration:
                self.complete_introduction()
            return
        
        # Handle post-introduction transition to pentagram phase
        if self.pentagram_creation_pending:
            # Wait for the post-intro delay before starting circle growth
            if not self.circle_growth_active and current_time - self.post_intro_timer >= self.post_intro_delay:
                # Start circle growth
                self.circle_growth_active = True
                self.circle_growth_start_time = current_time
                self.add_debug_message("Starting circle growth animation")
            
            # Update circle growth if active
            if self.circle_growth_active:
                elapsed = current_time - self.circle_growth_start_time
                growth_progress = min(1.0, elapsed / self.circle_growth_duration)
                self.current_outer_circle_radius = self.outer_circle_radius * growth_progress
                
                # When circle has grown completely, start the pentagram creation
                if growth_progress >= 1.0:
                    self.circle_growth_active = False
                    self.current_outer_circle_radius = self.outer_circle_radius
                    self.pentagram_creation_pending = False
                    self.create_pentagram_copies()
            return
        
        # Handle pentagram phase
        if self.pentagram_active:
            self.update_pentagram()
            
            # Check if only one copy remains to transition to final phase
            if len(self.copies) == 1 and self.defeated_copies_count < 4:
                # Make boss vulnerable in intermediate final phase
                self.invulnerable = False
                # Add debug message
                self.add_debug_message("Intermediate phase - Dark Lord is temporarily vulnerable!")
            else:
                # Ensure boss is invulnerable while multiple copies remain
                self.invulnerable = True
                
            # Check if player is in the death zone and apply effects if they are
            if self.is_player_in_death_zone(player):
                self.apply_death_zone_effect(player)
            
            # Check if player is in any mini death zones
            self.check_mini_death_zones(player)
            
            # Update death rays if active and pass the player for collision detection
            if self.death_rays_active:
                self.update_death_rays(current_time, player)
                
            # Update copies
            for copy in self.copies:
                copy.update(player)
            
            # Update summoned bosses
            for boss in self.summoned_bosses:
                boss.update(player)
                
            # Clean up expired mini death zones
            self.update_mini_death_zones(current_time)
                
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
        # Draw the circle (if growing or active) before anything else
        if (self.circle_growth_active or self.current_outer_circle_radius > 0 or 
            self.pentagram_fade_active):
            self.draw_circle(surface)
            
        if not self.visible:
            # Don't draw the main boss if not visible
            pass
        else:
            # Draw aura around boss
            self.draw_aura(surface)
            
            # Draw rope cone telegraph if active
            if hasattr(self, 'rope_cone_active') and self.rope_cone_active and self.rope_cone_casting:
                self.draw_rope_cone_telegraph(surface)
                
            # Draw rope cone ropes if active and cast is complete
            if hasattr(self, 'rope_cone_active') and self.rope_cone_active and self.rope_cone_cast_complete:
                self.draw_rope_cone_ropes(surface)
                
            # Draw charge telegraph if active
            if hasattr(self, 'charge_active') and self.charge_active and self.charge_casting:
                self.draw_charge_telegraph(surface)
            
            # Draw the main boss
            super().draw(surface)
        
        # Draw the pentagram if active
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
                health_bar_width = 50
                health_bar_height = 5
                health_ratio = boss.health / boss.max_health
                
                # Draw health bar background (red)
                pygame.draw.rect(
                    surface,
                    (255, 0, 0),
                    (boss.rect.centerx - health_bar_width // 2,
                     boss.rect.top - 15,
                     health_bar_width,
                     health_bar_height)
                )
                
                # Draw current health (green)
                pygame.draw.rect(
                    surface,
                    (0, 255, 0),
                    (boss.rect.centerx - health_bar_width // 2,
                     boss.rect.top - 15,
                     int(health_bar_width * health_ratio),
                     health_bar_height)
                )
        
        # Draw mini death zones (mini lightning zones)
        self.draw_mini_death_zones(surface)
        
        # Draw thunder flash over everything else
        if self.thunder_flash_active:
            self.draw_thunder_flash(surface)
        
        # Draw debug messages if enabled
        if self.debug_enabled:
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
    
    def draw_circle(self, surface):
        """Draw just the growing outer circle (separate from pentagram)"""
        if self.current_outer_circle_radius <= 0:
            return
            
        # Use the pulsing color
        alpha_value = int(100 * self.pentagram_pulse)
        circle_color = (*self.current_color, alpha_value)
        
        # Draw outer circle with current radius from growth animation
        pygame.draw.circle(
            surface, 
            circle_color, 
            self.pentagram_center, 
            self.current_outer_circle_radius,
            2  # Width of the circle
        )
        
        # Draw inner circle - scale with outer circle
        inner_circle_radius = self.current_outer_circle_radius * 0.5
        pygame.draw.circle(
            surface, 
            circle_color, 
            self.pentagram_center, 
            inner_circle_radius,
            2  # Width of the circle
        )
        
        # Draw center glow - slightly brighter version of the current pulsing color
        glow_color = (
            min(255, self.current_color[0] + 30),
            min(255, self.current_color[1] + 30),
            min(255, self.current_color[2] + 30),
            int(150 * self.pentagram_pulse)
        )
        center_radius = self.current_outer_circle_radius * 0.15
        pygame.draw.circle(
            surface,
            glow_color,
            self.pentagram_center,
            center_radius
        )
    
    def draw_pentagram(self, surface):
        """Draw the pentagram and effects (except the circles)"""
        if not self.pentagram_active or not self.pentagram_points:
            return
        
        # Draw pentagram lines connecting the points with pulsing color
        sequence = [0, 2, 4, 1, 3, 0]  # Repeat 0 at the end to close the shape
        
        # Use the pulsing color with alpha
        alpha_value = int(min(255, 150 + 100 * self.pentagram_pulse))
        line_color = (*self.current_color, alpha_value)
        
        for i in range(len(sequence) - 1):
            start_idx = sequence[i]
            end_idx = sequence[i+1]
            
            # Skip lines connected to the missing copy if it's been destroyed
            if self.summoned_boss is not None and self.blinking_copy_index is not None:
                if start_idx == self.blinking_copy_index or end_idx == self.blinking_copy_index:
                    if not any(copy.is_blinking for copy in self.copies):
                        continue
            
            if start_idx < len(self.pentagram_points) and end_idx < len(self.pentagram_points):
                start_pos = self.pentagram_points[start_idx]
                end_pos = self.pentagram_points[end_idx]
                
                # Draw line with pulsing color
                pygame.draw.line(
                    surface,
                    line_color,
                    start_pos,
                    end_pos,
                    2  # Line width
                )
        
        # Draw death rays if active
        if self.death_rays_active:
            self.draw_death_rays(surface)
        
        # Draw death zone if enabled
        if self.death_zone_enabled:
            # Draw filled circle with very low opacity
            death_circle = pygame.Surface((self.current_outer_circle_radius * 2, self.current_outer_circle_radius * 2), pygame.SRCALPHA)
            
            # Use a tint of the current pulsing color for death zone
            death_color = (*self.current_color, 40)  # Very transparent
            
            pygame.draw.circle(
                death_circle,
                death_color,
                (self.current_outer_circle_radius, self.current_outer_circle_radius),
                self.current_outer_circle_radius
            )
            
            # Position and draw the death zone
            death_x = self.pentagram_center[0] - self.current_outer_circle_radius
            death_y = self.pentagram_center[1] - self.current_outer_circle_radius
            surface.blit(death_circle, (death_x, death_y))
            
        # Draw mini death zones
        self.draw_mini_death_zones(surface)
        
        # DEBUG DRAWING
        # Draw debug messages if enabled
        if self.debug_enabled:
            self.draw_debug_messages(surface, None)
    
    def draw_death_rays(self, surface):
        """Draw the rotating death rays"""
        if not self.death_rays_active:
            return
            
        # Skip drawing during growth phase when the ray should be invisible (blinking effect)
        if self.death_ray_growth_active and not self.ray_visible:
            return
            
        center_x, center_y = self.pentagram_center
        
        # Use the pulsing color for death rays too
        ray_color = (*self.current_color, 200)
        
        # Draw all five death rays, one at each pentagram point
        for i in range(5):
            # Skip ray if the death ray is inactive
            if i >= len(self.active_death_rays) or not self.active_death_rays[i]:
                continue
                
            # Get the pentagram point as the ray's start position
            if i < len(self.pentagram_points):
                start_x, start_y = self.pentagram_points[i]
                
                # Calculate the base angle from the pentagram center to this point
                base_angle = math.atan2(start_y - center_y, start_x - center_x)
                
                # For non-spinning rays during growth, use the base angle directly
                # For spinning rays, add the spin offset
                ray_angle = base_angle
                if self.death_ray_spin_active:
                    ray_angle += self.death_ray_angle
                
                # Calculate the end point of the ray
                ray_length = self.death_ray_current_length
                end_x = start_x + math.cos(ray_angle) * ray_length
                end_y = start_y + math.sin(ray_angle) * ray_length
                
                # Create zig-zag ray effect instead of straight line
                if ray_length > 0:
                    # Get current time for animation
                    current_time = pygame.time.get_ticks()
                    
                    # Create list of points for the zig-zag path
                    zig_zag_points = [
                        (start_x, start_y),  # Start point
                    ]
                    
                    # Parameters for zig-zag effect
                    segment_length = 30  # Length of each segment in the zig-zag
                    
                    # Calculate number of segments based on ray length
                    num_segments = max(1, int(ray_length / segment_length))
                    remaining_length = ray_length
                    
                    # Calculate current direction vector
                    dir_x = math.cos(ray_angle)
                    dir_y = math.sin(ray_angle)
                    
                    # Create perpendicular vector for zig-zag displacement
                    perp_x = -dir_y
                    perp_y = dir_x
                    
                    # Current position
                    current_x, current_y = start_x, start_y
                    
                    # Animation modifier - makes the zig-zag points move/shift over time
                    animation_speed = 0.02
                    animation_offset = current_time * animation_speed % (math.pi * 2)
                    
                    # Amplitude increases with ray length for more dramatic effect
                    # But capped to avoid excessive zigzag
                    base_amplitude = 3
                    amplitude_factor = min(1.0, ray_length / (TILE_SIZE * 3))
                    max_amplitude = base_amplitude + (5 * amplitude_factor)
                    
                    # Create each segment of the zig-zag
                    for j in range(num_segments):
                        # Calculate segment length (last one might be shorter)
                        seg_length = min(segment_length, remaining_length)
                        if seg_length <= 0:
                            break
                            
                        # Calculate position along ray for this segment
                        segment_progress = (j * segment_length) / ray_length
                        
                        # Alternating zig-zag with sine wave modulation for smoother look
                        # Amplitude increases toward the middle of the ray and decreases toward the end
                        # This creates a pulsing/flowing effect along the ray
                        wave_position = segment_progress * 10 + animation_offset
                        
                        # Amplitude is stronger in the middle, weaker at start/end
                        # This creates a pulsing shape where the middle has more zigzag
                        amplitude_modifier = math.sin(segment_progress * math.pi)
                        amplitude = max_amplitude * amplitude_modifier
                        
                        # Calculate displacement using sine wave
                        displacement = amplitude * math.sin(wave_position)
                        
                        # Apply displacement perpendicular to ray direction
                        offset_x = perp_x * displacement
                        offset_y = perp_y * displacement
                        
                        # Calculate next point position
                        next_x = current_x + (dir_x * seg_length) + offset_x
                        next_y = current_y + (dir_y * seg_length) + offset_y
                        
                        # Add point to path
                        zig_zag_points.append((next_x, next_y))
                        
                        # Update current position (without the perpendicular displacement)
                        # This keeps the ray following the overall correct direction
                        current_x += dir_x * seg_length
                        current_y += dir_y * seg_length
                        
                        # Reduce remaining length
                        remaining_length -= seg_length
                    
                    # Make sure the last point is exactly at the end of the ray
                    # This ensures the ray has the correct total length regardless of zig-zags
                    zig_zag_points.append((end_x, end_y))
                    
                    # Draw the zig-zag ray
                    if len(zig_zag_points) > 1:
                        pygame.draw.lines(
                            surface,
                            ray_color,
                            False,  # Don't connect last point to first
                            zig_zag_points,
                            self.death_ray_width
                        )
                    
                    # Draw additional glow effect
                    if hasattr(self, 'particle_manager') and self.particle_manager:
                        # Generate particles along the ray path
                        for j in range(1, len(zig_zag_points)):
                            # Only spawn particles occasionally
                            if random.random() < 0.3:
                                # Get the segment
                                seg_start = zig_zag_points[j-1]
                                seg_end = zig_zag_points[j]
                                
                                # Calculate a random position along this segment
                                t = random.random()
                                particle_x = seg_start[0] + (seg_end[0] - seg_start[0]) * t
                                particle_y = seg_start[1] + (seg_end[1] - seg_start[1]) * t
                                
                                # Create a particle at this position
                                # Brighter color for better visibility
                                particle_color = (
                                    min(255, self.current_color[0]),
                                    min(255, self.current_color[1]),
                                    min(255, self.current_color[2])
                                )
                                
                                # Add a particle at this position
                                self.particle_manager.add_particle(
                                    particle_type='fade',
                                    pos=(particle_x, particle_y),
                                    velocity=(random.uniform(-0.5, 0.5), random.uniform(-0.5, 0.5)),
                                    direction=0,
                                    color=particle_color,
                                    size=random.randint(1, 3),
                                    lifetime=random.randint(5, 15)
                                )
                else:
                    # Fallback to simple line if ray_length is zero
                    pygame.draw.line(
                        surface,
                        ray_color,
                        (start_x, start_y),
                        (start_x, start_y),  # Same point
                        self.death_ray_width
                    )
                
                # Draw a small glow at the start of the ray
                glow_radius = self.death_ray_width * 1.5
                pygame.draw.circle(
                    surface,
                    ray_color,
                    (int(start_x), int(start_y)),
                    int(glow_radius)
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
    
    def take_damage(self, amount, knockback=None, damage_type=None):
        """Override take_damage to implement invulnerability during certain phases"""
        # If we're in the final phase (after the transition is complete),
        # we should be vulnerable regardless of copies
        if self.phase == 5 and not self.pentagram_active and self.visible:
            # In the final phase, we're always vulnerable
            # But we need to call the parent with only the expected arguments
            return super().take_damage(amount)
            
        # Make boss invulnerable during introduction phase
        if not self.introduction_complete:
            # Completely invulnerable during introduction
            return False
            
        # Make boss invulnerable during pentagram creation phase
        if self.pentagram_creation_pending or self.circle_growth_active:
            # Invulnerable while circle is growing
            return False
            
        # Phase check: Only take damage when in the final phase with one copy left
        if self.pentagram_active and len(self.copies) > 1:
            # Return early if we're in the pentagram phase and have more than one copy
            # This prevents damage during the pentagram ritual
            return False
            
        # Allow damage during transition phases (when only one copy remains)
        # Modified to only pass the arguments expected by the parent class
        return super().take_damage(amount)

    def trigger_thunder_effect(self):
        """Trigger the thunder effect with multiple flashes and sound"""
        # Start the flash effect
        self.thunder_flash_active = True
        self.thunder_flash_start_time = pygame.time.get_ticks()
        
        # Generate random sequence of 3-5 flashes with varying intensity and timing
        num_flashes = random.randint(3, 5)
        self.thunder_flashes = []
        
        # First flash is always the brightest
        self.thunder_flashes.append({
            'delay': 0,  # Immediate
            'duration': 150,
            'intensity': random.randint(160, 200)  # Main flash (bright)
        })
        
        # Add secondary flashes with varying delays and intensities
        total_duration = 150  # Keep track of cumulative duration
        for i in range(1, num_flashes):
            delay = total_duration + random.randint(50, 150)  # Random delay after previous flash
            duration = random.randint(50, 120)  # Random duration
            
            # Intensity decreases with each subsequent flash
            max_intensity = 180 - (i * 30)
            min_intensity = max(80, max_intensity - 40)
            intensity = random.randint(min_intensity, max_intensity)
            
            self.thunder_flashes.append({
                'delay': delay,
                'duration': duration,
                'intensity': intensity
            })
            
            total_duration = delay + duration
        
        # Reset flash tracking
        self.current_flash_index = 0
        self.thunder_flash_alpha = self.thunder_flashes[0]['intensity']
        
        # Only create mini death zones if we're in phase 3 or higher (after second boss is defeated)
        if self.phase >= 3:
            self.create_mini_death_zones()
        
        # Play thunder sound
        self.sound_manager.play_sound("effects/thunder")
        
        # Add debug message
        self.add_debug_message(f"Thunder effect triggered with {num_flashes} flashes")
    
    def update_thunder_flash(self, current_time):
        """Update the thunder flash effect with multiple flashes"""
        if not self.thunder_flash_active:
            return
            
        # Calculate time since thunder effect started
        elapsed = current_time - self.thunder_flash_start_time
        
        # Exit if we've gone through all flashes
        if self.current_flash_index >= len(self.thunder_flashes):
            self.thunder_flash_active = False
            self.thunder_flash_alpha = 0
            return
            
        # Get current flash info
        current_flash = self.thunder_flashes[self.current_flash_index]
        flash_start = current_flash['delay']
        flash_end = flash_start + current_flash['duration']
        
        # Check if we're in the current flash's time window
        if flash_start <= elapsed < flash_end:
            # Calculate the fade within this flash (start bright, fade out)
            flash_progress = (elapsed - flash_start) / current_flash['duration']
            self.thunder_flash_alpha = int(current_flash['intensity'] * (1 - flash_progress))
        elif elapsed >= flash_end:
            # Move to the next flash
            self.current_flash_index += 1
            
            # Set initial alpha for the next flash if there is one
            if self.current_flash_index < len(self.thunder_flashes):
                self.thunder_flash_alpha = self.thunder_flashes[self.current_flash_index]['intensity']
            else:
                # End the effect if we've used all flashes
                self.thunder_flash_active = False
                self.thunder_flash_alpha = 0
    
    def draw_thunder_flash(self, surface):
        """Draw a white flash overlay for the thunder effect"""
        # Create a full-screen white overlay with current alpha
        flash_surface = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        flash_surface.fill((255, 255, 255, self.thunder_flash_alpha))
        
        # Blit the flash overlay onto the screen
        surface.blit(flash_surface, (0, 0))
    
    def create_mini_death_zones(self):
        """Create mini death zones that last for 6 seconds"""
        # Determine how many mini zones to create
        # In phase 5, create 16 mini death zones; otherwise create 3-4
        if hasattr(self, 'phase') and self.phase == 5:
            num_zones = 16  # Create 16 zones in phase 5 (increased from 10)
        else:
            num_zones = random.randint(3, 4)  # Default for other phases
        
        # Get current time for end time calculation
        current_time = pygame.time.get_ticks()
        end_time = current_time + self.mini_death_zone_duration
        creation_time = current_time  # Store the creation time for grace period
        
        # Get room dimensions if available
        room_width = 0
        room_height = 0
        if hasattr(self, 'level_instance') and self.level_instance and hasattr(self.level_instance, 'current_room'):
            room = self.level_instance.current_room
            room_width = room.width * TILE_SIZE
            room_height = room.height * TILE_SIZE
        else:
            # Fallback dimensions
            room_width = 20 * TILE_SIZE
            room_height = 15 * TILE_SIZE
        
        # Create the specified number of mini death zones
        for _ in range(num_zones):
            # Keep trying until we find a valid position
            for attempt in range(20):  # Limit attempts to prevent infinite loop
                # Generate random position
                x = random.randint(TILE_SIZE, room_width - TILE_SIZE)
                y = random.randint(TILE_SIZE, room_height - TILE_SIZE)
                
                # Check if position is within the main death zone (only for phases 1-4)
                is_valid_position = True
                if not (hasattr(self, 'phase') and self.phase == 5):
                    # In phases other than 5, zones must be outside the death circle
                    dx = x - self.pentagram_center[0]
                    dy = y - self.pentagram_center[1]
                    distance = math.sqrt(dx*dx + dy*dy)
                    if distance <= self.outer_circle_radius:
                        is_valid_position = False
                
                # Also check if it overlaps with any existing mini zones
                overlaps_existing = False
                for zone_x, zone_y, _, _ in self.mini_death_zones:
                    zone_dx = x - zone_x
                    zone_dy = y - zone_y
                    zone_distance = math.sqrt(zone_dx*zone_dx + zone_dy*zone_dy)
                    if zone_distance < TILE_SIZE * 2:  # Keep them at least 2 tiles apart
                        overlaps_existing = True
                        break
                
                # Check if the position is valid
                if is_valid_position and not overlaps_existing:
                    new_zone = (x, y, end_time, creation_time)  # Include creation time
                    self.mini_death_zones.append(new_zone)
                    # Initialize lightning blink state for this zone
                    self.mini_zone_lightning_blinks[new_zone] = {
                        'visible': random.choice([True, False]),
                        'next_blink': current_time + random.randint(100, 300)
                    }
                    break
        
        # Add debug message
        phase_text = f"phase {self.phase}" if hasattr(self, 'phase') else "current phase"
        self.add_debug_message(f"Created {len(self.mini_death_zones)} blue lightning zones in {phase_text}")
    
    def update_mini_death_zones(self, current_time):
        """Update mini death zones and remove expired ones"""
        if not self.mini_death_zones:
            return
        
        # Update lightning blink states
        for zone in list(self.mini_zone_lightning_blinks.keys()):
            if zone not in self.mini_death_zones:
                # Remove blink data for expired zones
                self.mini_zone_lightning_blinks.pop(zone, None)
                continue
                
            # Check if it's time to change visibility
            blink_data = self.mini_zone_lightning_blinks[zone]
            if current_time >= blink_data['next_blink']:
                # Toggle visibility
                blink_data['visible'] = not blink_data['visible']
                # Set next blink time
                blink_data['next_blink'] = current_time + random.randint(100, 300)
            
        # Remove expired zones
        self.mini_death_zones = [(x, y, end_time, creation_time) for x, y, end_time, creation_time in self.mini_death_zones 
                               if current_time < end_time]
    
    def check_mini_death_zones(self, player):
        """Check if player is in any mini death zones and apply damage"""
        if not player or not self.mini_death_zones:
            return
            
        current_time = pygame.time.get_ticks()
            
        # Check each mini zone
        for zone_x, zone_y, _, creation_time in self.mini_death_zones:
            # Calculate distance from player to zone center
            dx = player.rect.centerx - zone_x
            dy = player.rect.centery - zone_y
            distance = math.sqrt(dx*dx + dy*dy)
            
            # Skip damage if we're in the 1-second grace period
            grace_period_active = (current_time - creation_time) < 1000  # 1 second grace period
            
            # If player is in the zone and grace period is over, apply damage (with cooldown)
            if distance <= self.mini_death_zone_radius + player.rect.width / 4 and not grace_period_active:
                if current_time - self.last_mini_zone_hit_time > self.mini_zone_hit_cooldown:
                    self.last_mini_zone_hit_time = current_time
                    player.take_damage(self.mini_death_zone_damage)
                    
                    # Create hit effect
                    if hasattr(self, 'particle_manager') and self.particle_manager:
                        for _ in range(10):
                            angle = random.uniform(0, math.pi * 2)
                            speed = random.uniform(0.5, 2)
                            size = random.randint(2, 5)
                            lifetime = random.randint(15, 30)
                            
                            # Calculate velocity
                            vx = math.cos(angle) * speed
                            vy = math.sin(angle) * speed
                            
                            # Add particles with blue color instead of red
                            self.particle_manager.add_particle(
                                particle_type='fade',
                                pos=(player.rect.centerx, player.rect.centery),
                                velocity=(vx, vy),
                                direction=angle,
                                color=(0, 100, 255),  # Blue color
                                size=size,
                                lifetime=lifetime
                            )
                    
                    # Add debug message
                    self.add_debug_message("Player hit by lightning zone!")
                    
                    # One hit is enough per frame
                    break
    
    def draw_mini_death_zones(self, surface):
        """Draw mini death zones with blue coloring and lightning effects"""
        if not self.mini_death_zones:
            return
            
        current_time = pygame.time.get_ticks()
            
        # Draw each mini zone
        for zone in self.mini_death_zones:
            zone_x, zone_y, end_time, creation_time = zone
            
            # Calculate time since creation
            time_since_creation = current_time - creation_time
            
            # Calculate remaining lifetime (for effects, not for alpha anymore)
            time_left = end_time - current_time
            
            # Use a constant alpha instead of fading out
            alpha = 150  # Constant alpha value for visibility
            
            # Create surface for the zone
            zone_surface = pygame.Surface((self.mini_death_zone_radius * 2, self.mini_death_zone_radius * 2), pygame.SRCALPHA)
            
            # Fill with blue color (instead of red)
            zone_color = (0, 100, 255, alpha)  # Blue color
            pygame.draw.circle(
                zone_surface,
                zone_color,
                (self.mini_death_zone_radius, self.mini_death_zone_radius),
                self.mini_death_zone_radius
            )
            
            # Draw a slight glow/border
            pygame.draw.circle(
                zone_surface,
                (50, 150, 255, alpha // 2),  # Lighter blue
                (self.mini_death_zone_radius, self.mini_death_zone_radius),
                self.mini_death_zone_radius,
                2
            )
            
            # Position and draw
            pos_x = zone_x - self.mini_death_zone_radius
            pos_y = zone_y - self.mini_death_zone_radius
            surface.blit(zone_surface, (pos_x, pos_y))
            
            # Highlight zones in grace period with subtle pulsing effect
            grace_period_active = (current_time - creation_time) < 1000  # 1 second grace period
            if grace_period_active:
                # Calculate pulse effect (subtle pulsing outline)
                pulse = (math.sin(current_time / 100) + 1) / 2  # Value between 0 and 1
                pulse_width = int(min(255, 2 + pulse * 2))  # Width between 2-4 pixels
                
                # Draw pulsing outline to indicate grace period
                pygame.draw.circle(
                    surface,
                    (100, 200, 255, int(200 * pulse)),  # Brighter blue with pulse alpha
                    (zone_x, zone_y),
                    self.mini_death_zone_radius + 2,
                    pulse_width
                )
            
            # Draw lightning image if it's in the visible state
            if self.lightning_image and zone in self.mini_zone_lightning_blinks:
                blink_data = self.mini_zone_lightning_blinks[zone]
                
                # Special handling for first 500ms - blink with 300% scale
                initial_effect = time_since_creation < 500
                
                if blink_data['visible'] or initial_effect:
                    # Store original dimensions for scaling calculations
                    orig_width = self.lightning_image.get_width()
                    orig_height = self.lightning_image.get_height()
                    
                    # Apply 300% scaling during the first 500ms
                    scale = 3.0 if initial_effect else 1.0
                    
                    # Create scaled image
                    if scale != 1.0:
                        scaled_width = int(orig_width * scale)
                        scaled_height = int(orig_height * scale)
                        scaled_img = pygame.transform.scale(self.lightning_image, (scaled_width, scaled_height))
                    else:
                        scaled_img = self.lightning_image
                    
                    # Position lightning image with bottom at the center of the zone
                    # Adjust for the new scaled size
                    lightning_x = zone_x - scaled_img.get_width() // 2
                    lightning_y = zone_y - scaled_img.get_height()
                    
                    # Blink effect during initial 500ms (rapid flashing)
                    if initial_effect:
                        # Faster blinking for dramatic effect (4 flashes in 500ms)
                        flash_period = 125  # ms per flash
                        flash_visible = (time_since_creation // flash_period) % 2 == 0
                        
                        if flash_visible:
                            # Full brightness for the initial strike
                            surface.blit(scaled_img, (lightning_x, lightning_y))
                    else:
                        # Normal display after initial effect
                        surface.blit(scaled_img, (lightning_x, lightning_y))
            
            # Occasionally add particles
            if hasattr(self, 'particle_manager') and self.particle_manager and random.random() < 0.1:
                angle = random.uniform(0, math.pi * 2)
                distance = random.uniform(0, self.mini_death_zone_radius * 0.8)
                particle_x = zone_x + math.cos(angle) * distance
                particle_y = zone_y + math.sin(angle) * distance
                
                self.particle_manager.add_particle(
                    particle_type='fade',
                    pos=(particle_x, particle_y),
                    velocity=(0, 0),
                    direction=0,
                    color=(50, 150, 255),  # Blue color
                    size=random.randint(1, 3),
                    lifetime=random.randint(10, 20)
                )
                
                # Add extra particles during initial strike
                if time_since_creation < 500 and random.random() < 0.5:
                    # More frequent and larger particles for initial strike
                    for _ in range(3):
                        spread_angle = random.uniform(0, math.pi * 2)
                        spread_distance = random.uniform(0, self.mini_death_zone_radius * 1.2)
                        strike_x = zone_x + math.cos(spread_angle) * spread_distance
                        strike_y = zone_y + math.sin(spread_angle) * spread_distance
                        
                        # Brighter particles for the strike effect
                        self.particle_manager.add_particle(
                            particle_type='fade',
                            pos=(strike_x, strike_y),
                            velocity=(random.uniform(-1, 1), random.uniform(-1, 1)),
                            direction=0,
                            color=(150, 200, 255),  # Brighter blue
                            size=random.randint(2, 6),
                            lifetime=random.randint(15, 30)
                        )

    def start_final_phase_transition(self):
        """Start the transition to the final phase after all copies are defeated"""
        self.final_phase_active = True
        self.final_phase_start_time = pygame.time.get_ticks()
        
        # We'll animate the last copy to the center
        if len(self.copies) > 0:
            # The last copy will move to the center
            self.blinking_copy_index = 0  # Use the first (and only) remaining copy
            self.copies[self.blinking_copy_index].is_blinking = True
            
            # Start the copy moving to the center
            self.copies[self.blinking_copy_index].target_x = self.pentagram_center[0]
            self.copies[self.blinking_copy_index].target_y = self.pentagram_center[1]
            self.copies[self.blinking_copy_index].is_moving = True
            self.copies[self.blinking_copy_index].move_speed = 1.0  # Slow movement to center
            
            # Start the pentagram fade out
            self.pentagram_fade_active = True
            self.pentagram_fade_start_time = pygame.time.get_ticks()
            
            # Play a sound effect for the transition
            self.sound_manager.play_sound("effects/boss_transition")
            
            self.add_debug_message("Final copy moving to center, pentagram fading out")
        else:
            # If no copies remain, just proceed directly to the final phase
            self.complete_final_phase_transition()

    def complete_final_phase_transition(self):
        """Complete the transition to the final phase"""
        # Deactivate pentagram elements
        self.pentagram_active = False
        self.death_rays_active = False
        self.death_zone_enabled = False  # Disable the main death zone (keep mini zones)
        
        # Remove any remaining copies
        self.copies = []
        
        # Make the real boss visible and vulnerable
        self.visible = True
        self.invulnerable = False
        
        # Force the correct phase
        self.phase = 5
        
        # Debug message to confirm vulnerability
        self.add_debug_message("Dark Lord is now VULNERABLE!")
        
        # If we have a final form image, use it
        if hasattr(self, 'final_form_image') and self.final_form_image:
            self.image = self.final_form_image
            self.rect = self.image.get_rect(center=(self.rect.centerx, self.rect.centery))
        
        # Reset chase timer for the delay
        self.chase_start_time = pygame.time.get_ticks()
        
        # Play a reveal sound effect
        self.sound_manager.play_sound("effects/boss_reveal")
        
        self.add_debug_message("Dark Lord revealed in final form! Will chase in 2 seconds")

    def update_final_phase_transition(self, current_time):
        """Update the final phase transition animation"""
        if not self.final_phase_active:
            return
            
        # First, check if the pentagram fade is active
        if self.pentagram_fade_active:
            elapsed = current_time - self.pentagram_fade_start_time
            fade_progress = min(1.0, elapsed / self.pentagram_fade_duration)
            
            # Update the fade - reverse of the growth animation
            self.current_outer_circle_radius = self.outer_circle_radius * (1.0 - fade_progress)
            
            # When fade is complete, complete the transition
            if fade_progress >= 1.0:
                self.pentagram_fade_active = False
                self.current_outer_circle_radius = 0
                self.complete_final_phase_transition()
                return
                
        # Check if the last copy has reached the center
        if len(self.copies) > 0 and self.blinking_copy_index is not None:
            # Update the copy's blinking state
            if current_time % 200 < 100:  # Fast blinking (every 200ms)
                if self.copies[self.blinking_copy_index].alpha > 50:
                    self.copies[self.blinking_copy_index].alpha = 50
                else:
                    self.copies[self.blinking_copy_index].alpha = 200
                self.copies[self.blinking_copy_index].image.set_alpha(self.copies[self.blinking_copy_index].alpha)
            
            # Check if the copy has reached the center
            if (abs(self.copies[self.blinking_copy_index].rect.centerx - self.pentagram_center[0]) < 5 and
                abs(self.copies[self.blinking_copy_index].rect.centery - self.pentagram_center[1]) < 5):
                # If the copy has reached the center, make it fade out
                self.copies[self.blinking_copy_index].alpha -= 5
                self.copies[self.blinking_copy_index].image.set_alpha(self.copies[self.blinking_copy_index].alpha)
                
                # When fully transparent, remove it
                if self.copies[self.blinking_copy_index].alpha <= 0:
                    self.copies.pop(self.blinking_copy_index)
                    self.blinking_copy_index = None
        
        # After the final phase is activated and the chase delay has passed, the dark lord starts chasing
        if not self.pentagram_fade_active and hasattr(self, 'chase_start_time'):
            chase_elapsed = current_time - self.chase_start_time
            if chase_elapsed >= self.chase_delay:
                # Start chasing
                if not hasattr(self, 'chase_active') or not self.chase_active:
                    self.chase_active = True
                    self.add_debug_message("Dark Lord begins chasing!")
                    
                    # Play angry sound
                    self.sound_manager.play_sound("effects/boss_angry")

    def use_random_ability(self, player):
        """Use a random ability based on the current phase"""
        current_time = pygame.time.get_ticks()
        
        # Update last ability time
        self.last_ability_time = current_time
        
        # Phase 5 abilities
        if self.phase == 5:
            # Use ability based on sequence state
            if self.ability_sequence_state == 'rope':
                # Use rope cone ability
                self.start_rope_cone_ability(player)
                # Next will be charge after a delay
                self.ability_sequence_state = 'wait_for_charge'
            elif self.ability_sequence_state == 'charge':
                # Use charge ability
                self.start_charge_ability(player)
                # Next will be projectile attack after a delay
                self.ability_sequence_state = 'wait_for_projectile'
            elif self.ability_sequence_state == 'projectile':
                # Use projectile attack
                self.start_projectile_attack(player)
                # Next will be rope after cooldown
                self.ability_sequence_state = 'rope'
            return True
            
        return False
    
    def start_rope_cone_ability(self, player):
        """Start the rope cone ability (similar to level 4 boss rope ability but in a cone)"""
        if not player:
            return False
            
        # Initialize rope cone properties
        self.rope_cone_active = True
        self.rope_cone_start_time = pygame.time.get_ticks()
        self.rope_cone_cast_duration = 1000  # 1 second cast time
        self.rope_cone_casting = True
        self.rope_cone_cast_complete = False
        self.rope_cone_telegraph_progress = 0.0
        
        # Save player's position at start for aiming the cone
        player_x, player_y = player.rect.centerx, player.rect.centery
        self.rope_cone_target_angle = math.atan2(player_y - self.rect.centery, player_x - self.rect.centerx)
        
        # Rope properties
        self.rope_cone_count = 4  # 4 ropes in the cone
        self.rope_cone_spread = math.pi / 4  # 45 degree cone spread
        self.rope_cone_max_length = TILE_SIZE * 7  # 7 tiles max length for ropes (increased from 5)
        self.rope_cone_ropes = []  # List to store rope data
        self.rope_cone_rope_width = 3  # Width of the rope lines
        self.rope_cone_pull_speed = 6  # How fast to pull player
        self.rope_cone_pull_duration = 1000  # 1 second pull duration
        
        # Make boss stop moving during cast
        self.rope_cone_original_speed = self.speed
        self.speed = 0
        
        # Add debug message
        if hasattr(self, 'add_debug_message'):
            self.add_debug_message("Starting rope cone ability cast")
            
        # Play sound if available
        if hasattr(self, 'sound_manager'):
            self.sound_manager.play_sound("effects/boss_10_ability")
            
        return True
    
    def update_rope_cone_ability(self, current_time, player):
        """Update the rope cone ability"""
        if not self.rope_cone_active or not player:
            return
            
        # Handle the casting phase
        if self.rope_cone_casting:
            elapsed_cast_time = current_time - self.rope_cone_start_time
            self.rope_cone_telegraph_progress = min(1.0, elapsed_cast_time / self.rope_cone_cast_duration)
            
            # Check if cast is complete
            if elapsed_cast_time >= self.rope_cone_cast_duration:
                self.rope_cone_casting = False
                self.rope_cone_cast_complete = True
                self.create_rope_cone(player)
                
                # Add debug message
                if hasattr(self, 'add_debug_message'):
                    self.add_debug_message("Rope cone cast complete, firing ropes")
                
        # Update active ropes after casting is complete
        elif self.rope_cone_cast_complete:
            # Check if any rope has hit the player
            rope_hit = False
            player_rect = pygame.Rect(player.rect.x, player.rect.y, player.rect.width, player.rect.height)
            
            for rope in self.rope_cone_ropes:
                # Skip ropes that are already pulling or have hit walls
                if rope['is_pulling'] or rope['hit_wall']:
                    continue
                    
                # Update rope length
                if rope['length'] < self.rope_cone_max_length:
                    rope['length'] += rope['speed']
                    
                    # Calculate end position
                    rope['end_x'] = self.rect.centerx + math.cos(rope['angle']) * rope['length']
                    rope['end_y'] = self.rect.centery + math.sin(rope['angle']) * rope['length']
                    
                    # Check if rope hit a wall
                    if (hasattr(player, 'level') and player.level and 
                        player.level.check_collision(pygame.Rect(
                            rope['end_x']-5, rope['end_y']-5, 10, 10), check_only_walls=True)):
                        rope['hit_wall'] = True
                        continue
                        
                    # Check if rope hit player
                    rope_end_rect = pygame.Rect(rope['end_x']-5, rope['end_y']-5, 10, 10)
                    if rope_end_rect.colliderect(player_rect) and not rope['is_pulling']:
                        rope['is_pulling'] = True
                        rope['pull_start_time'] = current_time
                        rope_hit = True
                        
                        # Add debug message
                        if hasattr(self, 'add_debug_message'):
                            self.add_debug_message("Rope hit player, starting pull")
                
            # Handle player pulling if any rope has hit them
            for rope in self.rope_cone_ropes:
                if rope['is_pulling']:
                    time_pulling = current_time - rope['pull_start_time']
                    
                    if time_pulling < self.rope_cone_pull_duration:
                        # Calculate pull direction
                        dx = self.rect.centerx - player.rect.centerx
                        dy = self.rect.centery - player.rect.centery
                        distance = math.sqrt(dx*dx + dy*dy)
                        
                        if distance > 0:
                            # Normalize and scale by pull speed
                            dx = dx / distance * self.rope_cone_pull_speed
                            dy = dy / distance * self.rope_cone_pull_speed
                            
                            # Move player towards boss
                            player.rect.x += dx
                            player.rect.y += dy
                            
                            # Update collision rect if it exists
                            if hasattr(player, 'collision_rect'):
                                player.collision_rect.center = player.rect.center
                            
                            # Keep rope end at player position
                            rope['end_x'] = player.rect.centerx
                            rope['end_y'] = player.rect.centery
                    else:
                        # Pulling complete
                        rope['is_pulling'] = False
                        
                        # End ability if all ropes are done
                        self.check_rope_cone_complete()
            
            # Check if all ropes have reached max length or hit walls
            all_ropes_done = True
            for rope in self.rope_cone_ropes:
                if not rope['hit_wall'] and rope['length'] < self.rope_cone_max_length and not rope['is_pulling']:
                    all_ropes_done = False
                    break
                    
            if all_ropes_done and not any(rope['is_pulling'] for rope in self.rope_cone_ropes):
                # All ropes have either hit a wall, reached max length, or finished pulling
                self.end_rope_cone_ability()
    
    def create_rope_cone(self, player):
        """Create and fire the rope cone after cast is complete"""
        # Use the saved target angle from when we started casting
        # (instead of recalculating based on player's current position)
        base_angle = self.rope_cone_target_angle
        
        # Calculate angles for each rope in the cone
        self.rope_cone_ropes = []
        
        if self.rope_cone_count == 1:
            # Single rope at base angle
            self.rope_cone_ropes.append({
                'angle': base_angle,
                'length': 0,
                'speed': 10,
                'end_x': self.rect.centerx,
                'end_y': self.rect.centery,
                'is_pulling': False,
                'hit_wall': False,
                'pull_start_time': 0
            })
        else:
            # Multiple ropes spread in a cone
            half_spread = self.rope_cone_spread / 2
            angle_step = self.rope_cone_spread / (self.rope_cone_count - 1)
            
            for i in range(self.rope_cone_count):
                # Calculate angle offset from center of cone
                angle_offset = -half_spread + (i * angle_step)
                rope_angle = base_angle + angle_offset
                
                # Create rope data
                self.rope_cone_ropes.append({
                    'angle': rope_angle,
                    'length': 0,
                    'speed': 10,
                    'end_x': self.rect.centerx,
                    'end_y': self.rect.centery,
                    'is_pulling': False,
                    'hit_wall': False,
                    'pull_start_time': 0
                })
        
        # Add debug message
        if hasattr(self, 'add_debug_message'):
            self.add_debug_message(f"Firing {len(self.rope_cone_ropes)} ropes at angle {base_angle:.2f}")
    
    def check_rope_cone_complete(self):
        """Check if the rope cone ability is complete"""
        if not self.rope_cone_active:
            return
            
        # Check if all ropes are done (hit wall, reached max length, or finished pulling)
        all_done = True
        for rope in self.rope_cone_ropes:
            if rope['is_pulling']:
                all_done = False
                break
                
        if all_done:
            self.end_rope_cone_ability()
    
    def end_rope_cone_ability(self):
        """End the rope cone ability and reset boss state"""
        self.rope_cone_active = False
        self.rope_cone_casting = False
        self.rope_cone_cast_complete = False
        self.rope_cone_ropes = []
        
        # Restore boss's original speed
        if hasattr(self, 'rope_cone_original_speed'):
            self.speed = self.rope_cone_original_speed
            
        # Add debug message
        if hasattr(self, 'add_debug_message'):
            self.add_debug_message("Rope cone ability ended")
    
    def draw_rope_cone_telegraph(self, surface):
        """Draw the telegraph for the rope cone ability during cast time"""
        if not hasattr(self, 'rope_cone_active') or not self.rope_cone_active or not self.rope_cone_casting:
            return
            
        # Calculate the cone boundaries
        base_angle = self.rope_cone_target_angle
        half_spread = self.rope_cone_spread / 2
        left_angle = base_angle - half_spread
        right_angle = base_angle + half_spread
        
        # Calculate current length based on cast progress
        current_length = self.rope_cone_max_length * self.rope_cone_telegraph_progress
        
        # Calculate points for the cone
        cone_points = [
            (self.rect.centerx, self.rect.centery),  # Apex of the cone
            (
                self.rect.centerx + math.cos(left_angle) * current_length,
                self.rect.centery + math.sin(left_angle) * current_length
            ),  # Left edge
            (
                self.rect.centerx + math.cos(base_angle) * current_length,
                self.rect.centery + math.sin(base_angle) * current_length
            ),  # Center point
            (
                self.rect.centerx + math.cos(right_angle) * current_length,
                self.rect.centery + math.sin(right_angle) * current_length
            ),  # Right edge
        ]
        
        # Create arc points to make a rounded cone shape
        arc_points = []
        arc_steps = 10
        angle_step = (right_angle - left_angle) / arc_steps
        for i in range(arc_steps + 1):
            angle = left_angle + (i * angle_step)
            arc_points.append((
                self.rect.centerx + math.cos(angle) * current_length,
                self.rect.centery + math.sin(angle) * current_length
            ))
        
        # Create the final polygon points
        polygon_points = [cone_points[0]] + arc_points
        
        # Draw filled cone with semi-transparency
        # Create a surface for the semi-transparent cone
        cone_surface = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        
        # Pulse the color intensity with time
        pulse_factor = (math.sin(pygame.time.get_ticks() / 150) + 1) / 2
        alpha = int(min(255, 100 + 50 * pulse_factor))  # Pulse between 100-150 alpha
        
        # Fill color that pulses with the cast progress
        progress_color = (
            int(255),  # Red increases with progress
            int(50),
            int(50),
            alpha
        )
        
        # Draw the filled cone
        pygame.draw.polygon(cone_surface, progress_color, polygon_points)
        
        # Blit the cone surface onto the main surface
        surface.blit(cone_surface, (0, 0))
        
        # Draw outline of the cone
        pygame.draw.lines(surface, (255, 0, 0), False, polygon_points, 2)
    
    def draw_rope_cone_ropes(self, surface):
        """Draw the ropes for the rope cone ability"""
        if not hasattr(self, 'rope_cone_active') or not self.rope_cone_active or not self.rope_cone_cast_complete:
            return
            
        # Draw each rope
        for rope in self.rope_cone_ropes:
            if rope['length'] <= 0:
                continue
                
            # Get start and end positions
            start_x, start_y = self.rect.centerx, self.rect.centery
            end_x, end_y = rope['end_x'], rope['end_y']
            
            # Draw rope with a zig-zag pattern similar to death rays
            if rope['length'] > 0:
                # Get current time for animation
                current_time = pygame.time.get_ticks()
                
                # Create list of points for the zig-zag path
                zig_zag_points = [
                    (start_x, start_y),  # Start point
                ]
                
                # Parameters for zig-zag effect
                segment_length = 20  # Length of each segment in the zig-zag
                
                # Calculate number of segments based on rope length
                num_segments = max(1, int(rope['length'] / segment_length))
                remaining_length = rope['length']
                
                # Calculate current direction vector
                dir_x = math.cos(rope['angle'])
                dir_y = math.sin(rope['angle'])
                
                # Create perpendicular vector for zig-zag displacement
                perp_x = -dir_y
                perp_y = dir_x
                
                # Current position
                current_x, current_y = start_x, start_y
                
                # Animation modifier for zig-zag
                animation_speed = 0.02
                animation_offset = current_time * animation_speed % (math.pi * 2)
                
                # Base amplitude for zig-zag
                amplitude = 2
                
                # Create each segment of the zig-zag
                for j in range(num_segments):
                    # Calculate segment length
                    seg_length = min(segment_length, remaining_length)
                    if seg_length <= 0:
                        break
                        
                    # Calculate position along rope
                    segment_progress = (j * segment_length) / rope['length']
                    
                    # Calculate displacement using sine wave
                    wave_position = segment_progress * 10 + animation_offset
                    displacement = amplitude * math.sin(wave_position)
                    
                    # Apply displacement perpendicular to rope direction
                    offset_x = perp_x * displacement
                    offset_y = perp_y * displacement
                    
                    # Calculate next point position
                    next_x = current_x + (dir_x * seg_length) + offset_x
                    next_y = current_y + (dir_y * seg_length) + offset_y
                    
                    # Add point to path
                    zig_zag_points.append((next_x, next_y))
                    
                    # Update current position (without perpendicular displacement)
                    current_x += dir_x * seg_length
                    current_y += dir_y * seg_length
                    
                    # Reduce remaining length
                    remaining_length -= seg_length
                
                # Make sure the last point is exactly at the end of the rope
                zig_zag_points.append((end_x, end_y))
                
                # Draw the zig-zag rope
                if len(zig_zag_points) > 1:
                    # Determine color based on if rope is pulling
                    rope_color = (255, 0, 0, 200) if rope['is_pulling'] else (200, 0, 0, 200)
                    
                    pygame.draw.lines(
                        surface,
                        rope_color,
                        False,  # Don't connect last point to first
                        zig_zag_points,
                        self.rope_cone_rope_width
                    )
                    
                    # Draw a small glow at the end of the rope
                    glow_radius = self.rope_cone_rope_width * 1.5
                    pygame.draw.circle(
                        surface,
                        rope_color,
                        (int(end_x), int(end_y)),
                        int(glow_radius)
                    )
                    
                    # Draw a small glow at the start of the rope
                    pygame.draw.circle(
                        surface,
                        rope_color,
                        (int(start_x), int(start_y)),
                        int(glow_radius)
                    )

    def start_charge_ability(self, player):
        """Start the charge ability with telegraph"""
        if not player:
            return False
            
        # Initialize charge properties
        self.charge_active = True
        self.charge_start_time = pygame.time.get_ticks()
        self.charge_cast_duration = 1000  # 1 second cast time
        self.charge_casting = True
        self.charge_cast_complete = False
        self.charge_telegraph_progress = 0.0
        
        # Save player's position at start for aiming the charge
        player_x, player_y = player.rect.centerx, player.rect.centery
        self.charge_target_angle = math.atan2(player_y - self.rect.centery, player_x - self.rect.centerx)
        
        # Charge properties
        self.charge_length = TILE_SIZE * 8  # 8 tiles long
        self.charge_width = TILE_SIZE * 2   # 2 tiles wide
        self.charge_speed = 12  # Charge speed in pixels per update
        self.charge_damage = self.damage  # Use normal melee damage
        self.charge_distance_traveled = 0  # Track how far boss has charged
        
        # Store original position to calculate distance traveled
        self.charge_original_position = (self.rect.centerx, self.rect.centery)
        
        # Calculate target position (will be adjusted if hitting walls)
        target_x = self.rect.centerx + math.cos(self.charge_target_angle) * self.charge_length
        target_y = self.rect.centery + math.sin(self.charge_target_angle) * self.charge_length
        self.charge_target_position = (target_x, target_y)
        
        # Make boss stop moving during cast
        self.charge_original_speed = self.speed
        self.speed = 0
        
        # Add debug message
        if hasattr(self, 'add_debug_message'):
            self.add_debug_message("Starting charge ability cast")
            
        # Play sound if available
        if hasattr(self, 'sound_manager'):
            self.sound_manager.play_sound("effects/boss_10_charge")
            
        return True
    
    def update_charge_ability(self, current_time, player):
        """Update the charge ability cast and execution"""
        if not self.charge_active:
            return
            
        # Handle the casting phase
        if self.charge_casting:
            elapsed_cast_time = current_time - self.charge_start_time
            self.charge_telegraph_progress = min(1.0, elapsed_cast_time / self.charge_cast_duration)
            
            # Check if cast is complete
            if elapsed_cast_time >= self.charge_cast_duration:
                self.charge_casting = False
                self.charge_cast_complete = True
                
                # Set movement direction for charge
                self.charge_dir_x = math.cos(self.charge_target_angle)
                self.charge_dir_y = math.sin(self.charge_target_angle)
                
                # Add debug message
                if hasattr(self, 'add_debug_message'):
                    self.add_debug_message("Charge cast complete, starting charge")
                
        # Execute charge after casting is complete
        elif self.charge_cast_complete:
            # Store original position before moving
            old_x, old_y = self.rect.centerx, self.rect.centery
            
            # Move boss in charge direction
            new_x = self.rect.centerx + self.charge_dir_x * self.charge_speed
            new_y = self.rect.centery + self.charge_dir_y * self.charge_speed
            
            # Update position
            self.rect.centerx = int(new_x)
            self.rect.centery = int(new_y)
            
            # Update collision rect if it exists
            if hasattr(self, 'collision_rect'):
                self.collision_rect.center = self.rect.center
                
            # Update damage hitbox if it exists
            if hasattr(self, 'damage_hitbox'):
                self.damage_hitbox.center = self.rect.center
                
            # Check for collision with walls
            wall_collision = False
            if hasattr(player, 'level') and player.level:
                if player.level.check_collision(self.rect, check_only_walls=True):
                    # Revert to position before charge update
                    self.rect.centerx = old_x
                    self.rect.centery = old_y
                    
                    # Update collision rect again after revert
                    if hasattr(self, 'collision_rect'):
                        self.collision_rect.center = self.rect.center
                        
                    # Update damage hitbox again after revert
                    if hasattr(self, 'damage_hitbox'):
                        self.damage_hitbox.center = self.rect.center
                        
                    wall_collision = True
                    
                    # Add debug message
                    if hasattr(self, 'add_debug_message'):
                        self.add_debug_message("Charge hit wall and stopped")
            
            # Calculate distance traveled
            dx = self.rect.centerx - self.charge_original_position[0]
            dy = self.rect.centery - self.charge_original_position[1]
            self.charge_distance_traveled = math.sqrt(dx*dx + dy*dy)
            
            # Check for collision with player
            if hasattr(self, 'damage_hitbox') and self.damage_hitbox.colliderect(player.rect):
                # Apply damage to player
                player.take_damage(self.charge_damage)
                
                # Add debug message
                if hasattr(self, 'add_debug_message'):
                    self.add_debug_message(f"Charge hit player for {self.charge_damage} damage")
            
            # End charge if hit wall or traveled max distance
            if wall_collision or self.charge_distance_traveled >= self.charge_length:
                self.end_charge_ability()
    
    def end_charge_ability(self):
        """End the charge ability and reset boss state"""
        self.charge_active = False
        self.charge_casting = False
        self.charge_cast_complete = False
        
        # Restore boss's original speed
        if hasattr(self, 'charge_original_speed'):
            self.speed = self.charge_original_speed
            
        # Add debug message
        if hasattr(self, 'add_debug_message'):
            self.add_debug_message(f"Charge ended after traveling {self.charge_distance_traveled:.1f} pixels")
    
    def draw_charge_telegraph(self, surface):
        """Draw the telegraph for the charge ability during cast time"""
        if not hasattr(self, 'charge_active') or not self.charge_active or not self.charge_casting:
            return
            
        # Calculate the rectangle for the charge telegraph
        half_width = self.charge_width / 2
        
        # Calculate current length based on cast progress
        current_length = self.charge_length * self.charge_telegraph_progress
        
        # Calculate the end point of the charge
        end_x = self.rect.centerx + math.cos(self.charge_target_angle) * current_length
        end_y = self.rect.centery + math.sin(self.charge_target_angle) * current_length
        
        # Calculate the perpendicular vector for width
        perp_x = -math.sin(self.charge_target_angle)
        perp_y = math.cos(self.charge_target_angle)
        
        # Calculate the four corners of the rectangle
        top_left = (
            self.rect.centerx + perp_x * half_width,
            self.rect.centery + perp_y * half_width
        )
        top_right = (
            self.rect.centerx - perp_x * half_width,
            self.rect.centery - perp_y * half_width
        )
        bottom_right = (
            end_x - perp_x * half_width,
            end_y - perp_y * half_width
        )
        bottom_left = (
            end_x + perp_x * half_width,
            end_y + perp_y * half_width
        )
        
        # Create the polygon points
        polygon_points = [top_left, top_right, bottom_right, bottom_left]
        
        # Draw filled rectangle with semi-transparency
        # Create a surface for the semi-transparent rectangle
        charge_surface = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        
        # Pulse the color intensity with time
        pulse_factor = (math.sin(pygame.time.get_ticks() / 150) + 1) / 2
        alpha = int(min(255, 100 + 50 * pulse_factor))  # Pulse between 100-150 alpha
        
        # Fill color that pulses
        progress_color = (
            int(255),  # Red
            int(min(255, 120 + 100 * pulse_factor)),  # Yellow-orange pulsing
            int(0),
            alpha
        )
        
        # Draw the filled rectangle
        pygame.draw.polygon(charge_surface, progress_color, polygon_points)
        
        # Blit the charge surface onto the main surface
        surface.blit(charge_surface, (0, 0))
        
        # Draw outline of the rectangle
        pygame.draw.lines(surface, (255, 150, 0), True, polygon_points, 2)
        
        # Draw arrow at the end to indicate direction
        arrow_size = half_width * 0.8
        arrow_tip = (
            end_x + math.cos(self.charge_target_angle) * arrow_size,
            end_y + math.sin(self.charge_target_angle) * arrow_size
        )
        
        arrow_left = (
            end_x + math.cos(self.charge_target_angle - 2.5) * arrow_size,
            end_y + math.sin(self.charge_target_angle - 2.5) * arrow_size
        )
        
        arrow_right = (
            end_x + math.cos(self.charge_target_angle + 2.5) * arrow_size,
            end_y + math.sin(self.charge_target_angle + 2.5) * arrow_size
        )
        
        # Draw arrow
        pygame.draw.polygon(surface, (255, 200, 0), [arrow_tip, arrow_left, arrow_right], 0)

    def start_projectile_attack(self, player):
        """Start the projectile attack, firing 3 projectiles in a circle"""
        if not player:
            return False
            
        # Create 3 projectiles spread evenly around in a circle
        for i in range(3):
            angle = (i * 2 * math.pi / 3) + random.uniform(0, math.pi/6)  # Add slight randomness
            dx = math.cos(angle)
            dy = math.sin(angle)
            
            # Create projectile
            projectile = BossProjectile(
                self.rect.centerx,
                self.rect.centery,
                (dx, dy),
                speed=self.projectile_speed,
                damage=self.projectile_damage,
                color=self.projectile_color,
                boss_level=10,  # Dark Lord projectiles
                spawn_secondary=True,  # Enable splitting
                spawn_time=self.projectile_split_time,  # Split after 2 seconds
                orbit_boss=self  # Reference to the boss for spawning
            )
            
            # Reduce the max distance so projectiles have time to split before leaving screen
            projectile.max_distance = TILE_SIZE * 20
            
            # Override the spawn_secondary_projectiles method with our custom implementation
            def custom_spawn_secondary_projectiles(proj_self):
                # Create 3 projectiles at 120-degree intervals
                for j in range(3):
                    split_angle = (j * 2 * math.pi / 3) + random.uniform(0, math.pi/6)  # Add slight randomness
                    split_dx = math.cos(split_angle)
                    split_dy = math.sin(split_angle)
                    
                    # Create new projectile with same properties but no secondary spawn
                    secondary = BossProjectile(
                        proj_self.rect.centerx,
                        proj_self.rect.centery,
                        (split_dx, split_dy),
                        proj_self.speed,
                        proj_self.damage,
                        proj_self.color,
                        boss_level=10,
                        spawn_secondary=False  # Prevent infinite spawning
                    )
                    
                    # Make sure secondary projectiles live long enough
                    secondary.max_distance = TILE_SIZE * 15
                    
                    # Add to Dark Lord's projectile group
                    self.projectiles.add(secondary)
                    
                # Play sound effect for splitting
                if hasattr(self, 'sound_manager'):
                    self.sound_manager.play_sound("effects/boss_projectile_split")
                    
            # Replace the original method with our custom one
            projectile.spawn_secondary_projectiles = types.MethodType(custom_spawn_secondary_projectiles, projectile)
            
            # Add to projectile group
            self.projectiles.add(projectile)
        
        # Play projectile sound
        if hasattr(self, 'sound_manager'):
            self.sound_manager.play_sound("effects/boss_10_projectile")
            
        # Add debug message
        if hasattr(self, 'add_debug_message'):
            self.add_debug_message("Fired 3 projectiles that will split after 2 seconds")
            
        return True

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