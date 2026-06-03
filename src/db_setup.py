import os
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import pandas as pd
from dotenv import load_dotenv

# Load database credentials from the .env file
load_dotenv()

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "postgres")
MAIN_DB_NAME = os.getenv("MAIN_DB_NAME", "main_company_db")
REMOTE_DB_NAME = os.getenv("REMOTE_DB_NAME", "sales_remote_db")

def create_database(dbname):
    """
    Connects to the default 'postgres' database just to run the 'CREATE DATABASE' command.
    We need ISOLATION_LEVEL_AUTOCOMMIT because databases cannot be created inside a transaction block.
    """
    conn = psycopg2.connect(host=DB_HOST, port=DB_PORT, user=DB_USER, password=DB_PASSWORD, dbname='postgres')
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    with conn.cursor() as cur:
        # Check if the database already exists
        cur.execute(f"SELECT 1 FROM pg_catalog.pg_database WHERE datname = '{dbname}'")
        exists = cur.fetchone()
        if not exists:
            # If it doesn't exist, create it
            cur.execute(f"CREATE DATABASE {dbname}")
            print(f"Created database: {dbname}")
        else:
            print(f"Database {dbname} already exists.")
    conn.close()

def setup_remote_db():
    """
    Sets up the 'sales_remote_db'. This acts as our external database source.
    We create a normal physical table here and insert the 5000 orders into it.
    """
    print(f"Setting up remote DB: {REMOTE_DB_NAME}...")
    conn = psycopg2.connect(host=DB_HOST, port=DB_PORT, user=DB_USER, password=DB_PASSWORD, dbname=REMOTE_DB_NAME)
    with conn.cursor() as cur:
        # 1. Create a normal physical table for orders in the remote database
        cur.execute("""
            DROP TABLE IF EXISTS orders_remote;
            CREATE TABLE orders_remote (
                order_id INTEGER PRIMARY KEY,
                customer_id INTEGER,
                order_date DATE,
                product_category TEXT,
                amount NUMERIC(10,2),
                status TEXT
            );
        """)
        # 2. Read the CSV file using Pandas and insert the rows into the remote database
        df = pd.read_csv('data/external/external_orders.csv')
        for _, row in df.iterrows():
            cur.execute("""
                INSERT INTO orders_remote (order_id, customer_id, order_date, product_category, amount, status)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (row['order_id'], row['customer_id'], row['order_date'], row['product_category'], row['amount'], row['status']))
    conn.commit()
    conn.close()
    print("Loaded data into orders_remote.")

def setup_main_db():
    """
    Sets up the 'main_company_db'. This is our core database.
    Here we create our local customers table, AND we set up the Foreign Data Wrappers
    to link to the CSV file and the remote database.
    """
    print(f"Setting up main DB: {MAIN_DB_NAME}...")
    conn = psycopg2.connect(host=DB_HOST, port=DB_PORT, user=DB_USER, password=DB_PASSWORD, dbname=MAIN_DB_NAME)
    
    # NOTE: The PostgreSQL background service often lacks permission to read files from user directories (like Documents).
    # To fix this, we copy the CSV file to the public 'C:/Users/Public' directory where Postgres has permission to read it.
    import shutil
    public_path = 'C:/Users/Public/external_orders.csv'
    try:
        shutil.copy('data/external/external_orders.csv', public_path)
    except Exception as e:
        print(f"Note: Could not overwrite {public_path} (it might be open in Excel or locked by Postgres). Using existing file.")
    
    csv_abs_path = public_path
    
    with conn.cursor() as cur:
        # ==========================================
        # 1. Setup LOCAL Customers Table
        # ==========================================
        # This is standard PostgreSQL. Data is physically stored here.
        cur.execute("""
            DROP TABLE IF EXISTS customers CASCADE;
            CREATE TABLE customers (
                customer_id INTEGER PRIMARY KEY,
                customer_name TEXT,
                city TEXT,
                segment TEXT,
                signup_date DATE
            );
        """)
        df = pd.read_csv('data/local/customers.csv')
        for _, row in df.iterrows():
            cur.execute("""
                INSERT INTO customers (customer_id, customer_name, city, segment, signup_date)
                VALUES (%s, %s, %s, %s, %s)
            """, (row['customer_id'], row['customer_name'], row['city'], row['segment'], row['signup_date']))
        print("Loaded data into local customers table.")

        # ==========================================
        # 2. Setup file_fdw (Data Federation with CSV)
        # ==========================================
        print("Setting up file_fdw...")
        # Step A: Enable the file_fdw extension
        cur.execute("CREATE EXTENSION IF NOT EXISTS file_fdw;")
        
        # Step B: Create a 'Server' object. This tells Postgres what kind of wrapper to use.
        cur.execute("DROP SERVER IF EXISTS csv_server CASCADE;")
        cur.execute("CREATE SERVER csv_server FOREIGN DATA WRAPPER file_fdw;")
        
        # Step C: Create the Foreign Table.
        # Notice we are NOT inserting data. We are just telling Postgres what the CSV columns look like,
        # and giving it the file path. Postgres will read the file live whenever we query this table.
        cur.execute(f"""
            CREATE FOREIGN TABLE foreign_orders_csv (
                order_id INTEGER,
                customer_id INTEGER,
                order_date DATE,
                product_category TEXT,
                amount NUMERIC(10,2),
                status TEXT
            )
            SERVER csv_server
            OPTIONS (
                filename '{csv_abs_path}',
                format 'csv',
                header 'true'
            );
        """)
        
        # ==========================================
        # 3. Setup postgres_fdw (Data Federation with Remote DB)
        # ==========================================
        print("Setting up postgres_fdw...")
        # Step A: Enable the postgres_fdw extension
        cur.execute("CREATE EXTENSION IF NOT EXISTS postgres_fdw;")
        
        # Step B: Create a 'Server' pointing to the sales_remote_db database
        cur.execute("DROP SERVER IF EXISTS pg_remote_server CASCADE;")
        cur.execute(f"""
            CREATE SERVER pg_remote_server 
            FOREIGN DATA WRAPPER postgres_fdw 
            OPTIONS (host '{DB_HOST}', port '{DB_PORT}', dbname '{REMOTE_DB_NAME}');
        """)
        
        # Step C: Create a User Mapping. 
        # This tells Postgres what username/password to use when connecting to the remote database.
        cur.execute(f"""
            CREATE USER MAPPING FOR CURRENT_USER
            SERVER pg_remote_server
            OPTIONS (user '{DB_USER}', password '{DB_PASSWORD}');
        """)
        
        # Step D: Import the table schema.
        # Instead of manually writing 'CREATE FOREIGN TABLE', this command automatically
        # reaches out to the remote database and imports the definition of 'orders_remote'.
        cur.execute("""
            IMPORT FOREIGN SCHEMA public
            LIMIT TO (orders_remote)
            FROM SERVER pg_remote_server
            INTO public;
        """)
        
    conn.commit()
    conn.close()
    print("Main DB setup complete with FDW links established!")

def main():
    # Run all the functions in order
    create_database(REMOTE_DB_NAME)
    create_database(MAIN_DB_NAME)
    setup_remote_db()
    setup_main_db()

if __name__ == "__main__":
    main()
