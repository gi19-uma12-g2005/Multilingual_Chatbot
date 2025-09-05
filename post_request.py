from dotenv import load_dotenv
import os
import mysql.connector

load_dotenv()
print("USER:", os.getenv("DB_USER"))
print("PASS:", os.getenv("DB_PASS"))
print("DB:", os.getenv("DB_DATABASE"))


try:
    con=mysql.connector.connect(

    host="127.0.0.1",
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASS"),
    database=os.getenv("DB_DATABASE")

)
    print("Connection succeed")


except mysql.connector.Error as e:
    print("❌ Failed:", e)

    
