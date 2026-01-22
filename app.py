import streamlit as st
import pandas as pd
import plotly.express as px
import os
from datetime import datetime

# --- CONFIGURATION ---
FILE_PATH = 'my_expenses.xlsx'
st.set_page_config(page_title="Monthly Expense Manager", layout="wide", page_icon="💰")

# --- 1. BACKEND FUNCTIONS ---

def load_data():
    """Loads data and ensures the Date column is correct for filtering."""
    if not os.path.exists(FILE_PATH):
        df = pd.DataFrame(columns=["Date", "Type", "Category", "Amount", "Notes"])
        df.to_excel(FILE_PATH, index=False)
        return df
    
    df = pd.read_excel(FILE_PATH)
    
    # FIX: Ensure Date is converted to DateTime objects for filtering
    # errors='coerce' turns bad dates into NaT (Not a Time) so the app doesn't crash
    df["Date"] = pd.to_datetime(df["Date"], errors='coerce') 
    
    # Remove any rows where the Date got messed up
    df = df.dropna(subset=["Date"])
    
    return df

def save_data(date, trans_type, category, amount, notes):
    """Saves data to Excel."""
    df = load_data()
    
    # Create new row
    new_data = pd.DataFrame({
        "Date": [date], # We keep it as datetime object here
        "Type": [trans_type],
        "Category": [category],
        "Amount": [amount],
        "Notes": [notes]
    })
    
    df = pd.concat([df, new_data], ignore_index=True)
    
    # Save back to Excel (Excel handles datetime objects well)
    df.to_excel(FILE_PATH, index=False)

def delete_data(original_index):
    """Deletes a row based on its original index in the Excel file."""
    df = load_data()
    
    # Check if index exists to prevent errors
    if original_index in df.index:
        df = df.drop(original_index)
        df.reset_index(drop=True, inplace=True)
        df.to_excel(FILE_PATH, index=False)
        return True
    return False

# --- 2. SIDEBAR FILTERS (MONTHLY VIEW) ---

st.sidebar.header("📅 Filter Data")
current_year = datetime.now().year
current_month = datetime.now().month

# Select Year
selected_year = st.sidebar.selectbox("Year", range(2023, 2030), index=(current_year - 2023))

# Select Month
month_names = {
    1: "January", 2: "February", 3: "March", 4: "April", 5: "May", 6: "June",
    7: "July", 8: "August", 9: "September", 10: "October", 11: "November", 12: "December"
}
selected_month_name = st.sidebar.selectbox("Month", list(month_names.values()), index=(current_month - 1))

# Convert name back to number (e.g., "January" -> 1)
selected_month = list(month_names.keys())[list(month_names.values()).index(selected_month_name)]

# --- 3. FILTER LOGIC ---
# Load all data first
all_data = load_data()

# Filter data based on sidebar selection
if not all_data.empty:
    # Filter: Get rows where Year matches AND Month matches
    filtered_df = all_data[
        (all_data["Date"].dt.year == selected_year) & 
        (all_data["Date"].dt.month == selected_month)
    ]
else:
    filtered_df = pd.DataFrame()

# --- 4. THE MAIN UI ---

st.title(f"💰 Finance Dashboard - {selected_month_name} {selected_year}")

tab1, tab2, tab3 = st.tabs(["📊 Dashboard (Monthly)", "➕ Add Transaction", "🗑️ History & Delete"])

