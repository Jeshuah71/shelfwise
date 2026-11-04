from datetime import datetime
import sqlite3

def add_food(name, category, quantity, expiration_date, db_path):
    # Conect to the database
    connection = sqlite3.connect(db_path)
    
    # Create a cursor to execute SQL commands
    cursor = connection.cursor()
    
    cursor.execute(
        "INSERT INTO food_items (name, category, quantity, expiration_date) VALUES (?, ?, ?, ?)",
        (name, category, quantity, expiration_date)
    )
    
    # Save the inserted record
    connection.commit()
    
    # Close the database connection 
    connection.close()
    
def view_food():
    
    connection = sqlite3.connect("shelfwise.db")
    
    cursor = connection.cursor()
    
    cursor.execute(
        "SELECT * FROM food_items"
    )
    
    foods = cursor.fetchall()
    
    for food in foods:
        print(f"ID: {food[0]} | Food: {food[1]} | Category: {food[2]} | Quantity: {food[3]} | Expires {food[4]}")
        
    connection.close()
    
def update_food(food_id, new_quantity):
    
    # 1 Connect to the database
    connection = sqlite3.connect("shelfwise.db")
    
    # 2. Create a cursor
    cursor = connection.cursor()
    
    # UPdate the quantity 
    cursor.execute(
        "UPDATE food_items SET quantity = ? WHERE id = ?",
        (new_quantity, food_id)
    )
    
    # 4. Commit changes
    connection.commit()
    
    # Close the connection
    connection.close()
    
def delete_food(food_id):
    
    connection = sqlite3.connect("shelfwise.db")
    
    cursor = connection.cursor()
    
    cursor.execute(
        "DELETE FROM food_items WHERE id = ?",
        (food_id,)    
    )
    
    connection.commit()
    
    connection.close()
    

def distribute_food(food_id, quantity, db_path):
    connection = sqlite3.connect(db_path)

    # Enable foreign key validation
    connection.execute("PRAGMA foreign_keys = ON")

    try:
        # TODO 1: Verify that the requested quantity is positive
        if quantity <= 0:
            raise ValueError("Quantity must be positive.")

        # TODO 2: Reduce inventory without allowing negative stock
        cursor = connection.cursor()
        cursor.execute(
            "UPDATE food_items SET quantity = quantity - ? WHERE id = ? AND quantity >= ?",
            (quantity, food_id, quantity)
        )
        # TODO 3: Check whether the inventory update succeeded
        if cursor.rowcount != 1:
            raise ValueError("Food not found or insufficient inventory.")

        # TODO 4: Insert the distribution history

        cursor.execute(
            """
            INSERT INTO distributions (food_item_id, quantity, distributed_at)
            VALUES (?, ?, ?)
            """,
            (food_id, quantity, datetime.now().isoformat(timespec="seconds"))
        )
        # TODO 5: Commit the transaction
        connection.commit()

        pass

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()

    

if __name__ == "__main__":
    print("BEFORE DISTRIBUTION")
    view_food()
    
    distribute_food(2,100)
    
    print("\nAFTER DISTRIBUTION")
    view_food()
    