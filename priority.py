from datetime import datetime, date
import sqlite3

def get_priority_food():
    
    connection = sqlite3.connect("shelfwise.db")
    
    cursor = connection.cursor()
    
    cursor.execute(
        "SELECT * FROM food_items WHERE quantity > 0 ORDER BY expiration_date ASC",
    )
    
    foods = cursor.fetchall()
    
    for food in foods:
        
        # Retrieve expiration date from the database
        expiration_string = food[4]
        
        # Convert the string into a date
        expiration = datetime.strptime(
            expiration_string, "%Y-%m-%d"
        ).date()
        
        # Calculate days ramaining
        days_left = (expiration - date.today()).days
        
        # if and else 
        
        if days_left < 0:
            priority = "REVIEW / HOLD"

        elif days_left <=2:
            priority = "HIGH"

        elif days_left <=7:
            priority = "MEDIUM"

        else :
            priority = "LOW"

        print(f"{food[1]} | {days_left} days | Priority: {priority}")
        
    connection.close()
    
get_priority_food()