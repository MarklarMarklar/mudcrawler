import pygame
import os
from config import *
from asset_manager import get_asset_manager
import math
import sys
from sound_manager import get_sound_manager  # Add this import
import random

# Try to import OpenCV, but don't fail if not available
try:
    import cv2
    import numpy as np
    OPENCV_AVAILABLE = True
except ImportError:
    print("OpenCV (cv2) not available. Video playback will be disabled.")
    OPENCV_AVAILABLE = False

class Button:
    def __init__(self, x, y, width, height, text, font_size=36):
        self.asset_manager = get_asset_manager()
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        
        # Create a path to the pixelated font
        font_path = os.path.join(ASSET_PATH, "fonts/PixelatedEleganceRegular-ovyAA.ttf")
        if os.path.exists(font_path):
            self.font = pygame.font.Font(font_path, font_size)
        else:
            # Fallback to default font if the pixelated font is not available
            self.font = pygame.font.Font(None, font_size)
            print(f"Pixelated font not found, using default font: {font_path}")
        
        # Create default button textures with rounded corners
        self.normal_image = pygame.Surface((width, height), pygame.SRCALPHA)
        self.normal_image.fill((0, 0, 0, 0))  # Transparent background
        
        # Dark background with yellow border to match the screenshot
        button_color = (80, 50, 30, 230)  # Dark background
        border_color = (255, 255, 0)  # Yellow border (matches the screenshot)
        
        # Draw rounded rectangle for normal state
        self._draw_rounded_rect(self.normal_image, button_color, pygame.Rect(0, 0, width, height), 10)
        self._draw_rounded_rect(self.normal_image, border_color, pygame.Rect(0, 0, width, height), 10, 3)  # Increased border width
        
        # Hover image - lighter with brighter border
        self.hover_image = pygame.Surface((width, height), pygame.SRCALPHA)
        self.hover_image.fill((0, 0, 0, 0))  # Transparent background
        
        hover_color = (120, 70, 40, 230)  # Lighter background
        hover_border = (255, 255, 100)  # Brighter yellow
        
        # Draw rounded rectangle for hover state
        self._draw_rounded_rect(self.hover_image, hover_color, pygame.Rect(0, 0, width, height), 10)
        self._draw_rounded_rect(self.hover_image, hover_border, pygame.Rect(0, 0, width, height), 10, 3)  # Increased border width
        
        self.use_images = True
        
        # Try to load button textures if they exist (keeping original texture loading as fallback)
        try:
            normal_path = os.path.join(UI_SPRITES_PATH, "button_normal.png")
            hover_path = os.path.join(UI_SPRITES_PATH, "button_hover.png")
            
            if os.path.exists(normal_path) and os.path.exists(hover_path):
                self.normal_image = self.asset_manager.load_image(normal_path, scale=(width, height))
                self.hover_image = self.asset_manager.load_image(hover_path, scale=(width, height))
        except Exception as e:
            print(f"Failed to load button textures: {e}")
            
        self.text_color = (255, 245, 225)  # Slightly off-white for better readability
        self.is_hovered = False
        print(f"Button created: {text} at position {x}, {y} with size {width}x{height}")
    
    def _draw_rounded_rect(self, surface, color, rect, radius, border_width=0):
        """Draw a rounded rectangle on the given surface"""
        if border_width > 0:
            # This is a border, draw a slightly larger rect behind it
            rect_for_border = pygame.Rect(rect.left, rect.top, rect.width, rect.height)
            self._draw_rounded_rect(surface, color, rect_for_border, radius)
            # Now draw the inner rect with transparency to create border effect
            inner_rect = pygame.Rect(rect.left + border_width, rect.top + border_width, 
                                    rect.width - (2 * border_width), rect.height - (2 * border_width))
            self._draw_rounded_rect(surface, (0, 0, 0, 0), inner_rect, radius - border_width)
            return
            
        # Draw the main rounded rectangle
        ellipse_rect = pygame.Rect(rect.left, rect.top, radius*2, radius*2)
        pygame.draw.ellipse(surface, color, ellipse_rect)
        
        ellipse_rect.top = rect.bottom - radius*2
        pygame.draw.ellipse(surface, color, ellipse_rect)
        
        ellipse_rect.left = rect.right - radius*2
        pygame.draw.ellipse(surface, color, ellipse_rect)
        
        ellipse_rect.top = rect.top
        pygame.draw.ellipse(surface, color, ellipse_rect)
        
        # Draw the connecting rectangles
        pygame.draw.rect(surface, color, pygame.Rect(rect.left + radius, rect.top, rect.width - radius*2, rect.height))
        pygame.draw.rect(surface, color, pygame.Rect(rect.left, rect.top + radius, rect.width, rect.height - radius*2))
        
    def draw(self, surface):
        # Draw button background
        image = self.hover_image if self.is_hovered else self.normal_image
        surface.blit(image, self.rect)
        
        # Draw button text with small shadow for better readability
        text_shadow = self.font.render(self.text, True, (0, 0, 0, 180))
        text_surface = self.font.render(self.text, True, self.text_color)
        
        text_rect = text_surface.get_rect(center=self.rect.center)
        shadow_rect = text_rect.copy()
        shadow_rect.x += 2
        shadow_rect.y += 2
        
        surface.blit(text_shadow, shadow_rect)
        surface.blit(text_surface, text_rect)
        
        # Draw debug outline if DEBUG_MODE is enabled
        if DEBUG_MODE:
            # Draw a highlighted border to show the clickable area
            debug_color = (255, 255, 0) if self.is_hovered else (255, 0, 0)
            pygame.draw.rect(surface, debug_color, self.rect, 2)
        
    def handle_event(self, event):
        # Update hover state for mouse motion events
        if event.type == pygame.MOUSEMOTION:
            mouse_pos = pygame.mouse.get_pos()
            previous_hover = self.is_hovered
            self.is_hovered = self.rect.collidepoint(mouse_pos)
                    
        # Handle mouse button clicks
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # Left click
                mouse_pos = event.pos
                is_clicked = self.rect.collidepoint(mouse_pos)
                if is_clicked:
                    return True
        return False

