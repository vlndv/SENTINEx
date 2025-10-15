import os
import re
import requests
from datetime import datetime
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, ENABLE_LOGGING

# 🔧 Constants
TELEGRAM_MSG_URL = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
MAX_MESSAGE_LENGTH = 4096
SPLIT_BUFFER = 50  # Safety margin for HTML length
LOG_DIR = os.path.join(os.path.dirname(__file__), "telegram_logs")
os.makedirs(LOG_DIR, exist_ok=True)

# 🧼 HTML Sanitizer — Only allow Telegram-safe tags and fix escaped tags
def sanitize_telegram_html(text: str) -> str:
    """Cleans HTML to keep only Telegram-safe tags."""
    allowed_tags = {
        "b", "strong", "i", "em", "u", "ins", "s", "strike", "del",
        "a", "code", "pre", "span", "br"
    }
    # Replace escaped HTML entities
    text = text.replace("&lt;", "<").replace("&gt;", ">")

    # Remove <br> inside <code> or <pre> blocks
    text = re.sub(r"(<code>.*?)(<br>)(.*?</code>)", r"\1\3", text, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r"(<pre>.*?)(<br>)(.*?</pre>)", r"\1\3", text, flags=re.IGNORECASE | re.DOTALL)

    # Normalize <br> tags
    text = re.sub(r"<\s*br\s*/?>", "<br>", text, flags=re.IGNORECASE)

    # Keep only allowed tags
    return re.sub(
        r"</?([a-zA-Z0-9]+)(\s[^>]*)?>",
        lambda m: m.group(0) if m.group(1).lower() in allowed_tags else "",
        text
    )

# ✂️ Safe HTML chunking
def safe_html_split(text: str, max_len: int) -> list:
    """Splits HTML-safe text into Telegram-safe chunks without breaking tags."""
    words = text.split(" ")
    chunks = []
    current = ""

    for word in words:
        if len(current) + len(word) + 1 > max_len:
            chunks.append(current)
            current = word
        else:
            current += (" " if current else "") + word

    if current:
        chunks.append(current)
    return chunks

# 📤 Send message to Telegram with full logging
def send_telegram_message(message: str) -> bool:
    """Sends a message to Telegram with HTML sanitization, chunking, and logging."""
    if ENABLE_LOGGING:
        print("DEBUG: send_telegram_message() was called")

    if not message or len(message.strip()) < 10:
        if ENABLE_LOGGING:
            print("DEBUG: Message too short or empty.")
        return False

    try:
        # Sanitize HTML
        message = sanitize_telegram_html(message)
        if ENABLE_LOGGING:
            print(f"DEBUG: Sanitized message length: {len(message)} chars")

        # Prepare base payload
        payload = {
            "chat_id": TELEGRAM_CHAT_ID,
            "parse_mode": "HTML",
            "protect_content": True,
            "disable_web_page_preview": True
        }

        # Split into safe chunks
        chunks = safe_html_split(message, MAX_MESSAGE_LENGTH - SPLIT_BUFFER)
        if ENABLE_LOGGING:
            print(f"DEBUG: Message split into {len(chunks)} chunk(s)")

        # Send each chunk
        for i, chunk in enumerate(chunks, start=1):
            payload["text"] = chunk
            resp = requests.post(TELEGRAM_MSG_URL, data=payload, timeout=10)

            if ENABLE_LOGGING:
                print(f"DEBUG: Chunk {i} response: {resp.status_code} — {resp.text}")

            # If HTML fails, retry without parse_mode
            if resp.status_code != 200:
                if resp.status_code == 400:  # HTML parse error
                    if ENABLE_LOGGING:
                        print("DEBUG: HTML parse failed — retrying without parse_mode.")
                    payload.pop("parse_mode", None)
                    resp = requests.post(TELEGRAM_MSG_URL, data=payload, timeout=10)
                    if resp.status_code == 200:
                        if ENABLE_LOGGING:
                            print(f"DEBUG: Chunk {i} sent successfully in plain text fallback")
                        continue

                _log_failure("TEXT", chunk, resp.status_code, resp.text)
                return False

        if ENABLE_LOGGING:
            print("DEBUG: All chunks sent successfully")
        return True

    except Exception as e:
        if ENABLE_LOGGING:
            print(f"DEBUG: Exception while sending: {e}")
        _log_failure("TEXT", message, "Exception", str(e))
        return False

# 🧾 Error logger
def _log_failure(content_type: str, content: str, error_code, error_detail):
    """Logs failed Telegram send attempts to file."""
    try:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_file = os.path.join(LOG_DIR, "telegram_failures.log")
        with open(log_file, "a", encoding="utf-8") as f:
            f.write("\n" + "-" * 60 + "\n")
            f.write(f"[{timestamp}] TELEGRAM {content_type} FAILURE\n")
            f.write(f"Error Code: {error_code}\n")
            f.write(f"Error Detail: {error_detail}\n")
            f.write("Content:\n" + content + "\n")
        if ENABLE_LOGGING:
            print(f"DEBUG: Failure logged to {log_file}")
    except Exception as log_error:
        if ENABLE_LOGGING:
            print(f"DEBUG: Failed to write failure log: {log_error}")
