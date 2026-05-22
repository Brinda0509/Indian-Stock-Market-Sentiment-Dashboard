"""
AUTO OUTAGE CLASSIFIER
Reads broker_outage_news.xlsx, filters real outages automatically,
assigns severity scores, and outputs a clean verified list.
"""

import pandas as pd
import re

# ── PATHS ─────────────────────────────────────────────────────────────────────
INPUT_FILE  = r"C:\Users\ELCOT\Desktop\Aivar\Dataset\broker_outage_news.xlsx"
OUTPUT_FILE = r"C:\Users\ELCOT\Desktop\Aivar\Dataset\verified_outages.xlsx"

# ── KEYWORD RULES ─────────────────────────────────────────────────────────────

# If headline contains ANY of these → likely a real outage
OUTAGE_KEYWORDS = [
    'down', 'outage', 'not working', 'unable to', 'cannot',
    'glitch', 'technical issue', 'technical glitch', 'disruption',
    'halt', 'halted', 'suspended', 'crash', 'crashed', 'offline',
    'server down', 'app down', 'trading halted', 'login failed',
    'login issue', 'access issue', 'connectivity', 'error',
    'users report', 'users face', 'users unable', 'facing issue',
    'service disruption', 'platform down', 'not accessible',
    'kaam nahi', 'band ho gaya',   # Hindi terms
]

# If headline contains ANY of these → NOT an outage (reject)
REJECT_KEYWORDS = [
    'launches', 'introduces', 'raises', 'funding', 'ipo',
    'feature', 'comparison', 'vs ', 'versus', 'review',
    'tips', 'how to', 'guide', 'tutorial', 'best broker',
    'charges', 'fee', 'brokerage', 'offer', 'discount',
    'partnership', 'acquisition', 'merger', 'appoints',
    'quarterly', 'annual', 'results', 'profit', 'revenue',
    'hire', 'hiring', 'job', 'career', 'expand',
]

# Severity rules — checked in order, first match wins
SEVERITY_RULES = [
    # Score 1.0 — full halt / exchange level
    (1.0, ['trading halted', 'trading suspended', 'exchange down',
           'nse down', 'bse down', 'market halted', 'expelled',
           'defaulter', 'full outage', 'complete outage']),

    # Score 0.8 — login completely broken, FNO positions at risk
    (0.8, ['unable to login', 'cannot login', 'login failed',
           'login issue', 'cannot trade', 'unable to trade',
           'position', 'fno', 'futures', 'options', 'sell order',
           'order failed', 'order not', 'app down', 'platform down']),

    # Score 0.6 — partial outage, delays
    (0.6, ['partial', 'delay', 'delayed', 'slow', 'intermittent',
           'some users', 'few users', 'connectivity', 'access issue',
           'server issue', 'technical issue', 'glitch']),

    # Score 0.5 — minor, resolved quickly
    (0.5, ['minor', 'brief', 'temporarily', 'briefly', 'resolved',
           'fixed', 'restored', 'back online', 'down for']),
]

DEFAULT_SEVERITY = 0.5   # fallback if no rule matches but it's still an outage

# Broker name detection
BROKER_PATTERNS = {
    'Zerodha'  : ['zerodha', 'kite'],
    'Groww'    : ['groww'],
    'AngelOne' : ['angelone', 'angel one', 'angel broking'],
    'Upstox'   : ['upstox'],
    'NSE'      : ['nse', 'national stock exchange'],
    'BSE'      : ['bse', 'bombay stock exchange'],
    'Exchange' : ['exchange', 'sebi'],
}

# ── FUNCTIONS ─────────────────────────────────────────────────────────────────

def clean_text(text):
    return str(text).lower().strip()

def is_real_outage(headline):
    h = clean_text(headline)
    # Reject if any reject keyword found
    for kw in REJECT_KEYWORDS:
        if kw in h:
            return False
    # Accept if any outage keyword found
    for kw in OUTAGE_KEYWORDS:
        if kw in h:
            return True
    return False

def get_severity(headline):
    h = clean_text(headline)
    for score, keywords in SEVERITY_RULES:
        for kw in keywords:
            if kw in h:
                return score
    return DEFAULT_SEVERITY

def get_broker(headline, query):
    h = clean_text(headline + ' ' + str(query))
    for broker, patterns in BROKER_PATTERNS.items():
        for p in patterns:
            if p in h:
                return broker
    return 'Unknown'

def clean_date(date_str):
    try:
        # Handle all formats including Google RSS: "Mon, 06 Nov 2023 10:30:00 GMT"
        d = pd.to_datetime(str(date_str), errors='coerce', utc=True)
        if pd.isna(d):
            cleaned = re.sub(r"[A-Z]{2,4}$", "", str(date_str)).strip()
            d = pd.to_datetime(cleaned, errors="coerce")
        return d.strftime("%Y-%m-%d") if pd.notna(d) else None
    except:
        return None

