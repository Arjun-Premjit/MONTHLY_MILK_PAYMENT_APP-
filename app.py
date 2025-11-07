import streamlit as st
import pandas as pd
import calendar
import os


def load_data(selected_month):
    file_path = f"data_{selected_month}.csv"
    
    if os.path.exists(file_path):
        return pd.read_csv(file_path)
    
    # Create default DataFrame for new month
    df = pd.DataFrame({
        "தேதி": range(1, 32),
        "காலை": [0.0] * 31,
        "மாலை": [0.0] * 31
    })
    df.to_csv(file_path, index=False)
    return df

def save_data(df, selected_month):
    """Save DataFrame to CSV file"""
    file_path = f"data_{selected_month}.csv"
    df.to_csv(file_path, index=False)

def app():
    st.title("MILK PAYMENT MONEY CALCULATOR 🐄🥛")

    # Initialize session state for the editor's key
    if 'editor_key' not in st.session_state:
        st.session_state.editor_key = 0

    month_names = [calendar.month_name[i] for i in range(1, 13)]
    selected_month = st.selectbox("Select a month:", month_names)
    st.write('\n'*20)

    # Load data for selected month
    df = load_data(selected_month)

    # Configure columns for editing
    edited_df = st.data_editor(
        df,
        column_config={
            "தேதி": st.column_config.NumberColumn(
                "தேதி",
                help="This column contains fixed values from 1 to 32 and cannot be edited.",
                disabled=True
            ),
            "காலை": st.column_config.NumberColumn(
                "காலை",
                help="You can edit the values in this column.",
                format="%.1f"
            ),
            "மாலை": st.column_config.NumberColumn(
                "மாலை",
                help="You can edit the values in this column.",
                format="%.1f"
            )
        },
        hide_index=True,
        num_rows="dynamic",
        key=f"editor_{st.session_state.editor_key}"
    )

    # Save changes immediately when data is edited
    if edited_df is not None and not edited_df.equals(df):
        save_data(edited_df, selected_month)
        st.session_state.editor_key += 1  # Force re-render of editor
        st.rerun()  # Rerun the app to show updated data

    # Calculate totals using the edited DataFrame
    total_quantity1 = edited_df["காலை"].sum()
    total_quantity2 = edited_df["மாலை"].sum()
    price = (total_quantity1 + total_quantity2) * 0.045
    
    integer_value = st.number_input("# Cost of 1 Litre Milk: ", value=45, step=1)

    st.write("# Total amount of milk bought in the month of ",selected_month,"is",(total_quantity1+total_quantity2)*0.001,"litres.")
    
    st.write("## Calculation: ", (total_quantity1+ total_quantity2*0.001)," X",integer_value," = ₹ ", price)

    st.write("# You have to pay: ₹", price)

if __name__ == "__main__":
    app()
