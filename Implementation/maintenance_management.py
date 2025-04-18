import os
import return_to_admin

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import logging
from dotenv import load_dotenv
import database_connection as db
import form_utils
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
logger = logging.getLogger("maintenance_management")

# Load environment variables
load_dotenv()

class MaintenanceManagement:
    def __init__(self, root):
        self.root = root
        self.root.title("Maintenance Management")
        self.root.geometry("1200x800")
        self.root.minsize(800, 600)
        
        # Create menu
        self.create_menu()
        
        # Create main UI
        self.create_ui()
    
    def create_menu(self):
        """Create application menu"""
        menubar = tk.Menu(self.root)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Export All Data", command=self.export_all_data)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)
        menubar.add_cascade(label="File", menu=file_menu)
        
        # Reports menu
        reports_menu = tk.Menu(menubar, tearoff=0)
        reports_menu.add_command(label="Maintenance History by Vehicle", command=self.show_vehicle_maintenance)
        reports_menu.add_command(label="Upcoming Maintenance", command=self.show_upcoming_maintenance)
        reports_menu.add_command(label="Maintenance Cost Summary", command=self.show_maintenance_costs)
        menubar.add_cascade(label="Reports", menu=reports_menu)
        
        # Tools menu
        tools_menu = tk.Menu(menubar, tearoff=0)
        tools_menu.add_command(label="Refresh All Data", command=self.refresh_all_data)
        tools_menu.add_command(label="Advanced Search", command=self.show_advanced_search)
        tools_menu.add_command(label="Schedule Maintenance", command=self.schedule_maintenance)
        menubar.add_cascade(label="Tools", menu=tools_menu)
        
        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label="Help", command=self.show_help)
        help_menu.add_command(label="About", command=self.show_about)
        menubar.add_cascade(label="Help", menu=help_menu)
        
        self.root.config(menu=menubar)
        # Add admin navigation
        return_to_admin.add_return_button(self.root, menubar)
    
    def create_ui(self):
        """Create the main UI components"""
        # Create notebook
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(expand=True, fill="both")
        
        # Define tables
        self.tables = [
            "Maintenance",
            "Maintenance_Type"
        ]
        
        # Dictionary to store treeviews
        self.treeviews = {}
        
        # Create tabs for each table
        for table in self.tables:
            label = table.replace("_", " ").title()
            tab = ttk.Frame(self.notebook)
            self.notebook.add(tab, text=label)
            
            # Setup tree and UI elements
            tree = form_utils.setup_tree_for_table(tab, table)
            self.treeviews[table] = tree
    
    def export_all_data(self):
        """Export all data to CSV files"""
        # Ask for directory
        export_dir = filedialog.askdirectory(title="Select Export Directory")
        if not export_dir:
            return
        
        try:
            # Export each table
            for table in self.tables:
                filename = os.path.join(export_dir, f"{table}.csv")
                db.export_data_to_csv(table, filename)
            
            messagebox.showinfo("Export Complete", f"All data exported to {export_dir}")
        except Exception as e:
            logger.error(f"Export error: {e}")
            messagebox.showerror("Export Error", str(e))
    
    def refresh_all_data(self):
        """Refresh all treeviews"""
        for table, tree in self.treeviews.items():
            form_utils.refresh_tree(tree, table)
        
        messagebox.showinfo("Refresh Complete", "All data has been refreshed")
    
    def show_advanced_search(self):
        """Show advanced search dialog"""
        search_window = tk.Toplevel(self.root)
        search_window.title("Advanced Maintenance Search")
        search_window.geometry("500x400")
        search_window.transient(self.root)
        search_window.grab_set()
        
        # Table selection
        ttk.Label(search_window, text="Search in:").pack(anchor="w", padx=20, pady=(20, 5))
        
        table_var = tk.StringVar(value=self.tables[0])
        table_combo = ttk.Combobox(search_window, textvariable=table_var, values=self.tables, state="readonly")
        table_combo.pack(fill="x", padx=20, pady=5)
        
        # Search criteria frame
        criteria_frame = ttk.LabelFrame(search_window, text="Search Criteria")
        criteria_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        # Will store entry widgets and their variables
        criteria_entries = []
        
        def update_criteria_fields(*args):
            # Clear existing fields
            for widget in criteria_frame.winfo_children():
                widget.destroy()
                
            criteria_entries.clear()
            
            # Get selected table
            selected_table = table_var.get()
            
            # Get columns for the table
            columns = db.get_table_columns(selected_table)
            
            # Create entries for each column
            for i, col in enumerate(columns):
                row_frame = ttk.Frame(criteria_frame)
                row_frame.pack(fill="x", pady=2)
                
                ttk.Label(row_frame, text=col, width=20).pack(side="left")
                
                var = tk.StringVar()
                entry = ttk.Entry(row_frame, textvariable=var)
                entry.pack(side="left", fill="x", expand=True, padx=5)
                
                criteria_entries.append((col, var))
        
        # Update when table changes
        table_var.trace_add("write", update_criteria_fields)
        
        # Initial population
        update_criteria_fields()
        
        # Results frame
        results_frame = ttk.LabelFrame(search_window, text="Results")
        results_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        # Create treeview for results
        results_tree = ttk.Treeview(results_frame)
        
        # Add scrollbars
        vsb = ttk.Scrollbar(results_frame, orient="vertical", command=results_tree.yview)
        hsb = ttk.Scrollbar(results_frame, orient="horizontal", command=results_tree.xview)
        results_tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        
        # Grid layout
        results_tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        
        # Configure grid weights
        results_frame.columnconfigure(0, weight=1)
        results_frame.rowconfigure(0, weight=1)
        
        def do_search():
            # Get selected table
            selected_table = table_var.get()
            
            # Get search criteria
            search_params = []
            for col, var in criteria_entries:
                if var.get():
                    search_params.append((col, var.get()))
            
            try:
                # Perform search
                if search_params:
                    rows, _ = db.advanced_search_data(selected_table, search_params)
                else:
                    rows, _ = db.fetch_data_paginated(selected_table)
                
                # Configure treeview columns
                columns = db.get_table_columns(selected_table)
                results_tree["columns"] = columns
                results_tree["show"] = "headings"
                
                for col in columns:
                    results_tree.heading(col, text=col)
                    results_tree.column(col, anchor="center", width=100)
                
                # Clear existing data
                results_tree.delete(*results_tree.get_children())
                
                # Add results
                for row in rows:
                    results_tree.insert("", "end", values=row)
                
            except Exception as e:
                logger.error(f"Search error: {e}")
                messagebox.showerror("Search Error", str(e))
        
        # Buttons
        button_frame = ttk.Frame(search_window)
        button_frame.pack(fill="x", padx=20, pady=15)
        
        ttk.Button(button_frame, text="Search", command=do_search).pack(side="left", padx=5)
        ttk.Button(button_frame, text="Export Results", 
                  command=lambda: form_utils.export_to_csv(search_window, results_tree, table_var.get())
                 ).pack(side="left", padx=5)
        ttk.Button(button_frame, text="Close", command=search_window.destroy).pack(side="right", padx=5)
    
    def schedule_maintenance(self):
        """Schedule new maintenance for a vehicle"""
        schedule_window = tk.Toplevel(self.root)
        schedule_window.title("Schedule Maintenance")
        schedule_window.geometry("500x600")
        schedule_window.transient(self.root)
        schedule_window.grab_set()
        
        # Create form layout
        ttk.Label(schedule_window, text="Schedule Vehicle Maintenance", 
                 font=("Arial", 14, "bold")).pack(pady=(20, 15))
        
        main_frame = ttk.Frame(schedule_window, padding=15)
        main_frame.pack(fill="both", expand=True)
        
        # Vehicle selection
        ttk.Label(main_frame, text="Vehicle:").grid(row=0, column=0, sticky="w", pady=5)
        
        # Get vehicles
        try:
            vehicle_query = """
            SELECT v.Vehicle_ID, CONCAT(v.Vehicle_ID, ' - ', v.Make, ' ', v.Model, ' (', v.Registration_Number, ')') 
            FROM Vehicle v
            ORDER BY v.Vehicle_ID
            """
            vehicles = db.execute_query(vehicle_query)
            vehicle_list = [v[1] for v in vehicles]
            vehicle_ids = {v[1]: v[0] for v in vehicles}
        except Exception as e:
            logger.error(f"Error loading vehicles: {e}")
            vehicle_list = []
            vehicle_ids = {}
        
        vehicle_var = tk.StringVar()
        vehicle_combo = ttk.Combobox(main_frame, textvariable=vehicle_var, values=vehicle_list, state="readonly", width=40)
        vehicle_combo.grid(row=0, column=1, sticky="ew", pady=5)
        
        # Maintenance type
        ttk.Label(main_frame, text="Maintenance Type:").grid(row=1, column=0, sticky="w", pady=5)
        
        # Get maintenance types
        try:
            type_query = """
            SELECT mt.Maintenance_Type_ID, mt.Type_Name 
            FROM Maintenance_Type mt
            ORDER BY mt.Type_Name
            """
            types = db.execute_query(type_query)
            type_list = [t[1] for t in types]
            type_ids = {t[1]: t[0] for t in types}
        except Exception as e:
            logger.error(f"Error loading maintenance types: {e}")
            type_list = []
            type_ids = {}
        
        type_var = tk.StringVar()
        type_combo = ttk.Combobox(main_frame, textvariable=type_var, values=type_list, state="readonly", width=40)
        type_combo.grid(row=1, column=1, sticky="ew", pady=5)
        
        # Service provider
        ttk.Label(main_frame, text="Service Provider:").grid(row=2, column=0, sticky="w", pady=5)
        
        # Get service providers
        try:
            provider_query = """
            SELECT sp.Service_Provider_ID, sp.Provider_Name 
            FROM Service_Provider sp
            ORDER BY sp.Provider_Name
            """
            providers = db.execute_query(provider_query)
            provider_list = [p[1] for p in providers]
            provider_ids = {p[1]: p[0] for p in providers}
        except Exception as e:
            logger.error(f"Error loading service providers: {e}")
            provider_list = []
            provider_ids = {}
        
        provider_var = tk.StringVar()
        provider_combo = ttk.Combobox(main_frame, textvariable=provider_var, values=provider_list, state="readonly", width=40)
        provider_combo.grid(row=2, column=1, sticky="ew", pady=5)
        
        # Scheduled date
        ttk.Label(main_frame, text="Scheduled Date:").grid(row=3, column=0, sticky="w", pady=5)
        
        date_frame = ttk.Frame(main_frame)
        date_frame.grid(row=3, column=1, sticky="ew", pady=5)
        
        # Default to today
        today = datetime.now()
        
        # Year
        year_var = tk.StringVar(value=str(today.year))
        year_spin = ttk.Spinbox(date_frame, from_=2020, to=2030, textvariable=year_var, width=6)
        year_spin.pack(side="left")
        
        ttk.Label(date_frame, text="-").pack(side="left")
        
        # Month
        month_var = tk.StringVar(value=str(today.month).zfill(2))
        month_spin = ttk.Spinbox(date_frame, from_=1, to=12, textvariable=month_var, width=4)
        month_spin.pack(side="left")
        
        ttk.Label(date_frame, text="-").pack(side="left")
        
        # Day
        day_var = tk.StringVar(value=str(today.day).zfill(2))
        day_spin = ttk.Spinbox(date_frame, from_=1, to=31, textvariable=day_var, width=4)
        day_spin.pack(side="left")
        
        # Description
        ttk.Label(main_frame, text="Description:").grid(row=4, column=0, sticky="nw", pady=5)
        
        description_var = tk.StringVar()
        description_text = tk.Text(main_frame, height=5, width=40)
        description_text.grid(row=4, column=1, sticky="ew", pady=5)
        
        # Estimated cost
        ttk.Label(main_frame, text="Estimated Cost:").grid(row=5, column=0, sticky="w", pady=5)
        
        cost_var = tk.StringVar()
        cost_entry = ttk.Entry(main_frame, textvariable=cost_var, width=40)
        cost_entry.grid(row=5, column=1, sticky="ew", pady=5)
        
        # Notes
        ttk.Label(main_frame, text="Notes:").grid(row=6, column=0, sticky="nw", pady=5)
        
        notes_text = tk.Text(main_frame, height=5, width=40)
        notes_text.grid(row=6, column=1, sticky="ew", pady=5)
        
        # Configure grid weights
        main_frame.columnconfigure(1, weight=1)
        
        # Action buttons
        button_frame = ttk.Frame(schedule_window)
        button_frame.pack(fill="x", pady=15, padx=15)
        
        def save_maintenance():
            # Get values
            try:
                vehicle_id = vehicle_ids.get(vehicle_var.get())
                type_id = type_ids.get(type_var.get())
                provider_id = provider_ids.get(provider_var.get())
                
                # Validate required fields
                if not vehicle_id or not type_id or not provider_id:
                    messagebox.showerror("Validation Error", "Please select vehicle, maintenance type, and service provider.")
                    return
                
                # Create date string (YYYY-MM-DD)
                try:
                    date_str = f"{year_var.get()}-{month_var.get().zfill(2)}-{day_var.get().zfill(2)}"
                    # Validate date
                    datetime.strptime(date_str, '%Y-%m-%d')
                except ValueError:
                    messagebox.showerror("Validation Error", "Invalid date format. Use YYYY-MM-DD.")
                    return
                
                # Get description and notes
                description = description_text.get("1.0", "end-1c")
                notes = notes_text.get("1.0", "end-1c")
                
                # Get cost (default to 0 if empty)
                cost = cost_var.get()
                if not cost:
                    cost = "0.00"
                
                # Validate cost
                try:
                    float(cost)
                except ValueError:
                    messagebox.showerror("Validation Error", "Cost must be a valid number.")
                    return
                
                # Create maintenance record
                columns = ["Vehicle_ID", "Maintenance_Type_ID", "Service_Provider_ID", 
                           "Scheduled_Date", "Description", "Estimated_Cost", "Notes"]
                values = [vehicle_id, type_id, provider_id, date_str, description, cost, notes]
                
                db.insert_data("Maintenance", columns, values)
                
                messagebox.showinfo("Success", "Maintenance scheduled successfully!")
                
                # Refresh maintenance view
                form_utils.refresh_tree(self.treeviews["Maintenance"], "Maintenance")
                
                # Close window
                schedule_window.destroy()
                
            except Exception as e:
                logger.error(f"Error scheduling maintenance: {e}")
                messagebox.showerror("Error", f"Failed to schedule maintenance: {e}")
        
        ttk.Button(button_frame, text="Schedule", command=save_maintenance).pack(side="left", padx=5)
        ttk.Button(button_frame, text="Cancel", command=schedule_window.destroy).pack(side="right", padx=5)
    
    def show_vehicle_maintenance(self):
        """Show maintenance history by vehicle"""
        # First, get list of vehicles
        try:
            vehicle_query = """
            SELECT v.Vehicle_ID, CONCAT(v.Make, ' ', v.Model, ' (', v.Registration_Number, ')') as Vehicle
            FROM Vehicle v
            ORDER BY v.Make, v.Model
            """
            vehicles = db.execute_query(vehicle_query)
        except Exception as e:
            logger.error(f"Error loading vehicles: {e}")
            messagebox.showerror("Error", f"Failed to load vehicles: {e}")
            return
        
        if not vehicles:
            messagebox.showinfo("No Data", "No vehicles found in the database.")
            return
        
        # Create selection dialog
        select_window = tk.Toplevel(self.root)
        select_window.title("Select Vehicle")
        select_window.geometry("400x300")
        select_window.transient(self.root)
        select_window.grab_set()
        
        ttk.Label(select_window, text="Select a vehicle to view maintenance history:", 
                 font=("Arial", 11)).pack(pady=(20, 10), padx=20)
        
        # Create listbox with scrollbar
        frame = ttk.Frame(select_window)
        frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        scrollbar = ttk.Scrollbar(frame)
        scrollbar.pack(side="right", fill="y")
        
        vehicle_listbox = tk.Listbox(frame, yscrollcommand=scrollbar.set, height=10)
        vehicle_listbox.pack(side="left", fill="both", expand=True)
        
        scrollbar.config(command=vehicle_listbox.yview)
        
        # Populate listbox
        vehicle_ids = {}
        for v in vehicles:
            vehicle_ids[v[1]] = v[0]
            vehicle_listbox.insert(tk.END, v[1])
        
        # Select first vehicle
        vehicle_listbox.select_set(0)
        
        def show_selected_vehicle_history():
            try:
                selected_idx = vehicle_listbox.curselection()
                if not selected_idx:
                    messagebox.showinfo("Select Vehicle", "Please select a vehicle.")
                    return
                
                selected_vehicle = vehicle_listbox.get(selected_idx[0])
                vehicle_id = vehicle_ids[selected_vehicle]
                
                # Close selection window
                select_window.destroy()
                
                # Show maintenance history
                show_maintenance_history(vehicle_id, selected_vehicle)
                
            except Exception as e:
                logger.error(f"Error showing vehicle history: {e}")
                messagebox.showerror("Error", f"Failed to load maintenance history: {e}")
        
        button_frame = ttk.Frame(select_window)
        button_frame.pack(fill="x", pady=15, padx=20)
        
        ttk.Button(button_frame, text="View History", command=show_selected_vehicle_history).pack(side="left", padx=5)
        ttk.Button(button_frame, text="Cancel", command=select_window.destroy).pack(side="right", padx=5)
    
    def show_maintenance_history(self, vehicle_id, vehicle_name):
        """Show maintenance history for a specific vehicle"""
        try:
            query = """
            SELECT m.Maintenance_ID, mt.Type_Name, m.Scheduled_Date, 
                   sp.Provider_Name, m.Description, m.Estimated_Cost,
                   m.Completion_Date, m.Actual_Cost, m.Notes 
            FROM Maintenance m
            JOIN Maintenance_Type mt ON m.Maintenance_Type_ID = mt.Maintenance_Type_ID
            JOIN Service_Provider sp ON m.Service_Provider_ID = sp.Service_Provider_ID
            WHERE m.Vehicle_ID = %s
            ORDER BY m.Scheduled_Date DESC
            """
            
            results = db.execute_query(query, (vehicle_id,))
            
            if not results:
                messagebox.showinfo("No History", f"No maintenance history found for {vehicle_name}")
                return
            
            # Create report window
            report_window = tk.Toplevel(self.root)
            report_window.title(f"Maintenance History - {vehicle_name}")
            report_window.geometry("1000x600")
            
            # Create treeview for results
            columns = ["ID", "Type", "Scheduled Date", "Provider", "Description", 
                       "Est. Cost", "Completion Date", "Actual Cost", "Notes"]
            
            # Container frame
            container = ttk.Frame(report_window)
            container.pack(fill="both", expand=True, padx=10, pady=10)
            
            # Add header
            ttk.Label(container, text=f"Maintenance History for {vehicle_name}", 
                     font=("Arial", 14, "bold")).pack(pady=(0, 10))
            
            # Create treeview with scrollbars
            tree_frame = ttk.Frame(container)
            tree_frame.pack(fill="both", expand=True)
            
            tree = ttk.Treeview(tree_frame, columns=columns, show="headings")
            
            # Add scrollbars
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
            for i, col in enumerate(columns):
                tree.heading(col, text=col)
                # Adjust width based on content type
                if i in [0, 5, 7]:  # ID, costs
                    tree.column(col, anchor="center", width=70)
                elif i in [2, 6]:  # Dates
                    tree.column(col, anchor="center", width=120)
                elif i == 8:  # Notes
                    tree.column(col, anchor="w", width=200)
                else:
                    tree.column(col, anchor="w", width=130)
            
            # Add data
            for row in results:
                # Format costs to show currency
                formatted_row = list(row)
                if formatted_row[5]:  # Estimated cost
                    formatted_row[5] = f"${float(formatted_row[5]):.2f}"
                if formatted_row[7]:  # Actual cost
                    formatted_row[7] = f"${float(formatted_row[7]):.2f}"
                
                tree.insert("", "end", values=formatted_row)
            
            # Add buttons
            button_frame = ttk.Frame(container)
            button_frame.pack(fill="x", pady=10)
            
            ttk.Button(
                button_frame, 
                text="Export to CSV", 
                command=lambda: form_utils.export_to_csv(report_window, tree, f"Maintenance_History_{vehicle_id}")
            ).pack(side="left", padx=5)
            
            ttk.Button(
                button_frame,
                text="Close",
                command=report_window.destroy
            ).pack(side="right", padx=5)
            
        except Exception as e:
            logger.error(f"Error showing maintenance history: {e}")
            messagebox.showerror("Report Error", str(e))
    
    def show_upcoming_maintenance(self):
        """Show upcoming scheduled maintenance"""
        try:
            # Get current date
            today = datetime.now().strftime('%Y-%m-%d')
            
            # Query to get upcoming maintenance
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
            
            results = db.execute_query(query)
            
            if not results:
                messagebox.showinfo("No Upcoming Maintenance", "No upcoming maintenance found.")
                return
            
            # Create report window
            report_window = tk.Toplevel(self.root)
            report_window.title("Upcoming Scheduled Maintenance")
            report_window.geometry("1000x600")
            
            # Create treeview for results
            columns = ["ID", "Reg Number", "Vehicle", "Type", "Scheduled Date", 
                        "Provider", "Description", "Estimated Cost"]
            
            # Container frame
            container = ttk.Frame(report_window)
            container.pack(fill="both", expand=True, padx=10, pady=10)
            
            # Add header
            ttk.Label(container, text="Upcoming Scheduled Maintenance", 
                     font=("Arial", 14, "bold")).pack(pady=(0, 10))
            
            # Create treeview with scrollbars
            tree_frame = ttk.Frame(container)
            tree_frame.pack(fill="both", expand=True)
            
            tree = ttk.Treeview(tree_frame, columns=columns, show="headings")
            
            # Add scrollbars
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
            for i, col in enumerate(columns):
                tree.heading(col, text=col)
                # Adjust width based on content type
                if i == 0:  # ID
                    tree.column(col, anchor="center", width=50)
                elif i == 7:  # Cost
                    tree.column(col, anchor="center", width=100)
                elif i == 4:  # Date
                    tree.column(col, anchor="center", width=120)
                elif i == 6:  # Description
                    tree.column(col, anchor="w", width=200)
                else:
                    tree.column(col, anchor="w", width=120)
            
            # Add data
            for row in results:
                # Format costs to show currency
                formatted_row = list(row)
                if formatted_row[7]:  # Estimated cost
                    formatted_row[7] = f"${float(formatted_row[7]):.2f}"
                
                tree.insert("", "end", values=formatted_row)
            
            # Add buttons
            button_frame = ttk.Frame(container)
            button_frame.pack(fill="x", pady=10)
            
            ttk.Button(
                button_frame, 
                text="Export to CSV", 
                command=lambda: form_utils.export_to_csv(report_window, tree, "Upcoming_Maintenance")
            ).pack(side="left", padx=5)
            
            ttk.Button(
                button_frame,
                text="Close",
                command=report_window.destroy
            ).pack(side="right", padx=5)
            
        except Exception as e:
            logger.error(f"Error showing upcoming maintenance: {e}")
            messagebox.showerror("Report Error", str(e))
    
    def show_maintenance_costs(self):
        """Show maintenance cost summary"""
        try:
            # Query to get maintenance costs by vehicle and type
            query = """
            SELECT v.Registration_Number, CONCAT(v.Make, ' ', v.Model) as Vehicle,
                   mt.Type_Name, COUNT(*) as Maintenance_Count,
                   SUM(m.Actual_Cost) as Total_Cost
            FROM Maintenance m
            JOIN Vehicle v ON m.Vehicle_ID = v.Vehicle_ID
            JOIN Maintenance_Type mt ON m.Maintenance_Type_ID = mt.Maintenance_Type_ID
            WHERE m.Actual_Cost IS NOT NULL AND m.Actual_Cost > 0
            GROUP BY v.Registration_Number, Vehicle, mt.Type_Name
            ORDER BY v.Registration_Number, mt.Type_Name
            """
            
            results = db.execute_query(query)
            
            if not results:
                messagebox.showinfo("No Cost Data", "No maintenance cost data found.")
                return
            
            # Create report window
            report_window = tk.Toplevel(self.root)
            report_window.title("Maintenance Cost Summary")
            report_window.geometry("800x600")
            
            # Create treeview for results
            columns = ["Registration", "Vehicle", "Maintenance Type", "Count", "Total Cost"]
            
            # Container frame
            container = ttk.Frame(report_window)
            container.pack(fill="both", expand=True, padx=10, pady=10)
            
            # Add header
            ttk.Label(container, text="Maintenance Cost Summary", 
                     font=("Arial", 14, "bold")).pack(pady=(0, 10))
            
            # Create treeview with scrollbars
            tree_frame = ttk.Frame(container)
            tree_frame.pack(fill="both", expand=True)
            
            tree = ttk.Treeview(tree_frame, columns=columns, show="headings")
            
            # Add scrollbars
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
            for i, col in enumerate(columns):
                tree.heading(col, text=col)
                # Adjust width based on content type
                if i in [3]:  # Count
                    tree.column(col, anchor="center", width=70)
                elif i == 4:  # Cost
                    tree.column(col, anchor="center", width=120)
                else:
                    tree.column(col, anchor="w", width=150)
            
            # Add data and calculate total
            total_cost = 0
            for row in results:
                # Format costs to show currency
                formatted_row = list(row)
                if formatted_row[4]:  # Total cost
                    cost_value = float(formatted_row[4])
                    total_cost += cost_value
                    formatted_row[4] = f"${cost_value:.2f}"
                
                tree.insert("", "end", values=formatted_row)
            
            # Add summary frame
            summary_frame = ttk.LabelFrame(container, text="Summary")
            summary_frame.pack(fill="x", pady=10)
            
            ttk.Label(summary_frame, text=f"Total Maintenance Cost: ${total_cost:.2f}", 
                     font=("Arial", 12)).pack(pady=5)
            
            # Add buttons
            button_frame = ttk.Frame(container)
            button_frame.pack(fill="x", pady=10)
            
            ttk.Button(
                button_frame, 
                text="Export to CSV", 
                command=lambda: form_utils.export_to_csv(report_window, tree, "Maintenance_Costs")
            ).pack(side="left", padx=5)
            
            ttk.Button(
                button_frame,
                text="Close",
                command=report_window.destroy
            ).pack(side="right", padx=5)
            
        except Exception as e:
            logger.error(f"Error showing maintenance costs: {e}")
            messagebox.showerror("Report Error", str(e))
    
    def show_help(self):
        """Show help dialog"""
        help_text = """
        Maintenance Management Help
        
        This module allows you to manage vehicle maintenance including:
        - Scheduled maintenance
        - Maintenance history
        - Maintenance types
        - Cost tracking
        
        Features:
        - View, add, edit, and delete maintenance records
        - Schedule new maintenance
        - Generate maintenance reports
        - Track maintenance costs
        - Export data to CSV
        
        Common Operations:
        - To add a new maintenance record, click the Add button
        - To edit a record, select it and click Edit
        - To delete a record, select it and click Delete
        - To search, enter text in the search box and click Search
        - To schedule maintenance, use the Tools menu
        - For reports, use the Reports menu
        """
        
        help_window = tk.Toplevel(self.root)
        help_window.title("Maintenance Management Help")
        help_window.geometry("500x400")
        
        text = tk.Text(help_window, wrap="word")
        text.pack(fill="both", expand=True, padx=10, pady=10)
        text.insert("1.0", help_text)
        text.config(state="disabled")
    
    def show_about(self):
        """Show about dialog"""
        messagebox.showinfo(
            "About Maintenance Management",
            "Maintenance Management Module\nVersion 1.0.0\n\n" +
            "Part of the Fleet Management System\n\n" +
            "© 2025 Fleet Management System"
        )

# Main entry point
def main():
    root = tk.Tk()
    app = MaintenanceManagement(root)
    root.mainloop()

if __name__ == "__main__":
    main()