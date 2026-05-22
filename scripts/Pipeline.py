"""
╔══════════════════════════════════════════════════════════════════════╗
║     INDIAN STOCK MARKET SENTIMENT PIPELINE — FULL PIPELINE          ║
║     Companies : ADANI, BHARATIARTL, HINDUSTAN, ICICIBANK,           ║
║                 INFY, ITC, RELIANCE, SBI, TCS                       ║
║     Range     : 2023 – 2025                                         ║
║     Signals   : VADER · Language Gap · Broker Panic ·               ║
║                 Model Disagreement · Hype vs Reality                 ║
╚══════════════════════════════════════════════════════════════════════╝

HOW TO RUN:
    python pipeline.py

OUTPUT FOLDERS (auto-created):
    Dataset/output/scored/        ← sentiment scored per company
    Dataset/output/merged/        ← sentiment + price merged
    Dataset/output/signals/       ← 4 India-specific signals
    Dataset/output/summary/       ← final correlation + summary CSVs
"""

import pandas as pd
import numpy as np
import os, glob, re, warnings
warnings.filterwarnings('ignore')

# ── Auto-install missing packages ─────────────────────────────────────────────
def install(pkg):
    os.system(f"pip install {pkg} -q")

try:
    from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
except ImportError:
    install("vaderSentiment"); from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

vader = SentimentIntensityAnalyzer()

# ══════════════════════════════════════════════════════════════════════
# SECTION 0 — CONFIGURATION
# ══════════════════════════════════════════════════════════════════════
BASE        = r"C:\Users\ELCOT\Desktop\Aivar\Dataset"
RAW_DIR     = os.path.join(BASE, "raw_data")
SENT_FILE   = os.path.join(BASE, "Financial_sentiment_dataset.xlsx")
HINDI_FILE  = os.path.join(BASE, "news_with_exact_dates.csv")
OUT_BASE    = os.path.join(BASE, "output")

PATHS = {
    "scored"  : os.path.join(OUT_BASE, "scored"),
    "merged"  : os.path.join(OUT_BASE, "merged"),
    "signals" : os.path.join(OUT_BASE, "signals"),
    "summary" : os.path.join(OUT_BASE, "summary"),
}
for p in PATHS.values():
    os.makedirs(p, exist_ok=True)

# Map: keyword in filename → standard ticker label
COMPANY_MAP = {
    "ADANI"      : "ADANI",
    "BHARTIARTL" : "BHARTIARTL",
    "BHARATI"    : "BHARTIARTL",
    "HINDUSTAN"  : "HINDUSTAN",
    "HINDUNILVR" : "HINDUSTAN",
    "ICICIBANK"  : "ICICIBANK",
    "ICICI"      : "ICICIBANK",
    "INFY"       : "INFY",
    "ITC"        : "ITC",
    "RELIANCE"   : "RELIANCE",
    "SBI"        : "SBI",
    "SBIN"       : "SBI",
    "TCS"        : "TCS",
}

# Broker outage events (verified — add more if needed)
BROKER_OUTAGES = [
    {"date": "2023-11-06", "broker": "Zerodha",  "severity": 0.8},
    {"date": "2023-12-04", "broker": "Zerodha",  "severity": 0.6},
    {"date": "2024-01-13", "broker": "Groww",    "severity": 0.5},
    {"date": "2024-01-23", "broker": "Groww",    "severity": 0.8},
    {"date": "2024-11-26", "broker": "Exchange", "severity": 1.0},  # Artha Vrddhi expelled
]

# Financial keyword boosts (word-boundary safe, no short words like 'up'/'down')
POS_WORDS = ['profit','rise','gain','growth','bull','rally','surge',
             'record','strong','beat','upside','munafa','achha','robust']
NEG_WORDS = ['loss','drop','fall','crash','bear','slump','decline',
             'weak','miss','downside','ghata','nuksan','fraud','default']

def sep(title):
    print("\n" + "═"*65)
    print(f"  {title}")
    print("═"*65)

# ══════════════════════════════════════════════════════════════════════
# STEP 1 — LOAD SENTIMENT DATA
# ══════════════════════════════════════════════════════════════════════
sep("STEP 1: Loading financial sentiment data")

