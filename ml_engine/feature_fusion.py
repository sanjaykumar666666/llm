"""
Multimodal Feature Fusion Engine.
File Location: ml_engine/feature_fusion.py
"""

from typing import Dict, Any, Optional
from processing.text_processor import TextProcessor


class MultimodalFeatureFusion:
    """
    Aggregates text prompts, image OCR output, video frame OCR output, and document text
    into a unified payload and feature representation for downstream ML models.
    """

    def __init__(self):
        self.text_processor = TextProcessor()

    def fuse_features(
        self,
        modality: str,
        text_content: Optional[str] = None,
        ocr_text: Optional[str] = None,
        frames_processed: int = 0,
        doc_metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Merges input streams and extracts unified structural, statistical, and security features.
        """
        combined_text_parts = []

        if text_content and text_content.strip():
            combined_text_parts.append(text_content.strip())

        if ocr_text and ocr_text.strip():
            combined_text_parts.append(ocr_text.strip())

        unified_text_sequence = " ".join(combined_text_parts)
        cleaned_unified_text = self.text_processor.clean_text(unified_text_sequence)

        # Run Deterministic PII Scan & Entropy Analysis
        text_analysis = self.text_processor.process(cleaned_unified_text)

        # Build Metadata Features
        metadata_features = {
            "is_text_modality": 1 if modality == "text" else 0,
            "is_image_modality": 1 if modality == "image" else 0,
            "is_video_modality": 1 if modality == "video" else 0,
            "is_document_modality": 1 if modality == "document" else 0,
            "has_ocr_content": 1 if ocr_text and len(ocr_text.strip()) > 0 else 0,
            "video_frames_sampled": frames_processed,
            "character_count": text_analysis["character_count"],
            "word_count": text_analysis["word_count"],
            "shannon_entropy": text_analysis["shannon_entropy"],
            "max_entity_severity": text_analysis["max_entity_severity"],
            "regex_pii_detected_count": len(text_analysis["detected_entities"]),
            "contains_regex_pii": 1 if text_analysis["contains_regex_pii"] else 0,
        }

        return {
            "modality": modality,
            "unified_text": cleaned_unified_text,
            "detected_entities": text_analysis["detected_entities"],
            "detected_entity_types": text_analysis["detected_entity_types"],
            "metadata_features": metadata_features,
            "shannon_entropy": text_analysis["shannon_entropy"],
            "max_entity_severity": text_analysis["max_entity_severity"],
            "doc_metadata": doc_metadata or {},
        }
