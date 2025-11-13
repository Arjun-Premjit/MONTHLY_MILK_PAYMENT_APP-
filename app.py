import os
import streamlit as st
import pandas as pd
import calendar
from datetime import datetime
import gspread
import json
from google.oauth2.service_account import Credentials

def get_connection():
  """Authenticate and connect to Google Sheets."""
  try:
    creds_dict = {
        "type": st.secrets["google"]["type"],
        "project_id": st.secrets["google"]["project_id"],
        "private_key_id": st.secrets["google"]["private_key_id"],
        "private_key": st.secrets["google"]["private_key"],
        "client_email": st.secrets["google"]["client_email"],
        "client_id": st.secrets["google"]["client_id"],
        "auth_uri": st.secrets["google"]["auth_uri"],
        "token_uri": st.secrets["google"]["token_uri"],
        "auth_provider_x509_cert_url": st.secrets["google"]["auth_provider_x509_cert_url"],
        "client_x509_cert_url": st.secrets["google"]["client_x509_cert_url"],
        "universe_domain": st.secrets["google"]["universe_domain"]
    }
    creds = Credentials.from_service_account_info(creds_dict, scopes=[
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ])
    client = gspread.authorize(creds)
    sheet_id = st.secrets["google"]["sheet_id"]
    sheet = client.open_by_key(sheet_id).sheet1  # Access the first sheet
    return sheet
  except Exception as e:
    st.error(f"Connection error: {e}. Verify your Google service account and sheet permissions.")
    return None
   

def get_days_in_month(month_num, year):
    """Return number of days in month."""
    return calendar.monthrange(year, month_num)[1]

def load_data_db(sheet, month_num, year):
    """Load data for given month/year from Google Sheet."""
    days = get_days_in_month(month_num, year)
    dates_list = [f"{day:02d}/{month_num:02d}/{year}" for day in range(1, days + 1)]
    
    # Default DataFrame structure
    default_df = pd.DataFrame({
        "தேதி": dates_list,
        "காலை": [0.0] * len(dates_list),
        "மாலை": [0.0] * len(dates_list)
    })
    
    if sheet is None:
        st.warning("No connection to Google Sheets. Showing default empty data.")
        return default_df
    
    try:
        # Get all records from sheet
        records = sheet.get_all_records()
        # Filter by dates
        data_dict = {}
        for record in records:
            if record["Date"] in dates_list:
                data_dict[record["Date"]] = (record.get("Morning", 0.0), record.get("Evening", 0.0))
        
        # Create DataFrame
        df_data = {
            "தேதி": dates_list,
            "காலை": [data_dict.get(date, (0.0, 0.0))[0] for date in dates_list],
            "மாலை": [data_dict.get(date, (0.0, 0.0))[1] for date in dates_list]
        }
        return pd.DataFrame(df_data)
    except Exception as e:
        st.error(f"Error loading data: {e}. Showing default empty data.")
        return default_df

def save_data_db(sheet, df):
    """Update existing rows if Date exists, otherwise append new rows."""
    if sheet is None:
        st.error("Cannot save: No connection to Google Sheets.")
        return

    try:
        # Get all existing records from the sheet
        existing_records = sheet.get_all_records()
        existing_dates = [record["Date"] for record in existing_records]

        # Create a mapping of Date → row number (starting from 2, since row 1 has headers)
        date_to_rownum = {record["Date"]: idx + 2 for idx, record in enumerate(existing_records)}

        # Track how many rows were updated and appended
        updated, appended = 0, 0

        # Iterate through each record in the DataFrame
        for _, row in df.iterrows():
            date_str = row["தேதி"]
            morning = float(row["காலை"])
            evening = float(row["மாலை"])

            if date_str in date_to_rownum:
                # Existing record found → update in place
                row_num = date_to_rownum[date_str]
                sheet.update(f"B{row_num}:C{row_num}", [[morning, evening]])
                updated += 1
            else:
                # New record → append as new row
                sheet.append_row([date_str, morning, evening], value_input_option="USER_ENTERED")
                appended += 1

        #st.success(f"✅ {updated} rows updated, {appended} new rows added successfully!")

    except Exception as e:
        st.error(f"❌ Error saving to Google Sheet: {e}")

def app():
    st.title("MILK PAYMENT MONEY CALCULATOR 🐄🥛")
    
    sheet = get_connection()

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
    df = load_data_db(sheet, selected_month_num, selected_year)

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
            save_data_db(sheet, edited_df)
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
    ft = '{:.2f}'.format(total_litres)
    st.write("---")

    st.write("# Total Amount of milk bought in the month of ", selected_month_name, " ", selected_year, " :", ft, " L")
    st.write("## Calculation: ", ft, " X ", price_per_litre, " = ₹ ", total_price) 
    st.write(f"# Total to Pay:   ₹ {total_price:.2f}")

if __name__ == "__main__":
    app()





