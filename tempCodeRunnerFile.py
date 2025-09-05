try:
    con = mysql.connector.connect(
        host="127.0.0.1",
        user="root",
        password="12345",
        database="bot"
    )
    cursor = con.cursor()
    print("✅ Connection succeed")
except mysql.connector.Error as e: