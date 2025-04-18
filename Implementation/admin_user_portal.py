import os
import return_to_admin

import tkinter as tk
from tkinter import ttk, messagebox
import threading
from dotenv import load_dotenv
import logging
import database_connection as db
import form_utils

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("fleet_management.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("admin_portal")

# Load environment variables
load_dotenv()

# Global variables for tracking loaded tabs
loaded_tabs = {}

class AdminPortal:
    def __init__(self, root):
        self.root = root
        self.root.title("Fleet Management - Admin Portal")
        self.root.geometry("1400x800")
        self.root.minsize(800, 600)
        
        # Create menu
        self.create_menu()
        
        # Show a loading message
        self.loading_label = tk.Label(root, text="Initializing...", font=("Arial", 16))
        self.loading_label.pack(expand=True)
        
        # Create the UI in a separate thread to keep the window responsive
        threading.Thread(target=self.setup_ui, daemon=True).start()
    
    def create_menu(self):
        """Create application menu"""
        menubar = tk.Menu(self.root)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Export All Data", command=self.export_all_data)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)
        menubar.add_cascade(label="File", menu=file_menu)
        
        # Tools menu
        tools_menu = tk.Menu(menubar, tearoff=0)
        tools_menu.add_command(label="Refresh All Data", command=self.refresh_all_data)
        tools_menu.add_command(label="Advanced Search", command=self.show_advanced_search)
        menubar.add_cascade(label="Tools", menu=tools_menu)
        
        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label="User Manual", command=self.show_user_manual)
        help_menu.add_command(label="About", command=self.show_about)
        menubar.add_cascade(label="Help", menu=help_menu)
        
        self.root.config(menu=menubar)
        # Add admin navigation
        return_to_admin.add_return_button(self.root, menubar)
    
    def export_all_data(self):
        """Export all data to CSV files"""
        from tkinter import filedialog
        import os
        import return_to_admin
        
        # Ask for directory
        export_dir = filedialog.askdirectory(title="Select Export Directory")
        if not export_dir:
            return
        
        # Create progress dialog
        progress_window = tk.Toplevel(self.root)
        progress_window.title("Exporting Data")
        progress_window.geometry("300x150")
        progress_window.transient(self.root)
        progress_window.grab_set()
        
        ttk.Label(progress_window, text="Exporting data files...").pack(pady=10)
        
        progress_var = tk.DoubleVar()
        progress_bar = ttk.Progressbar(progress_window, variable=progress_var, maximum=100)
        progress_bar.pack(fill="x", padx=20, pady=10)
        
        status_var = tk.StringVar(value="Starting export...")
        status_label = ttk.Label(progress_window, textvariable=status_var)
        status_label.pack(pady=10)
        
        def do_export():
            # Define sections with their tables
            sections = {
                "Vehicle Management": [
                    "Vehicle", "Vehicle_Type", "Vehicle_Status_Type", 
                    "Vehicle_Load", "Fuel_Type"
                ],
                "Driver Management": [
                    "Driver", "Driver_Address", "Driver_Qualification", 
                    "Emergency_Contact", "Vehicle_Driver_Assignment"
                ],
                "Customer Management": [
                    "Customer", "Customer_Address", "Load_Customer"
                ],
                "Delivery Management": ["Delivery_Status"],
                "Cargo Management": ["Cargo", "Cargo_Type"],
                "Maintenance Management": ["Maintenance", "Maintenance_Type"],
                "Service Management": [
                    "Service_Provider", "Service_Provider_Address", "Service_Status"
                ],
                "Address Management": ["Location", "Address"]
            }
            
            # Flatten the list of tables
            all_tables = [table for tables in sections.values() for table in tables]
            total_tables = len(all_tables)
            
            for i, table in enumerate(all_tables):
                try:
                    # Update progress
                    progress = (i / total_tables) * 100
                    progress_var.set(progress)
                    status_var.set(f"Exporting {table}...")
                    
                    # Create filename
                    filename = os.path.join(export_dir, f"{table}.csv")
                    
                    # Export the data
                    db.export_data_to_csv(table, filename)
                    
                    # Brief pause to update UI
                    progress_window.update()
                except Exception as e:
                    logger.error(f"Error exporting {table}: {e}")
            
            # Complete
            progress_var.set(100)
            status_var.set("Export complete!")
            
            # Close after a delay
            progress_window.after(1500, progress_window.destroy)
        
        # Run export in background thread
        threading.Thread(target=do_export, daemon=True).start()
    
    def refresh_all_data(self):
        """Refresh all loaded treeviews"""
        # Get all loaded tabs
        for tab_id in loaded_tabs:
            if loaded_tabs[tab_id]:
                # Get the tab widget
                tab = self.notebook.nametowidget(tab_id)
                # Find treeview in the tab's children recursively
                for child in tab.winfo_children():
                    if isinstance(child, ttk.Frame) and "tree_frame" in str(child):
                        for subchild in child.winfo_children():
                            if isinstance(subchild, ttk.Treeview):
                                tree = subchild
                                # Get table name from tab title
                                table = self.get_table_from_tab(tab_id)
                                if table:
                                    # Refresh data
                                    form_utils.refresh_tree(tree, table)
        
        messagebox.showinfo("Refresh Complete", "All data has been refreshed.")
    
    def get_table_from_tab(self, tab_id):
        """Get table name from tab ID"""
        tab = self.notebook.nametowidget(tab_id)
        tab_text = self.notebook.tab(tab_id, "text")
        # Convert display name back to table name
        return tab_text.replace(" ", "_")
    
    def show_advanced_search(self):
        """Show advanced search dialog"""
        search_window = tk.Toplevel(self.root)
        search_window.title("Advanced Search")
        search_window.geometry("500x400")
        search_window.transient(self.root)
        search_window.grab_set()
        
        # Table selection
        ttk.Label(search_window, text="Select Table:").pack(anchor="w", padx=20, pady=(20, 5))
        
        # Get all table names
        tables = []
        for section in self.sections:
            tables.extend(self.sections[section])
        
        table_var = tk.StringVar()
        table_combo = ttk.Combobox(search_window, textvariable=table_var, values=tables, state="readonly")
        table_combo.pack(fill="x", padx=20, pady=5)
        if tables:
            table_combo.current(0)
        
        # Frame for search criteria
        criteria_frame = ttk.LabelFrame(search_window, text="Search Criteria")
        criteria_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        # We'll create this dynamically when a table is selected
        criteria_entries = []
        
        def update_criteria_fields(*args):
            # Clear existing fields
            for widget in criteria_frame.winfo_children():
                widget.destroy()
            
            criteria_entries.clear()
            
            # Get the selected table
            selected_table = table_var.get()
            if not selected_table:
                return
            
            # Get columns for the selected table
            columns = db.get_table_columns(selected_table)
            
            # Create entry for each column
            for i, col in enumerate(columns):
                row_frame = ttk.Frame(criteria_frame)
                row_frame.pack(fill="x", pady=2)
                
                ttk.Label(row_frame, text=col, width=20).pack(side="left")
                
                var = tk.StringVar()
                entry = ttk.Entry(row_frame, textvariable=var)
                entry.pack(side="left", fill="x", expand=True, padx=5)
                
                criteria_entries.append((col, var))
        
        # Update fields when table changes
        table_var.trace_add("write", update_criteria_fields)
        
        # Initially populate
        update_criteria_fields()
        
        # Results frame
        results_frame = ttk.LabelFrame(search_window, text="Results")
        results_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        # Treeview for results
        results_tree = ttk.Treeview(results_frame)
        results_tree.pack(fill="both", expand=True)
        
        # Buttons
        button_frame = ttk.Frame(search_window)
        button_frame.pack(fill="x", padx=20, pady=15)
        
        def do_search():
            # Get the selected table
            selected_table = table_var.get()
            if not selected_table:
                return
            
            # Collect search parameters
            search_params = []
            for col, var in criteria_entries:
                if var.get():  # Only include non-empty criteria
                    search_params.append((col, var.get()))
            
            try:
                # Perform search
                if search_params:
                    rows, _ = db.advanced_search_data(selected_table, search_params)
                else:
                    rows, _ = db.fetch_data_paginated(selected_table)
                
                # Update treeview columns
                columns = db.get_table_columns(selected_table)
                results_tree["columns"] = columns
                results_tree["show"] = "headings"
                
                for col in columns:
                    results_tree.heading(col, text=col)
                    results_tree.column(col, anchor="center", width=100)
                
                # Clear existing items
                results_tree.delete(*results_tree.get_children())
                
                # Add results
                for row in rows:
                    results_tree.insert("", "end", values=row)
                
            except Exception as e:
                messagebox.showerror("Search Error", str(e))
        
        ttk.Button(button_frame, text="Search", command=do_search).pack(side="left", padx=5)
        ttk.Button(button_frame, text="Export Results", 
                  command=lambda: form_utils.export_to_csv(search_window, results_tree, table_var.get())
                 ).pack(side="left", padx=5)
        ttk.Button(button_frame, text="Close", command=search_window.destroy).pack(side="right", padx=5)
    
    def show_user_manual(self):
        """Show user manual"""
        manual_window = tk.Toplevel(self.root)
        manual_window.title("User Manual")
        manual_window.geometry("600x500")
        
        # Create a text widget with scrollbar
        text_frame = ttk.Frame(manual_window)
        text_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        text_widget = tk.Text(text_frame, wrap="word")
        scrollbar = ttk.Scrollbar(text_frame, command=text_widget.yview)
        text_widget.configure(yscrollcommand=scrollbar.set)
        
        text_widget.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Add manual content
        manual_text = """
        # Fleet Management System User Manual
        
        ## Overview
        The Fleet Management System allows you to manage all aspects of your fleet operations, including vehicles, drivers, customers, cargo, and maintenance.
        
        ## Admin Portal
        The Admin Portal provides full access to all system features and data management capabilities.
        
        ### Data Management
        - Each section contains related data tables
        - Use the tabs to navigate between different data views
        - Data is loaded when you select a tab
        
        ### Common Operations
        - **Search**: Enter text in the search box and click Search
        - **Add**: Click the Add button to create a new record
        - **Edit**: Select a record and click Edit
        - **Delete**: Select a record and click Delete
        - **Export**: Click Export CSV to save the current view to a file
        
        ### Advanced Features
        - **Export All Data**: From the File menu, export all tables to CSV
        - **Refresh All Data**: From the Tools menu, refresh all loaded data
        - **Advanced Search**: From the Tools menu, search with multiple criteria
        
        ## Troubleshooting
        If you encounter any issues:
        1. Check your database connection
        2. Ensure you have proper permissions
        3. Check the log file for error details
        
        ## Contact Support
        For additional help, contact support@fleetmanagementsystem.com
        """
        
        text_widget.insert("1.0", manual_text)
        text_widget.configure(state="disabled")
    
    def show_about(self):
        """Show about dialog"""
        about_window = tk.Toplevel(self.root)
        about_window.title("About Fleet Management System")
        about_window.geometry("400x300")
        about_window.resizable(False, False)
        
        # App info
        ttk.Label(
            about_window, 
            text="Fleet Management System",
            font=("Arial", 16, "bold")
        ).pack(pady=(20, 5))
        
        ttk.Label(
            about_window, 
            text="Version 1.0.0",
            font=("Arial", 10)
        ).pack()
        
        ttk.Separator(about_window, orient="horizontal").pack(fill="x", padx=20, pady=20)
        
        # Description
        description = ttk.Label(
            about_window,
            text="A comprehensive solution for managing fleet operations, "
                 "vehicle maintenance, driver assignments, and cargo tracking.",
            wraplength=350,
            justify="center"
        )
        description.pack(padx=20)
        
        # Copyright
        ttk.Label(
            about_window,
            text="© 2025 Fleet Management System",
            font=("Arial", 8)
        ).pack(side="bottom", pady=20)
    
    def setup_ui(self):
        """Setup the main UI structure"""
        # Initialize main notebook
        self.notebook = ttk.Notebook(self.root)
        
        # Define sections with their tables
        self.sections = {
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
        for section_name, tables in self.sections.items():
            section_tab = ttk.Frame(self.notebook)
            self.notebook.add(section_tab, text=section_name)
            
            sub_notebook = ttk.Notebook(section_tab)
            sub_notebook.pack(expand=True, fill="both")
            
            # Setup tabs for each table in the section
            for table in tables:
                label = table.replace("_", " ").title()
                tab = ttk.Frame(sub_notebook)
                sub_notebook.add(tab, text=label)
                
                # Just set up the UI structure, don't load data yet
                form_utils.setup_tree_for_table(tab, table)
                
                # Store the tab id for lazy loading
                tab_id = sub_notebook.tabs()[-1]
                
            # Add callback for tab selection to implement lazy loading
            sub_notebook.bind("<<NotebookTabChanged>>", 
                             lambda event, nb=sub_notebook, tables=tables: 
                                 self.tab_selected(event, nb, tables))
        
        # Add callback for main notebook tab selection
        self.notebook.bind("<<NotebookTabChanged>>", 
                     lambda event: 
                         self.main_tab_selected(event))
        
        # Remove loading label and show the UI
        self.root.after(0, self.loading_label.destroy)
        self.root.after(0, lambda: self.notebook.pack(expand=True, fill="both"))
    
    def tab_selected(self, event, notebook, tables):
        """Callback for when a tab is selected"""
        selected_tab = notebook.select()
        if selected_tab:
            tab_index = notebook.index(selected_tab)
            if tab_index < len(tables):
                table = tables[tab_index]
                self.lazy_load_tab(notebook, selected_tab, table)
    
    def main_tab_selected(self, event):
        """Callback for when a main tab is selected"""
        # Just ensure the tab exists, no loading yet
        # Loading happens when subtabs are selected
        pass
    
    def lazy_load_tab(self, notebook, tab_id, table):
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
                                target=lambda: self.fetch_and_update_tree(tree, table),
                                daemon=True
                            ).start()
                            break
            # Mark tab as loaded
            loaded_tabs[tab_id] = True
    
    def fetch_and_update_tree(self, tree, table, search_params=None):
        """Fetch data and update treeview in a non-blocking way"""
        try:
            if search_params:
                column, value = search_params
                rows = db.search_data(table, column, value)
            else:
                rows, _ = db.fetch_data_paginated(table)
            
            # Update UI in the main thread
            tree.after(0, lambda: self.populate_tree(tree, rows))
        except Exception as e:
            tree.after(0, lambda: messagebox.showerror("Data Error", str(e)))
    
    def populate_tree(self, tree, data):
        """Populate treeview with data"""
        tree.delete(*tree.get_children())
        for row in data:
            tree.insert("", tk.END, values=row)

# Main application entry point
def main():
    root = tk.Tk()
    app = AdminPortal(root)
    root.mainloop()

if __name__ == "__main__":
    main()