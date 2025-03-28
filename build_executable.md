# Building MudCrawler Executable

This document provides instructions on how to create an executable version of MudCrawler using PyInstaller.

## Prerequisites

Make sure you have all the required packages installed:

```bash
pip install -r requirements.txt
pip install pyinstaller pillow
```

## Creating an Icon (Optional)

To create a custom icon for your executable:

1. Run the `create_ico.py` script to convert a PNG to ICO format:

```bash
python create_ico.py assets/icons/fire_sword_icon.png assets/icons/game_icon.ico
```

2. After creating the icon, update the `mudcrawler.spec` file to reference it by uncommenting the `icon=` line and specifying the correct path.

## Building the Executable

There are two ways to build the executable:

### Method 1: Using the Updated Spec File (Recommended)

1. Run PyInstaller with the spec file:

```bash
pyinstaller mudcrawler.spec
```

2. The executable will be created in the `dist` directory.

### Method 2: Using the Bootstrap Script

If you're still having import issues, try this alternate method:

1. First build using the bootstrap script:

```bash
pyinstaller --onefile run_game.py --name MudCrawler
```

2. This creates a single file executable that ensures the game launches with the correct path settings.

## Testing the Executable

Before distributing, test that the executable works correctly:

1. Navigate to the `dist` directory
2. Run `MudCrawler.exe` (on Windows) or `./MudCrawler` (on Linux/Mac)
3. If there are any errors, check the console output (the spec file has been set with `console=True` to show errors)

## Troubleshooting

- **"No module named 'scripts'"**: This error indicates Python can't find the scripts package. Make sure you're using the updated spec file which includes proper path settings.

- **"ImportError" for any module**: Add the missing module to the `hiddenimports` list in the spec file.

- **Missing assets**: If game assets are missing in the executable, check the `datas` list in the spec file.

- **Blank screen or immediate crash**: 
  1. Run from the command line to see error messages
  2. Try setting `debug=True` in the spec file
  3. Check that all necessary DLLs are included

## Distribution

To distribute your game:

- For a single executable: Share the file in `dist/MudCrawler.exe` (Windows)
- For a directory with all files: Uncomment the `COLLECT` section in the spec file and distribute the entire `dist/MudCrawler` folder.

## Command Line Arguments

The executable supports the same command line arguments as the Python script:

```
MudCrawler.exe --fullscreen  # Start the game in fullscreen mode
``` 