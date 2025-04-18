import os
import return_to_admin

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import logging
from dotenv import load_dotenv
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
logger = logging.getLogger("customer_management")

# Load environment variables
load_dotenv()

class CustomerManagement:
    def __init__(self, root):
        self.root = root
        self.root.title("Customer Management")
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
        reports_menu.add_command(label="Customer Summary", command=self.show_customer_summary)
        reports_menu.add_command(label="Customer Locations", command=self.show_customer_locations)
        menubar.add_cascade(label="Reports", menu=reports_menu)
        
        # Tools menu
        tools_menu = tk.Menu(menubar, tearoff=0)
        tools_menu.add_command(label="Refresh All Data", command=self.refresh_all_data)
        tools_menu.add_command(label="Advanced Search", command=self.show_advanced_search)
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
            "Customer",
            "Customer_Address",
            "Load_Customer"
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
        search_window.title("Advanced Customer Search")
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
    
    def show_customer_summary(self):
        """Show customer summary report"""
        try:
            # Get customer count
            customer_count = db.execute_query("SELECT COUNT(*) FROM Customer")[0][0]
            
            # Get address count
            address_count = db.execute_query("SELECT COUNT(*) FROM Customer_Address")[0][0]
            
            # Get load count
            load_count = db.execute_query("SELECT COUNT(*) FROM Load_Customer")[0][0]
            
            # Show in a dialog
            summary = f"Customer Summary Report\n\n" \
                      f"Total Customers: {customer_count}\n" \
                      f"Customer Addresses: {address_count}\n" \
                      f"Customer Loads: {load_count}\n"
                      
            messagebox.showinfo("Customer Summary", summary)
        except Exception as e:
            logger.error(f"Error generating summary: {e}")
            messagebox.showerror("Report Error", str(e))
    
    def show_customer_locations(self):
        """Show customer locations report"""
        try:
            # Query to get customers with locations
            query = """
            SELECT c.Customer_ID, c.First_Name, c.Last_Name, a.City, a.State, a.Country
            FROM Customer c
            JOIN Customer_Address ca ON c.Customer_ID = ca.Customer_ID
            JOIN Address a ON ca.Address_ID = a.Address_ID
            ORDER BY a.Country, a.State, a.City
            """
            
            results = db.execute_query(query)
            
            if not results:
                messagebox.showinfo("Customer Locations", "No customer location data found.")
                return
            
            # Create report window
            report_window = tk.Toplevel(self.root)
            report_window.title("Customer Locations Report")
            report_window.geometry("700x500")
            
            # Create treeview for results
            columns = ["Customer_ID", "First_Name", "Last_Name", "City", "State", "Country"]
            tree = ttk.Treeview(report_window, columns=columns, show="headings")
            
            # Add scrollbars
            vsb = ttk.Scrollbar(report_window, orient="vertical", command=tree.yview)
            hsb = ttk.Scrollbar(report_window, orient="horizontal", command=tree.xview)
            tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
            
            # Pack components
            tree.pack(side="left", fill="both", expand=True)
            vsb.pack(side="right", fill="y")
            hsb.pack(side="bottom", fill="x")
            
            # Configure columns
            for col in columns:
                tree.heading(col, text=col.replace("_", " "))
                tree.column(col, anchor="center", width=100)
            
            # Add data
            for row in results:
                tree.insert("", "end", values=row)
            
            # Add export button
            ttk.Button(
                report_window, 
                text="Export Report", 
                command=lambda: form_utils.export_to_csv(report_window, tree, "Customer_Locations")
            ).pack(pady=10)
            
        except Exception as e:
            logger.error(f"Error generating locations report: {e}")
            messagebox.showerror("Report Error", str(e))
    
    def show_help(self):
        """Show help dialog"""
        help_text = """
        Customer Management Help
        
        This module allows you to manage customer information including:
        - Customer personal details
        - Customer addresses
        - Customer load assignments
        
        Features:
        - View, add, edit, and delete customer records
        - Search for specific customers
        - Generate reports
        - Export data to CSV
        
        Common Operations:
        - To add a new customer, click the Add button
        - To edit a customer, select the record and click Edit
        - To delete a customer, select the record and click Delete
        - To search, enter text in the search box and click Search
        - For advanced search options, use the Tools menu
        """
        
        help_window = tk.Toplevel(self.root)
        help_window.title("Customer Management Help")
        help_window.geometry("700x400")
        
        text = tk.Text(help_window, wrap="word")
        text.pack(fill="both", expand=True, padx=10, pady=10)
        text.insert("1.0", help_text)
        text.config(state="disabled")
    
    def show_about(self):
        """Show about dialog"""
        messagebox.showinfo(
            "About Customer Management",
            "Customer Management Module\nVersion 1.0.0\n\n" +
            "Part of the Fleet Management System\n\n" +
            "© 2025 Fleet Management System"
        )

# Main entry point
def main():
    root = tk.Tk()
    app = CustomerManagement(root)
    root.mainloop()

if __name__ == "__main__":
    main()