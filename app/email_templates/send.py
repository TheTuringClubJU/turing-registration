"""
app/email_templates/send.py

Transactional email delivery using Brevo (formerly Sendinblue) REST API.
Sends event registration confirmation emails with:
- Apple monochrome minimalist styling
- High-contrast short ticket code pill (TTC-XXXX)
- Universal QR code rendering (embedded base64 data URI + standard attachment)
- Attendee roster (team lead and members)
- Check-in instructions
"""

import base64
import json
import logging
import urllib.request
import urllib.error
from typing import Any

from app.core.config import settings

logger = logging.getLogger(__name__)

BREVO_API_URL = "https://api.brevo.com/v3/smtp/email"
SENDER_NAME = "The Turing Club"
SENDER_EMAIL = "ttclub.ju@gmail.com"


def render_confirmation_html(
    event: dict[str, Any],
    team_name: str | None,
    participants: list[dict[str, Any]],
    registration_id: str,
    ticket_code: str | None,
    qr_b64: str,
) -> str:
    """Build responsive Apple-monochrome HTML email template."""
    event_name = event.get("name", "TTC Event")

    # Participant roster rows
    participant_items = []
    for idx, p in enumerate(participants):
        p_name = p.get("name", "Participant")
        p_email = p.get("email", "")
        is_lead = p.get("is_team_lead", False) or idx == 0

        badge = '<span style="background-color:#ffffff;color:#000000;font-size:11px;font-weight:700;padding:2px 6px;border-radius:4px;margin-left:8px;text-transform:uppercase;">Lead</span>' if is_lead else ''
        participant_items.append(
            f'<div style="padding:10px 0;border-bottom:1px solid #222224;display:flex;justify-content:space-between;align-items:center;">'
            f'<div><span style="color:#ffffff;font-weight:600;font-size:14px;">{p_name}</span>{badge}<br>'
            f'<span style="color:#86868b;font-size:12px;">{p_email}</span></div>'
            f'</div>'
        )
    roster_html = "".join(participant_items)

    ticket_code_display = ticket_code or "TTC-PASS"
    team_display_html = f'<p style="margin:0 0 16px 0;color:#86868b;font-size:13px;">Team: <strong style="color:#ffffff;">{team_name}</strong></p>' if team_name else ''

    qr_image_src = f"data:image/png;base64,{qr_b64}"

    return f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Your Entry Pass: {event_name}</title>
