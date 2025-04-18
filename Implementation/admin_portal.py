import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import os
import sys
import subprocess
import logging
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
logger = logging.getLogger("admin_portal")

class AdminPortal:
    def __init__(self, root):
        self.root = root
        self.root.title("Fleet Management System - Admin Portal")
        self.root.geometry("900x600")
        self.root.minsize(800, 600)
        
        # Configure button style
        style = ttk.Style()
        style.configure('Module.TButton', font=('Arial', 12), padding=10)
        
        # Main frame
        self.main_frame = ttk.Frame(self.root, padding=20)
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        self.create_ui()
    
    def create_ui(self):
        """Create the main UI"""
        # Header
        header_frame = ttk.Frame(self.main_frame)
        header_frame.pack(fill=tk.X, pady=(0, 20))
        
        ttk.Label(
            header_frame, 
            text="Administrator Portal",
            font=("Arial", 24, "bold")
        ).pack(side=tk.LEFT)
        
        # User info and logout
        user_frame = ttk.Frame(header_frame)
        user_frame.pack(side=tk.RIGHT)
        
        ttk.Label(
            user_frame,
            text=f"Logged in as: Admin",
            font=("Arial", 10)
        ).pack(pady=2)
        
        ttk.Button(
            user_frame,
            text="Logout",
            command=self.logout
        ).pack(pady=2)
        
        # Create module grid
        self.create_module_grid()
    
    def create_module_grid(self):
        """Create grid of module buttons"""
        # Module grid frame
        module_frame = ttk.Frame(self.main_frame)
        module_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Configure grid with 3 columns
        for i in range(3):
            module_frame.columnconfigure(i, weight=1)
        
        # Configure grid with 3 rows
        for i in range(3):
            module_frame.rowconfigure(i, weight=1)
        
        # Define modules
        modules = [
            {
                "name": "General Administration",
                "description": "System administration and configuration",
                "command": self.open_admin_portal,
                "row": 0,
                "column": 0
            },
            {
                "name": "Cargo Management",
                "description": "Manage cargo and cargo types",
                "command": self.open_cargo_management,
                "row": 0,
                "column": 1
            },
            {
                "name": "Customer Management",
                "description": "Manage customer information",
                "command": self.open_customer_management,
                "row": 0,
                "column": 2
            },
            {
                "name": "Driver Management",
                "description": "Manage drivers and qualifications",
                "command": self.open_driver_management,
                "row": 1,
                "column": 0
            },
            {
                "name": "Maintenance Management",
                "description": "Vehicle maintenance scheduling",
                "command": self.open_maintenance_management,
                "row": 1,
                "column": 1
            },
            {
                "name": "Service Management",
                "description": "Manage service providers",
                "command": self.open_service_management,
                "row": 1,
                "column": 2
            },
            {
                "name": "System Logs",
                "description": "View system logs and activity",
                "command": self.open_logs,
                "row": 2,
                "column": 1
            }
        ]
        
        # Create module buttons
        for module in modules:
            frame = ttk.Frame(module_frame, padding=10)
            frame.grid(row=module["row"], column=module["column"], 
                      sticky="nsew", padx=10, pady=10)
            
            # Add button
            ttk.Button(
                frame,
                text=module["name"],
                style='Module.TButton',
                command=module["command"]
            ).pack(fill=tk.BOTH, expand=True, pady=5)
            
            # Add description
            ttk.Label(
                frame,
                text=module["description"],
                wraplength=150,
                justify="center"
            ).pack(pady=5)
    
    def open_admin_portal(self):
        """Open the admin user portal"""
        logger.info("Opening Admin User Portal")
        self.root.withdraw()
        
        # Start the module through our loader
        process = subprocess.Popen([sys.executable, "module_loader.py", "admin_user_portal"])
        
        # Wait for the process to complete
        process.wait()
        
        # Show this window again
        self.root.deiconify()
    
    def open_cargo_management(self):
        """Open the cargo management module"""
        logger.info("Opening Cargo Management")
        self.root.withdraw()
        
        # Start the module through our loader
        process = subprocess.Popen([sys.executable, "module_loader.py", "cargo_management"])
        
        # Wait for the process to complete
        process.wait()
        
        # Show this window again
        self.root.deiconify()
    
    def open_customer_management(self):
        """Open the customer management module"""
        logger.info("Opening Customer Management")
        self.root.withdraw()
        
        # Start the module through our loader
        process = subprocess.Popen([sys.executable, "module_loader.py", "customer_management"])
        
        # Wait for the process to complete
        process.wait()
        
        # Show this window again
        self.root.deiconify()
    
    def open_driver_management(self):
        """Open the driver management module"""
        logger.info("Opening Driver Management")
        self.root.withdraw()
        
        # Start the module through our loader
        process = subprocess.Popen([sys.executable, "module_loader.py", "driver_management"])
        
        # Wait for the process to complete
        process.wait()
        
        # Show this window again
        self.root.deiconify()
    
    def open_maintenance_management(self):
        """Open the maintenance management module"""
        logger.info("Opening Maintenance Management")
        self.root.withdraw()
        
        # Start the module through our loader
        process = subprocess.Popen([sys.executable, "module_loader.py", "maintenance_management"])
        
        # Wait for the process to complete
        process.wait()
        
        # Show this window again
        self.root.deiconify()
    
    def open_service_management(self):
        """Open the service management module"""
        logger.info("Opening Service Management")
        self.root.withdraw()
        
        # Start the module through our loader
        process = subprocess.Popen([sys.executable, "module_loader.py", "service_management"])
        
        # Wait for the process to complete
        process.wait()
        
        # Show this window again
        self.root.deiconify()
    
    def open_logs(self):
        """Open the system logs viewer"""
        logger.info("Opening System Logs")
        
        # Create logs window
        logs_window = tk.Toplevel(self.root)
        logs_window.title("System Logs")
        logs_window.geometry("900x600")
        logs_window.transient(self.root)
        logs_window.grab_set()
        
        # Create UI
        ttk.Label(
            logs_window, 
            text="System Logs",
            font=("Arial", 16, "bold")
        ).pack(pady=10, padx=10, anchor="w")
        
        # Create log view with scrollbars
        log_frame = ttk.Frame(logs_window)
        log_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        log_text = scrolledtext.ScrolledText(log_frame, wrap=tk.WORD)
        log_text.pack(fill=tk.BOTH, expand=True)
        
        # Load log file
        try:
            with open("fleet_management.log", "r") as f:
                log_content = f.read()
                log_text.insert(tk.END, log_content)
                log_text.see(tk.END)  # Scroll to bottom
        except Exception as e:
            logger.error(f"Error reading log file: {e}")
            log_text.insert(tk.END, f"Error reading log file: {e}")
        
        # Make text read-only
        log_text.config(state=tk.DISABLED)
        
        # Refresh button
        button_frame = ttk.Frame(logs_window)
        button_frame.pack(fill=tk.X, padx=10, pady=10)
        
        def refresh_logs():
            log_text.config(state=tk.NORMAL)
            log_text.delete(1.0, tk.END)
            
            try:
                with open("fleet_management.log", "r") as f:
                    log_content = f.read()
                    log_text.insert(tk.END, log_content)
                    log_text.see(tk.END)  # Scroll to bottom
            except Exception as e:
                logger.error(f"Error reading log file: {e}")
                log_text.insert(tk.END, f"Error reading log file: {e}")
            
            log_text.config(state=tk.DISABLED)
            
            # Update timestamp
            timestamp_var.set(f"Last refreshed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        ttk.Button(
            button_frame,
            text="Refresh Logs",
            command=refresh_logs
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            button_frame,
            text="Close",
            command=logs_window.destroy
        ).pack(side=tk.RIGHT, padx=5)
        
        # Last refresh timestamp
        timestamp_var = tk.StringVar(value=f"Last refreshed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        ttk.Label(
            logs_window,
            textvariable=timestamp_var,
            font=("Arial", 8),
            foreground="gray"
        ).pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=5)
    
    def logout(self):
        """Logout and return to landing page"""
        logger.info("Admin logged out")
        self.root.destroy()
        subprocess.Popen([sys.executable, "landing_page.py"])
        
# Main application entry point
def main():
    root = tk.Tk()
    app = AdminPortal(root)
    root.mainloop()

if __name__ == "__main__":
    main()