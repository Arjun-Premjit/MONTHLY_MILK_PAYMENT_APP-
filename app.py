import streamlit as st
import pandas as pd
import calendar

def app():
    st.title("MILK PAYMENT MONEY CALCULATOR 🐄🥛")


    month_names = [calendar.month_name[i] for i in range(1, 13)]

    # Display the selectbox
    selected_month = st.selectbox(
        "Select a month:",
        month_names
    )
    st.write('\n'*20)

    # Create the fixed column data
    fixed_column = pd.Series(range(1, 32), name="தேதி")

    # Create the editable columns data, initialized to 700.0
    editable_col1 = pd.Series([0.0] * 31, name="காலை")
    editable_col2 = pd.Series([0.0] * 31, name="மாலை")

    # Combine into a DataFrame
    df = pd.DataFrame({
        "தேதி": fixed_column,
        "காலை": editable_col1,
        "மாலை": editable_col2
    })

    # Configure columns for editing
    edited_df = st.data_editor(
        df,
        column_config={
            "தேதி": st.column_config.NumberColumn(
                "தேதி",
                help="This column contains fixed values from 1 to 32 and cannot be edited.",
                disabled=True  # Disable editing for this column
            ),
            "காலை": st.column_config.NumberColumn(
                "காலை",
                help="You can edit the values in this column.",
                format="%.1f" # Format to one decimal place
            ),
            "மாலை": st.column_config.NumberColumn(
                "மாலை",
                help="You can edit the values in this column.",
                format="%.1f" # Format to one decimal place
            )
        },
        hide_index=True, # Hide the DataFrame index
        num_rows="dynamic" # Allow adding/deleting rows if needed
    )

    total_quantity1 = edited_df["காலை"].sum()
    total_quantity2 = edited_df["மாலை"].sum()

    price=(total_quantity1 + total_quantity2)*0.045
    
    st.write("# You have to pay: ₹", price)

if __name__ == "__main__":
    app()