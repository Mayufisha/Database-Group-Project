import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import csv
import database_connection as db
import logging

logger = logging.getLogger("form_utils")

def create_edit_form(parent, table, columns, tree, data=None):
    """
    Creates a reusable form for adding or editing records
    
    Args:
        parent: The parent window
        table: Database table name
        columns: List of column names
        tree: The treeview to update after save
        data: Existing data for edit mode
    """
    form = tk.Toplevel(parent)
    form.title("Edit Record" if data else "Add Record")
    form.geometry("450x500")
    form.resizable(True, True)
    
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
    
    # Determine which fields should be editable
    editable_fields = columns
    if table in ["Vehicle_Type", "Vehicle_Status_Type", "Fuel_Type", "Cargo_Type"]:
        editable_fields = columns[1:3] if len(columns) >= 3 else columns[1:]
    
    # Track which fields are dropdowns
    dropdown_vars = {}
    
    for idx, col in enumerate(columns):
        # Skip auto-increment fields for new records
        if not data and col.endswith('_ID') and col == columns[0]:
            continue
        
        # Create frame for each field (improves layout)
        field_frame = ttk.Frame(scrollable_frame)
        field_frame.pack(fill="x", padx=10, pady=5)
        
        # Label with tooltip
        label = ttk.Label(field_frame, text=col, width=20, anchor="w")
        label.pack(side="left")
        
        # For foreign keys, create dropdowns
        if col.endswith('_ID') and col != columns[0]:
            # Extract base table name from field
            referenced_table = col.replace('_ID', '')
            try:
                # Fetch foreign key values
                ref_values = []
                
                # Get display field if available (use first non-ID field)
                ref_cols = db.get_table_columns(referenced_table)
                display_field = None
                
                for ref_col in ref_cols:
                    if not ref_col.endswith('_ID') and ref_col != 'ID':
                        display_field = ref_col
                        break
                
                if display_field:
                    # Fetch ID and display values
                    ref_data = db.get_foreign_key_options(referenced_table, col, display_field)
                    ref_values = [f"{item[0]} - {item[1]}" for item in ref_data]
                    ref_dict = {f"{item[0]} - {item[1]}": item[0] for item in ref_data}
                else:
                    # Just fetch IDs
                    ref_values = [str(item) for item in db.get_foreign_key_options(referenced_table, col)]
                    ref_dict = {item: item for item in ref_values}
                
                var = tk.StringVar(value=data[idx] if data else "")
                combo = ttk.Combobox(field_frame, values=ref_values, textvariable=var, width=30)
                combo.pack(side="left", fill="x", expand=True, padx=(0, 10))
                
                # Store the mapping dictionary for retrieval during save
                dropdown_vars[col] = (var, ref_dict)
                
                entries.append((col, var))
                
            except Exception as e:
                logger.error(f"Error setting up foreign key dropdown: {e}")
                # Fallback to regular input if foreign key lookup fails
                var = tk.StringVar(value=data[idx] if data else "")
                entry = ttk.Entry(field_frame, textvariable=var, width=30)
                entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
                entries.append((col, var))
        else:
            var = tk.StringVar(value=data[idx] if data else "")
            entry = ttk.Entry(field_frame, textvariable=var, width=30)
            entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
            entries.append((col, var))
    
    def validate_and_save():
        # Get values, handling dropdown mappings
        values = []
        data_dict = {}
        
        for col, var in entries:
            if col in dropdown_vars:
                # For dropdowns, get the actual ID value from the selected display text
                selected_text = var.get()
                dropdown_dict = dropdown_vars[col][1]
                
                # If the exact ID was entered or nothing was selected
                if selected_text in dropdown_dict:
                    value = dropdown_dict[selected_text]
                else:
                    # Try to extract ID from the display text (format "ID - Name")
                    try:
                        value = int(selected_text.split(' - ')[0])
                    except:
                        value = selected_text  # Keep as is if parsing fails
                
                values.append(value)
                data_dict[col] = value
            else:
                values.append(var.get())
                data_dict[col] = var.get()
        
        # Validate data
        is_valid, error_message = db.validate_data(table, data_dict)
        
        if not is_valid:
            messagebox.showerror("Validation Error", error_message)
            return
            
        # Save data
        try:
            if data:
                # Update existing record
                update_columns = [col for col, _ in entries[1:]]
                db.update_data(table, update_columns, values[1:], entries[0][0], values[0])
                messagebox.showinfo("Success", "Record updated successfully")
            else:
                # Insert new record
                insert_columns = [col for col, _ in entries]
                db.insert_data(table, insert_columns, values)
                messagebox.showinfo("Success", "Record added successfully")
                
            # Refresh the tree
            refresh_tree(tree, table)
            form.destroy()
        except Exception as e:
            handle_db_error("save", e)
    
    # Button frame
    button_frame = ttk.Frame(scrollable_frame)
    button_frame.pack(pady=15, padx=10)
    
    ttk.Button(button_frame, text="Save", command=validate_and_save).pack(side="left", padx=5)
    ttk.Button(button_frame, text="Cancel", command=form.destroy).pack(side="left", padx=5)
    
    # Pack canvas and scrollbar
    canvas.pack(side="left", fill="both", expand=True, padx=10, pady=10)
    scrollbar.pack(side="right", fill="y")
    
    # Make form modal
    form.transient(parent)
    form.grab_set()
    
    return form

