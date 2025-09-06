from flask import Flask, render_template, request, jsonify, redirect, url_for
import mysql.connector
from werkzeug.security import generate_password_hash, check_password_hash
app = Flask(__name__, template_folder=r"D:\Umang_Coding\AI_chatbot\template")

#  MySQL connection
try: 
    con = mysql.connector.connect(
        host="127.0.0.1",
        user="root",
        password="12345",
        database="bot"
    )
    cursor = con.cursor()
    print("Connection succeed")
except mysql.connector.Error as e:
    print("Failed:", e)

# 🔹 Serve Login page
@app.route("/")
def home():
    return render_template("ug1.html")  # Your login page

# 🔹 Serve Registration page
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        full_name = request.form.get("full_name")
        email = request.form.get("email")
        user_id = request.form.get("user_id")
        password = request.form.get("password")
        confirm_password = request.form.get("confirm_password")

        # Check required fields
        if not full_name or not email or not user_id or not password or not confirm_password:
            return jsonify({"message": "All fields are required!"})

        # Check password match
        if password != confirm_password:
            return jsonify({"message": "Passwords do not match!"})

        # Hash the password
        hashed_password = generate_password_hash(password)

        # Insert into DB
        try:
            cursor.execute(
                "INSERT INTO USER (USER_ID, FULL_NAME, EMAIL, PASSWORD) VALUES (%s, %s, %s, %s)",
                (user_id, full_name, email, hashed_password)
            )
            con.commit()
            return jsonify({"message": f"User {user_id} registered successfully!"})
        except mysql.connector.Error as e:
            return jsonify({"message": f"Database Error: {str(e)}"})
    
    # GET request -> render registration page
    return render_template("registation.html")

# 🔹 Login form submit
@app.route("/login", methods=["POST"])
def login():
    user = request.form.get("user_id")
    password = request.form.get("password")

    if not user or not password:
        return jsonify({"message": "User ID and Password required!"})

    try:
        cursor.execute("SELECT PASSWORD FROM USER WHERE USER_ID=%s", (user,))
        result = cursor.fetchone()
        if result and check_password_hash(result[0], password):
            return jsonify({"message": f"Welcome {user}!"})
        else:
            return jsonify({"message": "Invalid credentials!"})
    except mysql.connector.Error as e:
        return jsonify({"message": f"Database Error: {str(e)}"})


if __name__ == "__main__":
    app.run(debug=True)
