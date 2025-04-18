import os
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
logger = logging.getLogger("local_portal")

# load files variables from .env
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

def advanced_search(table, criteria):
    """Perform advanced search with multiple criteria"""
    try:
        conn = connect_db()
        cursor = conn.cursor()
        
        # Build WHERE clause
        where_clauses = []
        params = []
        
        for column, value in criteria:
            if value:  # Only include non-empty criteria
                where_clauses.append(f"{column} LIKE %s")
                params.append(f"%{value}%")
        
        # If no criteria, return all records
        if not where_clauses:
            cursor.execute(f"SELECT * FROM {table}")
        else:
            # Join all WHERE clauses with AND
            where_sql = " AND ".join(where_clauses)
            query = f"SELECT * FROM {table} WHERE {where_sql}"
            cursor.execute(query, params)
        
        # Get results
        rows = cursor.fetchall()
        conn.close()
        
        return rows
    except Exception as e:
        logger.error(f"Advanced search error: {e}")
        raise e

def export_to_csv(tree, filename):
    """Export treeview data to CSV file"""
    try:
        with open(filename, 'w', newline='') as f:
            writer = csv.writer(f)
            
            # Write header row
            columns = tree["columns"]
            writer.writerow(columns)
            
            # Write data rows
            for item_id in tree.get_children():
                values = tree.item(item_id)['values']
                writer.writerow(values)
                
        return True
    except Exception as e:
        logger.error(f"Export error: {e}")
        messagebox.showerror("Export Error", str(e))
        return False

def get_vehicle_status():
    """Get vehicle status information for reporting"""
    try:
        conn = connect_db()
        cursor = conn.cursor()
        
        query = """
        SELECT v.Vehicle_ID, v.Registration_Number, v.Make, v.Model, 
               vst.Status_Name, v.Last_Service_Date, v.Next_Service_Date,
               ft.Type_Name as Fuel_Type
        FROM Vehicle v
        JOIN Vehicle_Status_Type vst ON v.Status_Type_ID = vst.Status_Type_ID
        JOIN Fuel_Type ft ON v.Fuel_Type_ID = ft.Fuel_Type_ID
        ORDER BY v.Status_Type_ID, v.Make, v.Model
        """
        
        cursor.execute(query)
        results = cursor.fetchall()
        conn.close()
        
        return results
    except Exception as e:
        logger.error(f"Error getting vehicle status: {e}")
        raise e

def get_driver_assignments():
    """Get driver vehicle assignment information"""
    try:
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
        
        return results
    except Exception as e:
        logger.error(f"Error getting driver assignments: {e}")
        raise e

def get_upcoming_maintenance():
    """Get upcoming maintenance information"""
    try:
        conn = connect_db()
        cursor = conn.cursor()
        
        # Get current date
        today = datetime.now().strftime('%Y-%m-%d')
        
        query = f"""
        SELECT m.Maintenance_ID, v.Registration_Number, 
               CONCAT(v.Make, ' ', v.Model) as Vehicle, 
               mt.Type_Name, m.Scheduled_Date, sp.Provider_Name,
               m.Description, m.Estimated_Cost
        FROM Maintenance m
        JOIN Vehicle v ON m.Vehicle_ID = v.Vehicle_ID
        JOIN Maintenance_Type mt ON m.Maintenance_Type_ID = mt.Maintenance_Type_ID
        JOIN Service_Provider sp ON m.Service_Provider_ID = sp.Service_Provider_ID
        WHERE m.Scheduled_Date >= '{today}' 
              AND (m.Completion_Date IS NULL OR m.Completion_Date = '')
        ORDER BY m.Scheduled_Date
        """
        
        cursor.execute(query)
        results = cursor.fetchall()
        conn.close()
        
        return results
    except Exception as e:
        logger.error(f"Error getting upcoming maintenance: {e}")
        raise e

