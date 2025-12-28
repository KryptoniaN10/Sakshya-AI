import io
import os
from typing import List, Tuple

import requests
from PIL import Image
import pdfplumber
from pdf2image import convert_from_bytes
from langdetect import detect_langs


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


def _remote_paddle_ocr(img: Image.Image, url: str, timeout: int = 30) -> Tuple[str, float, object]:
    if not url:
        return "", 0.0, {"error": "no_url"}
    try:
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        buf.seek(0)
        files = {"file": ("image.png", buf, "image/png")}
        resp = requests.post(url, files=files, timeout=timeout)
        resp_info = {"status_code": resp.status_code}
        # try to parse JSON body, otherwise return text
        try:
            data = resp.json()
            resp_info["body"] = data
        except Exception:
            resp_info["body"] = resp.text

        if resp.status_code != 200:
            print(f"Remote PaddleOCR returned status {resp.status_code}")
            return "", 0.0, resp_info

        data = resp_info.get("body") if isinstance(resp_info.get("body"), dict) else {}
        text = (data.get("text") if isinstance(data, dict) else None) or (data.get("result") if isinstance(data, dict) else None) or (data.get("ocr_text") if isinstance(data, dict) else None) or ""
        conf = 0.0
        try:
            if isinstance(data, dict):
                conf = float(data.get("confidence") or data.get("avg_conf") or 0.0)
        except Exception:
            conf = 0.0
        return text.strip(), conf, resp_info
    except Exception as e:
        print(f"Remote PaddleOCR error: {e}")
        return "", 0.0, {"error": str(e)}


def _detect_language_summary(text: str) -> Tuple[str, str]:
    try:
        langs = detect_langs(text)
        if not langs:
            return "en", "low"
        top = langs[0]
        code = top.lang
        prob = top.prob
        supported = ["en", "hi", "ml", "ta", "te", "kn", "bn"]
        if code not in supported:
            return "en", "low"
        if prob > 0.85:
            conf = "high"
        elif prob > 0.6:
            conf = "medium"
        else:
            conf = "low"
        return code, conf
    except Exception:
        return "en", "low"


async def extract_text_from_file(file_bytes: bytes, filename: str) -> dict:
    filename = filename.lower()
    PADDLE_OCR_URL = os.getenv("PADDLE_OCR_URL")
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

        if not PADDLE_OCR_URL:
            return {'text': '', 'method': 'error', 'error': 'PADDLE_OCR_URL not configured in environment'}

        combined_texts = []
        confidences = []
        remote_responses = []
        for img in images:
            text, conf, resp_info = _remote_paddle_ocr(img, PADDLE_OCR_URL)
            print(f"DEBUG: Remote PaddleOCR produced {len(text)} chars (conf={conf})")
            remote_responses.append(resp_info)
            if text:
                combined_texts.append(text)
                confidences.append(conf)

        final_text = "\n\n".join([t for t in combined_texts if t])
        avg_conf = float(sum(confidences) / len(confidences)) if confidences else 0.0
        if avg_conf >= 0.7:
            conf_label = 'high'
        elif avg_conf >= 0.35:
            conf_label = 'medium'
        else:
            conf_label = 'low'

        det_lang, det_conf = _detect_language_summary(final_text)
        result = {
            'text': final_text,
            'method': 'paddle_remote',
            'confidence': conf_label,
            'detected_language': det_lang,
            'detection_confidence': det_conf,
            'disclaimer': 'OCR text may contain inaccuracies. Please verify before analysis.'
        }

        # Include raw remote responses when debugging is enabled via env flag
        debug_flag = os.getenv('PADDLE_OCR_DEBUG', '').lower() in ('1', 'true', 'yes')
        if debug_flag:
            result['remote_responses'] = remote_responses

        return result
    except Exception as e:
        print(f"OCR pipeline error: {e}")
        return {'text': '', 'method': 'error', 'error': str(e)}