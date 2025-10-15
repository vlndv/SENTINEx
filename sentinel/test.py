# dev_trigger.py
# 🧪 Manual test runner for Spectral Sniper GPT session logic

from oanda_connector import fetch_latest_data
from gpt_analysis import (
    generate_session_summary,
    generate_morning_forecast,
    generate_evening_review,
)
from telegram_alert import send_telegram_message
from prompt_formatter import format_spectral_summary
from log_writer import log_message
from config import ENABLE_LOGGING


def run_manual_test(session_name: str = "London Open"):
    """
    Triggers a full manual test of one session (e.g. "London Open", "Morning Forecast").
    Includes: fetching data, generating GPT summary, formatting, sending to Telegram, and logging.
    """
    try:
        print(f"\n🧪 TEST STARTED: {session_name}")

        # 1. Fetch data (30 M5 candles for context)
        candles = fetch_latest_data(count=30)
        if not candles:
            print("❌ No candle data fetched. Check OANDA connectivity.")
            return
        print(f"✅ Retrieved {len(candles)} candles for test.")

        # 2. Generate GPT summary
        # For tests, always ensure GPT is forced to fill all sections
        if session_name == "Morning Forecast":
            summary = generate_morning_forecast(candles)
        elif session_name == "Evening Review":
            summary = generate_evening_review(candles)
        else:
            # Pass a larger recent set so GPT has real market structure to analyze
            summary = generate_session_summary(candles, session_name)

        # 3. Debug GPT raw return
        if ENABLE_LOGGING:
            print("\nDEBUG — GPT Returned Summary Preview:")
            print(summary[:500] + ("..." if len(summary) > 500 else ""))

        if not summary or "Failed" in summary:
            print("⚠️ GPT summary generation failed or returned incomplete result.")
            return

        # 4. Format for Telegram (keeps formatting consistent with production flow)
        formatted_message = format_spectral_summary(summary, session_name)
        print("\n📝 Formatted Message Preview (first 500 chars):\n")
        print(formatted_message[:500] + ("..." if len(formatted_message) > 500 else ""))
        print("🧪 Message length:", len(formatted_message))

        # 5. Send to Telegram
        print("\n📤 Sending to Telegram...")
        sent = send_telegram_message(formatted_message)
        if sent:
            print("✅ Telegram message sent.")
        else:
            print("❌ Telegram failed — check logs or telegram_logs/telegram_failures.log")

        # 6. Log the summary
        log_message(session_name, summary, candle_count=len(candles))
        print("🗂️ Log entry saved.")

    except Exception as e:
        print(f"❌ TEST ERROR: {str(e)}")


# 🟢 Direct Execution
if __name__ == "__main__":
    run_manual_test("Pre-New York")
