"""
Daily Market Analysis Email Script
====================================
Invia ogni mattina un'analisi di mercato professionale via email,
generata da Claude AI con dati aggiornati in tempo reale.

SETUP:
  pip install anthropic yfinance requests schedule

CONFIGURAZIONE:
  1. Imposta le variabili d'ambiente (vedi sezione CONFIG)
  2. Esegui: python daily_market_email.py
  3. Per schedularlo automaticamente vedi le istruzioni in fondo al file

VARIABILI D'AMBIENTE RICHIESTE:
  ANTHROPIC_API_KEY   → chiave API Anthropic (https://console.anthropic.com)
  SMTP_HOST           → es. smtp.gmail.com
  SMTP_PORT           → es. 587
  SMTP_USER           → tuo indirizzo email mittente
  SMTP_PASSWORD       → password app (per Gmail: https://myaccount.google.com/apppasswords)
  EMAIL_TO            → indirizzo email destinatario
"""

import os
import smtplib
import schedule
import time
import json
from datetime import datetime, date
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import anthropic
import yfinance as yf
import requests

# ─────────────────────────────────────────────
# CONFIG — modifica qui o usa variabili d'ambiente
# ─────────────────────────────────────────────
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "YOUR_ANTHROPIC_API_KEY")
SMTP_HOST         = os.getenv("SMTP_HOST",    "smtp.gmail.com")
SMTP_PORT         = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER         = os.getenv("SMTP_USER",    "tuo@email.com")
SMTP_PASSWORD     = os.getenv("SMTP_PASSWORD","la_tua_password_app")
EMAIL_TO          = os.getenv("EMAIL_TO",     "destinatario@email.com")

SEND_TIME         = "09:00"   # orario invio (HH:MM)

# Ticker monitorati
TICKERS = {
    "Azioni":          ["^GSPC", "FTSEMIB.MI", "^IXIC", "^DJI", "^STOXX50E"],
    "Crypto":          ["BTC-USD", "ETH-USD", "SOL-USD"],
    "Materie Prime":   ["GC=F", "CL=F", "SI=F", "NG=F"],
    "Forex":           ["EURUSD=X", "GBPUSD=X", "USDJPY=X", "USDCHF=X"],
}

TICKER_LABELS = {
    "^GSPC":      "S&P 500",
    "FTSEMIB.MI": "FTSE MIB",
    "^IXIC":      "NASDAQ",
    "^DJI":       "Dow Jones",
    "^STOXX50E":  "Euro Stoxx 50",
    "BTC-USD":    "Bitcoin",
    "ETH-USD":    "Ethereum",
    "SOL-USD":    "Solana",
    "GC=F":       "Oro",
    "CL=F":       "Petrolio WTI",
    "SI=F":       "Argento",
    "NG=F":       "Gas Naturale",
    "EURUSD=X":   "EUR/USD",
    "GBPUSD=X":   "GBP/USD",
    "USDJPY=X":   "USD/JPY",
    "USDCHF=X":   "USD/CHF",
}

# ─────────────────────────────────────────────
# 1. RACCOLTA DATI DI MERCATO
# ─────────────────────────────────────────────
def fetch_market_data() -> dict:
    """Scarica prezzi, variazioni % e volumi per tutti i ticker."""
    data = {}
    all_tickers = [t for group in TICKERS.values() for t in group]

    for ticker_sym in all_tickers:
        try:
            tk   = yf.Ticker(ticker_sym)
            hist = tk.history(period="5d", interval="1d")
            if len(hist) < 2:
                continue

            prev_close = hist["Close"].iloc[-2]
            last_close = hist["Close"].iloc[-1]
            volume     = hist["Volume"].iloc[-1]
            pct_change = (last_close - prev_close) / prev_close * 100

            # 52-week high/low
            hist_1y = tk.history(period="1y", interval="1d")
            high_52w = hist_1y["High"].max()  if len(hist_1y) else None
            low_52w  = hist_1y["Low"].min()   if len(hist_1y) else None

            data[ticker_sym] = {
                "label":       TICKER_LABELS.get(ticker_sym, ticker_sym),
                "last":        round(last_close, 4),
                "prev_close":  round(prev_close, 4),
                "pct_change":  round(pct_change, 2),
                "volume":      int(volume) if volume else 0,
                "high_52w":    round(high_52w, 4) if high_52w else None,
                "low_52w":     round(low_52w, 4)  if low_52w  else None,
            }
        except Exception as e:
            print(f"  [WARN] {ticker_sym}: {e}")

    return data


def fetch_fear_greed() -> str:
    """Scarica l'indice Fear & Greed di CNN."""
    try:
        url = "https://production.dataviz.cnn.io/index/fearandgreed/graphdata"
        r   = requests.get(url, timeout=10,
                           headers={"User-Agent": "Mozilla/5.0"})
        score = r.json()["fear_and_greed"]["score"]
        rating = r.json()["fear_and_greed"]["rating"]
        return f"{score:.0f}/100 ({rating})"
    except Exception:
        return "N/D"


