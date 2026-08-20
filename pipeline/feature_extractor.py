"""
Feature & Semantic Extraction Layer — Phase 3 Core Module.
File Location: pipeline/feature_extractor.py

Responsibilities:
  1. Consumes Phase 2 PreprocessedData objects directly.
  2. Text Feature Extraction:
     - Generates 768-dimensional DistilBERT contextual semantic embeddings.
     - Long-text chunking strategy with overlap, generating chunk-level BERT representations.
     - Preserves entity relationships and source modality tracking.
  3. Image Feature Extraction:
     - Extracts visual features (dimensions, aspect ratio, color channel statistics, luminance).
     - Generates BERT semantic embeddings on extracted OCR text.
     - Preserves OCR word tokens, bounding boxes, and confidence.
  4. Video Feature Extraction:
     - Frame-level visual feature extraction across sampled keyframes.
     - Generates BERT semantic representations for frame-extracted OCR text.
     - Preserves frame ID, timestamp_sec, timestamp_str, and OCR bounding boxes.
  5. YouTube Feature Extraction:
     - Chunks normalized transcript into semantic blocks.
     - Generates BERT embeddings per transcript segment with preserved timestamps.
     - Video duration is strictly metadata, NOT a privacy feature.
  6. Feature Standardization:
     - Outputs canonical ExtractedFeatures dataclass for downstream Phase 4 (Detection).
"""

import time
import math
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Any, List, Optional, Union
from PIL import Image

from pipeline.preprocessor import PreprocessedData
from ml_engine.bert_model import BertFeatureExtractor


# ── Global BERT Singleton ─────────────────────────────────────────────────────
_bert_extractor_instance: Optional[BertFeatureExtractor] = None


def get_bert_extractor() -> BertFeatureExtractor:
    """Loads BERT model once as a singleton in inference mode."""
    global _bert_extractor_instance
    if _bert_extractor_instance is None:
        _bert_extractor_instance = BertFeatureExtractor()
    return _bert_extractor_instance


