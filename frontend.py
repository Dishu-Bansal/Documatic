import sys
import os
import requests
import mimetypes
import json

from PyQt5.QtWidgets import (
    QApplication, QLabel, QMainWindow, QVBoxLayout, QLineEdit, QPushButton, QWidget, QDialog, QMessageBox
)
from PyQt5.QtCore import QTimer, Qt, QThread, pyqtSignal, QPropertyAnimation
from PyQt5.QtGui import QPixmap
from PIL import Image


class APITask(QThread):
    """Handles API call to custom server"""
    completed = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self, message, file_path):
        super().__init__()
        self.message = message
        self.file_path = file_path

    def run(self):
        """Make API call to custom server"""
        try:
            # Prepare the API endpoint
            url = "http://127.0.0.1:4998/upload"  # Replace with your actual server URL

            # Prepare multipart/form-data payload
            payload = {
                'text': self.message,
                'path': self.file_path
            }

            # Prepare file if exists
            files = {}
            if self.file_path is not None:
                if os.path.exists(self.file_path):
                    # Detect MIME type
                    mime_type, _ = mimetypes.guess_type(self.file_path)
                    
                    # Add file to upload
                    files['file'] = (os.path.basename(self.file_path), open(self.file_path, 'rb'), mime_type)

                    # Make API call
                    response = requests.post(
                        url, 
                        data=payload, 
                        files=files
                    )
            else:
                response = requests.post(
                        url, 
                        data=payload
                    )

            # Check for successful response
            response.raise_for_status()

            # Extract response text
            api_response = response.text
            self.completed.emit(api_response)

        except requests.RequestException as e:
            self.completed.emit("API Error")
            #self.error.emit(f"API Request Error: {str(e)}")
        except Exception as e:
            self.completed.emit("Unexpected Error")
            #self.error.emit(f"Unexpected Error: {str(e)}")

class TextInputDialog(QDialog):
    def __init__(self, parent=None, file_desc=False):
        super().__init__(parent)
        # Remove window frame and make background transparent
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)  # Remove margins
        
        # Text box styling
        self.text_input = QLineEdit()
        self.text_input.setPlaceholderText("What is the file about?" if file_desc else "What file are you looking for?")
        self.text_input.setStyleSheet("""
            QLineEdit {
                padding: 8px;
                border: 1px solid #ccc;
                border-radius: 4px;
                background-color: white;
                min-width: 300px;
            }
        """)
        
        # Connect key press events
        self.text_input.returnPressed.connect(self.accept)
        layout.addWidget(self.text_input)
        
        self.setLayout(layout)
    
    def get_message(self):
        return self.text_input.text()
    
    def keyPressEvent(self, event):
        # Handle Escape key
        if event.key() == Qt.Key_Escape:
            self.reject()
        # Let parent class handle other keys
        else:
            super().keyPressEvent(event)
    
    def showEvent(self, event):
        # Center the dialog relative to the parent
        if self.parent():
            parent_rect = self.parent().geometry()
            self.move(
                parent_rect.center().x() - self.width() // 2,
                parent_rect.center().y() - self.height() // 2
            )
        super().showEvent(event)
        # Force focus and activation
        self.text_input.setFocus(Qt.OtherFocusReason)
        self.activateWindow()
        self.text_input.activateWindow()

    def exec_(self):
        # Override exec_ to ensure proper focus
        self.text_input.setFocus(Qt.OtherFocusReason)
        self.activateWindow()
        self.text_input.activateWindow()
        return super().exec_()
# class TextInputDialog(QDialog):
#     def __init__(self, parent=None):
#         super().__init__(parent)
#         self.setWindowTitle("Enter Message")
#         self.setGeometry(100, 100, 300, 150)
        
#         layout = QVBoxLayout()
        
#         # Text box
#         self.text_input = QLineEdit()
#         self.text_input.setPlaceholderText("Enter your message here...")
#         layout.addWidget(self.text_input)
        
#         # Send button
#         send_button = QPushButton("Send")
#         send_button.clicked.connect(self.accept)
#         layout.addWidget(send_button)
        
