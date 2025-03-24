"""Script to fix the sound effect in enemy.py"""

def fix_sound_file():
    with open('scripts/enemy.py', 'r') as file:
        content = file.read()
    
    # Replace boss_attack with boss_special
    fixed_content = content.replace("play_sound('boss_attack')", "play_sound('boss_special')")
    
    with open('scripts/enemy.py', 'w') as file:
        file.write(fixed_content)
    
    print("Fixed sound file reference in enemy.py")

if __name__ == "__main__":
    fix_sound_file() 