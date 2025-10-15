import re
import random
from datetime import datetime
from zoneinfo import ZoneInfo
from config import SESSION_WINDOWS

MAX_TELEGRAM_MESSAGE_LENGTH = 4096

SNIPER_QUOTES = [
    'Liquidity fuels intention. Timing defines direction.',
    'Smart money hides in silence, not noise.',
    'The map is time. The weapon is structure.',
    'Volume reveals intention. Time confirms execution.',
    'You don’t chase price. You anticipate narrative.',
    'Every candle is a question. Smart money answers with traps.',
    'Retail sees levels. Institutions see liquidity.',
    'The game isn’t entry. The game is understanding.',
    'True power is not prediction — it’s preparation.',
    'Price speaks loudest in silence.',
    'Wicks are whispers — hear what price refuses to say.',
    'When price hesitates, smart money accumulates.',
    'Trade during peace, and rest during war.',
    'The war is not over.',
    'Green or Red Candle? Remember, there is no turning back ',
    'The choice is yours… execution defines reality.',
]

def remove_emojis(text: str) -> str:
    """Remove all emoji and pictographs from text."""
    emoji_pattern = re.compile(
        "["
        "\U0001F600-\U0001F64F"
        "\U0001F300-\U0001F5FF"
        "\U0001F680-\U0001F6FF"
        "\U0001F1E0-\U0001F1FF"
        "\U00002500-\U00002BEF"
        "\U00002702-\U000027B0"
        "\U000024C2-\U0001F251"
        "]+", flags=re.UNICODE
    )
    return emoji_pattern.sub("", text)

def format_price_values(text: str) -> str:
    """Bold numbers like 3427.50 unless already bolded."""
    return re.sub(
        r"\b(\d{3,5}\.\d{2})\b",
        lambda m: f"<b>{m.group(1)}</b>"
        if f"<b>{m.group(1)}</b>" not in text else m.group(1),
        text
    )

def safe_trim_html(message: str, max_len: int) -> str:
    """Ensure HTML tags are not broken when trimming."""
    if len(message) <= max_len:
        return message
    trimmed = message[:max_len]
    for tag in ["b", "i"]:
        if trimmed.count(f"<{tag}>") != trimmed.count(f"</{tag}>"):
            trimmed += f"</{tag}>"
    return trimmed + "..."

def clean_gpt_output(summary: str, session_name: str) -> str:
    """Remove any GPT-added headers, quotes, or date/time lines (plain or HTML)."""
    # Remove GPT-added session headers
    summary = re.sub(r"(?i)📍.*session summary.*", "", summary)
    summary = re.sub(r"(?i)^.*session summary.*\n?", "", summary)

    # Remove italicised quotes
    summary = re.sub(r"<i>.*?</i>", "", summary)

    # Remove Date, Session, Time, and Sentinel Report lines (HTML-safe and plain)
    summary = re.sub(r"(?i)<b>\s*date\s*:.*?</b>.*", "", summary)
    summary = re.sub(r"(?i)<b>\s*session\s*:.*?</b>.*", "", summary)
    summary = re.sub(r"(?i)<b>\s*time\s*:.*?</b>.*", "", summary)
    summary = re.sub(r"(?i)<b>\s*sentinelx\s*:?.*?</b>.*", "", summary)
    summary = re.sub(r"(?i)<b>\s*xau/usd\s*\s*:?.*?</b>.*", "", summary)
    summary = re.sub(r"(?im)^\s*date\s*:.*$", "", summary)
    summary = re.sub(r"(?im)^\s*session\s*:.*$", "", summary)
    summary = re.sub(r"(?im)^\s*time\s*:.*$", "", summary)
    summary = re.sub(r"(?im)^\s*sentinelx\s*:?.*$", "", summary)
    summary = re.sub(r"(?im)^\s*xau/usd\s*report\s*:?.*$", "", summary)

    return summary.strip()


def format_spectral_summary(summary: str, session_name: str, tz: str = "Europe/Rome") -> str:
    """Final Telegram-ready summary with single header, quote, and session info."""
    if not summary or not summary.strip():
        return f"<b>{session_name} SESSION</b>\n\nNo valid summary generated."

    # Clean GPT text
    summary = clean_gpt_output(summary, session_name)
    summary = remove_emojis(summary)
    summary = format_price_values(summary)

    # Add one controlled random quote
    quote = f"<i>{random.choice(SNIPER_QUOTES)}</i>"

    # Time & session info
    local_tz = ZoneInfo(tz)
    utc_now = datetime.utcnow().replace(tzinfo=ZoneInfo("UTC"))
    local_now = utc_now.astimezone(local_tz)
    time_local = local_now.strftime("%H:%M")
    time_utc = utc_now.strftime("%H:%M UTC")
    date_str = local_now.strftime("%A, %d %B")
    session_window = SESSION_WINDOWS.get(session_name, "Time Window N/A")

    # Final message
    formatted = f"""<b>SENTINELx XAU/USD REPORT</b>

{summary}

{quote}

<b>Date:</b> {date_str}
<b>Session:</b> {session_name} ({session_window})
<b>Time:</b> {time_local} {tz} | {time_utc}
"""

    return safe_trim_html(formatted, MAX_TELEGRAM_MESSAGE_LENGTH)
