import sys
import os
import requests
import mimetypes
import json
import certifi
import tempfile
import shutil
import ssl
import logging
import traceback
from packaging.version import Version

Dockie_CURRENT_VERSION = Version("0.0.6")
Dockie_DROP_CURRENT_VERSION = Version("0.0.6")
Dockie_UI_CURRENT_VERSION = Version("0.0.6")
Dockie_DROP_UI_CURRENT_VERSION = Version("0.0.6")
METADATA_URL = "https://raw.githubusercontent.com/Dishu-Bansal/Documatic/refs/heads/main/update.json"

def check_for_updates():
    try:
        response = requests.get(METADATA_URL)
        response.raise_for_status()
        metadata = response.json()
        Dockie_LATEST_VERSION = Version(metadata["version"])
        Dockie_DROP_LATEST_VERSION = Version(metadata["version"])
        Dockie_UI_LATEST_VERSION = Version(metadata["version"])
        Dockie_DROP_UI_LATEST_VERSION = Version(metadata["version"])
        if latest_version > CURRENT_VERSION:
            return metadata["url"]
        else:
            return None
    except Exception as e:
        print(f"Error checking for updates: {e}")
        return None