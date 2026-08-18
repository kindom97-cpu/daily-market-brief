# 📈 Daily Market Brief — Deploy su Railway

## File inclusi
| File | Descrizione |
|------|-------------|
| `daily_market_email.py` | Script principale |
| `requirements.txt` | Dipendenze Python |
| `Procfile` | Dice a Railway come avviare lo script |
| `README.md` | Questa guida |

---

## 🚀 Guida al Deploy (passo per passo)

### STEP 1 — Crea un account GitHub (se non ce l'hai)
1. Vai su [github.com](https://github.com) → **Sign up**
2. Crea un account gratuito

---

### STEP 2 — Crea un repository GitHub
1. Vai su [github.com/new](https://github.com/new)
2. Nome repo: `daily-market-brief`
3. Lascia tutto il resto di default → clicca **Create repository**
4. Carica i 3 file (`daily_market_email.py`, `requirements.txt`, `Procfile`):
   - Clicca **uploading an existing file**
   - Trascina i 3 file
   - Clicca **Commit changes**

---

### STEP 3 — Crea un account Railway
1. Vai su [railway.app](https://railway.app)
2. Clicca **Start a New Project** → **Login with GitHub**
3. Autorizza Railway ad accedere al tuo GitHub

---

### STEP 4 — Crea il progetto su Railway
1. Dashboard Railway → **New Project**
2. Seleziona **Deploy from GitHub repo**
3. Scegli il repo `daily-market-brief`
4. Railway rileva automaticamente i file → clicca **Deploy Now**

---

### STEP 5 — Imposta le variabili d'ambiente ⚠️ (passo cruciale)
1. Nel tuo progetto Railway, clicca sul servizio creato
2. Vai su **Variables** (menu in alto)
3. Aggiungi queste variabili una per una cliccando **+ New Variable**:

| Nome variabile | Valore |
|----------------|--------|
| `ANTHROPIC_API_KEY` | La tua chiave da [console.anthropic.com](https://console.anthropic.com) |
| `SMTP_HOST` | `smtp.gmail.com` |
| `SMTP_PORT` | `587` |
| `SMTP_USER` | La tua email Gmail (es. `tuo@gmail.com`) |
| `SMTP_PASSWORD` | La **password per le app** Gmail (vedi sotto) |
| `EMAIL_TO` | L'email dove vuoi ricevere la brief |

4. Clicca **Deploy** per riavviare con le nuove variabili

---

### 🔑 Come ottenere la Password App Gmail
> La password normale di Gmail **non funziona**. Devi usare una "Password per le app".

1. Vai su [myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords)
2. Seleziona **Altro (nome personalizzato)** → scrivi `MarketBrief`
3. Clicca **Genera**
4. Copia la password di 16 caratteri (es. `abcd efgh ijkl mnop`)
5. Usala come valore di `SMTP_PASSWORD` su Railway

> ⚠️ Requisito: la verifica in due passaggi deve essere attiva sul tuo account Google

---

### STEP 6 — Verifica che funzioni
1. In Railway, clicca sul tuo servizio → **Logs**
2. Dovresti vedere:
   ```
   Daily Market Brief scheduler avviato — invio ogni giorno alle 09:00
   → Raccolta dati di mercato...
   → Fear & Greed Index...
   → Generazione analisi con Claude...
   → Invio email...
   ✅ Email inviata a tuo@email.com
   ```
3. Controlla la tua casella email!

---

## 💰 Costi stimati
| Servizio | Costo |
|----------|-------|
| Railway | ~$5/mese (piano Hobby) oppure gratuito con $5 di crediti iniziali |
| Anthropic API | ~$0.01–0.03 per email (modello Sonnet) |
| **Totale** | **~$5–6/mese** |

---

## ❓ Problemi comuni

**"Authentication failed" per Gmail**
→ Stai usando la password normale invece della Password App. Rigenera da [myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords)

**"Module not found"**
→ Verifica che `requirements.txt` sia nella root del repo GitHub

**Non ricevo la mail**
→ Controlla la cartella Spam. Aggiungi il mittente ai contatti.

**Lo script si ferma dopo la prima email**
→ Normale! Railway lo riavvia automaticamente. Controlla i Logs.
