from flask import Flask, request, render_template, jsonify, redirect, url_for
import mysql.connector

app = Flask(__name__, template_folder=r"D:\Umang_Coding\AI_chatbot\template")

try: 
    con = mysql.connector.connect(
        host="127.0.0.1",
        user="root",
        password="12345",
        database="bot"
    )
    cursor = con.cursor(dictionary=True)
    print("Connection succeed")
except mysql.connector.Error as e:
    print("Failed:", e)


@app.route("/", methods=["POST", "GET"])
def admin():
    error = request.args.get("error")
    if request.method == "POST":
        uid = request.form.get("admin_id")
        username = request.form.get("username")
        password = request.form.get("password")

        if not uid or not password:
            return redirect(url_for('admin', error="Please enter UID and Password"))

        try:
            cursor.execute("SELECT * FROM ADMIN WHERE UNIQUE_ID = %s", (uid,))
            result = cursor.fetchone()

            if result and result["PASSWORD"] == password:
                return redirect(url_for('dashboard'))
            else:
                return redirect(url_for('admin', error="Invalid credentials"))

        except mysql.connector.Error as e:
            return jsonify({"message": f"Database Error: {str(e)}"})

    return render_template("ug1.html", error=error)


@app.route("/dashboard")
def dashboard():
    return "Welcome to Dashboard!"


@app.route("/reset")
def reset():
    return render_template("registation.html")


if __name__ == "__main__":
    app.run(debug=True)
