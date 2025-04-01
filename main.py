import multiprocessing
# multiprocessing.set_start_method('forkserver', force=True)
multiprocessing.freeze_support()
import time
import sys
import os
import requests
import shutil
import zipfile, requests
from packaging.version import Version
import psutil  # You may need to install this: pip install psutil
import pystray, threading, subprocess
from PIL import Image
import signal
import atexit

CURRENT_VERSION = Version("0.0.1")
METADATA_URL = "https://raw.githubusercontent.com/Dishu-Bansal/Documatic/refs/heads/main/update.json"
UPDATE_URL = None
process_names = []
identifier_ui = "--dockie_ui"          # Unique identifier for new_ui.py
identifier_ui2 = "--dockie_ui2"        # Unique identifier for new_ui2.py

def get_resource_path(relative_path):
    """Get absolute path to resource, works for dev and PyInstaller."""
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

def create_system_tray():
    # Load an icon (you should replace this with your app's icon)
    image = Image.open(get_resource_path("icon.png"))
    
    # Define what happens when the icon is clicked
    def on_clicked(icon, item):
        if str(item) == "Exit":
            icon.stop()
            # Add any cleanup code here before your application exits
            cleanup()
    
    # Create a menu with a few options
    menu = pystray.Menu(
        pystray.MenuItem("Show Status", lambda: print("Application is running")),
        pystray.MenuItem("Exit", on_clicked)
    )
    
    # Create the icon
    icon = pystray.Icon("abcd", image, "Icon", menu)
    
    # Run the icon - this will block, so we'll run it in a separate thread
    icon.run()

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

def download_update(url):
    print("Downloading Update...")
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()
        temp_exe = "new_abcd.exe"  # Temporary file for the new .exe
        with open(temp_exe, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        return temp_exe
    except Exception as e:
        print(f"Error downloading update: {e}")
        return None

def apply_update_and_restart(temp_exe):
    print("Applying Update and Restarting...")
    current_exe = sys.executable  # Path to the running abcd.exe
    
    if os.name == 'nt':  # Windows
        # Create a batch script to replace and restart
        bat_path = "update.bat"
        with open(bat_path, "w") as bat_file:
            bat_file.write(f"""@echo off
timeout /t 1 /nobreak >nul
move /y "{temp_exe}" "{current_exe}"
start "" "{current_exe}"
del "%~f0"
""")
        # Run the batch script in the background and exit
        os.system(f'start /b "" "{bat_path}"')
    else:  # Unix-like systems
        # Create a shell script to replace and restart
        sh_path = "update.sh"
        with open(sh_path, "w") as sh_file:
            sh_file.write(f"""#!/bin/bash
sleep 1
mv "{temp_exe}" "{current_exe}"
chmod +x "{current_exe}"
"{current_exe}" &
rm "{sh_path}"
""")
        os.system(f"chmod +x {sh_path}")
        os.system(f"sh {sh_path} &")
    
    # Exit the current process to allow replacement
    sys.exit(0)

def auto_update():
    global UPDATE_URL
    UPDATE_URL = check_for_updates()
    if UPDATE_URL:
        temp_exe = download_update(UPDATE_URL)
        if temp_exe:
            apply_update_and_restart(temp_exe)
    else:
        startDockie()

def launch_process_no_window(script_name, identifier):
    """Launch a separate process without a window using direct OS commands."""
    python_executable = sys.executable  # Use the current Python environment
    script_path = os.path.abspath(script_name)
    if os.name == 'nt':  # Windows
        # Using Windows-specific command to hide window
        # The /min argument minimizes the window, effectively hiding it
        # The /b argument starts the application without creating a new window
        command = f'start /b {script_path} {identifier}'
        print("Command is: " + str(command))
        exit_code = os.system(command)
        process_names.append(script_name)
        # subprocess.Popen([python_executable, script_path, identifier],
        #                creationflags=subprocess.DETACHED_PROCESS,
        #                close_fds=True)
        print(f"Launched {script_name} as a separate process with no window, exit code: {exit_code}")
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
    print(f"Trying to kill {script_name}")
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
            launch_process_no_window(script_name, identifier_ui if script_name is "new_ui.py" else identifier_ui2)

dockie_lock = threading.Lock()

def startDockie():
    try:
        with dockie_lock:
            launch_process_no_window(get_resource_path("dockie_search.exe"), identifier_ui)
            launch_process_no_window(get_resource_path("dockie_drop.exe"), identifier_ui2)
            print("All processes launched. Monitoring every 10 seconds.")
            while True:
                time.sleep(10)
    except Exception as e:
        print(f"Error in startDockie: {e}")

def background_task():
    # This is where your actual background application logic goes
    auto_update()

def cleanup():
    """Perform cleanup tasks (kill processes, release lock)."""
    kill_process_by_script(get_resource_path("dockie_search.exe"), identifier_ui)
    kill_process_by_script(get_resource_path("dockie_drop.exe"), identifier_ui2)
    release_lock(lock_handle)
    print("Cleanup completed.")

def signal_handler(sig, frame):
    """Handle termination signals."""
    print(f"Received signal {sig}. Performing cleanup...")
    cleanup()
    sys.exit(0)

def acquire_lock():
    """Attempt to acquire a lock file to ensure single instance."""
    lock_file = "abcd.lock"
    if os.name == 'nt':  # Windows
        try:
            # Create or open the lock file in write mode
            fd = os.open(lock_file, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            os.close(fd)
            return True, lock_file
        except OSError:
            return False, lock_file  # File exists, another instance is running
    else:  # Unix-like
        lock_fd = open(lock_file, 'w')
        try:
            fcntl.flock(lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            return True, lock_fd
        except IOError:
            lock_fd.close()
            return False, None

def release_lock(lock_handle):
    """Release the lock file."""
    if os.name == 'nt':
        if os.path.exists(lock_handle):
            os.remove(lock_handle)
    else:
        fcntl.flock(lock_handle, fcntl.LOCK_UN)
        lock_handle.close()
        if os.path.exists("abcd.lock"):
            os.remove("abcd.lock")


# Register signal handlers and atexit
if os.name == 'nt':
    signal.signal(signal.SIGTERM, signal_handler)
else:
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGHUP, signal_handler)  # Optional: handle terminal hangup on Unix
atexit.register(cleanup)  # Fallback for normal Python shutdown

if __name__ == "__main__":
    locked, lock_handle = acquire_lock()
    if not locked:
        print("Another instance is already running. Exiting.")
        sys.exit(0)
    
    try:
        print("Hello 2")
        ic = threading.Thread(target=create_system_tray, daemon=True)
        ic.start()
        auto_update()
        ic.join()
    except KeyboardInterrupt:
        print("Interrupted by Ctrl+C. Cleaning up...")
        cleanup()
    finally:
        cleanup()  # Ensure cleanup runs even on unhandled exceptions
    sys.exit(0)