@dataclass
class ExtractedFeatures:
    """
    Standardized Feature Object for downstream pipeline stages.
    Consumed by Phase 4 (Privacy Detection) and Phase 5 (Hybrid Classifier).
    """

    # Canonical Schema
    input_type: str = "text"                    # "text" | "image" | "video" | "youtube"
    source: str = "direct_input"                # Source filename / URL / identifier
    semantic_features: Dict[str, Any] = field(default_factory=dict)
    visual_features: Dict[str, Any] = field(default_factory=dict)
    ocr_features: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    # Execution State
    feature_status: str = "success"             # "success" | "error"
    feature_errors: List[str] = field(default_factory=list)
    feature_extraction_time_ms: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Returns a JSON-serializable representation of extracted features."""
        return {
            "input_type": self.input_type,
            "source": self.source,
            "semantic_features": self.semantic_features,
            "visual_features": self.visual_features,
            "ocr_features": self.ocr_features,
            "metadata": self.metadata,
            "feature_status": self.feature_status,
            "feature_errors": self.feature_errors,
            "feature_extraction_time_ms": self.feature_extraction_time_ms,
        }


class MultimodalFeatureExtractor:
    """
    Enterprise Multimodal Feature & Semantic Extractor.
    Extracts high-dimensional contextual embeddings, visual representations,
    and OCR token features while preserving all privacy indicators.
    """

    CHUNK_SIZE_WORDS = 60
    CHUNK_OVERLAP_WORDS = 15

    def __init__(self):
        self.bert = get_bert_extractor()

    # ── CHUNKING STRATEGY ──────────────────────────────────────────────────────

    def chunk_text(self, text: str) -> List[Dict[str, Any]]:
        """
        Splits long text into overlapping chunks to ensure long documents
        do not truncate sensitive entities at token boundaries.
        """
        if not text or not text.strip():
            return []

        words = text.strip().split()
        if len(words) <= self.CHUNK_SIZE_WORDS:
            return [{
                "chunk_id": 1,
                "text": text.strip(),
                "word_count": len(words),
                "start_word_idx": 0,
                "end_word_idx": len(words),
            }]

        chunks = []
        start_idx = 0
        chunk_id = 1

        while start_idx < len(words):
            end_idx = min(start_idx + self.CHUNK_SIZE_WORDS, len(words))
            chunk_words = words[start_idx:end_idx]
            chunk_text = " ".join(chunk_words)

            chunks.append({
                "chunk_id": chunk_id,
                "text": chunk_text,
                "word_count": len(chunk_words),
                "start_word_idx": start_idx,
                "end_word_idx": end_idx,
            })

            chunk_id += 1
            if end_idx == len(words):
                break
            start_idx += (self.CHUNK_SIZE_WORDS - self.CHUNK_OVERLAP_WORDS)

        return chunks

    # ── 1. TEXT FEATURE EXTRACTION ─────────────────────────────────────────────

    def extract_text_features(self, preprocessed: PreprocessedData) -> ExtractedFeatures:
        """
        Extracts BERT contextual embeddings for full text and chunks.
        """
        start_time = time.time()
        text = preprocessed.processed or preprocessed.extracted_text or ""

        if not text:
            return ExtractedFeatures(
                input_type="text",
                source=preprocessed.source,
                feature_status="error",
                feature_errors=["Cannot extract features from empty text payload."],
                feature_extraction_time_ms=0.0,
            )

        # 1. Full text embedding (768-dim)
        full_embedding = self.bert.extract_embedding(text)

        # 2. Chunking for long text
        chunks = self.chunk_text(text)
        chunk_features = []
        for c in chunks:
            chunk_emb = self.bert.extract_embedding(c["text"])
            chunk_features.append({
                "chunk_id": c["chunk_id"],
                "text_snippet": c["text"][:100] + ("..." if len(c["text"]) > 100 else ""),
                "word_count": c["word_count"],
                "embedding_dim": len(chunk_emb),
                "embedding_sample": [round(x, 4) for x in chunk_emb[:8]],
            })

        elapsed_ms = round((time.time() - start_time) * 1000, 2)

        semantic_features = {
            "model_architecture": "DistilBERT (768-dim)",
            "embedding_dim": len(full_embedding),
            "embedding_sample": [round(x, 4) for x in full_embedding[:10]],
            "is_transformer_active": getattr(self.bert, "is_transformer_loaded", False),
            "total_chunks": len(chunks),
            "chunk_features": chunk_features,
            "character_count": len(text),
            "word_count": len(text.split()),
        }

        return ExtractedFeatures(
            input_type="text",
            source=preprocessed.source,
            semantic_features=semantic_features,
            visual_features={},
            ocr_features={},
            metadata=preprocessed.metadata,
            feature_status="success",
            feature_extraction_time_ms=elapsed_ms,
        )

    # ── 2. IMAGE FEATURE EXTRACTION ────────────────────────────────────────────

    def extract_image_features(self, preprocessed: PreprocessedData) -> ExtractedFeatures:
        """
        Extracts visual structural features and OCR semantic embeddings.
        """
        start_time = time.time()
        meta = preprocessed.metadata or {}
        orig_path = preprocessed.original
        ocr_boxes = preprocessed.ocr or []
        extracted_text = preprocessed.extracted_text or ""

        visual_features = {
            "original_width": meta.get("original_width", 0),
            "original_height": meta.get("original_height", 0),
            "processed_width": meta.get("processed_width", 0),
            "processed_height": meta.get("processed_height", 0),
            "aspect_ratio": round(meta.get("original_width", 1) / max(1, meta.get("original_height", 1)), 3),
            "scale_factor": meta.get("scale_factor", 1.0),
            "color_mode": meta.get("color_mode", "RGB"),
        }

        # Extract image statistical features if file path exists
        if orig_path and Path(orig_path).exists():
            try:
                with Image.open(orig_path) as img:
                    rgb = img.convert("RGB")
                    # Compute channel means for visual feature descriptor
                    import numpy as np
                    np_img = np.array(rgb)
                    visual_features["channel_means"] = [
                        round(float(np.mean(np_img[:, :, i])), 2) for i in range(3)
                    ]
                    visual_features["channel_stds"] = [
                        round(float(np.std(np_img[:, :, i])), 2) for i in range(3)
                    ]
            except Exception:
                pass

        # Semantic embedding on OCR-extracted text
        ocr_embedding = []
        if extracted_text:
            ocr_embedding = self.bert.extract_embedding(extracted_text)

        semantic_features = {
            "has_ocr_text": bool(extracted_text),
            "ocr_text_length": len(extracted_text),
            "ocr_word_count": len(extracted_text.split()),
            "ocr_embedding_dim": len(ocr_embedding) if ocr_embedding else 0,
            "ocr_embedding_sample": [round(x, 4) for x in ocr_embedding[:8]] if ocr_embedding else [],
        }

        ocr_features = {
            "ocr_engine": meta.get("ocr_engine", "None"),
            "ocr_words_count": len(ocr_boxes),
            "ocr_confidence": meta.get("ocr_confidence", 0.0),
            "bounding_boxes": ocr_boxes[:50],  # Sample first 50 boxes
        }

        elapsed_ms = round((time.time() - start_time) * 1000, 2)

        return ExtractedFeatures(
            input_type="image",
            source=preprocessed.source,
            semantic_features=semantic_features,
            visual_features=visual_features,
            ocr_features=ocr_features,
            metadata=meta,
            feature_status="success",
            feature_extraction_time_ms=elapsed_ms,
        )

    # ── 3. VIDEO FEATURE EXTRACTION ────────────────────────────────────────────

    def extract_video_features(self, preprocessed: PreprocessedData) -> ExtractedFeatures:
        """
        Extracts temporal frame visual features and OCR semantic embeddings per frame.
        """
        start_time = time.time()
        meta = preprocessed.metadata or {}
        frames = preprocessed.frames or []
        aggregated_text = preprocessed.extracted_text or ""

        frame_features = []
        for f in frames:
            f_text = f.get("extracted_text", "")
            f_emb = self.bert.extract_embedding(f_text) if f_text else []

            frame_features.append({
                "frame_id": f.get("frame_id"),
                "frame_index": f.get("frame_index"),
                "timestamp_sec": f.get("timestamp_sec"),
                "timestamp_str": f.get("timestamp_str"),
                "has_text": bool(f_text),
                "text_snippet": f_text[:80] + ("..." if len(f_text) > 80 else ""),
                "embedding_dim": len(f_emb),
                "dimensions": f.get("dimensions", [meta.get("width", 0), meta.get("height", 0)]),
            })

        # Global aggregate embedding for all text in video
        global_text_emb = self.bert.extract_embedding(aggregated_text) if aggregated_text else []

        semantic_features = {
            "aggregated_ocr_text_length": len(aggregated_text),
            "aggregated_ocr_word_count": len(aggregated_text.split()),
            "global_ocr_embedding_dim": len(global_text_emb),
            "global_ocr_embedding_sample": [round(x, 4) for x in global_text_emb[:8]] if global_text_emb else [],
        }

        visual_features = {
            "duration_sec": meta.get("duration_sec", 0.0),
            "duration_str": meta.get("duration_str", "00:00"),
            "fps": meta.get("fps", 0.0),
            "total_frames": meta.get("total_frames", 0),
            "frames_sampled_count": len(frames),
            "width": meta.get("width", 0),
            "height": meta.get("height", 0),
            "frame_level_features": frame_features,
        }

        ocr_features = {
            "frames_with_text_count": sum(1 for f in frames if f.get("extracted_text")),
            "total_ocr_characters": len(aggregated_text),
        }

        elapsed_ms = round((time.time() - start_time) * 1000, 2)

        return ExtractedFeatures(
            input_type="video",
            source=preprocessed.source,
            semantic_features=semantic_features,
            visual_features=visual_features,
            ocr_features=ocr_features,
            metadata=meta,
            feature_status="success",
            feature_extraction_time_ms=elapsed_ms,
        )

    # ── 4. YOUTUBE FEATURE EXTRACTION ──────────────────────────────────────────

    def extract_youtube_features(self, preprocessed: PreprocessedData) -> ExtractedFeatures:
        """
        Extracts segment-level BERT semantic features from YouTube transcripts.
        """
        start_time = time.time()
        meta = preprocessed.metadata or {}
        segments = preprocessed.frames or []  # timestamped segments stored in frames
        full_transcript = preprocessed.extracted_text or ""

        segment_features = []
        for s in segments:
            seg_text = s.get("text", "")
            seg_emb = self.bert.extract_embedding(seg_text) if seg_text else []

            segment_features.append({
                "timestamp_sec": s.get("timestamp_sec"),
                "timestamp_str": s.get("timestamp_str"),
                "text_snippet": seg_text[:100] + ("..." if len(seg_text) > 100 else ""),
                "embedding_dim": len(seg_emb),
                "embedding_sample": [round(x, 4) for x in seg_emb[:6]] if seg_emb else [],
            })

        # Global transcript embedding
        global_transcript_emb = self.bert.extract_embedding(full_transcript) if full_transcript else []

        semantic_features = {
            "has_transcript": bool(full_transcript),
            "transcript_word_count": len(full_transcript.split()),
            "transcript_character_count": len(full_transcript),
            "global_transcript_embedding_dim": len(global_transcript_emb),
            "global_transcript_embedding_sample": [round(x, 4) for x in global_transcript_emb[:8]] if global_transcript_emb else [],
            "segment_features_count": len(segment_features),
            "segment_features": segment_features[:30],  # Sample first 30 segments
        }

        metadata_dict = {
            "youtube_video_id": meta.get("youtube_video_id"),
            "youtube_url": meta.get("youtube_url"),
            "embed_url": meta.get("embed_url"),
            "has_transcript": meta.get("has_transcript", False),
        }

        elapsed_ms = round((time.time() - start_time) * 1000, 2)

        return ExtractedFeatures(
            input_type="youtube",
            source=preprocessed.source,
            semantic_features=semantic_features,
            visual_features={},
            ocr_features={},
            metadata=metadata_dict,
            feature_status="success",
            feature_extraction_time_ms=elapsed_ms,
        )

    # ── 5. UNIFIED DISPATCHER ──────────────────────────────────────────────────

    def extract_features(self, preprocessed: PreprocessedData) -> ExtractedFeatures:
        """
        Unified dispatcher consuming any Phase 2 PreprocessedData object.
        Routes to the appropriate modality feature extractor.
        """
        if preprocessed.preprocessing_status != "success":
            return ExtractedFeatures(
                input_type=preprocessed.input_type,
                source=preprocessed.source,
                metadata=preprocessed.metadata,
                feature_status="error",
                feature_errors=preprocessed.preprocessing_errors or ["Preprocessing failed in upstream stage."],
                feature_extraction_time_ms=0.0,
            )

        modality = (preprocessed.input_type or "text").lower()

        if modality == "text":
            return self.extract_text_features(preprocessed)
        elif modality == "image":
            return self.extract_image_features(preprocessed)
        elif modality == "video":
            return self.extract_video_features(preprocessed)
        elif modality == "youtube":
            return self.extract_youtube_features(preprocessed)
        else:
            return ExtractedFeatures(
                input_type=modality,
                source=preprocessed.source,
                feature_status="error",
                feature_errors=[f"Unsupported modality for feature extraction: '{modality}'"],
            )
