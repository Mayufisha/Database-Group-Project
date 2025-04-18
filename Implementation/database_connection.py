import os
from dotenv import load_dotenv
import mysql.connector
from mysql.connector import pooling

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
    print("Connection Pool created successfully")
except Exception as e:
    print(f"Error creating connection pool: {e}")

# Function to get a connection from the pool
def get_connection():
    try:
        return connection_pool.get_connection()
    except Exception as e:
        print(f"Error getting connection from pool: {e}")
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
        print(f"Error fetching columns for {table_name}: {e}")
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
        print(f"Error fetching data from {table}: {e}")
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
        return cursor.fetchall() if cursor.with_rows else None
    except Exception as e:
        if conn:
            conn.rollback()
        print(f"Error executing query: {e}")
        raise e
    finally:
        if conn:
            conn.close()

# Function to search data
def search_data(table, column, value):
    query = f"SELECT * FROM {table} WHERE {column} LIKE %s"
    return execute_query(query, (f"%{value}%",))

# Function to insert data
def insert_data(table, columns, values):
    col_clause = ", ".join(columns)
    placeholder_clause = ", ".join(["%s"] * len(values))
    query = f"INSERT INTO {table} ({col_clause}) VALUES ({placeholder_clause})"
    return execute_query(query, values)

# Function to update data
def update_data(table, columns, values, id_column, id_value):
    set_clause = ", ".join([f"{col}=%s" for col in columns])
    query = f"UPDATE {table} SET {set_clause} WHERE {id_column}=%s"
    all_values = values + [id_value]
    return execute_query(query, all_values)

# Function to delete data
def delete_data(table, id_column, id_value):
    query = f"DELETE FROM {table} WHERE {id_column}=%s"
    return execute_query(query, (id_value,))

# Add to database_connection.py:

def fetch_table_data(table, search_params=None):
    """Generic function to fetch data from any table with optional search"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        if search_params:
            column, value = search_params
            query = f"SELECT * FROM {table} WHERE {column} LIKE %s"
            cursor.execute(query, (f"%{value}%",))
        else:
            cursor.execute(f"SELECT * FROM {table}")
            
        rows = cursor.fetchall()
        return rows
    finally:
        if conn:
            conn.close()

