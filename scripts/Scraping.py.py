import requests
from bs4 import BeautifulSoup
import pandas as pd

companies = [
    "INFY",
    "RELIANCE",
    "ITC",
    "TCS",
    "SBI",
    "ICICI",
    "BAJAJ",
    "AIRTEL",
    "ADANI",
    "HINDUNILVR"
]

all_news = []

headers = {
    "User-Agent": "Mozilla/5.0"
}

for company in companies:

    print(f"\nCollecting {company} news...")

    url = f"https://economictimes.indiatimes.com/topic/{company}"

    try:

        response = requests.get(
            url,
            headers=headers
        )

        soup = BeautifulSoup(
            response.text,
            "html.parser"
        )

        headlines = soup.find_all("a")

        for h in headlines:

            text = h.get_text(strip=True)

            if len(text) > 30:

                all_news.append({
                    "Company": company,
                    "Headline": text
                })

        print("Collected")

    except Exception as e:

        print("Error:", e)

# dataframe
df = pd.DataFrame(all_news)

# remove duplicates
df.drop_duplicates(inplace=True)

# save
df.to_csv(
    "stock_news.csv",
    index=False,
    encoding="utf-8-sig"
)

print("\nDONE")
print(df.head())
print("Total Headlines:", len(df))