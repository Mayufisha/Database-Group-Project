Version 1 Read Me

# Fleet Management System

A comprehensive solution for managing fleet operations, vehicle maintenance, driver assignments, and cargo tracking.

## Overview

The Fleet Management System is a desktop application built with Python and Tkinter that provides a complete solution for businesses to manage their vehicle fleets. The system includes separate portals for administrators and local users, with appropriate access controls and functionality.

## Features

### Administrator Portal
- Complete fleet data management
- Vehicle tracking and status monitoring
- Driver management and assignment
- Customer and delivery tracking
- Maintenance scheduling and tracking
- Advanced search capabilities
- Data export to CSV

### Local User Portal
- Read-only access to fleet data
- Search functionality
- Predefined reports:
  - Vehicle Status
  - Driver Assignments
  - Upcoming Maintenance
- Data export capabilities

### Security
- User authentication system
- Role-based access control
- Password hashing for security

## System Requirements

- Python 3.7 or higher
- MySQL database
- Required Python packages:
  - tkinter
  - mysql-connector-python
  - python-dotenv
  - hashlib
  - logging

## Installation

1. Clone the repository:
```
git clone https://github.com/yourusername/fleet-management-system.git
cd fleet-management-system
```

2. Install the required packages:
```
pip install -r requirements.txt
```

3. Set up the MySQL database:
   - Create a new database called `fleet_management`
   - Import the database schema from `database/schema.sql`
   - (Optional) Import sample data from `database/sample_data.sql`

4. Configure database connection:
   - Create a `.env` file in the project root with the following details:
   ```
   MYSQL_HOST=localhost
   MYSQL_PORT=3306
   MYSQL_DATABASE=fleet_management
   MYSQL_USER=your_username
   MYSQL_PASSWORD=your_password
   ```

5. Run the application:
```
python login_system.py
```

## Project Structure

```
fleet-management-system/
├── admin_user_portal.py     # Admin portal implementation
├── local_user_portal.py     # Local user portal implementation
├── login_system.py          # Login system
├── database_connection.py   # Database utilities
├── form_utils.py            # Form utility functions
├── return_to_admin.py       # Navigation helper
├── config/                  # Configuration files
│   └── users.json           # User credentials (auto-generated)
├── assets/                  # Application assets
│   ├── logo.png             # Logo image
│   └── icon.ico             # Application icon
├── database/                # Database scripts
│   ├── schema.sql           # Database schema
│   └── sample_data.sql      # Optional sample data
└── LICENSE                  # License file
```

## Usage

### Default Login Credentials

The system comes with two default user accounts:

- Administrator:
  - Username: `admin`
  - Password: `12345`

- Local User:
  - Username: `local`
  - Password: `12345`

**Important:** Change the default passwords after the first login for security.

### Administrator Workflow

1. Login with administrator credentials
2. Use the tabbed interface to navigate between different sections
3. Manage vehicles, drivers, customers, and other fleet components
4. Use advanced search for complex queries
5. Export data as needed

### Local User Workflow

1. Login with local user credentials
2. Browse fleet data in a read-only mode
3. Generate predefined reports
4. Search for specific information
5. Export data for external use

## Troubleshooting

### Common Issues

1. **Database Connection Errors**
   - Check your database credentials in the `.env` file
   - Ensure the MySQL server is running
   - Verify network connectivity if using a remote database

2. **Missing Libraries**
   - Run `pip install -r requirements.txt` to ensure all dependencies are installed

3. **Login Issues**
   - If you can't log in with default credentials, check if the `config/users.json` file exists
   - If it's corrupted, delete it and restart the application to regenerate it

### Logging

The application logs information and errors to `fleet_management.log`. Check this file for troubleshooting.

## Development

### Adding New Features

1. **New Database Tables**
   - Add the table definition to `database/schema.sql`
   - Update the relevant section in `admin_user_portal.py`
   - Add read-only access in `local_user_portal.py` if needed

2. **New Reports**
   - Implement a query function in `local_user_portal.py`
   - Add a new menu item in the Reports menu
   - Create a display function for the report results

### Coding Standards

- Follow PEP 8 Python style guidelines
- Document functions and classes with docstrings
- Use consistent naming conventions
- Log appropriate information and errors

## License

[Include your license information here]

## Credits

Developed by [Your Name or Company]

## Contact

For support or inquiries, please contact:
- Email: support@fleetmanagementsystem.com
- Website: [your-website.com]


Version 2 Read Me

# Fleet Management System

## Overview

This is a comprehensive Fleet Management System with modular architecture that allows administrators and users to manage different aspects of a fleet operation including vehicles, drivers, cargo, customers, maintenance, and service providers.

## System Architecture

The system is divided into multiple modules that can be accessed through a central landing page. The system supports two types of users:

1. **Administrators**: Have access to all modules and features
2. **Local Users**: Have read-only access to limited functions

## Components

### Main Entry Points

- **landing_page.py**: The main entry point for the application
- **admin_login.py**: Administrator login page
- **user_login.py**: Regular user login page
- **admin_portal.py**: Main dashboard for administrators
- **module_loader.py**: Helper to load modules with admin navigation

### Core Modules

- **admin_user_portal.py**: General administration and system configuration
- **cargo_management.py**: Manage cargo and cargo types
- **customer_management.py**: Manage customer information and relationships
- **driver_management.py**: Manage drivers and their qualifications
- **maintenance_management.py**: Vehicle maintenance scheduling and tracking
- **service_management.py**: Manage service providers and service status

### Utilities

- **database_connection.py**: Handles all database interactions
- **form_utils.py**: Shared UI utilities for forms and data display
- **return_to_admin.py**: Adds navigation back to the admin portal in each module

## Installation

1. Ensure you have Python 3.7+ installed
2. Install required packages:
   ```
   pip install mysql-connector-python python-dotenv
   ```
3. Configure your database connection in a `.env` file

## Running the Application

Start the application by running the landing page:

```
python landing_page.py
```

### Default Credentials

- **Admin User**:
  - Username: admin
  - Password: 12345

- **Local User**:
  - Username: local
  - Password: 12345

## Navigation

The system includes a unified navigation approach:
- From the Admin Portal, click any module to open it
- Each module includes an Admin menu with "Return to Admin Portal" and "Logout" options
- The System Logs viewer shows activity logs from all modules

## Customization

To add new modules:
1. Create a new module file following the existing pattern
2. Add the module to the admin_portal.py modules list
3. The module_loader.py will automatically integrate it with the admin navigation

## Security

- User credentials are stored with SHA-256 hashing
- Role-based access control separates admin and user functions
- Session management ensures proper authentication

## Logging

All system actions are logged to fleet_management.log, which can be viewed through the Admin Portal's System Logs viewer.