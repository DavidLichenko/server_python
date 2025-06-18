import httpx
from bs4 import BeautifulSoup
from fastapi import FastAPI, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import List, Union
from pydantic import BaseModel
import yfinance as yf
import asyncio
import time

# FastAPI app setup
app = FastAPI()

# Middleware to handle CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Currency map for converting full names to abbreviations
currency_map = {
    "Euro": "EUR",
    "British Pound": "GBP",
    "Indian Rupee": "INR",
    "Australian Dollar": "AUD",
    "Canadian Dollar": "CAD",
    "Singapore Dollar": "SGD",
    "Swiss Franc": "CHF",
    "Malaysian Ringgit": "MYR",
    "Japanese Yen": "JPY",
    "Chinese Yuan Renminbi": "CNY",
    "Argentine Peso": "ARS",
    "Bahraini Dinar": "BHD",
    "Botswana Pula": "BWP",
    "Brazilian Real": "BRL",
    "Bruneian Dollar": "BND",
    "Bulgarian Lev": "BGN",
    "Chilean Peso": "CLP",
    "Colombian Peso": "COP",
    "Czech Koruna": "CZK",
    "Danish Krone": "DKK",
    "Hong Kong Dollar": "HKD",
    "Hungarian Forint": "HUF",
    "Icelandic Krona": "ISK",
    "Indonesian Rupiah": "IDR",
    "Iranian Rial": "IRR",
    "Israeli Shekel": "ILS",
    "Kazakhstani Tenge": "KZT",
    "South Korean Won": "KRW",
    "Kuwaiti Dinar": "KWD",
    "Libyan Dinar": "LYD",
    "Mauritian Rupee": "MUR",
    "Mexican Peso": "MXN",
    "Nepalese Rupee": "NPR",
    "New Zealand Dollar": "NZD",
    "Norwegian Krone": "NOK",
    "Omani Rial": "OMR",
    "Pakistani Rupee": "PKR",
    "Philippine Peso": "PHP",
    "Polish Zloty": "PLN",
    "Qatari Riyal": "QAR",
    "Romanian New Leu": "RON",
    "Russian Ruble": "RUB",
    "Saudi Arabian Riyal": "SAR",
    "South African Rand": "ZAR",
    "Sri Lankan Rupee": "LKR",
    "Swedish Krona": "SEK",
    "Taiwan New Dollar": "TWD",
    "Thai Baht": "THB",
    "Trinidadian Dollar": "TTD",
    "Turkish Lira": "TRY",
    "Emirati Dirham": "AED",
    "Venezuelan Bolivar": "VEF",
}



# URL to scrape forex data
FOREX_URL = 'https://www.x-rates.com/table/?from=USD&amount=1'

# Pydantic model for forex data response
class ForexData(BaseModel):
    pair: str
    rate: float

# Cache for forex data
forex_cache = {"data": [], "timestamp": None}

# Asynchronous function to scrape forex pairs from X-Rates
async def scrape_all_forex_data():
    async with httpx.AsyncClient() as client:
        response = await client.get(FOREX_URL)
        soup = BeautifulSoup(response.text, 'html.parser')

    rows = soup.select('table.ratesTable tr')
    forex_data = []

    for row in rows[1:]:
        columns = row.find_all('td')
        if len(columns) > 1:
            currency_full_name = columns[0].get_text().strip()
            rate = columns[1].get_text().strip()

            if currency_full_name and rate:
                currency_abbreviation = currency_map.get(currency_full_name, currency_full_name)
                forex_data.append({
                    'pair': f'USD/{currency_abbreviation}',
                    'rate': float(rate.replace(',', ''))
                })
    return forex_data

# Endpoint to get forex data
@app.get("/api/forex/", response_model=Union[List[ForexData], dict])
async def get_forex(background_tasks: BackgroundTasks):
    # Check if cached data is available and less than 10 minutes old
    current_time = time.time()
    if forex_cache["data"] and forex_cache["timestamp"] and (current_time - forex_cache["timestamp"] < 600):
        return  {"status": "success", "data": forex_cache["data"]}

    # Trigger background task to update cache
    background_tasks.add_task(update_forex_cache)

    # Return a valid dictionary response indicating the status
    return JSONResponse(
        content={"status": "fetching", "data": "Forex data is being updated. Try again shortly."},
        status_code=202
    )

# Background task to update the forex cache
async def update_forex_cache():
    forex_cache["data"] = await scrape_all_forex_data()
    forex_cache["timestamp"] = time.time()

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

    json_data = formatted_data.to_dict(orient='records')
    return json_data

# Endpoint to get historical candlestick data
@app.get("/api/stocks/{symbol}/candlesticks/")
async def get_historical_candlesticks(symbol: str, timeframe: str = "1m", duration: str = "1d"):
    data = await get_candlestick_data(symbol, timeframe, duration)
    return {"status": "success", "data": data}
