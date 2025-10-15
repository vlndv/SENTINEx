# main.py
# 🟦 Spectral Sniper Bot — Session Manager & Execution Entry

import time
import traceback
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from config import ENABLE_LOGGING
from oanda_connector import fetch_latest_data
from gpt_analysis import (
    generate_session_summary,
    generate_morning_forecast,
    generate_evening_review,
)
from telegram_alert import send_telegram_message
from prompt_formatter import format_spectral_summary
from session_tracker import check_sessions  # ✅ Session trigger logic


# 🔀 GPT Handler Router
def dispatch_gpt_handler(session_name: str, candles: list) -> str:
    if session_name == "Morning Forecast":
        return generate_morning_forecast(candles)
    elif session_name == "Evening Review":
        return generate_evening_review(candles)
    else:
        return generate_session_summary(candles, session_name)


# 🔁 Main loop — Calls check_sessions() every 10s
def run_scheduled_sessions(test_mode: bool = False):
    while True:
        try:
            triggered_session = check_sessions()
            print("DEBUG: check_sessions() returned:", triggered_session)

            # Force a test trigger if no session is active
            if test_mode and triggered_session is None:
                triggered_session = "Morning Forecast"
                print("DEBUG: Forcing test session trigger:", triggered_session)

            if triggered_session:
                print(f"⏰ Running GPT logic for: {triggered_session}")

                candles = fetch_latest_data()
                if not candles:
                    print("⚠️ No candle data fetched.")
                    time.sleep(10)
                    continue

                summary = dispatch_gpt_handler(triggered_session, candles)
                formatted = format_spectral_summary(summary, triggered_session)

                print("DEBUG: Sending formatted session message to Telegram...")
                send_telegram_message(formatted)

            time.sleep(10)

        except Exception as e:
            print("❌ Error in session loop:", str(e))
            traceback.print_exc()
            time.sleep(30)


# 🟢 Entry Point
if __name__ == "__main__":

    # ✅ Run loop in test mode (forces triggers if no real session is active)
    run_scheduled_sessions(test_mode=False)
