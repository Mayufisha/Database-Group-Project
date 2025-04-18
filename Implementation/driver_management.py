import os
import return_to_admin

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import logging
from dotenv import load_dotenv
import mysql.connector
import threading
import csv
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("fleet_management.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("driver_management")

# Load environment variables
load_dotenv()

# Access the environment variables
db_host = os.getenv("MYSQL_HOST")
db_port = os.getenv("MYSQL_PORT")
db_name = os.getenv("MYSQL_DATABASE")
db_user = os.getenv("MYSQL_USER")
db_password = os.getenv("MYSQL_PASSWORD")

def connect_db():
    """Create a database connection"""
    return mysql.connector.connect(
        host=db_host,
        port=db_port,
        user=db_user,
        password=db_password,
        database=db_name
    )

def fetch_data(tree, table):
    """Fetch data from a table and populate treeview"""
    try:
        conn = connect_db()
        cursor = conn.cursor()
        
        # Get columns
        cursor.execute(f"SHOW COLUMNS FROM {table}")
        cols = [col[0] for col in cursor.fetchall()]
        
        if tree:
            # Get data
            cursor.execute(f"SELECT * FROM {table}")
            rows = cursor.fetchall()
            
            # Clear existing data
            tree.delete(*tree.get_children())
            
            # Add new data
            for row in rows:
                tree.insert("", tk.END, values=row)
                
        conn.close()
        return cols
    except Exception as e:
        logger.error(f"Database error in fetch_data: {e}")
        messagebox.showerror("Database Error", str(e))
        return []

def search_data(tree, table, column, value):
    """Search for specific data in a table"""
    try:
        conn = connect_db()
        cursor = conn.cursor()
        
        # Execute search query
        query = f"SELECT * FROM {table} WHERE {column} LIKE %s"
        cursor.execute(query, (f"%{value}%",))
        
        rows = cursor.fetchall()
        
        # Clear existing data
        tree.delete(*tree.get_children())
        
        # Add search results
        for row in rows:
            tree.insert("", tk.END, values=row)
            
        conn.close()
        
        # Return number of results
        return len(rows)
    except Exception as e:
        logger.error(f"Search error: {e}")
        messagebox.showerror("Search Error", str(e))
        return 0

def add_edit_form(table, columns, tree, data=None):
    """Create form for adding or editing data"""
    form = tk.Toplevel()
    form.title("Edit" if data else "Add")
    form.geometry("450x600")
    
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
    
    # Determine which fields are editable
    editable_fields = columns
    
    # Dictionary to store references to dropdown variables and their mappings
    dropdown_vars = {}
    
    for idx, col in enumerate(columns):
        # Skip auto-increment fields for new records
        if not data and col.endswith('_ID') and col == columns[0]:
            continue
            
        # Create a frame for each field (improves layout)
        field_frame = ttk.Frame(scrollable_frame)
        field_frame.pack(fill="x", padx=10, pady=5)
        
        # Label
        ttk.Label(field_frame, text=col, width=20, anchor="w").pack(side="left")
        
        # For foreign keys, create dropdowns
        if col.endswith('_ID') and col != columns[0]:
            # Extract base table name from field
            referenced_table = col.replace('_ID', '')
            try:
                # Fetch foreign key values
                conn = connect_db()
                cursor = conn.cursor()
                
                # Get display field if available (use first non-ID field)
                cursor.execute(f"SHOW COLUMNS FROM {referenced_table}")
                ref_cols = [c[0] for c in cursor.fetchall()]
                display_field = None
                
                for ref_col in ref_cols:
                    if not ref_col.endswith('_ID') and ref_col != 'ID':
                        display_field = ref_col
                        break
                
                if display_field:
                    # Fetch ID and display values
                    cursor.execute(f"SELECT {col}, {display_field} FROM {referenced_table}")
                    ref_data = cursor.fetchall()
                    ref_values = [f"{item[0]} - {item[1]}" for item in ref_data]
                    ref_dict = {f"{item[0]} - {item[1]}": item[0] for item in ref_data}
                else:
                    # Just fetch IDs
                    cursor.execute(f"SELECT {col} FROM {referenced_table}")
                    ref_data = cursor.fetchall()
                    ref_values = [str(item[0]) for item in ref_data]
                    ref_dict = {str(item[0]): item[0] for item in ref_values}
                
                conn.close()
                
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
    
    def validate_form():
        """Validate form data"""
        # Simple validation - check required fields
        for col, var in entries:
            if col != columns[0] and not var.get() and 'ID' not in col:
                return False, f"{col} is required"
        
        return True, ""
    
    def save():
        """Save the data"""
        # Validate form
        valid, error_message = validate_form()
        if not valid:
            messagebox.showerror("Validation Error", error_message)
            return
        
        # Get values, handling dropdown mappings
        values = []
        
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
            else:
                values.append(var.get())
        
        try:
            conn = connect_db()
            cursor = conn.cursor()
            
            if data:
                # Update existing record
                set_clause = ", ".join([f"{col}=%s" for col, _ in entries[1:]])
                cursor.execute(f"UPDATE {table} SET {set_clause} WHERE {entries[0][0]}=%s", 
                              values[1:] + [values[0]])
                status = "updated"
            else:
                # Insert new record
                col_clause = ", ".join([col for col, _ in entries])
                q_clause = ", ".join(["%s"] * len(entries))
                cursor.execute(f"INSERT INTO {table} ({col_clause}) VALUES ({q_clause})", values)
                status = "added"
            
            conn.commit()
            conn.close()
            
            # Refresh the tree
            fetch_data(tree, table)
            
            # Close the form
            form.destroy()
            
            # Show success message
            messagebox.showinfo("Success", f"Record {status} successfully.")
            
        except Exception as e:
            logger.error(f"Save error: {e}")
            messagebox.showerror("Save Error", str(e))
    
    # Button frame
    button_frame = ttk.Frame(scrollable_frame)
    button_frame.pack(pady=15, padx=10)
    
    ttk.Button(button_frame, text="Save", command=save).pack(side="left", padx=5)
    ttk.Button(button_frame, text="Cancel", command=form.destroy).pack(side="left", padx=5)
    
    # Pack canvas and scrollbar
    canvas.pack(side="left", fill="both", expand=True, padx=10, pady=10)
    scrollbar.pack(side="right", fill="y")
    
    # Make form modal
    form.transient(tree.winfo_toplevel())
    form.grab_set()
    
    return form

def delete_selected(table, tree):
    """Delete the selected record"""
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
            id_column = tree["columns"][0]
            
            cursor.execute(f"DELETE FROM {table} WHERE {id_column}=%s", (record_id,))
            conn.commit()
            conn.close()
            
            # Refresh the tree
            fetch_data(tree, table)
            
            messagebox.showinfo("Success", "Record deleted successfully.")
            
        except Exception as e:
            logger.error(f"Delete error: {e}")
            
            # Check for foreign key constraint
            if "foreign key constraint fails" in str(e).lower():
                messagebox.showerror(
                    "Delete Error", 
                    "Cannot delete this record because it is referenced by other records."
                )
            else:
                messagebox.showerror("Delete Error", str(e))

def edit_selected(tree, table, cols):
    """Edit the selected record"""
    selected = tree.selection()
    if not selected:
        messagebox.showinfo("Edit", "Select a record first.")
        return
    
    data = tree.item(selected[0], "values")
    add_edit_form(table, cols, tree, data)

def export_to_csv(tree, filename=None):
    """Export treeview data to CSV"""
    if not filename:
        filename = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
    
    if not filename:
        return False
    
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
        
        return True
    except Exception as e:
        logger.error(f"Export error: {e}")
        messagebox.showerror("Export Error", str(e))
        return False

def get_expiring_qualifications():
    """Get qualifications approaching expiry"""
    try:
        conn = connect_db()
        cursor = conn.cursor()
        
        # Get current date
        today = datetime.now().strftime('%Y-%m-%d')
        
        # Query to get license expiry data
        query = f"""
        SELECT d.Driver_ID, d.First_Name, d.Last_Name, dq.Qualification_Type, 
               dq.Qualification_Number, dq.Expiry_Date,
               DATEDIFF(dq.Expiry_Date, '{today}') as Days_Remaining
        FROM Driver d
        JOIN Driver_Qualification dq ON d.Driver_ID = dq.Driver_ID
        WHERE dq.Qualification_Type LIKE '%License%' OR dq.Qualification_Type LIKE '%licence%'
        ORDER BY dq.Expiry_Date
        """
        
        cursor.execute(query)
        results = cursor.fetchall()
        conn.close()
        
        return results
    except Exception as e:
        logger.error(f"Error getting expiring qualifications: {e}")
        raise e

class DriverManagement:
    def __init__(self, root):
        self.root = root
        self.root.title("Driver Management")
        self.root.geometry("1200x800")
        self.root.minsize(800, 600)
        
        # Create menu
        self.create_menu()
        
        # Create UI
        self.create_ui()
    
    def create_menu(self):
        """Create application menu"""
        menubar = tk.Menu(self.root)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Export Current View", command=self.export_current_view)
        file_menu.add_command(label="Export All Data", command=self.export_all_data)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)
        menubar.add_cascade(label="File", menu=file_menu)
        
        # View menu
        view_menu = tk.Menu(menubar, tearoff=0)
        view_menu.add_command(label="Refresh Data", command=self.refresh_current_view)
        view_menu.add_command(label="Refresh All Tabs", command=self.refresh_all_tabs)
        menubar.add_cascade(label="View", menu=view_menu)
        
        # Reports menu
        reports_menu = tk.Menu(menubar, tearoff=0)
        reports_menu.add_command(label="Driver Qualifications", command=self.show_driver_qualifications)
        reports_menu.add_command(label="Driver Assignments", command=self.show_driver_assignments)
        reports_menu.add_command(label="License Expiry Report", command=self.show_license_expiry)
        menubar.add_cascade(label="Reports", menu=reports_menu)
        
        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label="User Manual", command=self.show_user_manual)
        help_menu.add_command(label="About", command=self.show_about)
        menubar.add_cascade(label="Help", menu=help_menu)
        
        self.root.config(menu=menubar)
        # Add admin navigation
        return_to_admin.add_return_button(self.root, menubar)
    
    def create_ui(self):
        """Create the main UI"""
        # Create notebook
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True)
        
        # Define tables
        self.tables = [
            "Driver",
            "Driver_Address",
            "Driver_Qualification",
            "Emergency_Contact",
            "Vehicle_Driver_Assignment"
        ]
        
        # Dictionary to store treeviews
        self.treeviews = {}
        
        # Create tabs for each table
        for table in self.tables:
            label = table.replace("_", " ").title()
            tab = ttk.Frame(self.notebook)
            self.notebook.add(tab, text=label)
            
            self.create_table_tab(tab, table)
        
        # Status bar at the bottom of the window
        self.status_var = tk.StringVar(value="Ready")
        status_bar = ttk.Label(self.root, textvariable=self.status_var, relief="sunken", anchor="w")
        status_bar.pack(side="bottom", fill="x", padx=10, pady=5)
        
        # Bind tab selection event
        self.notebook.bind("<<NotebookTabChanged>>", self.on_tab_change)
    
    def create_table_tab(self, tab, table):
        """Create a tab for a table"""
        # Search frame
        search_frame = ttk.Frame(tab)
        search_frame.pack(fill="x", padx=10, pady=5)
        
        label = table.replace("_", " ").title()
        tk.Label(search_frame, text=f"Search {label} by:").pack(side="left")
        
        # Get columns
        cols = fetch_data(None, table)
        
        # Column selector
        search_option = ttk.Combobox(search_frame, values=cols, state="readonly")
        if cols:
            search_option.set(cols[0])
        search_option.pack(side="left", padx=5)
        
        # Search entry
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
        
        # Search button
        ttk.Button(
            search_frame, 
            text="Search",
            command=lambda t=tree, tbl=table, s=search_option, e=search_entry: 
                self.search_data(t, tbl, s.get(), e.get())
        ).pack(side="left")
        
        # Clear button
        ttk.Button(
            search_frame, 
            text="Clear",
            command=lambda t=tree, tbl=table, e=search_entry: 
                [e.delete(0, tk.END), self.refresh_table(t, tbl)]
        ).pack(side="left", padx=5)
        
        # Action frame with buttons
        action_frame = ttk.Frame(tab)
        action_frame.pack(pady=10)
        
        # Add button
        ttk.Button(
            action_frame, 
            text="Add", 
            command=lambda t=tree, tbl=table, c=cols: 
                add_edit_form(tbl, c, t)
        ).pack(side="left", padx=5)
        
        # Edit button
        ttk.Button(
            action_frame, 
            text="Edit", 
            command=lambda t=tree, tbl=table, c=cols: 
                edit_selected(t, tbl, c)
        ).pack(side="left", padx=5)
        
        # Delete button
        ttk.Button(
            action_frame, 
            text="Delete", 
            command=lambda t=tree, tbl=table: 
                delete_selected(tbl, t)
        ).pack(side="left", padx=5)
        
        # Export button
        ttk.Button(
            action_frame, 
            text="Export CSV", 
            command=lambda t=tree: 
                export_to_csv(t)
        ).pack(side="left", padx=5)
        
        # Store the treeview
        self.treeviews[table] = tree
    
    def on_tab_change(self, event):
        """Handle tab change event"""
        current_tab = self.notebook.index(self.notebook.select())
        table = self.tables[current_tab]
        tree = self.treeviews[table]
        
        # If tree is empty, load data
        if len(tree.get_children()) == 0:
            self.refresh_table(tree, table)
    
    def refresh_table(self, tree, table):
        """Refresh data in a table"""
        # Update status
        self.status_var.set(f"Loading data from {table}...")
        
        # Function to run in background thread
        def background_load():
            try:
                # Fetch data
                fetch_data(tree, table)
                
                # Update status in main thread
                self.root.after(0, lambda: self.status_var.set(f"Ready - {len(tree.get_children())} records loaded from {table}"))
            except Exception as e:
                logger.error(f"Error refreshing {table}: {e}")
                # Update status in main thread
                self.root.after(0, lambda: self.status_var.set(f"Error: {str(e)[:50]}..."))
        
        # Start background thread
        threading.Thread(target=background_load, daemon=True).start()
    
    def search_data(self, tree, table, column, value):
        """Search for data in a table"""
        if not column or not value:
            messagebox.showinfo("Search", "Please select a column and enter a search term")
            return
        
        # Update status
        self.status_var.set(f"Searching for {value} in {column}...")
        
        # Function to run in background thread
        def background_search():
            try:
                # Perform search
                result_count = search_data(tree, table, column, value)
                
                # Update status in main thread
                self.root.after(0, lambda: self.status_var.set(f"Search complete - {result_count} matches found"))
            except Exception as e:
                logger.error(f"Error searching {table}: {e}")
                # Update status in main thread
                self.root.after(0, lambda: self.status_var.set(f"Search error: {str(e)[:50]}..."))
        
        # Start background thread
        threading.Thread(target=background_search, daemon=True).start()
    
    def export_current_view(self):
        """Export current tab data to CSV"""
        current_tab = self.notebook.index(self.notebook.select())
        table = self.tables[current_tab]
        tree = self.treeviews[table]
        
        # Default filename
        filename = f"{table}.csv"
        
        # Ask for filename
        export_to_csv(tree)
    
    def export_all_data(self):
        """Export all tables to CSV"""
        # Ask for directory
        directory = filedialog.askdirectory(title="Select Export Directory")
        if not directory:
            return
        
        # Update status
        self.status_var.set("Exporting all data...")
        
        # Function to run in background thread
        def background_export():
            try:
                # Export each table
                for table, tree in self.treeviews.items():
                    # Refresh to ensure latest data
                    fetch_data(tree, table)
                    
                    # Export
                    filename = os.path.join(directory, f"{table}.csv")
                    export_to_csv(tree, filename)
                
                # Update status in main thread
                self.root.after(0, lambda: self.status_var.set("Export complete"))
                self.root.after(0, lambda: messagebox.showinfo(
                    "Export Complete", 
                    f"All tables exported to {directory}"
                ))
            except Exception as e:
                logger.error(f"Export error: {e}")
                # Update status in main thread
                self.root.after(0, lambda: self.status_var.set(f"Export error: {str(e)[:50]}..."))
                self.root.after(0, lambda: messagebox.showerror("Export Error", str(e)))
        
        # Start background thread
        threading.Thread(target=background_export, daemon=True).start()
    
    def refresh_current_view(self):
        """Refresh current tab"""
        current_tab = self.notebook.index(self.notebook.select())
        table = self.tables[current_tab]
        tree = self.treeviews[table]
        
        self.refresh_table(tree, table)
    
    def refresh_all_tabs(self):
        """Refresh all tabs"""
        # Update status
        self.status_var.set("Refreshing all tabs...")
        
        # Function to run in background thread
        def background_refresh():
            try:
                # Refresh each table
                for table, tree in self.treeviews.items():
                    fetch_data(tree, table)
                
                # Update status in main thread
                self.root.after(0, lambda: self.status_var.set("All tabs refreshed"))
            except Exception as e:
                logger.error(f"Refresh error: {e}")
                # Update status in main thread
                self.root.after(0, lambda: self.status_var.set(f"Refresh error: {str(e)[:50]}..."))
                self.root.after(0, lambda: messagebox.showerror("Refresh Error", str(e)))
        
        # Start background thread
        threading.Thread(target=background_refresh, daemon=True).start()
    
    def show_driver_qualifications(self):
        """Show driver qualifications report"""
        # Update status
        self.status_var.set("Generating driver qualifications report...")
        
        # Function to run in background thread
        def background_report():
            try:
                # Get data
                conn = connect_db()
                cursor = conn.cursor()
                
                query = """
                SELECT d.Driver_ID, d.First_Name, d.Last_Name, dq.Qualification_Type, 
                       dq.Qualification_Number, dq.Expiry_Date 
                FROM Driver d
                JOIN Driver_Qualification dq ON d.Driver_ID = dq.Driver_ID
                ORDER BY d.Last_Name, d.First_Name
                """
                
                cursor.execute(query)
                results = cursor.fetchall()
                conn.close()
                
                # Show report in main thread
                self.root.after(0, lambda: self.display_qualifications_report(results))
                
                # Update status
                self.root.after(0, lambda: self.status_var.set("Ready"))
                
            except Exception as e:
                logger.error(f"Report error: {e}")
                # Update status in main thread
                self.root.after(0, lambda: self.status_var.set("Ready"))
                self.root.after(0, lambda: messagebox.showerror("Report Error", str(e)))
        
        # Start background thread
        threading.Thread(target=background_report, daemon=True).start()
    
    def display_qualifications_report(self, results):
        """Display driver qualifications report"""
        if not results:
            messagebox.showinfo("No Data", "No qualification data found")
            return
        
        # Create report window
        report_window = tk.Toplevel(self.root)
        report_window.title("Driver Qualifications Report")
        report_window.geometry("900x600")
        
        # Header
        header_frame = ttk.Frame(report_window)
        header_frame.pack(fill="x", padx=10, pady=10)
        
        ttk.Label(
            header_frame, 
            text="Driver Qualifications Report",
            font=("Arial", 14, "bold")
        ).pack(side="left")
        
        # Create columns
        columns = ["Driver ID", "First Name", "Last Name", "Qualification Type", 
                  "Qualification Number", "Expiry Date"]
        
        # Create filter frame
        filter_frame = ttk.Frame(report_window)
        filter_frame.pack(fill="x", padx=10, pady=5)
        
        ttk.Label(filter_frame, text="Filter by Qualification Type:").pack(side="left")
        
        # Get unique qualification types
        qual_types = list(set(row[3] for row in results))
        qual_types.sort()
        
        qual_var = tk.StringVar(value="All")
        qual_combo = ttk.Combobox(
            filter_frame, 
            textvariable=qual_var,
            values=["All"] + qual_types,
            state="readonly",
            width=30
        )
        qual_combo.pack(side="left", padx=5)
        
        # Main frame for treeview
        main_frame = ttk.Frame(report_window)
        main_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Create treeview with scrollbars
        tree = ttk.Treeview(main_frame, columns=columns, show="headings")
        vsb = ttk.Scrollbar(main_frame, orient="vertical", command=tree.yview)
        hsb = ttk.Scrollbar(main_frame, orient="horizontal", command=tree.xview)
        
        tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        
        # Grid layout
        tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        
        # Configure grid weights
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(0, weight=1)
        
        # Set up columns
        for i, col in enumerate(columns):
            tree.heading(col, text=col)
            # Adjust column width based on content
            if i == 0:  # Driver ID
                tree.column(col, anchor="center", width=70)
            elif i == 5:  # Expiry Date
                tree.column(col, anchor="center", width=120)
            elif i == 4:  # Qualification Number
                tree.column(col, anchor="center", width=150)
            else:
                tree.column(col, anchor="w", width=120)
        
        # Store all rows for filtering
        all_rows = results
        
        # Add all rows initially
        today = datetime.now().date()
        
        for row in all_rows:
            # Determine tag based on expiry date
            tag = None
            if row[5]:  # Expiry date
                try:
                    expiry_date = datetime.strptime(str(row[5]), '%Y-%m-%d').date()
                    days_until = (expiry_date - today).days
                    
                    if days_until < 0:
                        tag = "expired"
                    elif days_until < 30:
                        tag = "expiring"
                except (ValueError, TypeError):
                    pass
            
            if tag:
                tree.insert("", "end", values=row, tags=(tag,))
            else:
                tree.insert("", "end", values=row)
        
        # Configure tags for colors
        tree.tag_configure("expired", background="#ffcccc")  # Light red
        tree.tag_configure("expiring", background="#ffffcc")  # Light yellow
        
        # Function to filter by qualification type
        def filter_results(*args):
            selected = qual_var.get()
            
            # Clear current items
            tree.delete(*tree.get_children())
            
            # Add filtered items
            for row in all_rows:
                if selected == "All" or row[3] == selected:
                    # Determine tag based on expiry date
                    tag = None
                    if row[5]:  # Expiry date
                        try:
                            expiry_date = datetime.strptime(str(row[5]), '%Y-%m-%d').date()
                            days_until = (expiry_date - today).days
                            
                            if days_until < 0:
                                tag = "expired"
                            elif days_until < 30:
                                tag = "expiring"
                        except (ValueError, TypeError):
                            pass
                    
                    if tag:
                        tree.insert("", "end", values=row, tags=(tag,))
                    else:
                        tree.insert("", "end", values=row)
        
        # Bind qualification type change to filter function
        qual_var.trace_add("write", filter_results)
        
        # Add legend frame
        legend_frame = ttk.Frame(report_window)
        legend_frame.pack(fill="x", padx=10, pady=5)
        
        ttk.Label(legend_frame, text="Legend:", font=("Arial", 9, "bold")).pack(side="left", padx=5)
        
        # Expired indicator
        expired_label = ttk.Label(legend_frame, text="  ", background="#ffcccc")
        expired_label.pack(side="left", padx=2)
        ttk.Label(legend_frame, text="Expired").pack(side="left", padx=(0, 10))
        
        # Expiring indicator
        expiring_label = ttk.Label(legend_frame, text="  ", background="#ffffcc")
        expiring_label.pack(side="left", padx=2)
        ttk.Label(legend_frame, text="Expires Within 30 Days").pack(side="left")
        
        # Button frame
        button_frame = ttk.Frame(report_window)
        button_frame.pack(fill="x", padx=10, pady=10)
        
        # Export button
        ttk.Button(
            button_frame,
            text="Export to CSV",
            command=lambda: export_to_csv(tree, "Driver_Qualifications_Report.csv") and
                    messagebox.showinfo("Export Complete", "Report exported to Driver_Qualifications_Report.csv")
        ).pack(side="left")
        
        # Close button
        ttk.Button(
            button_frame,
            text="Close",
            command=report_window.destroy
        ).pack(side="right")
    
    def show_driver_assignments(self):
        """Show driver vehicle assignments report"""
        # Update status
        self.status_var.set("Generating driver assignments report...")
        
        # Function to run in background thread
        def background_report():
            try:
                # Get data
                conn = connect_db()
                cursor = conn.cursor()
                
                query = """
                SELECT d.Driver_ID, d.First_Name, d.Last_Name, v.Vehicle_ID, 
                       v.Make, v.Model, v.Registration_Number, vda.Assignment_Date 
                FROM Driver d
                JOIN Vehicle_Driver_Assignment vda ON d.Driver_ID = vda.Driver_ID
                JOIN Vehicle v ON vda.Vehicle_ID = v.Vehicle_ID
                ORDER BY d.Last_Name, d.First_Name
                """
                
                cursor.execute(query)
                results = cursor.fetchall()
                conn.close()
                
                # Show report in main thread
                self.root.after(0, lambda: self.display_assignments_report(results))
                
                # Update status
                self.root.after(0, lambda: self.status_var.set("Ready"))
                
            except Exception as e:
                logger.error(f"Report error: {e}")
                # Update status in main thread
                self.root.after(0, lambda: self.status_var.set("Ready"))
                self.root.after(0, lambda: messagebox.showerror("Report Error", str(e)))
        
        # Start background thread
        threading.Thread(target=background_report, daemon=True).start()
    
    def display_assignments_report(self, results):
        """Display driver assignments report"""
        if not results:
            messagebox.showinfo("No Data", "No driver assignment data found")
            return
        
        # Create report window
        report_window = tk.Toplevel(self.root)
        report_window.title("Driver Vehicle Assignments")
        report_window.geometry("900x600")
        
        # Header
        header_frame = ttk.Frame(report_window)
        header_frame.pack(fill="x", padx=10, pady=10)
        
        ttk.Label(
            header_frame, 
            text="Driver Vehicle Assignments",
            font=("Arial", 14, "bold")
        ).pack(side="left")
        
        # Create columns
        columns = ["Driver ID", "First Name", "Last Name", "Vehicle ID", 
                  "Make", "Model", "Registration", "Assignment Date"]
        
        # Main frame for treeview
        main_frame = ttk.Frame(report_window)
        main_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Create treeview with scrollbars
        tree = ttk.Treeview(main_frame, columns=columns, show="headings")
        vsb = ttk.Scrollbar(main_frame, orient="vertical", command=tree.yview)
        hsb = ttk.Scrollbar(main_frame, orient="horizontal", command=tree.xview)
        
        tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        
        # Grid layout
        tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        
        # Configure grid weights
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(0, weight=1)
        
        # Set up columns
        for i, col in enumerate(columns):
            tree.heading(col, text=col)
            # Adjust column width based on content
            if i in [0, 3]:  # IDs
                tree.column(col, anchor="center", width=70)
            elif i == 7:  # Date
                tree.column(col, anchor="center", width=120)
            else:
                tree.column(col, anchor="w", width=120)
        
        # Add all rows
        for row in results:
            tree.insert("", "end", values=row)
        
        # Button frame
        button_frame = ttk.Frame(report_window)
        button_frame.pack(fill="x", padx=10, pady=10)
        
        # Export button
        ttk.Button(
            button_frame,
            text="Export to CSV",
            command=lambda: export_to_csv(tree, "Driver_Assignments_Report.csv") and
                    messagebox.showinfo("Export Complete", "Report exported to Driver_Assignments_Report.csv")
        ).pack(side="left")
        
        # Close button
        ttk.Button(
            button_frame,
            text="Close",
            command=report_window.destroy
        ).pack(side="right")
    
    def show_license_expiry(self):
        """Show license expiry report"""
        # Update status
        self.status_var.set("Generating license expiry report...")
        
        # Function to run in background thread
        def background_report():
            try:
                # Get data
                results = get_expiring_qualifications()
                
                # Show report in main thread
                self.root.after(0, lambda: self.display_license_expiry(results))
                
                # Update status
                self.root.after(0, lambda: self.status_var.set("Ready"))
                
            except Exception as e:
                logger.error(f"Report error: {e}")
                # Update status in main thread
                self.root.after(0, lambda: self.status_var.set("Ready"))
                self.root.after(0, lambda: messagebox.showerror("Report Error", str(e)))
        
        # Start background thread
        threading.Thread(target=background_report, daemon=True).start()
    
    def display_license_expiry(self, results):
        """Display license expiry report"""
        if not results:
            messagebox.showinfo("No Data", "No license data found")
            return
        
        # Create report window
        report_window = tk.Toplevel(self.root)
        report_window.title("License Expiry Report")
        report_window.geometry("900x600")
        
        # Header
        header_frame = ttk.Frame(report_window)
        header_frame.pack(fill="x", padx=10, pady=10)
        
        ttk.Label(
            header_frame, 
            text="License Expiry Report",
            font=("Arial", 14, "bold")
        ).pack(side="left")
        
        # Create columns
        columns = ["Driver ID", "First Name", "Last Name", "Qualification Type", 
                  "Qualification Number", "Expiry Date", "Days Remaining"]
        
        # Main frame for treeview
        main_frame = ttk.Frame(report_window)
        main_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Create treeview with scrollbars
        tree = ttk.Treeview(main_frame, columns=columns, show="headings")
        vsb = ttk.Scrollbar(main_frame, orient="vertical", command=tree.yview)
        hsb = ttk.Scrollbar(main_frame, orient="horizontal", command=tree.xview)
        
        tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        
        # Grid layout
        tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        
        # Configure grid weights
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(0, weight=1)
        
        # Set up columns
        for i, col in enumerate(columns):
            tree.heading(col, text=col)
            # Adjust column width based on content
            if i == 0:  # Driver ID
                tree.column(col, anchor="center", width=70)
            elif i in [5, 6]:  # Dates and days
                tree.column(col, anchor="center", width=120)
            else:
                tree.column(col, anchor="w", width=120)
        
        # Create tags for expiry status
        tree.tag_configure("expired", background="#ffcccc")  # Light red
        tree.tag_configure("expiring", background="#ffffcc")  # Light yellow
        
        # Add rows with appropriate tags
        for row in results:
            days_remaining = row[6]
            
            # Determine tag based on days remaining
            if days_remaining is not None:
                try:
                    days_int = int(days_remaining)
                    if days_int < 0:
                        tree.insert("", "end", values=row, tags=("expired",))
                    elif days_int < 30:
                        tree.insert("", "end", values=row, tags=("expiring",))
                    else:
                        tree.insert("", "end", values=row)
                except (ValueError, TypeError):
                    tree.insert("", "end", values=row)
            else:
                tree.insert("", "end", values=row)
        
        # Add legend frame
        legend_frame = ttk.Frame(report_window)
        legend_frame.pack(fill="x", padx=10, pady=5)
        
        ttk.Label(legend_frame, text="Legend:", font=("Arial", 9, "bold")).pack(side="left", padx=5)
        
        # Expired indicator
        expired_label = ttk.Label(legend_frame, text="  ", background="#ffcccc")
        expired_label.pack(side="left", padx=2)
        ttk.Label(legend_frame, text="Expired").pack(side="left", padx=(0, 10))
        
        # Expiring indicator
        expiring_label = ttk.Label(legend_frame, text="  ", background="#ffffcc")
        expiring_label.pack(side="left", padx=2)
        ttk.Label(legend_frame, text="Expires Within 30 Days").pack(side="left")
        
        # Button frame
        button_frame = ttk.Frame(report_window)
        button_frame.pack(fill="x", padx=10, pady=10)
        
        # Export button
        ttk.Button(
            button_frame,
            text="Export to CSV",
            command=lambda: export_to_csv(tree, "License_Expiry_Report.csv") and
                    messagebox.showinfo("Export Complete", "Report exported to License_Expiry_Report.csv")
        ).pack(side="left")
        
        # Close button
        ttk.Button(
            button_frame,
            text="Close",
            command=report_window.destroy
        ).pack(side="right")
    
    def show_user_manual(self):
        """Show user manual"""
        manual_window = tk.Toplevel(self.root)
        manual_window.title("Driver Management - User Manual")
        manual_window.geometry("700x500")
        manual_window.transient(self.root)
        
        # Create scrollable text area
        text_frame = ttk.Frame(manual_window)
        text_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        text = tk.Text(text_frame, wrap="word")
        scrollbar = ttk.Scrollbar(text_frame, orient="vertical", command=text.yview)
        text.configure(yscrollcommand=scrollbar.set)
        
        text.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # User manual content
        manual_text = """
        # Driver Management Module - User Manual
        
        ## Overview
        The Driver Management Module allows you to manage driver information including personal details, addresses, qualifications, emergency contacts, and vehicle assignments.
        
        ## Main Features
        
        ### Viewing and Managing Driver Data
        - **Driver**: Basic driver information (name, contact details, etc.)
        - **Driver Address**: Driver residential and mailing addresses
        - **Driver Qualification**: Licenses, certifications, and other qualifications
        - **Emergency Contact**: Emergency contact information for drivers
        - **Vehicle Driver Assignment**: Which vehicles are assigned to which drivers
        
        ### Adding Records
        1. Select the appropriate tab for the type of record
        2. Click the "Add" button
        3. Fill in the required information in the form
        4. Click "Save" to add the record
        
        ### Editing Records
        1. Select a record in the list
        2. Click the "Edit" button
        3. Modify the information in the form
        4. Click "Save" to update the record
        
        ### Deleting Records
        1. Select a record in the list
        2. Click the "Delete" button
        3. Confirm the deletion
        
        ### Searching
        - Use the search dropdown to select a column
        - Enter a search term in the text field
        - Click "Search" to find matching records
        - Click "Clear" to show all records again
        
        ### Reports
        - **Driver Qualifications**: List of all driver qualifications with expiry dates
        - **Driver Assignments**: Shows vehicle assignments for each driver
        - **License Expiry Report**: Lists licenses by expiry date with warnings for upcoming expirations
        
        ### Exporting Data
        - Click "Export CSV" on any tab to export the current view
        - Use "Export All Data" in the File menu to export all tables
        - Reports can also be exported to CSV
        
        ## Tips and Shortcuts
        - Color coding in reports helps identify expired or soon-to-expire qualifications
        - Filtering options in reports allow you to focus on specific data
        - The status bar at the bottom shows the current operation and record count
        
        ## Troubleshooting
        If you encounter any issues:
        1. Check that you are connected to the database
        2. Try refreshing the data with "Refresh Data" in the View menu
        3. Restart the application if problems persist
        4. Check the log file for error messages
        
        For additional help or to report issues, contact system administration.
        """
        
        text.insert("1.0", manual_text)
        text.configure(state="disabled")
        
        # Button frame
        button_frame = ttk.Frame(manual_window)
        button_frame.pack(pady=10)
        
        ttk.Button(button_frame, text="Close", command=manual_window.destroy).pack()
    
    def show_about(self):
        """Show about dialog"""
        messagebox.showinfo(
            "About Driver Management",
            "Driver Management Module\nVersion 1.0.0\n\n"
            "Part of the Fleet Management System\n\n"
            "This module provides tools for managing driver information, "
            "qualifications, and vehicle assignments.\n\n"
            "© 2025 Fleet Management System"
        )

# Main entry point
def main():
    root = tk.Tk()
    app = DriverManagement(root)
    root.mainloop()

if __name__ == "__main__":
    main()