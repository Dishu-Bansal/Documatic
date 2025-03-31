import sys
import os
import requests
import shutil
import zipfile, requests
from packaging.version import Version
import time
import psutil  # You may need to install this: pip install psutil

CURRENT_VERSION = Version("0.0.3")
METADATA_URL = "https://raw.githubusercontent.com/Dishu-Bansal/Documatic/refs/heads/main/update.json"
UPDATE_URL = None
process_names = []
identifier_ui = "--dockie_ui"          # Unique identifier for new_ui.py
identifier_ui2 = "--dockie_ui2"        # Unique identifier for new_ui2.py

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

    def update_folder(name):
        # Check if the update has a top-level folder named "dockie"
        update_folder = os.path.join("update_temp", name)
        if os.path.isdir(update_folder):
            # Remove the existing "dockie" folder if it exists.
            if os.path.exists(name):
                shutil.rmtree(name)
            # Move the new folder in place.
            shutil.move(update_folder, name)
        else:
            # If there's no top-level folder named "dockie", move all extracted files.
            for item in os.listdir("update_temp"):
                src = os.path.join("update_temp", item)
                dst = item
                # Remove the destination if it already exists.
                if os.path.exists(dst):
                    if os.path.isdir(dst):
                        shutil.rmtree(dst)
                    else:
                        os.remove(dst)
                shutil.move(src, dst)
    update_folder("dockie")
    update_folder("dockiedrop")

    shutil.rmtree("update_temp")
    os.remove("update.zip")

def restart_main():
    print("Update Complete! Restarting...")
    python_executable = sys.executable  # Use the current Python environment
    # Use direct OS command
    os.system(f'"{python_executable}" "main.py"')
    sys.exit()

def auto_update():
    global UPDATE_URL
    UPDATE_URL = check_for_updates()
    if UPDATE_URL:
        if download_update():
            apply_update()
            restart_main()
    else:
        main()

def launch_process_no_window(script_name, identifier):
    """Launch a separate process without a window using direct OS commands."""
    python_executable = sys.executable  # Use the current Python environment
    script_path = os.path.abspath(script_name)
    
    if os.name == 'nt':  # Windows
        # Using Windows-specific command to hide window
        # The /min argument minimizes the window, effectively hiding it
        # The /b argument starts the application without creating a new window
        command = f'start /min /b "" "{python_executable}" "{script_path}" "{identifier}"'
        os.system(command)
        process_names.append(script_name)
        print(f"Launched {script_name} as a separate process with no window")
    else:  # macOS/Linux
        # Using nohup to make the process independent and redirect output
        command = f'nohup "{python_executable}" "{script_path}" > /dev/null 2>&1 &'
        os.system(command)
        process_names.append(script_name)
        print(f"Launched {script_name} as a separate process with no window")

def terminate_process(proc, timeout=5):
    try:
        proc.terminate()
        proc.wait(timeout=timeout)
        print(f"Process {proc.pid} terminated gracefully.")
    except psutil.TimeoutExpired:
        print(f"Process {proc.pid} did not exit in time; killing.")
        proc.kill()
    except Exception as e:
        print(f"Error terminating process {proc.pid}: {e}")

def kill_process_by_script(script_name, identifier):
    """
    Iterates through processes and terminates those whose command line
    contains both the script name and the unique identifier.
    """
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            cmdline = proc.info['cmdline']
            if cmdline and any(script_name in part for part in cmdline) and any(identifier in part for part in cmdline):
                print(f"Terminating process {proc.pid} running: {cmdline}")
                terminate_process(proc)
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue

def check_process_running(script_name):
    """Check if a Python process running the given script is active"""
    python_exe = os.path.basename(sys.executable)
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            # Check if this is a Python process
            if proc.info['name'] and python_exe in proc.info['name'].lower():
                # Check if it's running our script
                cmdline = proc.info['cmdline']
                if cmdline and any(script_name in cmd for cmd in cmdline):
                    return True
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
    return False

def monitor_processes():
    """Monitor the launched processes and restart them if needed"""
    for script_name in process_names:
        if not check_process_running(script_name):
            print(f"{script_name} is not running. Restarting...")
            launch_process_no_window(script_name)

def main():
    try:
        # Launch UI components as separate processes with no window
        launch_process_no_window("new_ui.py", identifier_ui)
        launch_process_no_window("new_ui2.py", identifier_ui2)
        
        print("All processes launched. Monitoring every 10 seconds. Press Ctrl+C to exit.")
        
        # Keep the main program running and periodically check processes
        while True:
            time.sleep(10)
            monitor_processes()
            
    except KeyboardInterrupt:
        print("Main program exiting. UI processes will continue running.")
        # Since we're using separate processes, they'll continue running
        # We could try to find and kill them here if desired
        # Kill the processes based on their script name and identifier
        kill_process_by_script("new_ui.py", identifier_ui)
        kill_process_by_script("new_ui2.py", identifier_ui2)

if __name__ == "__main__":
    auto_update()