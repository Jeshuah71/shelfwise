import sqlite3

# 1. Connect to your SQLite database 
# 1. Connect to your SQLite database
connection = sqlite3.connect("shelfwise.db")

# 2. Create a cursor
cursor = connection.cursor()

# 3. Create the food_items table
cursor.execute("""
    CREATE TABLE IF NOT EXISTS food_items (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        category TEXT NOT NULL,
        quantity INTEGER NOT NULL,
        expiration_date TEXT NOT NULL
    )
""")

cursor.execute("""
    CREATE TABLE IF NOT EXISTS distributions (
        id INTEGER PRIMARY KEY,
        food_item_id INTEGER NOT NULL,
        quantity INTEGER NOT NULL CHECK(quantity > 0),
        distributed_at TEXT NOT NULL,
        FOREIGN KEY (food_item_id) REFERENCES food_items(id)
    )
""")

# 4. Save database changes
connection.commit()

# 5. Close the connection
connection.close()

print("Database initialized successfully!")
