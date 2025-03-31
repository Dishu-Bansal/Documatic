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
import traceback, zipfile, requests, subprocess
from packaging.version import Version

CURRENT_VERSION = Version("0.0.1")
METADATA_URL = "https://raw.githubusercontent.com/Dishu-Bansal/Documatic/refs/heads/main/update.json"
UPDATE_URL = None

def check_for_updates():
    try:
        response = requests.get(METADATA_URL)
        response.raise_for_status()
        metadata = response.json()
        latest_version = Version(metadata["version"])
        if latest_version > CURRENT_VERSION:
            print("New Version Available!")
            return metadata["url"]
        else:
            print("Everything Up-To-Date")
            return None
    except Exception as e:
        print(f"Error checking for updates: {e}")
        return None

def download_update():
    print("Downloading Update...")
    global UPDATE_URL
    response = requests.get(UPDATE_URL, stream=True)
    if response.status_code == 200:
        with open("update.zip", "wb") as f:
            f.write(response.content)
        return True
    return False

def apply_update():
    print("Applying Update...")
    with zipfile.ZipFile("update.zip", "r") as zip_ref:
        zip_ref.extractall("update_temp")

    for file in os.listdir("update_temp"):
        shutil.move(os.path.join("update_temp", file), file)

    shutil.rmtree("update_temp")
    os.remove("update.zip")

def restart_main():
    print("Update Complete! Restarting...")
    subprocess.Popen(["python", "main.py"])
    sys.exit()

def auto_update():
    global UPDATE_URL
    UPDATE_URL = check_for_updates()
    if UPDATE_URL:
        if download_update():
            apply_update()
            restart_main()

if __name__ == "__main__":
    auto_update()