import os
import tempfile
import sqlite3
import pandas as pd
import streamlit as st

from inventory import add_food, distribute_food


# ==========================================
# 1. PAGE CONFIGURATION
# ==========================================

st.set_page_config(
    page_title="ShelfWise",
    page_icon="📦",
    layout="wide"
)

# CReate an isolated temporary datbase for each session
if "demo_directory" not in st.session_state:
    st.session_state.demo_directory = tempfile.TemporaryDirectory()

    db_path = os.path.join(
        st.session_state.demo_directory.name,
        "shelfwise.db"
    )

    connection = sqlite3.connect(db_path)

    connection.executescript("""
        CREATE TABLE food_items (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            category TEXT NOT NULL,
            quantity INTEGER NOT NULL CHECK(quantity >= 0),
            expiration_date TEXT NOT NULL
        );

        CREATE TABLE distributions (
            id INTEGER PRIMARY KEY,
            food_item_id INTEGER NOT NULL,
            quantity INTEGER NOT NULL CHECK(quantity > 0),
            distributed_at TEXT NOT NULL,
            FOREIGN KEY (food_item_id) REFERENCES food_items(id)
        );
    """)

    connection.executemany(
        """
        INSERT INTO food_items
        (name, category, quantity, expiration_date)
        VALUES (?, ?, ?, ?)
        """,
        [
            ("Apples", "Fruit", 15, "2026-11-08"),
            ("Milk", "Dairy", 10, "2026-11-10"),
            ("Rice", "Grains", 25, "2027-03-15")
        ]
    )
    
    connection.commit()
    connection.close()

# Retrieve this visitors database path
DB_PATH = os.path.join(
    st.session_state.demo_directory.name,
    "shelfwise.db"
)



# ==========================================
# 2. DATABASE FUNCTIONS
# ==========================================

def load_inventory(db_path):
    """Retrieve all food inventory records."""

    connection = sqlite3.connect(db_path)

    try:
        cursor = connection.cursor()

        cursor.execute("""
            SELECT id, name, category, quantity, expiration_date
            FROM food_items
            ORDER BY expiration_date ASC
        """)

        foods = cursor.fetchall()

    finally:
        connection.close()

    return pd.DataFrame(
        foods,
        columns=[
            "ID",
            "Food",
            "Category",
            "Quantity",
            "Expiration Date"
        ]
    )


def load_distributions(db_path):
    """Retrieve distribution history using SQL JOIN."""

    connection = sqlite3.connect(db_path)

    try:
        cursor = connection.cursor()

        cursor.execute("""
            SELECT
                food_items.name,
                distributions.quantity,
                distributions.distributed_at
            FROM distributions
            JOIN food_items
                ON distributions.food_item_id = food_items.id
            ORDER BY
                distributions.distributed_at DESC,
                distributions.id DESC
        """)

        distributions = cursor.fetchall()

    finally:
        connection.close()

    return pd.DataFrame(
        distributions,
        columns=[
            "Food",
            "Quantity Distributed",
            "Distributed At"
        ]
    )


# ==========================================
# 3. PRIORITY CLASSIFICATION
# ==========================================

def classify_priority(days_left):
    """Assign a date-based review priority."""

    if days_left < 0:
        return "REVIEW / HOLD"

    elif days_left <= 2:
        return "HIGH"

    elif days_left <= 7:
        return "MEDIUM"

    else:
        return "LOW"


# ==========================================
# 4. LOAD AND PREPARE DATA
# ==========================================

inventory_df = load_inventory(DB_PATH)
history_df = load_distributions(DB_PATH)

# Prepare priority columns, including for empty inventory.
inventory_df["Days Left"] = pd.Series(dtype="int64")
inventory_df["Priority"] = pd.Series(dtype="str")

if not inventory_df.empty:

    # Convert expiration strings into dates.
    inventory_df["Expiration Date"] = pd.to_datetime(
        inventory_df["Expiration Date"]
    )

    # Get today's date without the time component.
    today = pd.Timestamp.today().normalize()

    # Calculate remaining days.
    inventory_df["Days Left"] = (
        inventory_df["Expiration Date"] - today
    ).dt.days

    # Classify every food item.
    inventory_df["Priority"] = inventory_df[
        "Days Left"
    ].apply(classify_priority)

    # Format dates for display.
    inventory_df["Expiration Date"] = (
        inventory_df["Expiration Date"]
        .dt.strftime("%Y-%m-%d")
    )


# ==========================================
# 5. DASHBOARD HEADER
# ==========================================

st.title("ShelfWise")

st.write(
    "Smart Food Inventory and Distribution Tracker"
)

st.info(
    "Track donated food, monitor inventory, "
    "and prioritize distribution."
)

st.caption(
    "Date-based priorities are planning indicators, "
    "not food-safety determinations."
)


