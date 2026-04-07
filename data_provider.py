#負責所有與外界（Yahoo Finance、證交所）的數據對接

import yfinance as yf
import requests
import time
from datetime import datetime, timedelta

class MarketDataProvider:
    @staticmethod
    def is_market_open():
        now = datetime.now()
        if now.weekday() >= 5:
            return False
        start = now.replace(hour=9, minute=0, second=0)
        end = now.replace(hour=13, minute=30, second=0)
        return start <= now <= end

    @staticmethod
    def get_realtime_price(ticker):
        try:
            stock_id = ticker.split('.')[0]
            type_key = f"otc_{stock_id}.tw" if 'TWO' in ticker else f"tse_{stock_id}.tw"
            t = int(time.time() * 1000)
            url = f"https://mis.twse.com.tw/stock/api/getStockInfo.jsp?ex_ch={type_key}&json=1&delay=0&_={t}"
            res = requests.get(url, timeout=5)
            data = res.json()
            if 'msgArray' in data and len(data['msgArray']) > 0:
                info = data['msgArray'][0]
                price = info.get('z', '-')
                if price == '-':
                    price = info.get('b', '-').split('_')[0]
                return float(price) if price != '-' and price != '' else None
        except:
            return None

    @staticmethod
    def get_chip_data():
        date_obj = datetime.now()
        if date_obj.hour < 15:
            date_obj -= timedelta(days=1)
        for _ in range(3):
            date_str = date_obj.strftime('%Y%m%d')
            url = f"https://www.twse.com.tw/rwd/zh/fund/T86?date={date_str}&selectType=ALL&response=json"
            try:
                res = requests.get(url, timeout=10)
                data = res.json()
                if data['stat'] == 'OK':
                    return {row[0]: {"Foreign": int(row[4].replace(',', '')), "Trust": int(row[10].replace(',', ''))} for row in data['data']}, date_str
                date_obj -= timedelta(days=1)
                time.sleep(1)
            except:
                date_obj -= timedelta(days=1)
        return {}, "無資料"

    @staticmethod
    def get_market_context():
        try:
            market = yf.Ticker("^TWII").history(period="5d")
            fx = yf.Ticker("TWD=X").history(period="1mo")
            fx_val = 0
            fx_note = ""
            if not fx.empty:
                curr, ma10 = fx['Close'].iloc[-1], fx['Close'].tail(10).mean()
                if curr > ma10 * 1.002: fx_val, fx_note = 1, f"貶值 ({curr:.2f})"
                elif curr < ma10 * 0.998: fx_val, fx_note = -1, f"升值 ({curr:.2f})"
            return market, fx_val, fx_note
        except:
            return None, 0, ""

    @staticmethod
    def get_stock_history(ticker):
        try:
            stock = yf.Ticker(ticker)
            df = stock.history(period="1y")
            return df, stock if not df.empty else (None, None)
        except:
            return None, None