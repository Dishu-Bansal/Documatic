import PyInstaller.__main__
import os

# Adjust these variables for your program
PROGRAM_NAME = "Dockie"
MAIN_SCRIPT = "main.py"  # Your program's entry point
ICON_PATH = "robo.ico"   # Optional: Path to your program's icon

PyInstaller.__main__.run([
    MAIN_SCRIPT,
    '--onefile',  # Create a single executable
    # '--windowed',  # For GUI applications (remove for console applications)
    f'--icon={ICON_PATH}',  # Optional: Add an icon
    '--name', f'{PROGRAM_NAME}',
    '--add-data', 'D:\SPECIAL\Documatic\gcpKey.json;.',
    '--add-data', 'D:\SPECIAL\Documatic\dockie\*;dockie',
    '--add-data', 'D:\SPECIAL\Documatic\dockiedrop\*;dockiedrop',
    '--add-data', 'D:\SPECIAL\Documatic\icon.png;.',
    '--clean',  # Clean PyInstaller cache and remove temporary files
    '--console',
    '--hidden-import=_ssl',
    '--hidden-import=cryptography',
    '--collect-all', 'certifi',
    '--add-binary','D:\SPECIAL\Documatic\libssl-3-x64.dll;.',
    '--add-binary','D:\SPECIAL\Documatic\libcrypto-3-x64.dll;.'
])