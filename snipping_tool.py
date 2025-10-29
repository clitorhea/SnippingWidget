#!/usr/bin/env python3
"""
Cross-Platform Snipping Tool with OCR
Supports Windows, Linux, and macOS
"""

import sys
import io
from PIL import Image, ImageGrab, ImageEnhance, ImageFilter
import pytesseract
import pyperclip
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QLabel, 
                             QPushButton, QVBoxLayout, QHBoxLayout, QComboBox,
                             QSystemTrayIcon, QMenu, QMessageBox, QRubberBand)
from PyQt5.QtCore import Qt, QRect, QPoint, QSize, QTimer
from PyQt5.QtGui import QPixmap, QPainter, QPen, QColor, QCursor, QIcon, QScreen
import mss
import numpy as np

class SnippingWidget(QWidget):
    """Overlay widget for selecting screen region"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setWindowOpacity(0.3)
        
        self.begin = QPoint()
        self.end = QPoint()
        self.is_selecting = False
        self.screenshot = None
        self.rubber_band = QRubberBand(QRubberBand.Rectangle, self)
        
    def start_snip(self):
        """Start the snipping process"""
        # Capture all screens
        screen = QApplication.primaryScreen()
        self.screenshot = screen.grabWindow(0)
        
        # Show fullscreen overlay
        self.showFullScreen()
        self.setCursor(Qt.CrossCursor)
        
    def paintEvent(self, event):
        """Draw the selection overlay"""
        if self.is_selecting:
            painter = QPainter(self)
            painter.setPen(QPen(QColor(0, 255, 0, 255), 2, Qt.SolidLine))
            painter.setBrush(QColor(0, 255, 0, 30))
            painter.drawRect(QRect(self.begin, self.end))
    
    def mousePressEvent(self, event):
        """Start selection"""
        self.begin = event.pos()
        self.end = event.pos()
        self.is_selecting = True
        self.rubber_band.setGeometry(QRect(self.begin, QSize()))
        self.rubber_band.show()
        self.update()
    
    def mouseMoveEvent(self, event):
        """Update selection"""
        if self.is_selecting:
            self.end = event.pos()
            self.rubber_band.setGeometry(QRect(self.begin, self.end).normalized())
            self.update()
    
    def mouseReleaseEvent(self, event):
        """Finish selection and capture"""
        self.is_selecting = False
        self.rubber_band.hide()
        
        # Get selection rectangle
        rect = QRect(self.begin, self.end).normalized()
        
        if rect.width() > 10 and rect.height() > 10:
            # Capture the selected area
            self.capture_region(rect)
        
        self.hide()
        self.close()
    
    def keyPressEvent(self, event):
        """Cancel on ESC key"""
        if event.key() == Qt.Key_Escape:
            self.is_selecting = False
            self.rubber_band.hide()
            self.hide()
            self.close()
    
    def capture_region(self, rect):
        """Capture and process the selected region"""
        if self.screenshot:
            # Crop the screenshot to selected area
            cropped = self.screenshot.copy(rect)
            
            # Convert to PIL Image
            buffer = io.BytesIO()
            cropped.save(buffer, "PNG")
            buffer.seek(0)
            pil_image = Image.open(buffer)
            
            # Send to main window for processing
            if self.parent():
                self.parent().process_capture(pil_image)


class MainWindow(QMainWindow):
    """Main application window"""
    
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.captured_image = None
        
    def init_ui(self):
        """Initialize the user interface"""
        self.setWindowTitle("Snipping Tool with OCR")
        self.setGeometry(100, 100, 600, 500)
        
        # Central widget
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        
        # Control panel
        controls = QHBoxLayout()
        
        # Snip button
        self.snip_btn = QPushButton("📸 New Snip (Ctrl+Shift+S)")
        self.snip_btn.clicked.connect(self.start_snipping)
        self.snip_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 10px;
                font-size: 14px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        controls.addWidget(self.snip_btn)
        
        # Paste button
        self.paste_btn = QPushButton("📋 Paste Image (Ctrl+V)")
        self.paste_btn.clicked.connect(self.paste_from_clipboard)
        self.paste_btn.setStyleSheet("""
            QPushButton {
                background-color: #9C27B0;
                color: white;
                border: none;
                padding: 10px;
                font-size: 14px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #7B1FA2;
            }
        """)
        controls.addWidget(self.paste_btn)
        
        # OCR Engine selector
        self.ocr_combo = QComboBox()
        self.ocr_combo.addItems(["Tesseract (Fast)", "EasyOCR (Accurate - Not Installed)", "Cloud API (Premium - Not Implemented)"])
        self.ocr_combo.setCurrentIndex(0)
        controls.addWidget(self.ocr_combo)
        
        # Extract Text button
        self.extract_btn = QPushButton("🔍 Extract Text")
        self.extract_btn.clicked.connect(self.extract_text)
        self.extract_btn.setEnabled(False)
        self.extract_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                padding: 10px;
                font-size: 14px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #0b7dda;
            }
            QPushButton:disabled {
                background-color: #cccccc;
            }
        """)
        controls.addWidget(self.extract_btn)
        
        layout.addLayout(controls)
        
        # Image preview
        self.image_label = QLabel("Click 'New Snip' or press Ctrl+Shift+S to capture")
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setStyleSheet("""
            QLabel {
                border: 2px dashed #cccccc;
                border-radius: 5px;
                background-color: #f5f5f5;
                min-height: 200px;
            }
        """)
        layout.addWidget(self.image_label, 3)
        
        # Text output
        self.text_label = QLabel("Extracted text will appear here")
        self.text_label.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self.text_label.setWordWrap(True)
        self.text_label.setStyleSheet("""
            QLabel {
                border: 1px solid #cccccc;
                border-radius: 5px;
                padding: 10px;
                background-color: white;
                min-height: 150px;
            }
        """)
        layout.addWidget(self.text_label, 2)
        
        # Copy button
        self.copy_btn = QPushButton("📋 Copy to Clipboard")
        self.copy_btn.clicked.connect(self.copy_to_clipboard)
        self.copy_btn.setEnabled(False)
        self.copy_btn.setStyleSheet("""
            QPushButton {
                background-color: #FF9800;
                color: white;
                border: none;
                padding: 10px;
                font-size: 14px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #e68900;
            }
            QPushButton:disabled {
                background-color: #cccccc;
            }
        """)
        layout.addWidget(self.copy_btn)
        
        # Setup global hotkey (simplified - use keyboard library for better support)
        self.setup_shortcuts()
        
    def setup_shortcuts(self):
        """Setup keyboard shortcuts"""
        from PyQt5.QtWidgets import QShortcut
        from PyQt5.QtGui import QKeySequence
        
        # Snip shortcut
        shortcut = QShortcut(QKeySequence("Ctrl+Shift+S"), self)
        shortcut.activated.connect(self.start_snipping)
        
        # Paste shortcut
        paste_shortcut = QShortcut(QKeySequence("Ctrl+V"), self)
        paste_shortcut.activated.connect(self.paste_from_clipboard)
        
    def start_snipping(self):
        """Start the snipping process"""
        self.hide()  # Hide main window during snipping
        QTimer.singleShot(100, self._show_snipping_widget)
        
    def _show_snipping_widget(self):
        """Show snipping widget after delay"""
        self.snipping_widget = SnippingWidget(self)
        self.snipping_widget.start_snip()
        
    def process_capture(self, image):
        """Process captured image"""
        self.show()  # Show main window again
        self.captured_image = image
        
        # Display image
        img_byte_arr = io.BytesIO()
        image.save(img_byte_arr, format='PNG')
        img_byte_arr.seek(0)
        
        pixmap = QPixmap()
        pixmap.loadFromData(img_byte_arr.read())
        
        # Scale to fit
        scaled_pixmap = pixmap.scaled(self.image_label.size(), 
                                      Qt.KeepAspectRatio, 
                                      Qt.SmoothTransformation)
        self.image_label.setPixmap(scaled_pixmap)
        
        # Enable extract button
        self.extract_btn.setEnabled(True)
        self.text_label.setText("Image captured! Click 'Extract Text' to process.")
        
    def preprocess_image(self, image):
        """Preprocess image for better OCR accuracy"""
        # Convert to grayscale
        gray = image.convert('L')
        
        # Enhance contrast
        enhancer = ImageEnhance.Contrast(gray)
        enhanced = enhancer.enhance(2.0)
        
        # Sharpen
        sharpened = enhanced.filter(ImageFilter.SHARPEN)
        
        # Convert to numpy for thresholding
        img_array = np.array(sharpened)
        
        # Apply adaptive thresholding
        threshold = np.mean(img_array)
        binary = (img_array > threshold) * 255
        
        return Image.fromarray(binary.astype(np.uint8))
        
    def extract_text(self):
        """Extract text from captured image"""
        if not self.captured_image:
            return
            
        self.text_label.setText("Processing... Please wait.")
        QApplication.processEvents()
        
        try:
            # Preprocess image
            processed_image = self.preprocess_image(self.captured_image)
            
            # Get selected OCR engine
            engine = self.ocr_combo.currentText()
            
            if "Tesseract" in engine:
                # Use Tesseract
                text = pytesseract.image_to_string(processed_image, config='--psm 6')
            elif "EasyOCR" in engine:
                try:
                    import easyocr
                    reader = easyocr.Reader(['en'])
                    result = reader.readtext(np.array(processed_image))
                    text = '\n'.join([item[1] for item in result])
                except ImportError:
                    text = "EasyOCR not installed. Please install with: pip install easyocr"
            else:
                text = "Cloud API not implemented in this demo"
            
            if text.strip():
                self.text_label.setText(text)
                self.extracted_text = text
                self.copy_btn.setEnabled(True)
            else:
                self.text_label.setText("No text detected in image")
                self.copy_btn.setEnabled(False)
                
        except Exception as e:
            self.text_label.setText(f"Error during OCR: {str(e)}")
            QMessageBox.warning(self, "OCR Error", f"Failed to extract text: {str(e)}")
            
    def copy_to_clipboard(self):
        """Copy extracted text to clipboard"""
        if hasattr(self, 'extracted_text'):
            pyperclip.copy(self.extracted_text)
            QMessageBox.information(self, "Success", "Text copied to clipboard!")
    
    def paste_from_clipboard(self):
        """Paste and process image from clipboard"""
        clipboard = QApplication.clipboard()
        mime_data = clipboard.mimeData()
        
        # Check if clipboard has image
        if mime_data.hasImage():
            # Get QImage from clipboard
            q_image = clipboard.image()
            
            if q_image.isNull():
                QMessageBox.warning(self, "No Image", "No valid image found in clipboard")
                return
            
            # Convert QImage to PIL Image
            buffer = io.BytesIO()
            q_image.save(buffer, "PNG")
            buffer.seek(0)
            pil_image = Image.open(buffer)
            
            # Process the pasted image
            self.process_capture(pil_image)
            self.text_label.setText("Image pasted from clipboard! Click 'Extract Text' to process.")
            
        elif mime_data.hasUrls():
            # Handle image file paths
            urls = mime_data.urls()
            if urls:
                file_path = urls[0].toLocalFile()
                try:
                    pil_image = Image.open(file_path)
                    self.process_capture(pil_image)
                    self.text_label.setText("Image loaded from file! Click 'Extract Text' to process.")
                except Exception as e:
                    QMessageBox.warning(self, "Error", f"Could not open image file: {str(e)}")
        else:
            QMessageBox.warning(self, "No Image", 
                              "Clipboard does not contain an image.\n\n"
                              "Try:\n"
                              "1. Taking a screenshot (PrtScn)\n"
                              "2. Copying an image from a browser\n"
                              "3. Copying an image file")


def main():
    """Main entry point"""
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    
    # Check if Tesseract is installed
    try:
        pytesseract.get_tesseract_version()
    except Exception as e:
        QMessageBox.warning(None, "Tesseract Not Found", 
                          "Tesseract OCR is not installed or not in PATH.\n\n"
                          "Please install Tesseract:\n"
                          "- Windows: https://github.com/UB-Mannheim/tesseract/wiki\n"
                          "- Linux: sudo apt install tesseract-ocr\n"
                          "- macOS: brew install tesseract")
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()