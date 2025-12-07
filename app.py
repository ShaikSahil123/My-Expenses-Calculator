import streamlit as st
import pandas as pd
import plotly.express as px
import os
from datetime import datetime

# --- CONFIGURATION ---
FILE_PATH = 'my_expenses.xlsx'
st.set_page_config(page_title="Expense Tracker Pro", layout="wide", page_icon="💰")

# --- 1. BACKEND FUNCTIONS ---

def load_data():
    """Loads the Excel file. Creates it if it doesn't exist."""
    if not os.path.exists(FILE_PATH):
        # Create empty structure
        df = pd.DataFrame(columns=["Date", "Type", "Category", "Amount", "Notes"])
        df.to_excel(FILE_PATH, index=False)
        return df
    
    # Read the file
    df = pd.read_excel(FILE_PATH)
    
    # Ensure 'Date' column is treated as text/string to avoid the "45998" error
    df['Date'] = df['Date'].astype(str)
    return df

def save_data(date, trans_type, category, amount, notes):
    """Adds a new transaction."""
    df = load_data()
    
    # FIX: Convert date to a nice string "YYYY-MM-DD" before saving
    date_str = date.strftime("%Y-%m-%d")
    
    new_data = pd.DataFrame({
        "Date": [date_str],
        "Type": [trans_type],
        "Category": [category],
        "Amount": [amount],
        "Notes": [notes]
    })
    
    df = pd.concat([df, new_data], ignore_index=True)
    df.to_excel(FILE_PATH, index=False)

def delete_data(index_to_delete):
    """Deletes a transaction by row number."""
    df = load_data()
    if 0 <= index_to_delete < len(df):
        df = df.drop(index_to_delete)
        df.reset_index(drop=True, inplace=True)
        df.to_excel(FILE_PATH, index=False)
        return True
    return False

# --- 2. THE UI SETUP ---

st.title("💰 Smart Finance Manager")

# Load data
df = load_data()

# --- TABS LAYOUT ---
tab1, tab2, tab3 = st.tabs(["📊 Detailed Dashboard", "➕ Add Transaction", "🗑️ History & Delete"])

# --- TAB 1: DETAILED DASHBOARD ---
with tab1:
    if not df.empty:
        # --- A. SUMMARY CARDS ---
        money_in = df[df["Type"].isin(["Income", "Debt Repaid"])]["Amount"].sum()
        money_out = df[df["Type"].isin(["Expense", "Debt Given"])]["Amount"].sum()
        balance = money_in - money_out

        col1, col2, col3 = st.columns(3)
        col1.metric("TOTAL INCOME", f"₹{money_in:,.2f}", delta="Money In")
        col2.metric("TOTAL SPENT", f"₹{money_out:,.2f}", delta="-Money Out", delta_color="inverse")
        col3.metric("NET BALANCE", f"₹{balance:,.2f}", delta="Savings")
        
        st.divider()

        # --- B. DETAILED GRAPHS ---
        col_g1, col_g2 = st.columns(2)

        with col_g1:
            st.subheader("🍩 Spending Breakdown")
            # Filter for expenses only
            expenses_df = df[df["Type"] == "Expense"]
            
            if not expenses_df.empty:
                # Group by Category to sum up duplicates (e.g. 2 'Food' entries become 1 slice)
                pie_data = expenses_df.groupby("Category")["Amount"].sum().reset_index()
                
                fig_pie = px.pie(
                    pie_data, 
                    values='Amount', 
                    names='Category', 
                    title='Where is your money going?',
                    hole=0.4, # Makes it a Donut chart
                )
                # Show percentage and label on the chart
                fig_pie.update_traces(textposition='inside', textinfo='percent+label')
                st.plotly_chart(fig_pie, use_container_width=True)
            else:
                st.info("No expenses to show yet.")

        with col_g2:
            st.subheader("📉 Income vs Expense Flow")
            
            # Create a bar chart that stacks by Date
            # text_auto=True puts the number ON TOP of the bar
            fig_bar = px.bar(
                df, 
                x="Date", 
                y="Amount", 
                color="Type", 
                title="Daily Transactions", 
                text_auto='.2s',  # Short format for numbers (e.g. 1.2k)
                barmode='group'   # Groups bars side-by-side instead of stacking
            )
            # Make the chart background clean
            fig_bar.update_layout(xaxis_title="Date", yaxis_title="Amount (₹)")
            st.plotly_chart(fig_bar, use_container_width=True)

    else:
        st.info("Waiting for data... Go to 'Add Transaction' to start!")

# --- TAB 2: ADD TRANSACTION ---
with tab2:
    st.markdown("### Add a New Record")
    
    with st.form("entry_form", clear_on_submit=True):
        col_a, col_b = st.columns(2)
        
        with col_a:
            date_val = st.date_input("When?", datetime.today())
            trans_type = st.selectbox("What Type?", ["Expense", "Income", "Debt Given", "Debt Repaid"])
        
        with col_b:
            amount_val = st.number_input("Amount (₹)", min_value=0.0, format="%.2f")
            
            # Smart Labels
            if trans_type == "Expense":
                label = "Category (e.g., Food, Fuel)"
                placeholder = "Food"
            elif trans_type == "Income":
                label = "Source (e.g., Salary)"
                placeholder = "Salary"
            else:
                label = "Person Name"
                placeholder = "John Doe"
            
            category_val = st.text_input(label, placeholder=placeholder)

        notes_val = st.text_area("Notes (Optional)")
        
        submitted = st.form_submit_button("✅ Save to Excel")
        
        if submitted:
            if category_val and amount_val > 0:
                save_data(date_val, trans_type, category_val, amount_val, notes_val)
                st.success(f"Saved: ₹{amount_val} for {category_val}")
                st.rerun()
            else:
                st.error("Please ensure Amount is > 0 and Category is filled.")

# --- TAB 3: HISTORY & DELETE ---
with tab3:
    st.subheader("📜 Transaction History")
    
    if not df.empty:
        # Show the data table
        st.dataframe(df, use_container_width=True)
        
        st.divider()
        st.markdown("### 🗑️ Remove a Mistake")
        
        # Create a readable list for the dropdown
        # Format: "Row [0] | 2023-10-01 | Expense | Food | ₹500"
        delete_options = [
            f"Row [{i}] | {row['Date']} | {row['Type']} | {row['Category']} | ₹{row['Amount']}" 
            for i, row in df.iterrows()
        ]
        
        selected_option = st.selectbox("Select which entry to delete:", options=delete_options)
        
        if st.button("❌ Delete Selected Entry"):
            # Extract the index number from the string "Row [0]..."
            # We split by "]" and take the part after "Row ["
            try:
                index_to_delete = int(selected_option.split("]")[0].split("[")[1])
                if delete_data(index_to_delete):
                    st.success("Deleted successfully!")
                    st.rerun()
            except:
                st.error("Could not delete. Please try again.")
    else:
        st.info("No records found.")