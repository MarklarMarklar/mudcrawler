"""Script to fix the boss 6 homing projectile after teleport in enemy.py"""

def fix_boss6_projectile():
    with open('scripts/enemy.py', 'r') as file:
        content = file.read()
    
    # Find the teleport completion line
    teleport_complete_line = 'print(f"Boss 6 teleportation complete at time {current_time}")'
    
    # Check if we need to add the code (ensure we don't add it twice)
    if "# Shoot a projectile at the player when teleportation is complete" not in content:
        # Create the code to insert
        code_to_insert = '''                    # Shoot a projectile at the player when teleportation is complete
                    # Calculate normalized direction vector to player
                    dx = player.rect.centerx - self.rect.centerx
                    dy = player.rect.centery - self.rect.centery
                    length = math.sqrt(dx*dx + dy*dy)
                    
                    if length > 0:
                        # Normalize
                        dx = dx / length
                        dy = dy / length
                        
                        # Create a homing teleport projectile with a unique purple color
                        projectile = BossProjectile(
                            self.rect.centerx, 
                            self.rect.centery, 
                            (dx, dy), 
                            1.6,  # Slightly faster than Boss 2 projectiles
                            self.damage * 1.2,  # 20% more damage than normal
                            color=(160, 32, 240),  # Purple color for teleport projectile
                            is_homing=True,  # Enable homing behavior
                            boss_level=self.level  # Pass the boss level for animated projectiles
                        )
                        
                        # Store reference to player for homing
                        projectile.player_target = player
                        
                        # Enhance the trail effect
                        projectile.trail_enabled = True
                        projectile.max_trail_length = 12  # Longer trail for dramatic effect
                        projectile.trail_update_rate = 1   # Update every frame for smoother trail
                        
                        # Make it hunt the player more aggressively
                        projectile.homing_strength = 0.04  # More aggressive turning
                        projectile.max_homing_time = 5000  # Home for longer (5 seconds)
                        
                        # Increase projectile lifetime
                        projectile.max_distance = TILE_SIZE * 20  # Double the normal distance
                        
                        # Add to projectile group
                        self.projectiles.add(projectile)
                        
                        # Play a sound effect if available
                        self.sound_manager.play_sound("effects/projectile")
'''
        
        # Insert the code before the teleport complete print
        modified_content = content.replace(
            teleport_complete_line, 
            code_to_insert + "\n                    " + teleport_complete_line
        )
        
        with open('scripts/enemy.py', 'w') as file:
            file.write(modified_content)
        
        print("Added code for boss 6 to shoot a homing projectile after teleport")
    else:
        print("Boss 6 homing projectile code already exists")

if __name__ == "__main__":
    fix_boss6_projectile() 