import pytest
from ingestion.validator import InputValidator
from ingestion.pipeline import MultimodalIngestionPipeline
from classifier.hybrid_model import HybridBERTNaiveBayesPipeline
from gate.decision_gate import AutomatedDecisionGate
from gate.pii_sanitizer import PIISanitizer
from llm.gemini_client import GeminiLLMClient
from evaluation.metrics import PrivacyEvaluationMetrics
from processing.document_processor import DocumentProcessor


def test_input_validator():
    val = InputValidator()
    is_valid, msg, meta = val.validate_input("Hello world", "text")
    assert is_valid is True
    
    is_valid_img, _, _ = val.validate_input(b"bytes", "image", "sample.png")
    assert is_valid_img is True

    is_valid_doc, _, _ = val.validate_input(b"bytes", "document", "report.pdf")
    assert is_valid_doc is True

    is_valid_bad, _, _ = val.validate_input(b"bytes", "image", "sample.exe")
    assert is_valid_bad is False


def test_ingestion_pipeline():
    pipeline = MultimodalIngestionPipeline()
    res = pipeline.ingest("Explain photosynthesis", "text")
    assert res["success"] is True
    assert res["extracted_text"] == "Explain photosynthesis"

    res_doc = pipeline.ingest(b"User email: test@privacy.org", "document", "data.txt")
    assert res_doc["success"] is True
    assert "test@privacy.org" in res_doc["extracted_text"]


def test_document_processor():
    doc_proc = DocumentProcessor()
    res = doc_proc.process_file_bytes(b'{"name": "Alice", "email": "alice@corp.com"}', "data.json")
    assert res["contains_regex_pii"] is True
    assert "EMAIL_ADDRESS" in res["detected_entity_types"]


def test_hybrid_model_classifier():
    classifier = HybridBERTNaiveBayesPipeline()
    res = classifier.evaluate_privacy_risk("What is the capital of France?")
    assert res["risk_score"] < 0.35
    assert res["predicted_class"] == "SAFE"

    res_pii = classifier.evaluate_privacy_risk("Contact me at john.doe@privacy.com or call 555-0199.")
    assert res_pii["risk_score"] >= 0.25


def test_pii_sanitizer():
    sanitizer = PIISanitizer()
    text = "Send funds to john@corp.com with SSN 123-45-6789 and Card 4111222233334444."
    sanitized, entities = sanitizer.sanitize(text)
    assert "[EMAIL_REDACTED]" in sanitized
    assert "[SSN_REDACTED]" in sanitized
    assert "[CREDIT_CARD_REDACTED]" in sanitized
    assert len(entities) >= 3


def test_privacy_engine_package_exports():
    from privacy_engine import PrivacyEvaluator, PrivacySanitizer

    evaluator = PrivacyEvaluator()
    sanitizer = PrivacySanitizer()

    assert evaluator.evaluate_decision(0.1, [])["action"] == "ALLOW"
    assert sanitizer.sanitize("hello@example.com")[0].count("[EMAIL_REDACTED]") == 1


def test_decision_gate():
    gate = AutomatedDecisionGate()
    res_allow = gate.evaluate_decision("Tell me a joke.", 0.10)
    assert res_allow["decision"] == "ALLOW"
    assert res_allow["forward_prompt"] == "Tell me a joke."

    res_sanitize = gate.evaluate_decision("My email is alice@test.com", 0.45)
    assert res_sanitize["decision"] == "SANITIZE"
    assert "[EMAIL_REDACTED]" in res_sanitize["forward_prompt"]

    res_block = gate.evaluate_decision("TOP SECRET API KEY AKIAIOSFODNN7EXAMPLE", 0.90)
    assert res_block["decision"] == "BLOCK"
    assert res_block["forward_prompt"] is None


def test_gemini_client():
    client = GeminiLLMClient()
    res = client.generate_response("Explain relativity")
    assert res["success"] is True
    assert len(res["response_text"]) > 0


def test_evaluation_metrics():
    y_true = [0, 0, 1, 1, 2, 2]
    y_pred = [0, 0, 1, 1, 2, 2]
    metrics = PrivacyEvaluationMetrics.calculate_classifier_metrics(y_true, y_pred)
    assert metrics["accuracy"] == 1.0
    assert metrics["f1_score"] == 1.0
    assert metrics["false_positive_rate"] == 0.0
    assert metrics["false_negative_rate"] == 0.0