class VideoPlayer:
    def __init__(self, video_path, screen, loop=True, ping_pong=False):
        self.video_path = video_path
        self.screen = screen
        self.loop = loop
        self.ping_pong = ping_pong
        self.playing_reverse = False
        self.is_playing = False
        
        # Skip initialization if OpenCV is not available
        if not OPENCV_AVAILABLE:
            print(f"Cannot initialize video player for {video_path}: OpenCV not available")
            return
            
        # Initialize video capture
        self.video = cv2.VideoCapture(video_path)
        if not self.video.isOpened():
            print(f"Error: Could not open video file {video_path}")
            return
            
        # Get video properties
        self.fps = self.video.get(cv2.CAP_PROP_FPS)
        self.frame_count = int(self.video.get(cv2.CAP_PROP_FRAME_COUNT))
        self.width = int(self.video.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.height = int(self.video.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
        # Scale video to fit screen
        self.target_width = WINDOW_WIDTH
        self.target_height = WINDOW_HEIGHT
        
        # Initialize playback
        self.is_playing = True
        self.current_frame = 0
        self.last_frame_time = pygame.time.get_ticks()
        self.frame_delay = 1000 / self.fps  # milliseconds between frames
        
        print(f"Initialized video player for {video_path}")
        print(f"Video size: {self.width}x{self.height}, FPS: {self.fps}, Frames: {self.frame_count}")
        
        # For ping-pong mode, we'll need to store frames
        self.frames = []
        if ping_pong:
            print(f"Ping-pong mode enabled, pre-loading frames...")
            # Pre-load all frames for ping-pong mode
            success = True
            while success:
                success, frame = self.video.read()
                if success:
                    # Store the frame
                    self.frames.append(frame)
            print(f"Loaded {len(self.frames)} frames for ping-pong mode")
            # Reset video to first frame
            self.current_frame = 0
            if self.frames:
                self.frame = self.frames[0]
                self.surface = self.convert_frame_to_surface(self.frame)
            else:
                print("Error: Could not load any frames for ping-pong mode")
                self.is_playing = False
        else:
            # Read first frame
            self.success, self.frame = self.video.read()
            if self.success:
                self.surface = self.convert_frame_to_surface(self.frame)
            else:
                print("Error: Could not read first frame")
                self.is_playing = False
    
    def convert_frame_to_surface(self, frame):
        """Convert OpenCV frame to a pygame surface"""
        if not OPENCV_AVAILABLE:
            return None
            
        # Resize frame to fit screen
        if self.width != self.target_width or self.height != self.target_height:
            frame = cv2.resize(frame, (self.target_width, self.target_height))
        
        # Convert BGR (OpenCV) to RGB (Pygame)
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Create pygame surface
        surface = pygame.surfarray.make_surface(frame.swapaxes(0, 1))
        return surface
    
    def update(self):
        """Update video frame if needed based on time"""
        if not OPENCV_AVAILABLE or not self.is_playing:
            return None
            
        current_time = pygame.time.get_ticks()
        time_elapsed = current_time - self.last_frame_time
        
        # Check if it's time to update the frame
        if time_elapsed >= self.frame_delay:
            if self.ping_pong and self.frames:
                # Ping-pong mode using stored frames
                if not self.playing_reverse:
                    # Playing forward
                    self.current_frame += 1
                    # If we reach the end, switch to reverse
                    if self.current_frame >= len(self.frames) - 1:
                        self.playing_reverse = True
                else:
                    # Playing backward
                    self.current_frame -= 1
                    # If we reach the beginning, switch to forward
                    if self.current_frame <= 0:
                        self.playing_reverse = False
                
                # Get the current frame
                self.frame = self.frames[self.current_frame]
                self.surface = self.convert_frame_to_surface(self.frame)
                self.last_frame_time = current_time
            else:
                # Standard mode: Read next frame
                self.success, self.frame = self.video.read()
                
                # If end of video, loop or stop
                if not self.success:
                    if self.loop:
                        self.video.set(cv2.CAP_PROP_POS_FRAMES, 0)
                        self.success, self.frame = self.video.read()
                        if not self.success:
                            self.is_playing = False
                            return self.surface
                    else:
                        self.is_playing = False
                        return self.surface
                
                # Convert frame to surface
                self.surface = self.convert_frame_to_surface(self.frame)
                self.current_frame += 1
                self.last_frame_time = current_time
        
        return self.surface
    
    def draw(self):
        """Draw the current frame to the screen"""
        if not OPENCV_AVAILABLE:
            return
            
        if self.is_playing and hasattr(self, 'surface') and self.surface is not None:
            self.screen.blit(self.surface, (0, 0))
    
    def stop(self):
        """Stop the video and release resources"""
        if not OPENCV_AVAILABLE:
            return
            
        self.is_playing = False
        if hasattr(self, 'video') and self.video is not None and self.video.isOpened():
            self.video.release()

class Menu:
    def __init__(self, screen):
        self.screen = screen
        
        # Get the asset manager instance
        self.asset_manager = get_asset_manager()
        
        # Initialize sound manager
        self.sound_manager = get_sound_manager()
        
        # Initialize menu state flags
        self.showing_options = False
        self.showing_controls = False
        self.showing_audio = False
        self.showing_artworks = False
        self.in_pause_menu = False
        self.in_game_over = False
        self.in_victory = False

        # Initialize cheat code tracking
        self.cheat_code_buffer = ""
        self.show_warp_dialog = False
        self.warp_level_selected = 1
        
        # Create a font for menu text
        font_path = os.path.join(ASSET_PATH, "fonts/PixelatedEleganceRegular-ovyAA.ttf")
        if os.path.exists(font_path):
            self.font = pygame.font.Font(font_path, 48)
            self.subtitle_font = pygame.font.Font(font_path, 32)
            self.instruction_font = pygame.font.Font(font_path, 24)
            self.credits_font = pygame.font.Font(font_path, 28)
            print(f"Successfully loaded pixelated font for menu")
        else:
            # Fallback to default font if the pixelated font is not available
            self.font = pygame.font.Font(None, 48)
            self.subtitle_font = pygame.font.Font(None, 32)
            self.instruction_font = pygame.font.Font(None, 24)
            self.credits_font = pygame.font.Font(None, 28)
            print(f"Pixelated font not found, using default font: {font_path}")
            
        # Audio menu variables
        self.music_volume = 0.5  # Initial music volume (0.0 to 1.0)
        self.sfx_volume = 0.7    # Initial SFX volume (0.0 to 1.0)
        self.slider_dragging = None  # Track which slider is being dragged
        self.music_slider_rect = None  # Will be set when drawing audio menu
        self.sfx_slider_rect = None   # Will be set when drawing audio menu
        
        # Create default backgrounds
        self.menu_bg = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
        self.menu_bg.fill((50, 50, 80))
        # Add some simple decoration
        for i in range(0, WINDOW_HEIGHT, 40):
            pygame.draw.line(self.menu_bg, (60, 60, 100), (0, i), (WINDOW_WIDTH, i), 1)
        for i in range(0, WINDOW_WIDTH, 40):
            pygame.draw.line(self.menu_bg, (60, 60, 100), (i, 0), (i, WINDOW_HEIGHT), 1)
            
        self.gameover_bg = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
        self.gameover_bg.fill((80, 20, 20))
        # Add some simple decoration
        for i in range(0, WINDOW_HEIGHT, 40):
            pygame.draw.line(self.gameover_bg, (100, 30, 30), (0, i), (WINDOW_WIDTH, i), 1)
            
        self.victory_bg = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
        self.victory_bg.fill((20, 80, 20))
        # Add some simple decoration
        for i in range(0, WINDOW_HEIGHT, 40):
            pygame.draw.line(self.victory_bg, (30, 100, 30), (0, i), (WINDOW_WIDTH, i), 1)
        
        # Create a placeholder title
        self.title_image = None
        self.use_title_image = False
        
        # Welcome screen image
        self.welcome_screen = None
        self.use_welcome_screen = False
        self.video_player = None  # For video welcome screen
        
        # Game over custom image
        self.gameover_custom_img = None
        self.use_gameover_custom_img = False
        
        # Custom title image from images directory
        self.custom_title = None
        self.use_custom_title = False
            
        # Try to load menu background textures if they exist
        try:
            # First try to load from UI sprites path (backwards compatibility)
            bg_path = os.path.join(UI_SPRITES_PATH, "menu_background.png")
            
            # Then try to load from assets/images folder (prioritize this one)
            new_bg_path = os.path.join(ASSET_PATH, "images", "menu_background.png")
            
            if os.path.exists(new_bg_path):
                self.menu_bg = self.asset_manager.load_image(new_bg_path, scale=(WINDOW_WIDTH, WINDOW_HEIGHT))
                print(f"Successfully loaded menu background from assets/images: {new_bg_path}")
            elif os.path.exists(bg_path):
                self.menu_bg = self.asset_manager.load_image(bg_path, scale=(WINDOW_WIDTH, WINDOW_HEIGHT))
                print(f"Successfully loaded menu background from UI sprites: {bg_path}")
        except Exception as e:
            print(f"Failed to load menu background: {e}")
            
        # Try to load game over background
        try:
            gameover_path = os.path.join(UI_SPRITES_PATH, "gameover_background.png")
            if os.path.exists(gameover_path):
                self.gameover_bg = self.asset_manager.load_image(gameover_path, scale=(WINDOW_WIDTH, WINDOW_HEIGHT))
        except Exception as e:
            print(f"Failed to load game over background: {e}")
            
        # Try to load victory background
        try:
            victory_path = os.path.join(UI_SPRITES_PATH, "victory_background.png")
            if os.path.exists(victory_path):
                self.victory_bg = self.asset_manager.load_image(victory_path, scale=(WINDOW_WIDTH, WINDOW_HEIGHT))
        except Exception as e:
            print(f"Failed to load victory background: {e}")
            
        # Try to load title image
        try:
            title_path = os.path.join(UI_SPRITES_PATH, "game_title.png")
            if os.path.exists(title_path):
                self.title_image = self.asset_manager.load_image(title_path)
                self.use_title_image = True
        except Exception as e:
            print(f"Failed to load title image: {e}")
            
        # Try to load welcome screen image or video
        try:
            # First, try to load video if it exists and OpenCV is available
            video_path = os.path.join(ASSET_PATH, "images/menu.mp4")
            if OPENCV_AVAILABLE and os.path.exists(video_path):
                self.video_player = VideoPlayer(video_path, self.screen, loop=True)
                if self.video_player.is_playing:
                    self.use_welcome_screen = True
                    print(f"Successfully loaded welcome screen video: {video_path}")
                else:
                    print(f"Failed to initialize video player, falling back to static image")
                    self.video_player = None
                    # Fall back to static image
                    self._load_static_welcome_screen()
            else:
                # OpenCV not available or video doesn't exist, fall back to static image
                self._load_static_welcome_screen()
        except Exception as e:
            print(f"Failed to load welcome screen: {e}")
            
        # Try to load custom game over image
        try:
            gameover_custom_path = os.path.join(ASSET_PATH, "images/84adca9a-3915-4957-a916-f241219bf674.png")
            if os.path.exists(gameover_custom_path):
                self.gameover_custom_img = self.asset_manager.load_image(gameover_custom_path, scale=(WINDOW_WIDTH, WINDOW_HEIGHT))
                self.use_gameover_custom_img = True
                print(f"Successfully loaded custom game over image: {gameover_custom_path}")
            else:
                print(f"Custom game over image not found: {gameover_custom_path}")
        except Exception as e:
            print(f"Failed to load custom game over image: {e}")
            
        # Try to load custom victory image
        try:
            victory_custom_path = os.path.join(ASSET_PATH, "images/victory.png")
            if os.path.exists(victory_custom_path):
                self.victory_custom_img = self.asset_manager.load_image(victory_custom_path, scale=(WINDOW_WIDTH, WINDOW_HEIGHT))
                self.use_victory_custom_img = True
                print(f"Successfully loaded custom victory image: {victory_custom_path}")
            else:
                print(f"Custom victory image not found: {victory_custom_path}")
        except Exception as e:
            print(f"Failed to load custom victory image: {e}")
            
        # Try to load custom title image
        try:
            custom_title_path = os.path.join(ASSET_PATH, "images/title.png")
            if os.path.exists(custom_title_path):
                # Calculate appropriate scaling while maintaining aspect ratio
                img = pygame.image.load(custom_title_path)
                original_width, original_height = img.get_size()
                
                # Target width is 68% of screen width (80% reduced by 15%)
                target_width = int(WINDOW_WIDTH * 0.8 * 0.85)
                # Scale height proportionally
                target_height = int(original_height * (target_width / original_width))
                
                self.custom_title = self.asset_manager.load_image(custom_title_path, scale=(target_width, target_height))
                self.use_custom_title = True
                print(f"Successfully loaded custom title image: {custom_title_path}")
            else:
                print(f"Custom title image not found: {custom_title_path}")
        except Exception as e:
            print(f"Failed to load custom title image: {e}")
        
        # Create buttons with more space between them
        self.button_width = 280
        self.button_height = 50
        self.center_x = WINDOW_WIDTH // 2 - self.button_width // 2
        
        # Create buttons but don't position them yet - use placeholder positions
        # We'll set proper positions in _update_button_positions
        self.buttons = {
            'start': Button(self.center_x, 0, self.button_width, self.button_height, "Start Game", font_size=32),
            'resume': Button(self.center_x, 0, self.button_width, self.button_height, "Resume", font_size=32),
            'restart': Button(self.center_x, 0, self.button_width, self.button_height, "Restart", font_size=32),
            'options': Button(self.center_x, 0, self.button_width, self.button_height, "Options", font_size=32),
            'artworks': Button(self.center_x, 0, self.button_width, self.button_height, "Artworks", font_size=32),
            'quit': Button(self.center_x, 0, self.button_width, self.button_height, "Quit", font_size=32),
            'back': Button(self.center_x, 0, self.button_width, self.button_height, "Back", font_size=32),
            'fullscreen': Button(self.center_x, 0, self.button_width, self.button_height, "Fullscreen: Off", font_size=28),
            'controls': Button(self.center_x, 0, self.button_width, self.button_height, "Controls", font_size=28),
            'audio': Button(self.center_x, 0, self.button_width, self.button_height, "Audio", font_size=28)
        }
        
        # Track menu states
        self.showing_options = False
        self.showing_controls = False
        self.showing_audio = False
        self.showing_artworks = False
        self.in_pause_menu = False
        self.in_game_over = False
        self.in_victory = False
        
        # Controller navigation support
        self.selected_button_index = 0
        self.active_buttons = []
        
        # Track fullscreen state
        self.fullscreen_enabled = False
        
        # Game controls information
        self.controls_info = [
            ("Movement", "WASD / Arrow Keys"),
            ("Aim", "Mouse"),
            ("Throw", "Left Mouse Button"),
            ("Dodge", "Right Mouse Button"),
            ("Special Attack", "E"),
            ("Melee Attack", "Spacebar"),
            ("Pause", "Escape"),
            ("Toggle Fullscreen", "F11")
        ]
        
        # Set initial positions
        self._update_button_positions('main_menu')
        
        print("Menu initialized with buttons")
        
        # Credits scroll variables
        self.credits_text = [
            "MUD CRAWLER",
            "",
            "CREDITS",
            "",
            "Programming",
            "Cursor",
            "Claude 3.7 Sonnet",
            "",
            "Art & Design",
            "Hugging Face",
            "black-forest-labs/FLUX.1-schnell",
            "",
            "Music & Sound",
            "SUNO",
            "",
            "Special Thanks",
            "Kacsa, Pocok, Pupi",
            "Peti, Levi, Sebi,",
            "Zsizsik, Dubi"
            "",
            "Made with Python and Pygame",
            "",
            "Thanks for playing!"
        ]
        self.credits_y = WINDOW_HEIGHT  # Start below the screen
        self.credits_speed = 1.5  # Pixels per frame
        self.credits_line_height = 40
        self.show_credits = False
        self.credits_started_time = 0
        self.credits_completed = False  # Track if credits have scrolled through at least once
        
        # Artworks menu variables
        self.selected_level = 1
        self.artworks_bg = None
        self.level_buttons = []
        self.current_artwork_index = 0
        self.artwork_images = []
        
        # Create arrows for level navigation instead of individual buttons
        screen_center_x = WINDOW_WIDTH // 2
        self.left_level_arrow = Button(screen_center_x - 70, 50, 40, 40, "<", font_size=28)
        self.right_level_arrow = Button(screen_center_x + 30, 50, 40, 40, ">", font_size=28)
        
        # Try to load artwork background
        try:
            artwork_bg_path = os.path.join(ASSET_PATH, "images/artwork.png")
            if os.path.exists(artwork_bg_path):
                self.artworks_bg = self.asset_manager.load_image(artwork_bg_path, scale=(WINDOW_WIDTH, WINDOW_HEIGHT))
                print(f"Successfully loaded artworks background: {artwork_bg_path}")
        except Exception as e:
            print(f"Failed to load artworks background: {e}")
            # Create a default background if loading fails
            self.artworks_bg = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
            self.artworks_bg.fill((30, 30, 50))
            # Add some simple decoration
            for i in range(0, WINDOW_HEIGHT, 40):
                pygame.draw.line(self.artworks_bg, (40, 40, 70), (0, i), (WINDOW_WIDTH, i), 1)
            for i in range(0, WINDOW_WIDTH, 40):
                pygame.draw.line(self.artworks_bg, (40, 40, 70), (i, 0), (i, WINDOW_HEIGHT), 1)
        
            
    def _update_button_positions(self, menu_type):
        """Update button positions based on the menu type being displayed"""
        if menu_type == 'main_menu':
            # Position buttons for main menu
            self.buttons['start'].rect.x = self.center_x
            self.buttons['start'].rect.y = WINDOW_HEIGHT // 2
            
            self.buttons['options'].rect.x = self.center_x
            self.buttons['options'].rect.y = WINDOW_HEIGHT // 2 + 70
            
            self.buttons['artworks'].rect.x = self.center_x
            self.buttons['artworks'].rect.y = WINDOW_HEIGHT // 2 + 140
            
            self.buttons['quit'].rect.x = self.center_x
            self.buttons['quit'].rect.y = WINDOW_HEIGHT // 2 + 210
            
        elif menu_type == 'pause_menu':
            # Position buttons for pause menu
            self.buttons['resume'].rect.x = self.center_x
            self.buttons['resume'].rect.y = WINDOW_HEIGHT // 2
            
            self.buttons['restart'].rect.x = self.center_x
            self.buttons['restart'].rect.y = WINDOW_HEIGHT // 2 + 70
            
            self.buttons['options'].rect.x = self.center_x
            self.buttons['options'].rect.y = WINDOW_HEIGHT // 2 + 140
            
            self.buttons['quit'].rect.x = self.center_x
            self.buttons['quit'].rect.y = WINDOW_HEIGHT // 2 + 210
            
        elif menu_type == 'options_menu':
            # Position buttons for options menu
            self.buttons['fullscreen'].rect.x = self.center_x
            self.buttons['fullscreen'].rect.y = WINDOW_HEIGHT // 2
            
            self.buttons['controls'].rect.x = self.center_x
            self.buttons['controls'].rect.y = WINDOW_HEIGHT // 2 + 70
            
            self.buttons['audio'].rect.x = self.center_x
            self.buttons['audio'].rect.y = WINDOW_HEIGHT // 2 + 140
            
            self.buttons['back'].rect.x = self.center_x
            self.buttons['back'].rect.y = WINDOW_HEIGHT // 2 + 210
            
        elif menu_type == 'controls_menu':
            # Position back button for controls menu
            self.buttons['back'].rect.x = self.center_x
            self.buttons['back'].rect.y = WINDOW_HEIGHT - 100
            
        elif menu_type == 'game_over' or menu_type == 'victory':
            # Position buttons for game over and victory screens
            self.buttons['restart'].rect.x = self.center_x
            self.buttons['restart'].rect.y = WINDOW_HEIGHT // 2 + 60
            
            self.buttons['quit'].rect.x = self.center_x
            self.buttons['quit'].rect.y = WINDOW_HEIGHT // 2 + 130
            
        elif menu_type == 'artworks_menu':
            # Position back button for artworks menu
            self.buttons['back'].rect.x = self.center_x
            self.buttons['back'].rect.y = WINDOW_HEIGHT - 70
    
    def draw_main_menu(self):
        # Update button positions first
        self._update_button_positions('main_menu')
        
        # Update state flags
        self.in_pause_menu = False
        self.in_game_over = False
        self.in_victory = False
        
        # Draw welcome screen if available, otherwise fallback to menu background
        if self.use_welcome_screen:
            if self.video_player and self.video_player.is_playing:
                # Update and draw video
                self.video_player.update()
                self.video_player.draw()
            elif self.welcome_screen:
                # Fall back to static image if video not available
                self.screen.blit(self.welcome_screen, (0, 0))
        else:
            # Draw background
            self.screen.blit(self.menu_bg, (0, 0))
            
            # Draw title
            if self.use_title_image:
                title_rect = self.title_image.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 3))
                self.screen.blit(self.title_image, title_rect)
            else:
                title = self.font.render("MUD CRAWLER", True, WHITE)
                title_rect = title.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 3))
                self.screen.blit(title, title_rect)
            
            # Draw subtitle with pixelated font
            subtitle = self.subtitle_font.render("8-bit Dungeon Adventure", True, (200, 200, 200))
            subtitle_rect = subtitle.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 3 + 50))
            self.screen.blit(subtitle, subtitle_rect)
        
        # Draw version number in top right corner
        version_text = self.instruction_font.render("1.0 Beta", True, (255, 255, 0))
        version_rect = version_text.get_rect(topright=(WINDOW_WIDTH - 10, 10))
        self.screen.blit(version_text, version_rect)
        
        # Draw the custom title image if available
        if self.use_custom_title and self.custom_title:
            # Position the title above the start button
            title_y = self.buttons['start'].rect.y - self.custom_title.get_height() - 20  # 20px margin
            
            # Adjust y position if it's too high up on the screen 
            if title_y < 20:
                title_y = 20
                
            title_rect = self.custom_title.get_rect(centerx=WINDOW_WIDTH // 2, top=title_y)
            self.screen.blit(self.custom_title, title_rect)
        
        # Ensure the current controller-selected button is highlighted
        active_buttons = ['start', 'options', 'artworks', 'quit']
        if 0 <= self.selected_button_index < len(active_buttons):
            button_name = active_buttons[self.selected_button_index]
            self.buttons[button_name].is_hovered = True
        
        # Draw buttons with enhanced visibility
        self.buttons['start'].draw(self.screen)
        self.buttons['options'].draw(self.screen)
        self.buttons['artworks'].draw(self.screen)
        self.buttons['quit'].draw(self.screen)
        
        # Draw instructions with pixelated font at the bottom of the screen
        inst_text = self.instruction_font.render("Click START GAME or press ENTER to play", True, (255, 255, 0))
        inst_rect = inst_text.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT - 20))
        self.screen.blit(inst_text, inst_rect)
        
    def draw_pause_menu(self):
        # Update button positions first
        self._update_button_positions('pause_menu')
        
        # Update state flags
        self.in_pause_menu = True
        self.in_game_over = False
        self.in_victory = False
        
        # Draw background
        self.screen.blit(self.menu_bg, (0, 0))
        
        # Semi-transparent overlay
        overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
        overlay.fill((0, 0, 0))
        overlay.set_alpha(128)
        self.screen.blit(overlay, (0, 0))
        
        # Draw title with pixelated font
        title = self.font.render("PAUSED", True, WHITE)
        title_rect = title.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 3))
        self.screen.blit(title, title_rect)
        
        # Ensure the current controller-selected button is highlighted
        active_buttons = ['resume', 'restart', 'options', 'quit']
        if 0 <= self.selected_button_index < len(active_buttons):
            button_name = active_buttons[self.selected_button_index]
            self.buttons[button_name].is_hovered = True
            
        # Draw buttons
        self.buttons['resume'].draw(self.screen)
        self.buttons['restart'].draw(self.screen)
        self.buttons['options'].draw(self.screen)
        self.buttons['quit'].draw(self.screen)
        
        # Draw warp dialog if active
        if self.show_warp_dialog:
            self._draw_warp_dialog()
            
    def _draw_warp_dialog(self):
        """Draw the level warp selection dialog"""
        # Create dialog background - make it taller and position at top
        dialog_width = 300
        dialog_height = 450  # Increased height
        dialog_x = (WINDOW_WIDTH - dialog_width) // 2
        dialog_y = 50  # Fixed position at top of screen
        
        # Draw semi-transparent background
        dialog_bg = pygame.Surface((dialog_width, dialog_height), pygame.SRCALPHA)
        dialog_bg.fill((0, 0, 0, 200))
        self.screen.blit(dialog_bg, (dialog_x, dialog_y))
        
        # Draw border
        pygame.draw.rect(self.screen, (255, 215, 0), (dialog_x, dialog_y, dialog_width, dialog_height), 2)
        
        # Draw title
        title_font = pygame.font.Font(None, 36)
        title = title_font.render("LEVEL WARP", True, (255, 215, 0))
        title_rect = title.get_rect(center=(WINDOW_WIDTH // 2, dialog_y + 30))
        self.screen.blit(title, title_rect)
        
        # Draw level options
        level_font = pygame.font.Font(None, 28)
        for i in range(1, 11):
            level_text = f"Level {i}"
            
            # Highlight selected level
            if i == self.warp_level_selected:
                level_color = (255, 255, 0)  # Bright yellow for selected
                # Draw selection indicator
                indicator_x = dialog_x + 20
                indicator_y = dialog_y + 70 + (i * 28)  # Increased spacing
                pygame.draw.polygon(self.screen, level_color, 
                                  [(indicator_x, indicator_y), 
                                   (indicator_x + 10, indicator_y - 5),
                                   (indicator_x + 10, indicator_y + 5)])
            else:
                level_color = (200, 200, 200)  # Gray for unselected
                
            level_surf = level_font.render(level_text, True, level_color)
            self.screen.blit(level_surf, (dialog_x + 40, dialog_y + 70 + (i * 28)))  # Increased spacing
        
        # Draw instructions at bottom with more space
        inst_font = pygame.font.Font(None, 24)
        inst1 = inst_font.render("Enter: Warp", True, (200, 200, 200))
        inst2 = inst_font.render("Esc: Cancel", True, (200, 200, 200))
        
        # Position instructions at the bottom with more space
        self.screen.blit(inst1, (dialog_x + 40, dialog_y + dialog_height - 60))
        self.screen.blit(inst2, (dialog_x + 40, dialog_y + dialog_height - 30))
    
    def draw_game_over(self):
        # Update button positions first
        self._update_button_positions('game_over')
        
        # Update state flags
        self.in_pause_menu = False
        self.in_game_over = True
        self.in_victory = False
        
        # Draw background
        if self.use_gameover_custom_img and self.gameover_custom_img:
            self.screen.blit(self.gameover_custom_img, (0, 0))
        else:
            self.screen.blit(self.menu_bg, (0, 0))
        
        # Draw title with pixelated font
        if not self.use_gameover_custom_img or self.gameover_custom_img is None:
            title = self.font.render("GAME OVER", True, RED)
        else:
            # Create a better visible title for custom background
            title = self.font.render("GAME OVER", True, (255, 0, 0))
            
        title_rect = title.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 3))
        self.screen.blit(title, title_rect)
        
        # Ensure the current controller-selected button is highlighted
        active_buttons = ['restart', 'quit']
        if 0 <= self.selected_button_index < len(active_buttons):
            button_name = active_buttons[self.selected_button_index]
            self.buttons[button_name].is_hovered = True
        
        # Draw buttons
        self.buttons['restart'].draw(self.screen)
        self.buttons['quit'].draw(self.screen)
        
    def draw_victory(self):
        # Update button positions first
        self._update_button_positions('victory')
        
        # Update state flags
        self.in_pause_menu = False
        self.in_game_over = False
        self.in_victory = True
        
        # Draw background
        if self.use_victory_custom_img and self.victory_custom_img:
            self.screen.blit(self.victory_custom_img, (0, 0))
        else:
            self.screen.blit(self.menu_bg, (0, 0))
        
        # Start credits if not started yet
        if not self.show_credits:
            self.show_credits = True
            self.credits_y = WINDOW_HEIGHT
            self.credits_started_time = pygame.time.get_ticks()
        
        # Draw scrolling credits
        self._draw_scrolling_credits()
            
        # Draw title with pixelated font if not using custom image and if credits just started
        if (not self.use_victory_custom_img or self.victory_custom_img is None) and pygame.time.get_ticks() - self.credits_started_time < 5000:
            title = self.font.render("VICTORY!", True, GREEN)
            title_rect = title.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 3))
            self.screen.blit(title, title_rect)
            
            # Draw message with pixelated font
            msg = self.font.render("Congratulations!", True, WHITE)
            msg_rect = msg.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2))
            self.screen.blit(msg, msg_rect)
        
        # Do not draw buttons on victory screen since we're showing credits
        
    def _draw_scrolling_credits(self):
        """Draw scrolling credits text"""
        if not self.show_credits:
            return
            
        # Update credits position
        self.credits_y -= self.credits_speed
        
        # Draw each line of credits
        total_height = len(self.credits_text) * self.credits_line_height
        
        # Calculate if all credits have scrolled past the top
        all_credits_passed = self.credits_y + total_height < 0
        
        # Reset credits position if all credits have passed
        if all_credits_passed:
            self.credits_y = WINDOW_HEIGHT
            # Mark credits as completed (scrolled through at least once)
            self.credits_completed = True
        
        # Draw each line with semi-transparent background for better readability
        credits_width = 0
        for line in self.credits_text:
            text_surface = self.credits_font.render(line, True, WHITE)
            credits_width = max(credits_width, text_surface.get_width())
            
        # Create background for credits
        bg_width = credits_width + 40  # Add padding
        bg_height = total_height
        bg_surface = pygame.Surface((bg_width, bg_height), pygame.SRCALPHA)
        bg_surface.fill((0, 0, 0, 150))  # Semi-transparent black
        
        # Draw background
        bg_x = (WINDOW_WIDTH - bg_width) // 2
        self.screen.blit(bg_surface, (bg_x, self.credits_y))
        
        # Draw text
        for i, line in enumerate(self.credits_text):
            text_surface = self.credits_font.render(line, True, WHITE)
            text_rect = text_surface.get_rect(center=(WINDOW_WIDTH // 2, self.credits_y + i * self.credits_line_height + self.credits_line_height // 2))
            self.screen.blit(text_surface, text_rect)
            
            # Add special styling for headings (lines followed by empty line)
            if i < len(self.credits_text) - 1 and self.credits_text[i+1] == "" and line != "":
                # Draw line with golden color
                heading_surface = self.credits_font.render(line, True, (255, 215, 0))  # Gold color
                self.screen.blit(heading_surface, text_rect)
        
        # Show "Press any key to continue" message when credits have completed one cycle
        if self.credits_completed:
            # Create a pulsing effect for the text
            alpha = int(127 + 127 * math.sin(pygame.time.get_ticks() / 500))  # Pulse between 127-255 alpha
            continue_text = self.subtitle_font.render("Press any key to continue", True, (255, 255, 100, alpha))
            continue_rect = continue_text.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT - 50))
            
            # Semi-transparent background for better readability
            text_bg = pygame.Surface((continue_rect.width + 20, continue_rect.height + 10), pygame.SRCALPHA)
            text_bg.fill((0, 0, 0, 150))
            self.screen.blit(text_bg, (continue_rect.x - 10, continue_rect.y - 5))
            
            # Draw the text
            self.screen.blit(continue_text, continue_rect)
    
    def draw_options_menu(self):
        # Update button positions first
        self._update_button_positions('options_menu')
        
        # Draw background
        self.screen.blit(self.menu_bg, (0, 0))
        
        # Draw title
        title = self.font.render("OPTIONS", True, WHITE)
        title_rect = title.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 3))
        self.screen.blit(title, title_rect)
        
        # Update fullscreen button text based on current state
        fullscreen_text = "Fullscreen: On" if self.fullscreen_enabled else "Fullscreen: Off"
        self.buttons['fullscreen'].text = fullscreen_text
        
        # Ensure the current controller-selected button is highlighted
        active_buttons = ['fullscreen', 'controls', 'audio', 'back']
        if 0 <= self.selected_button_index < len(active_buttons):
            button_name = active_buttons[self.selected_button_index]
            self.buttons[button_name].is_hovered = True
        
        # Draw buttons
        self.buttons['fullscreen'].draw(self.screen)
        self.buttons['controls'].draw(self.screen)
        self.buttons['audio'].draw(self.screen)
        self.buttons['back'].draw(self.screen)
    
    def toggle_fullscreen(self):
        """Toggle the fullscreen state and update button text"""
        self.fullscreen_enabled = not self.fullscreen_enabled
        return self.fullscreen_enabled
        
    def cleanup(self):
        """Release resources when closing the game"""
        if self.video_player:
            self.video_player.stop()
            self.video_player = None
    
    def handle_event(self, event):
        """Handle a pygame event and return any button that was clicked"""
        # Determine which buttons should be active based on menu state
        active_buttons = []
        
        if self.showing_options:
            active_buttons = ['fullscreen', 'controls', 'audio', 'back']
        elif self.showing_controls:
            active_buttons = ['back']
            # Handle controls menu tab navigation
            if self.handle_controls_navigation(event):
                return None
        elif self.showing_audio:
            active_buttons = ['back']
        elif self.showing_artworks:
            active_buttons = ['back']
        elif self.in_pause_menu:
            active_buttons = ['resume', 'restart', 'options', 'quit']
            
            # Handle cheat code in pause menu
            if event.type == pygame.KEYDOWN:
                # If warp dialog is shown, handle level selection
                if self.show_warp_dialog:
                    if event.key == pygame.K_UP:
                        self.warp_level_selected = max(1, self.warp_level_selected - 1)
                        return None
                    elif event.key == pygame.K_DOWN:
                        self.warp_level_selected = min(10, self.warp_level_selected + 1)
                        return None
                    elif event.key == pygame.K_RETURN or event.key == pygame.K_SPACE:
                        # Return special command for level warping
                        self.show_warp_dialog = False
                        self.cheat_code_buffer = ""
                        return f"warp_to_level_{self.warp_level_selected}"
                    elif event.key == pygame.K_ESCAPE:
                        # Cancel warp dialog
                        self.show_warp_dialog = False
                        self.cheat_code_buffer = ""
                        return None
                else:
                    # Track cheat code input
                    if event.unicode.lower() in "iddqd":
                        self.cheat_code_buffer += event.unicode.lower()
                        # Keep only last 5 characters
                        self.cheat_code_buffer = self.cheat_code_buffer[-5:]
                        
                        # Check if cheat code is complete
                        if self.cheat_code_buffer == "iddqd":
                            print("Cheat code activated: IDDQD - Level warp enabled")
                            self.show_warp_dialog = True
                            self.warp_level_selected = 1
                            
                            # Play the warp sound directly using pygame instead of the sound manager
                            try:
                                warp_sound_path = os.path.join(SOUNDS_PATH, "effects", "level_warp.wav")
                                if os.path.exists(warp_sound_path):
                                    warp_sound = pygame.mixer.Sound(warp_sound_path)
                                    warp_sound.set_volume(0.7)  # Set appropriate volume
                                    warp_sound.play()
                                    print("Playing level warp sound directly")
                                else:
                                    print(f"Level warp sound file not found at: {warp_sound_path}")
                            except Exception as e:
                                print(f"Error playing level warp sound: {e}")
                                
                            return None
        elif self.in_game_over or self.in_victory:
            active_buttons = ['restart', 'quit']
        else:
            # Default to main menu buttons
            active_buttons = ['start', 'options', 'artworks', 'quit']
            
        # Store active buttons for controller navigation
        self.active_buttons = active_buttons
        
        # Reset the cheat code buffer when not in pause menu
        if not self.in_pause_menu:
            self.cheat_code_buffer = ""
            self.show_warp_dialog = False
        
        # Make sure selected button index is valid for current menu
        if self.active_buttons and self.selected_button_index >= len(self.active_buttons):
            self.selected_button_index = 0
        
        # Handle controller navigation
        if event.type == pygame.KEYDOWN:
            # Up/Down navigation (mapped from controller D-pad and left stick)
            if event.key == pygame.K_UP or event.key == pygame.K_w:
                self.navigate_menu(-1)  # Move up
                return None
            elif event.key == pygame.K_DOWN or event.key == pygame.K_s:
                self.navigate_menu(1)   # Move down
                return None
            # Select current button with Space (mapped from RT)
            elif event.key == pygame.K_SPACE:
                if self.active_buttons and 0 <= self.selected_button_index < len(self.active_buttons):
                    button_name = self.active_buttons[self.selected_button_index]
                    return button_name
        
        # Get current mouse position for hover check
        if event.type == pygame.MOUSEMOTION:
            mouse_pos = pygame.mouse.get_pos()
            for button_name, button in self.buttons.items():
                previous_hover = button.is_hovered
                button.is_hovered = button.rect.collidepoint(mouse_pos)
                        
                # Update selected button index when hovering with mouse
                if button.is_hovered and button_name in self.active_buttons:
                    self.selected_button_index = self.active_buttons.index(button_name)
        
        # If we're showing the artworks menu, handle its specialized events
        if self.showing_artworks:
            artworks_action = self.handle_artworks_navigation(event)
            if artworks_action:
                # If the action is a level selection, return that
                if artworks_action.startswith("level_"):
                    return artworks_action
                # Otherwise, just return None as we handled a navigation action
                return None
        
        # For mouse click events
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # Left mouse button
                mouse_pos = event.pos
                # Check all active buttons for click collision
                for button_name in active_buttons:
                    if button_name in self.buttons:
                        button = self.buttons[button_name]
                        if button.rect.collidepoint(mouse_pos):
                            # Handle video player cleanup for specific buttons
                            if button_name in ['start', 'restart', 'quit']:
                                if self.video_player:
                                    self.video_player.stop()
                            
                            return button_name
        
        # Handle all other events through normal button processing
        for button_name in active_buttons:
            if button_name in self.buttons and self.buttons[button_name].handle_event(event):
                # Handle video player cleanup for specific buttons
                if button_name in ['start', 'restart', 'quit']:
                    if self.video_player:
                        self.video_player.stop()
                        
                return button_name
                
        return None
    
    def handle_controls_navigation(self, event):
        """Handle navigation between keyboard and controller tabs in controls menu"""
        if not hasattr(self, 'controls_page'):
            self.controls_page = 'keyboard'  # Default to keyboard page
            
        # Switch between keyboard and controller pages using left/right arrow keys
        if event.type == pygame.KEYDOWN:
            if event.key in [pygame.K_LEFT, pygame.K_a, pygame.K_q]:  # Q maps to LB on controller
                self.controls_page = 'keyboard'
                return True
            elif event.key in [pygame.K_RIGHT, pygame.K_d, pygame.K_e]:  # E maps to RB on controller
                self.controls_page = 'controller'
                return True
                
        # Handle mouse clicks on tab headers
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mouse_pos = event.pos
            if hasattr(self, 'keyboard_tab_rect') and self.keyboard_tab_rect.collidepoint(mouse_pos):
                self.controls_page = 'keyboard'
                return True
            elif hasattr(self, 'controller_tab_rect') and self.controller_tab_rect.collidepoint(mouse_pos):
                self.controls_page = 'controller'
                return True
                
        return False
    
    def navigate_menu(self, direction):
        """Navigate through menu buttons (direction: 1=down, -1=up)"""
        if not self.active_buttons:
            return
            
        # Update the selected button index
        self.selected_button_index = (self.selected_button_index + direction) % len(self.active_buttons)
        
        # Reset hover states for all buttons
        for button in self.buttons.values():
            button.is_hovered = False
            
        # Highlight the selected button
        selected_button_name = self.active_buttons[self.selected_button_index]
        self.buttons[selected_button_name].is_hovered = True
    
    def get_active_buttons(self):
        """Return the appropriate list of buttons based on current menu state"""
        if self.showing_options:
            return ['fullscreen', 'controls', 'audio', 'back']
        elif self.showing_controls:
            return ['back']
        elif self.showing_audio:
            return ['back']
        elif self.showing_artworks:
            return ['back']
        elif self.in_pause_menu:
            return ['resume', 'restart', 'options', 'quit']
        elif self.in_game_over or self.in_victory:
            return ['restart', 'quit']
        else:
            # Default to main menu buttons
            return ['start', 'options', 'artworks', 'quit']

    def _load_static_welcome_screen(self):
        """Helper method to load the static welcome screen image"""
        welcome_path = os.path.join(ASSET_PATH, "images/e9aa7981-5ad9-44cf-91d9-3f5e4c45b13d.png")
        if os.path.exists(welcome_path):
            self.welcome_screen = self.asset_manager.load_image(welcome_path, scale=(WINDOW_WIDTH, WINDOW_HEIGHT))
            self.use_welcome_screen = True
            print(f"Successfully loaded welcome screen image: {welcome_path}")
        else:
            print(f"Welcome screen image not found: {welcome_path}, falling back to menu background")
            # Just use the menu background instead of default background
            
    def initialize_welcome_screen_video(self):
        """Initialize or reinitialize the welcome screen video player"""
        # Stop any existing video player
        if self.video_player:
            self.video_player.stop()
            self.video_player = None
            
        # Try to load video if it exists and OpenCV is available
        try:
            video_path = os.path.join(ASSET_PATH, "images/menu.mp4")
            if OPENCV_AVAILABLE and os.path.exists(video_path):
                self.video_player = VideoPlayer(video_path, self.screen, loop=True)
                if self.video_player.is_playing:
                    self.use_welcome_screen = True
                    print(f"Successfully initialized welcome screen video: {video_path}")
                else:
                    print(f"Failed to initialize video player, falling back to static image")
                    self.video_player = None
                    # Fall back to static image
                    self._load_static_welcome_screen()
            else:
                # OpenCV not available or video doesn't exist, fall back to static image
                self._load_static_welcome_screen()
        except Exception as e:
            print(f"Failed to initialize welcome screen video: {e}")
            self._load_static_welcome_screen()

    # Add a new method to draw the controls menu
    def draw_controls_menu(self):
        # Update button positions first
        self._update_button_positions('controls_menu')
        
        # Draw background
        self.screen.blit(self.menu_bg, (0, 0))
        
        # Draw title
        title = self.font.render("CONTROLS", True, WHITE)
        title_rect = title.get_rect(center=(WINDOW_WIDTH // 2, 50))
        self.screen.blit(title, title_rect)
        
        # Get the current controls page (default to keyboard)
        current_page = getattr(self, 'controls_page', 'keyboard')
        
        # Draw tabs for navigation
        self._draw_controls_tabs(current_page)
        
        if current_page == 'keyboard':
            # Draw keyboard controls
            y_pos = 140
            line_height = 40
            
            # Define column positions
            action_column_x = 30  # Move action column to the left edge
            value_column_x = WINDOW_WIDTH // 2 - 50  # Shifted left to give more room for value column
            
            # Calculate column widths
            action_width = value_column_x - action_column_x - 20
            value_width = WINDOW_WIDTH - value_column_x - 20  # Increased width
            
            # Header row
            header_font = pygame.font.Font(None, 36)
            action_text = header_font.render("Action", True, (180, 180, 255))
            key_text = header_font.render("Key / Button", True, (180, 180, 255))
            
            # Position headers
            action_rect = action_text.get_rect(x=action_column_x, y=y_pos)
            key_rect = key_text.get_rect(x=value_column_x, y=y_pos)
            
            # Draw header line
            pygame.draw.line(self.screen, (100, 100, 180), 
                             (action_column_x - 10, y_pos + action_text.get_height() + 5),
                             (value_column_x + value_width, y_pos + action_text.get_height() + 5), 2)
            
            # Draw headers
            self.screen.blit(action_text, action_rect)
            self.screen.blit(key_text, key_rect)
            
            # Update y position after headers
            y_pos += action_text.get_height() + 15
            
            controls_data = [
                ("Movement", "W, A, S, D / Arrow Keys"),
                ("Attack", "SPACE"),
                ("Bow Attack", "LEFT MOUSE BUTTON"),
                ("Dodge", "RIGHT MOUSE BUTTON"),
                ("Special Attack", "E"),
                ("Pause", "ESC"),
                ("Restart Level", "R (only in pause menu)"),
                ("Toggle Fullscreen", "F11")
            ]
            
            for label, value in controls_data:
                # Draw control label with a subtle background
                label_bg = pygame.Rect(action_column_x - 10, y_pos - 2, action_width, 30)
                pygame.draw.rect(self.screen, (60, 60, 80), label_bg, border_radius=3)
                
                text = self.instruction_font.render(label + ":", True, WHITE)
                text_rect = text.get_rect(x=action_column_x, y=y_pos)
                self.screen.blit(text, text_rect)
                
                # Draw control value with a key-like appearance
                value_bg = pygame.Rect(value_column_x - 10, y_pos - 2, value_width, 30)
                pygame.draw.rect(self.screen, (50, 50, 60), value_bg, border_radius=3)
                pygame.draw.rect(self.screen, (80, 80, 100), value_bg, 1, border_radius=3)
                
                text = self.instruction_font.render(value, True, (220, 220, 220))
                text_rect = text.get_rect(x=value_column_x, y=y_pos)
                self.screen.blit(text, text_rect)
                
                y_pos += line_height
                
        else:  # controller page
            # Draw controller controls
            y_pos = 140
            line_height = 40
            
            # Define column positions
            action_column_x = 30  # Move action column to the left edge
            value_column_x = WINDOW_WIDTH // 2 - 50  # Shifted left to give more room for value column
            
            # Calculate column widths
            action_width = value_column_x - action_column_x - 20
            value_width = WINDOW_WIDTH - value_column_x - 20  # Increased width
            
            # Header row
            header_font = pygame.font.Font(None, 36)
            action_text = header_font.render("Action", True, (180, 180, 255))
            key_text = header_font.render("Controller Input", True, (180, 180, 255))
            
            # Position headers
            action_rect = action_text.get_rect(x=action_column_x, y=y_pos)
            key_rect = key_text.get_rect(x=value_column_x, y=y_pos)
            
            # Draw header line
            pygame.draw.line(self.screen, (100, 100, 180), 
                             (action_column_x - 10, y_pos + action_text.get_height() + 5),
                             (value_column_x + value_width, y_pos + action_text.get_height() + 5), 2)
            
            # Draw headers
            self.screen.blit(action_text, action_rect)
            self.screen.blit(key_text, key_rect)
            
            # Update y position after headers
            y_pos += action_text.get_height() + 15
            
            controls_data = [
                ("Movement", "Left Stick / D-Pad"),
                ("Aim", "Right Stick"),
                ("Attack", "Right Trigger (RT)"),
                ("Bow Attack", "Left Trigger (LT)"),
                ("Dodge", "X Button"),
                ("Special Attack", "Y Button"),
                ("Pause", "Start Button")
            ]
            
            for label, value in controls_data:
                # Draw control label with a subtle background
                label_bg = pygame.Rect(action_column_x - 10, y_pos - 2, action_width, 30)
                pygame.draw.rect(self.screen, (60, 60, 80), label_bg, border_radius=3)
                
                text = self.instruction_font.render(label + ":", True, WHITE)
                text_rect = text.get_rect(x=action_column_x, y=y_pos)
                self.screen.blit(text, text_rect)
                
                # Draw control value with a button-like appearance
                value_bg = pygame.Rect(value_column_x - 10, y_pos - 2, value_width, 30)
                pygame.draw.rect(self.screen, (50, 50, 60), value_bg, border_radius=3)
                pygame.draw.rect(self.screen, (80, 80, 100), value_bg, 1, border_radius=3)
                
                text = self.instruction_font.render(value, True, (220, 220, 220))
                text_rect = text.get_rect(x=value_column_x, y=y_pos)
                self.screen.blit(text, text_rect)
                
                y_pos += line_height
        
        # Draw instructions for navigation between tabs
        hint_y = WINDOW_HEIGHT - 30
        
        # Create a smaller font for the hint text
        small_font = pygame.font.Font(None, 28)
        
        # Draw hint text directly without background
        hint_text = small_font.render("Use LEFT/RIGHT arrows or LB/RB to switch pages", True, (255, 255, 0))
        hint_rect = hint_text.get_rect(center=(WINDOW_WIDTH // 2, hint_y))
        self.screen.blit(hint_text, hint_rect)
        
        # Ensure the current controller-selected button is highlighted
        active_buttons = ['back']
        if 0 <= self.selected_button_index < len(active_buttons):
            button_name = active_buttons[self.selected_button_index]
            self.buttons[button_name].is_hovered = True
        
        # Draw back button
        self.buttons['back'].draw(self.screen)
    
    def _draw_controls_tabs(self, current_page):
        """Draw tabs for keyboard and controller pages"""
        # Tab dimensions
        tab_width = 220  # Increased from 180
        tab_height = 40
        margin = 10
        
        # Tab positions
        keyboard_tab_rect = pygame.Rect(WINDOW_WIDTH // 2 - tab_width - margin // 2, 80, tab_width, tab_height)
        controller_tab_rect = pygame.Rect(WINDOW_WIDTH // 2 + margin // 2, 80, tab_width, tab_height)
        
        # Draw keyboard tab
        keyboard_color = (255, 255, 255) if current_page == 'keyboard' else (100, 100, 100)
        pygame.draw.rect(self.screen, (60, 60, 80), keyboard_tab_rect)
        pygame.draw.rect(self.screen, keyboard_color, keyboard_tab_rect, 2)
        keyboard_text = self.instruction_font.render("Key/Mouse", True, keyboard_color)
        keyboard_text_rect = keyboard_text.get_rect(center=keyboard_tab_rect.center)
        self.screen.blit(keyboard_text, keyboard_text_rect)
        
        # Draw controller tab
        controller_color = (255, 255, 255) if current_page == 'controller' else (100, 100, 100)
        pygame.draw.rect(self.screen, (60, 60, 80), controller_tab_rect)
        pygame.draw.rect(self.screen, controller_color, controller_tab_rect, 2)
        controller_text = self.instruction_font.render("Controller", True, controller_color)
        controller_text_rect = controller_text.get_rect(center=controller_tab_rect.center)
        self.screen.blit(controller_text, controller_text_rect)
        
        # Store tab rects for click handling
        self.keyboard_tab_rect = keyboard_tab_rect
        self.controller_tab_rect = controller_tab_rect

    def draw_artworks_menu(self):
        """Draw the artworks gallery menu"""
        # Update button positions first
        self._update_button_positions('artworks_menu')
        
        # Draw the artwork background
        if self.artworks_bg:
            self.screen.blit(self.artworks_bg, (0, 0))
        else:
            # Fallback to a simple background
            self.screen.fill((30, 30, 50))
        
        # Center the level selector in the top area of the screen
        screen_center_x = WINDOW_WIDTH // 2
        
        # Update arrow button positions to be centered
        self.left_level_arrow.rect.x = screen_center_x - 70  # 40px left of center (plus offset for button width)
        self.left_level_arrow.rect.y = 50
        self.right_level_arrow.rect.x = screen_center_x + 30  # 40px right of center
        self.right_level_arrow.rect.y = 50
        
        # Draw level selector with arrows and number display
        self.left_level_arrow.draw(self.screen)
        self.right_level_arrow.draw(self.screen)
        
        # Draw level number between arrows with decorative background
        level_bg = pygame.Surface((60, 40), pygame.SRCALPHA)
        level_bg.fill((80, 60, 120, 180))  # Semi-transparent purple background
        pygame.draw.rect(level_bg, (255, 255, 100), pygame.Rect(0, 0, 60, 40), 2)  # Yellow border
        
        # Position the level number background between the arrows in the center
        level_bg_x = screen_center_x - 30  # Center the 60px background
        level_bg_y = 50  # Same Y as arrows
        self.screen.blit(level_bg, (level_bg_x, level_bg_y))
        
        # Draw the level number on top of the background
        level_text = self.font.render(f"{self.selected_level}", True, (255, 255, 100))
        level_rect = level_text.get_rect(center=(screen_center_x, level_bg_y + 20))  # Center in the background
        self.screen.blit(level_text, level_rect)
        
        # Label for the level selector
        level_label = self.instruction_font.render("Level", True, (200, 200, 200))
        level_label_rect = level_label.get_rect(center=(screen_center_x, 30))
        self.screen.blit(level_label, level_label_rect)
        
        # Load artwork images for the selected level if not already loaded
        if not self.artwork_images or len(self.artwork_images) == 0:
            self.load_artwork_images(self.selected_level)
        
        # Display the current artwork image
        if self.artwork_images and len(self.artwork_images) > 0:
            # Center the image in the main display area
            current_img = self.artwork_images[self.current_artwork_index]
            # Scale image to fit within the display area while maintaining aspect ratio
            display_area_width = WINDOW_WIDTH - 100
            display_area_height = WINDOW_HEIGHT - 150
            img_width, img_height = current_img.get_size()
            
            # Calculate scale factor to fit within display area
            scale_w = display_area_width / img_width
            scale_h = display_area_height / img_height
            scale = min(scale_w, scale_h)
            
            # Scale image
            new_width = int(img_width * scale)
            new_height = int(img_height * scale)
            scaled_img = pygame.transform.scale(current_img, (new_width, new_height))
            
            # Position in center of display area
            img_x = (WINDOW_WIDTH - new_width) // 2
            img_y = 120 + (display_area_height - new_height) // 2
            
            self.screen.blit(scaled_img, (img_x, img_y))
            
            # Draw navigation arrows if there are multiple images
            if len(self.artwork_images) > 1:
                # Calculate vertical center position for the navigation buttons
                vert_center = img_y + new_height // 2
                
                # Left arrow
                if self.current_artwork_index > 0:
                    left_text = self.instruction_font.render("< Prev", True, (255, 255, 100))
                    left_rect = left_text.get_rect(midright=(img_x - 20, vert_center))
                    self.screen.blit(left_text, left_rect)
                
                # Right arrow
                if self.current_artwork_index < len(self.artwork_images) - 1:
                    right_text = self.instruction_font.render("Next >", True, (255, 255, 100))
                    right_rect = right_text.get_rect(midleft=(img_x + new_width + 20, vert_center))
                    self.screen.blit(right_text, right_rect)
        else:
            # Display message if no images are available
            no_img_text = self.font.render("No artwork available for this level", True, WHITE)
            no_img_rect = no_img_text.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2))
            self.screen.blit(no_img_text, no_img_rect)
        
        # Draw back button
        self.buttons['back'].draw(self.screen)
    
    def load_artwork_images(self, level):
        """Load artwork images for the selected level"""
        self.artwork_images = []
        self.current_artwork_index = 0
        
        # Load enemy sprites
        enemy_path = None
        if level == 1:
            enemy_path = os.path.join(ENEMY_SPRITES_PATH, "slimes")
        elif level == 2:
            enemy_path = os.path.join(ENEMY_SPRITES_PATH, "skeletons")
        elif level == 3:
            enemy_path = os.path.join(ENEMY_SPRITES_PATH, "ghost")
        elif level == 4:
            enemy_path = os.path.join(ENEMY_SPRITES_PATH, "goblins")
        elif level == 5:
            enemy_path = os.path.join(ENEMY_SPRITES_PATH, "knights")
        elif level == 6:
            enemy_path = os.path.join(ENEMY_SPRITES_PATH, "wizard")
        elif level == 7:
            enemy_path = os.path.join(ENEMY_SPRITES_PATH, "demon")
        elif level == 8:
            enemy_path = os.path.join(ENEMY_SPRITES_PATH, "dragon")
        elif level == 9:
            enemy_path = os.path.join(ENEMY_SPRITES_PATH, "shadows")
        elif level == 10:
            enemy_path = os.path.join(ENEMY_SPRITES_PATH, "elfs")
        
        # Load enemy images - use a modified path key to avoid affecting game sprites
        if enemy_path and os.path.exists(enemy_path):
            for file in os.listdir(enemy_path):
                if file.endswith('.png') and not file.startswith('attack_') and not file.startswith('walk_') and not file.startswith('idle_'):
                    img_path = os.path.join(enemy_path, file)
                    try:
                        # Load the original image without scaling
                        original_img = pygame.image.load(img_path).convert_alpha()
                        # Create a copy for the artwork display
                        img = original_img.copy()
                        # Add to artwork images
                        self.artwork_images.append(img)
                    except Exception as e:
                        print(f"Failed to load enemy artwork: {img_path}, Error: {e}")
        
        # Load boss sprite - use a modified path key to avoid affecting game sprites
        boss_img_path = os.path.join(BOSS_SPRITES_PATH, f"boss_{level}.png")
        if os.path.exists(boss_img_path):
            try:
                # Load the original image without scaling
                original_boss_img = pygame.image.load(boss_img_path).convert_alpha()
                # Create a copy for the artwork display
                boss_img = original_boss_img.copy()
                # Add to artwork images
                self.artwork_images.append(boss_img)
            except Exception as e:
                print(f"Failed to load boss artwork: {boss_img_path}, Error: {e}")
    
    def handle_artworks_navigation(self, event):
        """Handle navigation in the artworks menu"""
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # Left mouse button
                # Check level navigation arrows 
                if self.left_level_arrow.rect.collidepoint(event.pos) and self.selected_level > 1:
                    self.selected_level -= 1
                    self.load_artwork_images(self.selected_level)
                    self.current_artwork_index = 0  # Reset to first image when changing levels
                    return f"level_{self.selected_level}"
                
                if self.right_level_arrow.rect.collidepoint(event.pos) and self.selected_level < 10:
                    self.selected_level += 1
                    self.load_artwork_images(self.selected_level)
                    self.current_artwork_index = 0  # Reset to first image when changing levels
                    return f"level_{self.selected_level}"
                
                # Check left/right navigation for images
                if len(self.artwork_images) > 0 and self.artwork_images:
                    # Get the current image dimensions and position
                    current_img = self.artwork_images[self.current_artwork_index]
                    display_area_width = WINDOW_WIDTH - 100
                    display_area_height = WINDOW_HEIGHT - 150
                    img_width, img_height = current_img.get_size()
                    
                    # Calculate scale factor to fit within display area
                    scale_w = display_area_width / img_width
                    scale_h = display_area_height / img_height
                    scale = min(scale_w, scale_h)
                    
                    # Get scaled dimensions
                    new_width = int(img_width * scale)
                    new_height = int(img_height * scale)
                    
                    # Position in center of display area
                    img_x = (WINDOW_WIDTH - new_width) // 2
                    img_y = 120 + (display_area_height - new_height) // 2
                    vert_center = img_y + new_height // 2
                    
                    # Create click areas for prev/next buttons
                    if len(self.artwork_images) > 1:
                        # Left navigation area (prev)
                        left_area = pygame.Rect(img_x - 100, vert_center - 30, 80, 60)
                        if left_area.collidepoint(event.pos) and self.current_artwork_index > 0:
                            self.current_artwork_index -= 1
                            return "prev_image"
                        
                        # Right navigation area (next)
                        right_area = pygame.Rect(img_x + new_width + 20, vert_center - 30, 80, 60)
                        if right_area.collidepoint(event.pos) and self.current_artwork_index < len(self.artwork_images) - 1:
                            self.current_artwork_index += 1
                            return "next_image"
        
        # Handle keyboard navigation
        elif event.type == pygame.KEYDOWN:
            # Left/right arrows for image navigation
            if event.key == pygame.K_LEFT and self.current_artwork_index > 0:
                self.current_artwork_index -= 1
                return "prev_image"
            elif event.key == pygame.K_RIGHT and self.current_artwork_index < len(self.artwork_images) - 1:
                self.current_artwork_index += 1
                return "next_image"
            
            # Up/down arrows for level navigation
            elif event.key == pygame.K_UP and self.selected_level < 10:
                self.selected_level += 1
                self.load_artwork_images(self.selected_level)
                self.current_artwork_index = 0  # Reset to first image when changing levels
                return f"level_{self.selected_level}"
            elif event.key == pygame.K_DOWN and self.selected_level > 1:
                self.selected_level -= 1
                self.load_artwork_images(self.selected_level)
                self.current_artwork_index = 0  # Reset to first image when changing levels
                return f"level_{self.selected_level}"
            
            # Number keys for direct level selection
            if event.key >= pygame.K_1 and event.key <= pygame.K_9:
                level = event.key - pygame.K_1 + 1
                if level <= 10:  # Make sure it's a valid level
                    self.selected_level = level
                    self.load_artwork_images(self.selected_level)
                    self.current_artwork_index = 0  # Reset to first image when changing levels
                    return f"level_{self.selected_level}"
            elif event.key == pygame.K_0:
                self.selected_level = 10
                self.load_artwork_images(self.selected_level)
                self.current_artwork_index = 0  # Reset to first image when changing levels
                return "level_10"
        
        return None

    def sync_audio_values(self):
        """Sync the audio slider values with the current sound manager settings"""
        sound_manager = get_sound_manager()
        self.music_volume = sound_manager.music_volume
        self.sfx_volume = sound_manager.sfx_volume
        
    def draw_audio_menu(self):
        """Draw the audio settings menu"""
        # Sync audio values with sound manager
        self.sync_audio_values()
        
        # Draw background
        self.screen.blit(self.menu_bg, (0, 0))
        
        # Draw title
        title = self.font.render("AUDIO SETTINGS", True, WHITE)
        title_rect = title.get_rect(center=(WINDOW_WIDTH // 2, 50))
        self.screen.blit(title, title_rect)
        
        # Draw music volume label and slider
        music_label = self.instruction_font.render("Music", True, (255, 255, 0))
        music_label_rect = music_label.get_rect(x=WINDOW_WIDTH // 4, y=120)
        self.screen.blit(music_label, music_label_rect)
        
        # Draw music volume slider
        slider_width = 200
        slider_height = 20
        slider_x = WINDOW_WIDTH // 2
        slider_y = 120
        
        # Draw slider background
        slider_bg = pygame.Rect(slider_x, slider_y, slider_width, slider_height)
        pygame.draw.rect(self.screen, (100, 100, 100), slider_bg)
        pygame.draw.rect(self.screen, (150, 150, 150), slider_bg, 2)
        
        # Draw slider fill based on volume
        fill_width = int(slider_width * self.music_volume)
        slider_fill = pygame.Rect(slider_x, slider_y, fill_width, slider_height)
        pygame.draw.rect(self.screen, (0, 200, 0), slider_fill)
        
        # Draw music volume percentage
        volume_text = self.instruction_font.render(f"{int(self.music_volume * 100)}%", True, WHITE)
        volume_rect = volume_text.get_rect(x=slider_x + slider_width + 10, y=slider_y)
        self.screen.blit(volume_text, volume_rect)
        
        # Draw SFX volume label and slider
        sfx_label = self.instruction_font.render("SFX", True, (255, 255, 0))
        sfx_label_rect = sfx_label.get_rect(x=WINDOW_WIDTH // 4, y=170)
        self.screen.blit(sfx_label, sfx_label_rect)
        
        # Draw SFX volume slider
        slider_y = 170
        
        # Draw slider background
        slider_bg = pygame.Rect(slider_x, slider_y, slider_width, slider_height)
        pygame.draw.rect(self.screen, (100, 100, 100), slider_bg)
        pygame.draw.rect(self.screen, (150, 150, 150), slider_bg, 2)
        
        # Draw slider fill based on volume
        fill_width = int(slider_width * self.sfx_volume)
        slider_fill = pygame.Rect(slider_x, slider_y, fill_width, slider_height)
        pygame.draw.rect(self.screen, (0, 200, 0), slider_fill)
        
        # Draw SFX volume percentage
        volume_text = self.instruction_font.render(f"{int(self.sfx_volume * 100)}%", True, WHITE)
        volume_rect = volume_text.get_rect(x=slider_x + slider_width + 10, y=slider_y)
        self.screen.blit(volume_text, volume_rect)
        
        # Ensure the current controller-selected button is highlighted
        active_buttons = ['back']
        if 0 <= self.selected_button_index < len(active_buttons):
            button_name = active_buttons[self.selected_button_index]
            self.buttons[button_name].is_hovered = True
        
        # Draw back button
        self.buttons['back'].draw(self.screen)
        
        # Store slider rects for interaction
        self.music_slider_rect = pygame.Rect(slider_x, 120, slider_width, slider_height)
        self.sfx_slider_rect = pygame.Rect(slider_x, 170, slider_width, slider_height)

    def handle_audio_menu_event(self, event):
        """Handle events specific to the audio menu"""
        if event.type == pygame.MOUSEBUTTONDOWN:
            mouse_pos = event.pos
            if self.music_slider_rect.collidepoint(mouse_pos):
                self.slider_dragging = 'music'
                # Update volume based on click position
                self.music_volume = (mouse_pos[0] - self.music_slider_rect.x) / self.music_slider_rect.width
                self.music_volume = max(0.0, min(1.0, self.music_volume))
                # Apply volume change immediately
                get_sound_manager().set_music_volume(self.music_volume)
                return True
            elif self.sfx_slider_rect.collidepoint(mouse_pos):
                self.slider_dragging = 'sfx'
                # Update volume based on click position
                self.sfx_volume = (mouse_pos[0] - self.sfx_slider_rect.x) / self.sfx_slider_rect.width
                self.sfx_volume = max(0.0, min(1.0, self.sfx_volume))
                # Apply volume change immediately
                sound_manager = get_sound_manager()
                sound_manager.sfx_volume = self.sfx_volume
                # Update volume of all loaded sounds
                for sound in sound_manager.sounds.values():
                    sound.set_volume(self.sfx_volume)
                return True
        elif event.type == pygame.MOUSEBUTTONUP:
            self.slider_dragging = None
        elif event.type == pygame.MOUSEMOTION and self.slider_dragging:
            mouse_pos = event.pos
            if self.slider_dragging == 'music':
                # Calculate new volume based on mouse position, clamped to slider bounds
                x_pos = max(self.music_slider_rect.left, min(mouse_pos[0], self.music_slider_rect.right))
                self.music_volume = (x_pos - self.music_slider_rect.x) / self.music_slider_rect.width
                self.music_volume = max(0.0, min(1.0, self.music_volume))
                # Apply volume change immediately
                get_sound_manager().set_music_volume(self.music_volume)
                return True
            elif self.slider_dragging == 'sfx':
                # Calculate new volume based on mouse position, clamped to slider bounds
                x_pos = max(self.sfx_slider_rect.left, min(mouse_pos[0], self.sfx_slider_rect.right))
                self.sfx_volume = (x_pos - self.sfx_slider_rect.x) / self.sfx_slider_rect.width
                self.sfx_volume = max(0.0, min(1.0, self.sfx_volume))
                # Apply volume change immediately
                sound_manager = get_sound_manager()
                sound_manager.sfx_volume = self.sfx_volume
                # Update volume of all loaded sounds
                for sound in sound_manager.sounds.values():
                    sound.set_volume(self.sfx_volume)
                return True
        return False

class HUD:
    def __init__(self, screen):
        self.screen = screen
        
        # Create a path to the pixelated font
        font_path = os.path.join(ASSET_PATH, "fonts/PixelatedEleganceRegular-ovyAA.ttf")
        if os.path.exists(font_path):
            self.font = pygame.font.Font(font_path, 24)
            print(f"Successfully loaded pixelated font for HUD")
        else:
            # Fallback to default font if the pixelated font is not available
            self.font = pygame.font.Font(None, 24)
            print(f"Pixelated font not found for HUD, using default font: {font_path}")
            
        self.asset_manager = get_asset_manager()
        
        # UI images
        self.health_bar_bg = None
        self.health_bar_alpha = None  # Alpha image for reference
        self.use_custom_health_bar = False
        self.sword_icon = None
        self.bow_icon = None
        self.sound_off_icon = None
        self.key_icon = None
        self.fire_sword_icon = None
        self.lightning_sword_icon = None
        
        # Health bar dimensions
        self.health_bar_width = 240  # Width of the health bar graphic
        self.health_bar_height = 80  # Height of the health bar graphic
        
        # Health and arrow bar positions and dimensions from the alpha reference
        self.health_bar_rect = pygame.Rect(42, 16, 100, 16)  # Default position and size
        self.arrow_bar_rect = pygame.Rect(42, 42, 100, 8)  # Default position and size
        
        # Minimap settings
        self.minimap_size = 10  # Size of each room on the minimap
        self.minimap_padding = 5
        
        # Try to load health bar texture
        try:
            health_bar_path = os.path.join(UI_SPRITES_PATH, "health_bar.png")
            if os.path.exists(health_bar_path):
                # Scale the health bar to an appropriate size
                self.health_bar_bg = self.asset_manager.load_image(health_bar_path, scale=(self.health_bar_width, self.health_bar_height))
                self.use_custom_health_bar = True
                print("Successfully loaded health bar image")
                
                # Try to load the alpha reference image for precise positioning
                alpha_path = os.path.join(UI_SPRITES_PATH, "health_bar_alpha.png")
                if os.path.exists(alpha_path):
                    self.health_bar_alpha = self.asset_manager.load_image(alpha_path, scale=(self.health_bar_width, self.health_bar_height))
                    print("Successfully loaded health bar alpha reference")
                    
                    # Parse the alpha reference to get exact positions
                    # The alpha image should have black areas where the bars should be placed
                    self._parse_alpha_reference()
        except Exception as e:
            print(f"Failed to load health bar texture: {e}")
            
        # Try to load weapon icons
        try:
            sword_icon_path = os.path.join(UI_SPRITES_PATH, "sword_icon.png")
            if os.path.exists(sword_icon_path):
                self.sword_icon = self.asset_manager.load_image(sword_icon_path, scale=(32, 32))
        except Exception as e:
            print(f"Failed to load sword icon: {e}")
            
        try:
            bow_icon_path = os.path.join(UI_SPRITES_PATH, "bow_icon.png")
            if os.path.exists(bow_icon_path):
                self.bow_icon = self.asset_manager.load_image(bow_icon_path, scale=(32, 32))
        except Exception as e:
            print(f"Failed to load bow icon: {e}")
            
        # Try to load fire sword icon
        try:
            fire_sword_icon_path = os.path.join(ASSET_PATH, "icons/fire_sword_icon.png")
            if os.path.exists(fire_sword_icon_path):
                self.fire_sword_icon = self.asset_manager.load_image(fire_sword_icon_path, scale=(32, 32))
                print("Successfully loaded fire sword icon")
        except Exception as e:
            print(f"Failed to load fire sword icon: {e}")
            
        # Try to load lightning sword icon
        try:
            lightning_sword_icon_path = os.path.join(ASSET_PATH, "icons/lightning_sword_icon.png")
            if os.path.exists(lightning_sword_icon_path):
                self.lightning_sword_icon = self.asset_manager.load_image(lightning_sword_icon_path, scale=(32, 32))
                print("Successfully loaded lightning sword icon")
        except Exception as e:
            print(f"Failed to load lightning sword icon: {e}")
            
        # Try to load key icon from UI sprites
        try:
            key_icon_path = os.path.join(ASSET_PATH, "icons/key.png")
            if os.path.exists(key_icon_path):
                self.key_icon = self.asset_manager.load_image(key_icon_path, scale=(32, 32))
                print("Successfully loaded key icon")
        except Exception as e:
            print(f"Failed to load key icon: {e}")
        
        # Try to load sound off icon
        try:
            sound_off_path = os.path.join(UI_SPRITES_PATH, "sound_off.png")
            if os.path.exists(sound_off_path):
                self.sound_off_icon = self.asset_manager.load_image(sound_off_path, scale=(24, 24))
            else:
                # Create a simple sound-off icon if not available
                self.sound_off_icon = pygame.Surface((24, 24), pygame.SRCALPHA)
                self.sound_off_icon.fill((0, 0, 0, 0))  # Transparent background
                pygame.draw.circle(self.sound_off_icon, (200, 200, 200), (12, 12), 10, 2)  # Circle
                pygame.draw.line(self.sound_off_icon, (200, 50, 50), (5, 5), (19, 19), 2)  # Red line across
        except Exception as e:
            print(f"Failed to load sound off icon: {e}")
            # Create a simple sound-off icon as fallback
            self.sound_off_icon = pygame.Surface((24, 24), pygame.SRCALPHA)
            self.sound_off_icon.fill((0, 0, 0, 0))  # Transparent background
            pygame.draw.circle(self.sound_off_icon, (200, 200, 200), (12, 12), 10, 2)  # Circle
            pygame.draw.line(self.sound_off_icon, (200, 50, 50), (5, 5), (19, 19), 2)  # Red line across
            
    def _parse_alpha_reference(self):
        """Parse the alpha reference image to find exact health and arrow bar positions"""
        if not self.health_bar_alpha:
            return
            
        # In health_bar_alpha.png, black areas (RGB: 0,0,0) represent where bars should be placed
        # We'll look for areas of consecutive black pixels for each row
        
        # Find areas for health bar (top section) and arrow bar (bottom section)
        health_row_detected = False
        arrow_row_detected = False
        
        health_y = None
        arrow_y = None
        
        # First pass: identify the y-positions of the health and arrow rows
        # Assuming the top black row is health, bottom black row is arrows
        for y in range(self.health_bar_height):
            black_count = 0
            for x in range(self.health_bar_width):
                color = self.health_bar_alpha.get_at((x, y))
                # Check for black (0,0,0)
                if color[0] == 0 and color[1] == 0 and color[2] == 0:
                    black_count += 1
            
            # If we have a substantial number of black pixels in this row,
            # it's likely part of a bar area
            if black_count > 30:  # Threshold to detect a bar row
                if not health_row_detected:
                    health_y = y
                    health_row_detected = True
                elif health_row_detected and not arrow_row_detected and y > health_y + 10:
                    # Found the second bar area (assume it's for arrows)
                    arrow_y = y
                    arrow_row_detected = True
        
        # If we found both rows, now find the horizontal extents and heights
        if health_y is not None and arrow_y is not None:
            # For health bar
            health_x_start = None
            health_width = 0
            health_height = 0
            
            # Scan health bar rows to find leftmost black pixel
            for y in range(health_y, min(health_y + 20, arrow_y if arrow_y else self.health_bar_height)):
                row_has_black = False
                for x in range(self.health_bar_width):
                    color = self.health_bar_alpha.get_at((x, y))
                    if color[0] == 0 and color[1] == 0 and color[2] == 0:
                        row_has_black = True
                        if health_x_start is None or x < health_x_start:
                            health_x_start = x
                        break
                if row_has_black:
                    health_height += 1
            
            # Find health bar width (rightmost black pixel minus leftmost)
            for x in range(self.health_bar_width - 1, health_x_start or 0, -1):
                for y in range(health_y, health_y + health_height):
                    if y < self.health_bar_height:
                        color = self.health_bar_alpha.get_at((x, y))
                        if color[0] == 0 and color[1] == 0 and color[2] == 0:
                            health_width = x - health_x_start + 1
                            break
                if health_width > 0:
                    break
            
            # For arrow bar
            arrow_x_start = None
            arrow_width = 0
            arrow_height = 0
            
            # Scan arrow bar rows to find leftmost black pixel
            for y in range(arrow_y, min(arrow_y + 20, self.health_bar_height)):
                row_has_black = False
                for x in range(self.health_bar_width):
                    color = self.health_bar_alpha.get_at((x, y))
                    if color[0] == 0 and color[1] == 0 and color[2] == 0:
                        row_has_black = True
                        if arrow_x_start is None or x < arrow_x_start:
                            arrow_x_start = x
                        break
                if row_has_black:
                    arrow_height += 1
            
            # Find arrow bar width (rightmost black pixel minus leftmost)
            for x in range(self.health_bar_width - 1, arrow_x_start or 0, -1):
                for y in range(arrow_y, arrow_y + arrow_height):
                    if y < self.health_bar_height:
                        color = self.health_bar_alpha.get_at((x, y))
                        if color[0] == 0 and color[1] == 0 and color[2] == 0:
                            arrow_width = x - arrow_x_start + 1
                            break
                if arrow_width > 0:
                    break
            
            # Store the detected rectangles
            if health_x_start is not None and health_height > 0 and health_width > 0:
                self.health_bar_rect = pygame.Rect(health_x_start, health_y, health_width, health_height)
                print(f"Found health bar rectangle: {self.health_bar_rect}")
            
            if arrow_x_start is not None and arrow_height > 0 and arrow_width > 0:
                self.arrow_bar_rect = pygame.Rect(arrow_x_start, arrow_y, arrow_width, arrow_height)
                print(f"Found arrow bar rectangle: {self.arrow_bar_rect}")
        
    def get_health_bar_position(self):
        """Helper method to get the health bar position for consistent placement"""
        return (10, 10)  # Standard top-left corner position
        
    def draw_minimap(self, level):
        """Draw a small map in the upper right corner showing room layout"""
        if not level or not hasattr(level, 'rooms') or not level.rooms:
            return  # Don't draw if level not available or initialized
            
        # Calculate bounds for centering
        min_x = min(x for x, y in level.rooms.keys())
        max_x = max(x for x, y in level.rooms.keys())
        min_y = min(y for x, y in level.rooms.keys())
        max_y = max(y for x, y in level.rooms.keys())
        
        width = max_x - min_x + 1
        height = max_y - min_y + 1
        
        # Position minimap in the upper right corner
        # Calculate minimap dimensions and position
        minimap_width = width * self.minimap_size + 2 * self.minimap_padding
        minimap_height = height * self.minimap_size + 2 * self.minimap_padding
        minimap_x = WINDOW_WIDTH - minimap_width - 10
        minimap_y = 10  # Top margin
        
        # Create the level text
        level_text = self.font.render(f"Level: {level.level_number}", True, WHITE)
        level_text_rect = level_text.get_rect()
        
        # Position the level text to the LEFT of the minimap
        level_text_rect.right = minimap_x - 10  # 10px spacing between text and minimap
        level_text_rect.top = minimap_y + (minimap_height // 2) - (level_text_rect.height // 2)  # Vertically center with the minimap
        
        # Draw background with slight transparency
        background_rect = pygame.Rect(
            minimap_x - self.minimap_padding,
            minimap_y - self.minimap_padding,
            minimap_width,
            minimap_height
        )
        # Create a surface with transparency
        bg_surface = pygame.Surface((background_rect.width, background_rect.height), pygame.SRCALPHA)
        bg_surface.fill((0, 0, 0, 180))  # Semi-transparent black
        self.screen.blit(bg_surface, (background_rect.x, background_rect.y))
        
        # Draw each room
        for (x, y), room in level.rooms.items():
            # Adjust for minimum coordinates
            adjusted_x = x - min_x
            adjusted_y = y - min_y
            
            # Calculate position
            room_x = minimap_x + adjusted_x * self.minimap_size
            room_y = minimap_y + adjusted_y * self.minimap_size
            
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
            if (x, y) == level.current_room_coords:
                # Draw current room marker
                pygame.draw.rect(self.screen, (255, 255, 255), 
                              (room_x, room_y, self.minimap_size, self.minimap_size))
                pygame.draw.rect(self.screen, color, 
                              (room_x + 1, room_y + 1, self.minimap_size - 2, self.minimap_size - 2))
            else:
                pygame.draw.rect(self.screen, color, 
                              (room_x, room_y, self.minimap_size, self.minimap_size))
                
            # Draw connections
            for direction, is_door in room.doors.items():
                if is_door:
                    # Draw a line indicating a connection
                    if direction == 'north' and (x, y - 1) in level.rooms:
                        pygame.draw.line(self.screen, (255, 255, 255),
                                       (room_x + self.minimap_size // 2, room_y),
                                       (room_x + self.minimap_size // 2, room_y - 1))
                    elif direction == 'south' and (x, y + 1) in level.rooms:
                        pygame.draw.line(self.screen, (255, 255, 255),
                                       (room_x + self.minimap_size // 2, room_y + self.minimap_size),
                                       (room_x + self.minimap_size // 2, room_y + self.minimap_size + 1))
                    elif direction == 'east' and (x + 1, y) in level.rooms:
                        pygame.draw.line(self.screen, (255, 255, 255),
                                       (room_x + self.minimap_size, room_y + self.minimap_size // 2),
                                       (room_x + self.minimap_size + 1, room_y + self.minimap_size // 2))
                    elif direction == 'west' and (x - 1, y) in level.rooms:
                        pygame.draw.line(self.screen, (255, 255, 255),
                                       (room_x, room_y + self.minimap_size // 2),
                                       (room_x - 1, room_y + self.minimap_size // 2))
        
        # Draw the level text to the left of the minimap
        self.screen.blit(level_text, level_text_rect)
        
    def draw_boss_health_bar(self, boss_health, boss_max_health, level_number=None):
        """Draw the boss health bar at the top of the screen"""
        # Draw background bar
        bar_width = 300
        bar_height = 20
        bar_x = (WINDOW_WIDTH - bar_width) // 2
        bar_y = 20
        
        # Background (dark red)
        pygame.draw.rect(self.screen, (100, 20, 20), (bar_x, bar_y, bar_width, bar_height))
        
        # Health percentage
        health_percent = boss_health / boss_max_health
        health_width = int(bar_width * health_percent)
        
        # Health bar color (bright red)
        health_color = (220, 0, 0)
        pygame.draw.rect(self.screen, health_color, (bar_x, bar_y, health_width, bar_height))
        
        # Draw border
        pygame.draw.rect(self.screen, (255, 255, 255), (bar_x, bar_y, bar_width, bar_height), 2)
        
        # Boss names dictionary
        boss_names = {
            1: "Vorthrax, the Eldritch Sovereign",
            2: "Nyx'tara, the Venomous Weaver",
            3: "Morg'roth, the Plague Harbinger",
            4: "Grak'tor, the Jade Warlord",
            5: "Kail'zar, the Void Blade",
            6: "Elysia, the Toxic Enchantress",
            7: "Azrathax, the Infernal Tyrant",
            8: "Drakor, the Crimson Overlord",
            9: "Nyxalith, the Shadow",
            10: "Git the Unclean Merger"
        }
        
        # Draw boss name above the health bar
        font = pygame.font.Font(None, 20)  # Reduced from 24 to 20
        boss_name = "BOSS"  # Default text
        if level_number and level_number in boss_names:
            boss_name = boss_names[level_number]
        text = font.render(boss_name, True, (255, 255, 255))
        text_rect = text.get_rect(center=(WINDOW_WIDTH // 2, bar_y - 10))
        self.screen.blit(text, text_rect)
    
    def draw_player_stats(self, player, level_number, has_key=False):
        """Draw player stats including health bar, arrow count, and key status"""
        # Draw health bar background
        if self.health_bar_bg:
            self.screen.blit(self.health_bar_bg, (10, 10))
        else:
            # Fallback if image not available
            pygame.draw.rect(self.screen, (50, 50, 50), (10, 10, 150, 60))
            
        # Create fallback health and arrow bar rects if not already defined
        if not hasattr(self, 'health_bar_rect') or self.health_bar_rect is None:
            # Default position and size for health bar
            self.health_bar_rect = pygame.Rect(42, 16, 100, 16)
            print("Using fallback health bar rectangle")
            
        if not hasattr(self, 'arrow_bar_rect') or self.arrow_bar_rect is None:
            # Default position and size for arrow bar
            self.arrow_bar_rect = pygame.Rect(42, 42, 100, 8)
            print("Using fallback arrow bar rectangle")
            
        # Adjust the positions to be relative to the health bar image position (10, 10)
        health_bar_x = 10 + self.health_bar_rect.x
        health_bar_y = 10 + self.health_bar_rect.y
        
        # Draw regular health portion (capped at player start health)
        regular_health = min(player.health, PLAYER_START_HEALTH)
        regular_health_percent = regular_health / PLAYER_START_HEALTH
        regular_health_width = int(self.health_bar_rect.width * regular_health_percent)
        
        # Choose color based on regular health percentage
        health_color = (0, 255, 0)  # Green
        if regular_health_percent < 0.5:
            health_color = (255, 255, 0)  # Yellow
        if regular_health_percent < 0.25:
            health_color = (255, 0, 0)  # Red
            
        # Draw regular health bar
        pygame.draw.rect(self.screen, health_color, 
                       (health_bar_x, health_bar_y, 
                       regular_health_width, self.health_bar_rect.height))
        
        # Display bonus health bar if player has more than starting health
        if player.max_health > PLAYER_START_HEALTH:
            # Calculate current bonus health (only if health exceeds starting health)
            bonus_health = max(0, player.health - PLAYER_START_HEALTH)
            
            # Scale relative to MAX_BONUS_HEALTH instead of current bonus max health
            # This makes each potion fill 10% of the bar (10/100)
            bonus_percent = bonus_health / MAX_BONUS_HEALTH
            bonus_width = int(self.health_bar_rect.width * bonus_percent)
            
            # Draw bonus health bar
            pygame.draw.rect(self.screen, BONUS_HEALTH_COLOR, 
                           (health_bar_x, health_bar_y, 
                           bonus_width, self.health_bar_rect.height))
            
            # Add sparkling effect to the bonus health bar
            if bonus_health > 0:
                # Get pulsing effect
                pulse = abs(math.sin(pygame.time.get_ticks() / 200))  # Faster pulsing
                
                # Create a glowing effect around the bonus health part
                if bonus_percent > 0.1:  # Only add glow if there's enough bonus health to see
                    # Draw multiple bars with decreasing alpha for glow
                    for i in range(2):  # Less intense glow than special attack
                        glow_alpha = int(100 * (1 - i * 0.3) * pulse)  # Fade out each layer
                        glow_surface = pygame.Surface((bonus_width + i*3, self.health_bar_rect.height + i*3), pygame.SRCALPHA)
                        glow_color = (20 + int(20 * pulse), 150 + int(50 * pulse), 50, glow_alpha)
                        pygame.draw.rect(glow_surface, glow_color, glow_surface.get_rect())
                        self.screen.blit(glow_surface, 
                                      (health_bar_x - i*1, health_bar_y - i*1))
                
                # Draw sparkle effects directly instead of using particles
                # Only add sparkles if bonus health is above certain threshold
                if bonus_percent > 0.3:
                    num_sparkles = max(1, int(3 * bonus_percent))  # More sparkles for higher bonus health
                    for _ in range(num_sparkles):
                        x = health_bar_x + random.random() * bonus_width
                        y = health_bar_y + random.randint(0, self.health_bar_rect.height)
                        sparkle_size = 1 + int(1 * pulse)
                        sparkle_color = (100 + int(155 * pulse), 255, 100 + int(155 * pulse), int(200 * pulse))
                        # Draw a simple sparkle using circles
                        pygame.draw.circle(self.screen, sparkle_color, (int(x), int(y)), sparkle_size)
                        # Add a cross shape for extra sparkle effect
                        pygame.draw.line(self.screen, sparkle_color, 
                                      (int(x - sparkle_size), int(y)), 
                                      (int(x + sparkle_size), int(y)), 1)
                        pygame.draw.line(self.screen, sparkle_color, 
                                      (int(x), int(y - sparkle_size)), 
                                      (int(x), int(y + sparkle_size)), 1)
        
        # Adjust the arrow bar positions to be relative to the health bar image position (10, 10)
        arrow_bar_x = 10 + self.arrow_bar_rect.x
        arrow_bar_y = 10 + self.arrow_bar_rect.y
        
        # Draw arrow count with yellow/gold color
        arrow_percent = min(1.0, player.arrow_count / player.max_arrows)
        arrow_width = int(self.arrow_bar_rect.width * arrow_percent)
        
        # Use gold/yellow color for arrow bar
        pygame.draw.rect(self.screen, (220, 180, 0),  # Gold/yellow color
                        (arrow_bar_x, arrow_bar_y, 
                        arrow_width, self.arrow_bar_rect.height))
        
        # Draw segmented markers for arrow count (1 segment per arrow)
        segment_width = 2
        segment_spacing = self.arrow_bar_rect.width / player.max_arrows
        for i in range(1, player.max_arrows):
            segment_x = arrow_bar_x + int(i * segment_spacing)
            # Only draw segment markers that are within the filled portion
            if segment_x <= arrow_bar_x + arrow_width:
                pygame.draw.line(self.screen, (180, 140, 0), 
                            (segment_x, arrow_bar_y), 
                            (segment_x, arrow_bar_y + self.arrow_bar_rect.height), 
                            segment_width)
        
        # Create and draw kill counter bar
        # Position it below the arrow bar
        kill_bar_height = 8
        kill_bar_y = arrow_bar_y + self.arrow_bar_rect.height + 6
        
        # Get kill counter from game instance
        kill_counter = 0
        kill_counter_max = 10
        if hasattr(player, 'kill_counter') and hasattr(player, 'kill_counter_max'):
            # Use values directly from player object if available
            kill_counter = player.kill_counter
            kill_counter_max = player.kill_counter_max
        elif hasattr(player, 'game') and player.game:
            # Fall back to game instance if player doesn't have these attributes
            kill_counter = player.game.kill_counter
            kill_counter_max = player.game.kill_counter_max
        
        # Draw kill counter bar background
        pygame.draw.rect(self.screen, (50, 50, 50), 
                         (arrow_bar_x, kill_bar_y, 
                         self.arrow_bar_rect.width, kill_bar_height))
        
        # Draw kill counter bar fill - use purple color for special attack
        kill_percent = min(1.0, kill_counter / kill_counter_max)
        kill_width = int(self.arrow_bar_rect.width * kill_percent)
        
        # Use purple color for special attack bar
        if kill_percent == 1.0:
            # Ready for special attack - enhanced pulsing effect
            pulse = abs(math.sin(pygame.time.get_ticks() / 200))  # Faster pulsing
            
            # Create a glowing effect when charged
            # Draw multiple bars with decreasing alpha for glow
            for i in range(3):
                glow_alpha = int(150 * (1 - i * 0.3) * pulse)  # Fade out each layer
                glow_surface = pygame.Surface((kill_width + i*4, kill_bar_height + i*4), pygame.SRCALPHA)
                glow_color = (200 + int(55 * pulse), 50 + int(50 * pulse), 255, glow_alpha)
                pygame.draw.rect(glow_surface, glow_color, glow_surface.get_rect())
                self.screen.blit(glow_surface, 
                               (arrow_bar_x - i*2, kill_bar_y - i*2))
            
            # Main bar with bright purple color
            bar_color = (200 + int(55 * pulse), 50 + int(150 * pulse), 255)  # Brighter purple pulse
            pygame.draw.rect(self.screen, bar_color,
                           (arrow_bar_x, kill_bar_y, kill_width, kill_bar_height))
            
            # Draw sparkle effects directly instead of using particles
            for _ in range(3):
                x = arrow_bar_x + kill_width * random.random()
                y = kill_bar_y + random.randint(-5, 5)
                sparkle_size = 2 + int(2 * pulse)
                sparkle_color = (255, 255, 255, int(200 * pulse))
                # Draw a simple sparkle using circles
                pygame.draw.circle(self.screen, sparkle_color, (int(x), int(y)), sparkle_size)
                # Add a cross shape for extra sparkle effect
                pygame.draw.line(self.screen, sparkle_color, 
                               (int(x - sparkle_size), int(y)), 
                               (int(x + sparkle_size), int(y)), 1)
                pygame.draw.line(self.screen, sparkle_color, 
                               (int(x), int(y - sparkle_size)), 
                               (int(x), int(y + sparkle_size)), 1)
        else:
            # Normal purple color while charging
            pygame.draw.rect(self.screen, (150, 50, 200),
                           (arrow_bar_x, kill_bar_y, kill_width, kill_bar_height))
        
        # Draw segmented markers for kill counter (1 segment per kill)
        segment_spacing = self.arrow_bar_rect.width / kill_counter_max
        for i in range(1, kill_counter_max):
            segment_x = arrow_bar_x + int(i * segment_spacing)
            # Draw all segment markers regardless of fill, as a guide
            pygame.draw.line(self.screen, (100, 30, 150),
                             (segment_x, kill_bar_y),
                             (segment_x, kill_bar_y + kill_bar_height),
                             1)  # Thinner line for kill segments
        
        # Add small "SP" label for special attack
        small_font = pygame.font.Font(None, 14)
        sp_text = small_font.render("SP", True, (200, 100, 255))
        self.screen.blit(sp_text, (arrow_bar_x - 22, kill_bar_y))
        
        # Draw key icon if player has key
        if has_key and self.key_icon:
            self.screen.blit(self.key_icon, (10, 76))  # Move down to accommodate new kill counter bar
    
    def draw_ui(self, player, level_number, audio_available=True, level=None, boss_health=None, boss_max_health=None, has_key=False, has_fire_sword=False, has_lightning_sword=False):
        """Draw all UI elements"""
        # Draw boss health if provided
        if boss_health is not None and boss_max_health is not None and boss_health > 0:
            self.draw_boss_health_bar(boss_health, boss_max_health, level_number)
            
        # Draw player stats
        self.draw_player_stats(player, level_number, has_key)
        
        # Draw special weapons (fire sword, lightning sword)
        self.draw_special_weapons(has_fire_sword, has_lightning_sword, has_key)
            
        # Draw sound status indicator if sound is disabled
        if not audio_available and self.sound_off_icon:
            self.screen.blit(self.sound_off_icon, (10, WINDOW_HEIGHT - 34))

    def draw_special_weapons(self, has_fire_sword=False, has_lightning_sword=False, has_key=False):
        """Draw special weapon indicators like fire sword"""
        # Draw fire sword icon if player has it
        if has_fire_sword:
            fire_sword_size = 32
            std_bar_width = 240  # Standard health bar width
            
            # Position the icon based on whether the player has a key
            bar_x, bar_y = self.get_health_bar_position()
            
            # Add more offset to account for the additional kill counter bar
            y_offset = 10
            if has_key:
                # If player has key, position to right of key icon
                fire_sword_x = bar_x + std_bar_width + 80  # Adjust as needed
                fire_sword_y = bar_y + y_offset
            else:
                # No key, position to right of health bar
                if self.use_custom_health_bar and self.health_bar_bg and self.health_bar_rect:
                    fire_sword_x = bar_x + self.health_bar_width + 10
                    fire_sword_y = bar_y + (self.health_bar_height // 2) - (fire_sword_size // 2) + y_offset
                else:
                    fire_sword_x = bar_x + std_bar_width + 20
                    fire_sword_y = bar_y + y_offset
            
            # Draw fire sword background glow with pulsing effect
            pulse = 0.5 + 0.5 * abs(math.sin(pygame.time.get_ticks() / 200))
            bg_size = fire_sword_size * 1.5
            bg_x = fire_sword_x - (bg_size - fire_sword_size) / 2
            bg_y = fire_sword_y - (bg_size - fire_sword_size) / 2
            
            # Create glowing background (orange/red for fire)
            bg_color = (255, 100, 0, int(100 * pulse))  # Fire glow with alpha
            bg_surface = pygame.Surface((bg_size, bg_size), pygame.SRCALPHA)
            pygame.draw.circle(bg_surface, bg_color, (bg_size//2, bg_size//2), bg_size//2)
            self.screen.blit(bg_surface, (bg_x, bg_y))
            
            # Draw the fire sword icon if available
            if self.fire_sword_icon:
                self.screen.blit(self.fire_sword_icon, (fire_sword_x, fire_sword_y))
            else:
                # Draw a custom fire sword icon if no image is available
                sword_icon = pygame.Surface((fire_sword_size, fire_sword_size), pygame.SRCALPHA)
                sword_icon.fill((0, 0, 0, 0))  # Transparent background
                
                # Draw sword body (vertical line)
                pygame.draw.rect(sword_icon, (200, 150, 50), (fire_sword_size//2-2, fire_sword_size//4, 4, fire_sword_size//2))
                
                # Draw sword hilt
                pygame.draw.rect(sword_icon, (150, 100, 50), (fire_sword_size//2-6, fire_sword_size//4+fire_sword_size//2, 12, 5))
                
                # Draw fire effect at the tip
                pygame.draw.polygon(sword_icon, (255, 100, 0), [
                    (fire_sword_size//2-4, fire_sword_size//4),
                    (fire_sword_size//2, fire_sword_size//8),
                    (fire_sword_size//2+4, fire_sword_size//4)
                ])
                
                self.screen.blit(sword_icon, (fire_sword_x, fire_sword_y))
            
            # Add fire sword label
            small_font = pygame.font.Font(None, 18)
            sword_text = small_font.render("FIRE", True, (255, 100, 0))
            sword_text_rect = sword_text.get_rect(center=(fire_sword_x + fire_sword_size//2, fire_sword_y + fire_sword_size + 8))
            self.screen.blit(sword_text, sword_text_rect)
            
        # Draw lightning sword icon if player has it
        if has_lightning_sword:
            lightning_sword_size = 32
            std_bar_width = 240  # Standard health bar width
            
            # Position the icon based on whether the player has other special items
            bar_x, bar_y = self.get_health_bar_position()
            
            if has_fire_sword:
                # If player has fire sword, position to right of it
                lightning_sword_x = bar_x + std_bar_width + 130  # Position after fire sword
                lightning_sword_y = bar_y
            elif has_key:
                # If player has key but no fire sword, position to right of key icon
                lightning_sword_x = bar_x + std_bar_width + 80
                lightning_sword_y = bar_y
            else:
                # No other special items, position to right of health bar
                if self.use_custom_health_bar and self.health_bar_bg and self.health_bar_rect:
                    lightning_sword_x = bar_x + self.health_bar_width + 10
                    lightning_sword_y = bar_y + (self.health_bar_height // 2) - (lightning_sword_size // 2)
                else:
                    lightning_sword_x = bar_x + std_bar_width + 20
                    lightning_sword_y = bar_y
            
            # Draw lightning sword background glow with pulsing effect
            pulse = 0.5 + 0.5 * abs(math.sin(pygame.time.get_ticks() / 150))  # Faster pulsing for lightning
            bg_size = lightning_sword_size * 1.5
            bg_x = lightning_sword_x - (bg_size - lightning_sword_size) / 2
            bg_y = lightning_sword_y - (bg_size - lightning_sword_size) / 2
            
            # Create glowing background (blue for lightning)
            bg_color = (100, 150, 255, int(100 * pulse))  # Blue glow with alpha
            bg_surface = pygame.Surface((bg_size, bg_size), pygame.SRCALPHA)
            pygame.draw.circle(bg_surface, bg_color, (bg_size//2, bg_size//2), bg_size//2)
            self.screen.blit(bg_surface, (bg_x, bg_y))
            
            # Draw the lightning sword icon if available
            if self.lightning_sword_icon:
                self.screen.blit(self.lightning_sword_icon, (lightning_sword_x, lightning_sword_y))
            else:
                # Draw a custom lightning sword icon if no image is available
                sword_icon = pygame.Surface((lightning_sword_size, lightning_sword_size), pygame.SRCALPHA)
                sword_icon.fill((0, 0, 0, 0))  # Transparent background
                
                # Draw sword body (vertical line)
                pygame.draw.rect(sword_icon, (200, 200, 220), (lightning_sword_size//2-2, lightning_sword_size//4, 4, lightning_sword_size//2))
                
                # Draw sword hilt
                pygame.draw.rect(sword_icon, (150, 150, 200), (lightning_sword_size//2-6, lightning_sword_size//4+lightning_sword_size//2, 12, 5))
                
                # Draw lightning effect at the tip
                for i in range(3):  # Draw multiple lightning bolts
                    offset = (i - 1) * 3
                    pygame.draw.line(sword_icon, (100, 150, 255), 
                                    (lightning_sword_size//2 + offset, lightning_sword_size//4),
                                    (lightning_sword_size//2 + offset - 2, lightning_sword_size//8),
                                    2)
                    pygame.draw.line(sword_icon, (100, 150, 255), 
                                    (lightning_sword_size//2 + offset - 2, lightning_sword_size//8),
                                    (lightning_sword_size//2 + offset + 2, lightning_sword_size//16),
                                    2)
                
                self.screen.blit(sword_icon, (lightning_sword_x, lightning_sword_y))
            
            # Add lightning sword label
            small_font = pygame.font.Font(None, 18)
            sword_text = small_font.render("LIGHTNING", True, (100, 150, 255))
            sword_text_rect = sword_text.get_rect(center=(lightning_sword_x + lightning_sword_size//2, lightning_sword_y + lightning_sword_size + 8))
            self.screen.blit(sword_text, sword_text_rect) 

    def draw(self, player, level_number, audio_available=True, level=None, boss_health=None, boss_max_health=None, has_key=False, has_fire_sword=False, has_lightning_sword=False):
        """Draw the HUD - compatibility method that calls draw_ui with all parameters"""
        # Draw the minimap if level is provided
        if level:
            self.draw_minimap(level)
        
        # Call the new draw_ui method with all parameters
        self.draw_ui(
            player,
            level_number,
            audio_available,
            level,
            boss_health,
            boss_max_health,
            has_key,
            has_fire_sword,
            has_lightning_sword
        ) 

    def render(self, player_health, player_max_health, arrow_count, max_arrows, kill_counter, kill_counter_max, level_number=1, level=None, boss_health=None, boss_max_health=None, has_key=False, has_fire_sword=False, has_lightning_sword=False):
        """Render the HUD - alias for compatibility with the new code using render instead of draw"""
        # Create a simplified player object with the stats we need
        class SimplePlayer:
            def __init__(self, health, max_health, arrow_count, max_arrows, kill_counter, kill_counter_max):
                self.health = health
                self.max_health = max_health
                self.arrow_count = arrow_count
                self.max_arrows = max_arrows
                self.kill_counter = kill_counter
                self.kill_counter_max = kill_counter_max
                
        player = SimplePlayer(player_health, player_max_health, arrow_count, max_arrows, kill_counter, kill_counter_max)
        
        # Call the existing draw method with our player object
        self.draw(
            player,
            level_number,
            True,  # audio_available
            level,
            boss_health,
            boss_max_health,
            has_key,
            has_fire_sword,
            has_lightning_sword
        )