import os
import streamlit as st
import pandas as pd
import calendar
from datetime import datetime

try:
    import mysql.connector
    from mysql.connector import Error
except ModuleNotFoundError:
    mysql = None
    Error = Exception

def get_connection():
    conn=mysql.connector.connect(
        host=st.secrets["mysql"]["host"],
        user=st.secrets["mysql"]["user"],
        password=st.secrets["mysql"]["password"],
        database=st.secrets["mysql"]["database"],
        port=st.secrets["mysql"]["port"] 
        )
    return conn

def get_days_in_month(month_num, year):
    """Return number of days in month."""
    return calendar.monthrange(year, month_num)[1]

def load_data_db(conn, month_num, year):
    """Load data for given month/year from milk_data table."""
    days = get_days_in_month(month_num, year)
    dates_list = [f"{day:02d}/{month_num:02d}/{year}" for day in range(1, days + 1)]
    
    cur = conn.cursor()
    placeholders = ",".join(["%s"] * len(dates_list))
    cur.execute(f"SELECT DATE, MORNING, EVENING FROM milk_data WHERE DATE IN ({placeholders})", dates_list)
    rows = cur.fetchall()
    cur.close()
    
    # Build dict from DB rows
    data_dict = {row[0]: (row[1], row[2]) for row in rows}
    
    # Create DataFrame with all dates for the month
    df_data = {
        "தேதி": dates_list,
        "காலை": [data_dict.get(date, (0.0, 0.0))[0] for date in dates_list],
        "மாலை": [data_dict.get(date, (0.0, 0.0))[1] for date in dates_list]
    }
    return pd.DataFrame(df_data)

def save_data_db(conn, df):
    """Save all rows from DataFrame to milk_data table."""
    rows = []
    for _, r in df.iterrows():
        rows.append((r["தேதி"], float(r["காலை"]), float(r["மாலை"])))
    
    cur = conn.cursor()
    sql = """
    INSERT INTO milk_data (DATE, MORNING, EVENING)
    VALUES (%s, %s, %s)
    ON DUPLICATE KEY UPDATE
        MORNING = VALUES(MORNING),
        EVENING = VALUES(EVENING);
    """

    cur.executemany(sql, rows)
    conn.commit()
    cur.close()

def app():
    st.title("MILK PAYMENT MONEY CALCULATOR 🐄🥛")
    
    conn = get_connection()


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
    df = load_data_db(conn, selected_month_num, selected_year)

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

    # Save on change
    if edited_df is not None and not edited_df.equals(df):
        try:
            save_data_db(conn, edited_df)
            st.session_state.editor_key += 1
        except Error as e:
            st.error(f"Error saving to DB: {e}")
        finally:
            conn.close()

    # Calculate totals
    total_morning = edited_df["காலை"].sum()
    total_evening = edited_df["மாலை"].sum()
    total_litres = (total_morning + total_evening) * 0.001
    
    price_per_litre = st.number_input("# Cost of 1 litre Milk(₹):", value=45, step=1)
    total_price = total_litres * price_per_litre

    st.write("---")

    #st.write(f"# **Total Morning:** {total_morning:.3f} Litres")
    #st.write(f"# **Total Evening:** {total_evening:.3f} Litres")
    
    st.write(f"# Total Amount of milk bought in the month of",selected_month_name,"  ",selected_year," : ",total_litres,"L")
    st.write("## Calculation:",total_litres,"X",price_per_litre  ," = ₹ ",'{:.2f}'.format(total_price)) 
    st.write(f"# **Total to Pay:** ₹ {total_price:.2f}")

if __name__ == "__main__":
    app()

