"""
Privacy-Preserving Audit Logging Module.
File Location: backend/logger.py
"""

import json
import csv
import io
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any
import config

# Setup console logger
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - [%(levelname)s] - %(message)s",
)
logger = logging.getLogger("PrivacyFirewall")

AUDIT_LOG_FILE = config.LOGS_DIR / "privacy_audit.json"


def log_privacy_audit(
    request_id: str,
    modality: str,
    risk_score: float,
    action_taken: str,
    detected_entities: list,
    original_length: int,
    llm_status: str,
):
    """
    Logs metadata about a request without saving raw sensitive prompts or images.
    """
    audit_entry = {
        "request_id": request_id,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "modality": modality,
        "risk_score": round(risk_score, 4),
        "action_taken": action_taken,
        "detected_entities_count": len(detected_entities),
        "detected_entity_types": list(set(detected_entities)),
        "input_character_length": original_length,
        "llm_status": llm_status,
    }

    logger.info(
        f"REQ [{request_id}] | Modality: {modality.upper()} | Risk: {risk_score:.2f} | Action: {action_taken} | Entities: {len(detected_entities)}"
    )

    # Append to JSON audit file safely
    try:
        logs = get_all_logs()
        logs.append(audit_entry)

        with open(AUDIT_LOG_FILE, "w", encoding="utf-8") as f:
            json.dump(logs, f, indent=2)

    except Exception as e:
        logger.error(f"Failed to write to audit log: {str(e)}")


def get_all_logs() -> List[Dict[str, Any]]:
    """Retrieves all logged audit entries from JSON file."""
    if AUDIT_LOG_FILE.exists() and AUDIT_LOG_FILE.stat().st_size > 0:
        try:
            with open(AUDIT_LOG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
    return []


def get_audit_summary_metrics() -> Dict[str, Any]:
    """Calculates aggregate statistical metrics over historical audit logs."""
    logs = get_all_logs()
    total_requests = len(logs)
    if total_requests == 0:
        return {
            "total_requests": 0,
            "blocked_count": 0,
            "sanitized_count": 0,
            "allowed_count": 0,
            "block_rate": 0.0,
            "avg_risk_score": 0.0,
            "entity_counts": {},
            "modality_counts": {},
        }

    blocked = sum(1 for log in logs if log.get("action_taken") == "BLOCK")
    sanitized = sum(1 for log in logs if log.get("action_taken") == "SANITIZE")
    allowed = sum(1 for log in logs if log.get("action_taken") == "ALLOW")

    avg_risk = sum(log.get("risk_score", 0.0) for log in logs) / total_requests

    entity_counts = {}
    modality_counts = {}

    for log in logs:
        mod = log.get("modality", "unknown")
        modality_counts[mod] = modality_counts.get(mod, 0) + 1

        for ent in log.get("detected_entity_types", []):
            entity_counts[ent] = entity_counts.get(ent, 0) + 1

    return {
        "total_requests": total_requests,
        "blocked_count": blocked,
        "sanitized_count": sanitized,
        "allowed_count": allowed,
        "block_rate": round((blocked / total_requests) * 100, 1),
        "avg_risk_score": round(avg_risk, 3),
        "entity_counts": entity_counts,
        "modality_counts": modality_counts,
    }


def export_logs_as_csv() -> str:
    """Exports audit logs as a CSV formatted string."""
    logs = get_all_logs()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "request_id", "timestamp", "modality", "risk_score",
        "action_taken", "detected_entities_count", "detected_entity_types",
        "input_character_length", "llm_status"
    ])

    for log in logs:
        writer.writerow([
            log.get("request_id", ""),
            log.get("timestamp", ""),
            log.get("modality", ""),
            log.get("risk_score", 0.0),
            log.get("action_taken", ""),
            log.get("detected_entities_count", 0),
            ", ".join(log.get("detected_entity_types", [])),
            log.get("input_character_length", 0),
            log.get("llm_status", ""),
        ])

    return output.getvalue()


def clear_audit_logs():
    """Clears all historical audit logs."""
    try:
        with open(AUDIT_LOG_FILE, "w", encoding="utf-8") as f:
            json.dump([], f)
    except Exception as e:
        logger.error(f"Failed to clear audit log: {str(e)}")

