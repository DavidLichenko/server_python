import pandas as pd
import yfinance as yf
from mangum import Mangum
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from typing import List

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins, or specify a list of origins
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods
    allow_headers=["*"],  # Allow all headers
)

handler = Mangum(app)



@app.get("/")
async def main():
    return {"status":"success","data":"hello"}



# Function to fetch and format candlestick data for lightweight chart
async def get_candlestick_data(symbol: str, timeframe: str = "1m", duration: str = "1d"):
    # Fetch data
    ticker = yf.Ticker(symbol)
    historical_data = ticker.history(period="1d", interval='1m')

    # Reset the index to make 'Datetime' a column
    historical_data.reset_index(inplace=True)

    # Restructure data to match the desired JSON format
    formatted_data = historical_data.rename(columns={
        'Datetime': 'time',
        'Open': 'open',
        'High': 'high',
        'Low': 'low',
        'Close': 'close'
    })[['time', 'open', 'high', 'low', 'close']]

    # Convert to dictionary with records orientation
    json_data = formatted_data.to_dict(orient='records')

    return json_data

@app.get("/api/stocks/{symbol}/candlesticks/")
async def get_historical_candlesticks(symbol: str, timeframe: str = "1m", duration: str = "1d"):
    # Get the formatted candlestick data
    data = await get_candlestick_data(symbol, timeframe, duration)
    return {"status":"success","data":data}
