import re

# Read the file
with open('ui.py', 'r') as f:
    content = f.read()

# Remove the level buttons creation section
pattern = r'# Create level buttons for artworks menu.*?self\.level_buttons\.append\(button\)\n'
updated_content = re.sub(pattern, '', content, flags=re.DOTALL)

# Write the updated content back to the file
with open('ui.py', 'w') as f:
    f.write(updated_content)

print("UI file updated successfully!") 