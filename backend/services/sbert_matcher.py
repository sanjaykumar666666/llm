"""
SBERT Sentence Embeddings & Cosine Similarity Semantic Matching Engine.
File Location: backend/services/sbert_matcher.py
"""

import math
import numpy as np
from typing import Dict, Any, List

# Enterprise Sensitive Policy Benchmarks for Cosine Similarity Matching
SENSITIVE_BENCHMARKS = [
    {
        "category": "Financial Credentials",
        "description": "Bank account details, IBAN, routing numbers, and credit card credentials.",
        "text": "My bank account number routing number credit card pin CVV password financial account balance transfer",
        "keywords": ["bank", "account", "routing", "credit card", "pin", "cvv", "iban", "swift", "deposit", "transfer"]
    },
    {
        "category": "Personal Identifiable Information (PII)",
        "description": "Government identity numbers, SSN, Aadhaar, passport, and phone numbers.",
        "text": "Social security number Aadhaar card driver license passport number email phone address date of birth national ID",
        "keywords": ["aadhaar", "ssn", "passport", "license", "email", "phone", "address", "identity", "social security"]
    },
    {
        "category": "Healthcare & Medical Data",
        "description": "Medical records, clinical diagnosis, prescription details, and health condition disclosures.",
        "text": "Medical history health records patient diagnosis clinical trial prescription drug condition treatment hospital MRN",
        "keywords": ["medical", "health", "patient", "diagnosis", "prescription", "hospital", "doctor", "mrn", "disease"]
    },
    {
        "category": "Security Keys & Credentials",
        "description": "API secret keys, passwords, bearer tokens, AWS keys, and private SSH keys.",
        "text": "Password secret key API key AWS access token authorization bearer private key ssh password token credential",
        "keywords": ["password", "secret", "api_key", "token", "aws", "bearer", "private_key", "ssh", "key", "credential"]
    },
    {
        "category": "Confidential Enterprise Specs",
        "description": "Internal server passwords, proprietary database connection strings, and unannounced project roadmaps.",
        "text": "Internal confidential proprietary server connection string database password secret code source code architecture roadmap",
        "keywords": ["confidential", "internal", "proprietary", "connection string", "postgres", "mysql", "roadmap", "source code"]
    }
]


class SBERTSemanticMatcher:
    """
    Computes SBERT sentence vector embeddings and Cosine Similarity scores
    against sensitive enterprise benchmark policies.
    """

    def __init__(self):
        self.is_sbert_loaded = False
        self.model = None
        self._initialize_sbert()

    def _initialize_sbert(self):
        """Attempts to load sentence-transformers SBERT model cleanly."""
        try:
            from sentence_transformers import SentenceTransformer
            self.model = SentenceTransformer("all-MiniLM-L6-v2")
            self.is_sbert_loaded = True
        except Exception:
            self.is_sbert_loaded = False

    def _get_embedding(self, text: str) -> List[float]:
        """Returns normalized 384-dimensional vector embedding."""
        if not text or not text.strip():
            return [0.0] * 384

        if self.is_sbert_loaded and self.model:
            try:
                emb = self.model.encode(text, convert_to_numpy=True)
                norm = np.linalg.norm(emb)
                if norm > 0:
                    emb = emb / norm
                return emb.tolist()
            except Exception:
                pass

        # Deterministic lightweight term-vector embedding fallback
        words = set(text.lower().split())
        vocab_seed = [
            "bank", "account", "number", "card", "password", "secret", "key", "ssn", "aadhaar",
            "email", "phone", "medical", "patient", "confidential", "database", "token", "private"
        ]
        vector = []
        for v in vocab_seed:
            val = 1.0 if v in text.lower() else (0.4 if any(v in w for w in words) else 0.05)
            vector.append(val)
        
        # Expand vector to 384-dim deterministically
        full_vec = []
        for i in range(384):
            idx = i % len(vector)
            val = vector[idx] * (1.0 + 0.1 * math.sin(i))
            full_vec.append(val)
        
        arr = np.array(full_vec)
        norm = np.linalg.norm(arr)
        if norm > 0:
            arr = arr / norm
        return arr.tolist()

    @staticmethod
    def cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
        """Computes Cosine Similarity dot product between two normalized vectors."""
        v1 = np.array(vec1)
        v2 = np.array(vec2)
        dot = float(np.dot(v1, v2))
        return float(min(1.0, max(0.0, dot)))

    def match_semantic_policy(self, text: str) -> Dict[str, Any]:
        """
        Evaluates input text against sensitive enterprise benchmarks using SBERT sentence embeddings + Cosine Similarity.
        """
        if not text or not text.strip():
            return {
                "highest_similarity": 0.0,
                "top_matched_category": "SAFE",
                "cosine_similarity_score": 0.0,
                "benchmark_matches": [],
                "is_sbert_model": self.is_sbert_loaded
            }

        input_emb = self._get_embedding(text)
        lower_text = text.lower()

        matches = []
        max_sim = 0.0
        top_cat = "SAFE"

        for b in SENSITIVE_BENCHMARKS:
            b_emb = self._get_embedding(b["text"])
            sim = self.cosine_similarity(input_emb, b_emb)

            # Keyword presence boosting
            kw_hits = sum(1 for kw in b["keywords"] if kw in lower_text)
            if kw_hits > 0:
                sim = min(1.0, sim + 0.15 * kw_hits)

            sim_score = round(sim * 100.0, 1)

            if sim > max_sim:
                max_sim = sim
                top_cat = b["category"]

            matches.append({
                "category": b["category"],
                "description": b["description"],
                "similarity_percentage": sim_score,
                "similarity_score": round(sim, 4),
                "is_match": sim > 0.40
            })

        matches.sort(key=lambda x: x["similarity_score"], reverse=True)

        return {
            "highest_similarity_percentage": round(max_sim * 100.0, 1),
            "highest_similarity_score": round(max_sim, 4),
            "top_matched_category": top_cat if max_sim >= 0.35 else "SAFE / GENERAL QUERY",
            "benchmark_matches": matches,
            "is_sbert_model": self.is_sbert_loaded
        }
