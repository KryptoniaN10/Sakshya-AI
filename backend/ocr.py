import io
import os
from typing import List, Tuple

import numpy as np
from PIL import Image

import pdfplumber
from pdf2image import convert_from_bytes

# Lightweight language detection
from langdetect import detect_langs

# PaddleOCR (lazy-loaded)
_PADDLE_OCR = None


def _resize_image_max(image: Image.Image, max_dim: int = 1600) -> Image.Image:
    w, h = image.size
    max_current = max(w, h)
    if max_current <= max_dim:
        return image
    scale = max_dim / max_current
    new_w = int(w * scale)
    new_h = int(h * scale)
    return image.resize((new_w, new_h), Image.LANCZOS)


def _image_from_pdf_bytes(file_bytes: bytes, max_pages: int = 3, dpi: int = 150) -> List[Image.Image]:
    images = convert_from_bytes(file_bytes, dpi=dpi, first_page=1, last_page=max_pages)
    return [_resize_image_max(img) for img in images]


def _init_paddle():
    global _PADDLE_OCR
    if _PADDLE_OCR is not None:
        return _PADDLE_OCR
    try:
        from paddleocr import PaddleOCR
        # Use English by default; Paddle supports other langs depending on install
        _PADDLE_OCR = PaddleOCR(use_angle_cls=False, lang='en')
        print("DEBUG: PaddleOCR initialized (CPU mode).")
        return _PADDLE_OCR
    except Exception as e:
        print(f"DEBUG: PaddleOCR import/init failed: {e}")
        _PADDLE_OCR = None
        return None


def _paddleocr_ocr(image: Image.Image) -> Tuple[str, float]:
    paddle = _init_paddle()
    if not paddle:
        return "", 0.0
    try:
        result = paddle.ocr(np.array(image), cls=False)
        texts = []
        confidences = []
        for line in result:
            for item in line:
                try:
                    # Handle several possible return shapes
                    if isinstance(item, list) and len(item) >= 2 and isinstance(item[1], dict):
                        text = item[1].get('text', '')
                        conf = float(item[1].get('confidence', 0.0))
                    elif isinstance(item, list) and len(item) >= 2 and isinstance(item[1], tuple):
                        text = item[1][0]
                        conf = float(item[1][1])
                    elif isinstance(item, tuple) and len(item) >= 2:
                        text = item[0]
                        conf = float(item[1])
                    else:
                        text = str(item)
                        conf = 0.0
                except Exception:
                    text = str(item)
                    conf = 0.0
                if text:
                    texts.append(text)
                    confidences.append(conf)
        avg_conf = float(np.mean(confidences)) if confidences else 0.0
        return "\n".join(texts).strip(), avg_conf
    except Exception as e:
        print(f"PaddleOCR error: {e}")
        return "", 0.0


def _detect_language_summary(text: str) -> Tuple[str, str]:
    try:
        langs = detect_langs(text)
        if not langs:
            return 'en', 'low'
        top = langs[0]
        code = top.lang
        prob = top.prob
        supported = ['en', 'hi', 'ml', 'ta', 'te', 'kn', 'bn']
        if code not in supported:
            return 'en', 'low'
        if prob > 0.85:
            conf = 'high'
        elif prob > 0.6:
            conf = 'medium'
        else:
            conf = 'low'
        return code, conf
    except Exception:
        return 'en', 'low'