# ── Load main English sentiment file ─────────────────────────────────────────
if not os.path.exists(SENT_FILE):
    print(f"  ❌ File not found: {SENT_FILE}")
    print(f"  Make sure Financial_sentiment_dataset.xlsx is in: {BASE}")
    exit()

print(f"  📄 Loading: {os.path.basename(SENT_FILE)}")
sent_raw = pd.read_excel(SENT_FILE)
print(f"  ✅ Loaded: {len(sent_raw)} rows")
print(f"  Columns : {sent_raw.columns.tolist()}")

# ── Auto-detect columns ───────────────────────────────────────────────────────
def find_col(df, names):
    for n in names:
        if n in df.columns: return n
    return None

company_col  = find_col(sent_raw, ['Company','company','CompanyName','company_name'])
symbol_col   = find_col(sent_raw, ['Symbol','symbol','Ticker','ticker','Stock'])
headline_col = find_col(sent_raw, ['Headline','headline','Title','title','News','news','text'])
date_col     = find_col(sent_raw, ['Date','date','Published','published','PublishedAt','publishedAt'])
orig_sent_col= find_col(sent_raw, ['Sentiment','sentiment','Label','label'])

print(f"\n  Detected:")
print(f"    Company  → {company_col}")
print(f"    Symbol   → {symbol_col}")
print(f"    Headline → {headline_col}")
print(f"    Date     → {date_col}")
print(f"    Sentiment→ {orig_sent_col}")

if not headline_col:
    print("  ❌ Cannot find headline/text column. Check your CSV.")
    exit()

# ── Parse and clean dates ─────────────────────────────────────────────────────
sent_raw[date_col] = pd.to_datetime(sent_raw[date_col], errors='coerce')
sent_raw = sent_raw.dropna(subset=[date_col])
sent_raw[date_col] = sent_raw[date_col].dt.normalize()

# Filter to 2023–2025
sent_raw = sent_raw[
    (sent_raw[date_col] >= '2023-01-01') &
    (sent_raw[date_col] <= '2025-12-31')
].copy()

print(f"\n  Rows after date filter (2023–2025): {len(sent_raw)}")

# ── Map company/symbol to standard ticker ────────────────────────────────────
ref_col = symbol_col if symbol_col else company_col

if ref_col is None:
    print("  ❌ Cannot find Company or Symbol column in your sentiment file.")
    print(f"  Columns found: {sent_raw.columns.tolist()}")
    exit()

def standardise_ticker(val):
    if pd.isna(val):
        return 'UNKNOWN'
    val_up = str(val).upper().strip()
    for key, std in COMPANY_MAP.items():
        if key in val_up:
            return std
    return val_up

sent_raw['Ticker'] = sent_raw[ref_col].apply(standardise_ticker)
# Remove rows where ticker couldn't be identified
sent_raw = sent_raw[sent_raw['Ticker'] != 'UNKNOWN'].copy()
print(f"  Tickers found: {sorted(sent_raw['Ticker'].unique())}")
print(f"  Rows after ticker filter: {len(sent_raw)}")

