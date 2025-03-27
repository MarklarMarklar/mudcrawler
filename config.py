# Window Settings
WINDOW_WIDTH = 800
WINDOW_HEIGHT = 600
TILE_SIZE = 32
FPS = 60

# Room Settings
ROOM_WIDTH = 25  # In tiles
ROOM_HEIGHT = 19  # In tiles

# Level Progression
EXIT_DOOR_TILE = 3  # Tile index for exit door
HAS_LEVEL_KEY = False  # Default state - player doesn't have key
EXIT_CONFIRMATION_TEXT = "Do you really want to proceed to the next level?"

# Colors
BLACK = (0, 0, 0  )
WHITE = (255, 255, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)
BROWN = (150, 75, 0)

# Asset Paths
import os
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ASSET_PATH = os.path.join(SCRIPT_DIR, "assets")
PLAYER_SPRITES_PATH = os.path.join(ASSET_PATH, "characters/player")
ENEMY_SPRITES_PATH = os.path.join(ASSET_PATH, "characters/enemies")
BOSS_SPRITES_PATH = os.path.join(ASSET_PATH, "characters/bosses")
WEAPON_SPRITES_PATH = os.path.join(ASSET_PATH, "weapons")
TILE_SPRITES_PATH = os.path.join(ASSET_PATH, "tiles")
UI_SPRITES_PATH = os.path.join(ASSET_PATH, "ui")
SOUNDS_PATH = os.path.join(ASSET_PATH, "sounds")

# Player Settings
PLAYER_START_HEALTH = 100
PLAYER_SPEED = 3.5  # Reduced from 5 to make player movement slower
SWORD_DAMAGE = 25
BOW_DAMAGE = 15
BOW_COOLDOWN = 1000  # milliseconds
SWORD_COOLDOWN = 500  # milliseconds

# Enemy Settings
ENEMY_TYPES = {
    'level1': {'name': 'Slime', 'health': 50, 'damage': 10, 'speed': 2},
    'level2': {'name': 'Skeleton', 'health': 60, 'damage': 12, 'speed': 2},
    'level3': {'name': 'Ghost', 'health': 40, 'damage': 2, 'speed': 2},
    'level4': {'name': 'Goblin', 'health': 70, 'damage': 30, 'speed': 2.5},
    'level5': {'name': 'Dark Knight', 'health': 80, 'damage': 23, 'speed': 2},
    'level6': {'name': 'Wizard', 'health': 65, 'damage': 15, 'speed': 1.8},
    'level7': {'name': 'Demon', 'health': 90, 'damage': 20, 'speed': 2},
    'level8': {'name': 'Dragon Spawn', 'health': 100, 'damage': 20, 'speed': 2},
    'level9': {'name': 'Shadow', 'health': 85, 'damage': 3, 'speed': 2.2},
    'level10': {'name': 'Dark Elf', 'health': 110, 'damage': 40, 'speed': 0.5}
}

# Boss Settings
BOSS_TYPES = {
    'level1': {'name': 'King Slime', 'health': 200, 'damage': 20, 'speed': 2},
    'level2': {'name': 'Skeleton Lord', 'health': 250, 'damage': 25, 'speed': 2},
    'level3': {'name': 'Phantom King', 'health': 300, 'damage': 5, 'speed': 2},
    'level4': {'name': 'Goblin Chief', 'health': 800, 'damage': 35, 'speed': 3},
    'level5': {'name': 'Dark Champion', 'health': 400, 'damage': 10, 'speed': 2},
    'level6': {'name': 'Arch Wizard', 'health': 450, 'damage': 15, 'speed': 2},
    'level7': {'name': 'Demon Lord', 'health': 500, 'damage': 10, 'speed': 2},
    'level8': {'name': 'Dragon', 'health': 550, 'damage': 8, 'speed': 2},
    'level9': {'name': 'Shadow King', 'health': 600, 'damage': 5, 'speed': 2},
    'level10': {'name': 'Dark Lord', 'health': 1, 'damage': 10, 'speed': 1}
}

# Game States
SPLASH_SCREEN = 'splash_screen'
MENU = 'menu'
PLAYING = 'playing'
PAUSED = 'paused'
GAME_OVER = 'game_over'
VICTORY = 'victory'

# Controls
CONTROLS = {
    'move_up': ['K_w', 'K_UP'],
    'move_down': ['K_s', 'K_DOWN'],
    'move_left': ['K_a', 'K_LEFT'],
    'move_right': ['K_d', 'K_RIGHT'],
    'attack_sword': ['K_SPACE'],
    'attack_bow': ['MOUSEBUTTONDOWN'],
    'special_attack': ['K_e'],
    'interact': ['K_e'],
    'pause': ['K_ESCAPE']
}

# Debug Settings
DEBUG_MODE = True  # Set to False for production
DEBUG_HITBOXES = True  # Set to True to show hitboxes 