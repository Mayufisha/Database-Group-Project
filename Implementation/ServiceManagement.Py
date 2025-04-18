import os
from dotenv import load_dotenv
import tkinter as tk
from tkinter import ttk, messagebox
import mysql.connector

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
def add_edit_form(table, columns, tree, data=None):
    form = tk.Toplevel()
    form.title("Edit" if data else "Add")
    form.geometry("400x600")
    
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
        if not data and col in ['Service_Provider_ID', 'Service_Status_ID']:
            continue
        
        label = tk.Label(scrollable_frame, text=col)
        label.pack(pady=2)
        
        if col == 'Vehicle_ID':
            conn = connect_db()
            cursor = conn.cursor()
            cursor.execute("SELECT Vehicle_ID FROM Vehicle")
            vehicle_ids = [str(vid[0]) for vid in cursor.fetchall()]
            conn.close()
            
            var = tk.StringVar(value=data[idx] if data else "")
            combo = ttk.Combobox(scrollable_frame, values=vehicle_ids, textvariable=var)
            combo.pack(pady=2)
            entries.append((col, var))
            
        elif col == 'Status_ID':
            conn = connect_db()
            cursor = conn.cursor()
            cursor.execute("SELECT Service_Status_ID FROM Service_Status")
            status_ids = [str(sid[0]) for sid in cursor.fetchall()]
            conn.close()
            
            var = tk.StringVar(value=data[idx] if data else "")
            combo = ttk.Combobox(scrollable_frame, values=status_ids, textvariable=var)
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
root = tk.Tk()
root.title("Service Management Portal")
root.geometry("1200x800")

notebook = ttk.Notebook(root)
notebook.pack(expand=True, fill="both")

service_tab = ttk.Frame(notebook)
notebook.add(service_tab, text="Service Management")

tables = {
    "Service_Provider": "Service Providers",
    "Service_Status": "Service Status",
    "Service_Provider_Address": "Provider Addresses"
}

sub_notebook = ttk.Notebook(service_tab)
sub_notebook.pack(expand=True, fill="both")

for table, label in tables.items():
    tab = ttk.Frame(sub_notebook)
    sub_notebook.add(tab, text=label)

    # Search Frame
    search_frame = ttk.Frame(tab)
    search_frame.pack(fill="x", padx=10, pady=5)

    tk.Label(search_frame, text=f"Search {label} by:").pack(side="left")
    cols = fetch_data(None, table)
    search_option = ttk.Combobox(search_frame, values=cols, state="readonly")
    search_option.set(cols[0])
    search_option.pack(side="left", padx=5)

    search_entry = tk.Entry(search_frame)
    search_entry.pack(side="left", padx=5)

    # Tree Frame
    tree_frame = ttk.Frame(tab)
    tree_frame.pack(expand=True, fill="both", padx=10, pady=5)

    tree = ttk.Treeview(tree_frame, columns=cols, show="headings")
    vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=tree.yview)
    hsb = ttk.Scrollbar(tree_frame, orient="horizontal", command=tree.xview)
    tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

    tree.grid(row=0, column=0, sticky="nsew")
    vsb.grid(row=0, column=1, sticky="ns")
    hsb.grid(row=1, column=0, sticky="ew")

    tree_frame.columnconfigure(0, weight=1)
    tree_frame.rowconfigure(0, weight=1)

    for col in cols:
        tree.heading(col, text=col)
        tree.column(col, anchor="center", width=100)

    fetch_data(tree, table)

    # Buttons
    ttk.Button(search_frame, text="Search",
               command=lambda t=tree, tbl=table, s=search_option, e=search_entry: 
               search_data(t, tbl, s.get(), e.get())).pack(side="left")

    ttk.Button(search_frame, text="Clear",
               command=lambda t=tree, tbl=table: [search_entry.delete(0, tk.END), 
               fetch_data(t, tbl)]).pack(side="left", padx=5)

    action_frame = ttk.Frame(tab)
    action_frame.pack(pady=10)

    ttk.Button(action_frame, text="Add", 
               command=lambda t=tree, tbl=table, c=cols: add_edit_form(tbl, c, t)).pack(side="left", padx=5)

    ttk.Button(action_frame, text="Edit", 
               command=lambda t=tree, tbl=table, c=cols: 
               add_edit_form(tbl, c, t, t.item(t.selection()[0])["values"] 
               if t.selection() else None)).pack(side="left", padx=5)

    ttk.Button(action_frame, text="Delete", 
               command=lambda t=tree, tbl=table: delete_selected(tbl, t)).pack(side="left", padx=5)

root.mainloop()