# ==========================================
# 6. INVENTORY OVERVIEW
# ==========================================

st.subheader("Inventory Overview")

col1, col2, col3, col4 = st.columns(4)

with col1:
    food_types = inventory_df["Food"].nunique()

    st.metric(
        "Food Types",
        int(food_types)
    )

with col2:
    available_units = inventory_df["Quantity"].sum()

    st.metric(
        "Available Units",
        int(available_units)
    )

with col3:
    high_priority = (
        inventory_df["Priority"] == "HIGH"
    ).sum()

    st.metric(
        "High Priority",
        int(high_priority)
    )

with col4:
    total_distributed = history_df[
        "Quantity Distributed"
    ].sum()

    st.metric(
        "Units Distributed",
        int(total_distributed)
    )


# ==========================================
# 7. FOOD INVENTORY
# ==========================================

st.divider()

st.subheader("Food Inventory")

if inventory_df.empty:
    st.info(
        "No food items have been added yet. "
        "Use the donation form below."
    )

else:
    st.dataframe(
        inventory_df,
        hide_index=True,
        use_container_width=True,
        column_config={
            "Priority": st.column_config.TextColumn(
                "Priority",
                help="Priority based on the listed date"
            ),
            "Quantity": st.column_config.NumberColumn(
                "Quantity",
                format="%d"
            )
        }
    )

    # Show a warning when records require review.
    held_items = (
        inventory_df["Priority"] == "REVIEW / HOLD"
    ).sum()

    if held_items > 0:
        st.warning(
            f"{held_items} inventory item(s) require "
            "review before distribution."
        )


# ==========================================
# 8. ADD NEW DONATION
# ==========================================

st.divider()

st.subheader("Add New Donation")

with st.form("donation_form", clear_on_submit=True):

    name = st.text_input(
        "Food name",
        placeholder="Example: Milk"
    )

    category = st.selectbox(
        "Category",
        [
            "Fruit",
            "Vegetables",
            "Dairy",
            "Grains",
            "Canned Food",
            "Other"
        ]
    )

    quantity = st.number_input(
        "Quantity",
        min_value=1,
        value=1,
        step=1
    )

    expiration_date = st.date_input(
        "Expiration date"
    )

    donation_submitted = st.form_submit_button(
        "Add Donation"
    )

    if donation_submitted:

        if not name.strip():
            st.error("Please enter a food name.")

        else:
            try:
                add_food(
                    name.strip(),
                    category,
                    int(quantity),
                    expiration_date.isoformat(),
                    DB_PATH
                )

                st.session_state["success_message"] = (
                    "Donation added successfully!"
                )

                st.rerun()

            except sqlite3.Error as error:
                st.error(
                    f"Unable to save donation: {error}"
                )


# ==========================================
# 9. DISTRIBUTE FOOD
# ==========================================

st.divider()

st.subheader("Distribute Food")

# Show only available items that are not on hold.
available_food = inventory_df[
    (inventory_df["Quantity"] > 0)
    & (inventory_df["Priority"] != "REVIEW / HOLD")
]

if available_food.empty:

    st.info(
        "No eligible inventory is currently available "
        "for distribution."
    )

else:

    # Map each ID to a readable dropdown label.
    food_options = {
        int(row["ID"]): (
            f"{row['Food']} "
            f"(ID: {row['ID']}, "
            f"Available: {row['Quantity']})"
        )
        for _, row in available_food.iterrows()
    }

    with st.form("distribution_form"):

        food_id = st.selectbox(
            "Select Food",
            options=list(food_options.keys()),
            format_func=lambda item_id: food_options[item_id]
        )

        quantity_to_distribute = st.number_input(
            "Quantity to distribute",
            min_value=1,
            value=1,
            step=1
        )

        distribution_submitted = st.form_submit_button(
            "Distribute Food"
        )

        if distribution_submitted:

            try:
                distribute_food(
                    int(food_id),
                    int(quantity_to_distribute),
                    DB_PATH
                )

                st.session_state["success_message"] = (
                    "Food distributed successfully!"
                )

                st.rerun()

            except ValueError as error:
                st.error(str(error))

            except sqlite3.Error as error:
                st.error(
                    f"Database error: {error}"
                )


# ==========================================
# 10. DISTRIBUTION HISTORY
# ==========================================

st.divider()

st.subheader("Distribution History")

if history_df.empty:

    st.info(
        "No distributions have been recorded yet."
    )

else:

    st.dataframe(
        history_df,
        hide_index=True,
        use_container_width=True
    )


# ==========================================
# 11. SUCCESS NOTIFICATIONS
# ==========================================

if "success_message" in st.session_state:

    st.toast(
        st.session_state.pop("success_message"),
    )


# ==========================================
# 12. FOOTER
# ==========================================

st.divider()

st.caption(
    "ShelfWise | Food Inventory & Distribution Tracker"
)
