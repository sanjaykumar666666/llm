"""
Image Processing and Optical Character Recognition (OCR) Engine.
File Location: processing/image_processor.py
"""

import os
import io
from pathlib import Path
from typing import Dict, Any, Union
from PIL import Image, ImageEnhance, ImageOps
import pytesseract
from processing.text_processor import TextProcessor

# Auto-configure Tesseract binary path on Windows if available
POSSIBLE_TESSERACT_PATHS = [
    r"C:\Program Files\Tesseract-OCR\tesseract.exe",
    r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
    os.path.expanduser(r"~\AppData\Local\Programs\Tesseract-OCR\tesseract.exe"),
]

TESSERACT_AVAILABLE = False
for p in POSSIBLE_TESSERACT_PATHS:
    if os.path.exists(p):
        pytesseract.pytesseract.tesseract_cmd = p
        TESSERACT_AVAILABLE = True
        break


class ImageProcessor:
    """
    Engine to preprocess images, execute OCR, and analyze extracted text for sensitive content.
    """

    def __init__(self):
        self.text_processor = TextProcessor()

    def preprocess_image(self, image: Image.Image) -> Image.Image:
        """
        Enhances image quality to maximize Tesseract OCR accuracy.
        """
        gray_img = image.convert("L")
        gray_img = ImageOps.autocontrast(gray_img)
        enhancer = ImageEnhance.Contrast(gray_img)
        enhanced_img = enhancer.enhance(1.8)
        return enhanced_img

    def extract_text_from_image(self, image_input: Union[str, Path, Image.Image, bytes]) -> str:
        """
        Loads an image, applies preprocessing, and extracts text via Tesseract.
        """
        try:
            if isinstance(image_input, bytes):
                image = Image.open(io.BytesIO(image_input))
            elif isinstance(image_input, (str, Path)):
                image = Image.open(image_input)
            else:
                image = image_input

            processed_img = self.preprocess_image(image)
            extracted_text = pytesseract.image_to_string(processed_img, config="--psm 3")
            return extracted_text.strip()

        except Exception:
            return ""

    def process(self, image_input: Union[str, Path, Image.Image, bytes]) -> Dict[str, Any]:
        """
        Executes complete image inspection pipeline: OCR + PII Scanning.
        """
        extracted_text = self.extract_text_from_image(image_input)
        text_analysis = self.text_processor.process(extracted_text)

        return {
            "extracted_text": extracted_text,
            "character_count": len(extracted_text),
            "word_count": text_analysis["word_count"],
            "detected_entities": text_analysis["detected_entities"],
            "detected_entity_types": text_analysis["detected_entity_types"],
            "contains_regex_pii": text_analysis["contains_regex_pii"],
            "shannon_entropy": text_analysis["shannon_entropy"],
            "ocr_available": TESSERACT_AVAILABLE,
        }
