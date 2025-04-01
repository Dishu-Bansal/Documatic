import time
import subprocess
import threading
from pynput import mouse
import win32gui
import win32process
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt, pyqtSlot, QThread, pyqtSignal, QObject, QEventLoop, QTimer
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
import wmi
import psutil
import logging, sys, os, certifi, ssl, requests, mimetypes, threading, signal, atexit

# def monitor_parent(poll_interval=1):
#     """
#     Monitor the parent process. If the parent process is no longer running,
#     exit the child process.
#     """
#     parent_pid = os.getppid()
#     while True:
#         # If parent process ID becomes 1 (or doesn't exist), it means the original parent is gone.
#         if parent_pid == 1 or not psutil.pid_exists(parent_pid):
#             print("Main process terminated. Exiting child process.")
#             break
#         time.sleep(poll_interval)
# Configure logging
logging.basicConfig(level=logging.DEBUG, 
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    handlers=[
                        logging.FileHandler("debug_log.txt"),
                        logging.StreamHandler()
                    ])

# Configure logging
logging.basicConfig(level=logging.DEBUG, 
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    handlers=[
                        logging.FileHandler("debug_log.txt"),
                        logging.StreamHandler()
                    ])

# Create QApplication before any other QT operations
app = QApplication(sys.argv)

c = wmi.WMI()
system_info = c.Win32_ComputerSystemProduct()[0]
id = system_info.UUID

url = ""

def configure_ssl():
    """Configure SSL certificate path for requests"""
    try:
        os.environ['REQUESTS_CA_BUNDLE'] = certifi.where()
        os.environ['SSL_CERT_FILE'] = certifi.where()
        ssl.create_default_context(cafile=certifi.where())
        requests.packages.urllib3.util.ssl_.DEFAULT_CERTS = certifi.where()
        logging.debug("SSL configuration completed successfully")
    except Exception as e:
        logging.error(f"SSL configuration error: {e}")

def get_resource_path(relative_path):
    """Get absolute path to resource, works for dev and PyInstaller."""
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

def setupAPI():
    global url
    configure_ssl()
    logging.info("Starting API setup")
    try:
        cred = credentials.Certificate(get_resource_path("gcpKey.json"))
        logging.info("Firebase credentials loaded successfully")

        app = firebase_admin.initialize_app(cred)
        logging.info("Firebase app initialized")

        db = firestore.client()
        logging.info("Firestore client created")

        doc_ref = db.collection("link").document("backend")
        doc = doc_ref.get()
        
        if doc.exists:
            url = doc.to_dict()['link'] + "/upload"
            logging.info(f"Backend URL retrieved: {url}")
            firebase_admin.delete_app(app)
        else:
            logging.error("Backend URL document not found!")
    except Exception as e:
        logging.error(f"API setup failed: {e}")

setupAPI()