class LocalUserPortal:
    def __init__(self, root):
        self.root = root
        self.root.title("Fleet Management - Local User Portal")
        self.root.geometry("1200x800")
        self.root.minsize(800, 600)
      
        # Dictionary to store treeviews
        self.treeviews = {}        
     
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
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)
        menubar.add_cascade(label="File", menu=file_menu)
        
        # View menu
        view_menu = tk.Menu(menubar, tearoff=0)
        view_menu.add_command(label="Refresh Data", command=self.refresh_current_view)
        menubar.add_cascade(label="View", menu=view_menu)
        
        # Reports menu
        reports_menu = tk.Menu(menubar, tearoff=0)
        reports_menu.add_command(label="Vehicle Status", command=self.show_vehicle_status)
        reports_menu.add_command(label="Driver Assignments", command=self.show_driver_assignments)
        reports_menu.add_command(label="Upcoming Maintenance", command=self.show_upcoming_maintenance)
        menubar.add_cascade(label="Reports", menu=reports_menu)
        
        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label="User Manual", command=self.show_user_manual)
        help_menu.add_command(label="About", command=self.show_about)
        menubar.add_cascade(label="Help", menu=help_menu)
        
        self.root.config(menu=menubar)
    
    def create_ui(self):
        """Create main UI components"""
        # Create notebook for tabs
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True)
        
        # Define tables with friendly names
        self.tables = {
            "Customer": "Customers",
            "Driver": "Drivers",
            "Vehicle": "Vehicles",
            "Vehicle_Type": "Vehicle Types",
            "Fuel_Type": "Fuel Types",
            "Delivery_Status": "Deliveries",
            "Maintenance": "Maintenance",
            "Service_Provider": "Service Providers"
        }
        
        # Create a tab for each table
        for table, label in self.tables.items():
            self.create_table_tab(table, label)
        
        # Bind tab selection event
        self.notebook.bind("<<NotebookTabChanged>>", self.on_tab_change)
    
    def create_table_tab(self, table, label):
        """Create a tab for a table"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text=label)
        
        # Search frame
        search_frame = ttk.Frame(tab)
        search_frame.pack(fill="x", padx=10, pady=5)
        
        ttk.Label(search_frame, text=f"Search {label} by:").pack(side="left")
        
        # Get columns for the table
        columns = fetch_data(None, table)
        
        # Column selector dropdown
        col_selector = ttk.Combobox(search_frame, values=columns, state="readonly")
        if columns:
            col_selector.set(columns[0])
        col_selector.pack(side="left", padx=5)
        
        # Search entry field
        search_entry = tk.Entry(search_frame)
        search_entry.pack(side="left", padx=5)
        
        # Frame to hold treeview and scrollbars
        tree_frame = ttk.Frame(tab)
        tree_frame.pack(expand=True, fill="both", padx=10, pady=5)
        
        # Treeview widget
        tree = ttk.Treeview(tree_frame, columns=columns, show="headings")
        
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
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, anchor="center")
        
        # Status bar
        status_var = tk.StringVar(value="Ready")
        status_bar = ttk.Label(tab, textvariable=status_var, relief="sunken", anchor="w")
        status_bar.pack(side="bottom", fill="x", padx=10, pady=(5, 10))
        
        # Store status variable with tree for updates
        tree.status_var = status_var
        
        # Search button
        ttk.Button(
            search_frame, 
            text="Search",
            command=lambda t=tree, tbl=table, s=col_selector, e=search_entry: 
                self.do_search(t, tbl, s.get(), e.get())
        ).pack(side="left")
        
        # Refresh button
        ttk.Button(
            search_frame, 
            text="Refresh",
            command=lambda t=tree, tbl=table, e=search_entry: 
                [e.delete(0, tk.END), self.refresh_table(t, tbl)]
        ).pack(side="left", padx=5)
        
        # Export button
        ttk.Button(
            search_frame,
            text="Export CSV",
            command=lambda t=tree, tbl=table:
                self.export_table(t, tbl)
        ).pack(side="left", padx=5)
        
        # Advanced search button
        ttk.Button(
            search_frame,
            text="Advanced Search",
            command=lambda tbl=table:
                self.show_advanced_search(tbl)
        ).pack(side="right", padx=5)
        
        # Store the treeview
        self.treeviews[table] = tree
    
    def on_tab_change(self, event):
        """Handle tab change event"""
        current_tab = self.notebook.index(self.notebook.select())
        table = list(self.tables.keys())[current_tab]
        tree = self.treeviews[table]
        
        # If tree is empty, load data
        if len(tree.get_children()) == 0:
            self.refresh_table(tree, table)
    
    def refresh_table(self, tree, table):
        """Refresh data in a table"""
        # Update status
        tree.status_var.set(f"Loading data from {table}...")
        
        # Function to run in background thread
        def background_load():
            try:
                # Fetch data
                columns = fetch_data(tree, table)
                
                # Update status in main thread
                self.root.after(0, lambda: tree.status_var.set(f"Ready - {len(tree.get_children())} records"))
            except Exception as e:
                logger.error(f"Error refreshing {table}: {e}")
                # Update status in main thread
                self.root.after(0, lambda: tree.status_var.set(f"Error: {str(e)[:50]}..."))
        
        # Start background thread
        threading.Thread(target=background_load, daemon=True).start()
    
    def do_search(self, tree, table, column, value):
        """Perform search"""
        if not column or not value:
            messagebox.showinfo("Search", "Please select a column and enter a search term")
            return
        
        # Update status
        tree.status_var.set(f"Searching for {value} in {column}...")
        
        # Function to run in background thread
        def background_search():
            try:
                # Perform search
                result_count = search_data(tree, table, column, value)
                
                # Update status in main thread
                self.root.after(0, lambda: tree.status_var.set(f"Search complete - {result_count} matches"))
            except Exception as e:
                logger.error(f"Error searching {table}: {e}")
                # Update status in main thread
                self.root.after(0, lambda: tree.status_var.set(f"Search error: {str(e)[:50]}..."))
        
        # Start background thread
        threading.Thread(target=background_search, daemon=True).start()
    
    def export_current_view(self):
        """Export current tab's data to CSV"""
        current_tab = self.notebook.index(self.notebook.select())
        table = list(self.tables.keys())[current_tab]
        tree = self.treeviews[table]
        
        self.export_table(tree, table)
    
    def export_table(self, tree, table):
        """Export a table to CSV"""
        # Ask for filename
        filename = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            initialfile=f"{table}.csv"
        )
        
        if not filename:
            return
        
        # Update status
        tree.status_var.set(f"Exporting to {filename}...")
        
        # Export data
        if export_to_csv(tree, filename):
            tree.status_var.set(f"Export complete - {filename}")
            messagebox.showinfo("Export Complete", f"Data exported to {filename}")
        else:
            tree.status_var.set("Export failed")
    
    def refresh_current_view(self):
        """Refresh current tab"""
        current_tab = self.notebook.index(self.notebook.select())
        table = list(self.tables.keys())[current_tab]
        tree = self.treeviews[table]
        
        self.refresh_table(tree, table)
    
    def show_advanced_search(self, table=None):
        """Show advanced search dialog"""
        # If no table specified, use current tab
        if table is None:
            current_tab = self.notebook.index(self.notebook.select())
            table = list(self.tables.keys())[current_tab]
        
        # Create dialog window
        search_window = tk.Toplevel(self.root)
        search_window.title(f"Advanced Search - {self.tables[table]}")
        search_window.geometry("600x500")
        search_window.transient(self.root)
        search_window.grab_set()
        
        # Get columns for the table
        columns = fetch_data(None, table)
        
        # Create search criteria frame
        criteria_frame = ttk.LabelFrame(search_window, text="Search Criteria")
        criteria_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Create scrollable frame for criteria
        canvas = tk.Canvas(criteria_frame)
        scrollbar = ttk.Scrollbar(criteria_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Create entry for each column
        criteria_entries = []
        for col in columns:
            row = ttk.Frame(scrollable_frame)
            row.pack(fill="x", padx=5, pady=3)
            
            label = ttk.Label(row, text=col, width=20)
            label.pack(side="left")
            
            var = tk.StringVar()
            entry = ttk.Entry(row, textvariable=var)
            entry.pack(side="left", fill="x", expand=True, padx=5)
            
            criteria_entries.append((col, var))
        
        # Results frame
        results_frame = ttk.LabelFrame(search_window, text="Results")
        results_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Create treeview for results
        results_tree = ttk.Treeview(results_frame, columns=columns, show="headings")
        
        # Scrollbars for results
        vsb = ttk.Scrollbar(results_frame, orient="vertical", command=results_tree.yview)
        hsb = ttk.Scrollbar(results_frame, orient="horizontal", command=results_tree.xview)
        results_tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        
        # Positioning
        results_tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        
        # Allow stretch
        results_frame.columnconfigure(0, weight=1)
        results_frame.rowconfigure(0, weight=1)
        
        # Add column headings
        for col in columns:
            results_tree.heading(col, text=col)
            results_tree.column(col, anchor="center")
        
        # Status bar
        status_var = tk.StringVar(value="Enter search criteria and click Search")
        status_bar = ttk.Label(search_window, textvariable=status_var, relief="sunken", anchor="w")
        status_bar.pack(side="bottom", fill="x", padx=10, pady=5)
        
        # Button frame
        button_frame = ttk.Frame(search_window)
        button_frame.pack(fill="x", padx=10, pady=10)
        
        # Search function
        def do_advanced_search():
            # Collect search criteria
            criteria = []
            for col, var in criteria_entries:
                if var.get():
                    criteria.append((col, var.get()))
            
            if not criteria:
                messagebox.showinfo("Search", "Please enter at least one search criterion")
                return
            
            status_var.set("Searching...")
            
            # Function to run in background thread
            def background_search():
                try:
                    # Perform search
                    results = advanced_search(table, criteria)
                    
                    # Update UI in main thread
                    def update_results():
                        # Clear existing results
                        results_tree.delete(*results_tree.get_children())
                        
                        # Add results
                        for row in results:
                            results_tree.insert("", tk.END, values=row)
                        
                        # Update status
                        status_var.set(f"Search complete - {len(results)} matches")
                    
                    self.root.after(0, update_results)
                    
                except Exception as e:
                    logger.error(f"Advanced search error: {e}")
                    # Update status in main thread
                    self.root.after(0, lambda: status_var.set(f"Search error: {str(e)[:50]}..."))
                    self.root.after(0, lambda: messagebox.showerror("Search Error", str(e)))
            
            # Start background thread
            threading.Thread(target=background_search, daemon=True).start()
        
        # Export function
        def export_results():
            # Ask for filename
            filename = filedialog.asksaveasfilename(
                parent=search_window,
                defaultextension=".csv",
                filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
                initialfile=f"{table}_search_results.csv"
            )
            
            if not filename:
                return
            
            # Export data
            if export_to_csv(results_tree, filename):
                status_var.set(f"Export complete - {filename}")
                messagebox.showinfo("Export Complete", f"Results exported to {filename}")
            else:
                status_var.set("Export failed")
        
        # Add buttons
        ttk.Button(button_frame, text="Search", command=do_advanced_search).pack(side="left", padx=5)
        ttk.Button(button_frame, text="Export Results", command=export_results).pack(side="left", padx=5)
        ttk.Button(button_frame, text="Clear", 
                  command=lambda: [var.set("") for _, var in criteria_entries]).pack(side="left", padx=5)
        ttk.Button(button_frame, text="Close", command=search_window.destroy).pack(side="right", padx=5)
    
    def show_vehicle_status(self):
        """Show vehicle status report"""
        # Update status in current tab
        current_tab = self.notebook.index(self.notebook.select())
        current_table = list(self.tables.keys())[current_tab]
        current_tree = self.treeviews[current_table]
        current_tree.status_var.set("Generating vehicle status report...")
        
        # Function to run in background thread
        def background_report():
            try:
                # Get vehicle status data
                results = get_vehicle_status()
                
                # Show report in main thread
                self.root.after(0, lambda: self.display_vehicle_status(results))
                self.root.after(0, lambda: current_tree.status_var.set("Ready"))
                
            except Exception as e:
                logger.error(f"Vehicle status report error: {e}")
                # Update status in main thread
                self.root.after(0, lambda: current_tree.status_var.set("Ready"))
                self.root.after(0, lambda: messagebox.showerror("Report Error", str(e)))
        
        # Start background thread
        threading.Thread(target=background_report, daemon=True).start()
    
    def display_vehicle_status(self, results):
        """Display vehicle status report"""
        if not results:
            messagebox.showinfo("Vehicle Status", "No vehicle data found")
            return
        
        # Create report window
        report_window = tk.Toplevel(self.root)
        report_window.title("Vehicle Status Report")
        report_window.geometry("1000x600")
        
        # Header
        header_frame = ttk.Frame(report_window)
        header_frame.pack(fill="x", padx=10, pady=10)
        
        ttk.Label(
            header_frame, 
            text="Vehicle Status Report",
            font=("Arial", 14, "bold")
        ).pack(side="left")
        
        # Create columns
        columns = ["ID", "Registration", "Make", "Model", "Status", 
                   "Last Service", "Next Service", "Fuel Type"]
        
        # Create filter frame
        filter_frame = ttk.Frame(report_window)
        filter_frame.pack(fill="x", padx=10, pady=5)
        
        ttk.Label(filter_frame, text="Filter by Status:").pack(side="left")
        
        # Get unique statuses
        statuses = list(set(row[4] for row in results))
        statuses.sort()
        
        status_var = tk.StringVar(value="All")
        status_combo = ttk.Combobox(
            filter_frame, 
            textvariable=status_var,
            values=["All"] + statuses,
            state="readonly"
        )
        status_combo.pack(side="left", padx=5)
        
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
            if i == 0:  # ID
                tree.column(col, anchor="center", width=50)
            elif i in [5, 6]:  # Dates
                tree.column(col, anchor="center", width=100)
            else:
                tree.column(col, anchor="w", width=120)
        
        # Create tags for upcoming service
        tree.tag_configure("overdue", background="#ffcccc")  # Light red
        tree.tag_configure("upcoming", background="#ffffcc")  # Light yellow
        
        # Add all rows initially
        all_rows = []
        today = datetime.now().date()
        
        for row in results:
            data_row = list(row)
            all_rows.append(data_row)
            
            # Determine if service is upcoming or overdue
            tag = None
            if row[6]:  # Next service date
                try:
                    next_service = datetime.strptime(str(row[6]), '%Y-%m-%d').date()
                    days_until = (next_service - today).days
                    
                    if days_until < 0:
                        tag = "overdue"
                    elif days_until <= 30:
                        tag = "upcoming"
                except (ValueError, TypeError):
                    pass
            
            if tag:
                tree.insert("", "end", values=data_row, tags=(tag,))
            else:
                tree.insert("", "end", values=data_row)
        
        # Function to filter by status
        def filter_results(*args):
            selected = status_var.get()
            
            # Clear current items
            tree.delete(*tree.get_children())
            
            # Add filtered items
            for row in all_rows:
                if selected == "All" or row[4] == selected:
                    # Determine tag based on service date
                    tag = None
                    if row[6]:  # Next service date
                        try:
                            next_service = datetime.strptime(str(row[6]), '%Y-%m-%d').date()
                            days_until = (next_service - today).days
                            
                            if days_until < 0:
                                tag = "overdue"
                            elif days_until <= 30:
                                tag = "upcoming"
                        except (ValueError, TypeError):
                            pass
                    
                    if tag:
                        tree.insert("", "end", values=row, tags=(tag,))
                    else:
                        tree.insert("", "end", values=row)
        
        # Bind status change to filter function
        status_var.trace_add("write", filter_results)
        
        # Add legend frame
        legend_frame = ttk.Frame(report_window)
        legend_frame.pack(fill="x", padx=10, pady=5)
        
        ttk.Label(legend_frame, text="Legend:", font=("Arial", 9, "bold")).pack(side="left", padx=5)
        
        # Overdue indicator
        overdue_label = ttk.Label(legend_frame, text="  ", background="#ffcccc")
        overdue_label.pack(side="left", padx=2)
        ttk.Label(legend_frame, text="Service Overdue").pack(side="left", padx=(0, 10))
        
        # Upcoming indicator
        upcoming_label = ttk.Label(legend_frame, text="  ", background="#ffffcc")
        upcoming_label.pack(side="left", padx=2)
        ttk.Label(legend_frame, text="Service Due Within 30 Days").pack(side="left")
        
        # Button frame
        button_frame = ttk.Frame(report_window)
        button_frame.pack(fill="x", padx=10, pady=10)
        
        # Export button
        ttk.Button(
            button_frame,
            text="Export to CSV",
            command=lambda: export_to_csv(tree, "Vehicle_Status_Report.csv") and
                    messagebox.showinfo("Export Complete", "Report exported to Vehicle_Status_Report.csv")
        ).pack(side="left")
        
        # Close button
        ttk.Button(
            button_frame,
            text="Close",
            command=report_window.destroy
        ).pack(side="right")
    
    def show_driver_assignments(self):
        """Show driver assignments report"""
        # Update status in current tab
        current_tab = self.notebook.index(self.notebook.select())
        current_table = list(self.tables.keys())[current_tab]
        current_tree = self.treeviews[current_table]
        current_tree.status_var.set("Generating driver assignments report...")
        
        # Function to run in background thread
        def background_report():
            try:
                # Get driver assignment data
                results = get_driver_assignments()
                
                # Show report in main thread
                self.root.after(0, lambda: self.display_driver_assignments(results))
                self.root.after(0, lambda: current_tree.status_var.set("Ready"))
                
            except Exception as e:
                logger.error(f"Driver assignments report error: {e}")
                # Update status in main thread
                self.root.after(0, lambda: current_tree.status_var.set("Ready"))
                self.root.after(0, lambda: messagebox.showerror("Report Error", str(e)))
        
        # Start background thread
        threading.Thread(target=background_report, daemon=True).start()
    
    def display_driver_assignments(self, results):
        """Display driver assignments report"""
        if not results:
            messagebox.showinfo("Driver Assignments", "No driver assignment data found")
            return
        
        # Create report window
        report_window = tk.Toplevel(self.root)
        report_window.title("Driver Vehicle Assignments")
        report_window.geometry("1000x600")
        
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
        
        # Add rows
        for row in results:
            tree.insert("", "end", values=row)
        
        # Status bar
        status_var = tk.StringVar(value=f"Showing {len(results)} driver assignments")
        status_bar = ttk.Label(report_window, textvariable=status_var, relief="sunken", anchor="w")
        status_bar.pack(fill="x", padx=10, pady=5)
        
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
    
    def show_upcoming_maintenance(self):
        """Show upcoming maintenance report"""
        # Update status in current tab
        current_tab = self.notebook.index(self.notebook.select())
        current_table = list(self.tables.keys())[current_tab]
        current_tree = self.treeviews[current_table]
        current_tree.status_var.set("Generating upcoming maintenance report...")
        
        # Function to run in background thread
        def background_report():
            try:
                # Get upcoming maintenance data
                results = get_upcoming_maintenance()
                
                # Show report in main thread
                self.root.after(0, lambda: self.display_upcoming_maintenance(results))
                self.root.after(0, lambda: current_tree.status_var.set("Ready"))
                
            except Exception as e:
                logger.error(f"Upcoming maintenance report error: {e}")
                # Update status in main thread
                self.root.after(0, lambda: current_tree.status_var.set("Ready"))
                self.root.after(0, lambda: messagebox.showerror("Report Error", str(e)))
        
        # Start background thread
        threading.Thread(target=background_report, daemon=True).start()
    
    def display_upcoming_maintenance(self, results):
        """Display upcoming maintenance report"""
        if not results:
            messagebox.showinfo("Upcoming Maintenance", "No upcoming maintenance found")
            return
        
        # Create report window
        report_window = tk.Toplevel(self.root)
        report_window.title("Upcoming Maintenance")
        report_window.geometry("1000x600")
        
        # Header
        header_frame = ttk.Frame(report_window)
        header_frame.pack(fill="x", padx=10, pady=10)
        
        ttk.Label(
            header_frame, 
            text="Upcoming Scheduled Maintenance",
            font=("Arial", 14, "bold")
        ).pack(side="left")
        
        # Create columns
        columns = ["ID", "Registration", "Vehicle", "Type", "Scheduled Date", 
                  "Provider", "Description", "Estimated Cost"]
        
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
            if i == 0:  # ID
                tree.column(col, anchor="center", width=50)
            elif i == 7:  # Cost
                tree.column(col, anchor="e", width=100)
            elif i == 4:  # Date
                tree.column(col, anchor="center", width=120)
            elif i == 6:  # Description
                tree.column(col, anchor="w", width=200)
            else:
                tree.column(col, anchor="w", width=120)
        
        # Create tags for upcoming service
        tree.tag_configure("imminent", background="#ffcccc")  # Light red for within 7 days
        tree.tag_configure("upcoming", background="#ffffcc")  # Light yellow for within 30 days
        
        # Add rows
        today = datetime.now().date()
        
        for row in results:
            # Format cost
            data_row = list(row)
            if data_row[7]:  # Cost
                try:
                    cost_value = float(data_row[7])
                    data_row[7] = f"${cost_value:.2f}"
                except (ValueError, TypeError):
                    pass
            
            # Determine tag based on scheduled date
            tag = None
            if data_row[4]:  # Scheduled date
                try:
                    scheduled = datetime.strptime(str(data_row[4]), '%Y-%m-%d').date()
                    days_until = (scheduled - today).days
                    
                    if days_until <= 7:
                        tag = "imminent"
                    elif days_until <= 30:
                        tag = "upcoming"
                except (ValueError, TypeError):
                    pass
            
            if tag:
                tree.insert("", "end", values=data_row, tags=(tag,))
            else:
                tree.insert("", "end", values=data_row)
        
        # Add legend frame
        legend_frame = ttk.Frame(report_window)
        legend_frame.pack(fill="x", padx=10, pady=5)
        
        ttk.Label(legend_frame, text="Legend:", font=("Arial", 9, "bold")).pack(side="left", padx=5)
        
        # Imminent indicator
        imminent_label = ttk.Label(legend_frame, text="  ", background="#ffcccc")
        imminent_label.pack(side="left", padx=2)
        ttk.Label(legend_frame, text="Within 7 Days").pack(side="left", padx=(0, 10))
        
        # Upcoming indicator
        upcoming_label = ttk.Label(legend_frame, text="  ", background="#ffffcc")
        upcoming_label.pack(side="left", padx=2)
        ttk.Label(legend_frame, text="Within 30 Days").pack(side="left")
        
        # Status bar
        status_var = tk.StringVar(value=f"Showing {len(results)} upcoming maintenance items")
        status_bar = ttk.Label(report_window, textvariable=status_var, relief="sunken", anchor="w")
        status_bar.pack(fill="x", padx=10, pady=5)
        
        # Button frame
        button_frame = ttk.Frame(report_window)
        button_frame.pack(fill="x", padx=10, pady=10)
        
        # Export button
        ttk.Button(
            button_frame,
            text="Export to CSV",
            command=lambda: export_to_csv(tree, "Upcoming_Maintenance_Report.csv") and
                    messagebox.showinfo("Export Complete", "Report exported to Upcoming_Maintenance_Report.csv")
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
        manual_window.title("User Manual")
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
        # Fleet Management System - Local User Portal
        
        ## Overview
        The Local User Portal provides read-only access to the fleet management database.
        You can view, search, and export data, but cannot modify the database.
        
        ## Main Features
        
        ### Viewing Data
        - Select tabs to view different data tables
        - Data is loaded automatically when you select a tab
        - Use scrollbars to navigate through large datasets
        
        ### Searching
        - Basic Search: Choose a column, enter a search term, and click Search
        - Advanced Search: Click Advanced Search for more complex queries with multiple criteria
        
        ### Reports
        Access predefined reports from the Reports menu:
        - Vehicle Status: Current status of all vehicles with service dates
        - Driver Assignments: See which drivers are assigned to which vehicles
        - Upcoming Maintenance: View scheduled maintenance that has not been completed
        
        ### Exporting Data
        - Export Current View: Export the data currently displayed in a tab
        - Export CSV: Export any search results or reports
        
        ## Tips and Shortcuts
        - Click on column headers to sort data
        - Use the status bar at the bottom of each tab for information
        - Refresh Data in the View menu updates the current tab with latest data
        
        ## Troubleshooting
        If you encounter any issues:
        1. Check that you are connected to the network
        2. Try refreshing the data
        3. Restart the application
        4. Contact system administrator if problems persist
        
        For additional help or to report issues, contact IT support.
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
            "About Fleet Management System",
            "Fleet Management System - Local User Portal\n\n"
            "Version 1.0.0\n\n"
            "This application provides read-only access to the fleet management database.\n\n"
            "© 2025 Fleet Management System"
        )

# Main entry point
def main():
    root = tk.Tk()
    app = LocalUserPortal(root)
    root.mainloop()

if __name__ == "__main__":
    main()