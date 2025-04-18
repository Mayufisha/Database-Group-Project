import os
import tkinter as tk
from tkinter import ttk, messagebox
import threading
from dotenv import load_dotenv
import database_connection as db

# Load environment variables
load_dotenv()

# Global variables for tracking loaded tabs
loaded_tabs = {}

def populate_tree(tree, data):
    """Populate treeview with data"""
    tree.delete(*tree.get_children())
    for row in data:
        tree.insert("", tk.END, values=row)

def lazy_load_tab(notebook, tab_id, table):
    """Load data for a tab when it's selected"""
    if tab_id not in loaded_tabs:
        # Get the tab widget from notebook
        tab = notebook.nametowidget(tab_id)
        # Find treeview in the tab's children recursively
        for child in tab.winfo_children():
            if isinstance(child, ttk.Frame) and "tree_frame" in str(child):
                for subchild in child.winfo_children():
                    if isinstance(subchild, ttk.Treeview):
                        tree = subchild
                        # Fetch data in a separate thread to avoid freezing UI
                        threading.Thread(
                            target=lambda: fetch_and_update_tree(tree, table),
                            daemon=True
                        ).start()
                        break
        # Mark tab as loaded
        loaded_tabs[tab_id] = True

def fetch_and_update_tree(tree, table, search_params=None):
    """Fetch data and update treeview in a non-blocking way"""
    try:
        if search_params:
            column, value = search_params
            rows = db.search_data(table, column, value)
        else:
            rows, _ = db.fetch_data_paginated(table)
        
        # Update UI in the main thread
        tree.after(0, lambda: populate_tree(tree, rows))
    except Exception as e:
        tree.after(0, lambda: messagebox.showerror("Data Error", str(e)))

def setup_tree_for_table(tab, table):
    """Setup treeview with proper columns for a table"""
    # Fetch columns once (using cache)
    cols = db.get_table_columns(table)
    
    # Setup search frame
    search_frame = ttk.Frame(tab)
    search_frame.pack(fill="x", padx=10, pady=5)
    
    label = table.replace("_", " ").title()
    tk.Label(search_frame, text=f"Search {label} by:").pack(side="left")
    
    search_option = ttk.Combobox(search_frame, values=cols, state="readonly")
    if cols:
        search_option.set(cols[0])
    search_option.pack(side="left", padx=5)
    
    search_entry = tk.Entry(search_frame)
    search_entry.pack(side="left", padx=5)
    
    # Create tree frame with scrollbars
    tree_frame = ttk.Frame(tab, name="tree_frame")
    tree_frame.pack(expand=True, fill="both", padx=10, pady=5)
    
    tree = ttk.Treeview(tree_frame, columns=cols, show="headings")
    
    # Scrollbars
    vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=tree.yview)
    hsb = ttk.Scrollbar(tree_frame, orient="horizontal", command=tree.xview)
    tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
    
    # Grid layout
    tree.grid(row=0, column=0, sticky="nsew")
    vsb.grid(row=0, column=1, sticky="ns")
    hsb.grid(row=1, column=0, sticky="ew")
    
    # Configure grid weights
    tree_frame.columnconfigure(0, weight=1)
    tree_frame.rowconfigure(0, weight=1)
    
    # Configure columns
    for col in cols:
        tree.heading(col, text=col)
        tree.column(col, anchor="center", width=100)
    
    # Add search buttons
    ttk.Button(
        search_frame, 
        text="Search",
        command=lambda t=tree, tbl=table, s=search_option, e=search_entry: 
            fetch_and_update_tree(t, tbl, (s.get(), e.get()))
    ).pack(side="left")
    
    ttk.Button(
        search_frame, 
        text="Clear",
        command=lambda t=tree, tbl=table, e=search_entry: 
            [e.delete(0, tk.END), fetch_and_update_tree(t, tbl)]
    ).pack(side="left", padx=5)
    
    # Add action buttons
    action_frame = ttk.Frame(tab)
    action_frame.pack(pady=10)
    
    ttk.Button(
        action_frame, 
        text="Add",
        command=lambda t=tree, tbl=table, c=cols: 
            add_edit_form(tbl, c, t)
    ).pack(side="left", padx=5)
    
    ttk.Button(
        action_frame, 
        text="Edit",
        command=lambda t=tree, tbl=table, c=cols: 
            edit_selected(t, tbl, c)
    ).pack(side="left", padx=5)
    
    ttk.Button(
        action_frame, 
        text="Delete",
        command=lambda t=tree, tbl=table: 
            delete_selected(t, tbl)
    ).pack(side="left", padx=5)
    
    return tree

