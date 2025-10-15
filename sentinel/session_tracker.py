# session_tracker.py
from datetime import datetime, timedelta, timezone
from typing import Optional
from config import SESSIONS, LOCAL_TZ, local_to_utc  # ✅ use your helpers

# 🧠 Tracks last triggered time for each session (per UTC date)
last_triggered_sessions = {}
last_reset_date = datetime.now(timezone.utc).date()

# ⏳ Make the window forgiving (±90s protects against drift & processing delay)
SESSION_TRIGGER_WINDOW_SEC = 90

# ⛑️ Optional catch-up window: if we missed the exact time, allow fire within +5 min
MISSED_TRIGGER_GRACE_SEC = 5 * 60

def _scheduled_time_utc_for_today(session_name: str) -> datetime:
    """
    Build today's scheduled datetime in LOCAL_TZ for the session, then convert to UTC.
    """
    # Get the local date 'today' according to LOCAL_TZ
    now_local = datetime.now(LOCAL_TZ)
    # Build a local datetime for today at the configured local time
    sess_local_dt = now_local.replace(
        hour=SESSIONS[session_name].hour,
        minute=SESSIONS[session_name].minute,
        second=0,
        microsecond=0
    )
    # Convert that local time to UTC using provided helper
    return local_to_utc(sess_local_dt)

def check_sessions() -> Optional[str]:
    """
    Timezone-aware session trigger:
    - Converts local session times to UTC at runtime (DST-safe).
    - Resets daily memory at UTC midnight.
    - Fires once per session with ±90s window + a 5min catch-up.
    """
    global last_triggered_sessions, last_reset_date

    now_utc = datetime.now(timezone.utc)
    weekday = now_utc.weekday()

    # 💤 Metals weekend safeguards
    if weekday in [5, 6]:  # Sat/Sun
        return None

    # 🔁 Reset memory at midnight UTC
    if now_utc.date() != last_reset_date:
        last_triggered_sessions.clear()
        last_reset_date = now_utc.date()

    # 🔎 Scan all sessions
    for session_name in SESSIONS.keys():
        scheduled_utc = _scheduled_time_utc_for_today(session_name)
        delta_sec = (now_utc - scheduled_utc).total_seconds()
        last_sent_time = last_triggered_sessions.get(session_name)

        # ✅ Fire inside ±window
        if abs(delta_sec) <= SESSION_TRIGGER_WINDOW_SEC:
            if not last_sent_time:
                last_triggered_sessions[session_name] = now_utc
                return session_name

        # 🧯 Catch-up if we missed (within +5 minutes and not sent yet)
        if 0 < delta_sec <= MISSED_TRIGGER_GRACE_SEC:
            if not last_sent_time:
                last_triggered_sessions[session_name] = now_utc
                return session_name

    return None
