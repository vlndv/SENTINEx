import os
import csv

from datetime import datetime

# 🔁 Path where logs will be saved (auto-sorted by date)
LOG_DIR = os.path.join(os.path.dirname(__file__), "logs")

def _get_today_log_paths():
    """
    Returns file paths for today's .txt and .csv logs.
    Auto-creates folders as needed.
    """
    today = datetime.now().strftime("%Y-%m-%d")
    day_dir = os.path.join(LOG_DIR, today)
    os.makedirs(day_dir, exist_ok=True)

    txt_path = os.path.join(day_dir, f"{today}_summary_log.txt")
    csv_path = os.path.join(day_dir, f"{today}_summary_log.csv")
    return txt_path, csv_path


def log_message(session_name: str, summary: str, candle_count: int):
    """
    Logs session summary to both TXT and CSV formats in dated folder.
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    txt_path, csv_path = _get_today_log_paths()

    # ───────────────── TXT LOG ─────────────────
    with open(txt_path, "a", encoding="utf-8") as txt_log:
        txt_log.write(f"\n{'─' * 60}\n")
        txt_log.write(f"[{timestamp}] SESSION: {session_name} | {candle_count} candles\n")
        txt_log.write(summary + "\n")

    # ───────────────── CSV LOG ─────────────────
    file_exists = os.path.isfile(csv_path)
    with open(csv_path, "a", newline='', encoding="utf-8") as csv_log:
        writer = csv.writer(csv_log)
        if not file_exists:
            writer.writerow(["Timestamp", "Session", "CandleCount", "Summary"])
        writer.writerow([timestamp, session_name, candle_count, summary.replace("\n", " ")[:1000]])