async def extract_text_from_file(file_bytes: bytes, filename: str) -> dict:
    filename = filename.lower()
    try:
        images: List[Image.Image] = []
        if filename.endswith('.pdf'):
            # Try typed text first
            try:
                with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
                    extracted = []
                    for i, page in enumerate(pdf.pages[:3]):
                        extracted.append(page.extract_text() or "")
                    raw_text = "\n".join(extracted).strip()
                if len(raw_text) > 50:
                    det_lang, det_conf = _detect_language_summary(raw_text)
                    return {
                        'text': raw_text,
                        'method': 'pdf_text',
                        'confidence': 'high',
                        'detected_language': det_lang,
                        'detection_confidence': det_conf,
                        'disclaimer': 'This text is machine-extracted and may contain inaccuracies. Please verify before analysis.'
                    }
            except Exception as e:
                print(f"DEBUG: pdfplumber text extraction failed: {e}")
            try:
                images = _image_from_pdf_bytes(file_bytes, max_pages=3, dpi=150)
            except Exception as e:
                print(f"DEBUG: PDF->image conversion failed: {e}")
                images = []
        elif filename.endswith(('.jpg', '.jpeg', '.png')):
            img = Image.open(io.BytesIO(file_bytes))
            images = [_resize_image_max(img)]
        else:
            return {'text': '', 'method': 'unsupported', 'error': 'Unsupported file format'}

        method_used = 'paddleocr'
        paddle = _init_paddle()
        if not paddle:
            return {'text': '', 'method': 'error', 'error': 'PaddleOCR not installed. Install paddlepaddle (CPU) and paddleocr.'}

        combined_texts = []
        confidences = []
        for img in images:
            text, conf = _paddleocr_ocr(img)
            print(f"DEBUG: PaddleOCR produced {len(text)} chars (conf={conf})")
            combined_texts.append(text)
            confidences.append(conf)

        final_text = "\n\n".join([t for t in combined_texts if t])
        avg_conf = float(np.mean(confidences)) if confidences else 0.0
        if avg_conf >= 0.7:
            conf_label = 'high'
        elif avg_conf >= 0.35:
            conf_label = 'medium'
        else:
            conf_label = 'low'

        det_lang, det_conf = _detect_language_summary(final_text)
        return {
            'text': final_text,
            'method': method_used,
            'confidence': conf_label,
            'detected_language': det_lang,
            'detection_confidence': det_conf,
            'disclaimer': 'OCR text may contain inaccuracies, especially for handwritten or regional-language documents. Please verify before analysis.'
        }
    except Exception as e:
        print(f"OCR pipeline error: {e}")
        return {'text': '', 'method': 'error', 'error': str(e)}
import io
import os
from typing import List, Tuple

import cv2
import numpy as np
from PIL import Image

import pytesseract
import pdfplumber

# Lightweight language detection
from langdetect import detect_langs

# PDF -> image
from pdf2image import convert_from_bytes

# Primary OCR: EasyOCR (CPU-only)
try:
    import easyocr
    _EASY_OCR_AVAILABLE = True
except Exception:
    easyocr = None
    _EASY_OCR_AVAILABLE = False

# PaddleOCR fallback (lazy import)
_PADDLE_LOADER = None

# Initialize EasyOCR reader once
_EASY_OCR_READER = None
_EASY_OCR_LANGS = ['en','hi','ml','ta','te','kn','bn']
if _EASY_OCR_AVAILABLE:
    # Try initializing EasyOCR with progressively smaller language sets
    tried_sets = [
        _EASY_OCR_LANGS,
        ['en','hi'],
        ['en']
    ]
    for langs in tried_sets:
        try:
            _EASY_OCR_READER = easyocr.Reader(langs, gpu=False)
            print(f"DEBUG: EasyOCR reader initialized with languages: {langs}")
            break
        except Exception as e:
            print(f"DEBUG: EasyOCR init failed for {langs}: {e}")
            _EASY_OCR_READER = None
    if _EASY_OCR_READER is None:
        print("DEBUG: EasyOCR initialization failed for all fallback language sets.")


def _resize_image_max(image: Image.Image, max_dim: int = 1600) -> Image.Image:
    w, h = image.size
    max_current = max(w, h)
    if max_current <= max_dim:
        return image
    scale = max_dim / max_current
    new_w = int(w * scale)
    new_h = int(h * scale)
    return image.resize((new_w, new_h), Image.LANCZOS)


def _image_from_pdf_bytes(file_bytes: bytes, max_pages: int = 3, dpi: int = 150) -> List[Image.Image]:
    # convert_from_bytes may raise if poppler not available; caller should handle exceptions
    images = convert_from_bytes(file_bytes, dpi=dpi, first_page=1, last_page=max_pages)
    # Ensure max dimension
    return [_resize_image_max(img) for img in images]


def _easyocr_ocr(image: Image.Image) -> Tuple[str, float]:
    """Run EasyOCR on a PIL image. Returns (text, avg_confidence)."""
    if not _EASY_OCR_READER:
        return "", 0.0
    # easyocr expects numpy array (RGB)
    arr = np.array(image.convert('RGB'))
    try:
        results = _EASY_OCR_READER.readtext(arr, detail=1)
        texts = [t[1] for t in results]
        confidences = [t[2] for t in results if len(t) > 2]
        avg_conf = float(np.mean(confidences)) if confidences else 0.0
        return "\n".join(texts).strip(), avg_conf
    except Exception as e:
        print(f"EasyOCR error: {e}")
        return "", 0.0


