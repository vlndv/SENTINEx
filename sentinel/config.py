import os
from datetime import datetime, time
from dotenv import load_dotenv
from zoneinfo import ZoneInfo

# ✅ Load environment variables from .env file in the same directory
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))

# 🔐 API Keys from .env
OANDA_API_KEY = os.getenv("OANDA_API_KEY")
OANDA_ACCOUNT_ID = os.getenv("OANDA_ACCOUNT_ID")
GPT_API_KEY = os.getenv("GPT_API_KEY")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# 🧠 GPT model selection (default = gpt-4o)
GPT_MODEL = os.getenv("GPT_MODEL", "gpt-4o")

# ✅ Session schedule (times are in CEST – Central European Summer Time)
SESSIONS = {
    # Forecast and Review
    "Morning Forecast": time(hour=6, minute=45),
    "Evening Review": time(hour=23, minute=0),

    # Asia + Pacific
    "Sydney Open": time(hour=0, minute=5),
    "Asian Open": time(hour=1, minute=0),
    "Tokyo Open": time(hour=1, minute=0),
    "Tokyo Close": time(hour=9, minute=0),

    # Europe
    "Frankfurt Open": time(hour=7, minute=0),
    "London Open": time(hour=8, minute=0),
    "Frankfurt Close": time(hour=9, minute=30),
    "London Close": time(hour=16, minute=30),

    # US Sessions
    "Pre-New York": time(hour=13, minute=30),
    "New York Open": time(hour=14, minute=30),
    "NY Lunch": time(hour=17, minute=30),
    "New York Close": time(hour=22, minute=0),

    # Post-NY Asia ramp-up
    "Asia Reopen": time(hour=0, minute=30),

    # Testing
    "Test Trigger": time(hour=21, minute=34),
}

# 🕒 Matching display windows for Telegram formatting
SESSION_WINDOWS = {
    "Morning Forecast": "06:45–07:00",
    "Evening Review": "23:00–23:15",
    "Sydney Open": "00:05–00:30",
    "Asian Open": "01:00–01:30",
    "Tokyo Open": "01:00–01:30",
    "Tokyo Close": "09:00–09:30",
    "Frankfurt Open": "07:00–07:30",
    "London Open": "08:00–10:00",
    "Frankfurt Close": "09:30–10:00",
    "London Close": "16:30–17:00",
    "Pre-New York": "13:30–14:30",
    "New York Open": "14:30–15:30",
    "NY Lunch": "17:30–18:30",
    "New York Close": "22:00–22:30",
    "Asia Reopen": "00:30–01:00",
    "Test Trigger": "Test Window"
}

# 🔁 Loop and logging control
SESSION_ALERT_DELAY_SEC = 15
ENABLE_LOGGING = True

# 🧭 OANDA account and feed configuration
OANDA_ACCOUNT_TYPE = os.getenv("OANDA_ACCOUNT_TYPE", "practice")  # or 'live'
OANDA_DOMAIN = (
    "https://api-fxpractice.oanda.com"
    if OANDA_ACCOUNT_TYPE == "practice"
    else "https://api-fxtrade.oanda.com"
)

INSTRUMENT = "XAU_USD"
GRANULARITY = "M5"

# 🚨 Required .env variables validation
REQUIRED_ENV_VARS = {
    "OANDA_API_KEY": OANDA_API_KEY,
    "OANDA_ACCOUNT_ID": OANDA_ACCOUNT_ID,
    "GPT_API_KEY": GPT_API_KEY,
    "TELEGRAM_BOT_TOKEN": TELEGRAM_BOT_TOKEN,
    "TELEGRAM_CHAT_ID": TELEGRAM_CHAT_ID,
}

missing_vars = [key for key, val in REQUIRED_ENV_VARS.items() if not val or "xxx" in val.lower()]
if missing_vars:
    raise EnvironmentError(
        f"❌ Missing or invalid environment variables: {', '.join(missing_vars)}\n"
        "Please check your .env file and complete all required variables."
    )

# 🛡 Validation: Ensure SESSIONS times are datetime.time objects
for s_name, s_time in SESSIONS.items():
    if not hasattr(s_time, "hour"):
        raise TypeError(
            f"❌ SESSIONS entry '{s_name}' must be a datetime.time object, got {type(s_time)} ({s_time})"
        )

# 🌐 Timezone Conversion Utilities
LOCAL_TZ = ZoneInfo("Europe/Rome")  # Set to your local timezone

def utc_to_local(utc_dt: datetime) -> datetime:
    """Converts a UTC datetime to local time (Europe/Rome)."""
    return utc_dt.replace(tzinfo=ZoneInfo("UTC")).astimezone(LOCAL_TZ)

def local_to_utc(local_dt: datetime) -> datetime:
    """Converts a local datetime (Europe/Rome) to UTC."""
    return local_dt.replace(tzinfo=LOCAL_TZ).astimezone(ZoneInfo("UTC"))
