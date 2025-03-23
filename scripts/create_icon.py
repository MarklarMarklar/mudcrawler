from PIL import Image
import os

# Use one of the existing PNG files as the source
source_file = os.path.join('assets', 'icons', 'fire_sword_icon.png')
output_file = os.path.join('assets', 'icon.ico')

# Check if source file exists
if not os.path.exists(source_file):
    print(f"Source file {source_file} not found!")
    exit(1)

# Convert PNG to ICO
try:
    img = Image.open(source_file)
    icon_sizes = [(16, 16), (32, 32), (48, 48), (64, 64), (128, 128)]
    img.save(output_file, sizes=icon_sizes)
    print(f"Icon successfully created at {output_file}")
except Exception as e:
    print(f"Error creating icon: {e}") 