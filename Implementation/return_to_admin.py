# This file is imported by modules to add "Return to Admin Portal" button
import tkinter as tk
from tkinter import ttk
import logging

# Configure logging
logger = logging.getLogger("return_to_admin")

def add_return_button(root, menubar=None):
    '''Add a return to admin portal button or menu item'''
    
    if menubar:
        # Add to existing menu
        admin_menu = tk.Menu(menubar, tearoff=0)
        admin_menu.add_command(label="Return to Admin Portal", command=root.destroy)
        admin_menu.add_command(label="Logout", command=lambda: exit(0))
        menubar.add_cascade(label="Admin", menu=admin_menu)
        logger.info("Added admin navigation to menu bar")
    else:
        # Create a button at the bottom
        return_frame = ttk.Frame(root)
        return_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=5)
        
        ttk.Button(
            return_frame,
            text="Return to Admin Portal",
            command=root.destroy
        ).pack(side=tk.RIGHT, padx=5)
        
        logger.info("Added return to admin button")

def patch_module_files():
    """Patch each module file to import and use the return_to_admin module"""
    import os
    
    # List of module files to patch
    module_files = [
        "admin_user_portal.py",
        "cargo_management.py",
        "customer_management.py",
        "driver_management.py",
        "maintenance_management.py",
        "service_management.py"
    ]
    
    for file_name in module_files:
        if not os.path.exists(file_name):
            logger.warning(f"Module file {file_name} not found")
            continue
        
        try:
            with open(file_name, "r") as f:
                content = f.read()
            
            # Check if already patched
            if "import return_to_admin" in content:
                logger.info(f"Module {file_name} already patched")
                continue
            
            # Find the class init method
            class_name = file_name.replace(".py", "").split("_")
            class_name = "".join(word.capitalize() for word in class_name)
            
            # Look for the create_menu method
            if "def create_menu(self" in content:
                # Add import at the top of the file
                import_line = "import return_to_admin\n"
                if "import os" in content:
                    content = content.replace("import os", "import os\n" + import_line)
                else:
                    content = import_line + content
                
                # Add return button to create_menu method
                create_menu_str = "def create_menu(self):"
                create_menu_end = "self.root.config(menu=menubar)"
                
                # Add line to call our function after menu is created
                new_code = create_menu_end + "\n        # Add admin navigation\n        return_to_admin.add_return_button(self.root, menubar)"
                content = content.replace(create_menu_end, new_code)
                
                # Write back the modified file
                with open(file_name, "w") as f:
                    f.write(content)
                
                logger.info(f"Successfully patched {file_name} with admin navigation")
            else:
                logger.warning(f"Could not find create_menu method in {file_name}")
        
        except Exception as e:
            logger.error(f"Error patching {file_name}: {e}")

if __name__ == "__main__":
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler("fleet_management.log"),
            logging.StreamHandler()
        ]
    )
    
    # Run the patcher
    patch_module_files()