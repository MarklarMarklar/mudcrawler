import pygame
import os
from config import *
from asset_manager import get_asset_manager

class Button:
    def __init__(self, x, y, width, height, text, font_size=36):
        self.asset_manager = get_asset_manager()
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.font = pygame.font.Font(None, font_size)
        
        # Create default button textures
        self.normal_image = pygame.Surface((width, height))
        self.normal_image.fill((100, 100, 100))
        pygame.draw.rect(self.normal_image, WHITE, pygame.Rect(0, 0, width, height), 2)
        
        self.hover_image = pygame.Surface((width, height))
        self.hover_image.fill((150, 150, 150))
        pygame.draw.rect(self.hover_image, WHITE, pygame.Rect(0, 0, width, height), 2)
        
        self.use_images = True
        
        # Try to load button textures if they exist
        try:
            normal_path = os.path.join(UI_SPRITES_PATH, "button_normal.png")
            hover_path = os.path.join(UI_SPRITES_PATH, "button_hover.png")
            
            if os.path.exists(normal_path) and os.path.exists(hover_path):
                self.normal_image = self.asset_manager.load_image(normal_path, scale=(width, height))
                self.hover_image = self.asset_manager.load_image(hover_path, scale=(width, height))
        except Exception as e:
            print(f"Failed to load button textures: {e}")
            
        self.text_color = WHITE
        self.is_hovered = False
        print(f"Button created: {text} at position {x}, {y} with size {width}x{height}")
        
    def draw(self, surface):
        # Draw button background
        image = self.hover_image if self.is_hovered else self.normal_image
        surface.blit(image, self.rect)
        
        # Draw button text
        text_surface = self.font.render(self.text, True, self.text_color)
        text_rect = text_surface.get_rect(center=self.rect.center)
        surface.blit(text_surface, text_rect)
        
    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            mouse_pos = pygame.mouse.get_pos()
            previous_hover = self.is_hovered
            self.is_hovered = self.rect.collidepoint(mouse_pos)
            
            # Debug print when hover state changes
            if previous_hover != self.is_hovered:
                if self.is_hovered:
                    print(f"Mouse hovering over {self.text} button")
                else:
                    print(f"Mouse left {self.text} button")
                    
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1 and self.rect.collidepoint(event.pos):  # Left click
                print(f"Button clicked: {self.text}")
                return True
        return False

class Menu:
    def __init__(self, screen):
        self.screen = screen
        self.font = pygame.font.Font(None, 48)
        self.asset_manager = get_asset_manager()
        
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
        
        # Game over custom image
        self.gameover_custom_img = None
        self.use_gameover_custom_img = False
            
        # Try to load menu background textures if they exist
        try:
            bg_path = os.path.join(UI_SPRITES_PATH, "menu_background.png")
            if os.path.exists(bg_path):
                self.menu_bg = self.asset_manager.load_image(bg_path, scale=(WINDOW_WIDTH, WINDOW_HEIGHT))
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
            
        # Try to load welcome screen image
        try:
            welcome_path = os.path.join(ASSET_PATH, "images/e9aa7981-5ad9-44cf-91d9-3f5e4c45b13d.png")
            if os.path.exists(welcome_path):
                self.welcome_screen = self.asset_manager.load_image(welcome_path, scale=(WINDOW_WIDTH, WINDOW_HEIGHT))
                self.use_welcome_screen = True
                print(f"Successfully loaded welcome screen: {welcome_path}")
            else:
                print(f"Welcome screen image not found: {welcome_path}")
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
        
        # Create buttons with more space between them
        button_width = 200
        button_height = 50
        center_x = WINDOW_WIDTH // 2 - button_width // 2
        
        # Position buttons more spread out
        self.buttons = {
            'start': Button(center_x, WINDOW_HEIGHT // 2, button_width, button_height, "Start Game"),
            'resume': Button(center_x, WINDOW_HEIGHT // 2, button_width, button_height, "Resume"),
            'restart': Button(center_x, WINDOW_HEIGHT // 2, button_width, button_height, "Restart"),
            'quit': Button(center_x, WINDOW_HEIGHT // 2 + 70, button_width, button_height, "Quit")
        }
        
        print("Menu initialized with buttons")
        
    def draw_main_menu(self):
        # Draw welcome screen if available, otherwise fallback to default background
        if self.use_welcome_screen and self.welcome_screen:
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
            
            # Draw subtitle
            subtitle = pygame.font.Font(None, 36).render("8-bit Dungeon Adventure", True, (200, 200, 200))
            subtitle_rect = subtitle.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 3 + 50))
            self.screen.blit(subtitle, subtitle_rect)
        
        # Draw buttons with enhanced visibility
        self.buttons['start'].draw(self.screen)
        self.buttons['quit'].draw(self.screen)
        
        # Draw instructions
        inst_text = pygame.font.Font(None, 24).render("Click START GAME or press ENTER to play", True, (255, 255, 0))
        inst_rect = inst_text.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT - 100))
        self.screen.blit(inst_text, inst_rect)
        
    def draw_pause_menu(self):
        # Semi-transparent overlay
        overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
        overlay.fill((0, 0, 0))
        overlay.set_alpha(128)
        self.screen.blit(overlay, (0, 0))
        
        # Draw title
        title = self.font.render("PAUSED", True, WHITE)
        title_rect = title.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 3))
        self.screen.blit(title, title_rect)
        
        # Draw buttons
        self.buttons['resume'].draw(self.screen)
        self.buttons['quit'].draw(self.screen)
        
    def draw_game_over(self):
        # Draw background
        if self.use_gameover_custom_img and self.gameover_custom_img:
            self.screen.blit(self.gameover_custom_img, (0, 0))
        else:
            self.screen.blit(self.gameover_bg, (0, 0))
        
        # Draw title (only if not using custom image, or make it more visible)
        if not self.use_gameover_custom_img or self.gameover_custom_img is None:
            title = self.font.render("GAME OVER", True, RED)
        else:
            # Create a better visible title for custom background
            title = self.font.render("GAME OVER", True, (255, 0, 0))
            
        title_rect = title.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 3))
        self.screen.blit(title, title_rect)
        
        # Draw buttons
        self.buttons['restart'].draw(self.screen)
        self.buttons['quit'].draw(self.screen)
        
    def draw_victory(self):
        # Draw background
        self.screen.blit(self.victory_bg, (0, 0))
        
        # Draw title
        title = self.font.render("VICTORY!", True, GREEN)
        title_rect = title.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 3))
        self.screen.blit(title, title_rect)
        
        # Draw message
        msg = self.font.render("Congratulations!", True, WHITE)
        msg_rect = msg.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2))
        self.screen.blit(msg, msg_rect)
        
        # Draw buttons
        self.buttons['restart'].draw(self.screen)
        self.buttons['quit'].draw(self.screen)
        
    def handle_event(self, event):
        for button_name, button in self.buttons.items():
            if button.handle_event(event):
                return button_name
        return None