def _load_paddle():
    global _PADDLE_LOADER
    if _PADDLE_LOADER is not None:
        return _PADDLE_LOADER
    try:
        from paddleocr import PaddleOCR
        # Use en for general recognition; Paddle may not support all Indic scripts equally,
        # but it's used as a fallback only.
        _PADDLE_LOADER = PaddleOCR(use_angle_cls=False, lang='en')
        print("DEBUG: PaddleOCR initialized (fallback).")
        return _PADDLE_LOADER
    except Exception as e:
        print(f"DEBUG: PaddleOCR import/init failed: {e}")
        _PADDLE_LOADER = None
        return None


def _paddleocr_ocr(image: Image.Image) -> Tuple[str, float]:
    paddle = _load_paddle()
    if not paddle:
        return "", 0.0
    try:
        result = paddle.ocr(np.array(image), cls=False)
        texts = []
        confidences = []
        for line in result:
            # Paddle returns [[bbox, (text, confidence)], ...]
            for item in line:
                if isinstance(item, tuple) and len(item) >= 2:
                    text, conf = item[0], item[1]
                    texts.append(text)
                    try:
                        confidences.append(float(conf))
                    except Exception:
                        pass
                elif isinstance(item, list) and len(item) >= 2 and isinstance(item[1], tuple):
                    text, conf = item[1][0], item[1][1]
                    texts.append(text)
                    try:
                        confidences.append(float(conf))
                    except Exception:
                        pass
        avg_conf = float(np.mean(confidences)) if confidences else 0.0
        return "\n".join(texts).strip(), avg_conf
    except Exception as e:
        print(f"PaddleOCR error: {e}")
        return "", 0.0


def _pytesseract_ocr(image: Image.Image, lang_code: str | None = None) -> Tuple[str, float]:
    try:
        # Map our short codes to tesseract traineddata codes
        lang_map = {
            'en': 'eng',
            'hi': 'hin',
            'bn': 'ben',
            'ta': 'tam',
            'te': 'tel',
            'kn': 'kan',
            'ml': 'mal'
        }
        tess_lang = None
        if lang_code and lang_code in lang_map:
            tess_lang = lang_map[lang_code]

        if tess_lang:
            text = pytesseract.image_to_string(image, lang=tess_lang)
        else:
            text = pytesseract.image_to_string(image)

        # No confidence info from pytesseract via this API; approximate using length
        conf = 0.6 if text and len(text.strip()) > 40 else (0.4 if text and len(text.strip()) > 10 else 0.0)
        return text.strip(), conf
    except Exception as e:
        print(f"pytesseract fallback error: {e}")
        return "", 0.0


_SCRIPT_RANGES = {
    'en': (r'\\u0000-\\u007F'),
    'hi': (r'\\u0900-\\u097F'),
    'bn': (r'\\u0980-\\u09FF'),
    'ta': (r'\\u0B80-\\u0BFF'),
    'te': (r'\\u0C00-\\u0C7F'),
    'kn': (r'\\u0C80-\\u0CFF'),
    'ml': (r'\\u0D00-\\u0D7F')
}


def _script_coverage(text: str, lang: str) -> float:
    import re
    if not text:
        return 0.0
    rng = _SCRIPT_RANGES.get(lang)
    if not rng:
        return 0.0
    pattern = re.compile(f"[{rng}]")
    matches = pattern.findall(text)
    return min(1.0, len(matches) / max(1, len(text)))


def _invalid_char_ratio(text: str) -> float:
    # Ratio of characters that are not whitespace or printable punctuation/letters
    if not text:
        return 1.0
    valid = [c for c in text if c.isprintable() and c != '\\x0c']
    return 1.0 - (len(valid) / len(text))


def _score_text(text: str, lang: str) -> float:
    # Simple heuristic combining length, script coverage and invalid chars
    length = len(text)
    if length == 0:
        return 0.0
    coverage = _script_coverage(text, lang)
    invalid = _invalid_char_ratio(text)
    return length * (1.0 - invalid) + coverage * 50


