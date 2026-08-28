"""
Automated Test Suite for AI Privacy Twin & Reversible Cryptographic Vault.
File: tests/test_privacy_twin_service.py
"""

import io
import pytest
from PIL import Image, ImageDraw

from backend.services.privacy_twin_service import PrivacyTwinService
from tests.test_granular_identity_privacy import create_synthetic_card


def test_privacy_twin_generation():
    """Test generating photorealistic context-preserving synthetic twin."""
    raw_bytes = create_synthetic_card(has_name=True, has_dob=True, has_id_num=True, has_address=True, has_face=True, has_qr=True)
    res = PrivacyTwinService.generate_privacy_twin(raw_bytes, "test_twin.png", seed_index=0, enable_reversible_vault=True)

    assert res["success"] is True
    assert res["replaced_count"] >= 3
    assert "twin_image_bytes" in res
    assert len(res["twin_image_bytes"]) > 100
    assert res["session_vault_key"].startswith("priv_vault_")
    assert len(res["vault_token"]) > 20
    assert res["is_context_preserved"] is True


def test_reversible_cryptographic_vault():
    """Test encrypting and decrypting vault with valid and invalid session keys."""
    sample_data = {
        "user_name": "Ramesh Kumar",
        "aadhaar": "9812 3456 7890",
        "address": "Flat 4B, MG Road, Pune",
        "secret_token": "TOKEN-99881122"
    }
    session_key = "priv_vault_test_key_secret_2026"

    # 1. Encrypt
    token = PrivacyTwinService.encrypt_vault_payload(sample_data, session_key)
    assert len(token) > 20

    # 2. Decrypt with correct key
    ok, decrypted, msg = PrivacyTwinService.decrypt_vault_payload(token, session_key)
    assert ok is True
    assert decrypted["user_name"] == "Ramesh Kumar"
    assert decrypted["aadhaar"] == "9812 3456 7890"

    # 3. Decrypt with wrong key (Must fail safely)
    ok_wrong, decrypted_wrong, msg_wrong = PrivacyTwinService.decrypt_vault_payload(token, "wrong_key_123")
    assert ok_wrong is False
    assert decrypted_wrong is None


def test_liveness_and_deepfake_radar():
    """Test 2D FFT spectrum and liveness score calculation."""
    raw_bytes = create_synthetic_card()
    res = PrivacyTwinService.analyze_liveness_and_deepfake(raw_bytes)

    assert res["success"] is True
    assert res["liveness_score"] > 0
    assert "verdict" in res
    assert "badge" in res
    assert "moire_ratio" in res
    assert "edge_sharpness_var" in res
