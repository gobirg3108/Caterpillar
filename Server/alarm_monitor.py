"""
CNC Fanuc Alarm Monitor - Email Alert System
=============================================
"NO ALARM" area மட்டும் watch பண்ணும்.
வேற text வந்தா (alarm வந்தா) → email அனுப்பும்.

Install:
    pip install pillow pytesseract pyautogui opencv-python

Tesseract (Windows):
    https://github.com/UB-Mannheim/tesseract/wiki
"""

import smtplib
import time
import datetime
import os
import sys
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage


SENDER_EMAIL    = "itzgobi3108@gmail.com"       # உங்கள் Gmail
SENDER_PASSWORD = "haoe ppid ifit nfau"        # Gmail App Password (16-digit)

CUSTOMER_EMAILS = [
    "itzgobi3108@gmail.com",
    # "another@example.com",   # கூடுதல் email add பண்ணலாம்
]

MACHINE_NAME = "VTC KELCH SUB"
MACHINE_ID   = "000009126"

# எத்தனை seconds-க்கு ஒரு முறை check பண்றது
CHECK_INTERVAL = 10

# ஒரே alarm மறுபடியும் email போகாம இருக்க (minutes)
COOLDOWN_MINUTES = 5

# ── Alarm Region (screen pixel coordinates) ──────────────
# இந்த values உங்கள் monitor resolution-க்கு adjust பண்ணணும்.
# உங்கள் screen 1920x1080 ஆ இருந்தா இந்த values use பண்ணுங்க.
# CNC window full screen போட்டு run பண்ணுங்க.
#
#   (left, top, right, bottom)  ← screen pixels
ALARM_BOX = (47, 618, 510, 665)   # "NO ALARM" text இருக்க area

# Tesseract path (Windows-ல install பண்ணிருந்தா இந்த path சரிதான்)
TESSERACT_CMD = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# ══════════════════════════════════════════


def setup_tesseract():
    try:
        import pytesseract
        if os.path.exists(TESSERACT_CMD):
            pytesseract.pytesseract.tesseract_cmd = TESSERACT_CMD
        return pytesseract
    except ImportError:
        print("❌ pytesseract இல்ல. 'pip install pytesseract' run பண்ணுங்க.")
        sys.exit(1)


def capture_alarm_region():
    """Screen-ல alarm box மட்டும் capture பண்று"""
    try:
        import pyautogui
        left, top, right, bottom = ALARM_BOX
        width  = right - left
        height = bottom - top
        shot = pyautogui.screenshot(region=(left, top, width, height))
        return shot
    except ImportError:
        print("❌ pyautogui இல்ல. 'pip install pyautogui' run பண்ணுங்க.")
        sys.exit(1)


def read_alarm_text(image, tess):
    """Image-ல இருந்து text படிக்கும்"""
    try:
        import cv2, numpy as np
        from PIL import Image

        arr  = np.array(image)
        gray = cv2.cvtColor(arr, cv2.COLOR_RGB2GRAY)
        # Threshold - white background, dark text → better OCR
        _, thresh = cv2.threshold(gray, 80, 255, cv2.THRESH_BINARY)
        pil = Image.fromarray(thresh)
        text = tess.image_to_string(pil, config='--psm 7').strip().upper()
        return text
    except Exception as e:
        return ""


def is_alarm(text):
    """
    'NO ALARM' இருந்தா → False (normal)
    வேற எதாவது இருந்தா → True (alarm!)
    """
    if not text:
        return False, ""

    # Safe - இப்படி இருந்தா alarm இல்ல
    safe = ["NO ALARM", "NO ALARM.", ""]
    for s in safe:
        if s in text:
            return False, ""

    # வேற எதாவது text இருந்தா alarm
    return True, text


