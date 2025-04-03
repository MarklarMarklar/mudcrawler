import re

# Remove debug print about mouse constraints in main.py
with open('scripts/main.py', 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace(
    'pygame.mouse.set_pos((constrained_x, constrained_y))\n            print(f"Mouse constrained from ({mouse_x}, {mouse_y}) to ({constrained_x}, {constrained_y})")',
    'pygame.mouse.set_pos((constrained_x, constrained_y))'
)

with open('scripts/main.py', 'w', encoding='utf-8') as f:
    f.write(content)

# Remove debug prints in player.py
with open('scripts/player.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Remove attack direction debug print
content = content.replace(
    'print(f"Attack direction: {self.attack_direction}, Setting facing to: {primary_direction}")',
    ''
)

# Remove speed debuff debug print
content = content.replace(
    'print("Speed debuff removed on player death")',
    ''
)

# Remove player speed restoration debug print
content = content.replace(
    'print(f"Player speed restored to {self._original_speed}")',
    ''
)

# Remove attack animation completion debug print
content = content.replace(
    'print(f"Attack animation complete. Returning facing from {self.facing} to {self.movement_facing}")',
    ''
)

with open('scripts/player.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Debug print statements removed successfully.") 