#         # Cancel button
#         cancel_button = QPushButton("Cancel")
#         cancel_button.clicked.connect(self.reject)
#         layout.addWidget(cancel_button)
        
#         self.setLayout(layout)

class InteractiveAnimation(QLabel):
    def __init__(self, animation1_path, animation2_path, animation3_path, animation4_path, animation5_path):
        super().__init__()

        self.async_task = None
        self.async_task_completed = False 
        self.downloading_file = False
        self.api_task = None
        self.dragged_file_path = None
        self.found_file = [] 

        # Load animation files
        self.animation1_files = sorted(
            [os.path.join(animation1_path, f) for f in os.listdir(animation1_path) if f.endswith(".png")]
        )
        self.animation2_files = sorted(
            [os.path.join(animation2_path, f) for f in os.listdir(animation2_path) if f.endswith(".png")]
        )
        self.animation3_files = sorted(
            [os.path.join(animation3_path, f) for f in os.listdir(animation3_path) if f.endswith(".png")]
        )
        self.animation4_files = sorted(
            [os.path.join(animation4_path, f) for f in os.listdir(animation4_path) if f.endswith(".png")]
        )
        self.animation5_files = sorted(
            [os.path.join(animation5_path, f) for f in os.listdir(animation5_path) if f.endswith(".png")]
        )

        # Verify image files
        for file_list in [
            self.animation1_files, self.animation2_files, 
            self.animation3_files, self.animation4_files, 
            self.animation5_files
        ]:
            for file_name in file_list:
                try:
                    with Image.open(file_name) as img:
                        img.verify()  # Verifies if the file is intact
                except Exception as e:
                    print(f"Error with {file_name}: {e}")
        
        # Enum for animation states
        self.AnimationState = type('AnimationState', (), {
            'IDLE': 0,
            'DRAGGING_FORWARD': 1, 
            'DRAGGING_REVERSE': 2,
            'ANIMATION1_FORWARD': 3,
            'ANIMATION1_REVERSE': 4,
            'ANIMATION2_FORWARD': 5,
            'ANIMATION2_REVERSE': 6,
            'WAITING_TEXT_INPUT': 7,
            'ANIMATION3_FORWARD': 8,
            'ANIMATION3_REVERSE': 9,
            'ANIMATION4_REPEAT': 10,
            'ANIMATION5_FORWARD': 11,
            'ANIMATION5_REVERSE': 12
        })

        # Initial state setup
        self.current_state = self.AnimationState.IDLE
        self.current_animation = self.animation1_files
        self.current_frame = 0
        self.total_frames = len(self.current_animation)
        self.dragged_file_path = None
        
        self.async_task = None

        # Configure the transparent window
        self.setFixedSize(600, 300)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WA_NoSystemBackground, True)

        self.label = QLabel(self)
        self.label.setFixedSize(600, 300)
        
        # Set up animation timer
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_animation)
        self.timer.start(1)  # Slower frame rate for smoother animation
        
        # Enable drag-and-drop
        self.setAcceptDrops(True)
        
        # Initialize display with the first frame of animation 1
        self.set_frame(0)

        # Position at top-right corner
        screen_geometry = QApplication.primaryScreen().geometry()
        self.move(screen_geometry.width() - self.width(), 0)

    def set_frame(self, frame):
        """Update the QLabel to show the specified frame."""
        try:
            pixmap = QPixmap(self.current_animation[frame])
            scaled_pixmap = pixmap.scaled(600, 300, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.label.setPixmap(scaled_pixmap)
        except IndexError:
            print(f"Frame {frame} not found in the sequence.")
        except Exception as e:
            print(f"Error loading frame {frame}: {e}")

    def update_animation(self):
        """Control animation frames based on state."""
        if self.current_state == self.AnimationState.IDLE:
            # Stay at first frame of animation 1
            self.current_animation = self.animation1_files
            self.current_frame = 0
            self.set_frame(self.current_frame)

        elif self.current_state == self.AnimationState.DRAGGING_FORWARD:
            # Animate forward during drag
            if self.current_frame < self.total_frames - 1:
                self.current_frame += 1
                self.set_frame(self.current_frame)
            # Hold at last frame when fully dragged
            else:
                self.current_frame = self.total_frames - 1
                self.set_frame(self.current_frame)

        elif self.current_state == self.AnimationState.DRAGGING_REVERSE:
            # Animate reverse during drag out
            if self.current_frame > 0:
                self.current_frame -= 1
                self.set_frame(self.current_frame)
            # Back to idle when fully reversed
            else:
                self.current_state = self.AnimationState.IDLE

        elif self.current_state == self.AnimationState.ANIMATION1_FORWARD:
            # Play animation 1 forward
            if self.current_frame < self.total_frames - 1:
                self.current_frame += 1
                self.set_frame(self.current_frame)
            else:
                # Reached end of animation 1
                self.trigger_drop_event()

        elif self.current_state == self.AnimationState.ANIMATION1_REVERSE:
            # Reverse animation 1
            if self.current_frame > 0:
                self.current_frame -= 1
                self.set_frame(self.current_frame)
            else:
                self.current_state = self.AnimationState.IDLE
                if self.downloading_file:
                    self.downloading_file = False
                    # if self.found_file:
                    #     if os.path.isfile(self.found_file):
                    #         os.startfile(self.found_file)
                    #         self.found_file = ""
                    if len(self.found_file) > 0:
                        toast = FileToast(self.found_file)
                        toast.show()

        elif self.current_state == self.AnimationState.ANIMATION2_FORWARD:
            # Play animation 2 forward
            if self.current_frame < self.total_frames - 1:
                self.current_frame += 1
                self.set_frame(self.current_frame)
            else:
                # Reached end of animation 2, show text input
                self.show_text_input(True)

        elif self.current_state == self.AnimationState.ANIMATION2_REVERSE:
            # Reverse animation 2
            if self.current_frame > 0:
                self.current_frame -= 1
                self.set_frame(self.current_frame)
            else:
                # Fully reversed animation 2, reset to animation 1
                self.current_state = self.AnimationState.ANIMATION1_REVERSE
                self.current_animation = self.animation1_files
                self.total_frames = len(self.current_animation)
                self.current_frame = self.total_frames - 1
        
        elif self.current_state == self.AnimationState.ANIMATION3_FORWARD:
            # Play animation 3 forward
            if self.current_frame < self.total_frames - 1:
                self.current_frame += 1
                self.set_frame(self.current_frame)
            else:
                # Reached end of animation 3, start animation 4 repeat
                self.current_state = self.AnimationState.ANIMATION4_REPEAT
                self.current_animation = self.animation4_files
                self.total_frames = len(self.current_animation)
                self.current_frame = 0
        
        elif self.current_state == self.AnimationState.ANIMATION3_REVERSE:
            # Reverse animation 2
            if self.current_frame > 0:
                self.current_frame -= 1
                self.set_frame(self.current_frame)
            else:
                # Fully reversed animation 2, reset to animation 1
                self.current_state = self.AnimationState.ANIMATION2_REVERSE
                self.current_animation = self.animation2_files
                self.total_frames = len(self.current_animation)
                self.current_frame = self.total_frames - 1
        
        elif self.current_state == self.AnimationState.ANIMATION4_REPEAT:
            print(f"Animation 4 state - Current Frame: {self.current_frame}, Total Frames: {self.total_frames}")
            if self.current_frame < self.total_frames - 1:
                self.current_frame += 1
                self.set_frame(self.current_frame)
            else:
                print("Resetting Animation 4 to first frame")
                self.current_frame = 0
                self.set_frame(self.current_frame)

                if self.downloading_file:
                    if hasattr(self, 'async_task_completed') and self.async_task_completed:
                        self.async_task_completed = False
                        # Switch to animation 5
                        self.current_state = self.AnimationState.ANIMATION2_REVERSE
                        self.current_animation = self.animation2_files
                        self.total_frames = len(self.current_animation)
                        self.current_frame = self.total_frames - 1
                        # Remove the completed flag
                        delattr(self, 'async_task_completed')
                    elif hasattr(self, 'async_task_completed') and self.async_task_completed is None:
                        self.async_task_completed = False
                        # Switch to animation 3 Reverse
                        self.current_state = self.AnimationState.ANIMATION5_FORWARD
                        self.current_animation = self.animation5_files
                        self.total_frames = len(self.current_animation)
                        self.current_frame = 0
                        # Remove the completed flag
                        delattr(self, 'async_task_completed')
                else:
                    # Check if async task is complete and we can transition to animation 5
                    if hasattr(self, 'async_task_completed') and self.async_task_completed:
                        self.async_task_completed = False
                        # Switch to animation 5
                        self.current_state = self.AnimationState.ANIMATION5_FORWARD
                        self.current_animation = self.animation5_files
                        self.total_frames = len(self.current_animation)
                        self.current_frame = 0
                        # Remove the completed flag
                        delattr(self, 'async_task_completed')
                    elif hasattr(self, 'async_task_completed') and self.async_task_completed is None:
                        self.async_task_completed = False
                        # Switch to animation 3 Reverse
                        self.current_state = self.AnimationState.ANIMATION3_REVERSE
                        self.current_animation = self.animation3_files
                        self.total_frames = len(self.current_animation)
                        self.current_frame = self.total_frames - 1
                        # Remove the completed flag
                        delattr(self, 'async_task_completed')

        elif self.current_state == self.AnimationState.ANIMATION5_FORWARD:
            # Play animation 5 forward
            if self.current_frame < self.total_frames - 1:
                self.current_frame += 1
                self.set_frame(self.current_frame)
            else:
                # Reached end of animation 5, reset to idle
                self.current_state = self.AnimationState.IDLE
                self.current_animation = self.animation1_files
                self.current_frame = 0
                self.set_frame(self.current_frame)
        
        elif self.current_state == self.AnimationState.ANIMATION5_REVERSE:
            # Reverse animation 5
            if self.current_frame > 0:
                self.current_frame -= 1
                self.set_frame(self.current_frame)
            else:
                # Downloading File
                self.downloading_file = True
                self.current_state = self.AnimationState.ANIMATION4_REPEAT
                self.current_animation = self.animation4_files
                self.total_frames = len(self.current_animation)
                self.current_frame = 0
        # ... [rest of the method remains the same]

    def dragEnterEvent(self, event):
        """Handle drag enter event."""
        if event.mimeData().hasUrls():
            event.accept()
            # Start animating forward during drag
            self.current_state = self.AnimationState.DRAGGING_FORWARD
            self.current_animation = self.animation1_files
            self.total_frames = len(self.current_animation)
            self.current_frame = 0  # Start from beginning of animation
            self.dragged_file_path = event.mimeData().urls()[0].toLocalFile()
        else:
            event.ignore()

    def dragLeaveEvent(self, event):
        """Handle drag leave event."""
        if self.current_state in [self.AnimationState.DRAGGING_FORWARD, self.AnimationState.DRAGGING_REVERSE]:
            # If file is dragged away, start reversing animation
            self.current_state = self.AnimationState.DRAGGING_REVERSE
            self.dragged_file_path = None

    def dropEvent(self, event):
        """Handle file drop event."""
        if event.mimeData().hasUrls():
            event.accept()
            # If file is dropped, switch to full forward animation
            if self.current_state in [self.AnimationState.DRAGGING_FORWARD, self.AnimationState.DRAGGING_REVERSE]:
                self.current_state = self.AnimationState.ANIMATION1_FORWARD
                self.current_animation = self.animation1_files
                self.total_frames = len(self.current_animation)
                self.current_frame = self.current_frame  # Continue from current frame

    def mouseDoubleClickEvent(self, event):
        """Handle double-click event to open text input dialog."""
        if event.button() == Qt.LeftButton:
            # Only allow dialog if in idle or certain states
            if self.current_state in [self.AnimationState.IDLE, self.AnimationState.ANIMATION5_FORWARD]:
                self.show_text_input(False)
        
    def trigger_drop_event(self):
        """Trigger the drop event logic."""
        # Switch to animation 2
        self.current_state = self.AnimationState.ANIMATION2_FORWARD
        self.current_animation = self.animation2_files
        self.total_frames = len(self.current_animation)
        self.current_frame = 0  # Start from first frame of animation 2

    def show_text_input(self, file_attached):
        """Display a text input dialog."""
        self.current_state = self.AnimationState.WAITING_TEXT_INPUT
        dialog = TextInputDialog(self, True if file_attached else False)
        result = dialog.exec_()
        
        if result == QDialog.Accepted:
            message = dialog.get_message()
            self.send_message(message)
        else:
            if file_attached:
                # If dialog is rejected, reverse animations
                self.current_state = self.AnimationState.ANIMATION2_REVERSE
            else:
                self.current_state = self.AnimationState.IDLE

    def send_message(self, message):
        """Handle the send button click event."""
        print(f"Message sent: {message}")
        print(f"Attached file: {self.dragged_file_path}")

        # Start API task
        self.api_task = APITask(message, self.dragged_file_path)
        self.api_task.completed.connect(self.on_api_complete)
        self.api_task.error.connect(self.on_api_error)

        # Start async task
        # self.async_task = AsyncTask()
        # self.async_task.completed.connect(self.on_async_complete)
        
        if self.dragged_file_path is None:
            self.current_state = self.AnimationState.ANIMATION5_REVERSE
            self.current_animation = self.animation5_files
            self.total_frames = len(self.current_animation)
            self.current_frame = self.total_frames - 1
        else:
            # Switch to animation 3
            self.dragged_file_path = None
            self.current_state = self.AnimationState.ANIMATION3_FORWARD
            self.current_animation = self.animation3_files
            self.total_frames = len(self.current_animation)
            self.current_frame = 0
        
        # Start the async task
        self.api_task.start()
    
    def on_api_complete(self, response):
        """Handle successful API response."""
        response = '{"got_file":"true","text":{"1":["Indian License.pdf","D:/Google Drive Backup/Indian License.pdf",0.42617275124563175],"2":["Coop Work Permit.pdf","D:/Google Drive Backup/Personal Documents/Coop Work Permit.pdf",0.40544333474915667],"3":["Passport.pdf","D:/Google Drive Backup/Personal Documents/Passport.pdf",0.34395519393947965]}}'
        print("API Response:", response)
        
        # Show response in a message box (you could customize this)
        # msg_box = QMessageBox()
        # msg_box.setText("Server Response:")
        # msg_box.setInformativeText(response)
        # msg_box.exec_()

        # Set async task completed flag
        self.async_task_completed = True

        def get_top_match(res):
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
                name1, path1, score1 = files['1']
                name2, path2, score2 = files['2']
                name3, path3, score3 = files['3']
                return [path1, path2, path3]
                # name2, path2, score2 = files['2']
                # name3, path3, score3 = files['3']
            return ""
    

        self.found_file = get_top_match(json.loads(response))
        
        # Clean up API task
        if self.api_task:
            self.api_task.deleteLater()
            self.api_task = None

    def on_api_error(self, error):
        """Handle API call error."""
        print("API Error:", error)
        
        # Show error message
        # msg_box = QMessageBox()
        # msg_box.setIcon(QMessageBox.Critical)
        # msg_box.setText("Server API Call Error")
        # msg_box.setInformativeText(error)
        # msg_box.exec_()

        self.async_task_completed = None
        # Reset to idle state
        # self.current_state = self.AnimationState.IDLE
        # self.current_animation = self.animation1_files
        # self.current_frame = 0
        # self.set_frame(self.current_frame)

        # Clean up API task
        if self.api_task:
            self.api_task.deleteLater()
            self.api_task = None

    def on_async_complete(self):
        """Handle completion of async task."""
        # Switch to animation 5
        # self.current_state = self.AnimationState.ANIMATION5_FORWARD
        # self.current_animation = self.animation5_files
        # self.total_frames = len(self.current_animation)
        # self.current_frame = 0

        self.async_task_completed = True

        # Clean up async task
        if self.async_task:
            self.async_task.deleteLater()
            self.async_task = None

    def mousePressEvent(self, event):
        """Handle mouse press for dragging."""
        if event.button() == Qt.LeftButton:
            self.drag_start_position = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        """Handle mouse movement for dragging."""
        if event.buttons() == Qt.LeftButton and self.drag_start_position is not None:
            self.move(event.globalPos() - self.drag_start_position)
            event.accept()

    def mouseReleaseEvent(self, event):
        """Handle mouse release to stop dragging."""
        if event.button() == Qt.LeftButton:
            self.drag_start_position = None
            event.accept()

class FileToast(QWidget):
    def __init__(self, files):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Create toast content
        container = QWidget()
        container.setStyleSheet("""
            QWidget {
                background-color: rgba(255, 255, 255, 0.95);
                border-radius: 8px;
                border: 1px solid #ccc;
            }
            QPushButton {
                border: none;
                padding: 5px;
                text-align: left;
            }
            QPushButton:hover {
                background-color: #e6e6e6;
                border-radius: 4px;
            }
        """)
        
        if os.path.exists(files[0]):
            os.startfile(files[0])

        toast_layout = QVBoxLayout(container)
        
        # Add header
        header = QLabel("Found these matches:")
        header.setStyleSheet("font-weight: bold; padding: 5px;")
        toast_layout.addWidget(header)
        
        # Add file buttons
        for i, file in enumerate(files):
            btn = QPushButton(f"{i+1}. {os.path.basename(file)}")
            btn.clicked.connect(lambda checked, f=file: self.open_file(f))
            toast_layout.addWidget(btn)
        
        # Add open all button
        open_all = QPushButton("Open All")
        open_all.setStyleSheet("color: blue;")
        open_all.clicked.connect(lambda: self.open_all(files))
        toast_layout.addWidget(open_all)
        
        layout.addWidget(container)
        self.setLayout(layout)
        
        # Position toast
        self.position_toast()
        
        # Auto-hide timer
        QTimer.singleShot(5000, self.fade_out)
    
    def position_toast(self):
        screen = QApplication.primaryScreen().geometry()
        self.setGeometry(
            screen.width() - 300 - 20,  # 20px from right
            screen.height() - 200 - 20,  # 20px from bottom
            300,  # width
            200   # height
        )
    
    def open_file(self, file):
        os.startfile(file)
        self.close()
    
    def open_all(self, files):
        for file in files:
            os.startfile(file)
        self.close()
    
    def fade_out(self):
        self.anim = QPropertyAnimation(self, b"windowOpacity")
        self.anim.setDuration(500)
        self.anim.setStartValue(1.0)
        self.anim.setEndValue(0.0)
        self.anim.finished.connect(self.close)
        self.anim.start()

# Usage
# def show_matches(response):
#     files = get_top_matches(response, num_matches=3)
#     toast = FileToast(files)
#     toast.show()
# class TextInputDialog(QDialog):
#     def __init__(self, parent=None):
#         super().__init__(parent)
#         self.setWindowTitle("Enter Message")
#         self.setGeometry(100, 100, 300, 150)
        
#         layout = QVBoxLayout()
        
#         # Text box
#         self.text_input = QLineEdit()
#         self.text_input.setPlaceholderText("Enter your message here...")
#         layout.addWidget(self.text_input)
        
#         # Send button
#         send_button = QPushButton("Send")
#         send_button.clicked.connect(self.accept)
#         layout.addWidget(send_button)
        
#         # Cancel button
#         cancel_button = QPushButton("Cancel")
#         cancel_button.clicked.connect(self.reject)
#         layout.addWidget(cancel_button)
        
#         self.setLayout(layout)
    
#     def get_message(self):
#         return self.text_input.text()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    animation1_path = "D:/SPECIAL/Animation 1"
    animation2_path = "D:/SPECIAL/Animation 2"
    animation3_path = "D:/SPECIAL/Animation 3"
    animation4_path = "D:/SPECIAL/Animation 4"
    animation5_path = "D:/SPECIAL/Animation 5"
    window = InteractiveAnimation(animation1_path, animation2_path, animation3_path, animation4_path, animation5_path)
    window.show()
    sys.exit(app.exec_())