# ── Load and integrate Hindi headlines ───────────────────────────────────────
if os.path.exists(HINDI_FILE):
    print(f"\n  Loading Hindi headlines: {os.path.basename(HINDI_FILE)}")
    hindi_raw = pd.read_csv(HINDI_FILE, encoding='utf-8-sig')

    # Standardise columns to match English data
    hindi_raw = hindi_raw.rename(columns={
        'Headline': headline_col if headline_col else 'Headline',
    })

    # Ensure required columns exist
    if headline_col not in hindi_raw.columns:
        hindi_raw[headline_col] = hindi_raw.get('Headline', '')

    # Parse dates — Hindi file uses DD-MM-YYYY format
    date_raw_col = 'Date' if 'Date' in hindi_raw.columns else hindi_raw.columns[1]
    hindi_raw['Date_parsed'] = pd.to_datetime(
        hindi_raw[date_raw_col], dayfirst=True, errors='coerce'
    )
    # Try without dayfirst if many failed
    failed = hindi_raw['Date_parsed'].isna().sum()
    if failed > len(hindi_raw) * 0.5:
        hindi_raw['Date_parsed'] = pd.to_datetime(
            hindi_raw[date_raw_col], dayfirst=False, errors='coerce'
        )
    hindi_raw = hindi_raw.dropna(subset=['Date_parsed'])
    hindi_raw[date_col] = hindi_raw['Date_parsed'].dt.normalize()
    hindi_raw = hindi_raw.drop(columns=['Date_parsed'], errors='ignore')
    if date_raw_col in hindi_raw.columns and date_raw_col != date_col:
        hindi_raw = hindi_raw.drop(columns=[date_raw_col], errors='ignore')

    # Filter to project range
    hindi_raw = hindi_raw[
        (hindi_raw[date_col] >= '2023-01-01') &
        (hindi_raw[date_col] <= '2025-12-31')
    ].copy()

    # Set required flags
    hindi_raw['Is_Hindi'] = 1
    hindi_raw['Language'] = 'Hindi'
    if 'Ticker' not in hindi_raw.columns:
        hindi_raw['Ticker'] = hindi_raw.get('Ticker', 'UNKNOWN')

    # Add missing columns with defaults so concat works cleanly
    for col in sent_raw.columns:
        if col not in hindi_raw.columns:
            hindi_raw[col] = np.nan

    # Keep only columns that exist in main dataframe
    hindi_raw = hindi_raw[[c for c in sent_raw.columns if c in hindi_raw.columns]]

    # Append to main sentiment dataframe
    sent_raw = pd.concat([sent_raw, hindi_raw], ignore_index=True)
    print(f"  ✅ Added {len(hindi_raw)} Hindi headlines")
    print(f"  Total headlines now: {len(sent_raw)}")
    print(f"  Hindi by ticker:")
    print(hindi_raw['Ticker'].value_counts().to_string())
else:
    print(f"  ℹ️  Hindi file not found at {HINDI_FILE} — skipping Language Gap signal")

# ══════════════════════════════════════════════════════════════════════
# STEP 2 — SCORE SENTIMENT (VADER + keyword boost)
# ══════════════════════════════════════════════════════════════════════
sep("STEP 2: Scoring sentiment with VADER")

def compute_vader_score(text):
    text = str(text).lower().strip()
    if not text or text == 'nan':
        return 0.0

    # VADER base
    score = vader.polarity_scores(text)['compound']

    # Financial keyword boost (capped at ±0.4)
    boost = 0.0
    for w in POS_WORDS:
        if re.search(rf'\b{w}\b', text): boost += 0.2
    for w in NEG_WORDS:
        if re.search(rf'\b{w}\b', text): boost -= 0.2
    boost = max(-0.4, min(0.4, boost))

    return round(max(-1.0, min(1.0, score + boost)), 4)

def score_to_label(s):
    if s >  0.05: return 'Positive'
    if s < -0.05: return 'Negative'
    return 'Neutral'

print("  Scoring all headlines...")
sent_raw['VADER_Score']  = sent_raw[headline_col].apply(compute_vader_score)
sent_raw['VADER_Label']  = sent_raw['VADER_Score'].apply(score_to_label)

# Keep original sentiment for Language Gap analysis
if orig_sent_col:
    sent_raw.rename(columns={orig_sent_col: 'Original_Sentiment'}, inplace=True)

# Detect if headline is Hindi (simple heuristic: non-ASCII characters)
def is_hindi(text):
    text = str(text)
    hindi_chars = len(re.findall(r'[\u0900-\u097F]', text))
    return 1 if hindi_chars > 2 else 0

sent_raw['Is_Hindi'] = sent_raw[headline_col].apply(is_hindi)

print(f"  ✅ Scored {len(sent_raw)} headlines")
print(f"  Hindi headlines detected : {sent_raw['Is_Hindi'].sum()}")
print(f"  Label distribution:")
print(sent_raw['VADER_Label'].value_counts().to_string())

# ── Forward-fill weekend dates to Monday ─────────────────────────────────────
def next_trading_day(d):
    if pd.isna(d): return d
    if d.weekday() == 5: return d + pd.Timedelta(days=2)
    if d.weekday() == 6: return d + pd.Timedelta(days=1)
    return d

