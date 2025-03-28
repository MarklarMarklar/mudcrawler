"""
Boss factory module for MudCrawler

This module handles the creation of bosses for different levels,
with special handling for the Level 10 boss (Dark Lord).
"""

from scripts.enemy import Boss
from scripts.dark_lord import DarkLord

def create_boss(x, y, level, level_instance=None):
    """
    Factory function to create the appropriate boss for each level
    
    Args:
        x: X position
        y: Y position
        level: Level number (1-10)
        level_instance: Reference to the level
        
    Returns:
        A boss instance for the given level
    """
    # Create special Dark Lord boss for level 10
    if level == 10:
        print(f"Creating Level 10 Dark Lord boss at ({x}, {y})")
        return DarkLord(x, y, level_instance)
    
    # Use normal boss class for other levels
    print(f"Creating Level {level} boss at ({x}, {y})")
    return Boss(x, y, level, level_instance) 