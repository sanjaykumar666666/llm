"""
Backward-compatible alias for classifier.bert_embedder.
Delegates to ml_engine.bert_model.
"""

from ml_engine.bert_model import BertFeatureExtractor


class BERTEmbedder:
    def __init__(self):
        self.extractor = BertFeatureExtractor()

    def get_embeddings(self, text: str):
        return self.extractor.extract_embedding(text)
