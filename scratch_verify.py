import sys
sys.stdout.reconfigure(encoding='utf-8')

from backend.services.evidence_risk import run_full_analysis
from privacy_engine.sanitizer import PrivacySanitizer
from frontend.views.chatbot import _render_privacy_blurred_text

sanitizer = PrivacySanitizer()

test_cases = [
    "Hello",
    "My adhar number 18212938323",
    "My Aadhaar card number is 123456789012",
    "My Aadhaar card number is 1234 5678 9012",
    "Aadhaar: 123456789012",
    "My Aadhar number is 1234 5678 9012",
    "My password is MySecret123",
    "My PAN is ABCDE1234F",
    "My OTP is 483921",
    "My phone number is +91 98765-43210",
    "My bank account number is 123456789012",
    "Hello, my Aadhaar is 9918 4019 2011 and my password is secret123",
]

print("=" * 110)
for p in test_cases:
    analysis = run_full_analysis(p)
    san_obj = sanitizer.sanitize_text(p, mode="REDACT")
    san_text = san_obj.get("sanitized_text", p)
    blurred_html = _render_privacy_blurred_text(san_text)
    print(f"Original    : {p}")
    print(f"Risk        : {analysis['risk_score']}% ({analysis['risk_level']}) -> Decision: {analysis['decision']}")
    print(f"Sanitized   : {san_text}")
    print(f"Blurred HTML: {blurred_html}")
    print("-" * 110)

