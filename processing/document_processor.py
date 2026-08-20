"""
Document Processing & Ingestion Engine (PDF, TXT, CSV, JSON, Markdown).
File Location: processing/document_processor.py
"""

import json
import csv
import io
import re
from pathlib import Path
from typing import Dict, Any, Union
from processing.text_processor import TextProcessor


class DocumentProcessor:
    """
    Parses structural and raw textual content from document files (.pdf, .txt, .csv, .json, .md).
    """

    def __init__(self):
        self.text_processor = TextProcessor()

    def process_file_bytes(self, file_bytes: bytes, filename: str) -> Dict[str, Any]:
        """
        Parses document byte content according to file extension.
        """
        ext = Path(filename).suffix.lower()
        extracted_text = ""
        doc_metadata = {"filename": filename, "extension": ext, "bytes": len(file_bytes)}

        try:
            if ext in [".txt", ".md", ".log"]:
                extracted_text = file_bytes.decode("utf-8", errors="ignore")

            elif ext == ".json":
                parsed = json.loads(file_bytes.decode("utf-8", errors="ignore"))
                extracted_text = json.dumps(parsed, indent=2)
                doc_metadata["json_keys_count"] = len(parsed) if isinstance(parsed, dict) else len(parsed)

            elif ext == ".csv":
                text_str = file_bytes.decode("utf-8", errors="ignore")
                reader = csv.reader(io.StringIO(text_str))
                rows = list(reader)
                extracted_text = "\n".join([", ".join(row) for row in rows])
                doc_metadata["row_count"] = len(rows)

            elif ext == ".pdf":
                extracted_text = self._extract_pdf_text(file_bytes)
                doc_metadata["parser"] = "PDF Stream Parser"

            else:
                extracted_text = file_bytes.decode("utf-8", errors="ignore")

        except Exception as e:
            extracted_text = f"[DOCUMENT PARSE ERROR]: Could not parse file '{filename}': {str(e)}"

        # Run text processing analysis on extracted content
        analysis = self.text_processor.process(extracted_text)

        return {
            "extracted_text": extracted_text,
            "character_count": len(extracted_text),
            "word_count": len(extracted_text.split()),
            "detected_entities": analysis["detected_entities"],
            "detected_entity_types": analysis["detected_entity_types"],
            "contains_regex_pii": analysis["contains_regex_pii"],
            "shannon_entropy": analysis["shannon_entropy"],
            "doc_metadata": doc_metadata,
        }

    def _extract_pdf_text(self, pdf_bytes: bytes) -> str:
        """
        Extracts printable text from PDF byte streams using pypdf or stream regex extraction fallback.
        """
        try:
            import pypdf
            reader = pypdf.PdfReader(io.BytesIO(pdf_bytes))
            text_pages = [page.extract_text() for page in reader.pages if page.extract_text()]
            if text_pages:
                return "\n\n".join(text_pages)
        except ImportError:
            pass
        except Exception:
            pass

        # Fallback text extraction from raw PDF byte stream
        raw_stream = pdf_bytes.decode("latin1", errors="ignore")
        text_matches = re.findall(r"\(([^()]{3,})\)", raw_stream)
        if text_matches:
            return " ".join(text_matches[:200])
        return "[PDF DOCUMENT]: Binary stream parsed. No readable text streams detected."
