import tkinter as tk
from tkinter import ttk, messagebox
import mysql.connector

# ========== DB Connection ==========
def connect_db():
    return mysql.connector.connect(
        host="ls-d3311d7ae41e61c25d492ef874e447d39eb24c2b.cz88m42um6aw.ca-central-1.rds.amazonaws.com",
        user="dbmasteruser",
        password="M(;+O4+>L{PM~c;tCmd)XEt]9?y9sAe{",
        database="corporate"
    )

# ========== Utility Functions ==========
def fetch_data(tree, table):
    try:
        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute(f"SHOW COLUMNS FROM {table}")
        cols = [col[0] for col in cursor.fetchall()]

        if tree:
            cursor.execute(f"SELECT * FROM {table}")
            rows = cursor.fetchall()
            tree.delete(*tree.get_children())
            for row in rows:
                tree.insert("", tk.END, values=row)

        conn.close()
        return cols
    except Exception as e:
        messagebox.showerror("DB Error", str(e))
        return []
