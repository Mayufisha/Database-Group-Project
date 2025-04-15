import tkinter as tk
from tkinter import ttk, messagebox
import mysql.connector

def connect_db():
    return mysql.connector.connect(
        host="ls-d3311d7ae41e61c25d492ef874e447d39eb24c2b.cz88m42um6aw.ca-central-1.rds.amazonaws.com",
        user="dbmasteruser",
        password="M(;+O4+>L{PM~c;tCmd)XEt]9?y9sAe{",
        database="corporate"
    )

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
        cursor.execute(f"SELECT * FROM {table} WHERE {column} LIKE %s", (f"%{value}%",))
        rows = cursor.fetchall()
        tree.delete(*tree.get_children())
        for row in rows:
            tree.insert("", tk.END, values=row)
        conn.close()
    except Exception as e:
        messagebox.showerror("Search Error", str(e))

def add_edit_form(table, columns, tree, data=None):
    form = tk.Toplevel()
    form.title("Edit" if data else "Add")
    form.geometry("400x400")
    entries = []

    editable_fields = columns
    if table in ["Vehicle_Type", "Vehicle_Status_Type", "Fuel_Type"]:
        editable_fields = columns[1:3] if len(columns) >= 3 else columns[1:]

    for idx, col in enumerate(columns):
        if col not in editable_fields and not data:
            continue
        tk.Label(form, text=col).pack()
        var = tk.StringVar(value=data[idx] if data else "")
        ent = tk.Entry(form, textvariable=var)
        ent.pack()
        entries.append((col, var))

    def save():
        values = [v.get() for _, v in entries]
        try:
            conn = connect_db()
            cursor = conn.cursor()
            if data:
                set_clause = ", ".join([f"{col}=%s" for col, _ in entries[1:]])
                cursor.execute(f"UPDATE {table} SET {set_clause} WHERE {entries[0][0]}=%s", values[1:] + [values[0]])
            else:
                col_clause = ", ".join([col for col, _ in entries])
                q_clause = ", ".join(["%s"] * len(entries))
                cursor.execute(f"INSERT INTO {table} ({col_clause}) VALUES ({q_clause})", values)
            conn.commit()
            conn.close()
            fetch_data(tree, table)
            form.destroy()
        except Exception as e:
            messagebox.showerror("Error", str(e))

    tk.Button(form, text="Save", command=save).pack(pady=10)

def delete_selected(table, tree):
    selected = tree.selection()
    if not selected:
        messagebox.showinfo("Delete", "Select a record first.")
        return
    item = tree.item(selected[0])
    record_id = item["values"][0]
    try:
        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute(f"DELETE FROM {table} WHERE {tree['columns'][0]}=%s", (record_id,))
        conn.commit()
        conn.close()
        fetch_data(tree, table)
    except Exception as e:
        messagebox.showerror("Delete Error", str(e))