sent_raw[date_col] = sent_raw[date_col].apply(next_trading_day)

# ── Save full scored file ─────────────────────────────────────────────────────
scored_all_path = os.path.join(PATHS["scored"], "ALL_SCORED.csv")
sent_raw.to_csv(scored_all_path, index=False)
print(f"\n  ✅ Saved: ALL_SCORED.csv")

# ── Split and save per ticker ─────────────────────────────────────────────────
ticker_dfs = {}
for ticker in sorted(sent_raw['Ticker'].unique()):
    df_t = sent_raw[sent_raw['Ticker'] == ticker].copy()
    out  = os.path.join(PATHS["scored"], f"{ticker}_scored.csv")
    df_t.to_csv(out, index=False)
    ticker_dfs[ticker] = df_t
    print(f"  ✅ {ticker:<14} {len(df_t):>4} headlines saved")

# ══════════════════════════════════════════════════════════════════════
# STEP 3 — LOAD RAW PRICE DATA
# ══════════════════════════════════════════════════════════════════════
sep("STEP 3: Loading raw price data from raw_data folder")

price_files = glob.glob(os.path.join(RAW_DIR, "FINAL_*.csv")) + \
              glob.glob(os.path.join(RAW_DIR, "FINAL_*.xlsx")) + \
              glob.glob(os.path.join(RAW_DIR, "*.csv"))

price_dfs = {}

for f in price_files:
    fname = os.path.basename(f).upper()

    # Find which ticker this file belongs to
    matched_ticker = None
    for key, std in COMPANY_MAP.items():
        if key in fname:
            matched_ticker = std
            break

    if not matched_ticker:
        print(f"  ⚠️  Skipped (no ticker match): {os.path.basename(f)}")
        continue

    try:
        df = pd.read_csv(f) if f.endswith('.csv') else pd.read_excel(f)

        # Detect date column
        date_c = find_col(df, ['Date','date','DATE','Timestamp','timestamp'])
        if not date_c:
            print(f"  ⚠️  No date column in {os.path.basename(f)}")
            continue

        df[date_c] = pd.to_datetime(df[date_c], errors='coerce')
        df = df.dropna(subset=[date_c])
        df[date_c] = df[date_c].dt.normalize()
        df = df.rename(columns={date_c: 'Date'})
        df = df.set_index('Date').sort_index()

        # Detect close column
        close_c = find_col(df, ['Close','close','CLOSE','Adj Close','adj_close'])
        if not close_c:
            close_c = df.columns[0]
        df = df.rename(columns={close_c: 'Close'})

        # Standardise volume
        vol_c = find_col(df, ['Volume','volume','VOLUME'])
        if vol_c:
            df = df.rename(columns={vol_c: 'Volume'})
        else:
            df['Volume'] = np.nan

        # Filter to 2023–2025
        df = df[(df.index >= '2023-01-01') & (df.index <= '2025-12-31')]

        # Compute returns and volatility
        df['Daily_Return_%'] = df['Close'].pct_change() * 100
        df['Volatility_5d']  = df['Daily_Return_%'].rolling(5).std()
        df['Volatility_20d'] = df['Daily_Return_%'].rolling(20).std()
        df['Volume_Avg20']   = df['Volume'].rolling(20).mean()
        df['Volume_Spike']   = (df['Volume'] > df['Volume_Avg20'] * 1.5).astype(int)

        price_dfs[matched_ticker] = df
        print(f"  ✅ {matched_ticker:<14} {len(df):>4} trading days | "
              f"{df.index.min().date()} → {df.index.max().date()}")

    except Exception as e:
        print(f"  ❌ Error loading {os.path.basename(f)}: {e}")

# ══════════════════════════════════════════════════════════════════════
# STEP 4 — WEEKLY SENTIMENT AGGREGATION
# (Weekly instead of daily because news is sparse — ~2363 headlines
#  spread across 9 stocks over 2 years = ~1-5 headlines per stock/day)
# ══════════════════════════════════════════════════════════════════════
sep("STEP 4: Aggregating weekly sentiment per ticker")