# --- TAB 1: DASHBOARD (FILTERED BY MONTH) ---
with tab1:
    if not filtered_df.empty:
        # Calculate Metrics for the SELECTED MONTH only
        money_in = filtered_df[filtered_df["Type"].isin(["Income", "Debt Repaid"])]["Amount"].sum()
        money_out = filtered_df[filtered_df["Type"].isin(["Expense", "Debt Given"])]["Amount"].sum()
        balance = money_in - money_out

        col1, col2, col3 = st.columns(3)
        col1.metric("Income (This Month)", f"${money_in:,.2f}", delta="In")
        col2.metric("Spent (This Month)", f"${money_out:,.2f}", delta="-Out", delta_color="inverse")
        col3.metric("Balance (This Month)", f"${balance:,.2f}", delta="Net")
        
        st.divider()

        col_g1, col_g2 = st.columns(2)

        with col_g1:
            st.subheader("🍩 Monthly Expenses")
            expenses_df = filtered_df[filtered_df["Type"] == "Expense"]
            if not expenses_df.empty:
                fig_pie = px.pie(expenses_df, values='Amount', names='Category', hole=0.4)
                fig_pie.update_traces(textposition='inside', textinfo='percent+label')
                st.plotly_chart(fig_pie, use_container_width=True)
            else:
                st.info("No expenses in this month.")

        with col_g2:
            st.subheader("📉 Daily Activity")
            # Format date to show nicely on graph
            plot_df = filtered_df.copy()
            plot_df["Date"] = plot_df["Date"].dt.strftime("%Y-%m-%d")
            
            fig_bar = px.bar(plot_df, x="Date", y="Amount", color="Type", barmode='group', text_auto='.2s')
            st.plotly_chart(fig_bar, use_container_width=True)
    else:
        st.info(f"No records found for {selected_month_name} {selected_year}.")

# --- TAB 2: ADD TRANSACTION (FIXED FORM) ---
with tab2:
    st.subheader("Add New Record")
    
    # --- FIX: RADIO BUTTON OUTSIDE FORM ---
    # This ensures the label updates immediately when you click "Income" or "Expense"
    trans_type = st.radio("Transaction Type", ["Expense", "Income", "Debt Given", "Debt Repaid"], horizontal=True)

    # Dynamic Label Logic
    if trans_type == "Expense":
        label_text = "Category (e.g., Food, Rent)"
        ph_text = "Food"
    elif trans_type == "Income":
        label_text = "Source (e.g., Salary, Freelance)"
        ph_text = "Salary"
    else:
        label_text = "Person Name"
        ph_text = "John Doe"

    # --- START FORM ---
    with st.form("entry_form", clear_on_submit=True):
        col_a, col_b = st.columns(2)
        
        with col_a:
            date_val = st.date_input("Date", datetime.today())
        
        with col_b:
            amount_val = st.number_input("Amount (₹)", min_value=0.0, format="%.2f")
        
        # The label here now updates correctly because 'trans_type' is outside
        category_val = st.text_input(label_text, placeholder=ph_text)
        notes_val = st.text_area("Notes (Optional)")
        
        submitted = st.form_submit_button("✅ Save Entry")
        
        if submitted:
            # FIX: Robust error checking
            if amount_val <= 0:
                st.error("⚠️ Error: Amount must be greater than 0.")
            elif not category_val:
                st.error(f"⚠️ Error: The '{label_text}' field is empty.")
            else:
                save_data(date_val, trans_type, category_val, amount_val, notes_val)
                st.success("Entry Saved!")
                st.rerun()

# --- TAB 3: MANAGE & DELETE (GLOBAL VIEW) ---
with tab3:
    st.subheader("📜 All History (Delete items here)")
    
    if not all_data.empty:
        # We show ALL data here so you can delete old mistakes even if they are not in the current month
        # We add an 'ID' column so the user knows exactly which row is which
        display_df = all_data.copy()
        display_df["Date"] = display_df["Date"].dt.strftime("%Y-%m-%d") # Make date readable
        display_df.index.name = "ID"
        
        st.dataframe(display_df, use_container_width=True)
        
        st.divider()
        st.markdown("### 🗑️ Delete an Entry")
        
        # Create a list for the dropdown that INCLUDES the unique ID
        # Format: "ID: 5 | 2023-10-01 | Expense | Food | ₹50.0"
        delete_options = [
            f"ID: {i} | {row['Date'].strftime('%Y-%m-%d')} | {row['Type']} | {row['Category']} | ₹{row['Amount']}" 
            for i, row in all_data.iterrows()
        ]
        
        selected_option = st.selectbox("Select entry to delete:", delete_options)
        
        if st.button("❌ Delete Selected"):
            try:
                # Extract the ID from the string "ID: 5 | ..."
                id_to_delete = int(selected_option.split("|")[0].replace("ID:", "").strip())
                
                if delete_data(id_to_delete):
                    st.success(f"Successfully deleted ID: {id_to_delete}")
                    st.rerun()
                else:
                    st.error("Error: Could not find that row.")
            except Exception as e:
                st.error(f"Delete failed: {e}")
    else:
        st.info("No data available.")