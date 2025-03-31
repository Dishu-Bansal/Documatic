import sys
import time
import subprocess
import requests
import os
import mimetypes
import logging
import certifi
import ssl, json
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QThread, pyqtSignal, QObject, QEventLoop, QTimer
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
import wmi
import keyboard
from frontend import FileToast

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
        else:
            logging.error("Backend URL document not found!")
    except Exception as e:
        logging.error(f"API setup failed: {e}")

setupAPI()

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

            print("Payload: " + str(payload))
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

def process_search_query(search_query):
    logging.debug(f"Processing search query: {search_query}")
    
    # Create API task
    api_task = APITask(search_query, "")
    
    # Create an event loop to manage the thread
    loop = QEventLoop()
    
    # Connect signals with extensive logging
    def log_complete(response):
        logging.debug(f"COMPLETE CALLBACK - Response: {response}")
        print(f"API Complete: {response}")
        res = json.loads(response)
        if 'got_file' in res:
            files = res['text']
            # score1, score2 = 0, 0
            # file1, file2 = "", ""
            # name1, name2 = "", ""
            
            # def get_first_number(string):
            #     import re
            #     match = re.search(r'\d+', string)
            #     return int(match.group()) if match else None
            
            # for file in files[:-1]:
            #     name, path, score = file.replace("(", "").replace(")", "").split(",")
            #     num = get_first_number(score)
            #     if num >= score1:
            #         score2, score1 = score1, num
            #         file2, file1 = file1, path.strip()
            #         name2, name1 = name1, name.strip()
            # return file1
            result = []
            if '1' in files:
                name1, path1, score1 = files['1']
                result += [path1]
            if '2' in files:
                name2, path2, score2 = files['2']
                result += [path2]
            if '3' in files:
                name3, path3, score3 = files['3']
                result += [path3]
            toast = FileToast(result)
            toast.show()
        # Exit the event loop
        loop.quit()
    
    def log_error(error):
        logging.error(f"ERROR CALLBACK - Error: {error}")
        print(f"API Error: {error}")
        # Exit the event loop
        loop.quit()
    
    # Connect signals
    api_task.completed.connect(log_complete)
    api_task.error.connect(log_error)
    
    # Ensure thread finishes
    api_task.finished.connect(loop.quit)
    
    # Start the task
    logging.debug("Starting API task")
    api_task.start()
    
    # Run the event loop with a timeout
    QTimer.singleShot(10000, loop.quit)  # 10-second timeout
    loop.exec_()

import time
import subprocess
import logging
import keyboard

# Constants
SHIFT_COUNT = 3
TIMEOUT = 0.6
MAX_PRESS_INTERVAL = 0.1  # Minimum time between distinct presses
MIN_PRESS_INTERVAL = 0.1  # Add a minimum to detect key holds (adjust as needed)

# Global variables
shift_presses = []
last_shift_press_time = 0
exe_path = get_resource_path("dockie/dockie.exe")

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

def on_shift_press(event):
    global shift_presses, last_shift_press_time
    current_time = time.time()

    # Calculate time since last press
    time_since_last = current_time - last_shift_press_time if last_shift_press_time else float('inf')

    # Log the event for debugging
    logging.debug(f"Shift press detected. Time since last: {time_since_last:.3f}s")

    # Only count as a distinct press if it's not a keypad event and not too fast (key hold)
    if not event.is_keypad and time_since_last > MAX_PRESS_INTERVAL:
        shift_presses.append(current_time)
        last_shift_press_time = current_time
        logging.debug(f"Valid press added. Total presses: {len(shift_presses)}")

        # Remove presses outside the timeout window
        shift_presses = [t for t in shift_presses if current_time - t < TIMEOUT]

        # Check if we have exactly 3 distinct presses within the timeout
        if len(shift_presses) == SHIFT_COUNT:
            logging.debug("Shift count threshold reached")
            print("Opening Dockie...")

            # Run the Flutter app and capture output
            try:
                result = subprocess.run(exe_path, shell=True, capture_output=True, text=True)
                search_query = result.stdout.strip()
                # Filter out Flutter debug output
                search_query = "\n".join(line for line in search_query.split("\n")
                                        if not line.startswith("flutter: The Dart VM service"))

                if search_query:
                    logging.debug(f"Search query obtained: {search_query}")
                    print(f"User searched: {search_query}")
                    # Process the search query (define this function as needed)
                    process_search_query(search_query)
            except Exception as e:
                logging.error(f"Error running Dockie: {e}")

            # Clear presses after successful trigger
            shift_presses.clear()
    elif time_since_last < MIN_PRESS_INTERVAL:
        # If presses are too close together, assume a key hold and reset
        logging.debug("Key hold detected, resetting presses")
        shift_presses.clear()
        last_shift_press_time = current_time

def main():
    logging.info("Application starting")
    keyboard.on_press_key("shift", on_shift_press)
    print("Listening for Shift key presses...")
    # Keep the application running
    keyboard.wait()

if __name__ == "__main__":
    main()