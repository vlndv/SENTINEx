# gpt_analysis.py
# 🧠 Generates concise sniper-level GPT summaries with final Telegram-ready formatting

import time
from openai import OpenAI
from config import GPT_API_KEY, ENABLE_LOGGING, GPT_MODEL
from prompt_formatter import format_spectral_summary

# 🔐 OpenAI client
client = OpenAI(api_key=GPT_API_KEY)

# 📏 Model token capacities (approx.)
MODEL_CAPACITY = {
    "gpt-4o-mini": 16384,
    "gpt-4o": 128000,
    "gpt-3.5-turbo": 4096
}
DEFAULT_CAPACITY = 8192

# 🔁 GPT chat completion with dynamic token budget
def chat_completion(user_text: str, system_prompt: str) -> str | None:
    max_retries = 3
    model_limit = MODEL_CAPACITY.get(GPT_MODEL, DEFAULT_CAPACITY)

    # Reserve at least 1000–1500 tokens for output
    prompt_tokens_est = len(user_text + system_prompt) // 4
    max_output_tokens = max(800, min(1500, model_limit - prompt_tokens_est - 50))

    for attempt in range(1, max_retries + 1):
        try:
            if ENABLE_LOGGING:
                print(f"\n🧠 GPT Request [Attempt {attempt}] — Model: {GPT_MODEL}")
                print(f"DEBUG — Prompt length (chars): {len(user_text)} | Est tokens: {prompt_tokens_est}")
                print(f"DEBUG — Max output tokens allowed: {max_output_tokens}")

            response = client.chat.completions.create(
                model=GPT_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_text}
                ],
                temperature=0.6,
                max_tokens=max_output_tokens
            )

            raw_content = response.choices[0].message.content
            if ENABLE_LOGGING:
                print("DEBUG — Raw GPT Output Before Strip:", repr(raw_content))

            if raw_content and raw_content.strip():
                return raw_content.strip()
            else:
                print(f"⚠️ GPT returned empty content on attempt {attempt}.")

        except Exception as e:
            print(f"❌ GPT API Error [Attempt {attempt}]: {e}")

        time.sleep(1.5)

    return None


# 📝 Prompt template for all summaries
SUMMARY_PROMPT_TEMPLATE = """
You are an elite institutional XAU/USD analyst.
Output the **final Telegram-ready format** exactly as shown below.

Use **these exact section names** (in this exact order):

<b>DOMINANT TREND</b>
• Describe the trend.

<b>LIQUIDITY EVENTS</b>
• Report any key sweeps or reversals happened during the session.

<b>VOLUME BEHAVIOUR</b>
• Explain how the volume moved during the session — for example, sudden spikes, sharp drops, or gradual fading.

<b>SESSION RANGE</b>
• Describe range, highs/lows respected or broken, possible trap, wether to avoid trading or not.

<b>OUTLOOK AHEAD</b>
• One concise forward-looking statement. Forecast the next move with high probability success.

Rules:
- Use only one concise sentence for each section.
- Simple words for less expert traders. 
- No fluff or filler.
- Catchy style.
- Analyze the market with the precision and insight of BlackRock’s Aladdin system.
- Use only smart money concepts: liquidity grabs, BOS/CHoCH, FVGs, rejections, absorption, volume shifts, exhaustion.
- All numbers must be bold.
- Prices must have a maximum of two decimal places (e.g., 3280.88).
- No emojis, icons, or decorative symbols in any section.
- Never use  **double asterisks**.
- Never change header wording, capitalization, or order.
- Do not use bullet points, dashes, or list markers — write in sentences only.
- Do not repeat the header name in the section body.
- Do not repeat the same level or event in multiple sections.
- Do not add any commentary, quotes, or text outside the 5 sections.
- Each section must directly follow its header with no blank line in between.

Do not include:
- Session title/header
- Date or time
- Any random quote
- Any extra footer text
"""

# 📍 SESSION SUMMARY
def generate_session_summary(candles: list, session_name: str):
    if not candles:
        print(f"❌ No candle data for {session_name}")
        return f"⚠️ No candle data for {session_name}"

    # Increased to 100 candles for full-session coverage
    candle_data = "\n".join([
        f"{c['time']} | O:{c['mid']['o']} H:{c['mid']['h']} L:{c['mid']['l']} C:{c['mid']['c']}"
        for c in candles[-100:]
    ])
    if ENABLE_LOGGING:
        print(f"DEBUG — {session_name} using {len(candles[-100:])} candles.")

    user_text = f"""
Analyze these {len(candles[-100:])} M5 candles for {session_name}:
{candle_data}

{SUMMARY_PROMPT_TEMPLATE}
"""

    summary = chat_completion(user_text, "You are a concise institutional trading analyst.")
    return format_spectral_summary(summary, session_name, tz="Europe/Rome") if summary else f"⚠️ GPT returned no output for {session_name}"


# 🌅 MORNING FORECAST
def generate_morning_forecast(candles: list):
    if not candles:
        print("❌ No candle data for Morning Forecast")
        return "⚠️ No candle data for Morning Forecast"

    # Increased to 50 candles for broader Asia context
    candle_data = "\n".join([
        f"{c['time']} | O:{c['mid']['o']} H:{c['mid']['h']} L:{c['mid']['l']} C:{c['mid']['c']}"
        for c in candles[-50:]
    ])

    user_text = f"""
Analyze these overnight (Asia) candles for London session prep:
{candle_data}

{SUMMARY_PROMPT_TEMPLATE}
"""

    summary = chat_completion(user_text, "You are a concise institutional gold forecaster.")
    return format_spectral_summary(summary, "Morning Forecast", tz="Europe/Rome") if summary else "⚠️ GPT returned no output for Morning Forecast"


# 🌙 EVENING REVIEW
def generate_evening_review(candles: list):
    if not candles:
        print("❌ No candle data for Evening Review")
        return "⚠️ No candle data for Evening Review"

    # Increased to 120 candles for full-day coverage
    candle_data = "\n".join([
        f"{c['time']} | O:{c['mid']['o']} H:{c['mid']['h']} L:{c['mid']['l']} C:{c['mid']['c']}"
        for c in candles[-120:]
    ])

    user_text = f"""
Review these full-day XAU/USD candles:
{candle_data}

{SUMMARY_PROMPT_TEMPLATE}
"""

    summary = chat_completion(user_text, "You are a concise institutional gold strategist.")
    return format_spectral_summary(summary, "Evening Review", tz="Europe/Rome") if summary else "⚠️ GPT returned no output for Evening Review"
