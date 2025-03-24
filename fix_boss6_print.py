"""Fix the print statement in the summon_homing_projectiles method"""

def fix_print_statement():
    with open('scripts/enemy.py', 'r') as file:
        content = file.read()
    
    # Find and replace the incorrect print statement
    incorrect_print = 'print("Boss 7 is summoning homing projectiles!")'
    correct_print = 'print("Boss 6 is summoning homing projectiles!")'
    
    if incorrect_print in content:
        modified_content = content.replace(incorrect_print, correct_print)
        
        with open('scripts/enemy.py', 'w') as file:
            file.write(modified_content)
        
        print("Fixed the print statement in summon_homing_projectiles")
    else:
        print("Print statement already correct or not found")

if __name__ == "__main__":
    fix_print_statement() 