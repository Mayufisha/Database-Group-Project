import os
import sys
import importlib
import tkinter as tk
from tkinter import ttk, messagebox
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
logger = logging.getLogger("module_loader")

def load_module(module_name):
    """Load a module and patch it with admin navigation
    
    Args:
        module_name: Name of the module file without .py extension
    """
    logger.info(f"Loading module: {module_name}")
    
    # Import return_to_admin module
    try:
        import return_to_admin
    except ImportError:
        logger.error("return_to_admin module not found")
        return
    
    # Patch modules with admin navigation
    return_to_admin.patch_module_files()
    
    # Import the requested module
    try:
        module_file = f"{module_name}.py"
        if not os.path.exists(module_file):
            logger.error(f"Module file {module_file} not found")
            return
        
        # Use importlib to load the module
        spec = importlib.util.spec_from_file_location(module_name, module_file)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        # Call the main function if it exists
        if hasattr(module, 'main'):
            module.main()
        else:
            logger.error(f"Module {module_name} has no main function")
    
    except Exception as e:
        logger.error(f"Error loading module {module_name}: {e}")
        messagebox.showerror("Module Error", f"Error loading {module_name}: {e}")

if __name__ == "__main__":
    # Check if module name was provided
    if len(sys.argv) > 1:
        module_name = sys.argv[1]
        load_module(module_name)
    else:
        print("Usage: python module_loader.py <module_name>")