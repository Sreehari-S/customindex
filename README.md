# customindex
Project to create a custom index from top 100 US stocks

## Description

This is a simple project to source data from public Fin APIs for US stocks, build a database, create a custom index for top 100 stocks and visualize its performance for past 30 days

## Installation and Usage

1.  Clone the repository and cd to it:

    ```
    git clone https://github.com/Sreehari-S/customindex
    cd customindex
    ```
2. Create a venv and activate it
    ```
    python3 -m venv venv
    source venv/bin/activate
    ```
    
3.  Install dependencies:

    ```
    pip3 install -r requirements.txt
    ```
4. Sourcing stock data from yFinance/finnhub

   The downloaded data is already saved to SQLite database `stocks_data.db`. If you want to repeat this step, clear this file and run:
    ```
    python3 data_acq.py
    ```
     
Other wise you can skip this step.

5. Compute index
    ```
    python3 compute_index.py
    
    ```
6. Visualize in streamlit.
    ```
    streamlit run dashboard.py
    
    ```
   
   
   




