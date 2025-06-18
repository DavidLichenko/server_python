import pandas as pd
import yfinance as yf
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def main():
    return {"status": "success", "data": "hello"}

# Function to fetch and format candlestick data
async def get_candlestick_data(symbol: str, timeframe: str = "1m", duration: str = "1d"):
    ticker = yf.Ticker(symbol)
    historical_data = ticker.history(period=duration, interval=timeframe)
    historical_data.reset_index(inplace=True)

    formatted_data = historical_data.rename(columns={
        'Datetime': 'time',
        'Open': 'open',
        'High': 'high',
        'Low': 'low',
        'Close': 'close'
    })[['time', 'open', 'high', 'low', 'close']]

    return formatted_data.to_dict(orient='records')

@app.get("/api/stocks/{symbol}/candlesticks/")
async def get_historical_candlesticks(symbol: str, timeframe: str = "1m", duration: str = "1d"):
    data = await get_candlestick_data(symbol, timeframe, duration)
    return {"status": "success", "data": data}
