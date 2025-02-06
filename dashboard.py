import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
import matplotlib.pyplot as plt
from io import BytesIO


# Convert to human-readable format (B for Billion, T for Trillion)
def format_market_cap(value):
    if value >= 1e12:  # Trillion
        return f"{value / 1e12:.2f}T"
    elif value >= 1e9:  # Billion
        return f"{value / 1e9:.2f}B"
    else:
        return f"{value:.2f}"  # Keep as is for smaller numbers
    
# Connect to SQLite database
conn = sqlite3.connect("stocks_data.db")

# Load index performance data
index_df = pd.read_sql("SELECT * FROM custom_index ORDER BY date", conn)

# Load index composition data
composition_df = pd.read_sql("SELECT * FROM index_composition ORDER BY date", conn)

conn.close()

# Filter available dates
available_dates = index_df["date"].unique()

# Streamlit UI
st.title("📊 Custom Stock Index Dashboard")
st.sidebar.header("Filter Options")

# Select Date
selected_date = st.sidebar.selectbox("Select a date", available_dates, index=len(available_dates) - 1)

# Interactive Performance Chart
st.subheader("📈 Index Performance Over the Past Month")
fig = px.line(index_df, x="date", y="index_value", title="Index Performance", markers=True)
index_df['Changedcomp'] = index_df['ncompchanges'].ne(index_df['ncompchanges'].shift()).astype(bool)
index_df.loc[0,'Changedcomp']=False
changed_days = index_df[index_df['Changedcomp']==True]
fig.add_scatter(x=changed_days["date"], y=changed_days["index_value"], mode="markers", marker=dict(color='red', size=8), name="Composition Changed")
st.plotly_chart(fig, use_container_width=True)

# Interactive Index Composition Table
st.subheader(f"📊 Index Composition on {selected_date}")
composition_df['Marketcap'] = composition_df['marketcap'].apply(format_market_cap)
composition_today = composition_df[composition_df["date"] == str(selected_date)][['ticker','weight','Marketcap']].reset_index(drop=True)
st.dataframe(composition_today,hide_index=True)

# Summary Metrics
st.subheader("📊 Summary Metrics")
cumulative_return = index_df[index_df["date"] == str(selected_date)]["cumreturns"]
daily_pct_change = index_df[index_df["date"] == str(selected_date)]["daily_pct_change"]
ncompchanges = index_df[index_df["date"] == str(selected_date)]["ncompchanges"]
st.metric(label="Cumulative Return (%)", value=round(cumulative_return, 2))
st.metric(label="Daily Percentage Change (%)", value=round(daily_pct_change, 2))
st.metric(label="Number of Compisition Changes till date", value=ncompchanges)

# Add interactivity with filters
st.sidebar.subheader("Filters")
ticker = st.sidebar.selectbox("Select a stock ticker", composition_df["ticker"].unique())
filtered_data = composition_df[composition_df["ticker"] == ticker]
st.subheader(f"📌 Performance of {ticker}")
fig2 = px.line(filtered_data, x="date", y="marketcap", title=f"Market Cap Trend of {ticker}", markers=True)
st.plotly_chart(fig2, use_container_width=True)

# Function to export chart as PDF
def export_chart_as_pdf():
    buffer = BytesIO()
    fig, ax = plt.subplots()
    ax.plot(index_df["date"], index_df["index_value"], marker="o", label="Index Value")
    ax.scatter(changed_days["date"], changed_days["index_value"], color='red', label='Composition Change', s=100)
    ax.set_title("Index Performance")
    ax.legend()
    plt.xticks(rotation=45)
    plt.savefig(buffer, format="pdf")
    buffer.seek(0)
    return buffer

# Function to export index composition table as Excel
def export_table_as_excel(mode):
    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
        if mode=='Composition':
            composition_today.to_excel(writer, sheet_name="Index Composition", index=False)
        else:
            index_df.to_excel(writer, sheet_name="Index Performance", index=False)
    buffer.seek(0)
    return buffer

# Buttons to download files
st.sidebar.subheader("Download Options")
if st.sidebar.button("Download Charts as PDF"):
    pdf_buffer = export_chart_as_pdf()
    st.sidebar.download_button(label="Download Index Performance", data=pdf_buffer, file_name="index_performance.pdf", mime="application/pdf")

if st.sidebar.button("Download Table as Excel"):
    excel_buffer = export_table_as_excel('Composition')
    st.sidebar.download_button(label="Download Composition", data=excel_buffer, file_name="index_composition.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    excel_buffer = export_table_as_excel('Index')
    st.sidebar.download_button(label="Download Index Performace", data=excel_buffer, file_name="index_performance.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