async def extract_text_from_file(file_bytes: bytes, filename: str) -> dict:
    """Hybrid OCR pipeline entrypoint.

    Returns dict with keys: text, method, confidence, detected_language, detection_confidence, disclaimer
    """
    filename = filename.lower()

    # Helper: detect language from OCRed text (map to supported set)
    def detect_language_summary(text: str) -> Tuple[str, str]:
        try:
            langs = detect_langs(text)
            if not langs:
                return 'en', 'low'
            top = langs[0]
            code = top.lang
            prob = top.prob
            # Map to supported list
            supported = ['en','hi','ml','ta','te','kn','bn']
            if code not in supported:
                # Some Indic languages may be reported as 'bn' etc — keep only supported
                return 'en', 'low'
            if prob > 0.85:
                conf = 'high'
            elif prob > 0.6:
                conf = 'medium'
            else:
                conf = 'low'
            return code, conf
        except Exception:
            return 'en', 'low'

    try:
        images: List[Image.Image] = []
        method_used = ''
        combined_texts = []
        confidences = []

        if filename.endswith('.pdf'):
            # First try direct text extraction (typed PDFs)
            try:
                with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
                    extracted = []
                    for i, page in enumerate(pdf.pages[:3]):
                        extracted.append(page.extract_text() or "")
                    raw_text = "\n".join(extracted).strip()
                if len(raw_text) > 50:
                    return {
                        'text': raw_text,
                        'method': 'pdf_text',
                        'confidence': 'high',
                        'detected_language': detect_language_summary(raw_text)[0],
                        'detection_confidence': detect_language_summary(raw_text)[1],
                        'disclaimer': 'This text is machine-extracted and may contain inaccuracies. Please verify before analysis.'
                    }
            except Exception as e:
                # If pdfplumber fails, fall back to image conversion
                print(f"DEBUG: pdfplumber text extraction failed: {e}")

            # Convert PDF pages to images (max 3 pages, 150 DPI)
            try:
                images = _image_from_pdf_bytes(file_bytes, max_pages=3, dpi=150)
            except Exception as e:
                print(f"DEBUG: PDF->image conversion failed: {e}")
                images = []

        elif filename.endswith(('.jpg', '.jpeg', '.png')):
            img = Image.open(io.BytesIO(file_bytes))
            images = [_resize_image_max(img)]
        else:
            return {'text': '', 'method': 'unsupported', 'error': 'Unsupported file format'}

        # Process pages sequentially (no parallelization)
        for img in images:
            # Primary OCR: EasyOCR
            primary_text, primary_conf = _easyocr_ocr(img)
            # Only load paddle if needed
            fallback_text, fallback_conf = '', 0.0

            use_fallback = False
            # Decide if primary is weak: very short or low confidence
            if (not primary_text) or (len(primary_text.strip()) < 20) or (primary_conf < 0.35):
                # Try PaddleOCR as fallback
                fallback_text, fallback_conf = _paddleocr_ocr(img)
                # Debug lengths
                print(f"DEBUG: OCR lengths primary={len(primary_text)} (conf={primary_conf}) fallback={len(fallback_text)} (conf={fallback_conf})")
                # Compare scores
                lang_primary, _ = detect_language_summary(primary_text)
                lang_fallback, _ = detect_language_summary(fallback_text)
                score_primary = _score_text(primary_text, lang_primary)
                score_fallback = _score_text(fallback_text, lang_fallback)
                if score_fallback > score_primary * 1.5:
                    use_fallback = True

            # If both primary and fallback are empty/very short, try pytesseract as a last resort
            if (not primary_text or len(primary_text.strip()) < 10) and (not fallback_text or len(fallback_text.strip()) < 10):
                # Choose a language hint: prefer primary detection, then fallback, else default
                hint_lang, _ = detect_language_summary(primary_text or fallback_text or "")
                pt_text, pt_conf = _pytesseract_ocr(img, hint_lang)
                print(f"DEBUG: pytesseract produced {len(pt_text)} chars (approx conf={pt_conf})")
                if len(pt_text.strip()) > len(primary_text.strip()) and len(pt_text.strip()) > len(fallback_text.strip()):
                    combined_texts.append(pt_text)
                    confidences.append(pt_conf)
                    method_used = 'pytesseract_fallback'
                    continue

            if use_fallback and fallback_text:
                combined_texts.append(fallback_text)
                confidences.append(fallback_conf)
                method_used = 'paddle_fallback'
            else:
                combined_texts.append(primary_text)
                confidences.append(primary_conf)
                method_used = 'easyocr'

        final_text = "\n\n".join([t for t in combined_texts if t])
        avg_conf = float(np.mean(confidences)) if confidences else 0.0

        det_lang, det_conf = detect_language_summary(final_text)
        # Map avg_conf to high/medium/low
        if avg_conf >= 0.7:
            conf_label = 'high'
        elif avg_conf >= 0.35:
            conf_label = 'medium'
        else:
            conf_label = 'low'

        return {
            'text': final_text,
            'method': method_used,
            'confidence': conf_label,
            'detected_language': det_lang,
            'detection_confidence': det_conf,
            'disclaimer': 'OCR text may contain inaccuracies, especially for handwritten or regional-language documents. Please verify before analysis.'
        }

    except Exception as e:
        print(f"OCR pipeline error: {e}")
        return {'text': '', 'method': 'error', 'error': str(e)}
