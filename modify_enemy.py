import os

def modify_enemy_file():
    # Path to the enemy.py file
    file_path = 'scripts/enemy.py'
    
    # Read the entire file
    with open(file_path, 'r', encoding='utf-8') as file:
        lines = file.readlines()
    
    # Find and modify the line that sets can_shoot
    for i, line in enumerate(lines):
        if "self.can_shoot = level == 6" in line:
            # Replace with new condition that includes level 2
            lines[i] = "        self.can_shoot = level == 6 or level == 2  # Enable shooting for level 2 and 6 enemies\n"
            break
    
    # Write the modified content back to the file
    with open(file_path, 'w', encoding='utf-8') as file:
        file.writelines(lines)

if __name__ == "__main__":
    try:
        modify_enemy_file()
        print("Successfully modified enemy.py to enable projectile shooting for level 2 enemies")
    except Exception as e:
        print(f"Error modifying file: {e}") 