import tkinter as tk
from tkinter import ttk, messagebox
import os
import subprocess
import sys
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("fleet_management.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("landing_page")

class LandingPage:
    def __init__(self, root):
        self.root = root
        self.root.title("Fleet Management System")
        self.root.geometry("800x500")
        self.root.minsize(800, 500)
        
        # Configure style for buttons
        style = ttk.Style()
        style.configure('PortalButton.TButton', font=('Arial', 12, 'bold'), padding=20)
        style.configure('ModuleButton.TButton', font=('Arial', 11), padding=10)
        
        # Main frame
        self.main_frame = ttk.Frame(self.root, padding=20)
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create header
        self.create_header()
        
        # Initial view - Portal Selection
        self.create_portal_selection()
        
    def create_header(self):
        """Create header with app title and logo if available"""
        header_frame = ttk.Frame(self.main_frame)
        header_frame.pack(fill=tk.X, pady=(0, 20))
        
        # Try to load logo if available
        try:
            logo_img = tk.PhotoImage(file='assets/logo.png')
            logo_label = ttk.Label(header_frame, image=logo_img)
            logo_label.image = logo_img  # Keep a reference
            logo_label.pack(side=tk.LEFT, padx=(0, 20))
        except:
            pass
            
        # App title
        title_label = ttk.Label(
            header_frame, 
            text="Fleet Management System",
            font=("Arial", 24, "bold")
        )
        title_label.pack(side=tk.LEFT, pady=10)
        
    def create_portal_selection(self):
        """Create portal selection view with large buttons"""
        # Clear existing content if any
        for widget in self.main_frame.winfo_children():
            if widget != self.main_frame.winfo_children()[0]:  # Skip header
                widget.destroy()
        
        # Container for portal buttons
        portal_frame = ttk.Frame(self.main_frame)
        portal_frame.pack(expand=True, fill=tk.BOTH, padx=50, pady=20)
        
        # Configure grid with 2 columns
        portal_frame.columnconfigure(0, weight=1)
        portal_frame.columnconfigure(1, weight=1)
        
        # Admin portal button (left)
        admin_frame = ttk.Frame(portal_frame, padding=20)
        admin_frame.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)
        
        ttk.Label(
            admin_frame, 
            text="Administrator Portal",
            font=("Arial", 16, "bold")
        ).pack(pady=(0, 10))
        
        ttk.Button(
            admin_frame,
            text="Admin Login",
            style='PortalButton.TButton',
            command=self.open_admin_login
        ).pack(expand=True, fill=tk.BOTH, padx=20, pady=20)
        
        # User portal button (right)
        user_frame = ttk.Frame(portal_frame, padding=20)
        user_frame.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
        
        ttk.Label(
            user_frame, 
            text="User Portal",
            font=("Arial", 16, "bold")
        ).pack(pady=(0, 10))
        
        ttk.Button(
            user_frame,
            text="User Login",
            style='PortalButton.TButton',
            command=self.open_user_login
        ).pack(expand=True, fill=tk.BOTH, padx=20, pady=20)
        
        # Version info at bottom
        version_label = ttk.Label(
            self.main_frame, 
            text="Version 1.0.0",
            font=("Arial", 8),
            foreground="gray"
        )
        version_label.pack(side=tk.BOTTOM, pady=5)
        
    def open_admin_login(self):
        """Open admin login screen"""
        logger.info("Admin Login selected")
        self.root.withdraw()  # Hide main window
        
        # Launch admin login
        subprocess.Popen([sys.executable, "admin_login.py"])
        self.root.destroy()  # Close this window
        
    def open_user_login(self):
        """Open user login screen"""
        logger.info("User Login selected")
        self.root.withdraw()  # Hide main window
        
        # Launch user login
        subprocess.Popen([sys.executable, "user_login.py"])
        self.root.destroy()  # Close this window
        
# Main application entry point
def main():
    root = tk.Tk()
    app = LandingPage(root)
    root.mainloop()

if __name__ == "__main__":
    main()