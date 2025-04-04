import os

def modify_enemy_file():
    # Path to the enemy.py file
    file_path = 'scripts/enemy.py'
    
    # Read the entire file
    with open(file_path, 'r', encoding='utf-8') as file:
        lines = file.readlines()
    
    # Find the shoot_projectile method and modify the projectile creation
    in_shoot_projectile = False
    for i, line in enumerate(lines):
        if "def shoot_projectile(self, player):" in line:
            in_shoot_projectile = True
        elif in_shoot_projectile and "is_homing=True" in line:
            # Replace with conditional homing based on level
            lines[i] = "            is_homing=(self.level == 6),  # Only level 6 enemies have homing projectiles\n"
            break
    
    # Write the modified content back to the file
    with open(file_path, 'w', encoding='utf-8') as file:
        file.writelines(lines)

if __name__ == "__main__":
    try:
        modify_enemy_file()
        print("Successfully modified enemy.py to make level 2 projectiles non-homing")
    except Exception as e:
        print(f"Error modifying file: {e}") 