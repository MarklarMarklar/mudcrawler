"""Script to fix the slow effect duration for boss 9 in enemy.py"""

def fix_slow_effect():
    with open('scripts/enemy.py', 'r') as file:
        content = file.read()
    
    # Find the end of the boss 9 poison trails section
    boss9_section_end = content.find("# Rest of boss update code", content.find("# Update Boss 9 poison trails"))
    
    # Check if we need to add the code
    check_code = "# Check if debuff should be removed - do this every frame"
    if check_code not in content[content.find("# Update Boss 9 poison trails"):boss9_section_end]:
        # Get the code to insert
        code_to_insert = """
            # Check if debuff should be removed - do this every frame
            if hasattr(player, '_original_speed') and hasattr(player, '_speed_debuff_end_time'):
                if current_time >= player._speed_debuff_end_time:
                    # Restore original speed
                    player.speed = player._original_speed
                    # Delete the end time so this only happens once per debuff
                    delattr(player, '_speed_debuff_end_time')
                    print("Player speed restored")"""
        
        # Insert the code before "# Rest of boss update code"
        before = content[:boss9_section_end]
        after = content[boss9_section_end:]
        new_content = before + code_to_insert + "\n        " + after
        
        with open('scripts/enemy.py', 'w') as file:
            file.write(new_content)
        
        print("Added code to remove slow effect for boss 9")
    else:
        print("Slow effect removal code already exists for boss 9")

if __name__ == "__main__":
    fix_slow_effect() 