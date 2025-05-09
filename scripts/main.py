import pygame
import sys
import os
import time
import random
import math
import atexit
import argparse
import traceback

# Add the parent directory to the path so we can import config
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import *
from scripts.player import Player
from scripts.level import Level
from scripts.weapons import WeaponManager
from scripts.ui import Menu, HUD
from scripts.asset_manager import get_asset_manager
from scripts.camera import Camera  # Import our new Camera class
from scripts.sound_manager import get_sound_manager  # Import our new sound manager
from scripts.particle import ParticleSystem  # Import our new particle system
from scripts.controller import ControllerHandler  # Import our new controller handler

class Game:
    def __init__(self, start_fullscreen=False):
        global WINDOW_WIDTH, WINDOW_HEIGHT
        
        # Initialize pygame
        pygame.init()
        
        # Create screen
        if start_fullscreen:
            self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.FULLSCREEN)
            self.fullscreen = True
        else:
            self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
            self.fullscreen = False
            
        # Set window title and icon
        pygame.display.set_caption("Mud Crawler")
        
        # Try to load icon
        try:
            icon_path = os.path.join(ASSET_PATH, "icon.ico")
            if os.path.exists(icon_path):
                icon = pygame.image.load(icon_path)
                pygame.display.set_icon(icon)
                print(f"Successfully loaded game icon: {icon_path}")
        except Exception as e:
            print(f"Failed to load game icon: {e}")
            
        # Initialize clock for controlling frame rate
        self.clock = pygame.time.Clock()
        
        # Splash screen attributes
        self.splash_start_time = 0
        self.splash_image = None
        self.original_splash_image = None
        self.glitched_splash_image = None
        self.glitch_next_frame = False
        self.splash_duration = 3000  # 3 seconds
        self.glitch_duration = 1500  # Show glitches for first 1.5 seconds
        self.glitch_last_update = 0  # Time of last glitch update
        self.glitch_update_rate = 50  # Update glitches every 50ms
        
        # Intro scene attributes
        self.intro_images = []
        self.intro_videos = []
        self.intro_current_image = 0
        self.intro_start_time = 0
        self.intro_image_duration = 5000  # 5 seconds per image
        self.intro_fade_duration = 1000  # 1 second fade transition
        self.intro_alpha = 255  # Fully opaque
        self.intro_fading = False
        self.intro_fade_start_time = 0
        self.intro_fade_in = True
        self.current_video_player = None
        self.intro_subtitles = [
            ["In the realm of Eldoria, peace reigned,", "and Princess Anya's laughter filled the halls."],
            ["She was the light of my life,", "the anchor of my world."], 
            ["Then, from the chaotic void, he emerged", "Git, the Unclean Merger."],
            ["His corrupted code lashed out,", "ensnaring the Princess in broken data!"],
            ["He dragged her into the murky depths", "of the Mud Crawler's Lair..."],
            ["Through mud and conflict,", "I will merge her fate back with mine.", "Anya, I'm coming!"]
        ]
        
        # Try to create a simple splash screen
        try:
            # Create a black screen with logo
            self.splash_image = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
            self.splash_image.fill((0, 0, 0))
            
            # Add a simple gradient background
            for y in range(WINDOW_HEIGHT):
                for x in range(WINDOW_WIDTH):
                    brightness = 30 + (y / WINDOW_HEIGHT) * 30
                    self.splash_image.set_at((x, y), (int(brightness), int(brightness * 0.8), int(brightness * 0.5)))
            
            # Add "MUD CRAWLER" text
            font_path = os.path.join(ASSET_PATH, "fonts/PixelatedEleganceRegular-ovyAA.ttf")
            if os.path.exists(font_path):
                font = pygame.font.Font(font_path, 72)
            else:
                font = pygame.font.Font(None, 72)
            
            logo_text = font.render("MUD CRAWLER", True, (255, 255, 255))
            shadow_text = font.render("MUD CRAWLER", True, (0, 0, 0))
            
            # Position in center with shadow
            text_x = (WINDOW_WIDTH - logo_text.get_width()) // 2
            text_y = (WINDOW_HEIGHT - logo_text.get_height()) // 2
            self.splash_image.blit(shadow_text, (text_x + 3, text_y + 3))
            self.splash_image.blit(logo_text, (text_x, text_y))
            
            # Add "loading..." text at bottom
            small_font = pygame.font.Font(None, 24)
            loading_text = small_font.render("Loading...", True, (200, 200, 200))
            self.splash_image.blit(loading_text, ((WINDOW_WIDTH - loading_text.get_width()) // 2, WINDOW_HEIGHT - 100))
            
            # Store the original splash image
            self.original_splash_image = self.splash_image.copy()
            
            # Create a glitched version for visual effects
            self.glitched_splash_image = self._apply_horizontal_glitch(self.original_splash_image.copy())
            
            print("Splash screen created successfully")
        except Exception as e:
            print(f"Failed to create splash screen: {e}")
            # Create a minimal fallback
            self.splash_image = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
            self.splash_image.fill((0, 0, 0))
            self.original_splash_image = self.splash_image
            self.glitched_splash_image = self.splash_image
            
        # Load intro videos and images
        try:
            intro_dir = os.path.join(ASSET_PATH, "images/intro_scene")
            if os.path.exists(intro_dir):
                # Check for all 6 videos
                for i in range(1, 7):
                    video_path = os.path.join(intro_dir, f"intro_0{i}.mp4")
                    if os.path.exists(video_path):
                        # For the last video, we'll use ping-pong mode
                        ping_pong = (i == 6)
                        
                        # Create placeholder entries - actual VideoPlayer will be initialized when needed
                        self.intro_videos.append({
                            'path': video_path,
                            'player': None,
                            'ping_pong': ping_pong
                        })
                        print(f"Found intro video: {video_path}" + (" (ping-pong)" if ping_pong else ""))
                    else:
                        print(f"Video not found: {video_path}")
                        self.intro_videos.append(None)
                
                print(f"Loaded {len(self.intro_videos)} intro videos")
            else:
                print(f"Intro scene directory not found: {intro_dir}")
        except Exception as e:
            print(f"Failed to load intro assets: {e}")
            traceback.print_exc()
        
        # Game configuration
        self.god_mode = False
        self.infinite_arrows = False
        self.infinite_special = False
        self.infinite_stamina = False
        
        # Debug flags
        self.debug_frame_times = False
        self.debug_particles = False
        
        # Shake effect
        self.shake_amount = 0
        self.shake_duration = 0
        self.shake_offset = [0, 0]
        
        # List to store delayed screen shake requests
        self.shake_requests = []
        
        # Initialize game variables
        self.last_frame_time = pygame.time.get_ticks()
        self.frame_times = []  # Store last N frame times
        self.frame_time_sum = 0
        self.frame_time_count = 0
        
        # Torch lighting settings
        self.torch_enabled = True
        self.torch_radius = 300
        self.torch_inner_radius = 150
        self.darkness_level = 220  # Increased from 180 to 220 to make the field darker
        
        # Death sequence flag
        self.death_sequence_active = False
        self.death_message_shown = False
        self.death_zoom_complete = False
        self.death_zoom_start_time = 0
        self.death_zoom_duration = 3000  # 3 seconds for zoom effect
        self.death_original_zoom = 2.0  # Store original zoom level
        self.death_target_zoom = 4.0  # Target zoom level for death sequence
        
        # Boss introduction sequence
        self.boss_intro_active = False
        self.boss_intro_start_time = 0
        self.boss_intro_duration = 2000  # 2 seconds for boss intro
        self.boss_intro_original_zoom = 2.0
        self.boss_intro_target_zoom = 3.0
        self.boss_intro_complete = False
        self.boss_intro_original_camera_pos = None
        self.boss_intro_target_camera_pos = None
        
        # Special attack variables
        self.special_attack_active = False
        self.special_attack_data = None
        self.kill_counter = 0  # Counter of enemy kills
        self.kill_counter_max = 10  # Kills needed for special attack
        
        # Special attack trail effect
        self.special_attack_trail_positions = []  # List of positions for trail images
        self.special_attack_trail_duration = 1500  # How long trail lasts in milliseconds (3x dodge trail)
        
        # Debug: Print working directory
        print(f"Current working directory: {os.getcwd()}")
        print(f"Asset path: {ASSET_PATH}")
        print(f"Player sprites path: {PLAYER_SPRITES_PATH}")
        print(f"Absolute player sprites path: {os.path.abspath(PLAYER_SPRITES_PATH)}")
        
        # Set up display
        self.fullscreen = start_fullscreen
        
        if self.fullscreen:
            # Get display info for fullscreen mode
            display_info = pygame.display.Info()
            WINDOW_WIDTH = display_info.current_w
            WINDOW_HEIGHT = display_info.current_h
            self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT), 
                                               pygame.FULLSCREEN | pygame.HWSURFACE | pygame.DOUBLEBUF)
        else:
            self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
            
        self.clock = pygame.time.Clock()
        
        # Store original window size
        self.windowed_size = (WINDOW_WIDTH, WINDOW_HEIGHT)
        
        # Initialize camera with screen dimensions
        self.camera = Camera(WINDOW_WIDTH, WINDOW_HEIGHT)
        
        # Initialize sound manager
        self.sound_manager = get_sound_manager()
        
        # Initialize asset manager first
        self.asset_manager = get_asset_manager()
        print("Asset manager initialized")
        
        # Set custom mouse cursor
        self.set_custom_cursor()
        
        # Check if assets directory exists, if not create it with necessary subdirectories
        self.ensure_asset_directories()
        
        # Initialize controller handler
        self.controller_handler = ControllerHandler()
        
        # Debug font
        self.debug_font = pygame.font.Font(None, 24)
        
        # Game state
        self.running = True
        self.state = SPLASH_SCREEN  # Start with splash screen instead of menu
        self.current_level = 1
        self.max_levels = 10
        
        # State transition protection - prevents immediate weapon use after state change
        self.state_transition_time = pygame.time.get_ticks()
        self.state_transition_cooldown = 500  # 500ms cooldown after state change
        
        # Initialize UI first
        self.menu = Menu(self.screen)
        self.hud = HUD(self.screen)
        
        # Initialize particle system
        self.particle_system = ParticleSystem()
        
        # Initialize game components
        self.player = Player(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2)
        self.player.set_game(self)  # Set game instance in player
        self.weapon_manager = WeaponManager(self.player)
        
        # Level is initialized only when starting the game, not at menu
        self.level = None
        
        # Don't play welcome music during splash screen - it will be started after splash screen
        
        # Print debug info
        print(f"Game initialized. State: {self.state}")
        print(f"Screen size: {WINDOW_WIDTH}x{WINDOW_HEIGHT}")
        print(f"Camera zoom: {self.camera.zoom}x")
        
        # Splash screen
        self.splash_start_time = None
        self.splash_duration = 5000  # 5 seconds in milliseconds
        self.splash_image = None
        self.glitch_duration = 1500  # 1.5 seconds in milliseconds
        self.glitch_last_update = 0
        self.glitch_update_rate = 50  # milliseconds between glitch updates
        self.original_splash_image = None
        self.glitched_splash_image = None
        
        try:
            splash_path = os.path.join(ASSET_PATH, "images/near_human.png")
            if not os.path.exists(splash_path):
                # Try alternative image if specified one doesn't exist
                splash_path = os.path.join(ASSET_PATH, "images/almost_human.png")
                print(f"Splash screen image 'near_human.png' not found, trying alternative: {splash_path}")
                
            if os.path.exists(splash_path):
                self.original_splash_image = pygame.image.load(splash_path)
                self.original_splash_image = pygame.transform.scale(self.original_splash_image, (WINDOW_WIDTH, WINDOW_HEIGHT))
                self.splash_image = self.original_splash_image.copy()
                print(f"Successfully loaded splash screen image: {splash_path}")
            else:
                print(f"Splash screen image not found: {splash_path}")
                self.state = MENU  # Skip to menu if image not found
        except Exception as e:
            print(f"Failed to load splash screen image: {e}")
            self.state = MENU  # Skip to menu if there's an error
        
    def ensure_asset_directories(self):
        """Make sure all the asset directories exist"""
        # Check assets root directory
        if not os.path.exists(ASSET_PATH):
            print(f"Creating assets directory at {ASSET_PATH}")
            os.makedirs(ASSET_PATH, exist_ok=True)
            
        # Create subdirectories for each asset type
        for path in [
            PLAYER_SPRITES_PATH,
            ENEMY_SPRITES_PATH,
            BOSS_SPRITES_PATH,
            WEAPON_SPRITES_PATH,
            TILE_SPRITES_PATH,
            UI_SPRITES_PATH,
            SOUNDS_PATH
        ]:
            if not os.path.exists(path):
                print(f"Creating directory: {path}")
                os.makedirs(path, exist_ok=True)
        
        # Print informational message about asset placement
        print("-" * 50)
        print("ASSETS SETUP INFORMATION:")
        print("Place your texture files in the following directories:")
        print(f"- Player textures: {PLAYER_SPRITES_PATH}")
        print(f"- Enemy textures: {ENEMY_SPRITES_PATH}")
        print(f"- Boss textures: {BOSS_SPRITES_PATH}")
        print(f"- Weapon textures: {WEAPON_SPRITES_PATH}")
        print(f"- Tile textures: {TILE_SPRITES_PATH}")
        print(f"- UI textures: {UI_SPRITES_PATH}")
        print(f"- Sound files: {SOUNDS_PATH}")
        print("-" * 50)
        
    def reset_game(self):
        print("Resetting game...")
        self.current_level = 1
        # Reset death sequence flags
        self.death_sequence_active = False
        self.death_message_shown = False
        self.death_zoom_complete = False
        self.death_zoom_start_time = 0
        self.death_zoom_duration = 3000  # 3 seconds for zoom effect
        self.death_original_zoom = 2.0  # Store original zoom level
        self.death_target_zoom = 4.0  # Target zoom level for death sequence
        
        # Reset special ability counter
        self.kill_counter = 0
        print(f"Special ability counter reset: {self.kill_counter}/{self.kill_counter_max}")
        
        # Reset camera zoom to default value
        self.camera.zoom = 2.0  # Reset to default zoom
        self.camera.view_width = self.camera.width / self.camera.zoom
        self.camera.view_height = self.camera.height / self.camera.zoom
        print(f"Camera zoom reset to default: {self.camera.zoom}x")
        
        # Reset particle system
        self.particle_system = ParticleSystem()
        # First initialize the level
        self.level = Level(self.current_level)
        
        # Give the level access to the particle system and game instance
        self.level.particle_system = self.particle_system
        self.level.game = self
        
        # Then get a valid position for the player
        player_x, player_y = self.level.get_valid_player_start_position()
        self.player = Player(player_x, player_y)
        self.player.set_game(self)  # Set game instance in player
        self.player.level = self.level  # Give player a reference to the level
        self.weapon_manager = WeaponManager(self.player)
        # Ensure any existing arrows are cleared
        self.weapon_manager.clear_arrows()
        
        # Play level-appropriate music
        self.play_level_appropriate_music()
        
    def initialize_level(self):
        print(f"Initializing level {self.current_level}")
        self.level = Level(self.current_level)
        
        # Give the level access to the particle system and game instance
        self.level.particle_system = self.particle_system
        self.level.game = self
        
        # Get a valid starting position for the player
        player_x, player_y = self.level.get_valid_player_start_position()
        self.player.rect.centerx = player_x
        self.player.rect.centery = player_y
        self.player.level = self.level  # Give player a reference to the level
        
        # Play level-appropriate music
        self.play_level_appropriate_music()
        
    def screen_to_world_coords(self, screen_x, screen_y):
        """Convert screen coordinates to world coordinates accounting for camera"""
        world_x = screen_x / self.camera.zoom + self.camera.x
        world_y = screen_y / self.camera.zoom + self.camera.y
        return (world_x, world_y)

    def handle_events(self):
        # Process controller input if available
        controller_events = self.controller_handler.update_controller()
        
        # Add the controller events to pygame's event queue
        for event in controller_events:
            pygame.event.post(event)
            
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                
            # Skip other event handling during splash screen except for clicks/keys to skip
            if self.state == SPLASH_SCREEN:
                if event.type in (pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN):
                    print(f"Splash screen skipped after {pygame.time.get_ticks() - self.splash_start_time}ms")
                    if self.intro_images and len(self.intro_images) > 0:
                        # If we have intro images, go to intro scene
                        self.state = INTRO_SCENE
                        self.intro_start_time = pygame.time.get_ticks()
                        self.intro_current_image = 0
                        self.intro_alpha = 0  # Start with fade in
                        self.intro_fading = True
                        self.intro_fade_in = True
                        self.intro_fade_start_time = pygame.time.get_ticks()
                        print("Starting intro scene")
                        # Play intro music if available
                        self.sound_manager.play_music('intro')
                    else:
                        # Otherwise go directly to menu
                        self.state = MENU
                        print("Starting welcome screen music (after skip)")
                        self.sound_manager.play_music('menu')
                continue
                
            # Handle intro scene - allow skipping with any key/click
            if self.state == INTRO_SCENE:
                if event.type in (pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN):
                    print(f"Intro scene skipped at image {self.intro_current_image + 1}")
                    
                    # Stop video player if it's active
                    if self.current_video_player:
                        self.current_video_player.stop()
                        self.current_video_player = None
                    
                    self.state = MENU
                    print("Starting welcome screen music (after intro skip)")
                    self.sound_manager.play_music('menu')
                continue
            
            # Update player's attack direction based on mouse position
            # We need to do this continuously, not just on mouse click
            if self.state == PLAYING and not self.death_sequence_active:
                # Get screen mouse position
                screen_mouse_pos = pygame.mouse.get_pos()
                
                # Confine mouse to window to prevent it from disappearing
                self.confine_mouse_to_window()
                
                # Convert to world coordinates
                world_mouse_pos = self.screen_to_world_coords(*screen_mouse_pos)
                # Update player's attack direction
                self.player.update_attack_direction_from_mouse(world_mouse_pos)

            # Check for any key press during death sequence 
            if self.state == PLAYING and self.death_sequence_active and self.player.death_animation_complete:
                if event.type in (pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN):
                    print("Player pressed a button after death - showing game over screen")
                    self.state = GAME_OVER
                    # When game over track is added, uncomment this
                    # self.sound_manager.play_music('game_over')
                    continue  # Skip other event handling
                
            # Handle exit confirmation dialog if it's showing
            if self.level and self.level.show_exit_confirmation and event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # Left click
                    # Get dialog yes/no button rects
                    yes_rect, no_rect = self.level.draw_exit_confirmation(self.screen)
                    
                    # Check for clicks on the dialog buttons
                    # No need to convert coordinates since the dialog is drawn directly on screen
                    if yes_rect.collidepoint(event.pos):
                        print("Exit confirmed, proceeding to next level")
                        self.level.confirm_exit()
                    elif no_rect.collidepoint(event.pos):
                        print("Exit cancelled")
                        self.level.cancel_exit()
                continue  # Don't process other events while dialog is open
                
            # Handle menu button clicks - ONLY when in appropriate states (not during gameplay)
            if self.state in [MENU, PAUSED, GAME_OVER, VICTORY]:
                # Handle audio menu events if it's showing
                if self.menu.showing_audio:
                    if self.menu.handle_audio_menu_event(event):
                        continue

                # Check for any keypress during victory screen after credits have completed one cycle
                if self.state == VICTORY and self.menu.credits_completed and event.type in (pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN):
                    print("Key pressed after credits completion - returning to welcome screen")
                    # Reset game state
                    self.reset_game()
                    # Reset menu state
                    self.menu.show_credits = False
                    self.menu.credits_completed = False
                    self.menu.credits_y = self.menu.screen.get_height()
                    # Change state to menu
                    self.state = MENU
                    # Play welcome screen music
                    self.sound_manager.play_music('menu')
                    continue  # Skip other event handling

                button_clicked = self.menu.handle_event(event)
                if button_clicked:
                    if button_clicked == 'start':
                        print("Start button clicked")
                        if self.level is None:
                            self.initialize_level()
                        self.state = PLAYING
                        # Set transition time to prevent immediate bow attack
                        self.state_transition_time = pygame.time.get_ticks()
                        # Switch to appropriate music based on level
                        self.play_level_appropriate_music()
                    elif button_clicked == 'resume':
                        print("Resume button clicked")
                        self.state = PLAYING
                        # Set transition time to prevent immediate bow attack
                        self.state_transition_time = pygame.time.get_ticks()
                        # Unpause music if it was paused
                        self.sound_manager.unpause_music()
                    elif button_clicked == 'restart':
                        print("Restart button clicked")
                        self.reset_game()
                        self.state = PLAYING
                        # Set transition time to prevent immediate bow attack
                        self.state_transition_time = pygame.time.get_ticks()
                    elif button_clicked == 'options':
                        print("Options button clicked")
                        # Update button positions before showing options
                        self.menu.showing_options = True
                        self.menu._update_button_positions('options_menu')
                    elif button_clicked == 'audio':
                        print("Audio button clicked")
                        # Show audio menu
                        self.menu.showing_audio = True
                        self.menu.showing_options = False
                        # Slider values are now synced in draw_audio_menu
                    elif button_clicked == 'artworks':
                        print("Artworks button clicked")
                        # Show artworks menu
                        self.menu.showing_artworks = True
                        self.menu._update_button_positions('artworks_menu')
                        # Remember the previously playing music to restore it later
                        self.previous_music = self.sound_manager.current_music
                        # Play music for the selected level
                        self.play_artwork_music(self.menu.selected_level)
                    elif button_clicked == 'back':
                        print("Back button clicked")
                        # If we're in the controls menu, go back to options
                        if self.menu.showing_controls:
                            self.menu.showing_controls = False
                            self.menu.showing_options = True
                            self.menu._update_button_positions('options_menu')
                        # If we're in the audio menu, go back to options
                        elif self.menu.showing_audio:
                            self.menu.showing_audio = False
                            self.menu.showing_options = True
                            self.menu._update_button_positions('options_menu')
                        # If we're in the artworks menu, go back to main menu
                        elif self.menu.showing_artworks:
                            self.menu.showing_artworks = False
                            self.menu._update_button_positions('main_menu')
                            # Restore the previous music
                            if hasattr(self, 'previous_music') and self.previous_music:
                                self.sound_manager.play_music(self.previous_music)
                            else:
                                self.sound_manager.play_music('menu')
                        else:
                            # Otherwise normal back button behavior for options menu
                            self.menu.showing_options = False
                            # Update button positions when going back to previous menu
                            if self.state == MENU:
                                self.menu._update_button_positions('main_menu')
                                # Reset pause menu flag if we were in options from main menu
                                self.menu.in_pause_menu = False
                            elif self.state == PAUSED:
                                self.menu._update_button_positions('pause_menu')
                                # Set pause menu flag if we were in options from pause menu
                                self.menu.in_pause_menu = True
                    elif button_clicked == 'controls':
                        print("Controls button clicked")
                        # Show controls menu
                        self.menu.showing_controls = True
                        self.menu.showing_options = False
                        self.menu._update_button_positions('controls_menu')
                    elif button_clicked == 'fullscreen':
                        print("Fullscreen toggle button clicked")
                        self.toggle_fullscreen()
                        # Make sure we stay in options menu after toggling fullscreen
                        self.menu.showing_options = True
                        self.menu._update_button_positions('options_menu')
                    elif button_clicked == 'quit':
                        print("Quit button clicked")
                        self.running = False
                    # Handle level selection in artworks menu
                    elif button_clicked and button_clicked.startswith('level_'):
                        # Extract level number from the button clicked
                        level_num = int(button_clicked.split('_')[1])
                        print(f"Selected level {level_num} in artworks menu")
                        # Update music to match the selected level
                        self.play_artwork_music(level_num)
                    # Handle level warp cheat code
                    elif button_clicked and button_clicked.startswith('warp_to_level_'):
                        # Extract level number from the command
                        try:
                            level_num = int(button_clicked.split('_')[-1])
                            print(f"CHEAT CODE: Warping to level {level_num}")
                            self.warp_to_level(level_num)
                            # Return to playing state
                            self.state = PLAYING
                            # Unpause music
                            self.sound_manager.unpause_music()
                        except (ValueError, IndexError) as e:
                            print(f"Error parsing warp level: {e}")
            
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if self.state == PLAYING:
                        print("Pausing game")
                        self.state = PAUSED
                        # Pause music
                        self.sound_manager.pause_music()
                    elif self.state == PAUSED:
                        print("Resuming game")
                        self.state = PLAYING
                        # Set transition time to prevent immediate bow attack
                        self.state_transition_time = pygame.time.get_ticks()
                        # Unpause music
                        self.sound_manager.unpause_music()
                elif event.key == pygame.K_RETURN:
                    # Alt+Enter toggles fullscreen
                    if pygame.key.get_mods() & pygame.KMOD_ALT:
                        self.toggle_fullscreen()
                    elif self.state == MENU:
                        print("Enter key pressed at menu")
                        if self.level is None:
                            self.initialize_level()
                        self.state = PLAYING
                        # Set transition time to prevent immediate bow attack
                        self.state_transition_time = pygame.time.get_ticks()
                        # Switch to appropriate music based on level
                        self.play_level_appropriate_music()
                    elif self.state == GAME_OVER:
                        print("Enter key pressed at game over")
                        self.reset_game()
                        self.state = PLAYING
                        # Set transition time to prevent immediate bow attack
                        self.state_transition_time = pygame.time.get_ticks()
                    # Debug key - force state change
                    elif event.key == pygame.K_m:
                        self.state = MENU
                        print("Forced state change to MENU")
                        # Switch to menu music
                        self.sound_manager.play_music('menu')
                    elif event.key == pygame.K_p:
                        self.state = PLAYING
                        if self.level is None:
                            self.initialize_level()
                        print("Forced state change to PLAYING")
                        # Set transition time to prevent immediate bow attack
                        self.state_transition_time = pygame.time.get_ticks()
                        # Switch to appropriate music based on level
                        self.play_level_appropriate_music()
                    # Zoom control keys
                    elif event.key == pygame.K_PLUS or event.key == pygame.K_EQUALS:
                        self.camera.zoom = min(self.camera.zoom + 0.1, 3.0)
                        self.camera.view_width = self.camera.width / self.camera.zoom
                        self.camera.view_height = self.camera.height / self.camera.zoom
                        print(f"Zoom in: {self.camera.zoom:.1f}x")
                    elif event.key == pygame.K_MINUS:
                        self.camera.zoom = max(self.camera.zoom - 0.1, 1.0)
                        self.camera.view_width = self.camera.width / self.camera.zoom
                        self.camera.view_height = self.camera.height / self.camera.zoom
                        print(f"Zoom out: {self.camera.zoom:.1f}x")
                    # Sound controls
                    elif event.key == pygame.K_m and pygame.key.get_mods() & pygame.KMOD_CTRL:
                        enabled = self.sound_manager.toggle_music()
                        print(f"Music {'enabled' if enabled else 'disabled'}")
                    elif event.key == pygame.K_s and pygame.key.get_mods() & pygame.KMOD_CTRL:
                        enabled = self.sound_manager.toggle_sfx()
                        print(f"Sound effects {'enabled' if enabled else 'disabled'}")
                    # Volume controls
                    elif event.key == pygame.K_UP and pygame.key.get_mods() & pygame.KMOD_CTRL:
                        new_volume = min(1.0, self.sound_manager.music_volume + 0.1)
                        self.sound_manager.set_music_volume(new_volume)
                        print(f"Music volume: {int(new_volume * 100)}%")
                    elif event.key == pygame.K_DOWN and pygame.key.get_mods() & pygame.KMOD_CTRL:
                        new_volume = max(0.0, self.sound_manager.music_volume - 0.1)
                        self.sound_manager.set_music_volume(new_volume)
                        print(f"Music volume: {int(new_volume * 100)}%")
                    # Exit key
                    elif event.key == pygame.K_q:
                        self.running = False
                    # Toggle torch lighting with 'L' key
                    elif event.key == pygame.K_l:
                        self.torch_enabled = not self.torch_enabled
                    elif event.key == pygame.K_e:
                        self.activate_special_attack()
                
            if self.state == PLAYING:
                # Check if we're within the state transition cooldown period
                current_time = pygame.time.get_ticks()
                if current_time - self.state_transition_time < self.state_transition_cooldown:
                    # Skip weapon events during cooldown
                    continue
                    
                # Skip weapon inputs if death sequence is active
                if self.death_sequence_active:
                    continue
                    
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE:
                        self.weapon_manager.attack_sword()
                    elif event.key == pygame.K_e:
                        self.activate_special_attack()
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:  # Left click
                        # Get screen mouse position 
                        screen_mouse_pos = pygame.mouse.get_pos()
                        # Convert to world coordinates
                        world_mouse_pos = self.screen_to_world_coords(*screen_mouse_pos)
                        
                        # Attack with bow using the exact mouse position
                        self.weapon_manager.attack_bow(world_mouse_pos)
                    elif event.button == 3:  # Right click
                        # Trigger dodge in the movement direction
                        if self.player.dodge():
                            # Apply a small screen shake for feedback
                            self.trigger_screen_shake(amount=3, duration=5)
                            # Play dodge sound effect
                            self.sound_manager.play_sound("effects/dodge")
                
        # Ensure mouse cursor stays within window boundaries after processing all events
        if self.state == PLAYING:
            self.confine_mouse_to_window()

    def update(self):
        # Update splash screen timer
        if self.state == SPLASH_SCREEN:
            current_time = pygame.time.get_ticks()
            
            # Initialize start time if not set
            if self.splash_start_time == 0:
                self.splash_start_time = current_time
                # print(f"Splash screen started at time: {current_time}")
                # Force an immediate glitch effect at the beginning
                self.glitched_splash_image = self._apply_horizontal_glitch(self.original_splash_image)
                self.glitch_last_update = current_time
                self.splash_image = self.glitched_splash_image
                self.glitch_next_frame = True
                
            # Update glitch effect during the first 1.5 seconds
            if current_time - self.splash_start_time < self.glitch_duration:
                # Update glitch effect at regular intervals
                if current_time - self.glitch_last_update > self.glitch_update_rate:
                    # print(f"Applying glitch effect at time: {current_time - self.splash_start_time}ms")
                    self.glitched_splash_image = self._apply_horizontal_glitch(self.original_splash_image.copy())
                    self.glitch_last_update = current_time
                    self.splash_image = self.glitched_splash_image
                    self.glitch_next_frame = True
                else:
                    # Reset glitch flag to occasionally show normal image between glitches
                    if random.random() < 0.3:  # 30% chance to show normal image
                        self.glitch_next_frame = False
            else:
                if self.splash_image != self.original_splash_image:
                    #  print(f"Glitch effect ended at time: {current_time - self.splash_start_time}ms")
                    self.splash_image = self.original_splash_image
                    self.glitch_next_frame = False
            
            # Check if splash duration has passed
            if current_time - self.splash_start_time >= self.splash_duration:
                # print(f"Splash screen complete at time: {current_time - self.splash_start_time}ms")
                if self.intro_videos and len(self.intro_videos) > 0:
                    # If we have intro videos, go to intro scene
                    self.state = INTRO_SCENE
                    self.intro_start_time = pygame.time.get_ticks()
                    self.intro_current_image = 0
                    self.intro_alpha = 0  # Start with fade in
                    self.intro_fading = True
                    self.intro_fade_in = True
                    self.intro_fade_start_time = pygame.time.get_ticks()
                    print("Starting intro scene")
                    # Play intro music if available
                    self.sound_manager.play_music('intro')
                else:
                    # Otherwise go directly to menu
                    self.state = MENU
                    # print("Starting welcome screen music")
                    self.sound_manager.play_music('menu')
            return  # Skip other updates during splash screen
            
        # Update intro scene
        if self.state == INTRO_SCENE:
            current_time = pygame.time.get_ticks()
            
            # All screens are now video-based
            # Initialize video player if needed
            if self.current_video_player is None and self.intro_current_image < len(self.intro_videos):
                video_data = self.intro_videos[self.intro_current_image]
                if video_data:
                    # Import here to avoid circular imports
                    from ui import VideoPlayer
                    # For the last video (intro_06), use ping-pong mode and loop
                    is_last_video = (self.intro_current_image == 5)  # 0-based index, so 5 is the 6th video
                    loop = is_last_video
                    ping_pong = video_data.get('ping_pong', False)
                    
                    self.current_video_player = VideoPlayer(
                        video_data['path'], 
                        self.screen, 
                        loop=loop, 
                        ping_pong=ping_pong
                    )
                    print(f"Initialized video player for intro scene {self.intro_current_image + 1}" + 
                          (" (ping-pong, looping)" if ping_pong else ""))
            
            # For the last video, we continue playing in ping-pong mode until a key is pressed
            # This is handled in handle_events
            if self.intro_current_image == 5:  # Last video (0-based index)
                # Just keep the video playing in ping-pong mode
                if self.current_video_player:
                    self.current_video_player.update()
            else:
                # For other videos, check if finished playing
                if self.current_video_player and not self.current_video_player.is_playing:
                    # Move to next video
                    self.intro_current_image += 1
                    # Clean up current video player
                    if self.current_video_player:
                        self.current_video_player.stop()
                        self.current_video_player = None
            
            # Always update video player if active
            if self.current_video_player:
                self.current_video_player.update()
                    
            return  # Skip other updates during intro scene
            
        # Tell controller handler if we're in a menu or playing
        self.controller_handler.set_menu_state(self.state != PLAYING)
            
        # Only update game objects in PLAYING state
        if self.state != PLAYING:
            return
            
        # Ensure level is initialized
        if self.level is None:
            self.initialize_level()
            
        # Update particle system
        self.particle_system.update()
            
        # Handle boss introduction sequence
        if self.boss_intro_active:
            # Ensure player walking sound is stopped during boss intro
            if self.player.walk_sound_channel is not None:
                self.sound_manager.stop_sound_channel(self.player.walk_sound_channel)
                self.player.walk_sound_channel = None
                self.player.was_walking = False
                
            current_time = pygame.time.get_ticks()
            elapsed = current_time - self.boss_intro_start_time
            
            if not self.boss_intro_complete:
                # Calculate progress (0.0 to 1.0)
                progress = min(1.0, elapsed / self.boss_intro_duration)
                
                # Use easing function for smoother zoom (ease-in-out)
                if progress < 0.5:
                    # Ease in (slow start)
                    t = 2 * progress * progress
                else:
                    # Ease out (slow end)
                    t = -1 + (4 - 2 * progress) * progress
                
                # Interpolate zoom level
                new_zoom = self.boss_intro_original_zoom + (self.boss_intro_target_zoom - self.boss_intro_original_zoom) * t
                
                # Update camera zoom
                self.camera.zoom = new_zoom
                self.camera.view_width = self.camera.width / self.camera.zoom
                self.camera.view_height = self.camera.height / self.camera.zoom
                
                # Get current room and boss
                current_room = self.level.rooms[self.level.current_room_coords]
                if current_room and current_room.boss:
                    # Calculate target camera position to center on boss
                    target_x = current_room.boss.rect.centerx - (self.camera.view_width / 2)
                    target_y = current_room.boss.rect.centery - (self.camera.view_height / 2)
                    
                    # Interpolate camera position
                    if self.boss_intro_original_camera_pos:
                        self.camera.x = int(self.boss_intro_original_camera_pos[0] + 
                                          (target_x - self.boss_intro_original_camera_pos[0]) * t)
                        self.camera.y = int(self.boss_intro_original_camera_pos[1] + 
                                          (target_y - self.boss_intro_original_camera_pos[1]) * t)
                
                # Mark as complete when we reach the end
                if progress >= 1.0:
                    self.boss_intro_complete = True
            else:
                # After 2 seconds, return to player
                if elapsed >= self.boss_intro_duration + 2000:  # Wait 2 seconds after zoom
                    # Reset camera to follow player
                    self.camera.zoom = self.boss_intro_original_zoom
                    self.camera.view_width = self.camera.width / self.camera.zoom
                    self.camera.view_height = self.camera.height / self.camera.zoom
                    self.camera.center_on_point(self.player.rect.centerx, self.player.rect.centery)
                    
                    # End boss intro sequence
                    self.boss_intro_active = False
                    self.boss_intro_complete = False
                    self.boss_intro_start_time = 0
                    self.boss_intro_original_camera_pos = None
                    self.boss_intro_target_camera_pos = None
            return  # Skip normal updates during boss intro
            
        # Handle special attack if active
        if self.special_attack_active:
            # Update debug print to handle both boss and regular enemy special attacks
            if self.special_attack_data.get('is_boss_attack', False):
                print(f"Special attack active - state: {self.special_attack_data['state']}, boss attack: {self.special_attack_data['attack_count'] + 1}/{self.special_attack_data['max_attacks']}")
            else:
                print(f"Special attack active - state: {self.special_attack_data['state']}, enemy index: {self.special_attack_data['current_enemy_index']}")
            self._update_special_attack()
            # Skip normal updates when special attack is active
            return
            
        # Check if death sequence is active
        if self.death_sequence_active:
            # Update the player still to advance death animation
            self.player.update()
            
            # Handle camera zoom effect during death sequence
            current_time = pygame.time.get_ticks()
            
            # Only start the zoom effect once we've detected death
            if self.death_zoom_start_time == 0:
                self.death_zoom_start_time = current_time
                self.death_original_zoom = self.camera.zoom  # Store the current zoom level
            
            # Calculate how far through the zoom effect we are (0.0 to 1.0)
            if not self.death_zoom_complete:
                elapsed = current_time - self.death_zoom_start_time
                progress = min(elapsed / self.death_zoom_duration, 1.0)
                
                # Create blood pool particles throughout the zoom effect
                # More frequent at the beginning, less frequent towards the end
                if random.random() < 0.3 * (1 - progress/2):  # Gradually reduce frequency
                    # Create blood pool centered on player
                    pool_x = self.player.rect.centerx
                    pool_y = self.player.rect.centery
                    
                    # Vary particle size based on zoom progress (larger as we zoom in)
                    min_size = 4 + progress * 6  # Start at 4, grow to 10
                    max_size = 8 + progress * 12  # Start at 8, grow to 20
                    
                    # Create blood pool particles
                    self.particle_system.create_blood_pool(
                        pool_x, pool_y, 
                        amount=random.randint(1, 3),
                        size_range=(min_size, max_size)
                    )
                
                # Use easing function for smoother zoom (ease-in-out)
                if progress < 0.5:
                    # Ease in (slow start)
                    t = 2 * progress * progress
                else:
                    # Ease out (slow end)
                    t = -1 + (4 - 2 * progress) * progress
                
                # Interpolate zoom level
                new_zoom = self.death_original_zoom + (self.death_target_zoom - self.death_original_zoom) * t
                
                # Update camera zoom
                self.camera.zoom = new_zoom
                self.camera.view_width = self.camera.width / self.camera.zoom
                self.camera.view_height = self.camera.height / self.camera.zoom
                
                # Center camera on player
                self.camera.center_on_point(self.player.rect.centerx, self.player.rect.centery)
                
                # Mark zoom as complete when we reach the end
                if progress >= 1.0:
                    self.death_zoom_complete = True
                    
                    # Final large blood pool at the end of the zoom
                    self.particle_system.create_blood_pool(
                        self.player.rect.centerx, 
                        self.player.rect.centery,
                        amount=8,
                        size_range=(12, 25)  # Larger final pool
                    )
            
            # Check if death animation is complete and waiting for input
            if self.player.death_animation_complete:
                # Keep showing the death scene until any button is pressed
                return
            
            # Continue updating camera during death even after zoom is complete
            self.camera.center_on_point(self.player.rect.centerx, self.player.rect.centery)
            return
        
        # Update controller aim position when playing
        if self.controller_handler.connected:
            is_aiming, aim_direction = self.controller_handler.update_aim_from_right_stick(self)
            if is_aiming and self.player:
                # Update player's aim direction based on controller input
                # Fix: use update_attack_direction_from_mouse instead of non-existent set_aim_direction
                # Calculate aim position
                player_x, player_y = self.player.rect.centerx, self.player.rect.centery
                aim_x = player_x + (aim_direction[0] * 100)
                aim_y = player_y + (aim_direction[1] * 100)
                self.player.update_attack_direction_from_mouse((aim_x, aim_y))
        
        # Get mouse position and update player's attack direction
        screen_mouse_pos = pygame.mouse.get_pos()
        
        # Confine mouse to window to prevent it from disappearing
        self.confine_mouse_to_window()
        
        world_mouse_pos = self.screen_to_world_coords(*screen_mouse_pos)
        
        # Handle controller input for aiming
        is_aiming, aim_direction = self.controller_handler.update_aim_from_right_stick(self)
        if is_aiming and self.player and not self.player.is_dead:
            # Get player position in world coordinates
            player_x, player_y = self.player.rect.centerx, self.player.rect.centery
            
            # Calculate new aim position based on stick direction
            scale_factor = 100
            aim_x = player_x + (aim_direction[0] * scale_factor)
            aim_y = player_y + (aim_direction[1] * scale_factor)
            
            # Calculate angle for direction
            angle = math.degrees(math.atan2(aim_direction[1], aim_direction[0]))
            if angle < 0:
                angle += 360
                
            # Determine cardinal direction
            if (angle >= 315 or angle < 45):
                attack_dir = 'right'
            elif (angle >= 45 and angle < 135):
                attack_dir = 'down'
            elif (angle >= 135 and angle < 225):
                attack_dir = 'left'
            else:  # angle >= 225 and angle < 315
                attack_dir = 'up'
            
            # Update player's facing if not in attack animation
            if self.player.current_state != 'attack':
                self.player.facing = attack_dir
            
            # Update player's aim direction with world coordinates
            self.player.update_attack_direction_from_mouse((aim_x, aim_y))
            
        else:
            # Use mouse for aiming if not using controller right stick
            screen_mouse_pos = pygame.mouse.get_pos()
            world_mouse_pos = self.screen_to_world_coords(*screen_mouse_pos)
            if self.player and not self.player.is_dead:
                self.player.update_attack_direction_from_mouse(world_mouse_pos)
        
        # Update screen shake effect
        self.update_screen_shake()
        
        # Update player movement
        keys = pygame.key.get_pressed()
        
        # Also handle controller input directly for movement
        if self.controller_handler.connected:
            # Create a class to wrap keyboard state with controller overrides
            class KeyWrapper:
                def __init__(self, keyboard_state):
                    self.keyboard_state = keyboard_state
                    self.overrides = {}
                
                def __getitem__(self, key):
                    # Check if we have an override for this key
                    if key in self.overrides:
                        return self.overrides[key]
                    # Otherwise return the original keyboard state
                    return self.keyboard_state[key]
            
            # Create wrapper around keyboard state
            wrapped_keys = KeyWrapper(keys)
            
            try:
                # Check analog stick
                if self.controller_handler.controller.get_numaxes() > self.controller_handler.AXIS_LEFT_Y:
                    x_axis = self.controller_handler.controller.get_axis(self.controller_handler.AXIS_LEFT_X)
                    y_axis = self.controller_handler.controller.get_axis(self.controller_handler.AXIS_LEFT_Y)
                    
                    # Set movement keys based on analog stick
                    if x_axis < -self.controller_handler.DEADZONE:
                        wrapped_keys.overrides[pygame.K_a] = True
                    if x_axis > self.controller_handler.DEADZONE:
                        wrapped_keys.overrides[pygame.K_d] = True
                    if y_axis < -self.controller_handler.DEADZONE:
                        wrapped_keys.overrides[pygame.K_w] = True
                    if y_axis > self.controller_handler.DEADZONE:
                        wrapped_keys.overrides[pygame.K_s] = True
                        
                # Check D-pad (hat)
                if self.controller_handler.controller.get_numhats() > 0:
                    dpad_x, dpad_y = self.controller_handler.controller.get_hat(0)
                    
                    # D-pad values override analog stick
                    if dpad_x == -1:  # Left
                        wrapped_keys.overrides[pygame.K_a] = True
                        wrapped_keys.overrides[pygame.K_d] = False
                    elif dpad_x == 1:  # Right
                        wrapped_keys.overrides[pygame.K_d] = True
                        wrapped_keys.overrides[pygame.K_a] = False
                    
                    if dpad_y == 1:  # Up
                        wrapped_keys.overrides[pygame.K_w] = True
                        wrapped_keys.overrides[pygame.K_s] = False
                    elif dpad_y == -1:  # Down
                        wrapped_keys.overrides[pygame.K_s] = True
                        wrapped_keys.overrides[pygame.K_w] = False
                
                # Debug output for movement
                if wrapped_keys.overrides:
                    movement_keys = []
                    if wrapped_keys.overrides.get(pygame.K_w, False):
                        movement_keys.append("W")
                    if wrapped_keys.overrides.get(pygame.K_s, False):
                        movement_keys.append("S")
                    if wrapped_keys.overrides.get(pygame.K_a, False):
                        movement_keys.append("A")
                    if wrapped_keys.overrides.get(pygame.K_d, False):
                        movement_keys.append("D")
                    if movement_keys:
                        pass  # Remove the print statement that was here
                
                # Use the wrapped keys instead of the original
                keys = wrapped_keys
            except Exception as e:
                # Remove debug print for error reading controller input
                pass
        
        self.player.move(keys)
        
        # Check collision using separate X and Y axis checks to allow sliding
        # Store original position
        orig_x = self.player.rect.x
        orig_y = self.player.rect.y
        orig_hitbox_x = self.player.hitbox.x
        orig_hitbox_y = self.player.hitbox.y
        
        # First update X position and check for collision
        self.player.update_x()
        if self.level.check_collision(self.player.hitbox):
            # Collision on X axis, revert X position only
            self.player.rect.x = orig_x
            self.player.hitbox.x = orig_hitbox_x
        
        # Then update Y position and check for collision
        self.player.update_y()
        if self.level.check_collision(self.player.hitbox):
            # Collision on Y axis, revert Y position only
            self.player.rect.y = orig_y
            self.player.hitbox.y = orig_hitbox_y
            
        # Update camera to follow player
        self.camera.update(self.player.rect.centerx, self.player.rect.centery)
        
        # Check for door transitions
        try:
            door_direction, new_position = self.level.check_door_transition(self.player.hitbox)
            if door_direction and new_position:
                # Move player to new room
                self.player.rect.centerx = new_position[0]
                self.player.rect.centery = new_position[1]
                self.player.hitbox.centerx = new_position[0]
                self.player.hitbox.centery = new_position[1]
                print(f"Player moved through {door_direction} door to room at {self.level.current_room_coords}")
                
                # Clear all arrows when moving between rooms
                self.weapon_manager.clear_arrows()
                
                # Check if entering a boss room
                current_room = self.level.rooms[self.level.current_room_coords]
                if current_room.room_type == 'boss' and current_room.boss and current_room.boss.health > 0:
                    # Stop any walking sound before starting the boss intro
                    if self.player.walk_sound_channel is not None:
                        self.sound_manager.stop_sound_channel(self.player.walk_sound_channel)
                        self.player.walk_sound_channel = None
                        self.player.was_walking = False
                        
                    # Start boss introduction sequence
                    self.boss_intro_active = True
                    self.boss_intro_start_time = pygame.time.get_ticks()
                    self.boss_intro_original_zoom = self.camera.zoom
                    
                    # Make sure camera is positioned on player before starting the transition
                    self.camera.center_on_point(self.player.rect.centerx, self.player.rect.centery)
                    self.boss_intro_original_camera_pos = (self.camera.x, self.camera.y)
                    print("Starting boss introduction sequence")
                    
                    # REMOVED: No longer play level 10 boss music here. 
                    # It will be handled by play_level_appropriate_music when the game state updates.
                    # if self.current_level == 10:
                    #     self.sound_manager.play_music('level10_boss')
                    #     print("Playing level 10 boss music")
                    #     return
                
        except Exception as e:
            print(f"Error during door transition: {e}")
            
        # Update weapons
        try:
            self.weapon_manager.update()
        except Exception as e:
            print(f"Error updating weapons: {e}")
        
        # Update level and check collisions
        try:
            self.level.update(self.player)
        except Exception as e:
            print(f"Error updating level: {e}")
        
        # Check for health pickups
        try:
            health_amount = self.level.check_health_pickup(self.player.hitbox)
            if health_amount > 0:
                # Heal player with the amount returned
                self.player.heal(health_amount)
                print(f"Player healed for {health_amount} HP!")
        except Exception as e:
            print(f"Error checking health pickup: {e}")
                
        # Check for arrow pickups
        try:
            # Only check for arrow pickups if player doesn't have max arrows
            if self.player.arrow_count < self.player.max_arrows:
                arrow_amount = self.level.check_arrow_pickup(self.player.hitbox)
                if arrow_amount > 0:
                    # Add arrows to player inventory
                    arrows_added = self.player.add_arrows(arrow_amount)
                    print(f"Player picked up {arrow_amount} arrows! Now has {self.player.arrow_count}/{self.player.max_arrows} arrows.")
            else:
                # Still check if player is touching an arrow pickup, but don't collect it
                self.level.check_arrow_pickup(self.player.hitbox, check_only=True)
        except Exception as e:
            print(f"Error checking arrow pickup: {e}")
            
        # Check for weapon pickups
        try:
            weapon_type = self.level.check_weapon_pickup(self.player.hitbox)
            if weapon_type:
                if weapon_type == "fire_sword":
                    # Enable fire sword
                    self.weapon_manager.enable_fire_sword()
                    
                    # Create particles effect for pickup
                    self.particle_system.create_fire_effect(
                        self.player.rect.centerx,
                        self.player.rect.centery,
                        amount=20
                    )
                    
                    # Also trigger screen shake for epic effect
                    self.trigger_screen_shake(amount=5, duration=15)
                elif weapon_type == "lightning_sword":
                    # Enable lightning sword
                    self.weapon_manager.enable_lightning_sword()
                    
                    # Create particles effect for pickup
                    self.particle_system.create_lightning_effect(
                        self.player.rect.centerx,
                        self.player.rect.centery,
                        amount=20
                    )
                    
                    # Also trigger screen shake for epic effect
                    self.trigger_screen_shake(amount=5, duration=15)
        except Exception as e:
            print(f"Error checking weapon pickup: {e}")
        
        # Get current room for entity interactions
        current_room = self.level.rooms[self.level.current_room_coords]
        
        # Check for sword collisions with destroyable walls
        if self.weapon_manager.sword.active:
            try:
                # Get the current rotated attack hitbox
                sword_hitbox = self.player.get_attack_hitbox()
                
                # Get the current room for tile checks
                current_room = self.level.rooms[self.level.current_room_coords]
                
                # Check all nearby wall tiles that could potentially be hit by the rotated hitbox
                # Get the player's center position in tile coordinates
                center_tile_x = self.player.rect.centerx // TILE_SIZE
                center_tile_y = self.player.rect.centery // TILE_SIZE
                
                # Check a 3x3 area around the player for potentially destroyable walls
                for y_offset in range(-2, 3):
                    for x_offset in range(-2, 3):
                        # Calculate the tile coordinates
                        wall_tile_x = center_tile_x + x_offset
                        wall_tile_y = center_tile_y + y_offset
                        
                        # Skip if out of bounds
                        if (wall_tile_x < 0 or wall_tile_x >= current_room.width or
                            wall_tile_y < 0 or wall_tile_y >= current_room.height):
                            continue
                        
                        # Check if this tile is a wall
                        if current_room.tiles[wall_tile_y][wall_tile_x] == 1:
                            # Create a rect for this wall tile
                            wall_rect = pygame.Rect(
                                wall_tile_x * TILE_SIZE,
                                wall_tile_y * TILE_SIZE,
                                TILE_SIZE,
                                TILE_SIZE
                            )
                            
                            # Check if the rotated sword hitbox collides with this wall tile
                            if self.player.collide_with_rotated_hitbox(wall_rect):
                                # Try to destroy the wall
                                if self.level.try_destroy_wall(wall_tile_x, wall_tile_y):
                                    # Wall was successfully destroyed, we can break out of the loop
                                    break
                
            except Exception as e:
                print(f"Error checking sword-wall collisions: {e}")
        
        # Check for arrow collisions with destroyable walls
        arrows_to_remove = []
        try:
            for arrow in self.weapon_manager.bow.arrows:
                try:
                    # Only check collision after arrow has traveled for at least 5 frames
                    # This allows the arrow to be rendered for longer before being removed
                    if hasattr(arrow, 'frames_alive'):
                        arrow.frames_alive += 1
                    else:
                        arrow.frames_alive = 1
                    
                    # Skip collision check for the first 5 frames to allow the arrow to be visible
                    if arrow.frames_alive <= 5:
                        continue
                        
                    # Get the tile at the arrow's position
                    arrow_tile_x = arrow.rect.centerx // TILE_SIZE
                    arrow_tile_y = arrow.rect.centery // TILE_SIZE
                    
                    # Check if the arrow hit ANY wall, not just destroyable walls
                    if (0 <= arrow_tile_y < current_room.height and 
                        0 <= arrow_tile_x < current_room.width and 
                        current_room.tiles[arrow_tile_y][arrow_tile_x] == 1):  # Any wall tile
                        
                        # Mark the arrow for removal
                        arrows_to_remove.append(arrow)
                        
                        # Try to destroy the wall (if it's destroyable)
                        if self.level.try_destroy_wall(arrow_tile_x, arrow_tile_y):
                            pass # Wall was destroyed
                except Exception as e:
                    print(f"Error processing arrow-wall collision: {e}")
                    arrows_to_remove.append(arrow)
        except Exception as e:
            print(f"Error checking arrow-wall collisions: {e}")
            
        # Remove arrows that hit walls
        if arrows_to_remove:
            for arrow in arrows_to_remove:
                try:
                    self.weapon_manager.bow.remove_arrow(arrow)
                except Exception as e:
                    print(f"Error removing arrow after wall collision: {e}")
                
        # Check enemy collisions with weapons
        try:
            # Get the current attack hitbox
            sword_hitbox = None
            if self.weapon_manager.sword.active:
                # Get the hitbox without triggering an attack
                sword_hitbox = self.player.get_attack_hitbox()
                
                # Create lightning effect on sword swing if using lightning sword
                if self.weapon_manager.has_lightning_sword:
                    # Get the position at the end of the sword in the attack direction
                    if self.player.facing == 'right':
                        effect_x = self.player.rect.right + TILE_SIZE // 4  # Closer to player (was TILE_SIZE // 2)
                        effect_y = self.player.rect.centery
                    elif self.player.facing == 'left':
                        effect_x = self.player.rect.left - TILE_SIZE // 4  # Closer to player
                        effect_y = self.player.rect.centery
                    elif self.player.facing == 'up':
                        effect_x = self.player.rect.centerx
                        effect_y = self.player.rect.top - TILE_SIZE // 4  # Closer to player
                    else:  # down
                        effect_x = self.player.rect.centerx
                        effect_y = self.player.rect.bottom + TILE_SIZE // 4  # Closer to player
                        
                    # Create the lightning effect at this position, passing player's facing direction
                    # to ensure lightning goes in the correct direction
                    if hasattr(self.player, 'attack_angle'):
                        # Use exact attack angle if available
                        angle = math.radians(self.player.attack_angle)
                        
                        # Calculate multiple positions around the attack arc
                        # Use the attack box to determine locations for lightning particles
                        num_positions = 2  # Reduced from 3 to 2 for better performance
                        lightning_positions = []
                        
                        for i in range(num_positions):
                            # Calculate position with angle variation to spread lightning around attack arc
                            offset_angle = angle
                            if i == 1:
                                offset_angle = angle - random.uniform(0.05, 0.1)  # Smaller offset for tighter grouping
                                
                            # Use different distances from player for each lightning source
                            distance = TILE_SIZE * random.uniform(0.5, 0.7)  # Reduced distance variation
                            pos_x = self.player.rect.centerx + math.cos(offset_angle) * distance
                            pos_y = self.player.rect.centery + math.sin(offset_angle) * distance
                            
                            lightning_positions.append((pos_x, pos_y, angle))  # Store position and original angle
                        
                        # Create lightning effects at multiple positions
                        for pos_x, pos_y, beam_angle in lightning_positions:
                            self.particle_system.create_directional_lightning(
                                pos_x, 
                                pos_y,
                                angle=beam_angle,
                                amount=2  # Reduced from 3 to 2 per position
                            )
                    else:
                        # Fallback to 4-directional angles
                        if self.player.facing == 'right':
                            angle = 0  # 0 radians = right
                        elif self.player.facing == 'left':
                            angle = math.pi  # π radians = left
                        elif self.player.facing == 'up':
                            angle = -math.pi/2  # -π/2 radians = up
                        else:  # down
                            angle = math.pi/2  # π/2 radians = down
                            
                        # Create lightning effect with specific angle at a single position
                        self.particle_system.create_directional_lightning(
                            effect_x, 
                            effect_y,
                            angle=angle,
                            amount=10  # Original amount
                        )
                
                # Create fire effect on sword swing if using fire sword
                elif self.weapon_manager.has_fire_sword:
                    # Get the position at the end of the sword in the attack direction
                    if hasattr(self.player, 'attack_angle'):
                        # Calculate position based on exact attack angle
                        angle_rad = math.radians(self.player.attack_angle)
                        effect_x = self.player.rect.centerx + math.cos(angle_rad) * (TILE_SIZE // 2)
                        effect_y = self.player.rect.centery + math.sin(angle_rad) * (TILE_SIZE // 2)
                        angle = angle_rad  # Use the same angle for particle direction
                    else:
                        # Fallback to 4-directional positioning
                        if self.player.facing == 'right':
                            effect_x = self.player.rect.right + TILE_SIZE // 4
                            effect_y = self.player.rect.centery
                            angle = 0  # 0 radians = right
                        elif self.player.facing == 'left':
                            effect_x = self.player.rect.left - TILE_SIZE // 4
                            effect_y = self.player.rect.centery
                            angle = math.pi  # π radians = left
                        elif self.player.facing == 'up':
                            effect_x = self.player.rect.centerx
                            effect_y = self.player.rect.top - TILE_SIZE // 4
                            angle = -math.pi/2  # -π/2 radians = up
                        else:  # down
                            effect_x = self.player.rect.centerx
                            effect_y = self.player.rect.bottom + TILE_SIZE // 4
                            angle = math.pi/2  # π/2 radians = down
                    
                    # Create fire effect with specific angle
                    self.particle_system.create_directional_fire(
                        effect_x,
                        effect_y,
                        angle=angle,
                        amount=12
                    )

            # Process sword collisions with enemies first
            for enemy in current_room.enemies:
                # Check sword collisions using the rotated attack hitbox
                if self.weapon_manager.sword.active and sword_hitbox and not enemy.has_been_hit_this_swing:
                    # Use the new collision detection with rotated hitbox
                    collision_detected = self.player.collide_with_rotated_hitbox(enemy.rect)
                    
                    if collision_detected:
                        # Check line of sight between player and enemy before applying damage
                        # Use the enemy's existing line of sight check function
                        has_line_of_sight = enemy.check_line_of_sight(
                            self.player.rect.centerx, self.player.rect.centery,
                            enemy.rect.centerx, enemy.rect.centery,
                            self.level
                        )
                        
                        if has_line_of_sight:
                            # Apply sword damage based on sword type
                            damage = SWORD_DAMAGE
                            if self.weapon_manager.has_fire_sword:
                                damage = int(SWORD_DAMAGE * 1.5)  # 50% damage bonus
                                # Create fire particles on hit
                                self.particle_system.create_fire_effect(
                                    enemy.rect.centerx, 
                                    enemy.rect.centery,
                                    amount=5
                                )
                                # Play fire sword sound effect
                                self.sound_manager.play_sound("effects/fire_sword")
                            elif self.weapon_manager.has_lightning_sword:
                                damage = int(SWORD_DAMAGE * 1.8)  # 80% damage bonus
                                # Create additional lightning particles at enemy position on hit
                                self.particle_system.create_lightning_effect(
                                    enemy.rect.centerx, 
                                    enemy.rect.centery,
                                    amount=8
                                )
                                # Play lightning sword sound effect
                                self.sound_manager.play_sound("effects/lightning_sword")
                            
                            # Apply damage and check if enemy was killed
                            if enemy.take_damage(damage):
                                # Enemy was killed, increment kill counter
                                self.kill_counter += 1
                                print(f"Enemy killed! Kill counter: {self.kill_counter}/{self.kill_counter_max}")
                                
                            enemy.has_been_hit_this_swing = True  # Mark as hit for this swing
                        else:
                            # Wall is in the way, show a small particle effect to indicate blocked attack
                            self.particle_system.create_particle(
                                enemy.rect.centerx, 
                                enemy.rect.centery,
                                color=(150, 150, 150),  # Gray particles for blocked attack
                                size=3,
                                velocity=(random.uniform(-0.5, 0.5), random.uniform(-0.5, 0.5)),
                                lifetime=10
                            )
                    # Note: Removed the else clause here that was showing the blocked attack effect for enemies out of range

            # Now process arrow collisions with enemies (separate from sword logic)
            arrows_to_remove = []
            for arrow in self.weapon_manager.bow.arrows:
                for enemy in current_room.enemies:
                    try:
                        if arrow.rect.colliderect(enemy.rect):
                            # Apply damage and check if enemy was killed
                            if enemy.take_damage(BOW_DAMAGE):
                                # Enemy was killed, increment kill counter
                                self.kill_counter += 1
                                print(f"Enemy killed with arrow! Kill counter: {self.kill_counter}/{self.kill_counter_max}")
                                
                            arrows_to_remove.append(arrow)
                            break  # Break inner loop once arrow hits an enemy
                    except Exception as e:
                        print(f"Error checking arrow-enemy collision: {e}")
                        arrows_to_remove.append(arrow)
                        break  # Break inner loop if error
            
            # Remove arrows that hit enemies
            for arrow in arrows_to_remove:
                try:
                    self.weapon_manager.bow.remove_arrow(arrow)
                except Exception as e:
                    print(f"Error removing arrow after enemy collision: {e}")
                    
        except Exception as e:
            print(f"Error checking enemy collisions: {e}")
                
        # Check boss collisions with weapons
        try:
            # Check for sword collisions with boss
            if current_room.boss and current_room.boss.health > 0:
                if self.weapon_manager.sword.active and sword_hitbox and not current_room.boss.has_been_hit_this_swing:
                    # Use the new collision detection with rotated hitbox
                    collision_detected = self.player.collide_with_rotated_hitbox(current_room.boss.damage_hitbox)
                    
                    if collision_detected:
                        # Check line of sight between player and boss before applying damage
                        has_line_of_sight = current_room.boss.check_line_of_sight(
                            self.player.rect.centerx, self.player.rect.centery,
                            current_room.boss.rect.centerx, current_room.boss.rect.centery,
                            self.level
                        )
                        
                        if has_line_of_sight:
                            # Apply sword damage based on sword type
                            damage = SWORD_DAMAGE
                            if self.weapon_manager.has_fire_sword:
                                damage = int(SWORD_DAMAGE * 1.5)  # 50% damage bonus
                                # Create fire particles on hit
                                self.particle_system.create_fire_effect(
                                    current_room.boss.rect.centerx, 
                                    current_room.boss.rect.centery,
                                    amount=10
                                )
                                # Play fire sword sound effect
                                self.sound_manager.play_sound("effects/fire_sword")
                            elif self.weapon_manager.has_lightning_sword:
                                damage = int(SWORD_DAMAGE * 1.8)  # 80% damage bonus
                                # Create lightning particles on hit
                                self.particle_system.create_lightning_effect(
                                    current_room.boss.rect.centerx, 
                                    current_room.boss.rect.centery,
                                    amount=12
                                )
                                # Play lightning sword sound effect
                                self.sound_manager.play_sound("effects/lightning_sword")
                            current_room.boss.take_damage(damage)
                            current_room.boss.has_been_hit_this_swing = True  # Mark as hit for this swing
                            
                            # Check if damage was reflected by level 4 boss in defensive mode
                            if hasattr(current_room.boss, 'reflected_damage') and current_room.boss.reflected_damage > 0:
                                reflected = current_room.boss.reflected_damage
                                # Add debug logging
                                print(f"Processing reflected damage: {reflected}, boss defensive mode: {getattr(current_room.boss, 'defensive_mode', False)}")
                                
                                # Apply reflected damage to player
                                self.player.take_damage(reflected)
                                
                                # Different reflection effects based on boss level
                                if hasattr(current_room.boss, 'level') and current_room.boss.level == 7:
                                    # Purple reflection particles for level 7 boss
                                    particle_color = (150, 50, 255)
                                    self.display_message(f"Shield reflected {int(reflected)} damage!", particle_color)
                                else:
                                    # Blue reflection particles for level 4 boss
                                    particle_color = (0, 100, 255)
                                    self.display_message(f"Boss reflected {int(reflected)} damage!", particle_color)
                                    
                                # Create visual effect to show damage reflection
                                self.particle_system.create_particle(
                                    current_room.boss.rect.centerx, 
                                    current_room.boss.rect.centery,
                                    color=particle_color,
                                    size=random.randint(4, 8),
                                    velocity=(random.uniform(-0.5, 0.5), random.uniform(-0.5, 0.5)),
                                    lifetime=random.randint(20, 30)
                                )
                                
                                # Reset reflected damage
                                current_room.boss.reflected_damage = 0
                        else:
                            # Wall is in the way, show a small particle effect to indicate blocked attack
                            self.particle_system.create_particle(
                                current_room.boss.rect.centerx, 
                                current_room.boss.rect.centery,
                                color=(150, 150, 150),  # Gray particles for blocked attack
                                size=3,
                                velocity=(random.uniform(-0.5, 0.5), random.uniform(-0.5, 0.5)),
                                lifetime=10
                            )
                    # Note: Removed the else clause here that was showing the blocked attack effect for bosses out of range

            # NEW CODE - Check for sword collisions with summoned bosses from Dark Lord (level 10 boss)
            if current_room.boss and hasattr(current_room.boss, 'summoned_bosses'):
                # Iterate over all summoned bosses
                for summoned_boss in current_room.boss.summoned_bosses:
                    if summoned_boss.health > 0 and hasattr(summoned_boss, 'damage_hitbox'):
                        if self.weapon_manager.sword.active and sword_hitbox and not summoned_boss.has_been_hit_this_swing:
                            # Use the new collision detection with rotated hitbox
                            collision_detected = self.player.collide_with_rotated_hitbox(summoned_boss.damage_hitbox)
                            
                            if collision_detected:
                                # Check line of sight
                                has_line_of_sight = summoned_boss.check_line_of_sight(
                                    self.player.rect.centerx, self.player.rect.centery,
                                    summoned_boss.rect.centerx, summoned_boss.rect.centery,
                                    self.level
                                )
                                
                                if has_line_of_sight:
                                    print(f"SWORD HIT SUMMONED BOSS! Health before: {summoned_boss.health}")
                                    # Apply sword damage based on sword type
                                    damage = SWORD_DAMAGE
                                    if self.weapon_manager.has_fire_sword:
                                        damage = int(SWORD_DAMAGE * 1.5)  # 50% damage bonus
                                        # Create fire particles on hit
                                        self.particle_system.create_fire_effect(
                                            summoned_boss.rect.centerx, 
                                            summoned_boss.rect.centery,
                                            amount=10
                                        )
                                        # Play fire sword sound effect
                                        self.sound_manager.play_sound("effects/fire_sword")
                                    elif self.weapon_manager.has_lightning_sword:
                                        damage = int(SWORD_DAMAGE * 1.8)  # 80% damage bonus
                                        # Create lightning particles on hit
                                        self.particle_system.create_lightning_effect(
                                            summoned_boss.rect.centerx, 
                                            summoned_boss.rect.centery,
                                            amount=12
                                        )
                                        # Play lightning sword sound effect
                                        self.sound_manager.play_sound("effects/lightning_sword")
                                        
                                    # Apply damage
                                    summoned_boss.take_damage(damage)
                                    summoned_boss.has_been_hit_this_swing = True
                                    print(f"Applied {damage} damage. Health after: {summoned_boss.health}")
                                    
                                    # Check if damage was reflected by the summoned boss in defensive mode
                                    if hasattr(summoned_boss, 'reflected_damage') and summoned_boss.reflected_damage > 0:
                                        reflected = summoned_boss.reflected_damage
                                        print(f"Summoned boss reflected sword damage: {reflected}")
                                        
                                        # Apply reflected damage to player
                                        self.player.take_damage(reflected)
                                        
                                        # Different reflection effects based on boss level
                                        if hasattr(summoned_boss, 'level') and summoned_boss.level == 7:
                                            particle_color = (150, 50, 255)  # Purple for level 7
                                            self.display_message(f"Shield reflected {int(reflected)} damage!", particle_color)
                                        else:
                                            particle_color = (0, 100, 255)  # Blue for level 4
                                            self.display_message(f"Boss reflected {int(reflected)} damage!", particle_color)
                                        
                                        # Create visual effect to show damage reflection
                                        self.particle_system.create_particle(
                                            summoned_boss.rect.centerx, 
                                            summoned_boss.rect.centery,
                                            color=particle_color,
                                            size=random.randint(4, 8),
                                            velocity=(random.uniform(-0.5, 0.5), random.uniform(-0.5, 0.5)),
                                            lifetime=random.randint(20, 30)
                                        )
                                        
                                        # Reset reflected damage
                                        summoned_boss.reflected_damage = 0
            
            # Check for arrow collisions with boss (completely separate logic)
            if current_room.boss and current_room.boss.health > 0:
                arrows_to_remove = []
                for arrow in self.weapon_manager.bow.arrows:
                    try:
                        # Debug output to help trace collisions
                        print(f"Checking arrow collision with boss: arrow at ({arrow.rect.x}, {arrow.rect.y}), boss at ({current_room.boss.rect.x}, {current_room.boss.rect.y})")
                        print(f"Arrow rect: {arrow.rect}, Boss damage hitbox: {current_room.boss.damage_hitbox}")
                        
                        if arrow.rect.colliderect(current_room.boss.damage_hitbox):
                            print(f"ARROW HIT BOSS! Applying {BOW_DAMAGE} damage")
                            current_room.boss.take_damage(BOW_DAMAGE)
                            
                            # Check if damage was reflected
                            if hasattr(current_room.boss, 'reflected_damage') and current_room.boss.reflected_damage > 0:
                                reflected = current_room.boss.reflected_damage
                                print(f"Boss reflected arrow damage: {reflected}")
                                
                                # Apply reflected damage to player
                                self.player.take_damage(reflected)
                                
                                # Different reflection effects based on boss level
                                if hasattr(current_room.boss, 'level') and current_room.boss.level == 7:
                                    particle_color = (150, 50, 255)  # Purple for level 7
                                    self.display_message(f"Shield reflected {int(reflected)} damage!", particle_color)
                                else:
                                    particle_color = (0, 100, 255)  # Blue for level 4
                                    self.display_message(f"Boss reflected {int(reflected)} damage!", particle_color)
                                
                                # Create visual effect
                                self.particle_system.create_particle(
                                    current_room.boss.rect.centerx, 
                                    current_room.boss.rect.centery,
                                    color=particle_color,
                                    size=random.randint(4, 8),
                                    velocity=(random.uniform(-0.5, 0.5), random.uniform(-0.5, 0.5)),
                                    lifetime=random.randint(20, 30)
                                )
                                
                                # Reset reflected damage
                                current_room.boss.reflected_damage = 0
                            
                            # Mark arrow for removal
                            arrows_to_remove.append(arrow)
                    except Exception as e:
                        print(f"Error checking arrow-boss collision: {e}")
                        arrows_to_remove.append(arrow)
                
                # NEW CODE - Check for arrow collisions with summoned bosses from Dark Lord
                if hasattr(current_room.boss, 'summoned_bosses'):
                    for summoned_boss in current_room.boss.summoned_bosses:
                        if summoned_boss.health > 0 and hasattr(summoned_boss, 'damage_hitbox'):
                            for arrow in self.weapon_manager.bow.arrows:
                                if arrow not in arrows_to_remove and arrow.rect.colliderect(summoned_boss.damage_hitbox):
                                    print(f"ARROW HIT SUMMONED BOSS! Health before: {summoned_boss.health}")
                                    summoned_boss.take_damage(BOW_DAMAGE)
                                    print(f"Applied {BOW_DAMAGE} damage. Health after: {summoned_boss.health}")
                                    
                                    # Check if damage was reflected by the summoned boss in defensive mode
                                    if hasattr(summoned_boss, 'reflected_damage') and summoned_boss.reflected_damage > 0:
                                        reflected = summoned_boss.reflected_damage
                                        print(f"Summoned boss reflected arrow damage: {reflected}")
                                        
                                        # Apply reflected damage to player
                                        self.player.take_damage(reflected)
                                        
                                        # Different reflection effects based on boss level
                                        if hasattr(summoned_boss, 'level') and summoned_boss.level == 7:
                                            particle_color = (150, 50, 255)  # Purple for level 7
                                            self.display_message(f"Shield reflected {int(reflected)} damage!", particle_color)
                                        else:
                                            particle_color = (0, 100, 255)  # Blue for level 4
                                            self.display_message(f"Boss reflected {int(reflected)} damage!", particle_color)
                                        
                                        # Create visual effect
                                        self.particle_system.create_particle(
                                            summoned_boss.rect.centerx, 
                                            summoned_boss.rect.centery,
                                            color=particle_color,
                                            size=random.randint(4, 8),
                                            velocity=(random.uniform(-0.5, 0.5), random.uniform(-0.5, 0.5)),
                                            lifetime=random.randint(20, 30)
                                        )
                                        
                                        # Reset reflected damage
                                        summoned_boss.reflected_damage = 0
                                    
                                    arrows_to_remove.append(arrow)
                
                # Remove arrows that hit the boss
                for arrow in arrows_to_remove:
                    try:
                        self.weapon_manager.bow.remove_arrow(arrow)
                    except Exception as e:
                        print(f"Error removing arrow after boss collision: {e}")
        except Exception as e:
            print(f"Error checking boss collisions: {e}")
            
        # Reset hit tracking if sword is not active anymore
        if not self.weapon_manager.sword.active:
            for enemy in current_room.enemies:
                enemy.has_been_hit_this_swing = False
            if current_room.boss:
                current_room.boss.has_been_hit_this_swing = False
                # Reset hit tracking for summoned bosses
                if hasattr(current_room.boss, 'summoned_bosses'):
                    for summoned_boss in current_room.boss.summoned_bosses:
                        if hasattr(summoned_boss, 'has_been_hit_this_swing'):
                            summoned_boss.has_been_hit_this_swing = False

        # Check if level is completed
        if self.level.completed:
            self.current_level += 1
            if self.current_level > self.max_levels:
                self.state = VICTORY
                # Play victory music when player wins
                self.sound_manager.play_music('victory')
            else:
                # Clear any existing arrows before changing levels
                self.weapon_manager.clear_arrows()
                
                # Change music based on level
                self.play_level_appropriate_music()
                
                self.level = Level(self.current_level)
                # Give the level access to the particle system and game instance
                self.level.particle_system = self.particle_system
                self.level.game = self
                
                # Place player on a valid floor tile in the new level
                player_x, player_y = self.level.get_valid_player_start_position()
                self.player.rect.centerx = player_x
                self.player.rect.centery = player_y
                # Set player's level reference
                self.player.level = self.level
                
                # Show level notification
                self.level.show_notification(f"Level {self.current_level}", (255, 255, 0), 3000)
        
        # Check if player died
        if self.player.is_dead and not self.death_sequence_active:
            # Start death sequence instead of immediately showing game over
            self.death_sequence_active = True
            self.death_zoom_start_time = 0  # Will be set in the next update
            self.death_zoom_complete = False
            print("Player died - starting death sequence")
            # We'll show the game over screen after death animation completes
        
        # Process delayed screen shake requests
        current_time = pygame.time.get_ticks()
        due_requests = [req for req in self.shake_requests if current_time >= req['trigger_at']]
        for req in due_requests:
            self.trigger_screen_shake(req['amount'], req['duration'])
        self.shake_requests = [req for req in self.shake_requests if current_time < req['trigger_at']]

        # Update screen shake effect
        self.update_screen_shake()

    def render(self):
        # Clear screen first
        self.screen.fill(BLACK)
        
        # Draw based on current game state
        if self.state == SPLASH_SCREEN:
            # Simple splash screen with generated logo
            if self.splash_start_time == 0:
                self.splash_start_time = pygame.time.get_ticks()
            
            # Skip splash screen after 3 seconds
            current_time = pygame.time.get_ticks()
            if current_time - self.splash_start_time > self.splash_duration:
                print("Splash screen timed out, transitioning to menu")
                if self.intro_images and len(self.intro_images) > 0:
                    # If we have intro images, go to intro scene
                    self.state = INTRO_SCENE
                    self.intro_start_time = pygame.time.get_ticks()
                    self.intro_current_image = 0
                    self.intro_alpha = 0  # Start with fade in
                    self.intro_fading = True
                    self.intro_fade_in = True
                    self.intro_fade_start_time = pygame.time.get_ticks()
                    print("Starting intro scene")
                    # Play intro music if available
                    self.sound_manager.play_music('intro')
                else:
                    # Otherwise go directly to menu
                    self.state = MENU
                    # Start welcome screen music after splash screen
                    self.sound_manager.play_music('menu')
                    
            # Render the splash screen
            if self.glitch_next_frame:
                # Show a glitched version of the splash screen
                self.screen.blit(self.glitched_splash_image, (0, 0))
            else:
                # Show the normal splash screen
                self.screen.blit(self.original_splash_image, (0, 0))
        elif self.state == INTRO_SCENE:
            # All screens now use videos
            if self.current_video_player:
                # Draw the video frame
                self.current_video_player.draw()
                
                # Get the subtitle for this screen
                if self.intro_current_image < len(self.intro_subtitles):
                    # Create subtitle font with smaller size
                    font_path = os.path.join(ASSET_PATH, "fonts/PixelatedEleganceRegular-ovyAA.ttf")
                    if os.path.exists(font_path):
                        subtitle_font = pygame.font.Font(font_path, 22)
                    else:
                        subtitle_font = pygame.font.Font(None, 22)
                    
                    # Get the lines of text
                    subtitle_lines = self.intro_subtitles[self.intro_current_image]
                    num_lines = len(subtitle_lines)
                    
                    # Calculate total height for all lines with spacing
                    line_height = subtitle_font.get_height()
                    line_spacing = 8  # 8px spacing between lines
                    total_height = (line_height * num_lines) + (line_spacing * (num_lines - 1))
                    
                    # Find the widest line to determine background width
                    line_surfaces = []
                    max_width = 0
                    
                    for line in subtitle_lines:
                        line_surface = subtitle_font.render(line, True, (255, 255, 255))
                        line_surfaces.append(line_surface)
                        max_width = max(max_width, line_surface.get_width())
                    
                    # Position subtitle at bottom of screen with some padding
                    subtitle_x = (WINDOW_WIDTH - max_width) // 2
                    subtitle_base_y = WINDOW_HEIGHT - total_height - (70 if num_lines > 2 else 60)
                    
                    # Add a semi-transparent background for better readability
                    bg_rect = pygame.Rect(
                        subtitle_x - 20, 
                        subtitle_base_y - 10, 
                        max_width + 40, 
                        total_height + 20
                    )
                    bg_surface = pygame.Surface((bg_rect.width, bg_rect.height), pygame.SRCALPHA)
                    bg_surface.fill((0, 0, 0, 150))  # Semi-transparent black background
                    self.screen.blit(bg_surface, (bg_rect.x, bg_rect.y))
                    
                    # Draw each line of the subtitle
                    for i, line_surface in enumerate(line_surfaces):
                        line_x = (WINDOW_WIDTH - line_surface.get_width()) // 2
                        line_y = subtitle_base_y + (i * (line_height + line_spacing))
                        self.screen.blit(line_surface, (line_x, line_y))
                
                    # Add skip text for videos 1-5, and "press any key to continue" for video 6
                    font = pygame.font.Font(None, 24)
                    if self.intro_current_image < 5:  # Not the last video
                        skip_text = font.render("Press any key to skip...", True, (200, 200, 200))
                    else:
                        # For the last video, show "Press any key to continue..." instead
                        skip_text = font.render("Press any key to continue...", True, (255, 255, 255))
                    
                    self.screen.blit(skip_text, (WINDOW_WIDTH - skip_text.get_width() - 20, WINDOW_HEIGHT - 40))
            
        elif self.state == MENU:
            if self.menu.showing_controls:
                self.menu.draw_controls_menu()
            elif self.menu.showing_options:
                self.menu.draw_options_menu()
            elif self.menu.showing_audio:
                self.menu.draw_audio_menu()
            elif self.menu.showing_artworks:
                self.menu.draw_artworks_menu()
            else:
                self.menu.draw_main_menu()
        elif self.state == PLAYING:
            self.render_game()
        elif self.state == PAUSED:
            self.render_game()  # Draw game state in background
            if self.menu.showing_controls:
                self.menu.draw_controls_menu()
            elif self.menu.showing_options:
                self.menu.draw_options_menu()
            elif self.menu.showing_audio:
                self.menu.draw_audio_menu()
            else:
                self.menu.draw_pause_menu()
        elif self.state == GAME_OVER:
            self.menu.draw_game_over()
        elif self.state == VICTORY:
            self.menu.draw_victory()
            
        # Draw some debug info in development
        if DEBUG_MODE:
            font = pygame.font.Font(None, 24)
            state_text = font.render(f"Game State: {self.state}", True, WHITE)
            self.screen.blit(state_text, (10, 10))
            
            # Show mouse position for debugging
            mouse_pos = pygame.mouse.get_pos()
            mouse_text = font.render(f"Mouse: {mouse_pos}", True, WHITE)
            self.screen.blit(mouse_text, (10, 30))
        
        # Actually update the display
        pygame.display.flip()
        
        # Ensure mouse stays within window boundaries at all times
        self.confine_mouse_to_window()
        
    def render_game(self):
        # Create a temporary surface for the zoomed room rendering
        room_width = ROOM_WIDTH * TILE_SIZE
        room_height = ROOM_HEIGHT * TILE_SIZE
        room_surface = pygame.Surface((room_width, room_height))
        room_surface.fill(BLACK)
        
        # Draw level to room surface (except exit confirmation dialog and key notification)
        if self.level:
            # Store the current state of the exit confirmation
            show_confirmation = self.level.show_exit_confirmation
            # Temporarily disable exit confirmation to avoid drawing it on the room surface
            self.level.show_exit_confirmation = False
            
            # Store if we have a key pickup notification
            has_key_notification = hasattr(self.level, 'key_pickup_time')
            key_pickup_time = getattr(self.level, 'key_pickup_time', 0)
            
            # Temporarily remove key pickup notification if it exists
            if has_key_notification:
                delattr(self.level, 'key_pickup_time')
                
            # Draw level (without confirmation dialog or key notification)
            self.level.draw(room_surface)
            
            # Restore the original states
            self.level.show_exit_confirmation = show_confirmation
            if has_key_notification:
                self.level.key_pickup_time = key_pickup_time
        
        # Special handling for death sequence to ensure blood pools are drawn underneath the player
        if self.death_sequence_active:
            # First draw only the blood pool particles (underneath the player)
            self.particle_system.draw_blood_pools_only(room_surface, (0, 0))
            
            # Then draw the player
            self.player.draw(room_surface)
            
            # Then draw all other particles (on top of player)
            self.particle_system.draw_except_blood_pools(room_surface, (0, 0))
        else:
            # Normal rendering order when player is alive
            # Draw player to room surface
            self.player.draw(room_surface)
            
            # Draw special attack trail if active
            if self.special_attack_active and self.special_attack_trail_positions:
                player_image = self.player.image.copy()  # Use current player image
                
                # Calculate the max alpha value (make it more visible than dodge trail)
                max_alpha = 160  # Higher than dodge trail's 128
                
                # Calculate alpha for each trail position (newer positions are more opaque)
                for i, pos in enumerate(self.special_attack_trail_positions):
                    # Calculate progress (0 to 1) with newer positions having higher values
                    progress = i / len(self.special_attack_trail_positions)
                    
                    # Calculate alpha (quadratic falloff for faster fading)
                    alpha = int(max_alpha * (progress ** 2))
                    
                    # Create a copy with adjusted alpha
                    ghost_image = player_image.copy()
                    
                    # Apply custom alpha
                    ghost_image.fill((255, 150, 0, alpha), None, pygame.BLEND_RGBA_MULT)  # Yellow-orange tint
                    
                    # Draw ghost at stored position
                    ghost_rect = ghost_image.get_rect(center=pos)
                    room_surface.blit(ghost_image, ghost_rect)
            
            # Draw particles
            self.particle_system.draw(room_surface, (0, 0))
        
        # Draw weapons (EXCEPT arrows, which we'll draw last)
        if self.weapon_manager.sword.active:
            self.weapon_manager.weapon_sprites.draw(room_surface)

        # Get the view rect (visible portion of room)
        view_rect = pygame.Rect(
            int(self.camera.x),
            int(self.camera.y),
            int(self.camera.view_width), 
            int(self.camera.view_height)
        )
        # Ensure view_rect is within bounds of room_surface
        if view_rect.left < 0:
            view_rect.left = 0
        if view_rect.top < 0:
            view_rect.top = 0
        if view_rect.right > room_width:
            view_rect.width = room_width - view_rect.left
        if view_rect.bottom > room_height:
            view_rect.height = room_height - view_rect.top
            
        # Make sure view_rect has valid dimensions
        if view_rect.width <= 0:
            view_rect.width = 1
        if view_rect.height <= 0:
            view_rect.height = 1
            
        # One final safety check
        if (view_rect.right > room_width or 
            view_rect.bottom > room_height or 
            view_rect.left < 0 or 
            view_rect.top < 0):
            print(f"Warning: Invalid view_rect: {view_rect}, room size: {room_width}x{room_height}")
            view_rect = pygame.Rect(0, 0, min(room_width, 100), min(room_height, 100))
        
        try:
            # Scale and blit the visible portion to the screen
            visible_portion = room_surface.subsurface(view_rect)
            scaled_portion = pygame.transform.scale(
                visible_portion, 
                (WINDOW_WIDTH, WINDOW_HEIGHT)
            )
            
            # Apply screen shake offset when drawing the game world
            shake_x, shake_y = self.shake_offset
            self.screen.blit(scaled_portion, (shake_x, shake_y))
        except ValueError as e:
            print(f"Error creating subsurface: {e}")
            print(f"View rect: {view_rect}, Room surface: {room_surface.get_size()}")
            # Fall back to drawing the entire room surface scaled down
            try:
                scaled_portion = pygame.transform.scale(
                    room_surface, 
                    (WINDOW_WIDTH, WINDOW_HEIGHT)
                )
                # Apply screen shake to fallback rendering too
                shake_x, shake_y = self.shake_offset
                self.screen.blit(scaled_portion, (shake_x, shake_y))
            except Exception as e2:
                print(f"Fatal error during fallback rendering: {e2}")
                # Last resort - just fill the screen with a solid color
                self.screen.fill((0, 0, 0))
        except Exception as ex:
            print(f"Unexpected error during rendering: {ex}")
            # Last resort - just fill the screen with a solid color
            self.screen.fill((0, 0, 0))
        
        # Create lighting effect - dark overlay with circular light around player
        if self.torch_enabled:
            light_effect = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
            light_effect.fill((0, 0, 0, self.darkness_level))  # Semi-transparent black overlay
            
            # Calculate torch position based on current camera view
            
            # During boss intro, we need to use the camera's current position for the light
            if self.boss_intro_active:
                # Get the screen center (where the torch should be during intro)
                screen_center_x = WINDOW_WIDTH // 2
                screen_center_y = WINDOW_HEIGHT // 2
                
                # Use screen center for torch position during intro
                torch_screen_x = screen_center_x
                torch_screen_y = screen_center_y
            else:
                # Normal gameplay - light follows player
                # Get player's world position
                player_world_x = self.player.rect.centerx
                player_world_y = self.player.rect.centery
                
                # Calculate relative position to camera
                rel_x = player_world_x - self.camera.x
                rel_y = player_world_y - self.camera.y
                
                # Scale by zoom factor
                torch_screen_x = rel_x * self.camera.zoom
                torch_screen_y = rel_y * self.camera.zoom
            
            # Ensure coordinates are integers for drawing
            torch_screen_x = int(torch_screen_x)
            torch_screen_y = int(torch_screen_y)
            
            # Inner fully lit area (radius where light is 100%)
            fully_lit_radius = 80
            
            # Maximum radius of the torch light
            max_radius = self.torch_radius
            
            # Very small step size for smoother gradient
            step_size = 2
            
            # Draw from maximum radius inward
            for radius in range(max_radius, 0, -step_size):
                # Calculate normalized distance (0.0 at center, 1.0 at max radius)
                normalized_distance = radius / max_radius
                
                # Use a smooth curve for alpha (darkness) calculation
                # This is a sigmoidal-like curve that creates a more natural falloff
                if radius <= fully_lit_radius:
                    # Inside fully lit radius - completely transparent
                    alpha = 0
                else:
                    # Calculate how far we are from fully lit radius (as a percentage from 0.0 to 1.0)
                    t = (radius - fully_lit_radius) / (max_radius - fully_lit_radius)
                    
                    # Apply a cubic ease-in function for natural light falloff
                    # This creates a very smooth transition that starts slow and accelerates
                    falloff = t * t * t
                    
                    # Apply falloff to darkness level
                    alpha = int(self.darkness_level * falloff)
                
                # Draw the circle with calculated alpha
                pygame.draw.circle(light_effect, (0, 0, 0, alpha), (torch_screen_x, torch_screen_y), radius)
            
            # Apply the lighting effect
            self.screen.blit(light_effect, (0, 0))
        
        # Draw arrows LAST to ensure they're on top - draw directly to screen with camera transformation
        arrow_count = len(self.weapon_manager.bow.arrows)
        
        # Instead of just drawing all arrows, we'll manually draw each one with camera transformation
        for arrow in self.weapon_manager.bow.arrows:
            # Convert arrow position to screen coordinates
            screen_x, screen_y = self.camera.apply_pos(arrow.x, arrow.y)
            # Store original position
            orig_x, orig_y = arrow.x, arrow.y
            # Temporarily update arrow position for drawing
            arrow.x, arrow.y = screen_x, screen_y
            # Scale up the arrow size for drawing
            orig_size = arrow.size
            arrow.size = arrow.size * self.camera.zoom
            # Draw the arrow
            arrow.draw(self.screen)
            # Restore original position and size
            arrow.x, arrow.y = orig_x, orig_y
            arrow.size = orig_size
        
        # Draw the UI elements
        try:
            if self.level and self.hud:
                current_room = self.level.rooms.get(self.level.current_room_coords)
                boss_health = current_room.boss.health if current_room and hasattr(current_room, 'boss') and current_room.boss else None
                boss_max_health = current_room.boss.max_health if current_room and hasattr(current_room, 'boss') and current_room.boss else None
                has_key = hasattr(self.level, 'has_key') and self.level.has_key
                has_fire_sword = self.weapon_manager.has_fire_sword
                has_lightning_sword = self.weapon_manager.has_lightning_sword
                
                # Draw the UI with all relevant information
                self.hud.draw(
                    self.player,
                    self.current_level,
                    self.sound_manager.audio_available,
                    self.level,
                    boss_health,
                    boss_max_health,
                    has_key,
                    has_fire_sword,
                    has_lightning_sword
                )
        except Exception as e:
            print(f"Error drawing UI: {e}")
        
        # Draw "Press any button to continue" message when death animation is complete
        if self.death_sequence_active and self.player.death_animation_complete:
            # Only show the message after zoom is complete and a brief delay
            current_time = pygame.time.get_ticks()
            if self.death_zoom_complete and current_time - self.player.death_time > 2500:  # 2.5 seconds
                # Create a message with a pulsing effect
                try:
                    # Try to use the pixelated font
                    font_path = os.path.join(ASSET_PATH, "fonts/PixelatedEleganceRegular-ovyAA.ttf")
                    font = pygame.font.Font(font_path, 32)
                except:
                    # Fall back to default font
                    font = pygame.font.Font(None, 36)
                    
                # Create pulsing effect
                pulse = 0.5 + 0.5 * abs(math.sin(pygame.time.get_ticks() / 500))
                
                # Create a semi-transparent background for better readability
                overlay = pygame.Surface((WINDOW_WIDTH, 80), pygame.SRCALPHA)
                overlay.fill((0, 0, 0, 180))  # Semi-transparent black
                self.screen.blit(overlay, (0, WINDOW_HEIGHT // 2 - 40))
                
                # Draw the message
                text_color = (255, 255, 255)
                message = font.render("Press any button to continue", True, text_color)
                rect = message.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2))
                
                # Add shadow for better readability
                shadow = font.render("Press any button to continue", True, (0, 0, 0))
                shadow_rect = rect.copy()
                shadow_rect.x += 2
                shadow_rect.y += 2
                self.screen.blit(shadow, shadow_rect)
                
                # Apply pulse effect by scaling alpha
                alpha_surface = pygame.Surface(message.get_size(), pygame.SRCALPHA)
                alpha_surface.fill((255, 255, 255, int(255 * pulse)))
                message.blit(alpha_surface, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
                
                self.screen.blit(message, rect)
        
        # Draw key pickup notification directly on the screen
        if self.level and hasattr(self.level, 'key_pickup_time'):
            time_since_pickup = pygame.time.get_ticks() - self.level.key_pickup_time
            if time_since_pickup < 3000:  # Show for 3 seconds
                try:
                    font_path = os.path.join(ASSET_PATH, "fonts/PixelatedEleganceRegular-ovyAA.ttf")
                    font = pygame.font.Font(font_path, 22)  # Smaller font for better visibility
                except:
                    font = pygame.font.Font(None, 24)  # Fallback to system font
                
                # Create a notification with smaller text
                notification = font.render("KEY COLLECTED! Find the exit.", True, (255, 255, 0))
                
                # Create a background for better visibility
                padding = 10
                bg_rect = notification.get_rect()
                bg_rect.width += padding * 2
                bg_rect.height += padding * 2
                
                # Position at the top of the screen
                bg_rect.centerx = WINDOW_WIDTH // 2
                bg_rect.top = 20
                
                # Draw semi-transparent dark background with rounded corners
                bg_surface = pygame.Surface((bg_rect.width, bg_rect.height), pygame.SRCALPHA)
                pygame.draw.rect(bg_surface, (0, 0, 0, 180), pygame.Rect(0, 0, bg_rect.width, bg_rect.height), 0, 8)
                # Add a subtle border
                pygame.draw.rect(bg_surface, (255, 215, 0, 150), pygame.Rect(0, 0, bg_rect.width, bg_rect.height), 2, 8)
                self.screen.blit(bg_surface, bg_rect)
                
                # Apply pulsing effect
                pulse = abs(math.sin(time_since_pickup / 300))
                # Vary the color slightly for the pulse effect
                color = (255, 255, 0) if pulse > 0.5 else (255, 215, 0)
                notification = font.render("KEY COLLECTED! Find the exit.", True, color)
                
                # Draw text centered on the background
                notification_rect = notification.get_rect(center=bg_rect.center)
                self.screen.blit(notification, notification_rect)
        
        # Draw exit confirmation dialog last, directly on the screen (not affected by camera)
        if self.level and self.level.show_exit_confirmation:
            self.level.draw_exit_confirmation(self.screen)
        
        # Render HUD
        # Check for missing attributes in Level object and provide defaults
        has_key = False
        has_fire_sword = False 
        has_lightning_sword = False
        
        if self.level:
            has_key = getattr(self.level, 'has_key', False)
            has_fire_sword = getattr(self.level, 'has_fire_sword', False)
            has_lightning_sword = getattr(self.level, 'has_lightning_sword', False)
        
        # Get boss health if available
        boss_health = None
        boss_max_health = None
        
        if self.level and hasattr(self.level, 'rooms') and hasattr(self.level, 'current_room_coords'):
            current_room = self.level.rooms.get(self.level.current_room_coords)
            if current_room and hasattr(current_room, 'boss') and current_room.boss:
                boss_health = current_room.boss.health
                boss_max_health = current_room.boss.max_health
        
        self.hud.render(
            self.player.health,
            self.player.max_health,
            self.player.arrow_count,
            self.player.max_arrows,
            self.kill_counter,
            self.kill_counter_max,
            self.current_level,
            self.level,
            boss_health,
            boss_max_health,
            has_key=has_key,
            has_fire_sword=has_fire_sword,
            has_lightning_sword=has_lightning_sword
        )
        
        # Display controller status if debug mode is on
        if DEBUG_HITBOXES:
            controller_status = "Controller: Connected" if self.controller_handler.get_controller_status() else "Controller: Not Connected"
            controller_text = self.debug_font.render(controller_status, True, WHITE)
            self.screen.blit(controller_text, (10, WINDOW_HEIGHT - 30))
        
    def run(self):
        print("Starting game loop")
        self.splash_start_time = pygame.time.get_ticks()  # Initialize splash timer at the start
        
        # Play splash sound at the beginning if we're in splash screen mode
        if self.state == SPLASH_SCREEN:
            try:
                # Use absolute path for splash sound
                splash_path = os.path.join(ASSET_PATH, "sounds", "effects", "splash.mp3")
                print(f"Attempting to play splash sound from: {splash_path}")
                print(f"File exists: {os.path.exists(splash_path)}")
                
                if os.path.exists(splash_path):
                    try:
                        print(f"Loading splash sound...")
                        splash_sound = pygame.mixer.Sound(splash_path)
                        print(f"Splash sound loaded successfully, playing now...")
                        splash_sound.play()
                        print(f"Splash sound played successfully")
                    except Exception as e:
                        print(f"Error loading or playing splash sound: {e}")
                else:
                    print(f"Splash sound file not found at: {splash_path}")
            except Exception as e:
                print(f"Error with splash sound (outer try/catch): {e}")
                
        # Pre-load the intro music if it exists
        try:
            # Check if intro music file exists directly in the sounds directory
            intro_music_path = os.path.join(ASSET_PATH, "sounds", "Intro.mp3")  # Note: Updated to use exact filename with capital I
            if not os.path.exists(intro_music_path):
                # Try lowercase name
                intro_music_path = os.path.join(ASSET_PATH, "sounds", "intro.mp3")
            if not os.path.exists(intro_music_path):
                # Try .ogg format if mp3 doesn't exist
                intro_music_path = os.path.join(ASSET_PATH, "sounds", "intro.ogg")
            
            if os.path.exists(intro_music_path):
                print(f"Intro music found at: {intro_music_path}")
                # Add the intro music to the sound manager's music tracks dictionary
                self.sound_manager.music_tracks['intro'] = intro_music_path
                print(f"Added intro music to sound manager: {intro_music_path}")
            else:
                print(f"No intro music found, will use menu music for intro scene")
        except Exception as e:
            print(f"Error checking for intro music: {e}")
                
        while self.running:
            self.handle_events()
            self.update()
            self.render()
            self.clock.tick(FPS)
            
        # Clean up resources before quitting
        if hasattr(self, 'menu') and self.menu:
            self.menu.cleanup()
            
        pygame.quit()
        sys.exit()

    def toggle_fullscreen(self):
        """Toggle between fullscreen and windowed mode"""
        global WINDOW_WIDTH, WINDOW_HEIGHT
        
        # Toggle fullscreen flag
        self.fullscreen = not self.fullscreen
        
        try:
            print(f"Attempting to switch to {'fullscreen' if self.fullscreen else 'windowed'} mode")
            
            # Detect Linux platform for special handling
            is_linux = 'linux' in sys.platform
            if is_linux:
                print("Linux platform detected, using special fullscreen handling")
            
            if self.fullscreen:
                # Save current window size for later
                self.windowed_size = (WINDOW_WIDTH, WINDOW_HEIGHT)
                print(f"Saved windowed size: {self.windowed_size}")
                
                # Get display info
                display_info = pygame.display.Info()
                new_width = display_info.current_w
                new_height = display_info.current_h
                
                print(f"Switching to fullscreen: {new_width}x{new_height}")
                
                # Use different flags for Linux to properly scale content
                if is_linux:
                    # For Linux, use SCALED flag to ensure proper content scaling
                    self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT), 
                                                        pygame.FULLSCREEN | pygame.SCALED)
                    # Note: We keep WINDOW_WIDTH and WINDOW_HEIGHT at their original values
                    # since the SCALED flag will handle the scaling properly
                else:
                    # For Windows/Mac, use the standard approach
                    WINDOW_WIDTH = new_width
                    WINDOW_HEIGHT = new_height
                    self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT), 
                                                        pygame.FULLSCREEN | pygame.HWSURFACE | pygame.DOUBLEBUF)
                
                pygame.display.flip()  # Ensure display is updated
                
            else:
                # Restore windowed mode with saved dimensions
                WINDOW_WIDTH, WINDOW_HEIGHT = self.windowed_size
                print(f"Returning to windowed mode: {WINDOW_WIDTH}x{WINDOW_HEIGHT}")
                
                self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
                pygame.display.flip()  # Ensure display is updated
            
            # Always reset the camera after changing modes
            print(f"Resetting camera for dimensions: {WINDOW_WIDTH}x{WINDOW_HEIGHT}")
            self.camera.width = WINDOW_WIDTH
            self.camera.height = WINDOW_HEIGHT
            self.camera.view_width = WINDOW_WIDTH / self.camera.zoom
            self.camera.view_height = WINDOW_HEIGHT / self.camera.zoom
            
            # Force camera update to center on player
            if self.player:
                player_x = self.player.rect.centerx
                player_y = self.player.rect.centery
                print(f"Centering camera on player at {player_x}, {player_y}")
                self.camera.center_on_point(player_x, player_y)
            else:
                print("No player to center on, resetting camera to origin")
                self.camera.x = 0
                self.camera.y = 0
                
            # Recreate menu to ensure it matches the new screen size
            self.menu = Menu(self.screen)
            
            # Update fullscreen button text in all menus
            # Make sure we only update Button objects, not strings or other items
            fullscreen_text = "Fullscreen: On" if self.fullscreen else "Fullscreen: Off"
            for button in self.menu.buttons:
                if hasattr(button, 'text') and isinstance(button.text, str) and button.text.startswith("Fullscreen:"):
                    button.text = fullscreen_text
            
            print(f"Mode switch complete. Current mode: {'Fullscreen' if self.fullscreen else 'Windowed'}")
            return True
            
        except Exception as e:
            print(f"Error during screen mode toggle: {e}")
            # Try to recover by reverting to a safe state
            self.fullscreen = not self.fullscreen  # Revert flag
            
            try:
                # Try to set a safe fallback resolution
                WINDOW_WIDTH, WINDOW_HEIGHT = 800, 600
                self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
                
                # Reset camera for fallback dimensions
                self.camera.width = WINDOW_WIDTH
                self.camera.height = WINDOW_HEIGHT
                self.camera.view_width = WINDOW_WIDTH / self.camera.zoom
                self.camera.view_height = WINDOW_HEIGHT / self.camera.zoom
                
                if self.player:
                    self.camera.center_on_point(self.player.rect.centerx, self.player.rect.centery)
                
                # Recreate menu
                self.menu = Menu(self.screen)
                
                print("Recovered to fallback window mode after error")
            except Exception as e2:
                print(f"Critical error during recovery: {e2}")
                
            return False
            
    def trigger_screen_shake(self, amount=8, duration=10):
        """Trigger a screen shake effect"""
        # Ensure amount is an integer to avoid TypeError in random.randint
        self.shake_amount = int(amount)
        self.shake_duration = int(duration)
        
    def update_screen_shake(self):
        """Update the screen shake effect"""
        if self.shake_duration > 0:
            self.shake_duration -= 1
            self.shake_offset = [
                random.randint(-self.shake_amount, self.shake_amount),
                random.randint(-self.shake_amount, self.shake_amount)
            ]
        else:
            self.shake_offset = [0, 0]

    def play_level_appropriate_music(self):
        """Helper method to play the appropriate music for the current level"""
        # Check if player is in a level 10 boss room
        if self.current_level == 10 and hasattr(self, 'level') and self.level:
            current_room = self.level.rooms.get(self.level.current_room_coords)
            if current_room and current_room.room_type == 'boss':
                self.sound_manager.play_music('level10_boss')
                print(f"Playing level 10 boss music in boss room")
                return
                
        # Regular level music based on level number
        if self.current_level >= 3 and self.current_level <= 4:
            self.sound_manager.play_music('level3')
            print(f"Playing level 3-4 music for level {self.current_level}")
        elif self.current_level >= 5 and self.current_level <= 6:
            self.sound_manager.play_music('level5')
            print(f"Playing level 5-6 music for level {self.current_level}")
        elif self.current_level >= 7 and self.current_level <= 8:
            self.sound_manager.play_music('level7')
            print(f"Playing level 7-8 music for level {self.current_level}")
        elif self.current_level == 9:
            self.sound_manager.play_music('level9')
            print(f"Playing level 9 music for level {self.current_level}")
        elif self.current_level == 10:
            self.sound_manager.play_music('level10')
            print(f"Playing dedicated level 10 music for final level")
        else:
            self.sound_manager.play_music('game')
            print(f"Playing standard game music for level {self.current_level}")

    def play_artwork_music(self, level_num):
        """Play the music appropriate for the selected level in the artworks menu"""
        if level_num == 1 or level_num == 2:
            self.sound_manager.play_music('game')
            print(f"Playing standard game music for level {level_num} artwork")
        elif level_num == 3 or level_num == 4:
            self.sound_manager.play_music('level3')
            print(f"Playing level 3-4 music for level {level_num} artwork")
        elif level_num == 5 or level_num == 6:
            self.sound_manager.play_music('level5')
            print(f"Playing level 5-6 music for level {level_num} artwork")
        elif level_num == 7 or level_num == 8:
            self.sound_manager.play_music('level7')
            print(f"Playing level 7-8 music for level {level_num} artwork")
        elif level_num == 9:
            self.sound_manager.play_music('level9')
            print(f"Playing level 9 music for level {level_num} artwork")
        elif level_num == 10:
            self.sound_manager.play_music('level10')
            print(f"Playing level 10 music for level {level_num} artwork")
        else:
            # Default fallback
            self.sound_manager.play_music('game')
            print(f"Playing default game music for unknown level {level_num}")

    def warp_to_level(self, level_number):
        """DEVELOPMENT FEATURE: Warps the player to the specified level"""
        if level_number < 1 or level_number > 10:
            print(f"Invalid level number: {level_number}")
            return
            
        print(f"Warping to level {level_number}")
        self.current_level = level_number
        
        # Create new level
        self.level = Level(self.current_level)
        
        # Give the level access to the particle system and game instance
        self.level.particle_system = self.particle_system
        self.level.game = self
        
        # Get valid player position
        player_x, player_y = self.level.get_valid_player_start_position()
        
        # Reset player position
        self.player.rect.centerx = player_x
        self.player.rect.centery = player_y
        self.player.level = self.level
        
        # Reset relevant game state
        self.death_sequence_active = False
        self.weapon_manager.clear_arrows()
        self.particle_system = ParticleSystem()
        
        # Update music for the new level
        self.play_level_appropriate_music()
        
        # Show level notification
        self.level.show_notification(f"Level {self.current_level}", (255, 255, 0), 3000)

    def new_game(self):
        """Start a new game"""
        print("Starting new game...")
        self.state = PLAYING
        self.current_level = 1
        
        # Create first level
        self.level = Level(self.current_level)
        
        # Give the level access to the particle system and game instance
        self.level.particle_system = self.particle_system
        self.level.game = self
        
        # Reset death sequence flags
        self.death_sequence_active = False
        self.death_message_shown = False
        self.death_zoom_complete = False
        self.death_zoom_start_time = 0
        self.death_zoom_duration = 3000  # 3 seconds for zoom effect
        self.death_original_zoom = 2.0  # Store original zoom level
        self.death_target_zoom = 4.0  # Target zoom level for death sequence
        
        # Reset special ability counter
        self.kill_counter = 0
        print(f"Special ability counter reset: {self.kill_counter}/{self.kill_counter_max}")
        
        # Reset camera zoom to default value
        self.camera.zoom = 2.0  # Reset to default zoom
        self.camera.view_width = self.camera.width / self.camera.zoom
        self.camera.view_height = self.camera.height / self.camera.zoom
        print(f"Camera zoom reset to default: {self.camera.zoom}x")
        
        # Reset particle system
        self.particle_system = ParticleSystem()
        
        # Play level-appropriate music
        self.play_level_appropriate_music()
        
        # Place player on a valid floor tile in the new level
        player_x, player_y = self.level.get_valid_player_start_position()
        self.player.rect.centerx = player_x
        self.player.rect.centery = player_y
        
        # Print debug info
        print(f"Game initialized. State: {self.state}")
        print(f"Screen size: {WINDOW_WIDTH}x{WINDOW_HEIGHT}")
        print(f"Camera zoom: {self.camera.zoom}x")

    def activate_special_attack(self):
        """Activate the special attack"""
        # Check if player is near an interactable object (prioritize interaction)
        if self.level and hasattr(self.level, 'is_near_interactable') and self.level.is_near_interactable(self.player):
            # Let the interaction happen instead of special attack
            return
            
        # Check if kill counter has reached maximum
        if self.kill_counter < self.kill_counter_max:
            # Not enough kills for special attack
            remaining = self.kill_counter_max - self.kill_counter
            print(f"Special attack not ready: {self.kill_counter}/{self.kill_counter_max} kills")
            return
            
        # Check if there are enemies to attack
        current_room = self.level.rooms[self.level.current_room_coords]
        visible_enemies = [enemy for enemy in current_room.enemies.sprites() if enemy.health > 0]
        
        # Check if there's a boss to attack
        boss = None
        if hasattr(current_room, 'boss') and current_room.boss and current_room.boss.health > 0:
            boss = current_room.boss
            
            # Special case for Dark Lord boss - Don't allow special attack on him during phases 1-4
            if hasattr(boss, 'name') and boss.name == "Dark Lord" and hasattr(boss, 'phase'):
                if boss.phase < 5:
                    # Instead, target any summoned bosses if available
                    if hasattr(boss, 'summoned_bosses') and boss.summoned_bosses:
                        # Replace the boss with one of the summoned bosses
                        boss = boss.summoned_bosses.sprites()[0]  # Target the first summoned boss
                    else:
                        print("Cannot use special attack on the Dark Lord during summoning phases")
                        return
        
        if not visible_enemies and not boss:
            print("No enemies or boss in range for special attack")
            return
            
        # Store original player position for return after attack
        original_pos = (self.player.rect.centerx, self.player.rect.centery)
        
        # Store original camera zoom
        original_zoom = self.camera.zoom
        
        # Zoom out by 30%
        new_zoom = original_zoom * 0.7  # 30% zoom out
        self.camera.zoom = new_zoom
        self.camera.view_width = self.camera.width / self.camera.zoom
        self.camera.view_height = self.camera.height / self.camera.zoom
        print(f"Camera zoomed out to {self.camera.zoom:.2f}x for special attack")
        
        # Initialize special attack data with different behavior for boss
        if boss:
            # For boss, we attack 3 times from different angles
            self.special_attack_data = {
                'state': 'init',
                'boss': boss,
                'attack_count': 0,
                'max_attacks': 3,
                'original_player_pos': original_pos,
                'original_camera_zoom': original_zoom,
                'start_time': pygame.time.get_ticks(),
                'transition_time': 500,  # 500ms for each transition
                'damage': 100,  # Damage per boss hit (reduced from 100)
                'is_boss_attack': True
            }
            print(f"Special attack activated targeting boss")
        else:
            # Regular enemy special attack
            self.special_attack_data = {
                'state': 'init',
                'enemies': visible_enemies,
                'current_enemy_index': 0,
                'original_player_pos': original_pos,
                'original_camera_zoom': original_zoom,
                'start_time': pygame.time.get_ticks(),
                'transition_time': 500,  # 500ms for each enemy transition
                'damage': 100,  # Damage per enemy hit (reduced from 100)
                'is_boss_attack': False
            }
            print(f"Special attack activated targeting {len(visible_enemies)} enemies")
        
        # Activate special attack
        self.special_attack_active = True
        
        # Play special attack sound
        self.sound_manager.play_sound("effects/sword_attack")  # Replace with special sound when available
        
    def _update_special_attack(self):
        """Update special attack animation and effects"""
        if not self.special_attack_active or not self.special_attack_data:
            return
            
        current_time = pygame.time.get_ticks()
        data = self.special_attack_data
        
        # Handle boss special attack differently
        if data.get('is_boss_attack', False):
            boss = data['boss']
            
            # Handle different states of the boss special attack
            if data['state'] == 'init':
                # Just started, set up first attack position
                if boss.health > 0:
                    # Calculate first attack angle (above the boss)
                    angle = random.uniform(0, 2 * math.pi)  # Random first angle
                    distance = TILE_SIZE * 2  # Distance from boss
                    target_x = boss.rect.centerx + math.cos(angle) * distance
                    target_y = boss.rect.centery + math.sin(angle) * distance
                    
                    data['state'] = 'moving'
                    data['target_pos'] = (target_x, target_y)
                    data['move_start_time'] = current_time
                    data['current_angle'] = angle
                    # Play dodge sound when starting to move to a new position
                    self.sound_manager.play_sound("effects/dodge")
                    print(f"Moving to boss attack position 1/{data['max_attacks']}")
                else:
                    # Boss already defeated
                    self._finish_special_attack()
                    
            elif data['state'] == 'moving':
                # Moving to attack position
                elapsed = current_time - data['move_start_time']
                
                if elapsed >= data['transition_time']:
                    # Arrived at position, now attack the boss
                    data['state'] = 'attacking'
                    data['attack_start_time'] = current_time
                    print(f"Attacking boss - hit {data['attack_count'] + 1}")
                else:
                    # Update player position during movement
                    progress = min(1.0, elapsed / data['transition_time'])
                    
                    # Get start position
                    if data['attack_count'] == 0:
                        # First attack, start from original position
                        start_pos = data['original_player_pos']
                    else:
                        # After first attack, start from previous attack position
                        prev_angle = data['current_angle'] - (2 * math.pi / 3)  # 120° back
                        prev_distance = TILE_SIZE * 2
                        start_pos = (
                            boss.rect.centerx + math.cos(prev_angle) * prev_distance,
                            boss.rect.centery + math.sin(prev_angle) * prev_distance
                        )
                        
                    # Interpolate position
                    self.player.rect.centerx = int(start_pos[0] + (data['target_pos'][0] - start_pos[0]) * progress)
                    self.player.rect.centery = int(start_pos[1] + (data['target_pos'][1] - start_pos[1]) * progress)
                    
                    # Track positions for trail effect
                    if 'last_trail_time' not in data or current_time - data['last_trail_time'] > 30:
                        self.special_attack_trail_positions.append((self.player.rect.centerx, self.player.rect.centery))
                        if len(self.special_attack_trail_positions) > 10:
                            self.special_attack_trail_positions.pop(0)
                        data['last_trail_time'] = current_time
                    
            elif data['state'] == 'attacking':
                # Check if attack animation should be complete
                elapsed = current_time - data['attack_start_time']
                
                if elapsed >= 300:  # 300ms for attack animation
                    # Attack complete, damage the boss
                    if boss.health > 0:
                        # Apply damage to the boss
                        boss.take_damage(data['damage'])
                        
                        # Create blood particles for damage visualization
                        self.particle_system.create_blood_splash(
                            boss.rect.centerx, boss.rect.centery,
                            amount=max(8, int(data['damage'] * 0.5))
                        )
                        
                        # Apply screen shake for impact feedback
                        self.trigger_screen_shake(amount=5, duration=10)
                        
                        # Play hit sound
                        self.sound_manager.play_sound("effects/enemy_hit")
                        
                        # Increment attack count
                        data['attack_count'] += 1
                        
                        if data['attack_count'] < data['max_attacks']:
                            # Move to next attack position (120° rotated)
                            angle = data['current_angle'] + (2 * math.pi / 3)  # 120° rotation
                            distance = TILE_SIZE * 2
                            target_x = boss.rect.centerx + math.cos(angle) * distance
                            target_y = boss.rect.centery + math.sin(angle) * distance
                            
                            data['state'] = 'moving'
                            data['target_pos'] = (target_x, target_y)
                            data['move_start_time'] = current_time
                            data['current_angle'] = angle
                            # Play dodge sound when moving to another attack position
                            self.sound_manager.play_sound("effects/dodge")
                            print(f"Moving to boss attack position {data['attack_count'] + 1}/{data['max_attacks']}")
                        else:
                            # All attacks complete, return to original position
                            data['state'] = 'returning'
                            data['target_pos'] = data['original_player_pos']
                            data['move_start_time'] = current_time
                            # Play dodge sound when returning
                            self.sound_manager.play_sound("effects/dodge")
                            print("All boss attacks complete, returning to original position")
                    else:
                        # Boss defeated during special attack
                        data['state'] = 'returning'
                        data['target_pos'] = data['original_player_pos']
                        data['move_start_time'] = current_time
                        # Play dodge sound when returning after boss defeat
                        self.sound_manager.play_sound("effects/dodge")
                        print("Boss defeated, returning to original position")
                        
            elif data['state'] == 'returning':
                # Returning to original position
                elapsed = current_time - data['move_start_time']
                
                if elapsed >= data['transition_time']:
                    # Return complete, end special attack
                    self._finish_special_attack()
                else:
                    # Update player position during return
                    progress = min(1.0, elapsed / data['transition_time'])
                    
                    # Get start position (last attack position)
                    angle = data['current_angle']
                    distance = TILE_SIZE * 2
                    start_pos = (
                        boss.rect.centerx + math.cos(angle) * distance,
                        boss.rect.centery + math.sin(angle) * distance
                    )
                    
                    # Interpolate position
                    self.player.rect.centerx = int(start_pos[0] + (data['target_pos'][0] - start_pos[0]) * progress)
                    self.player.rect.centery = int(start_pos[1] + (data['target_pos'][1] - start_pos[1]) * progress)
                    
                    # Track positions for trail effect
                    if 'last_trail_time' not in data or current_time - data['last_trail_time'] > 30:
                        self.special_attack_trail_positions.append((self.player.rect.centerx, self.player.rect.centery))
                        if len(self.special_attack_trail_positions) > 10:
                            self.special_attack_trail_positions.pop(0)
                        data['last_trail_time'] = current_time
        else:
            # Regular enemy special attack code
            # Get references to necessary objects
            enemies = data['enemies']
            
            # Handle different states of the special attack
            if data['state'] == 'init':
                # Just started, initiate movement to first enemy
                if enemies:
                    data['state'] = 'moving'
                    data['target_pos'] = (enemies[0].rect.centerx, enemies[0].rect.centery)
                    data['move_start_time'] = current_time
                    # Play dodge sound when starting to move to first enemy
                    self.sound_manager.play_sound("effects/dodge")
                    print(f"Moving to enemy 1/{len(enemies)}")
                else:
                    # No enemies to attack, finish
                    self._finish_special_attack()
                    
            elif data['state'] == 'moving':
                # Moving to next enemy
                elapsed = current_time - data['move_start_time']
                
                if elapsed >= data['transition_time']:
                    # Arrived at enemy, damage it
                    enemy_idx = data['current_enemy_index']
                    if enemy_idx < len(enemies):
                        enemy = enemies[enemy_idx]
                        
                        # Apply damage to the enemy
                        if enemy.take_damage(data['damage']):
                            # Enemy was killed during special attack
                            # We don't increment the kill counter for special attack kills
                            print("Enemy killed during special attack")
                        
                        # Create blood particles for damage visualization
                        self.particle_system.create_blood_splash(
                            enemy.rect.centerx, enemy.rect.centery,
                            amount=max(5, int(data['damage'] * 0.5))
                        )
                        
                        # Apply screen shake for impact feedback
                        self.trigger_screen_shake(amount=5, duration=10)
                        
                        # Play hit sound
                        self.sound_manager.play_sound("effects/enemy_hit")
                        
                        # Prepare for next enemy or finish
                        data['current_enemy_index'] += 1
                        if data['current_enemy_index'] < len(enemies):
                            # Move to next enemy
                            next_enemy = enemies[data['current_enemy_index']]
                            data['target_pos'] = (next_enemy.rect.centerx, next_enemy.rect.centery)
                            data['move_start_time'] = current_time
                            data['state'] = 'moving'
                            # Play dodge sound when moving to next enemy
                            self.sound_manager.play_sound("effects/dodge")
                            print(f"Moving to enemy {data['current_enemy_index']+1}/{len(enemies)}")
                        else:
                            # All enemies damaged, return to original position
                            data['target_pos'] = data['original_player_pos']
                            data['move_start_time'] = current_time
                            data['state'] = 'returning'
                            # Play dodge sound when returning after hitting all enemies
                            self.sound_manager.play_sound("effects/dodge")
                            print("All enemies hit, returning to original position")
                else:
                    # Update player position during movement (visually only)
                    current_enemy_idx = data['current_enemy_index']
                    
                    # If moving to an enemy (not returning), set player position
                    if current_enemy_idx < len(enemies):
                        progress = min(1.0, elapsed / data['transition_time'])
                        
                        # Calculate interpolation between current position and target
                        if data['state'] == 'moving':
                            # Get start position (either original or previous enemy)
                            if current_enemy_idx == 0:
                                start_pos = data['original_player_pos']
                            else:
                                prev_enemy = enemies[current_enemy_idx - 1]
                                start_pos = (prev_enemy.rect.centerx, prev_enemy.rect.centery)
                                
                            # Interpolate position
                            self.player.rect.centerx = int(start_pos[0] + (data['target_pos'][0] - start_pos[0]) * progress)
                            self.player.rect.centery = int(start_pos[1] + (data['target_pos'][1] - start_pos[1]) * progress)
                            
                            # Track positions for trail effect - store every few frames
                            # We create more points than dodge for a longer trail
                            if 'last_trail_time' not in data or current_time - data['last_trail_time'] > 30:  # Save position every 30ms
                                # Add current position to trail
                                self.special_attack_trail_positions.append((self.player.rect.centerx, self.player.rect.centery))
                                
                                # Keep only the last 10 positions (longer than dodge's 4)
                                if len(self.special_attack_trail_positions) > 10:
                                    self.special_attack_trail_positions.pop(0)
                                
                                # Update last trail time
                                data['last_trail_time'] = current_time
                    
            elif data['state'] == 'returning':
                # Returning to original position
                elapsed = current_time - data['move_start_time']
                
                if elapsed >= data['transition_time']:
                    # Return complete, end special attack
                    self.player.rect.centerx = data['original_player_pos'][0]
                    self.player.rect.centery = data['original_player_pos'][1]
                    self._finish_special_attack()
                else:
                    # Update player position during return
                    progress = min(1.0, elapsed / data['transition_time'])
                    
                    # Get start position (last enemy)
                    last_enemy = enemies[len(enemies) - 1]
                    start_pos = (last_enemy.rect.centerx, last_enemy.rect.centery)
                    
                    # Interpolate position
                    self.player.rect.centerx = int(start_pos[0] + (data['target_pos'][0] - start_pos[0]) * progress)
                    self.player.rect.centery = int(start_pos[1] + (data['target_pos'][1] - start_pos[1]) * progress)
        
        # Make camera follow player during special attack
        self.camera.center_on_point(self.player.rect.centerx, self.player.rect.centery)
    
    def _finish_special_attack(self):
        """Reset the special attack state"""
        if self.special_attack_data:
            # Ensure player is back at original position
            orig_pos = self.special_attack_data['original_player_pos']
            self.player.rect.centerx = orig_pos[0]
            self.player.rect.centery = orig_pos[1]
            
            # Restore original camera zoom
            orig_zoom = self.special_attack_data['original_camera_zoom']
            self.camera.zoom = orig_zoom
            self.camera.view_width = self.camera.width / self.camera.zoom
            self.camera.view_height = self.camera.height / self.camera.zoom
            print(f"Camera zoom restored to {self.camera.zoom:.2f}x after special attack")
            
            # Center camera on player's final position
            self.camera.center_on_point(self.player.rect.centerx, self.player.rect.centery)
            
        # Reset special attack state
        self.special_attack_active = False
        self.special_attack_data = None
        
        # Reset kill counter after using special attack
        self.kill_counter = 0
        print("Special attack completed - kill counter reset")

    def _start_special_attack(self, enemies):
        """Start the special attack sequence."""
        # For now, only allow if there are enemies to attack
        if not enemies:
            # There are no enemies to attack
            print("No enemies to perform special attack on")
            return

        # Activate special attack
        self.special_attack_active = True
        self.special_attack_trail_positions = []  # Reset trail positions
        
        # Set up special attack data
        original_player_pos = (self.player.rect.centerx, self.player.rect.centery)
        
        # Order enemies by distance to player
        # This creates a sequence where the player moves from one enemy to the next
        ordered_enemies = sorted(enemies, key=lambda e: math.dist(
            (self.player.rect.centerx, self.player.rect.centery), 
            (e.rect.centerx, e.rect.centery)
        ))
        
        self.special_attack_data = {
            'enemies': ordered_enemies,
            'current_enemy_idx': 0,
            'start_time': pygame.time.get_ticks(),
            'original_player_pos': original_player_pos,
            'target_pos': (ordered_enemies[0].rect.centerx, ordered_enemies[0].rect.centery),
            'state': 'moving',  # moving or attacking
            'attack_start_time': 0,
            'last_trail_time': pygame.time.get_ticks(),  # Track when we last saved a trail position
        }
        
        # Reset the kill counter
        self.kill_counter = 0
        
        # Make player temporarily invulnerable
        self.player.make_invulnerable(3000)  # 3 seconds of invulnerability during special attack
        
        # Play special attack sound
        self.sfx.play_sound('special_attack')

    def _end_special_attack(self):
        """End the special attack and return player to original position."""
        if not self.special_attack_active:
            return
            
        # Handle transition back to normal state
        self.special_attack_active = False
        self.special_attack_data = None
        
        # Clear trail positions
        self.special_attack_trail_positions = []

    def set_custom_cursor(self):
        """Load and set a custom mouse cursor"""
        try:
            cursor_path = os.path.join(ASSET_PATH, 'icons', 'mouse_cursor.png')
            cursor_image = pygame.image.load(cursor_path).convert_alpha()
            
            # Size check - resize if too large
            width, height = cursor_image.get_size()
            if width > 64 or height > 64:
                # Pygame has a size limit for cursors
                scale_factor = min(64 / width, 64 / height)
                new_width = int(width * scale_factor)
                new_height = int(height * scale_factor)
                cursor_image = pygame.transform.smoothscale(cursor_image, (new_width, new_height))
                print(f"Resized cursor from {width}x{height} to {new_width}x{new_height}")
            
            # Set the hotspot to the top-left corner of the image
            # For a typical cursor, you might want to set it to the tip of the cursor
            # For example, for an arrow pointing to the top-left, use (0, 0)
            # For an arrow pointing to the top-right, use (width, 0)
            hotspot = (0, 0)
            
            # Create a cursor from the image
            cursor = pygame.cursors.Cursor(hotspot, cursor_image)
            
            # Set the cursor
            pygame.mouse.set_cursor(cursor)
            print(f"Custom cursor set from {cursor_path}")
        except Exception as e:
            print(f"Error setting custom cursor: {e}")
            print(f"Using default cursor instead")

    def _apply_horizontal_glitch(self, image):
        """Apply horizontal glitching effect to the image"""
        if image is None:
            return None
            
        # Create a copy of the original image
        glitched = image.copy()
        
        # Apply several horizontal glitch effects
        for _ in range(10):  # Number of glitch lines
            # Choose random y position for the glitch line
            y_pos = random.randint(0, WINDOW_HEIGHT - 1)
            # Determine random height of the glitch
            glitch_height = random.randint(5, 30)
            # Determine random shift amount
            shift_amount = random.randint(10, 60)
            
            # Randomize whether to shift left or right
            if random.random() > 0.5:
                shift_amount = -shift_amount
                
            # Define the area to glitch
            glitch_area = pygame.Rect(0, y_pos, WINDOW_WIDTH, glitch_height)
            
            # Create a surface for the glitched part
            glitched_part = pygame.Surface((WINDOW_WIDTH, glitch_height))
            # Copy the slice from the original image
            glitched_part.blit(glitched, (0, 0), glitch_area)
            
            # Draw the sliced part with a horizontal shift
            glitched.blit(glitched_part, (shift_amount, y_pos))
            
            # Sometimes add color distortion (without using surfarray)
            if random.random() > 0.7:
                # Create a colorful overlay with random color and transparency
                color_rect = pygame.Surface((random.randint(50, 200), glitch_height))
                
                # Choose a random RGB color with high intensity
                r = random.randint(150, 255) if random.random() > 0.5 else 0
                g = random.randint(150, 255) if random.random() > 0.5 else 0
                b = random.randint(150, 255) if random.random() > 0.5 else 0
                
                # Fill with that color
                color_rect.fill((r, g, b))
                
                # Set alpha for partial transparency
                color_rect.set_alpha(random.randint(50, 150))
                
                # Blit onto a random position on the same line
                x_pos = random.randint(0, WINDOW_WIDTH - color_rect.get_width())
                glitched.blit(color_rect, (x_pos, y_pos))
        
        # Add occasional vertical strips
        for _ in range(3):  # Number of vertical strips
            if random.random() > 0.5:  # 50% chance for vertical strips
                # Choose random x position for the vertical strip
                x_pos = random.randint(0, WINDOW_WIDTH - 1)
                # Determine random width of the strip
                strip_width = random.randint(5, 15)
                # Choose random color
                color = (
                    random.randint(150, 255) if random.random() > 0.5 else 0,
                    random.randint(150, 255) if random.random() > 0.5 else 0,
                    random.randint(150, 255) if random.random() > 0.5 else 0
                )
                
                # Draw vertical strip
                vertical_strip = pygame.Surface((strip_width, WINDOW_HEIGHT))
                vertical_strip.fill(color)
                vertical_strip.set_alpha(random.randint(50, 150))
                glitched.blit(vertical_strip, (x_pos, 0))
        
        return glitched

    def confine_mouse_to_window(self):
        """Ensures the mouse cursor stays within the game window"""
        # Get current mouse position
        mouse_x, mouse_y = pygame.mouse.get_pos()
        
        # Create a small margin (5 pixels) from the edge to prevent cursor from disappearing
        margin = 5
        
        # Get window dimensions
        window_width = self.screen.get_width()
        window_height = self.screen.get_height()
        
        # Constrain mouse position within window boundaries with margin
        constrained_x = max(margin, min(mouse_x, window_width - margin))
        constrained_y = max(margin, min(mouse_y, window_height - margin))
        
        # Only set position if it needs to be changed
        if (mouse_x, mouse_y) != (constrained_x, constrained_y):
            pygame.mouse.set_pos((constrained_x, constrained_y))

    def request_screen_shake(self, delay, amount, duration):
        """Request a screen shake to happen after a delay."""
        current_time = pygame.time.get_ticks()
        self.shake_requests.append({
            'trigger_at': current_time + delay,
            'amount': amount,
            'duration': duration
        })

if __name__ == "__main__":
    import argparse
    
    # Set up command line arguments
    parser = argparse.ArgumentParser(description='Mud Crawler Game')
    parser.add_argument('--fullscreen', action='store_true', help='Start in fullscreen mode')
    args = parser.parse_args()
    
    print("Initializing Mud Crawler game...")
    game = Game(start_fullscreen=args.fullscreen)
    game.run() 