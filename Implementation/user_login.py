import subprocess
import tkinter as tk
from tkinter import ttk, messagebox
import os
import sys
import hashlib
import json
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("fleet_management.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("user_login")

# User credentials file path
CREDENTIALS_FILE = 'config/users.json'

# Ensure config directory exists
Path('config').mkdir(exist_ok=True)

# Default credentials (used if file doesn't exist)
DEFAULT_CREDENTIALS = {
    "admin": {
        "password_hash": hashlib.sha256("12345".encode()).hexdigest(),
        "role": "admin"
    },
    "local": {
        "password_hash": hashlib.sha256("12345".encode()).hexdigest(),
        "role": "local"
    }
}

def save_default_credentials():
    """Save default credentials if file doesn't exist"""
    if not os.path.exists(CREDENTIALS_FILE):
        os.makedirs(os.path.dirname(CREDENTIALS_FILE), exist_ok=True)
        with open(CREDENTIALS_FILE, 'w') as f:
            json.dump(DEFAULT_CREDENTIALS, f, indent=4)
        logger.info("Created default credentials file")

def get_user_credentials():
    """Load user credentials from file"""
    if not os.path.exists(CREDENTIALS_FILE):
        save_default_credentials()
        
    try:
        with open(CREDENTIALS_FILE, 'r') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading credentials: {e}")
        return DEFAULT_CREDENTIALS

def hash_password(password):
    """Create a SHA-256 hash of the password"""
    return hashlib.sha256(password.encode()).hexdigest()

class UserLoginSystem:
    def __init__(self, root):
        self.root = root
        self.root.title("Fleet Management System - User Login")
        self.root.geometry("400x450")
        self.root.resizable(False, False)
        self.root.configure(bg='#f0f0f0')
        
        # Set app icon if available
        try:
            self.root.iconbitmap('assets/icon.ico')
        except:
            pass
        
        self.create_widgets()
    
    def create_widgets(self):
        # Main frame
        self.main_frame = ttk.Frame(self.root, padding=20)
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Logo/header image if available
        try:
            logo_img = tk.PhotoImage(file='assets/logo.png')
            logo_label = ttk.Label(self.main_frame, image=logo_img)
            logo_label.image = logo_img  # Keep a reference
            logo_label.pack(pady=15)
        except:
            # Fallback to text header
            header = ttk.Label(
                self.main_frame, 
                text="User Login",
                font=("Arial", 18, "bold")
            )
            header.pack(pady=15)
        
        # Login frame
        login_frame = ttk.LabelFrame(self.main_frame, text="Enter User Credentials", padding=15)
        login_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Username
        ttk.Label(login_frame, text="Username").pack(anchor="w", pady=(0, 5))
        self.username_var = tk.StringVar()
        self.username_entry = ttk.Entry(login_frame, textvariable=self.username_var, width=30)
        self.username_entry.pack(fill=tk.X, pady=(0, 15))
        
        # Password
        ttk.Label(login_frame, text="Password").pack(anchor="w", pady=(0, 5))
        self.password_var = tk.StringVar()
        self.password_entry = ttk.Entry(login_frame, textvariable=self.password_var, show="•", width=30)
        self.password_entry.pack(fill=tk.X, pady=(0, 20))
        
        # Button frame
        button_frame = ttk.Frame(login_frame)
        button_frame.pack(fill=tk.X, pady=5)
        
        # Login button
        self.login_button = ttk.Button(
            button_frame, 
            text="Login",
            command=self.login
        )
        self.login_button.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        # Back button
        self.back_button = ttk.Button(
            button_frame, 
            text="Back",
            command=self.go_back
        )
        self.back_button.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        # Bind Enter key to login
        self.root.bind('<Return>', lambda event: self.login())
        
        # Status message
        self.status_var = tk.StringVar()
        self.status_label = ttk.Label(
            self.main_frame, 
            textvariable=self.status_var,
            foreground="red"
        )
        self.status_label.pack(pady=10)
        
        # Version info
        version_label = ttk.Label(
            self.main_frame, 
            text="Version 1.0.0",
            font=("Arial", 8),
            foreground="gray"
        )
        version_label.pack(side=tk.BOTTOM, pady=5)
        
        # Set focus to username entry
        self.username_entry.focus()
    
    def login(self):
        username = self.username_var.get()
        password = self.password_var.get()
        
        if not username or not password:
            self.status_var.set("Please enter both username and password")
            return
        
        # Get user credentials
        credentials = get_user_credentials()
        
        # Check if user exists and has local role
        if (username in credentials and 
            credentials[username]["password_hash"] == hash_password(password) and
            credentials[username]["role"] == "local"):
            
            logger.info(f"User {username} logged in")
            self.status_var.set("Login successful!")
            
            # Launch local user portal
            self.root.destroy()
            subprocess.Popen([sys.executable, "local_user_portal.py"])
        else:
            self.status_var.set("Invalid user credentials")
            logger.warning(f"Failed user login attempt for user: {username}")
            # Clear password field
            self.password_var.set("")
            self.password_entry.focus()
    
    def go_back(self):
        """Return to landing page"""
        self.root.destroy()
        subprocess.Popen([sys.executable, "landing_page.py"])

# Run the application
if __name__ == "__main__":
    root = tk.Tk()
    app = UserLoginSystem(root)
    root.mainloop()