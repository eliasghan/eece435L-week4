import os
import sqlite3

from flask import Flask, jsonify, request
from flask_cors import CORS

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "database.db")


def connect_to_db():
    conn = sqlite3.connect(DB_PATH)
    return conn


def create_db_table():
    conn = None
    try:
        conn = connect_to_db()
        conn.execute('''
            CREATE TABLE users (
                user_id INTEGER PRIMARY KEY NOT NULL,
                name TEXT NOT NULL,
                email TEXT NOT NULL,
                phone TEXT NOT NULL,
                address TEXT NOT NULL,
                country TEXT NOT NULL
            );
        ''')
        conn.commit()
        print("User table created successfully")
    except sqlite3.Error:
        print("User table creation failed - Maybe table already exists")
    finally:
        if conn is not None:
            conn.close()


def insert_user(user):
    inserted_user = {}
    conn = None
    try:
        conn = connect_to_db()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO users (name, email, phone, address, country) VALUES (?, ?, ?, ?, ?)",
            (user["name"], user["email"], user["phone"], user["address"], user["country"]),
        )
        conn.commit()
        inserted_user = get_user_by_id(cur.lastrowid)
    except (sqlite3.Error, KeyError, TypeError):
        if conn is not None:
            conn.rollback()
    finally:
        if conn is not None:
            conn.close()
    return inserted_user


def row_to_user(row):
    return {
        "user_id": row["user_id"],
        "name": row["name"],
        "email": row["email"],
        "phone": row["phone"],
        "address": row["address"],
        "country": row["country"],
    }


def get_users():
    users = []
    conn = None
    try:
        conn = connect_to_db()
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute("SELECT * FROM users")
        users = [row_to_user(row) for row in cur.fetchall()]
    except sqlite3.Error:
        users = []
    finally:
        if conn is not None:
            conn.close()
    return users


def get_user_by_id(user_id):
    user = {}
    conn = None
    try:
        conn = connect_to_db()
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
        row = cur.fetchone()
        if row is not None:
            user = row_to_user(row)
    except sqlite3.Error:
        user = {}
    finally:
        if conn is not None:
            conn.close()
    return user


def update_user(user):
    updated_user = {}
    conn = None
    try:
        conn = connect_to_db()
        cur = conn.cursor()
        cur.execute(
            "UPDATE users SET name = ?, email = ?, phone = ?, address = ?, country = ? "
            "WHERE user_id = ?",
            (user["name"], user["email"], user["phone"], user["address"],
             user["country"], user["user_id"]),
        )
        conn.commit()
        updated_user = get_user_by_id(user["user_id"])
    except (sqlite3.Error, KeyError, TypeError):
        if conn is not None:
            conn.rollback()
        updated_user = {}
    finally:
        if conn is not None:
            conn.close()
    return updated_user


def delete_user(user_id):
    message = {}
    conn = None
    try:
        conn = connect_to_db()
        cur = conn.execute("DELETE FROM users WHERE user_id = ?", (user_id,))
        conn.commit()
        if cur.rowcount:
            message["status"] = "User deleted successfully"
        else:
            message["status"] = "Cannot delete user"
    except sqlite3.Error:
        if conn is not None:
            conn.rollback()
        message["status"] = "Cannot delete user"
    finally:
        if conn is not None:
            conn.close()
    return message


app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})


@app.route("/api/users", methods=["GET"])
def api_get_users():
    return jsonify(get_users())


@app.route("/api/users/<user_id>", methods=["GET"])
def api_get_user(user_id):
    return jsonify(get_user_by_id(user_id))


@app.route("/api/users/add", methods=["POST"])
def api_add_user():
    user = request.get_json()
    return jsonify(insert_user(user))


@app.route("/api/users/update", methods=["PUT"])
def api_update_user():
    user = request.get_json()
    return jsonify(update_user(user))


@app.route("/api/users/delete/<user_id>", methods=["DELETE"])
def api_delete_user(user_id):
    return jsonify(delete_user(user_id))


if __name__ == "__main__":
    create_db_table()
    app.run()
