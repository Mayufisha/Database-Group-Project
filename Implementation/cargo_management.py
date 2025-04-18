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
logger = logging.getLogger("cargo_management")

# Load environment variables
load_dotenv()

class CargoManagement:
    def __init__(self, root):
        self.root = root
        self.root.title("Cargo Management")
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
        
        # Tools menu
        tools_menu = tk.Menu(menubar, tearoff=0)
        tools_menu.add_command(label="Refresh All Data", command=self.refresh_all_data)
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
            "Cargo",
            "Cargo_Type"
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
    
    def show_help(self):
        """Show help dialog"""
        help_text = """
        Cargo Management Help
        
        This module allows you to manage cargo and cargo types.
        
        Features:
        - View, add, edit, and delete cargo records
        - Manage cargo types
        - Search for specific records
        - Export data to CSV
        
        Common Operations:
        - To add a new record, click the Add button
        - To edit a record, select it and click Edit
        - To delete a record, select it and click Delete
        - To search, enter text in the search box and click Search
        - To export data, click Export CSV or use the File menu
        """
        
        help_window = tk.Toplevel(self.root)
        help_window.title("Cargo Management Help")
        help_window.geometry("500x400")
        
        text = tk.Text(help_window, wrap="word")
        text.pack(fill="both", expand=True, padx=10, pady=10)
        text.insert("1.0", help_text)
        text.config(state="disabled")
    
    def show_about(self):
        """Show about dialog"""
        messagebox.showinfo(
            "About Cargo Management",
            "Cargo Management Module\nVersion 1.0.0\n\n" +
            "Part of the Fleet Management System\n\n" +
            "© 2025 Fleet Management System"
        )

# Main entry point
def main():
    root = tk.Tk()
    app = CargoManagement(root)
    root.mainloop()

if __name__ == "__main__":
    main()