</head>
<body style="margin:0;padding:0;background-color:#0a0a0a;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;color:#ffffff;">
  <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="background-color:#0a0a0a;padding:32px 16px;">
    <tr>
      <td align="center">
        <table role="presentation" width="100%" style="max-width:540px;background-color:#161617;border:1px solid #262628;border-radius:20px;overflow:hidden;box-shadow:0 12px 32px rgba(0,0,0,0.6);" cellspacing="0" cellpadding="0">
          
          <!-- Header -->
          <tr>
            <td style="padding:28px 28px 20px 28px;text-align:center;border-bottom:1px solid #222224;">
              <span style="font-size:12px;font-weight:700;letter-spacing:0.15em;text-transform:uppercase;color:#86868b;display:block;margin-bottom:8px;">The Turing Club</span>
              <span style="display:inline-block;background-color:rgba(255,255,255,0.1);color:#ffffff;font-size:11px;font-weight:600;padding:4px 10px;border-radius:20px;letter-spacing:0.05em;text-transform:uppercase;margin-bottom:12px;">Registration Confirmed</span>
              <h1 style="margin:0;font-size:24px;font-weight:700;letter-spacing:-0.02em;color:#ffffff;line-height:1.2;">{event_name}</h1>
            </td>
          </tr>

          <!-- Ticket Pass Section -->
          <tr>
            <td style="padding:28px 28px 20px 28px;text-align:center;">
              <div style="background-color:#0d0d0d;border:1px solid #262628;border-radius:16px;padding:24px;display:inline-block;width:100%;box-sizing:border-box;">
                
                <!-- QR Code (data:image/png;base64) -->
                <div style="margin-bottom:18px;">
                  <img src="{qr_image_src}" alt="Registration QR Code" width="180" height="180" style="display:inline-block;border-radius:12px;background-color:#ffffff;padding:8px;" />
                </div>

                <!-- Ticket Code Pill -->
                <div style="margin-bottom:12px;">
                  <span style="display:inline-block;background-color:#ffffff;color:#000000;font-family:ui-monospace,SFMono-Regular,Menlo,Monaco,Consolas,monospace;font-size:22px;font-weight:800;letter-spacing:0.1em;padding:8px 20px;border-radius:30px;">
                    {ticket_code_display}
                  </span>
                </div>
                <span style="display:block;font-size:11px;color:#86868b;text-transform:uppercase;letter-spacing:0.08em;margin-bottom:10px;">Short Ticket Code</span>

                <span style="display:block;font-family:ui-monospace,monospace;font-size:11px;color:#555558;">ID: {registration_id}</span>
              </div>
            </td>
          </tr>

          <!-- Attendee Roster -->
          <tr>
            <td style="padding:0 28px 24px 28px;">
              <h3 style="margin:0 0 12px 0;font-size:12px;font-weight:600;color:#86868b;text-transform:uppercase;letter-spacing:0.08em;">Registration Details</h3>
              {team_display_html}
              <div style="background-color:#0d0d0d;border:1px solid #222224;border-radius:12px;padding:0 16px;">
                {roster_html}
              </div>
            </td>
          </tr>

          <!-- Check-in Instructions -->
          <tr>
            <td style="padding:0 28px 28px 28px;">
              <div style="background-color:#1c1c1e;border-left:3px solid #ffffff;border-radius:8px;padding:14px 16px;">
                <span style="display:block;font-size:12px;font-weight:700;color:#ffffff;text-transform:uppercase;letter-spacing:0.05em;margin-bottom:6px;">Check-in Desk Instructions</span>
                <p style="margin:0 0 6px 0;font-size:12px;line-height:1.5;color:#a1a1a6;">1. Present this QR code on your phone when arriving at the Turing Club desk.</p>
                <p style="margin:0 0 6px 0;font-size:12px;line-height:1.5;color:#a1a1a6;">2. You can also state your 6-character short ticket code (<strong style="color:#ffffff;">{ticket_code_display}</strong>) to the organizers.</p>
                <p style="margin:0;font-size:12px;line-height:1.5;color:#a1a1a6;">3. One scan or entry admits your entire registered party.</p>
              </div>
            </td>
          </tr>

          <!-- Footer -->
          <tr>
            <td style="padding:20px 28px;text-align:center;border-top:1px solid #222224;background-color:#111112;">
              <p style="margin:0;font-size:12px;color:#666668;letter-spacing:-0.01em;">The Turing Club • Building for Builders</p>
            </td>
          </tr>

        </table>
      </td>
    </tr>
  </table>
</body>
</html>
"""


def send_registration_confirmation(
    to: str,
    event: dict[str, Any],
    team_name: str | None,
    participants: list[dict[str, Any]],
    qr_bytes: bytes,
    registration_id: str,
    ticket_code: str | None = None,
) -> None:
    """
    Sends the confirmation email via Brevo transactional API.
    Uses embedded data:image/png;base64 for universal rendering across all web & mobile clients,
    plus an attachment backup for desktop clients.
    """
    api_key = getattr(settings, "BREVO_API_KEY", "").strip()
    if not api_key:
        logger.warning("Brevo API key is not configured; skipping email delivery.")
        return

    event_name = event.get("name", "TTC Event")
    ticket_subject = f"Your Entry Pass: {event_name}"
    if ticket_code:
        ticket_subject += f" — {ticket_code}"

    qr_b64 = base64.b64encode(qr_bytes).decode("ascii")

    html_content = render_confirmation_html(
        event=event,
        team_name=team_name,
        participants=participants,
        registration_id=registration_id,
        ticket_code=ticket_code,
        qr_b64=qr_b64,
    )

    payload = {
        "sender": {
            "name": SENDER_NAME,
            "email": SENDER_EMAIL,
        },
        "to": [
            {
                "email": to.strip(),
            }
        ],
        "subject": ticket_subject,
        "htmlContent": html_content,
        "attachment": [
            {
                "name": f"ticket-qr-{ticket_code or 'pass'}.png",
                "content": qr_b64,
            }
        ],
    }

    req = urllib.request.Request(
        BREVO_API_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "api-key": api_key,
            "Content-Type": "application/json",
            "accept": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=15) as response:
            logger.info("Confirmation email sent successfully to %s", to)
    except urllib.error.HTTPError as exc:
        err_msg = exc.read().decode("utf-8", errors="ignore")
        logger.error("Brevo API HTTP Error %s: %s", exc.code, err_msg)
        raise RuntimeError(f"Brevo API failed with {exc.code}: {err_msg}") from exc
    except Exception as exc:
        logger.error("Failed to send email via Brevo: %s", type(exc).__name__)
        raise
