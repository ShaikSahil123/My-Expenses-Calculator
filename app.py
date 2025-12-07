import streamlit as st
import pandas as pd
import plotly.express as px
import os
from datetime import datetime

# --- CONFIGURATION ---
FILE_PATH = 'my_expenses.xlsx'

# --- 1. LOAD DATA FUNCTION ---
# This checks if the excel file exists. If not, it creates a new one.
def load_data():
    if not os.path.exists(FILE_PATH):
        # Create a blank dataframe with columns
        df = pd.DataFrame(columns=["Date", "Type", "Category", "Amount", "Notes"])
        df.to_excel(FILE_PATH, index=False)
    
    return pd.read_excel(FILE_PATH)

# --- 2. SAVE DATA FUNCTION ---
def save_data(date, trans_type, category, amount, notes):
    df = load_data()
    new_data = pd.DataFrame({
        "Date": [date],
        "Type": [trans_type],
        "Category": [category],
        "Amount": [amount],
        "Notes": [notes]
    })
    # Combine old data with new data
    df = pd.concat([df, new_data], ignore_index=True)
    df.to_excel(FILE_PATH, index=False)

# --- 3. THE WEB INTERFACE (FRONTEND) ---
st.set_page_config(page_title="Personal Finance Manager", layout="wide")
st.title("💰 Personal Finance Manager")

# Sidebar for adding data
st.sidebar.header("Add New Entry")

# Dynamic Inputs
entry_date = st.sidebar.date_input("Date", datetime.today())
trans_type = st.sidebar.selectbox("Type", ["Expense", "Income", "Debt Given", "Debt Repaid"])

# Logic for "Flexible Fields" based on type
if trans_type == "Expense":
    category = st.sidebar.text_input("Category (e.g., Food, Rent)")
elif trans_type == "Income":
    category = st.sidebar.text_input("Source (e.g., Salary, Freelance)")
else:
    category = st.sidebar.text_input("Person Name (e.g., John, Alice)")

amount = st.sidebar.number_input("Amount", min_value=0.0, format="%.2f")
notes = st.sidebar.text_area("Notes (Optional)")

if st.sidebar.button("Add Entry"):
    save_data(entry_date, trans_type, category, amount, notes)
    st.sidebar.success("Added Successfully!")

# --- 4. DASHBOARD & ANALYSIS ---
# Load the data to display
df = load_data()

# Calculate Summary
if not df.empty:
    # Logic: Income + Debt Repaid = Money In. Expense + Debt Given = Money Out.
    money_in = df[df["Type"].isin(["Income", "Debt Repaid"])]["Amount"].sum()
    money_out = df[df["Type"].isin(["Expense", "Debt Given"])]["Amount"].sum()
    balance = money_in - money_out
    
    # Display Scorecards
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Income", f"${money_in:,.2f}")
    col2.metric("Total Spend/Lent", f"${money_out:,.2f}")
    col3.metric("Current Balance", f"${balance:,.2f}")

    st.markdown("---")

    # --- 5. GRAPHS (The Visuals you wanted) ---
    st.subheader("📊 Visualizations")
    
    col_graph1, col_graph2 = st.columns(2)

    with col_graph1:
        st.caption("Expenses Breakdown")
        # Filter only expenses for the pie chart
        expenses_df = df[df["Type"] == "Expense"]
        if not expenses_df.empty:
            fig_pie = px.pie(expenses_df, values='Amount', names='Category', title='Spending by Category')
            st.plotly_chart(fig_pie)
        else:
            st.info("No expenses added yet.")

    with col_graph2:
        st.caption("Income vs Expense Trend")
        # Bar graph of all types
        fig_bar = px.bar(df, x="Date", y="Amount", color="Type", title="Cash Flow Over Time")
        st.plotly_chart(fig_bar)

    # --- 6. DISPLAY RAW DATA ---
    st.subheader("Recent Transactions")
    st.dataframe(df.sort_values(by="Date", ascending=False), use_container_width=True)

else:
    st.info("No data found. Add your first transaction in the sidebar!")