#!/usr/bin/env python
"""
MudCrawler Game Launcher
This script ensures the game is launched from the correct directory with
proper import paths.
"""

import os
import sys
import argparse

# Add project root to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

# Add scripts directory to Python path
scripts_dir = os.path.join(project_root, 'scripts')
sys.path.insert(0, scripts_dir)

if __name__ == "__main__":
    # Change to the project root directory
    os.chdir(project_root)
    
    # Set up command line arguments
    parser = argparse.ArgumentParser(description='Mud Crawler Game')
    parser.add_argument('--fullscreen', action='store_true', help='Start in fullscreen mode')
    args = parser.parse_args()
    
    # Import the game module
    try:
        from scripts.main import Game
        print("Initializing Mud Crawler game via bootstrap launcher...")
        game = Game(start_fullscreen=args.fullscreen)
        game.run()
    except ImportError as e:
        print(f"Error importing game modules: {e}")
        print(f"Current directory: {os.getcwd()}")
        print(f"Python path: {sys.path}")
        sys.exit(1)
    except Exception as e:
        print(f"Error starting game: {e}")
        sys.exit(1) 