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
    form.geometry("400x600")
    
    # Create a canvas with scrollbar
    canvas = tk.Canvas(form)
    scrollbar = ttk.Scrollbar(form, orient="vertical", command=canvas.yview)
    scrollable_frame = ttk.Frame(canvas)

    scrollable_frame.bind(
        "<Configure>",
        lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
    )

    canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)

    entries = []
    
    for idx, col in enumerate(columns):
        if not data and col in ['Maintenance_ID']:  # Skip auto-increment fields for new entries
            continue
        
        label = tk.Label(scrollable_frame, text=col)
        label.pack(pady=2)
        
        if col == 'Vehicle_ID':  # Create dropdown for Vehicle selection
            conn = connect_db()
            cursor = conn.cursor()
            cursor.execute("SELECT Vehicle_ID FROM Vehicle")
            vehicle_ids = [str(vid[0]) for vid in cursor.fetchall()]
            conn.close()
            
            var = tk.StringVar(value=data[idx] if data else "")
            combo = ttk.Combobox(scrollable_frame, values=vehicle_ids, textvariable=var)
            combo.pack(pady=2)
            entries.append((col, var))
            
        elif col == 'Service_Provider_ID':  # Create dropdown for Service Provider selection
            conn = connect_db()
            cursor = conn.cursor()
            cursor.execute("SELECT Service_Provider_ID FROM Service_Provider")
            provider_ids = [str(pid[0]) for pid in cursor.fetchall()]
            conn.close()
            
            var = tk.StringVar(value=data[idx] if data else "")
            combo = ttk.Combobox(scrollable_frame, values=provider_ids, textvariable=var)
            combo.pack(pady=2)
            entries.append((col, var))
            
        else:
            var = tk.StringVar(value=data[idx] if data else "")
            entry = tk.Entry(scrollable_frame, textvariable=var)
            entry.pack(pady=2)
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

    tk.Button(scrollable_frame, text="Save", command=save).pack(pady=10)

    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

def delete_selected(table, tree):
    selected = tree.selection()
    if not selected:
        messagebox.showinfo("Delete", "Select a record first.")
        return
    
    if messagebox.askyesno("Confirm Delete", "Are you sure you want to delete this record?"):
        try:
            conn = connect_db()
            cursor = conn.cursor()
            item = tree.item(selected[0])
            record_id = item["values"][0]
            cursor.execute(f"DELETE FROM {table} WHERE {tree['columns'][0]}=%s", (record_id,))
            conn.commit()
            conn.close()
            fetch_data(tree, table)
        except Exception as e:
            messagebox.showerror("Delete Error", str(e))


    # Pack the canvas and scrollbar
    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")


