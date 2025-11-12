import os
import streamlit as st
import pandas as pd
import calendar
from datetime import datetime
from pymongo import MongoClient  # Added for MongoDB

def get_connection():
    client = MongoClient(st.secrets["mongodb"]["uri"])
    db = client["cluster0.xfcb70r"]
    return db
       

def get_days_in_month(month_num, year):
    """Return number of days in month."""
    return calendar.monthrange(year, month_num)[1]

def load_data_db(db, month_num, year):
    """Load data for given month/year from milk_data collection."""
    if db is None:
        return pd.DataFrame()  # Return empty DF if no connection
      
    days = get_days_in_month(month_num, year)
    dates_list = [f"{day:02d}/{month_num:02d}/{year}" for day in range(1, days + 1)]
      
    collection = db["milk_data"]  # Define collection here, outside try
      
    try:
        query = {"date": {"$in": dates_list}}
        rows = list(collection.find(query))
          
          # Build dict from DB documents
        data_dict = {row["date"]: (row.get("morning", 0.0), row.get("evening", 0.0)) for row in rows}
          
          # Create DataFrame with all dates for the month
        df_data = {
            "தேதி": dates_list,
            "காலை": [data_dict.get(date, (0.0, 0.0))[0] for date in dates_list],
            "மாலை": [data_dict.get(date, (0.0, 0.0))[1] for date in dates_list]
        }
        return pd.DataFrame(df_data)
    except Exception as e:
        st.error(f"Error loading data: {e}")
        # Return empty DataFrame on error
        return pd.DataFrame({
            "தேதி": dates_list,
            "காலை": [0.0] * len(dates_list),
            "மாலை": [0.0] * len(dates_list)
        })
  

def save_data_db(db, df):
    """Save all rows from DataFrame to milk_data collection."""
    collection = db["milk_data"]
    for _, r in df.iterrows():
        # Upsert document
        collection.update_one(
            {"date": r["தேதி"]},
            {"$set": {"morning": float(r["காலை"]), "evening": float(r["மாலை"])}},
            upsert=True
        )

def app():
    st.title("MILK PAYMENT MONEY CALCULATOR 🐄🥛")
    
    db = get_connection()

    # Get current month and year
    now = datetime.now()
    current_month_num = now.month
    current_year = now.year

    # Month dropdown (all 12 months with current month as default)
    month_names = [calendar.month_name[i] for i in range(1, 13)]
    selected_month_name = st.selectbox(
        "Select Month:",
        options=month_names,
        index=current_month_num - 1  # Default to current month
    )
    selected_month_num = month_names.index(selected_month_name) + 1

    # Year input
    selected_year = st.number_input(
        "Select Year:",
        min_value=2000,
        max_value=2100,
        value=current_year,
        step=1
    )

    st.write(f"**Showing data for: {selected_month_name} {selected_year}**")
    st.write('\n')

    # Load data for selected month/year
    df = load_data_db(db, selected_month_num, selected_year)

    # Data editor
    if 'editor_key' not in st.session_state:
        st.session_state.editor_key = 0

    edited_df = st.data_editor(
        df,
        column_config={
            "தேதி": st.column_config.TextColumn("தேதி (dd/mm/yyyy)", disabled=True),
            "காலை": st.column_config.NumberColumn("காலை", format="%.3f"),
            "மாலை": st.column_config.NumberColumn("மாலை", format="%.3f"),
        },
        hide_index=True,
        num_rows="fixed",
        key=f"editor_{st.session_state.editor_key}"
    )

    # After the data_editor
    if st.button("Save Changes"):
        try:
            save_data_db(db, edited_df)
            st.success("Data saved successfully!")
            st.session_state.editor_key += 1  # Refresh editor
        except Exception as e:
            st.error(f"Error saving to DB: {e}")

    # Calculate totals
    total_morning = edited_df["காலை"].sum()
    total_evening = edited_df["மாலை"].sum()
    total_litres = (total_morning + total_evening) * 0.001
    
    price_per_litre = st.number_input("# Cost of 1 litre Milk(₹):", value=45, step=1)
    total_price = total_litres * price_per_litre
    ft='{:.2f}'.format(total_litres)
    st.write("---")

    st.write("# Total Amount of milk bought in the month of ",selected_month_name," ",selected_year," :",ft," L")
    st.write("## Calculation: ",ft," X ",price_per_litre," = ₹ ",ft) 
    st.write(f"# Total to Pay:   ₹ {total_price:.2f}")

if __name__ == "__main__":
    app()



