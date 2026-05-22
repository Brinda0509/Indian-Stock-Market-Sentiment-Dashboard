import feedparser
import pandas as pd
from datetime import datetime

queries = [
    "Zerodha+down",
    "Zerodha+outage",
    "Groww+down",
    "Groww+outage",
    "AngelOne+down",
    "Upstox+outage",
    "NSE+trading+halt",
]

results = []

for query in queries:
    url = f"https://news.google.com/rss/search?q={query}+when:2y&hl=en-IN&gl=IN&ceid=IN:en"
    feed = feedparser.parse(url)

    for entry in feed.entries:
        results.append({
            'Query'    : query.replace('+', ' '),
            'Date'     : entry.get('published', '')[:10],
            'Headline' : entry.get('title', ''),
            'Source'   : entry.get('source', {}).get('title', ''),
            'URL'      : entry.get('link', ''),
        })
    print(f"✅ '{query}' → {len(feed.entries)} articles")

if results:
    df = pd.DataFrame(results).drop_duplicates(subset=['Headline'])
    df = df.sort_values('Date')
    df.to_excel("broker_outage_news.xlsx", index=False)
    print(f"\n✅ Saved {len(df)} articles → broker_outage_news.xlsx")
else:
    print("❌ No results found")