def acquire_lock():
    lock_file = "dockie_drop.lock"
    if os.name == 'nt':
        try:
            fd = os.open(lock_file, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            os.close(fd)
            return True, lock_file
        except OSError:
            return False, lock_file
    else:
        import fcntl
        lock_fd = open(lock_file, 'w')
        try:
            fcntl.flock(lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            return True, lock_fd
        except IOError:
            lock_fd.close()
            return False, None

def release_lock(lock_handle):
    if os.name == 'nt':
        if os.path.exists(lock_handle):
            os.remove(lock_handle)
    else:
        import fcntl
        fcntl.flock(lock_handle, fcntl.LOCK_UN)
        lock_handle.close()
        if os.path.exists("dockie_drop.lock"):
            os.remove("dockie_drop.lock")

class APITask(QThread):
    """Handles API call to custom server"""
    # Define signals directly in the class
    completed = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self, message, file_path=None):
        super().__init__()
        self.message = message
        self.file_path = file_path
        logging.debug(f"APITask initialized with message: {message}")
        # self.moveToThread(QApplication.instance().thread())  # Ensure signals run in main thread

        
        # Ensure thread is terminated properly
        self.finished.connect(self.deleteLater)

    def run(self):
        """Make API call to custom server"""
        try:
            global url, id
            logging.debug(f"Running API Task - URL: {url}, Device ID: {id}")

            # Prepare multipart/form-data payload
            payload = {
                'id': id,
                'text': self.message,
                'path': self.file_path
            }

            # Prepare file if exists
            files = {}
            if self.file_path and os.path.exists(self.file_path):
                # Detect MIME type
                mime_type, _ = mimetypes.guess_type(self.file_path)
                
                # Add file to upload
                files['file'] = (os.path.basename(self.file_path), open(self.file_path, 'rb'), mime_type)

                # Make API call with file
                response = requests.post(
                    url, 
                    data=payload, 
                    files=files,
                    verify=False
                )
            else:
                # Make API call without file
                response = requests.post(
                    url, 
                    data=payload
                )

            # Check for successful response
            response.raise_for_status()

            # Extract response text
            api_response = response.text
            
            logging.debug(f"API Response: {api_response}")
            
            # CRITICAL: Emit the completed signal
            logging.debug("Attempting to emit completed signal")
            self.completed.emit(api_response)
            logging.debug("Completed signal emitted successfully")

        except requests.RequestException as e:
            error_msg = f"API Request Error: {str(e)}"
            logging.error(error_msg)
            self.error.emit(error_msg)
        except Exception as e:
            error_msg = f"Unexpected Error: {str(e)}"
            logging.error(error_msg)
            self.error.emit(error_msg)
        finally:
            # Ensure the thread terminates
            self.quit()

class LoopQuitter(QObject):
    loop = None

    def __init__(self, loop):
        super().__init__()
        self.loop = loop

    @pyqtSlot()
    def quit_loop(self):
        # This slot should be called in the main thread.
        self.loop.quit()

def process_search_query(search_query, path):
    logging.debug(f"Processing search query: {search_query}")
    
    # Create API task
    api_task = APITask(search_query, path)
    
    # Create an event loop to manage the thread
    loop = QEventLoop()
    
    # Connect signals with extensive logging
    # def log_complete(response):
    #     logging.debug(f"COMPLETE CALLBACK - Response: {response}")
    #     print(f"API Complete: {response}")
    #     # Exit the event loop
    #     QMetaObject.invokeMethod(quitter, "quit_loop", Qt.QueuedConnection)
    
    # def log_error(error):
    #     logging.error(f"ERROR CALLBACK - Error: {error}")
    #     print(f"API Error: {error}")
    #     # Exit the event loop
    #     QMetaObject.invokeMethod(quitter, "quit_loop", Qt.QueuedConnection)
    
    # Connect signals
    api_task.completed.connect(
        lambda response: (print(f"API Complete: {response}"), loop.quit()), 
        type=Qt.QueuedConnection
    )
    
    api_task.error.connect(
        lambda error: (print(f"API Error: {error}"), loop.quit()), 
        type=Qt.QueuedConnection
    )
    
    # Ensure thread finishes
    # api_task.finished.connect(lambda: QMetaObject.invokeMethod(quitter, "quit_loop", Qt.QueuedConnection))
    
    # Start the task
    logging.debug("Starting API task")
    api_task.start()
    
    # Set a timeout more safely
    timer = QTimer()
    timer.setSingleShot(True)
    timer.timeout.connect(loop.quit)
    timer.start(10000)  # 10-second timeout

    # Run the event loop with a timeout
    # QTimer.singleShot(10000, lambda: QMetaObject.invokeMethod(quitter, "quit_loop", Qt.QueuedConnection))  # 10-second timeout
    loop.exec_()

    # Clean up
    timer.stop()
    if api_task.isRunning():
        api_task.wait()  # Wait for thread to finish

flutter_exe_path = get_resource_path("dockiedrop/dockie_drop.exe")
flutter_process = None  # Store Flutter process

# Variables to track dragging
dragging = False
start_pos = None
drag_threshold = 10  # Minimum movement in pixels to consider as a drag
start_process_name = ""

def get_active_window_process_name():
    hwnd = win32gui.GetForegroundWindow()
    try:
        _, pid = win32process.GetWindowThreadProcessId(hwnd)
        proc = psutil.Process(pid)
        return proc.name()
    except Exception:
        return ""

def read_flutter_stdout(process):
    """Continuously read and print stdout from the flutter process."""
    while True:
        line = process.stdout.readline()
        if not line:
            # If process has terminated, break out
            if process.poll() is not None:
                break
            continue
        if line:
            if ";;" in line:
                print("FLUTTER STDOUT:", line.strip())
                s = line.strip().split(";;")[0]
                description = line.strip().split(";;")[1]
                # Remove the surrounding square brackets and then split by comma.
                items = s.strip("[]").split(',')

                # Strip whitespace from each item.
                lst = [item.strip() for item in items]
                for item in lst:
                    process_search_query(description if description else "", item)
                print("List is " + str(lst))
            else:
                continue

def launch_flutter():
    global flutter_process
    if not flutter_process:  # Ensure UI is launched only once
        flutter_process = subprocess.Popen(
            [flutter_exe_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        # Start a background thread to read stdout
        stdout_thread = threading.Thread(target=read_flutter_stdout, args=(flutter_process,), daemon=True)
        stdout_thread.start()
        print("Launched Flutter UI")

def on_click(x, y, button, pressed):
    global start_pos, dragging, start_process_name
    if pressed:
        # Record the initial position and source process name at press
        start_pos = (x, y)
        dragging = False
        start_process_name = get_active_window_process_name()
        print("Mouse pressed. Source process:", start_process_name)
    else:
        # On release, if dragging was detected, decide whether to keep or close Flutter UI
        if dragging:
            # Get the current cursor position (ensuring we use updated screen coordinates)
            pos = win32gui.GetCursorPos()  # returns (x, y)
            hwnd = win32gui.WindowFromPoint(pos)
            if hwnd:
                title = win32gui.GetWindowText(hwnd)
                print("Window under cursor:", title)
                if "FLUTTER" in title.upper():
                    print("Drop inside Flutter UI")
                else:
                    print("Title is", title)
                    print("Drop outside Flutter UI, closing UI")
                    close_flutter()
            else:
                print("No window detected under cursor, closing UI")
                close_flutter()
        # Reset state
        start_pos = None
        dragging = False
        start_process_name = ""

def on_move(x, y):
    global dragging, start_pos, start_process_name
    if start_pos is None:
        return
    if not dragging:
        dx = x - start_pos[0]
        dy = y - start_pos[1]
        distance = (dx**2 + dy**2) ** 0.5
        if distance > drag_threshold:
            # Check if the drag started from File Explorer (explorer.exe)
            if start_process_name.lower() == "explorer.exe":
                dragging = True
                print("File/Folder drag detected!")
                launch_flutter()
            else:
                print("Non-file drag detected; ignoring.")
                # Optionally, stop tracking this event by resetting start_pos
                start_pos = None

def close_flutter():
    global flutter_process, lock_handle
    if flutter_process:
        flutter_process.terminate()
        try:
            flutter_process.wait(timeout=3)
        except subprocess.TimeoutExpired:
            flutter_process.kill()
        flutter_process = None
        print("Closed Flutter UI")
    # release_lock(lock_handle)

def monitor_parent(poll_interval=1):
    parent_pid = os.getppid()
    while True:
        if parent_pid == 1 or not psutil.pid_exists(parent_pid):
            print("Main process terminated. Exiting child process.")
            close_flutter()
            sys.exit(0)
        time.sleep(poll_interval)

def signal_handler(sig, frame):
    print(f"Received signal {sig}. Cleaning up...")
    close_flutter()
    sys.exit(0)

# locked, lock_handle = acquire_lock()
# if not locked:
#     print("Another instance of dockie_drop is already running. Exiting.")
#     sys.exit(0)
signal.signal(signal.SIGTERM, signal_handler)
signal.signal(signal.SIGINT, signal_handler)
atexit.register(close_flutter)

monitor_thread = threading.Thread(target=monitor_parent, daemon=True, name="DockieDropParentMonitor")
monitor_thread.start()
# monitor_thread = threading.Thread(target=monitor_parent, daemon=True)
# monitor_thread.start()
# Listen for mouse events
with mouse.Listener(
    on_click=on_click,
    on_move=on_move,
) as listener:
    listener.join()