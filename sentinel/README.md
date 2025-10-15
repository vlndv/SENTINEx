Sentinel – Precision Trading Monitor

Sentinel is a tactical execution and monitoring system built for XAU/USD and high-volatility pairs. It connects to OANDA for live feeds, runs AI-driven analysis, and pushes sniper-grade alerts straight to Telegram.

🔑 Core Functions

Broker Integration → OANDA REST API for price, orders, and account sync.

Session Tracking → Logs and monitors active sessions (London, NY, Asia).

AI Market Analysis → GPT-based model generates directional bias + liquidity trap logic.

Alert System → Pushes clean signals + session reports to Telegram.

Logging → Every session and trigger recorded for review and refinement.

TradingView Script → PineScript EMA/RSI test harness for strategy alignment.

⚡ Setup

Clone the repo

git clone <repo_url>
cd sentinel


Create environment

python3 -m venv venv
source venv/bin/activate


Install dependencies

pip install -r requirements.txt


Configure environment

Copy .env template.

Add:

OANDA_API_KEY

OANDA_ACCOUNT_ID

TELEGRAM_BOT_TOKEN

TELEGRAM_CHAT_ID

Run Sentinel

python sentinel/main.py

🎯 Workflow

Market Feeds → OANDA data streams in real-time.

AI Layer → gpt_analysis.py builds directional bias & trap detection.

Session Tracker → Marks liquidity windows (Asia close, London open, NY overlap).

Alerts → Precision entries and warnings go directly to Telegram.

Logs → Every execution + session stored in /logs.

📂 Key Files

main.py → Launch point.

oanda_connector.py → Broker data + execution.

session_tracker.py → Session-based market mapping.

gpt_analysis.py → AI-driven bias/trap engine.

telegram_alert.py → Signal dispatch to Telegram.

emaretest.pinescript → TradingView backtest tool.

📲 Telegram Alert Samples
🔔 Bias Update
[Sentinel Update]
Session: London Open
Bias: SHORT
Reason: Liquidity sweep above 2354 → strong rejection
Confluence: EMA crossover + RSI divergence
Action: Wait for NY overlap for precision entry

⚡ Trade Trigger
[Sentinel Signal]
PAIR: XAUUSD
Direction: LONG
Entry Zone: 2321.50 – 2323.00
Stop Loss: 2317.20
Take Profit: 2335.00
Reason: Liquidity grab below Asia Low + RSI reset

📑 Session Report
[Sentinel Session Report]
Date: 2025-08-25
Asia: Range → liquidity build
London: Swept highs, bias SHORT
NY: Confirmed drop into 2320 zone
Trades Logged: 3
Result: +145 pips

🛠 Next Steps

Refine GPT prompt templates (prompt_formatter.py).

Expand liquidity-trap detection rules.

Add risk management module (lot sizing, SL/TP enforcement).

⚔️ Execution Mindset

This is not a retail signal bot.
Sentinel is built for precision traders running sniper setups — institutional timing, liquidity hunts, and clean alerts only.