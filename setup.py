from setuptools import setup

setup(
    name="Documatic",
    version="1.0",
    description="Smart Document Assistant",
    author="Dishu Bansal",
    packages=["documatic"],  # Replace with your package name
    install_requires=[
        # List your dependencies here
        'sys',
        'os',
        'requests',
        'mimetypes',
        'tempfile',
        'shutil',
        'packaging',
        'json',
        'PyQt5',
        'pillow',
        'firebase_admin',
        'wmi',
        'certifi',
        'ssl',
        'logging',
        'traceback',
        'time',
        'psutil',
        'zipfile',
        'subprocess',
        'threading',
        'keyboard',
        'win32gui',
        'win32process',
        'pynput',
        'pystray'
    ],
)