def weekly_sentiment(df_ticker, date_col):
    df_ticker = df_ticker.copy()
    df_ticker[date_col] = pd.to_datetime(df_ticker[date_col])

    # Map every date to the Monday of its week
    df_ticker['Week'] = df_ticker[date_col] - pd.to_timedelta(
        df_ticker[date_col].dt.weekday, unit='D'
    )

    df_en = df_ticker[df_ticker['Is_Hindi'] == 0]
    df_hi = df_ticker[df_ticker['Is_Hindi'] == 1]

    agg = df_ticker.groupby('Week').agg(
        Avg_VADER_Score    = ('VADER_Score', 'mean'),
        Median_VADER_Score = ('VADER_Score', 'median'),
        News_Count         = ('VADER_Score', 'count'),
        Sentiment_Std      = ('VADER_Score', 'std'),
        Hindi_Count        = ('Is_Hindi',    'sum'),
    ).reset_index()
    agg.rename(columns={'Week': 'Date'}, inplace=True)

    # English-only avg
    if not df_en.empty:
        en_avg = df_en.groupby(
            df_en[date_col] - pd.to_timedelta(df_en[date_col].dt.weekday, unit='D')
        )['VADER_Score'].mean().reset_index()
        en_avg.columns = ['Date', 'English_Avg_Score']
        agg = agg.merge(en_avg, on='Date', how='left')
    else:
        agg['English_Avg_Score'] = np.nan

    # Hindi-only avg
    if not df_hi.empty:
        hi_avg = df_hi.groupby(
            df_hi[date_col] - pd.to_timedelta(df_hi[date_col].dt.weekday, unit='D')
        )['VADER_Score'].mean().reset_index()
        hi_avg.columns = ['Date', 'Hindi_Avg_Score']
        agg = agg.merge(hi_avg, on='Date', how='left')
    else:
        agg['Hindi_Avg_Score'] = np.nan

    agg['Date'] = pd.to_datetime(agg['Date'])
    return agg

# Build daily_dfs (kept for signal compatibility) + weekly_dfs for merging
daily_dfs  = {}
weekly_dfs = {}

for ticker, df_t in ticker_dfs.items():
    # Daily (used by signals)
    df_t_copy = df_t.copy()
    df_t_copy[date_col] = pd.to_datetime(df_t_copy[date_col])
    daily_agg = df_t_copy.groupby(date_col).agg(
        Avg_VADER_Score    = ('VADER_Score', 'mean'),
        Median_VADER_Score = ('VADER_Score', 'median'),
        News_Count         = ('VADER_Score', 'count'),
        Sentiment_Std      = ('VADER_Score', 'std'),
        Hindi_Count        = ('Is_Hindi',    'sum'),
    ).reset_index()
    daily_agg.rename(columns={date_col: 'Date'}, inplace=True)
    daily_agg['English_Avg_Score'] = np.nan
    daily_agg['Hindi_Avg_Score']   = np.nan
    daily_agg['Date'] = pd.to_datetime(daily_agg['Date'])
    daily_dfs[ticker] = daily_agg

    # Weekly (used for merge)
    weekly = weekly_sentiment(df_t, date_col)
    weekly_dfs[ticker] = weekly
    print(f"  ✅ {ticker:<14} {len(weekly):>3} news weeks | {len(daily_agg):>4} news days")

# ══════════════════════════════════════════════════════════════════════
# STEP 5 — MERGE WEEKLY SENTIMENT + PRICE
# ══════════════════════════════════════════════════════════════════════
sep("STEP 5: Merging weekly sentiment with price data")

merged_dfs = {}

