import PyInstaller.__main__
import os

# Adjust these variables for your program
PROGRAM_NAME = "abcd"
MAIN_SCRIPT = "main.py"  # Your program's entry point
ICON_PATH = "robo.ico"   # Optional: Path to your program's icon

PyInstaller.__main__.run([
    "new_ui.py",
    '--onefile',  # Create a single executable
    # '--windowed',  # For GUI applications (remove for console applications)
    # f'--icon={ICON_PATH}',  # Optional: Add an icon
    '--name', f'dockie_search',
    '--add-data', 'D:\SPECIAL\Documatic\gcpKey.json;.',
    '--add-data', 'D:\SPECIAL\Documatic\dockie;dockie',
    '--add-data', 'D:\SPECIAL\Documatic\dockie\data;dockie\data',
    # '--add-data', 'D:\SPECIAL\Documatic\dockiedrop\*;dockiedrop',
    # '--add-data', 'D:\SPECIAL\Documatic\icon.png;.',
    # '--add-data', 'D:\SPECIAL\Documatic\\new_ui.py;.',
    # '--add-data', 'D:\SPECIAL\Documatic\\new_ui2.py;.',
    '--clean',  # Clean PyInstaller cache and remove temporary files
    '--console',
    '--hidden-import=_ssl',
    '--hidden-import=cryptography',
    '--collect-all', 'certifi',
    '--add-binary','D:\SPECIAL\Documatic\libssl-3-x64.dll;.',
    '--add-binary','D:\SPECIAL\Documatic\libcrypto-3-x64.dll;.'
])

PyInstaller.__main__.run([
    "new_ui2.py",
    '--onefile',  # Create a single executable
    # '--windowed',  # For GUI applications (remove for console applications)
    # f'--icon={ICON_PATH}',  # Optional: Add an icon
    '--name', 'dockie_drop',
    '--add-data', 'D:\SPECIAL\Documatic\gcpKey.json;.',
    # '--add-data', 'D:\SPECIAL\Documatic\dockie\*;dockie',
    '--add-data', 'D:\SPECIAL\Documatic\dockiedrop;dockiedrop',
    '--add-data', 'D:\SPECIAL\Documatic\dockiedrop\data;dockiedrop\data',
    # '--add-data', 'D:\SPECIAL\Documatic\icon.png;.',
    # '--add-data', 'D:\SPECIAL\Documatic\\new_ui.py;.',
    # '--add-data', 'D:\SPECIAL\Documatic\\new_ui2.py;.',
    '--clean',  # Clean PyInstaller cache and remove temporary files
    '--console',
    '--hidden-import=_ssl',
    '--hidden-import=cryptography',
    '--collect-all', 'certifi',
    '--add-binary','D:\SPECIAL\Documatic\libssl-3-x64.dll;.',
    '--add-binary','D:\SPECIAL\Documatic\libcrypto-3-x64.dll;.'
])

PyInstaller.__main__.run([
    MAIN_SCRIPT,
    '--onefile',  # Create a single executable
    # '--windowed',  # For GUI applications (remove for console applications)
    f'--icon={ICON_PATH}',  # Optional: Add an icon
    '--name', f'{PROGRAM_NAME}',
    '--add-data', 'D:\SPECIAL\Documatic\gcpKey.json;.',
    # '--add-data', 'D:\SPECIAL\Documatic\dockie\*;dockie',
    # '--add-data', 'D:\SPECIAL\Documatic\dockiedrop\*;dockiedrop',
    '--add-data', 'D:\SPECIAL\Documatic\icon.png;.',
    '--add-data', 'D:\SPECIAL\Documatic\dist\dockie_search.exe;.',
    '--add-data', 'D:\SPECIAL\Documatic\dist\dockie_drop.exe;.',
    '--clean',  # Clean PyInstaller cache and remove temporary files
    '--console',
    '--hidden-import=_ssl',
    '--hidden-import=cryptography',
    '--collect-all', 'certifi',
    '--add-binary','D:\SPECIAL\Documatic\libssl-3-x64.dll;.',
    '--add-binary','D:\SPECIAL\Documatic\libcrypto-3-x64.dll;.'
])