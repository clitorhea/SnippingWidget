# Snipping Tool with OCR

Cross‑platform screen snipping utility with built‑in OCR, built using PyQt5 and Tesseract. Capture any region of your screen, preview it, extract text, and copy the result to your clipboard. Optional EasyOCR support is available for improved recognition in some cases.

## Features
- Region snipping overlay with click‑and‑drag selection
- Image preview and text extraction in a simple UI
- Keyboard shortcuts: `Ctrl+Shift+S` (New Snip), `Ctrl+V` (Paste Image)
- OCR via Tesseract (default); optional EasyOCR
- Copy extracted text to clipboard with one click
- Works on Windows, Linux, and macOS

## Project Structure
- `snipping_tool.py` — main application (PyQt5 UI, snipping overlay, OCR pipeline)

## Requirements
- Python 3.8+
- System Tesseract OCR installation
- Python packages:
  - `PyQt5`, `Pillow`, `pytesseract`, `pyperclip`, `mss`, `numpy`
  - Optional: `easyocr` (for the EasyOCR engine)

## Install
1. Install Tesseract OCR (required by pytesseract):
   - Windows: Download installer from https://github.com/UB-Mannheim/tesseract/wiki
   - Linux (Debian/Ubuntu): `sudo apt update && sudo apt install -y tesseract-ocr`
   - macOS (Homebrew): `brew install tesseract`

2. Install Python dependencies (ideally in a virtual environment):
   ```bash
   pip install --upgrade pip
   pip install PyQt5 Pillow pytesseract pyperclip mss numpy
   # Optional (for alternate OCR engine):
   pip install easyocr
   ```

## Usage
```bash
python snipping_tool.py
```

- Click "📸 New Snip (Ctrl+Shift+S)" or press `Ctrl+Shift+S` to start snipping.
- Click and drag to select a region. Release the mouse to capture.
- Click "🔍 Extract Text" to run OCR on the captured image.
- Click "📋 Copy to Clipboard" to copy the recognized text.
- You can also paste an image from your clipboard with `Ctrl+V`.

### OCR Engines
- Tesseract (Fast) — default via `pytesseract`. Good all‑round performance and local/offline.
- EasyOCR (Accurate - Not Installed) — install with `pip install easyocr` and select it from the dropdown.
- Cloud API (Premium - Not Implemented) — placeholder for future integration.

## Windows: Tesseract Path
If Tesseract is installed but not in your `PATH`, you can set the executable path in code before using `pytesseract`:
```python
import pytesseract
pytesseract.pytesseract.tesseract_cmd = r"C:\\Program Files\\Tesseract-OCR\\tesseract.exe"
```
Alternatively, add the Tesseract installation folder to your system `PATH`.

## Tips for Better OCR
- Use high‑contrast images; the app applies basic preprocessing (grayscale, contrast, sharpen, threshold).
- Prefer clear, non‑compressed text regions; zoom in if needed before snipping.
- Switch to EasyOCR if Tesseract struggles with specific fonts or languages.

## Troubleshooting
- "Tesseract Not Found": Ensure Tesseract is installed and accessible in `PATH` (or set `tesseract_cmd` as above).
- Missing Qt platform plugin / display issues: On Linux, ensure an available display server (X11/Wayland). Try `QT_QPA_PLATFORM=xcb` if needed.
- Clipboard issues in headless environments: GUI clipboard access requires a running desktop session.
- EasyOCR import error: Install it with `pip install easyocr` or select Tesseract.

## Development
- Start the app with `python snipping_tool.py`.
- The snipping overlay is implemented in `SnippingWidget`; the main UI and OCR logic live in `MainWindow`.
- Contributions are welcome via pull requests.

## License
No license specified. Add a `LICENSE` file to define usage terms.

