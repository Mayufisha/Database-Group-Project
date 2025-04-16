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


    #    editable_fields = columns["Vehicle", "Vehicle_Type", "Vehicle_Status_Type", "Vehicle_Load", "Fuel_Type",
    # "Driver", "Driver_Address", "Driver_Qualification", "Emergency_Contact", "Vehicle_Driver_Assignment",
    # "Customer", "Customer_Address", "Load_Customer",
    # "Delivery_Status",
    # "Cargo", "Cargo_Type",
    # "Maintenance", "Maintenance_Type",
    # "Service_Provider", "Service_Provider_Address", "Service_Status",
    # "Location", "Address"]

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

# === UI ===
root = tk.Tk()
root.title("Admins Portal")
root.geometry("1200x800")

notebook = ttk.Notebook(root)
notebook.pack(expand=True, fill="both")

# vehicle_mgmt_tab = ttk.Frame(notebook)
# notebook.add(vehicle_mgmt_tab, text="Vehicle Management")
#
# sub_notebook = ttk.Notebook(vehicle_mgmt_tab)
# sub_notebook.pack(expand=True, fill="both")

sections = {
    "Vehicle Management" : [
         "Vehicle",
         "Vehicle_Type",
         "Vehicle_Status_Type",
         "Vehicle_Load",
        "Fuel_Type"
    ],
    "Driver Management": [
        "Driver",
        "Driver_Address",
        "Driver_Qualification",
        "Emergency_Contact",
        "Vehicle_Driver_Assignment"
    ],
    "Customer Management": [
        "Customer",
        "Customer_Address",
        "Load_Customer"
    ],
    "Delivery Management" : [
        "Delivery_Status"
    ],
    "Cargo Management": [
        "Cargo",
        "Cargo_Type"
    ],
    "Maintenance Management": [
        "Maintenance",
        "Maintenance_Type"
    ],
    "Service Management": [
        "Service_Provider",
        "Service_Provider_Address",
        "Service_Status"
    ],
    "Address Management": [
        "Location",
        "Address"
    ]
}

for section_name, tables in sections.items():
    section_tab = ttk.Frame(notebook)
    notebook.add(section_tab, text=section_name)

    sub_notebook = ttk.Notebook(section_tab)
    sub_notebook.pack(expand=True, fill="both")

    for table in tables:
        label = table.replace("_", " ").title()
        tab = ttk.Frame(sub_notebook)
        sub_notebook.add(tab, text=label)

        search_frame = ttk.Frame(tab)
        search_frame.pack(fill="x", padx=10, pady=5)

        tk.Label(search_frame, text=f"Search {label} by:").pack(side="left")
        cols = fetch_data(None, table)
        search_option = ttk.Combobox(search_frame, values=cols, state="readonly")
        search_option.set(cols[0])
        search_option.pack(side="left", padx=5)

        search_entry = tk.Entry(search_frame)
        search_entry.pack(side="left", padx=5)

        # Frame to hold treeview and scrollbars
        tree_frame = ttk.Frame(tab)
        tree_frame.pack(expand=True, fill="both", padx=10, pady=5)

        # Treeview widget
        tree = ttk.Treeview(tree_frame, columns=cols, show="headings")

        # Scrollbars
        vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=tree.yview)
        hsb = ttk.Scrollbar(tree_frame, orient="horizontal", command=tree.xview)
        tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        # Positioning using grid
        tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")

        # Allow stretch
        tree_frame.columnconfigure(0, weight=1)
        tree_frame.rowconfigure(0, weight=1)

        # Add column headings
        for col in cols:
            tree.heading(col, text=col)
            tree.column(col, anchor="center")

        fetch_data(tree, table)

        ttk.Button(search_frame, text="Search",
                   command=lambda t=tree, tbl=table, s=search_option, e=search_entry: search_data(t, tbl, s.get(),
                                                                                                  e.get())).pack(
            side="left")

        ttk.Button(search_frame, text="Clear",
               command=lambda t=tree, tbl=table: [search_entry.delete(0, tk.END), fetch_data(t, tbl)]).pack(side="left",
                                                                                                            padx=5)

    action_frame = ttk.Frame(tab)
    action_frame.pack(pady=10)

    ttk.Button(action_frame, text="Add", command=lambda t=tree, tbl=table, c=cols: add_edit_form(tbl, c, t)).pack(
        side="left", padx=5)

    def edit_wrapper(t=tree, tbl=table, c=cols):
        selected = t.selection()
        if not selected:
            messagebox.showinfo("Edit", "Select a record first.")
            return
        data = t.item(selected[0], "values")
        add_edit_form(tbl, c, t, data)

    ttk.Button(action_frame, text="Edit", command=edit_wrapper).pack(side="left", padx=5)
    ttk.Button(action_frame, text="Delete", command=lambda t=tree, tbl=table: delete_selected(tbl, t)).pack(side="left", padx=5)

root.mainloop()