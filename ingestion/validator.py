import os
from typing import Tuple, Dict, Any, Optional
import config

ALLOWED_IMAGE_EXTS = config.ALLOWED_IMAGE_EXTENSIONS
ALLOWED_VIDEO_EXTS = config.ALLOWED_VIDEO_EXTENSIONS
ALLOWED_DOC_EXTS = config.ALLOWED_DOCUMENT_EXTENSIONS


class InputValidator:
    """
    Validates input payloads across supported modalities: Text, Image, Video, Document.
    """

    @staticmethod
    def validate_input(
        input_data: Any,
        modality: str,
        filename: Optional[str] = None
    ) -> Tuple[bool, str, Dict[str, Any]]:
        meta = {
            "modality": modality,
            "filename": filename or "inline_prompt",
            "size_bytes": 0,
            "format_valid": True
        }

        if modality == "text":
            if not isinstance(input_data, str) or not input_data.strip():
                return False, "Text input cannot be empty.", meta
            meta["size_bytes"] = len(input_data.encode('utf-8'))
            return True, "Valid text input.", meta

        elif modality == "image":
            if not input_data:
                return False, "No image payload provided.", meta
            
            meta["size_bytes"] = len(input_data)
            if filename:
                ext = os.path.splitext(filename)[1].lower()
                if ext not in ALLOWED_IMAGE_EXTS:
                    meta["format_valid"] = False
                    return False, f"Unsupported image extension '{ext}'. Allowed: {ALLOWED_IMAGE_EXTS}", meta
            return True, "Valid image payload.", meta

        elif modality == "video":
            if not input_data:
                return False, "No video payload provided.", meta

            meta["size_bytes"] = len(input_data)
            if filename:
                ext = os.path.splitext(filename)[1].lower()
                if ext not in ALLOWED_VIDEO_EXTS:
                    meta["format_valid"] = False
                    return False, f"Unsupported video extension '{ext}'. Allowed: {ALLOWED_VIDEO_EXTS}", meta
            return True, "Valid video payload.", meta

        elif modality == "document":
            if not input_data:
                return False, "No document payload provided.", meta

            meta["size_bytes"] = len(input_data)
            if filename:
                ext = os.path.splitext(filename)[1].lower()
                if ext not in ALLOWED_DOC_EXTS:
                    meta["format_valid"] = False
                    return False, f"Unsupported document extension '{ext}'. Allowed: {ALLOWED_DOC_EXTS}", meta
            return True, "Valid document payload.", meta

        return False, f"Unknown input modality '{modality}'.", meta
