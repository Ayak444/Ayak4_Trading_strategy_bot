#主程式
from fastapi import FastAPI
import uvicorn
import os
from models import StockTarget
from data_provider import MarketDataProvider
from analyzer import TechnicalAnalyzer
from strategy import StrategyEngine
from notifier import TelegramNotifier
from keep_alive import keep_alive

app = FastAPI()
notifier = TelegramNotifier()

def get_targets():
    return [
        StockTarget("0050.TW", "元大台灣50", "ETF", 76.18, 250),
        StockTarget("00631L.TW", "正2", "ETF", 537.0, 10),
        StockTarget("2308.TW", "台達電", "STOCK", 0, 0),
        StockTarget("2368.TW", "金像電", "STOCK", 0, 0)
    ]

@app.get("/report")
def generate_report():
    targets = get_targets()
    chip_data, _ = MarketDataProvider.get_chip_data()
    market_df, fx_val, fx_note = MarketDataProvider.get_market_context()
    
    results = []
    for t in targets:
        df, obj = MarketDataProvider.get_stock_history(t.id)
        if df is None: continue
        price = MarketDataProvider.get_realtime_price(t.id)
        if price: df.iloc[-1, df.columns.get_loc('Close')] = price
        
        df = TechnicalAnalyzer.calculate_indicators(df)
        advice, sigs, score, pl = StrategyEngine.evaluate(df, t, chip_data, market_df, fx_val)
        sl, note = StrategyEngine.get_exit_point(df, t.cost)
        val = TechnicalAnalyzer.analyze_valuation(obj, df, df['Close'].iloc[-1])
        
        results.append({
            "name": t.name, "ticker": t.id, "price": float(df['Close'].iloc[-1]),
            "score": score, "advice": advice, "pl": round(pl, 2),
            "valuation": val, "signals": sigs, "exit": note, "sl": round(sl, 1)
        })
    return {"status": "success", "data": results, "fx": fx_note}

if __name__ == "__main__":
    keep_alive()
    uvicorn.run(app, host="192.168.213.90", port=8080)