class HUD:
    def __init__(self, screen):
        self.screen = screen
        self.font = pygame.font.Font(None, 36)
        self.asset_manager = get_asset_manager()
        
        # Create default health bar background
        self.health_bar_bg = pygame.Surface((200, 20))
        self.health_bar_bg.fill((100, 0, 0))
        pygame.draw.rect(self.health_bar_bg, WHITE, pygame.Rect(0, 0, 200, 20), 2)
        self.use_custom_health_bar = False
        
        # Create default weapon icons
        self.sword_icon = pygame.Surface((32, 32))
        self.sword_icon.fill((50, 50, 50))
        pygame.draw.rect(self.sword_icon, (200, 200, 200), pygame.Rect(8, 8, 16, 16))
        pygame.draw.line(self.sword_icon, (200, 200, 200), (16, 8), (16, 24), 2)
        
        self.bow_icon = pygame.Surface((32, 32))
        self.bow_icon.fill((50, 50, 50))
        pygame.draw.arc(self.bow_icon, (200, 200, 200), pygame.Rect(8, 4, 16, 24), 0.5, 5.8, 2)
        pygame.draw.line(self.bow_icon, (200, 200, 200), (16, 16), (24, 16), 2)
        
        self.use_weapon_icons = True
        
        # Try to load HUD elements if they exist
        try:
            health_bar_path = os.path.join(UI_SPRITES_PATH, "health_bar.png")
            if os.path.exists(health_bar_path):
                self.health_bar_bg = self.asset_manager.load_image(health_bar_path)
                self.use_custom_health_bar = True
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
        
    def draw(self, player, level_number):
        # Draw health bar
        health_width = 200
        health_height = 20
        health_x = 10
        health_y = 10
        
        health_ratio = max(0, min(1, player.health / PLAYER_START_HEALTH))
        
        if self.use_custom_health_bar:
            # Custom health bar implementation - depends on the image format
            # Assuming the image has a background and foreground layer
            self.screen.blit(self.health_bar_bg, (health_x, health_y))
            # Draw the foreground health portion based on current health
            health_rect = pygame.Rect(health_x + 4, health_y + 4, int((health_width - 8) * health_ratio), health_height - 8)
            pygame.draw.rect(self.screen, (0, 255, 0), health_rect)
        else:
            # Background
            pygame.draw.rect(self.screen, (100, 0, 0),
                          (health_x, health_y, health_width, health_height))
            # Health
            pygame.draw.rect(self.screen, (0, 255, 0),
                          (health_x, health_y, int(health_width * health_ratio), health_height))
            # Border
            pygame.draw.rect(self.screen, WHITE,
                          (health_x, health_y, health_width, health_height), 2)
        
        # Draw health text
        health_text = self.font.render(f"HP: {player.health}/{PLAYER_START_HEALTH}", True, WHITE)
        self.screen.blit(health_text, (health_x + health_width + 10, health_y))
        
        # Draw arrow count text next to the health text
        arrow_text = self.font.render(f"Arrows: {player.arrow_count}/{player.max_arrows}", True, WHITE)
        self.screen.blit(arrow_text, (health_x + health_width + 10, health_y + health_height + 10))
        
        # Draw level number
        level_text = self.font.render(f"Level: {level_number}", True, WHITE)
        self.screen.blit(level_text, (10, health_y + health_height + 10)) 