def add_edit_form(table, columns, tree, data=None):
    """Create form for adding or editing data"""
    form = tk.Toplevel()
    form.title("Edit" if data else "Add")
    form.geometry("400x400")
    
    # Create scrollable canvas for forms with many fields
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
    
    editable_fields = columns
    if table in ["Vehicle_Type", "Vehicle_Status_Type", "Fuel_Type", "Cargo_Type"]:
        editable_fields = columns[1:3] if len(columns) >= 3 else columns[1:]
    
    for idx, col in enumerate(columns):
        # Skip auto-increment fields for new records
        if not data and col.endswith('_ID') and col == columns[0]:
            continue
            
        tk.Label(scrollable_frame, text=col).pack(pady=2)
        
        # For foreign keys, create dropdowns
        if col.endswith('_ID') and col != columns[0]:
            # Extract base table name from field
            referenced_table = col.replace('_ID', '')
            try:
                # Fetch foreign key values
                ref_data = db.execute_query(f"SELECT {col} FROM {referenced_table}")
                ref_values = [str(item[0]) for item in ref_data] if ref_data else []
                
                var = tk.StringVar(value=data[idx] if data else "")
                combo = ttk.Combobox(scrollable_frame, values=ref_values, textvariable=var)
                combo.pack(pady=2)
                entries.append((col, var))
            except:
                # Fallback to regular input if foreign key lookup fails
                var = tk.StringVar(value=data[idx] if data else "")
                entry = tk.Entry(scrollable_frame, textvariable=var)
                entry.pack(pady=2)
                entries.append((col, var))
        else:
            var = tk.StringVar(value=data[idx] if data else "")
            entry = tk.Entry(scrollable_frame, textvariable=var)
            entry.pack(pady=2)
            entries.append((col, var))
    
    def save():
        values = [v.get() for _, v in entries]
        try:
            if data:
                # Update existing record
                update_columns = [col for col, _ in entries[1:]]
                db.update_data(table, update_columns, values[1:], entries[0][0], values[0])
            else:
                # Insert new record
                insert_columns = [col for col, _ in entries]
                db.insert_data(table, insert_columns, values)
                
            # Refresh the tree
            fetch_and_update_tree(tree, table)
            form.destroy()
        except Exception as e:
            messagebox.showerror("Error", str(e))
    
    tk.Button(scrollable_frame, text="Save", command=save).pack(pady=10)
    
    # Pack canvas and scrollbar
    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

def edit_selected(tree, table, cols):
    """Edit the selected record"""
    selected = tree.selection()
    if not selected:
        messagebox.showinfo("Edit", "Select a record first.")
        return
    
    data = tree.item(selected[0], "values")
    add_edit_form(table, cols, tree, data)

def delete_selected(tree, table):
    """Delete the selected record"""
    selected = tree.selection()
    if not selected:
        messagebox.showinfo("Delete", "Select a record first.")
        return
    
    if messagebox.askyesno("Confirm Delete", "Are you sure you want to delete this record?"):
        try:
            item = tree.item(selected[0])
            record_id = item["values"][0]
            id_column = tree["columns"][0]
            
            db.delete_data(table, id_column, record_id)
            fetch_and_update_tree(tree, table)
        except Exception as e:
            messagebox.showerror("Delete Error", str(e))

# === UI Setup ===
def create_ui():
    root = tk.Tk()
    root.title("Admin Portal")
    root.geometry("1200x800")
    
    # Show a loading message
    loading_label = tk.Label(root, text="Initializing...", font=("Arial", 16))
    loading_label.pack(expand=True)
    
    # Create the UI in a separate thread to keep the window responsive
    threading.Thread(target=lambda: setup_ui(root, loading_label), daemon=True).start()
    
    root.mainloop()

def setup_ui(root, loading_label):
    # Initialize main notebook
    notebook = ttk.Notebook(root)
    
    # Define sections with their tables
    sections = {
        "Vehicle Management": [
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
        "Delivery Management": [
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
    
    # Setup tabs for each section
    for section_name, tables in sections.items():
        section_tab = ttk.Frame(notebook)
        notebook.add(section_tab, text=section_name)
        
        sub_notebook = ttk.Notebook(section_tab)
        sub_notebook.pack(expand=True, fill="both")
        
        # Setup tabs for each table in the section
        for table in tables:
            label = table.replace("_", " ").title()
            tab = ttk.Frame(sub_notebook)
            sub_notebook.add(tab, text=label)
            
            # Just set up the UI structure, don't load data yet
            setup_tree_for_table(tab, table)
            
            # Store the tab id for lazy loading
            tab_id = sub_notebook.tabs()[-1]
            
        # Add callback for tab selection to implement lazy loading
        sub_notebook.bind("<<NotebookTabChanged>>", 
                         lambda event, nb=sub_notebook, tables=tables: 
                             tab_selected(event, nb, tables))
    
    # Add callback for main notebook tab selection
    notebook.bind("<<NotebookTabChanged>>", 
                 lambda event, nb=notebook: 
                     main_tab_selected(event, nb, sections))
    
    # Remove loading label and show the UI
    root.after(0, loading_label.destroy)
    root.after(0, lambda: notebook.pack(expand=True, fill="both"))

def tab_selected(event, notebook, tables):
    """Callback for when a tab is selected"""
    selected_tab = notebook.select()
    if selected_tab:
        tab_index = notebook.index(selected_tab)
        if tab_index < len(tables):
            table = tables[tab_index]
            lazy_load_tab(notebook, selected_tab, table)

def main_tab_selected(event, notebook, sections):
    """Callback for when a main tab is selected"""
    selected_tab = notebook.select()
    if selected_tab:
        # Just ensure the tab exists, no loading yet
        # Loading happens when subtabs are selected
        pass

if __name__ == "__main__":
    create_ui()