for ticker in sorted(set(weekly_dfs.keys()) & set(price_dfs.keys())):
    weekly = weekly_dfs[ticker].copy()

    # Map price data to week (Monday)
    price = price_dfs[ticker].reset_index().copy()
    price['Date'] = pd.to_datetime(price['Date'])
    price['Week'] = price['Date'] - pd.to_timedelta(price['Date'].dt.weekday, unit='D')

    # Aggregate price by week
    weekly_price = price.groupby('Week').agg(
        Close          = ('Close',          'last'),
        Weekly_Return  = ('Daily_Return_%', 'sum'),
        Volume         = ('Volume',         'sum'),
        Volume_Avg20   = ('Volume_Avg20',   'mean'),
        Volume_Spike   = ('Volume_Spike',   'max'),
        Volatility_5d  = ('Volatility_5d',  'mean'),
        Volatility_20d = ('Volatility_20d', 'mean'),
    ).reset_index()
    weekly_price.rename(columns={'Week': 'Date', 'Weekly_Return': 'Daily_Return_%'}, inplace=True)
    weekly_price['Date'] = pd.to_datetime(weekly_price['Date'])

    # Merge on week
    merged = pd.merge(weekly_price, weekly, on='Date', how='left')
    merged = merged.sort_values('Date').reset_index(drop=True)
    merged['Ticker'] = ticker

    # Forward fill up to 2 weeks for sparse news gaps
    for col in ['Avg_VADER_Score','English_Avg_Score','Hindi_Avg_Score','News_Count']:
        if col in merged.columns:
            merged[col] = merged[col].ffill(limit=2)

    # Lag/lead features (now weekly shifts)
    merged['Sentiment_Yesterday'] = merged['Avg_VADER_Score'].shift(1)  # prev week sentiment
    merged['Return_Tomorrow']     = merged['Daily_Return_%'].shift(-1)  # next week return
    merged['Return_Day_After']    = merged['Daily_Return_%'].shift(-2)  # 2 weeks ahead
    merged['Return_Yesterday']    = merged['Daily_Return_%'].shift(1)   # prev week return

    # Check coverage
    filled   = merged['Avg_VADER_Score'].notna().sum()
    total    = len(merged)
    missing  = (total - filled) / total * 100
    print(f"  ✅ {ticker:<14} {total:>3} weeks | sentiment coverage: {100-missing:.1f}%")

    out = os.path.join(PATHS["merged"], f"{ticker}_merged.csv")
    merged.to_csv(out, index=False)
    merged_dfs[ticker] = merged

if not merged_dfs:
    print("\n  ❌ No merged data.")
    print(f"     Sentiment tickers : {sorted(weekly_dfs.keys())}")
    print(f"     Price tickers     : {sorted(price_dfs.keys())}")

# ══════════════════════════════════════════════════════════════════════
# STEP 6 — FOUR INDIA-SPECIFIC SIGNALS
# ══════════════════════════════════════════════════════════════════════
sep("STEP 6: Computing 4 India-specific signals")

outage_dates = pd.to_datetime([o['date'] for o in BROKER_OUTAGES])
outage_severity = {
    pd.Timestamp(o['date']): o['severity'] for o in BROKER_OUTAGES
}

signal_dfs = {}