# ── MAIN ──────────────────────────────────────────────────────────────────────
print("=" * 60)
print("  AUTO OUTAGE CLASSIFIER")
print("=" * 60)

# Load
print(f"\n  Loading: {INPUT_FILE}")
df = pd.read_excel(INPUT_FILE)
print(f"  Total articles: {len(df)}")
print(f"  Columns: {df.columns.tolist()}")

# Detect headline and date columns
headline_col = None
date_col     = None
query_col    = None

for c in df.columns:
    cl = c.lower()
    if 'headline' in cl or 'title' in cl: headline_col = c
    if 'date' in cl or 'published' in cl: date_col = c
    if 'query' in cl: query_col = c

print(f"\n  Headline col : {headline_col}")
print(f"  Date col     : {date_col}")
print(f"  Query col    : {query_col}")

# ── STEP 1: Filter real outages ───────────────────────────────────────────────
print("\n  Filtering real outages...")
df['Is_Outage'] = df[headline_col].apply(is_real_outage)
real = df[df['Is_Outage']].copy()
print(f"  Real outages found : {len(real)} / {len(df)}")
print(f"  Rejected           : {len(df) - len(real)}")

# ── STEP 2: Assign severity ───────────────────────────────────────────────────
real['Severity'] = real[headline_col].apply(get_severity)

# ── STEP 3: Detect broker ────────────────────────────────────────────────────
qcol = query_col if query_col else headline_col
real['Broker'] = real.apply(
    lambda row: get_broker(row[headline_col], row[qcol]), axis=1
)

# ── STEP 4: Clean dates ───────────────────────────────────────────────────────
# Debug: show sample raw date values before parsing
print(f"\n  Sample raw dates from file:")
print(real[date_col].dropna().head(5).to_string())
real['Clean_Date'] = real[date_col].apply(clean_date)
failed = real['Clean_Date'].isna().sum()
print(f"  Dates parsed successfully : {real['Clean_Date'].notna().sum()}")
print(f"  Dates failed to parse     : {failed}")
real = real.dropna(subset=['Clean_Date'])

# ── STEP 5: Keep one entry per date per broker (highest severity) ─────────────
real = (
    real.sort_values('Severity', ascending=False)
        .drop_duplicates(subset=['Clean_Date', 'Broker'])
        .sort_values('Clean_Date')
        .reset_index(drop=True)
)

# ── STEP 6: Filter to project date range ─────────────────────────────────────
real['Clean_Date'] = pd.to_datetime(real['Clean_Date'])
real = real[
    (real['Clean_Date'] >= '2023-01-01') &
    (real['Clean_Date'] <= '2025-12-31')
]

print(f"\n  After deduplication: {len(real)} unique outage events")

# ── STEP 7: Show results ──────────────────────────────────────────────────────
print("\n  VERIFIED OUTAGE EVENTS:")
print("-" * 60)
display_cols = ['Clean_Date', 'Broker', 'Severity', headline_col]
display_cols = [c for c in display_cols if c in real.columns]
print(real[display_cols].to_string(index=False))

# ── STEP 8: Save Excel ────────────────────────────────────────────────────────
real.to_excel(OUTPUT_FILE, index=False)
print(f"\n  ✅ Saved: verified_outages.xlsx")

# ── STEP 9: Auto-generate pipeline code ──────────────────────────────────────
print("\n" + "=" * 60)
print("  COPY THIS INTO YOUR pipeline.py")
print("=" * 60)
print("\nBROKER_OUTAGES = [")

# Always include the 5 manually verified dates first
manual = [
    ("2023-11-06", "Zerodha",  0.8, "Verified — 1600+ Downdetector reports"),
    ("2023-12-04", "Zerodha",  0.6, "Verified — Zerodha acknowledged second glitch"),
    ("2024-01-13", "Groww",    0.5, "Verified — pre-market outage"),
    ("2024-01-23", "Groww",    0.8, "Verified — login/trading access down"),
    ("2024-11-26", "Exchange", 1.0, "Verified — Artha Vrddhi NSE expelled"),
]

manual_dates = set(d for d, *_ in manual)

for date, broker, severity, note in manual:
    print(f'    {{"date": "{date}", "broker": "{broker}", '
          f'"severity": {severity}}},  # {note}')

# Add auto-detected ones not already in manual list
auto_added = 0
for _, row in real.iterrows():
    d = row['Clean_Date'].strftime('%Y-%m-%d')
    if d not in manual_dates:
        broker   = row['Broker']
        severity = row['Severity']
        headline = str(row[headline_col])[:60]
        print(f'    {{"date": "{d}", "broker": "{broker}", '
              f'"severity": {severity}}},  # Auto: {headline}')
        auto_added += 1

print("]")
print(f"\n  Total: 5 manual + {auto_added} auto-detected = "
      f"{5 + auto_added} outage events")
print("=" * 60)