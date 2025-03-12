import pygame
import sys
import os

# Add the parent directory to the path so we can import config
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import *
from player import Player
from level import Level
from weapons import WeaponManager
from ui import Menu, HUD
from asset_manager import get_asset_manager

class Game:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("Mud Crawler")
        
        # Debug: Print working directory
        print(f"Current working directory: {os.getcwd()}")
        print(f"Asset path: {ASSET_PATH}")
        print(f"Player sprites path: {PLAYER_SPRITES_PATH}")
        print(f"Absolute player sprites path: {os.path.abspath(PLAYER_SPRITES_PATH)}")
        
        # Set up display
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        self.clock = pygame.time.Clock()
        
        # Initialize asset manager first
        self.asset_manager = get_asset_manager()
        print("Asset manager initialized")
        
        # Check if assets directory exists, if not create it with necessary subdirectories
        self.ensure_asset_directories()
        
        # Debug font
        self.debug_font = pygame.font.Font(None, 24)
        
        # Game state
        self.running = True
        self.state = MENU
        self.current_level = 1
        self.max_levels = 10
        
        # State transition protection - prevents immediate weapon use after state change
        self.state_transition_time = pygame.time.get_ticks()
        self.state_transition_cooldown = 500  # 500ms cooldown after state change
        
        # Initialize UI first
        self.menu = Menu(self.screen)
        self.hud = HUD(self.screen)
        
        # Initialize game components
        self.player = Player(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2)
        self.weapon_manager = WeaponManager(self.player)
        
        # Level is initialized only when starting the game, not at menu
        self.level = None
        
        # Print debug info
        print(f"Game initialized. State: {self.state}")
        print(f"Screen size: {WINDOW_WIDTH}x{WINDOW_HEIGHT}")
        
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
            UI_SPRITES_PATH
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
        print("-" * 50)
        
    def reset_game(self):
        print("Resetting game...")
        self.current_level = 1
        # First initialize the level
        self.level = Level(self.current_level)
        # Then get a valid position for the player
        player_x, player_y = self.level.get_valid_player_start_position()
        self.player = Player(player_x, player_y)
        self.player.level = self.level  # Give player a reference to the level
        self.weapon_manager = WeaponManager(self.player)
        # Ensure any existing arrows are cleared
        self.weapon_manager.clear_arrows()
        
    def initialize_level(self):
        print(f"Initializing level {self.current_level}")
        self.level = Level(self.current_level)
        # Get a valid starting position for the player
        player_x, player_y = self.level.get_valid_player_start_position()
        self.player.rect.centerx = player_x
        self.player.rect.centery = player_y
        self.player.level = self.level  # Give player a reference to the level
        
    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                
            # Handle exit confirmation dialog if it's showing
            if self.level and self.level.show_exit_confirmation and event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # Left click
                    yes_rect, no_rect = self.level.draw_exit_confirmation(self.screen)
                    if yes_rect.collidepoint(event.pos):
                        print("Exit confirmed, proceeding to next level")
                        self.level.confirm_exit()
                    elif no_rect.collidepoint(event.pos):
                        print("Exit cancelled")
                        self.level.cancel_exit()
                continue  # Don't process other events while dialog is open
                
            # Handle menu button clicks
            button_clicked = self.menu.handle_event(event)
            if button_clicked:
                if button_clicked == 'start':
                    print("Start button clicked")
                    if self.level is None:
                        self.initialize_level()
                    self.state = PLAYING
                    # Set transition time to prevent immediate bow attack
                    self.state_transition_time = pygame.time.get_ticks()
                elif button_clicked == 'resume':
                    print("Resume button clicked")
                    self.state = PLAYING
                    # Set transition time to prevent immediate bow attack
                    self.state_transition_time = pygame.time.get_ticks()
                elif button_clicked == 'restart':
                    print("Restart button clicked")
                    self.reset_game()
                    self.state = PLAYING
                    # Set transition time to prevent immediate bow attack
                    self.state_transition_time = pygame.time.get_ticks()
                elif button_clicked == 'quit':
                    print("Quit button clicked")
                    self.running = False
                    
            if event.type == pygame.KEYDOWN:
                # Print debug info on key press
                print(f"Key pressed: {pygame.key.name(event.key)}")
                
                if event.key == pygame.K_ESCAPE:
                    if self.state == PLAYING:
                        print("Pausing game")
                        self.state = PAUSED
                    elif self.state == PAUSED:
                        print("Resuming game")
                        self.state = PLAYING
                        # Set transition time to prevent immediate bow attack
                        self.state_transition_time = pygame.time.get_ticks()
                elif event.key == pygame.K_RETURN:
                    if self.state == MENU:
                        print("Enter key pressed at menu")
                        if self.level is None:
                            self.initialize_level()
                        self.state = PLAYING
                        # Set transition time to prevent immediate bow attack
                        self.state_transition_time = pygame.time.get_ticks()
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
                elif event.key == pygame.K_p:
                    self.state = PLAYING
                    if self.level is None:
                        self.initialize_level()
                    print("Forced state change to PLAYING")
                    # Set transition time to prevent immediate bow attack
                    self.state_transition_time = pygame.time.get_ticks()
                # Exit key
                elif event.key == pygame.K_q:
                    self.running = False
                    
            if self.state == PLAYING:
                # Check if we're within the state transition cooldown period
                current_time = pygame.time.get_ticks()
                if current_time - self.state_transition_time < self.state_transition_cooldown:
                    # Skip weapon events during cooldown
                    continue
                    
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE:
                        self.weapon_manager.attack_sword()
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:  # Left click
                        self.weapon_manager.attack_bow(pygame.mouse.get_pos())
                        
    def update(self):
        if self.state != PLAYING:
            return
            
        # Ensure level is initialized
        if self.level is None:
            self.initialize_level()
            
        # Update player movement
        keys = pygame.key.get_pressed()
        self.player.move(keys)
        
        # Update player position if no collision
        old_rect = self.player.rect.copy()
        old_hitbox = self.player.hitbox.copy()
        self.player.update()
        
        # Check collision using the smaller hitbox instead of the full sprite rect
        if self.level.check_collision(self.player.hitbox):
            self.player.rect = old_rect
            self.player.hitbox = old_hitbox
            
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
                # Only heal if health is not full
                if self.player.health < PLAYER_START_HEALTH:
                    self.player.heal(health_amount)
                    print(f"Player healed for {health_amount} HP!")
                else:
                    print("Health is already full!")
        except Exception as e:
            print(f"Error checking health pickup: {e}")
                
        # Check for arrow pickups
        try:
            arrow_amount = self.level.check_arrow_pickup(self.player.hitbox)
            if arrow_amount > 0:
                # Add arrows to player inventory
                arrows_added = self.player.add_arrows(arrow_amount)
                print(f"Player picked up {arrow_amount} arrows! Now has {self.player.arrow_count}/{self.player.max_arrows} arrows.")
        except Exception as e:
            print(f"Error checking arrow pickup: {e}")
        
        # Get current room for entity interactions
        current_room = self.level.rooms[self.level.current_room_coords]
        
        # Check for sword collisions with destroyable walls
        if self.weapon_manager.sword.active:
            try:
                # Check walls in front of the player based on facing direction
                wall_tile_x, wall_tile_y = None, None
                
                # Get the tile in front of the player based on facing direction
                center_tile_x = self.player.rect.centerx // TILE_SIZE
                center_tile_y = self.player.rect.centery // TILE_SIZE
                
                if self.player.facing == 'right':
                    wall_tile_x = center_tile_x + 1
                    wall_tile_y = center_tile_y
                elif self.player.facing == 'left':
                    wall_tile_x = center_tile_x - 1
                    wall_tile_y = center_tile_y
                elif self.player.facing == 'up':
                    wall_tile_x = center_tile_x
                    wall_tile_y = center_tile_y - 1
                elif self.player.facing == 'down':
                    wall_tile_x = center_tile_x
                    wall_tile_y = center_tile_y + 1
                
                # Try to destroy the wall
                if wall_tile_x is not None and wall_tile_y is not None:
                    if self.level.try_destroy_wall(wall_tile_x, wall_tile_y):
                        print(f"Destroyed wall at {wall_tile_x}, {wall_tile_y}")
            except Exception as e:
                print(f"Error checking sword-wall collisions: {e}")
        
        # Check for arrow collisions with destroyable walls
        arrows_to_remove = []
        try:
            for arrow in self.weapon_manager.bow.arrows:
                try:
                    # Get the tile at the arrow's position
                    arrow_tile_x = arrow.rect.centerx // TILE_SIZE
                    arrow_tile_y = arrow.rect.centery // TILE_SIZE
                    
                    # Try to destroy the wall
                    if self.level.try_destroy_wall(arrow_tile_x, arrow_tile_y):
                        print(f"Destroyed wall at {arrow_tile_x}, {arrow_tile_y} with arrow")
                        # Mark the arrow for removal
                        arrows_to_remove.append(arrow)
                except Exception as e:
                    print(f"Error processing arrow-wall collision: {e}")
                    arrows_to_remove.append(arrow)
        except Exception as e:
            print(f"Error checking arrow-wall collisions: {e}")
            
        # Remove arrows that hit walls
        for arrow in arrows_to_remove:
            try:
                self.weapon_manager.bow.remove_arrow(arrow)
            except Exception as e:
                print(f"Error removing arrow after wall collision: {e}")
                
        # Check enemy collisions with weapons
        try:
            for enemy in current_room.enemies:
                # Check sword collisions
                if (self.weapon_manager.sword.active and 
                    self.weapon_manager.sword.rect.colliderect(enemy.rect)):
                    enemy.take_damage(SWORD_DAMAGE)
                    
                # Check arrow collisions with enemies
                arrows_to_remove = []
                for arrow in self.weapon_manager.bow.arrows:
                    try:
                        if arrow.rect.colliderect(enemy.rect):
                            enemy.take_damage(BOW_DAMAGE)
                            arrows_to_remove.append(arrow)
                            break
                    except Exception as e:
                        print(f"Error checking arrow-enemy collision: {e}")
                        arrows_to_remove.append(arrow)
                
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
            if current_room.boss and current_room.boss.health > 0:
                if (self.weapon_manager.sword.active and 
                    self.weapon_manager.sword.rect.colliderect(current_room.boss.rect)):
                    current_room.boss.take_damage(SWORD_DAMAGE)
                    
                # Check arrow collisions with boss
                arrows_to_remove = []
                for arrow in self.weapon_manager.bow.arrows:
                    try:
                        if arrow.rect.colliderect(current_room.boss.rect):
                            current_room.boss.take_damage(BOW_DAMAGE)
                            arrows_to_remove.append(arrow)
                            break
                    except Exception as e:
                        print(f"Error checking arrow-boss collision: {e}")
                        arrows_to_remove.append(arrow)
                
                # Remove arrows that hit the boss
                for arrow in arrows_to_remove:
                    try:
                        self.weapon_manager.bow.remove_arrow(arrow)
                    except Exception as e:
                        print(f"Error removing arrow after boss collision: {e}")
        except Exception as e:
            print(f"Error checking boss collisions: {e}")

        # Check if level is completed
        if self.level.completed:
            self.current_level += 1
            if self.current_level > self.max_levels:
                self.state = VICTORY
            else:
                # Clear any existing arrows before changing levels
                self.weapon_manager.clear_arrows()
                
                self.level = Level(self.current_level)
                # Place player on a valid floor tile in the new level
                player_x, player_y = self.level.get_valid_player_start_position()
                self.player.rect.centerx = player_x
                self.player.rect.centery = player_y
                
        # Check if player died
        if self.player.health <= 0:
            self.state = GAME_OVER
            
    def render(self):
        # Clear screen first
        self.screen.fill(BLACK)
        
        # Draw debug info
        state_text = self.debug_font.render(f"Game State: {self.state}", True, (255, 0, 0))
        self.screen.blit(state_text, (10, WINDOW_HEIGHT - 30))
        
        # Render based on game state
        if self.state == MENU:
            self.menu.draw_main_menu()
        elif self.state == PLAYING:
            self.render_game()
        elif self.state == PAUSED:
            self.render_game()  # Draw game state in background
            self.menu.draw_pause_menu()
        elif self.state == GAME_OVER:
            self.menu.draw_game_over()
        elif self.state == VICTORY:
            self.menu.draw_victory()
            
        # Actually update the display
        pygame.display.flip()
        
    def render_game(self):
        # Draw level
        if self.level:
            self.level.draw(self.screen)
        
        # Draw player
        self.player.draw(self.screen)
        
        # Draw weapons (EXCEPT arrows, which we'll draw last)
        if self.weapon_manager.sword.active:
            self.weapon_manager.weapon_sprites.draw(self.screen)
        
        # Draw HUD
        self.hud.draw(self.player, self.current_level)
        
        # Draw arrows LAST to ensure they're on top
        self.weapon_manager.bow.draw(self.screen)
        
        # Draw a debug message showing arrow count
        if self.player.arrow_count > 0:
            debug_font = pygame.font.Font(None, 24)
            debug_text = debug_font.render(f"Left-click to shoot ({self.player.arrow_count} arrows)", True, (255, 255, 0))
            self.screen.blit(debug_text, (10, 10))
        
    def run(self):
        print("Starting game loop")
        while self.running:
            self.handle_events()
            self.update()
            self.render()
            self.clock.tick(FPS)
            
        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    print("Initializing Mud Crawler game...")
    game = Game()
    game.run() 