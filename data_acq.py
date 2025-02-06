import requests
import pandas as pd
import yfinance as yf
import sqlite3
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor

# API_KEY for finnhub API access
# Should be ideally stored in .env file, but putting it here for testing purpose
# (So that someone evaluating don't need to create his own API key)
API_KEY = "cuhh9a9r01qva71tpvjgcuhh9a9r01qva71tpvk0"

# Step 1: Get all US stock symbols
print("Getting all US stock symbols from finnhub:")
url = f"https://finnhub.io/api/v1/stock/symbol?exchange=US&token={API_KEY}"
response = requests.get(url)
stocks = pd.DataFrame(response.json())

# Filter only NASDAQ stocks where currency is USD 
# Remove this filter if needed, but it will take a lot of time to fetch all data
# So, for testing i would advice to keep this or modify according to your need
stocks = stocks[(stocks['mic'] == 'XNAS') & (stocks['currency'] == 'USD')]


symbols = stocks.symbol.tolist() # Extract stock symbols
print(f"Extracted all symbols. Found {len(symbols)} US stocks")

# Initialize an empty list to store the combined data
combined_data = []

# Function to fetch stock data and process it
def fetch_stock_data(symbol):
    try:
        # Fetch data for the stock
        stock = yf.Ticker(symbol)
        
        # Get shares outstanding
        shares_outstanding = stock.info.get('sharesOutstanding', None)
        
        # Skip this stock if sharesOutstanding is None
        if shares_outstanding is None:
            return None
        
        # Fetch historical data for the last 30 days (daily closing prices)
        historical_data = stock.history(period="30d")  # You can use "30d" or specify start and end dates
        historical_data['symbol'] = symbol  # Add a column for the symbol
        
        # Calculate market cap as sharesOutstanding * closing price
        historical_data['marketcap'] = historical_data['Close'] * shares_outstanding
        
        # Convert the index (Date) to just the date (remove time and timezone)
        historical_data['date'] = historical_data.index.date
        
        # Select relevant columns: Date, Symbol, Price (Closing), Market Cap
        return historical_data[['date', 'symbol', 'Close', 'marketcap']].reset_index(drop=True)
    except (requests.exceptions.HTTPError, Exception) as e:
        return None

print("Fetching price and marketcap for all extracted stocks using yfinance")
# Step 2: Fetch data concurrently for multiple stocks
# Using multiple threads is affecting ratelimiting of API
# If running for only NASDAQ (or fewer tickers), I would advice to keep max_workers as 1
with ThreadPoolExecutor(max_workers=1) as executor:
    # Use executor to fetch data for multiple symbols concurrently
    results = list(tqdm(executor.map(fetch_stock_data, symbols), total=len(symbols)))

# Filter out any None results due to errors
results = [result for result in results if result is not None]

print("Combining data for all symbols")
# Step 3: Combine data for all symbols
final_data = pd.concat(results, ignore_index=True)

# Rename columns for clarity
final_data.rename(columns={'Close': 'price', 'symbol': 'ticker'}, inplace=True)

# Step 5: Save to SQLite database
print("Connecting to SQLite DB")
conn = sqlite3.connect('stocks_data.db')

# Create a table to store the stock data
conn.execute('''
    CREATE TABLE IF NOT EXISTS stock_data (
        date TEXT,
        ticker TEXT,
        price REAL,
        marketcap REAL
    )
''')

# Insert the stock data into the stock_data table
print("Inserting data into stock_data table")
final_data.to_sql('stock_data', conn, if_exists='replace', index=False)

# Commit the transaction and close the connection
conn.commit()

# Query to check the data inserted into the table
query = "SELECT * FROM stock_data LIMIT 10;"  # Just fetching the first 10 rows for preview
result = pd.read_sql(query, conn)

# Display the result
print("First 10 rows of the data in the SQLite database:")
print(result)

# Close the connection
conn.close()