import PyInstaller.__main__
import os

# Adjust these variables for your program
PROGRAM_NAME = "Dockie"
MAIN_SCRIPT = "frontend.py"  # Your program's entry point
ICON_PATH = "robo.ico"   # Optional: Path to your program's icon

PyInstaller.__main__.run([
    MAIN_SCRIPT,
    '--onefile',  # Create a single executable
    '--windowed',  # For GUI applications (remove for console applications)
    f'--icon={ICON_PATH}',  # Optional: Add an icon
    '--name', f'{PROGRAM_NAME}',
    '--add-data', 'gcpKey.json;.',
    '--add-data', 'Animation 1/*;Animation 1',
    '--add-data', 'Animation 2/*;Animation 2',
    '--add-data', 'Animation 3/*;Animation 3',
    '--add-data', 'Animation 4/*;Animation 4',
    '--add-data', 'Animation 5/*;Animation 5',  # Optional: Include additional files
    '--clean',  # Clean PyInstaller cache and remove temporary files
    # '--console',
    '--hidden-import=_ssl',
    '--hidden-import=cryptography',
    '--collect-all', 'certifi',
    '--add-binary','D:\SPECIAL\Documatic\libssl-3-x64.dll;.',
    '--add-binary','D:\SPECIAL\Documatic\libcrypto-3-x64.dll;.'
])