import sqlite3
import pandas as pd

# Connect to SQLite database
conn = sqlite3.connect("stocks_data.db")

# Fetch unique dates from database
dates_query = "SELECT DISTINCT date FROM stock_data ORDER BY date"
dates = pd.read_sql(dates_query, conn)['date'].tolist()

# List to store index values
index_history = []
composition_records = []  # To store index composition data
comp_changes = 0 # To store number of composition changes till date

# Let's assume base value (index value on day 0) to be 1000
base_index = 1000

# Dictionary to track base_price of each stock
base_prices = {}

# Track previous index composition and index
previous_top_100, prev_index = set(), base_index

# Loop through each trading day
for i, date in enumerate(dates):
    # Fetch top 100 stocks by market cap for the given date
    query = f"""
        SELECT ticker, price, marketcap 
        FROM stock_data 
        WHERE date = '{date}'
        ORDER BY marketcap DESC
        LIMIT 100
    """
    df = pd.read_sql(query, conn)

    # Skip if less than 100 stocks are available,  just to be safe
    if len(df) < 100:
        print(f'Less than 100 stocks are available on date:{date}')
        continue

    # Track current day's top 100 stocks
    current_top_100 = set(df["ticker"])

    # Identify changes in index composition
    removed_stocks = previous_top_100 - current_top_100  # Stocks removed
    added_stocks = current_top_100 - previous_top_100  # New stocks added
    comp_changes+=len(removed_stocks)>0 # Tracking number of composition changes

    previous_top_100 = current_top_100 #Update previous_top_100 as current_top_100

    #Stocks which got added in the date
    added_df = df[df['ticker'].isin(added_stocks)]

    for _, row in added_df.iterrows():
        if row['ticker'] not in base_prices:
            base_prices[row['ticker']] = row['price'] #base_prices is the price of each ticker the first time it appears in top 100

    print(f"Date: {date} | Removed: {len(removed_stocks)} | Added: {len(added_stocks)}")

    
    df["refprice"] =   df['ticker'].map(base_prices)

    # Compute the index value: sum of (weight * price)
    # Assign equal notional weight to each stock
    df["contribution"] = 0.01 * df["price"]/df["refprice"]
    index_value = base_index*df["contribution"].sum()

    daily_pct_change = 100*(index_value - prev_index)/prev_index
    prev_index = index_value

    # Store index value for tracking
    index_history.append({"date": date, "index_value": index_value, "daily_pct_change":daily_pct_change, "cumreturns": 100*(index_value/base_index -1), "ncompchanges":comp_changes})

    # Store index composition data
    for _, row in df.iterrows():
        composition_records.append({"date": date, "ticker": row["ticker"], "weight": 1/100, "marketcap": row["marketcap"]})

# Convert index history to DataFrame
index_df = pd.DataFrame(index_history)

# Convert composition records to DataFrame
composition_df = pd.DataFrame(composition_records)

# Store index values in SQLite database
index_df.to_sql("custom_index", conn, if_exists="replace", index=False)

# Store index composition in SQLite database
composition_df.to_sql("index_composition", conn, if_exists="replace", index=False)

# Close database connection
conn.close()

print("Index values and composition stored successfully.")