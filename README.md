# Mud Crawler

A dungeon crawler game created in Cursor with Python and Pygame. Explore procedurally generated dungeons, battle enemies, and collect items as you progress through increasingly challenging levels.

## Features

- Procedurally generated dungeon levels
- Multiple enemy types with random textures
- Boss battles
- Weapons including sword and bow
- Special attacks with kill-counter mechanics
- Fire and lightning sword power-ups
- Destroyable walls that may contain health and arrow pickups
- Random textures for floors, walls, and enemies for visual variety
- In-game controls menu
- Minimap system to track room exploration

## Controls

- WASD or Arrow Keys: Move
- Left Mouse Button: Shoot arrow/Attack
- Right Mouse Button: Dodge
- E: Special Attack (when charged)
- Space: Melee/Sword attack
- ESC: Pause game
- F11: Toggle Fullscreen

## Requirements

- Python 3.x
- Pygame
- OpenCV (optional, for video playback)

## Installation

1. Clone this repository:
```
git clone https://github.com/MarklarMarklar/mudcrawler.git
```

2. Install the required dependencies:
```
pip install pygame
pip install opencv-python # Optional, for video playback
```

3. Run the game:
```
python scripts/main.py
```

## User Interface

- Main Menu: Start Game, Options, Quit
- Options Menu: Fullscreen toggle, Controls menu
- In-game HUD: Health bar, arrow count, special attack meter
- Minimap: Shows explored rooms and your current position

## Screenshots

![image](https://github.com/user-attachments/assets/72bb3fde-d0e8-47de-a25b-91e8fe50395b)
![image](https://github.com/user-attachments/assets/28e3f38c-7692-4c95-b978-ef3732e3112d)

## Development

This game is still in development. Future plans include:
- Additional enemy types
- More weapon varieties
- Enhanced visual effects
- Additional levels and boss types