def send_email(alarm_text, screenshot):
    """Customer-க்கு alarm email அனுப்பு"""
    now = datetime.datetime.now()
    ts  = now.strftime("%d-%m-%Y %H:%M:%S")
    subject = f"🚨 CNC ALARM - {MACHINE_NAME} - {ts}"

    html = f"""
<html><body style="font-family:Arial,sans-serif;background:#f4f4f4;padding:20px;">
<div style="max-width:580px;margin:auto;background:white;border-radius:8px;overflow:hidden;
            box-shadow:0 2px 8px rgba(0,0,0,0.15);">

  <div style="background:#c62828;padding:22px;text-align:center;">
    <h2 style="color:white;margin:0;">🚨 CNC MACHINE ALARM ALERT</h2>
  </div>

  <div style="padding:24px;">
    <table style="width:100%;border-collapse:collapse;font-size:15px;">
      <tr style="background:#fff8e1;">
        <td style="padding:10px 14px;font-weight:bold;color:#bf360c;width:38%;">⚠️ Alarm Message</td>
        <td style="padding:10px 14px;color:#b71c1c;font-weight:bold;">{alarm_text}</td>
      </tr>
      <tr>
        <td style="padding:10px 14px;font-weight:bold;color:#444;">🕐 Time</td>
        <td style="padding:10px 14px;">{ts}</td>
      </tr>
      <tr style="background:#f9f9f9;">
        <td style="padding:10px 14px;font-weight:bold;color:#444;">🏭 Machine</td>
        <td style="padding:10px 14px;">{MACHINE_NAME}</td>
      </tr>
      <tr>
        <td style="padding:10px 14px;font-weight:bold;color:#444;">🔢 Machine ID</td>
        <td style="padding:10px 14px;">{MACHINE_ID}</td>
      </tr>
    </table>

    <div style="margin-top:18px;padding:14px;background:#ffebee;
                border-left:4px solid #c62828;border-radius:4px;">
      <b style="color:#c62828;">Action Required:</b>
      <ul style="margin:8px 0 0;padding-left:18px;color:#555;line-height:1.8;">
        <li>மெஷினை உடனே சரிபாருங்க</li>
        <li>Fanuc screen-ல alarm code பாருங்க</li>
        <li>காரணம் தெரியாம restart பண்ணாதீங்க</li>
        <li>தேவைப்பட்டா maintenance-ஐ தொடர்பு கொள்ளுங்க</li>
      </ul>
    </div>

    <p style="color:#777;font-size:13px;margin-top:16px;">
      📷 Alarm area screenshot கீழே attach ஆகியிருக்கு.
    </p>
  </div>

  <div style="background:#eee;padding:12px;text-align:center;">
    <p style="margin:0;color:#999;font-size:12px;">
      Auto-generated by CNC Alarm Monitor · Do not reply
    </p>
  </div>
</div>
</body></html>
"""

    try:
        msg = MIMEMultipart('related')
        msg['Subject'] = subject
        msg['From']    = SENDER_EMAIL
        msg['To']      = ", ".join(CUSTOMER_EMAILS)
        msg.attach(MIMEText(html, 'html'))

        # Screenshot attach
        if screenshot:
            tmp = "alarm_snap.png"
            screenshot.save(tmp)
            with open(tmp, 'rb') as f:
                img_att = MIMEImage(f.read())
                img_att.add_header('Content-Disposition', 'attachment',
                                   filename=f'alarm_{now.strftime("%Y%m%d_%H%M%S")}.png')
                msg.attach(img_att)
            os.remove(tmp)

        with smtplib.SMTP("smtp.gmail.com", 587) as s:
            s.starttls()
            s.login(SENDER_EMAIL, SENDER_PASSWORD)
            s.sendmail(SENDER_EMAIL, CUSTOMER_EMAILS, msg.as_string())

        print(f"  ✅ Email sent → {', '.join(CUSTOMER_EMAILS)}")
        return True

    except Exception as e:
        print(f"  ❌ Email error: {e}")
        return False


def main():
    tess = setup_tesseract()

    print("\n" + "═"*50)
    print("  🏭  CNC ALARM MONITOR  –  RUNNING")
    print("═"*50)
    print(f"  Machine      : {MACHINE_NAME} ({MACHINE_ID})")
    print(f"  Alarm region : {ALARM_BOX}")
    print(f"  Check every  : {CHECK_INTERVAL} seconds")
    print(f"  Email to     : {', '.join(CUSTOMER_EMAILS)}")
    print(f"  Cooldown     : {COOLDOWN_MINUTES} min")
    print("═"*50)
    print("  Ctrl+C → Stop\n")

    last_sent   = {}   # alarm_text → datetime
    check_no    = 0

    while True:
        try:
            check_no += 1
            ts = datetime.datetime.now().strftime("%H:%M:%S")

            screenshot = capture_alarm_region()
            text       = read_alarm_text(screenshot, tess)
            alarm, msg = is_alarm(text)

            if alarm:
                print(f"\n[{ts}] 🚨 ALARM DETECTED: '{msg}'")

                # Cooldown check
                now = datetime.datetime.now()
                last = last_sent.get(msg)
                if last and (now - last).total_seconds() < COOLDOWN_MINUTES * 60:
                    wait = COOLDOWN_MINUTES - (now - last).total_seconds() / 60
                    print(f"  ⏳ Cooldown: {wait:.1f} min மீதம் — email skip")
                else:
                    # Full screen screenshot also capture for context
                    try:
                        import pyautogui
                        full = pyautogui.screenshot()
                    except:
                        full = screenshot

                    if send_email(msg, full):
                        last_sent[msg] = now
            else:
                # Normal — just show dot every 10 checks
                if check_no % 6 == 0:
                    print(f"[{ts}] ✅ NO ALARM  (check #{check_no})")

            time.sleep(CHECK_INTERVAL)

        except KeyboardInterrupt:
            print(f"\n\n⛔ Stopped after {check_no} checks.")
            sys.exit(0)
        except Exception as e:
            print(f"\n❌ Error: {e}")
            time.sleep(CHECK_INTERVAL)


if __name__ == "__main__":
    main()