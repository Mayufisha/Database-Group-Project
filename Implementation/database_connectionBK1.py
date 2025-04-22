import os
import logging
from dotenv import load_dotenv
import mysql.connector
from mysql.connector import pooling

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("fleet_management.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("database")

# Load environment variables
load_dotenv()

# Access the environment variables
db_host = os.getenv("MYSQL_HOST")
db_port = os.getenv("MYSQL_PORT")
db_name = os.getenv("MYSQL_DATABASE")
db_user = os.getenv("MYSQL_USER")
db_password = os.getenv("MYSQL_PASSWORD")

# Create connection pool
try:
    connection_pool = mysql.connector.pooling.MySQLConnectionPool(
        pool_name="fleet_management_pool",
        pool_size=5,
        host=db_host,
        port=db_port,
        user=db_user,
        password=db_password,
        database=db_name
    )
    logger.info("Connection Pool created successfully")
except Exception as e:
    logger.error(f"Error creating connection pool: {e}")

# Function to get a connection from the pool
def get_connection():
    try:
        return connection_pool.get_connection()
    except Exception as e:
        logger.error(f"Error getting connection from pool: {e}")
        # Fallback to direct connection if pool fails
        return mysql.connector.connect(
            host=db_host,
            port=db_port,
            user=db_user,
            password=db_password,
            database=db_name
        )

# Function to fetch table columns (with caching)
column_cache = {}
def get_table_columns(table_name):
    # Check if columns are already in cache
    if table_name in column_cache:
        return column_cache[table_name]
    
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(f"SHOW COLUMNS FROM {table_name}")
        cols = [col[0] for col in cursor.fetchall()]
        # Store in cache
        column_cache[table_name] = cols
        return cols
    except Exception as e:
        logger.error(f"Error fetching columns for {table_name}: {e}")
        return []
    finally:
        if conn:
            conn.close()

# Function to fetch data with pagination
def fetch_data_paginated(table, page=1, items_per_page=100):
    offset = (page - 1) * items_per_page
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(f"SELECT * FROM {table} LIMIT %s OFFSET %s", 
                     (items_per_page, offset))
        rows = cursor.fetchall()
        
        # Also get total count for pagination info
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        total_count = cursor.fetchone()[0]
        
        return rows, total_count
    except Exception as e:
        logger.error(f"Error fetching data from {table}: {e}")
        return [], 0
    finally:
        if conn:
            conn.close()

# Function to execute queries with proper connection management
def execute_query(query, params=None):
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        conn.commit()
        result = cursor.fetchall() if cursor.with_rows else None
        logger.info(f"Query executed: {query[:50]}...")
        return result
    except Exception as e:
        if conn:
            conn.rollback()
        logger.error(f"Error executing query: {e}")
        raise e
    finally:
        if conn:
            conn.close()

# Function to search data
def search_data(table, column, value):
    query = f"SELECT * FROM {table} WHERE {column} LIKE %s"
    return execute_query(query, (f"%{value}%",))

# Function to advanced search with multiple criteria
def advanced_search_data(table, search_params):
    """Search with multiple criteria"""
    query_parts = []
    params = []
    
    for column, value in search_params:
        if value:  # Only add non-empty criteria
            query_parts.append(f"{column} LIKE %s")
            params.append(f"%{value}%")
    
    if not query_parts:
        return fetch_data_paginated(table)[0], 0
    
    query = f"SELECT * FROM {table} WHERE " + " AND ".join(query_parts)
    return execute_query(query, params), len(params)

# Function to insert data
def insert_data(table, columns, values):
    col_clause = ", ".join(columns)
    placeholder_clause = ", ".join(["%s"] * len(values))
    query = f"INSERT INTO {table} ({col_clause}) VALUES ({placeholder_clause})"
    logger.info(f"Inserting into {table}: {', '.join(str(v) for v in values[:3])}...")
    return execute_query(query, values)

# Function to update data
def update_data(table, columns, values, id_column, id_value):
    set_clause = ", ".join([f"{col}=%s" for col in columns])
    query = f"UPDATE {table} SET {set_clause} WHERE {id_column}=%s"
    all_values = values + [id_value]
    logger.info(f"Updating {table} where {id_column}={id_value}")
    return execute_query(query, all_values)

# Function to delete data
def delete_data(table, id_column, id_value):
    query = f"DELETE FROM {table} WHERE {id_column}=%s"
    logger.info(f"Deleting from {table} where {id_column}={id_value}")
    return execute_query(query, (id_value,))

# Generic function to fetch all data from a table
def fetch_all_data(table):
    query = f"SELECT * FROM {table}"
    return execute_query(query)

# Function to get foreign key data for dropdowns
def get_foreign_key_options(table, id_column, display_column=None):
    """Get options for foreign key dropdowns"""
    if display_column:
        query = f"SELECT {id_column}, {display_column} FROM {table}"
        result = execute_query(query)
        return result if result else []
    else:
        query = f"SELECT {id_column} FROM {table}"
        result = execute_query(query)
        return [item[0] for item in result] if result else []

# Function to export data to CSV
def export_data_to_csv(table, filename):
    """Export table data to CSV file"""
    import csv
    
    try:
        data = fetch_all_data(table)
        columns = get_table_columns(table)
        
        with open(filename, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(columns)  # Write header
            writer.writerows(data)    # Write data
        
        logger.info(f"Data from {table} exported to {filename}")
        return True
    except Exception as e:
        logger.error(f"Error exporting data: {e}")
        return False

# Validate data before insert/update
def validate_data(table, data_dict):
    """Validate data before saving to database
    Returns (is_valid, error_message)"""
    
    errors = []
    
    # Get table columns and their properties
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(f"DESCRIBE {table}")
        columns_info = cursor.fetchall()
        
        # Basic validation rules based on column properties
        for col_info in columns_info:
            col_name = col_info[0]
            col_type = col_info[1]
            is_nullable = col_info[2] == 'YES'
            
            if col_name in data_dict:
                value = data_dict[col_name]
                
                # Check for required fields
                if not is_nullable and (value is None or value == ''):
                    errors.append(f"{col_name} is required")
                
                # Type validation
                if value and 'int' in col_type and not str(value).isdigit():
                    errors.append(f"{col_name} must be a number")
                
                # Date validation
                if value and 'date' in col_type:
                    try:
                        from datetime import datetime
                        datetime.strptime(value, '%Y-%m-%d')
                    except ValueError:
                        errors.append(f"{col_name} must be a valid date (YYYY-MM-DD)")
        
        return (len(errors) == 0, ', '.join(errors))
    
    except Exception as e:
        logger.error(f"Validation error: {e}")
        return (False, str(e))
    finally:
        if conn:
            conn.close()