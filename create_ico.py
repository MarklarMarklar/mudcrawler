import os
import sys
from PIL import Image  # Requires Pillow package (pip install Pillow)

def create_ico(input_path, output_path, sizes=[16, 32, 48, 64, 128, 256]):
    """
    Convert a PNG image to ICO format with multiple sizes
    
    Args:
        input_path: Path to the input PNG file
        output_path: Path to save the ICO file
        sizes: List of icon sizes to include
    """
    try:
        # Open the input image
        img = Image.open(input_path)
        
        # Create resized versions of the image
        resized_images = []
        for size in sizes:
            resized_img = img.resize((size, size), Image.LANCZOS)
            resized_images.append(resized_img)
        
        # Save as ICO
        resized_images[0].save(
            output_path, 
            format='ICO', 
            sizes=[(img.width, img.height) for img in resized_images],
            append_images=resized_images[1:]
        )
        
        print(f"Successfully created icon at {output_path}")
        return True
    except Exception as e:
        print(f"Error creating icon: {e}")
        return False

if __name__ == "__main__":
    # Default paths
    default_input = "assets/icons/fire_sword_icon.png"  # Example input
    default_output = "assets/icons/game_icon.ico"
    
    # Allow command line arguments
    input_path = sys.argv[1] if len(sys.argv) > 1 else default_input
    output_path = sys.argv[2] if len(sys.argv) > 2 else default_output
    
    # Make sure the output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Create the icon
    if create_ico(input_path, output_path):
        print(f"\nNow you can update mudcrawler.spec to use the icon:")
        print(f"    icon='{output_path}',") 