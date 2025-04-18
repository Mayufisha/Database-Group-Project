import os
from dotenv import load_dotenv
import tkinter as tk
from tkinter import ttk, messagebox
import mysql.connector

# ========== DB Connection ==========
# load files variables from .env
load_dotenv()


# Access the environment variables
db_host = os.getenv("MYSQL_HOST")
db_port = os.getenv("MYSQL_PORT")
db_name = os.getenv("MYSQL_DATABASE")
db_user = os.getenv("MYSQL_USER")
db_password = os.getenv("MYSQL_PASSWORD")

def connect_db():
    return mysql.connector.connect(
        host=db_host,
        port=db_port,
        user=db_user,
        password=db_password,
        database=db_name
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

def search_data(tree, table, column, value):
    try:
        conn = connect_db()
        cursor = conn.cursor()
        query = f"SELECT * FROM {table} WHERE {column} LIKE %s"
        cursor.execute(query, (f"%{value}%",))
        rows = cursor.fetchall()
        tree.delete(*tree.get_children())
        for row in rows:
            tree.insert("", tk.END, values=row)
        conn.close()
    except Exception as e:
        messagebox.showerror("Search Error", str(e))

# ========== UI Setup ==========
root = tk.Tk()
root.title("Local-User Portal")
root.geometry("1200x800")

notebook = ttk.Notebook(root)
notebook.pack(fill="both", expand=True)

tables = {
    "Customer": "Customers",
    "Driver": "Drivers",
    "Vehicle": "Vehicles",
    "Vehicle_Type": "Vehicle Types",
    "Fuel_Type": "Fuel Types",
    "Delivery_Status": "Deliveries",
    "Maintenance": "Maintenance",
    "Service_Provider": "Service Providers"
}
treeviews = {}

for table, label in tables.items():
    tab = ttk.Frame(notebook)
    notebook.add(tab, text=label)

    search_frame = ttk.Frame(tab)
    search_frame.pack(fill="x", padx=10, pady=5)

    tk.Label(search_frame, text=f"Search {label} by:").pack(side="left")
    columns = fetch_data(None, table)
    col_selector = ttk.Combobox(search_frame, values=columns, state="readonly")
    col_selector.set(columns[0])
    col_selector.pack(side="left", padx=5)

    search_entry = tk.Entry(search_frame)
    search_entry.pack(side="left", padx=5)

    tree = ttk.Treeview(tab, columns=columns, show="headings")
    for col in columns:
        tree.heading(col, text=col)
        tree.column(col, anchor=tk.CENTER)
    tree.pack(expand=True, fill="both", padx=10, pady=10)

    search_button = ttk.Button(
        search_frame,
        text="Search",
        command=lambda t=tree, tbl=table, cs=col_selector, se=search_entry: search_data(t, tbl, cs.get(), se.get())
    )
    search_button.pack(side="left")

    refresh_button = ttk.Button(
        search_frame,
        text="Refresh",
        command=lambda t=tree, tbl=table, se=search_entry: [
            se.delete(0, tk.END),  # Clear the search field
            fetch_data(t, tbl)     # Reload the full table
        ]
    )
    refresh_button.pack(side="left", padx=5)


    fetch_data(tree, table)
    treeviews[table] = tree

# ========== Run ==========
root.mainloop()