for ticker, df in merged_dfs.items():
    sig = df[['Date','Ticker','Close','Daily_Return_%',
              'Avg_VADER_Score','News_Count',
              'English_Avg_Score','Hindi_Avg_Score',
              'Volume','Volume_Spike']].copy()

    # ── Signal 1: Language Gap ────────────────────────────────────────
    # Hindi score minus English score per day
    # Positive = Hindi more optimistic than English (retail vs institutional gap)
    sig['Language_Gap'] = sig['Hindi_Avg_Score'] - sig['English_Avg_Score']
    sig['Language_Gap_Abs'] = sig['Language_Gap'].abs()

    # ── Signal 2: Broker Outage Panic Metric ─────────────────────────
    # 1.0 on outage day, decays over 2 following days
    def broker_panic(date):
        for od in outage_dates:
            delta = (date - od).days
            if delta == 0: return outage_severity.get(od, 0.8)
            if delta == 1: return outage_severity.get(od, 0.8) * 0.5
            if delta == 2: return outage_severity.get(od, 0.8) * 0.2
        return 0.0

    sig['Broker_Panic_Score'] = sig['Date'].apply(broker_panic)
    sig['Is_Outage_Day'] = (sig['Broker_Panic_Score'] > 0).astype(int)

    # ── Signal 3: Model Disagreement Score ───────────────────────────
    # |VADER - FinBERT| → here we approximate using score std across headlines
    # (Replace with actual FinBERT scores when available)
    sig['Model_Disagreement'] = sig['Avg_VADER_Score'].rolling(3).std().fillna(0)
    sig['High_Disagreement']  = (sig['Model_Disagreement'] > 0.3).astype(int)

    # ── Signal 4: Hype vs Reality ─────────────────────────────────────
    # High positive sentiment + high volume + negative/flat price return
    # = potential bull trap or pump-and-dump signal
    sentiment_thresh = 0.2
    volume_thresh    = 1.3  # volume 30% above average

    if 'Volume_Avg20' in df.columns:
        merged_with_vol = df[['Date','Volume','Volume_Avg20','Daily_Return_%']].copy()
        sig = sig.merge(merged_with_vol[['Date','Volume_Avg20']], on='Date', how='left')
        high_sentiment   = sig['Avg_VADER_Score'] > sentiment_thresh
        high_volume      = sig['Volume'] > (sig['Volume_Avg20'] * volume_thresh)
        negative_return  = sig['Daily_Return_%'] <= 0

        sig['Hype_vs_Reality'] = (
            high_sentiment & high_volume & negative_return
        ).astype(int)

        # Divergence score: how much sentiment and return disagree
        sig['Hype_Divergence_Score'] = np.where(
            sig['Avg_VADER_Score'].notna() & sig['Daily_Return_%'].notna(),
            (sig['Avg_VADER_Score'] - sig['Daily_Return_%'].clip(-1,1)).round(4),
            np.nan
        )
        sig.drop(columns=['Volume_Avg20'], inplace=True, errors='ignore')
    else:
        sig['Hype_vs_Reality']       = 0
        sig['Hype_Divergence_Score'] = np.nan

    out = os.path.join(PATHS["signals"], f"{ticker}_signals.csv")
    sig.to_csv(out, index=False)
    signal_dfs[ticker] = sig
    print(f"  ✅ {ticker:<14} signals computed")

# ══════════════════════════════════════════════════════════════════════
# STEP 7 — CORRELATION ANALYSIS
# ══════════════════════════════════════════════════════════════════════
sep("STEP 7: Correlation analysis — leading vs lagging")

results = []

for ticker, df in merged_dfs.items():
    df = df.dropna(subset=['Avg_VADER_Score','Daily_Return_%'])
    if len(df) < 15:
        print(f"  ⚠️  {ticker}: too few rows ({len(df)}), skipping")
        continue

    def safe_corr(a, b):
        mask = a.notna() & b.notna()
        if mask.sum() < 5: return np.nan
        return round(a[mask].corr(b[mask]), 4)

    c_same  = safe_corr(df['Avg_VADER_Score'], df['Daily_Return_%'])
    c_lead1 = safe_corr(df['Avg_VADER_Score'], df['Return_Tomorrow'])
    c_lead2 = safe_corr(df['Avg_VADER_Score'], df['Return_Day_After'])
    c_lag1  = safe_corr(df['Sentiment_Yesterday'], df['Daily_Return_%'])

    best = max(
        {'Same-day': abs(c_same or 0), 'Lead+1d': abs(c_lead1 or 0),
         'Lead+2d': abs(c_lead2 or 0), 'Lag-1d': abs(c_lag1 or 0)},
        key=lambda k: {'Same-day': abs(c_same or 0),
                       'Lead+1d': abs(c_lead1 or 0),
                       'Lead+2d': abs(c_lead2 or 0),
                       'Lag-1d': abs(c_lag1 or 0)}[k]
    )

    # Signal stats
    sig = signal_dfs.get(ticker, pd.DataFrame())
    outage_days    = int(sig['Is_Outage_Day'].sum()) if 'Is_Outage_Day' in sig else 0
    hype_days      = int(sig['Hype_vs_Reality'].sum()) if 'Hype_vs_Reality' in sig else 0
    high_disag     = int(sig['High_Disagreement'].sum()) if 'High_Disagreement' in sig else 0
    lang_gap_mean  = round(sig['Language_Gap'].mean(), 4) if 'Language_Gap' in sig and sig['Language_Gap'].notna().any() else np.nan

    results.append({
        'Ticker'             : ticker,
        'Matched_Days'       : len(df),
        'Total_Headlines'    : int(df['News_Count'].sum() if 'News_Count' in df else 0),
        'Avg_Sentiment'      : round(df['Avg_VADER_Score'].mean(), 4),
        'Avg_Return_%'       : round(df['Daily_Return_%'].mean(), 4),
        'Corr_Same_Day'      : c_same,
        'Corr_Lead_1Day'     : c_lead1,
        'Corr_Lead_2Day'     : c_lead2,
        'Corr_Lag_1Day'      : c_lag1,
        'Best_Indicator'     : best,
        'Language_Gap_Mean'  : lang_gap_mean,
        'Broker_Outage_Days' : outage_days,
        'Hype_Trap_Days'     : hype_days,
        'High_Disagreement_Days': high_disag,
    })

    print(f"\n  {ticker}")
    print(f"    Matched days    : {len(df)}")
    print(f"    Avg sentiment   : {df['Avg_VADER_Score'].mean():+.4f}")
    print(f"    Avg return      : {df['Daily_Return_%'].mean():+.4f}%")
    print(f"    Corr same-day   : {c_same:+.4f}")
    print(f"    Corr lead +1d   : {c_lead1:+.4f}  ← sentiment predicts tomorrow?")
    print(f"    Corr lead +2d   : {c_lead2:+.4f}")
    print(f"    Corr lag  -1d   : {c_lag1:+.4f}  ← price drives sentiment?")
    print(f"    Best fit        : {best}")
    print(f"    Hype trap days  : {hype_days}")
    print(f"    Outage days     : {outage_days}")