# ─────────────────────────────────────────────
# 2. GENERAZIONE ANALISI CON CLAUDE
# ─────────────────────────────────────────────
def generate_analysis(market_data: dict, fear_greed: str) -> str:
    """Chiede a Claude un'analisi professionale basata sui dati raccolti."""
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    today = date.today().strftime("%A %d %B %Y")
    data_str = json.dumps(market_data, indent=2, ensure_ascii=False)

    prompt = f"""
Oggi è {today}. Sei un analista quantitativo senior con esperienza in equity, fixed income,
commodities e macro. Il tuo destinatario è un neolaureato magistrale in finanza.

Dati di mercato aggiornati:
{data_str}

Fear & Greed Index: {fear_greed}

Scrivi una DAILY MARKET BRIEF in italiano, strutturata così:

1. **Executive Summary** (3-5 righe) — sintesi del sentiment e dei driver principali
2. **Equity** — analisi di S&P 500, FTSE MIB, Nasdaq, Dow Jones, Euro Stoxx 50:
   performance, livelli chiave, eventuale distanza da 52w high/low
3. **Crypto** — BTC, ETH, SOL: momentum, dominance relativa, segnali tecnici
4. **Forex** — EUR/USD, GBP/USD, USD/JPY, USD/CHF: movimenti, possibili catalizzatori macro
5. **Materie Prime** — Oro, Petrolio WTI, Argento, Gas: dinamiche domanda/offerta e geopolitica
6. **Fear & Greed & Sentiment** — interpretazione dell'indice e implicazioni per il rischio
7. **Outlook & Risk Watch** — 2-3 temi macro/micro da tenere d'occhio nelle prossime 48h

Usa terminologia tecnica appropriata (beta, sharpe, spread, momentum, mean reversion…).
Evita banalità. Sii conciso ma sostanzioso. Usa il grassetto per i valori numerici chiave.
Rispondi SOLO con il testo della brief, senza preamboli.
"""

    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=2000,
        messages=[{"role": "user", "content": prompt}],
    )
    return message.content[0].text


# ─────────────────────────────────────────────
# 3. COMPOSIZIONE EMAIL HTML
# ─────────────────────────────────────────────
def build_html_email(analysis_text: str, market_data: dict) -> str:
    """Crea un template HTML professionale per la mail."""
    today_str = date.today().strftime("%d %B %Y")

    # Mini tabella riepilogativa
    rows = ""
    for sym, info in market_data.items():
        color  = "#16a34a" if info["pct_change"] >= 0 else "#dc2626"
        arrow  = "▲" if info["pct_change"] >= 0 else "▼"
        rows += f"""
        <tr>
          <td style="padding:6px 12px;border-bottom:1px solid #f0f0f0;">{info['label']}</td>
          <td style="padding:6px 12px;border-bottom:1px solid #f0f0f0;text-align:right;font-weight:600;">
            {info['last']:,.4g}
          </td>
          <td style="padding:6px 12px;border-bottom:1px solid #f0f0f0;text-align:right;
                     color:{color};font-weight:700;">
            {arrow} {abs(info['pct_change']):.2f}%
          </td>
        </tr>"""

    # Converti markdown minimo in HTML
    html_body = analysis_text \
        .replace("**", "<b>", 1)
    # Semplice sostituzione grassetto
    import re
    html_body = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', analysis_text)
    html_body = html_body.replace("\n\n", "</p><p>").replace("\n", "<br>")
    html_body = f"<p>{html_body}</p>"

    return f"""
<!DOCTYPE html>
<html lang="it">
<head>
  <meta charset="UTF-8">
  <style>
    body {{ font-family: 'Helvetica Neue', Arial, sans-serif; background:#f8f9fa;
            color:#1a1a1a; margin:0; padding:0; }}
    .container {{ max-width:680px; margin:30px auto; background:#fff;
                  border-radius:10px; overflow:hidden;
                  box-shadow:0 2px 12px rgba(0,0,0,.08); }}
    .header {{ background:linear-gradient(135deg,#0f172a,#1e3a5f);
               padding:28px 32px; color:#fff; }}
    .header h1 {{ margin:0; font-size:22px; font-weight:700; letter-spacing:.5px; }}
    .header p  {{ margin:6px 0 0; font-size:13px; opacity:.75; }}
    .snapshot  {{ padding:24px 32px; background:#f0f4ff; border-bottom:1px solid #e2e8f0; }}
    .snapshot h2 {{ margin:0 0 14px; font-size:14px; text-transform:uppercase;
                   letter-spacing:1px; color:#475569; }}
    table {{ width:100%; border-collapse:collapse; font-size:14px; }}
    th {{ padding:6px 12px; text-align:left; color:#64748b; font-size:12px;
          text-transform:uppercase; letter-spacing:.5px; }}
    .analysis {{ padding:28px 32px; font-size:15px; line-height:1.75; color:#1e293b; }}
    .analysis h2,h3 {{ color:#0f172a; }}
    .footer {{ background:#f1f5f9; padding:16px 32px; text-align:center;
               font-size:12px; color:#94a3b8; }}
  </style>
</head>
<body>
<div class="container">
  <div class="header">
    <h1>📈 Daily Market Brief</h1>
    <p>{today_str} — Analisi professionale generata da Claude AI</p>
  </div>

  <div class="snapshot">
    <h2>Snapshot Mercati</h2>
    <table>
      <tr>
        <th>Asset</th>
        <th style="text-align:right">Ultimo</th>
        <th style="text-align:right">Δ%</th>
      </tr>
      {rows}
    </table>
  </div>

  <div class="analysis">
    {html_body}
  </div>

  <div class="footer">
    Questo report è generato automaticamente a scopo informativo.<br>
    Non costituisce consulenza finanziaria. Dati: Yahoo Finance.
  </div>
</div>
</body>
</html>
"""


