import io
import pytesseract
import pdfplumber
import cv2
import numpy as np
from PIL import Image

import os

# For MVP, assume Tesseract is installed in system PATH or default location.
# Auto-detect Tesseract path if not in PATH
def set_tesseract_path():
    # Common locations on Windows
    possible_paths = [
        r"C:\Program Files\Tesseract-OCR\tesseract.exe",
        r"C:\Users\ADMIN\AppData\Local\Programs\Tesseract-OCR\tesseract.exe",
        r"C:\Users\ADMIN\AppData\Local\Tesseract-OCR\tesseract.exe",
        r"C:\Tesseract-OCR\tesseract.exe"
    ]
    
    # Check if 'tesseract' is in PATH first
    import shutil
    if shutil.which("tesseract"):
        return

    for path in possible_paths:
        if os.path.exists(path):
            print(f"DEBUG: Found Tesseract at {path}")
            pytesseract.pytesseract.tesseract_cmd = path
            return

set_tesseract_path()

def preprocess_image(image: Image.Image) -> Image.Image:
    """
    Applies standard preprocessing for OCR: Grayscale, Adaptive Thresholding.
    """
    # Convert PIL to CV2
    img_cv = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
    
    # 1. Grayscale
    gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
    
    # 2. Noise Removal (Gaussian Blur)
    blur = cv2.GaussianBlur(gray, (5, 5), 0)
    
    # 3. Adaptive Thresholding (Binarization)
    thresh = cv2.adaptiveThreshold(
        blur, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
    )
    
    # Convert back to PIL
    return Image.fromarray(thresh)

async def extract_text_from_file(file_bytes: bytes, filename: str) -> dict:
    """
    Determines file type and extracts text.
    Returns: {"text": str, "method": "pdf_text" | "ocr", "confidence": str}
    """
    filename = filename.lower()
    text = ""
    method = ""
    confidence = "high" # default

    try:
        if filename.endswith(".pdf"):
            # Stage 1: Try direct text extraction
            with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
                extracted = []
                for page in pdf.pages:
                    extracted.append(page.extract_text() or "")
                text = "\n".join(extracted).strip()
            
            if len(text) > 50: # Arbitrary threshold for "good" text
                method = "pdf_text"
            else:
                method = "pdf_text_low_quality"
                confidence = "low"

        elif filename.endswith((".jpg", ".jpeg", ".png")):
            method = "ocr"
            image = Image.open(io.BytesIO(file_bytes))
            
            # Preprocess
            processed_img = preprocess_image(image)
            
            # Tesseract
            try:
                text = pytesseract.image_to_string(processed_img, lang='eng')
            except pytesseract.TesseractNotFoundError:
                return {"text": "", "method": "error", "error": "OCR Engine (Tesseract) not found on server. Please install Tesseract-OCR."}
            except Exception as e:
                return {"text": "", "method": "error", "error": f"OCR Failed: {str(e)}"}
            
            # Simple confidence check
            if len(text.strip()) < 10:
                confidence = "low"
            else:
                confidence = "medium" # OCR is rarely high confidence without verification

        else:
            return {"text": "", "method": "unsupported", "error": "Unsupported file format"}
            
        return {
            "text": text,
            "method": method,
            "confidence": confidence,
            "disclaimer": "This text is machine-extracted and may contain inaccuracies. Please verify with the original document."
        }
        
    except Exception as e:
        print(f"OCR Error: {e}")
        return {"text": "", "method": "error", "error": str(e)}
