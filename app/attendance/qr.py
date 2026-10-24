import io
import qrcode
from qrcode.constants import ERROR_CORRECT_L

def generate_image(registration_id: str) -> bytes:
    qr = qrcode.QRCode(
        version=1,
        error_correction=ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    
    qr.add_data(registration_id)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    
    buffer = io.BytesIO()
    # Use # type: ignore to clear the Pylance signature mismatch warning
    img.save(buffer, format="PNG")  # type: ignore
    
    return buffer.getvalue()