# ─────────────────────────────────────────────
# 4. INVIO EMAIL
# ─────────────────────────────────────────────
def send_email(html_content: str):
    """Invia la mail via SMTP con TLS."""
    today_str = date.today().strftime("%d/%m/%Y")
    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"📈 Daily Market Brief — {today_str}"
    msg["From"]    = SMTP_USER
    msg["To"]      = EMAIL_TO
    msg.attach(MIMEText(html_content, "html", "utf-8"))

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
        server.ehlo()
        server.starttls()
        server.login(SMTP_USER, SMTP_PASSWORD)
        server.sendmail(SMTP_USER, EMAIL_TO, msg.as_string())
    print(f"  ✅ Email inviata a {EMAIL_TO}")


# ─────────────────────────────────────────────
# 5. PIPELINE COMPLETA
# ─────────────────────────────────────────────
def run_daily_brief():
    print(f"\n[{datetime.now():%H:%M:%S}] Avvio Daily Market Brief...")

    print("  → Raccolta dati di mercato...")
    market_data = fetch_market_data()

    print("  → Fear & Greed Index...")
    fear_greed = fetch_fear_greed()

    print("  → Generazione analisi con Claude...")
    analysis = generate_analysis(market_data, fear_greed)

    print("  → Composizione email HTML...")
    html = build_html_email(analysis, market_data)

    print("  → Invio email...")
    send_email(html)

    print(f"[{datetime.now():%H:%M:%S}] Brief completata.\n")


# ─────────────────────────────────────────────
# 6. SCHEDULER
# ─────────────────────────────────────────────
if __name__ == "__main__":
    print(f"Daily Market Brief scheduler avviato — invio ogni giorno alle {SEND_TIME}")
    print("Premi Ctrl+C per fermare.\n")

    schedule.every().day.at(SEND_TIME).do(run_daily_brief)

    # Esegui subito al primo avvio (rimuovi se non lo vuoi)
    run_daily_brief()

    while True:
        schedule.run_pending()
        time.sleep(30)


# ═══════════════════════════════════════════════════════════════
# GUIDA RAPIDA AL DEPLOY
# ═══════════════════════════════════════════════════════════════
#
# ── OPZIONE A: Esecuzione manuale (terminale aperto) ────────────
#   export ANTHROPIC_API_KEY="sk-ant-..."
#   export SMTP_USER="tuo@gmail.com"
#   export SMTP_PASSWORD="xxxx xxxx xxxx xxxx"   # Password app Gmail
#   export EMAIL_TO="destinatario@email.com"
#   python daily_market_email.py
#
# ── OPZIONE B: Cron job su Linux/Mac ───────────────────────────
#   crontab -e
#   # Aggiungi questa riga (invia alle 09:00 ogni giorno):
#   0 9 * * * ANTHROPIC_API_KEY=sk-ant-... SMTP_USER=... SMTP_PASSWORD=... \
#             EMAIL_TO=... /usr/bin/python3 /percorso/daily_market_email.py
#
# ── OPZIONE C: Task Scheduler su Windows ───────────────────────
#   1. Apri "Utilità di pianificazione"
#   2. Crea attività → Azione: python C:\percorso\daily_market_email.py
#   3. Trigger: ogni giorno alle 09:00
#   4. Imposta le variabili d'ambiente nelle proprietà del sistema
#
# ── OPZIONE D: Deploy su server cloud (es. Railway, Render) ────
#   1. Crea un repo GitHub con questo file
#   2. Collega a Railway/Render come "Worker" (non web server)
#   3. Imposta le env vars nella dashboard
#   4. Deploy — girerà 24/7 e invierà la mail ogni mattina
#
# ── NOTE SU GMAIL ───────────────────────────────────────────────
#   Per usare Gmail come mittente devi usare una "Password per le app":
#   https://myaccount.google.com/apppasswords
#   (richiede la verifica in due passaggi attiva)
# ═══════════════════════════════════════════════════════════════
