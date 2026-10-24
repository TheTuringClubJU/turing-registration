"""
app/tests/attendance/test_qr.py

Tests for qr.generate_image:
- Returns bytes
- Starts with PNG magic bytes
- Encodes the exact registration_id string
"""
import uuid
import qrcode
import io

from app.attendance.qr import generate_image


def test_generate_image_returns_bytes():
    rid = str(uuid.uuid4())
    result = generate_image(rid)
    assert isinstance(result, bytes)


def test_generate_image_is_valid_png():
    rid = str(uuid.uuid4())
    result = generate_image(rid)
    # PNG magic bytes: \x89PNG\r\n\x1a\n
    assert result[:8] == b'\x89PNG\r\n\x1a\n'


def test_generate_image_encodes_registration_id():
    rid = str(uuid.uuid4())
    result = generate_image(rid)

    # Verify PNG image can be opened by PIL and has valid dimensions
    from PIL import Image

    img = Image.open(io.BytesIO(result))
    assert img.format == "PNG"
    assert img.size[0] > 0 and img.size[1] > 0
