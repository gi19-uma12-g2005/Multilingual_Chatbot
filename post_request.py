from flask import Flask, render_template, request, jsonify
import mysql.connector
from werkzeug.security import generate_password_hash, check_password_hash
import os
app = Flask(__name__,template_folder=r"D:\Umang_Coding\AI_chatbot\template")

#  MySQL connection
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
    print("❌ Failed:", e)

# 🔹 Serve HTML page
@app.route("/")
def home():
    return render_template("ug1.html")  # Browser me colorful page dikhega

# 🔹 Login form submit
@app.route("/login", methods=["POST"])
def login():
    user = request.form.get("user_id")
    password = request.form.get("password")

    if not user or not password:
        return jsonify({"message": "❌ User ID and Password required!"})
    
    hashed_password = generate_password_hash(password)


    try:
        cursor.execute("INSERT INTO USER (USER_ID, PASSWORD) VALUES (%s, %s)", (user,hashed_password))
        con.commit()
        return jsonify({"message": f"✅ User {user} added successfully!"})
    except mysql.connector.Error as e:
        return jsonify({"message": f"❌ Database Error: {str(e)}"})




if __name__ == "__main__":
    app.run(debug=True)