# ══════════════════════════════════════════════════════════════════════
# STEP 8 — SAVE FINAL SUMMARY FILES
# ══════════════════════════════════════════════════════════════════════
sep("STEP 8: Saving summary files")

if results:
    res_df = pd.DataFrame(results)
    corr_path = os.path.join(PATHS["summary"], "CORRELATION_SUMMARY.csv")
    res_df.to_csv(corr_path, index=False)
    print("\n  CORRELATION SUMMARY:")
    print(res_df[['Ticker','Corr_Same_Day','Corr_Lead_1Day',
                  'Corr_Lag_1Day','Best_Indicator','Hype_Trap_Days']].to_string(index=False))
    print(f"\n  ✅ Saved: CORRELATION_SUMMARY.csv")

# Label distribution per ticker
label_rows = []
for ticker, df_t in ticker_dfs.items():
    counts = df_t['VADER_Label'].value_counts()
    total  = len(df_t)
    label_rows.append({
        'Ticker'    : ticker,
        'Total'     : total,
        'Positive'  : counts.get('Positive', 0),
        'Neutral'   : counts.get('Neutral',  0),
        'Negative'  : counts.get('Negative', 0),
        'Pos_%'     : round(counts.get('Positive', 0)/total*100, 1),
        'Neg_%'     : round(counts.get('Negative', 0)/total*100, 1),
        'Mean_Score': round(df_t['VADER_Score'].mean(), 4),
    })

lbl_df = pd.DataFrame(label_rows)
lbl_path = os.path.join(PATHS["summary"], "LABEL_DISTRIBUTION.csv")
lbl_df.to_csv(lbl_path, index=False)
print(f"\n  LABEL DISTRIBUTION:")
print(lbl_df.to_string(index=False))
print(f"\n  ✅ Saved: LABEL_DISTRIBUTION.csv")

# ══════════════════════════════════════════════════════════════════════
# DONE
# ══════════════════════════════════════════════════════════════════════
sep("ALL STEPS COMPLETE")
print(f"""
  Output structure:
  Dataset/output/
  ├── scored/
  │   ├── ALL_SCORED.csv              ← all headlines with VADER scores
  │   ├── ADANI_scored.csv
  │   └── ... (one per company)
  ├── merged/
  │   ├── ADANI_merged.csv            ← sentiment + price per day
  │   └── ... (one per company)
  ├── signals/
  │   ├── ADANI_signals.csv           ← 4 India-specific signals
  │   └── ... (one per company)
  └── summary/
      ├── CORRELATION_SUMMARY.csv     ← main research output
      └── LABEL_DISTRIBUTION.csv      ← sentiment breakdown

  Next step → Streamlit dashboard using merged/ and signals/ files
""")
