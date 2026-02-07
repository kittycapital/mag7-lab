#!/usr/bin/env python3
"""
Fetch daily price history for Magnificent 7 stocks.
Outputs data.js in the same format as the strategy-lab.
Run: python fetch_mag7.py
"""

import json
import datetime
import urllib.request
import urllib.error
import time
import sys

TICKERS = {
    'AAPL': 'AAPL',
    'MSFT': 'MSFT',
    'NVDA': 'NVDA',
    'GOOGL': 'GOOGL',
    'AMZN': 'AMZN',
    'META': 'META',
    'TSLA': 'TSLA',
}

# Fetch from 2000-01-01 (or IPO date, whichever is later)
START_DATE = '2000-01-01'


def fetch_yahoo(ticker, start_date, end_date):
    """Fetch daily close prices from Yahoo Finance v8 API."""
    start_ts = int(datetime.datetime.strptime(start_date, '%Y-%m-%d').timestamp())
    end_ts = int(datetime.datetime.strptime(end_date, '%Y-%m-%d').timestamp())

    url = (
        f'https://query1.finance.yahoo.com/v8/finance/chart/{ticker}'
        f'?period1={start_ts}&period2={end_ts}&interval=1d'
        f'&includePrePost=false&events=div%7Csplit'
    )

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }

    req = urllib.request.Request(url, headers=headers)

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode())
    except Exception as e:
        print(f'  ❌ Error fetching {ticker}: {e}', file=sys.stderr)
        return None, None

    try:
        result = data['chart']['result'][0]
        timestamps = result['timestamp']
        closes = result['indicators']['adjclose'][0]['adjclose']

        dates = []
        prices = []
        for ts, close in zip(timestamps, closes):
            if close is None:
                continue
            dt = datetime.datetime.utcfromtimestamp(ts)
            dates.append(dt.strftime('%Y-%m-%d'))
            prices.append(round(close, 2))

        return dates, prices

    except (KeyError, IndexError, TypeError) as e:
        print(f'  ❌ Error parsing {ticker}: {e}', file=sys.stderr)
        return None, None


def main():
    end_date = datetime.datetime.now().strftime('%Y-%m-%d')
    asset_data = {}

    for key, yahoo_ticker in TICKERS.items():
        print(f'  📥 Fetching {key} ({yahoo_ticker})...')
        dates, prices = fetch_yahoo(yahoo_ticker, START_DATE, end_date)

        if dates and prices and len(dates) > 100:
            asset_data[key] = {'dates': dates, 'prices': prices}
            print(f'     ✅ {len(dates)} days ({dates[0]} ~ {dates[-1]})')
        else:
            print(f'     ❌ Failed or insufficient data for {key}')

        time.sleep(1)  # Rate limit

    if not asset_data:
        print('❌ No data fetched!', file=sys.stderr)
        sys.exit(1)

    # Write data.js
    js = 'var ASSET_DATA = ' + json.dumps(asset_data, separators=(',', ':')) + ';\n'

    with open('data.js', 'w') as f:
        f.write(js)

    size_kb = len(js) / 1024
    print(f'\n✅ data.js written ({size_kb:.0f} KB)')
    print(f'   Assets: {", ".join(asset_data.keys())}')
    for key in asset_data:
        d = asset_data[key]
        print(f'   {key}: {len(d["dates"])} days ({d["dates"][0]} ~ {d["dates"][-1]})')


if __name__ == '__main__':
    main()