def refresh_tree(tree, table):
    """Update treeview with latest data"""
    try:
        rows, _ = db.fetch_data_paginated(table)
        tree.delete(*tree.get_children())
        for row in rows:
            tree.insert("", tk.END, values=row)
    except Exception as e:
        handle_db_error("refresh data", e)

def handle_db_error(operation, exception):
    """Better error handling with specific messages"""
    error_message = str(exception)
    
    if "foreign key constraint fails" in error_message.lower():
        messagebox.showerror(
            "Related Data Exists", 
            "Cannot delete this record because it is being used by other records."
        )
    elif "duplicate entry" in error_message.lower():
        messagebox.showerror(
            "Duplicate Record", 
            "A record with this ID or unique key already exists."
        )
    else:
        messagebox.showerror(
            f"Database Error during {operation}", 
            f"An error occurred: {error_message}"
        )
    
    # Log error
    logger.error(f"DB Error during {operation}: {error_message}")

def export_to_csv(parent, tree, table):
    """Export treeview data to CSV"""
    filename = filedialog.asksaveasfilename(
        parent=parent,
        defaultextension=".csv",
        filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
    )
    
    if not filename:
        return
    
    try:
        with open(filename, "w", newline="") as f:
            writer = csv.writer(f)
            # Write header
            columns = tree["columns"]
            writer.writerow(columns)
            
            # Write data
            for item_id in tree.get_children():
                values = tree.item(item_id)["values"]
                writer.writerow(values)
        
        messagebox.showinfo("Export Complete", f"Data exported to {filename}")
    except Exception as e:
        messagebox.showerror("Export Error", f"Failed to export data: {e}")
        logger.error(f"Export error: {e}")

def setup_tree_for_table(parent, table):
    """Setup treeview with proper columns for a table"""
    # Fetch columns
    cols = db.get_table_columns(table)
    
    # Setup search frame
    search_frame = ttk.Frame(parent)
    search_frame.pack(fill="x", padx=10, pady=5)
    
    label = table.replace("_", " ").title()
    ttk.Label(search_frame, text=f"Search {label} by:").pack(side="left")
    
    search_option = ttk.Combobox(search_frame, values=cols, state="readonly")
    if cols:
        search_option.set(cols[0])
    search_option.pack(side="left", padx=5)
    
    search_entry = ttk.Entry(search_frame)
    search_entry.pack(side="left", padx=5)
    
    # Create tree frame with scrollbars
    tree_frame = ttk.Frame(parent, name="tree_frame")
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
            search_data(t, tbl, s.get(), e.get())
    ).pack(side="left")
    
    ttk.Button(
        search_frame, 
        text="Clear",
        command=lambda t=tree, tbl=table, e=search_entry: 
            [e.delete(0, tk.END), refresh_tree(t, tbl)]
    ).pack(side="left", padx=5)
    
    # Add action buttons
    action_frame = ttk.Frame(parent)
    action_frame.pack(pady=10)
    
    ttk.Button(
        action_frame, 
        text="Add",
        command=lambda t=tree, tbl=table, c=cols: 
            create_edit_form(parent, tbl, c, t)
    ).pack(side="left", padx=5)
    
    ttk.Button(
        action_frame, 
        text="Edit",
        command=lambda t=tree, tbl=table, c=cols: 
            edit_selected(parent, t, tbl, c)
    ).pack(side="left", padx=5)
    
    ttk.Button(
        action_frame, 
        text="Delete",
        command=lambda t=tree, tbl=table: 
            delete_selected(t, tbl)
    ).pack(side="left", padx=5)
    
    ttk.Button(
        action_frame, 
        text="Export CSV",
        command=lambda t=tree, tbl=table: 
            export_to_csv(parent, t, tbl)
    ).pack(side="left", padx=5)
    
    # Initial data load
    refresh_tree(tree, table)
    
    return tree

def search_data(tree, table, column, value):
    """Search data and update treeview"""
    try:
        rows = db.search_data(table, column, value)
        tree.delete(*tree.get_children())
        for row in rows:
            tree.insert("", tk.END, values=row)
    except Exception as e:
        handle_db_error("search", e)

def edit_selected(parent, tree, table, cols):
    """Edit the selected record"""
    selected = tree.selection()
    if not selected:
        messagebox.showinfo("Edit", "Select a record first.")
        return
    
    data = tree.item(selected[0], "values")
    create_edit_form(parent, table, cols, tree, data)

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
            refresh_tree(tree, table)
        except Exception as e:
            handle_db_error("delete", e)