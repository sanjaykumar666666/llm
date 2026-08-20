"""
Asset Generator for AI Privacy Guard Dashboard.
Generates realistic high-resolution previews for Original/Protected Aadhaar cards and Video Frames.
"""

import io
import os
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter

ASSETS_DIR = Path("data/dashboard_assets")
ASSETS_DIR.mkdir(parents=True, exist_ok=True)


def create_demo_aadhaar():
    """Creates crisp Original and Protected Aadhaar card images matching the dashboard UI."""
    width, height = 480, 290

    # ── 1. ORIGINAL AADHAAR CARD ───────────────────────────────────────────────
    orig = Image.new("RGB", (width, height), (255, 255, 255))
    draw = ImageDraw.Draw(orig)

    # Top tricolor bar
    draw.rectangle([(0, 0), (width, 10)], fill=(249, 115, 22))    # Saffron
    draw.rectangle([(0, 10), (width, 18)], fill=(255, 255, 255))  # White
    draw.rectangle([(0, 18), (width, 26)], fill=(34, 197, 94))    # Green

    # Header Text
    draw.text((width // 2 - 45, 32), "भारत सरकार", fill=(225, 29, 72))
    draw.text((width // 2 - 75, 48), "GOVERNMENT OF INDIA", fill=(15, 23, 42))

    # User Photo Placeholder (Avatar with face)
    draw.rectangle([(25, 75), (145, 215)], fill=(226, 232, 240), outline=(148, 163, 184), width=1)
    # Draw simple human silhouette/face inside photo box
    draw.ellipse([(60, 95), (110, 145)], fill=(100, 116, 139))
    draw.ellipse([(45, 155), (125, 215)], fill=(71, 85, 105))

    # Details
    draw.text((165, 78), "नाम / Name :", fill=(100, 116, 139))
    draw.text((165, 96), "RAMAN KUMAR", fill=(15, 23, 42))

    draw.text((165, 122), "जन्म तिथि / DOB : 14/07/1990", fill=(15, 23, 42))
    draw.text((165, 142), "पुरुष / Male", fill=(15, 23, 42))

    draw.text((165, 172), "आधार संख्या / Aadhaar No.", fill=(100, 116, 139))
    draw.text((165, 192), "1234 5678 9012", fill=(15, 23, 42))

    # Fake QR Code Box
    draw.rectangle([(360, 90), (455, 185)], fill=(241, 245, 249), outline=(15, 23, 42), width=2)
    for qx in range(370, 445, 8):
        for qy in range(100, 175, 8):
            if (qx + qy) % 16 == 0 or (qx * qy) % 24 == 0:
                draw.rectangle([(qx, qy), (qx + 6, qy + 6)], fill=(15, 23, 42))

    # Bottom red line
    draw.rectangle([(0, height - 8), (width, height)], fill=(225, 29, 72))

    orig_path = ASSETS_DIR / "aadhaar_original.png"
    orig.save(orig_path)

    # ── 2. PROTECTED AADHAAR CARD (REAL GAUSSIAN BLUR & REDACTION) ────────────
    prot = orig.copy()
    prot_draw = ImageDraw.Draw(prot)

    # 1. Real Gaussian Blur on Face
    face_box = (25, 75, 145, 215)
    face_crop = prot.crop(face_box)
    face_blurred = face_crop.filter(ImageFilter.GaussianBlur(radius=18))
    prot.paste(face_blurred, face_box)

    # 2. Solid/Structured Redaction over Name & DOB
    prot_draw.rectangle([(165, 94), (320, 114)], fill=(241, 245, 249))
    prot_draw.text((165, 96), "[IDENTITY REDACTED]", fill=(225, 29, 72))

    prot_draw.rectangle([(255, 120), (345, 138)], fill=(241, 245, 249))
    prot_draw.text((255, 122), "[REDACTED]", fill=(225, 29, 72))

    # 3. Mask Aadhaar Number
    prot_draw.rectangle([(165, 190), (320, 212)], fill=(241, 245, 249))
    prot_draw.text((165, 192), "•••• •••• 9012", fill=(15, 23, 42))

    # 4. Pixelate / Blur QR Code
    qr_box = (360, 90, 455, 185)
    qr_crop = prot.crop(qr_box)
    qr_blurred = qr_crop.filter(ImageFilter.GaussianBlur(radius=12))
    prot.paste(qr_blurred, qr_box)

    prot_path = ASSETS_DIR / "aadhaar_protected.png"
    prot.save(prot_path)


def create_demo_video_frame():
    """Creates a sample video frame with face detection bounding box and timestamp overlay."""
    w, h = 480, 270
    frame = Image.new("RGB", (w, h), (30, 41, 59))
    draw = ImageDraw.Draw(frame)

    # Office background gradient & plant
    draw.rectangle([(0, 0), (w, 180)], fill=(51, 65, 85))
    draw.rectangle([(380, 80), (440, 200)], fill=(22, 101, 52))  # Plant

    # Human figure
    draw.ellipse([(200, 70), (280, 150)], fill=(148, 163, 184))  # Head
    draw.polygon([(160, 150), (320, 150), (360, 270), (120, 270)], fill=(30, 58, 138))  # Shoulders

    # Red Bounding Box on Face
    draw.rectangle([(195, 65), (285, 155)], outline=(239, 68, 68), width=3)

    # Blur face inside box for sensitive detection preview
    face_crop = frame.crop((198, 68, 282, 152))
    blurred_face = face_crop.filter(ImageFilter.GaussianBlur(radius=14))
    frame.paste(blurred_face, (198, 68))

    # Timestamp tag [00:00:12]
    draw.rectangle([(15, h - 35), (90, h - 12)], fill=(15, 23, 42, 220))
    draw.text((22, h - 30), "00:00:12", fill=(255, 255, 255))

    # Sensitive Frame Badge
    draw.rectangle([(w - 120, h - 35), (w - 15, h - 12)], fill=(239, 68, 68))
    draw.text((w - 110, h - 30), "Sensitive Frame", fill=(255, 255, 255))

    frame_path = ASSETS_DIR / "video_frame_preview.png"
    frame.save(frame_path)


if __name__ == "__main__":
    create_demo_aadhaar()
    create_demo_video_frame()
    print("Assets generated successfully in data/dashboard_assets/")
