# Indian Stock Market Sentiment Dashboard
---
## Overview

This project studies how sentiment relates to stock price movement for Indian stocks.  
It compares weekly close prices with sentiment signals and highlights important market events such as broker outage panic, language gap, hype vs reality, and model disagreement.

The dashboard helps answer:

- Does sentiment lead stock price or lag behind it?
- How do Indian retail and English sentiment differ?
- Which stocks show the strongest sentiment-price relationship?
- Which market events create panic or disagreement?
---
## Features

- Interactive company selector.
- Date range filtering.
- Weekly close price vs sentiment visualization.
- Broker outage panic analysis.
- Correlation heatmap across stocks.
- Stock-wise findings panel.
- Optional support for India-specific signals:
  - Broker Outage Panic
  - Hindi vs English Sentiment
  - Language Gap
  - Hype vs Reality
  - VADER vs FinBERT disagreement
---
## Tech Stack

- Python
- Streamlit
- Pandas
- NumPy
- Plotly
---
## Project Structure

```bash
Indian-Stock-Market-Sentiment-Dashboard/
│
├── final.py
├── requirements.txt
├── README.md
│
├── output/
│   ├── merged/
│   ├── signals/
│   ├── summary/
│
├── scripts/
│   ├── preprocessing.py
│   ├── sentiment_analysis.py
│   ├── pipeline.py
│
├── assets/
│   ├── dashboard.png
```

---
## Data Files

The dashboard expects CSV files in the following folders:

- `output/merged/`
- `output/signals/`
- `output/summary/`
- `output/scored/`

### Important files
- `*_merged.csv` — merged weekly stock data.
- `*_signals.csv` — India-specific signal data.
- `CORRELATION_SUMMARY.csv` — correlation analysis results.
- `FINBERT_SCORED.csv` — optional FinBERT output.
- `ALL_SCORED.csv` — optional scored dataset.
---
## How to Run

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Run the dashboard
```bash
python -m streamlit run dashboard.py
```

---
## Dashboard Sections

### KPI Cards
Shows quick summary metrics like:
- Average sentiment
- Weekly return
- Total headlines
- Best indicator

### Sentiment vs Price
- Shows how stock close price moves with sentiment over time.

### Broker Outage Panic
- Highlights major Indian broker outage events and market panic behavior.

### Correlation Heatmap
- Summarizes how sentiment relates to returns across stocks and time windows.

### Findings per Stock
- Gives a short interpretation for each stock based on the correlation results.
---
## Why Weekly Analysis?

- Weekly aggregation reduces daily noise and gives a clearer view of sentiment-price relationships.  
It also makes lead-lag analysis more reliable.
---
## India-Specific Part

This project is focused on the Indian market, so it includes signals that are especially relevant to India:

- Broker outages across major Indian platforms.
- Hindi vs English sentiment differences.
- Language gap between retail and English sentiment.
- Hype vs reality in stock discussions.
- Sentiment model disagreement.
---
## Notes

- This is a **historical analytics dashboard**, not a fully real-time system.
- It can be extended later with live APIs for near-real-time updates.
- Make sure all required CSV files are placed in the correct folders before running the app.
---
## Example Insight

- For a stock like Reliance, the dashboard can show how sentiment moved over time, where broker outage panic appeared, and whether sentiment led or lagged price movement.
---
## License

For academic and portfolio use only.
