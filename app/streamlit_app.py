import streamlit as st
import pandas as pd
import psycopg2
import os
from dotenv import load_dotenv

# Load database configuration from the .env file
load_dotenv()

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "postgres")
MAIN_DB_NAME = os.getenv("MAIN_DB_NAME", "main_company_db")

def get_connection():
    """
    Helper function to establish a connection to our main PostgreSQL database.
    Notice we only ever connect to the main database, never the remote database directly!
    """
    return psycopg2.connect(host=DB_HOST, port=DB_PORT, user=DB_USER, password=DB_PASSWORD, dbname=MAIN_DB_NAME)

# Setup Streamlit page configuration (title and layout style)
st.set_page_config(page_title="Data Federation Demo", layout="wide")

st.title("Data Federation with PostgreSQL Foreign Data Wrappers")
st.markdown("""
This demo showcases how PostgreSQL can act as a **federated data hub**.
Instead of migrating all data into a single database, PostgreSQL queries data where it natively lives using Foreign Data Wrappers (FDW).
""")

# Setup the sidebar to explain the architecture to the viewer
st.sidebar.header("Architecture")
st.sidebar.markdown("""
**1. Local Data (`customers`)**
Stored normally inside `main_company_db`.

**2. CSV External Data (`file_fdw`)**
Orders stored in a raw `.csv` file on the hard drive. Accessed via the `foreign_orders_csv` pointer.

**3. Remote PostgreSQL (`postgres_fdw`)**
Orders stored in a completely separate database called `sales_remote_db`. Accessed via the `orders_remote` pointer.
""")

# Create two tabs in the UI for our two different demos
tab1, tab2 = st.tabs(["Demo 1: Querying a CSV (file_fdw)", "Demo 2: Querying Remote DB (postgres_fdw)"])

# ==========================================
# TAB 1: file_fdw Demo
# ==========================================
with tab1:
    st.header("Joining Local Table with External CSV")
    st.write("We will join `customers` (Local Table) with `foreign_orders_csv` (External CSV file accessed via `file_fdw`).")
    
    # This is the standard SQL query. Notice there is no special syntax here!
    # Because of FDW, the user just writes standard SQL, and PostgreSQL handles the complexity
    # of reading the CSV file from the hard drive in the background.
    query1 = """
    SELECT
        c.customer_name,
        c.city,
        c.segment,
        o.order_id,
        o.product_category,
        o.amount,
        o.status
    FROM customers c
    JOIN foreign_orders_csv o
    ON c.customer_id = o.customer_id;
    """
    # Display the SQL code on the screen with syntax highlighting
    st.code(query1, language="sql")
    
    # When the user clicks the button, execute the query
    if st.button("Run file_fdw Join Query"):
        with st.spinner("Querying..."): # Show a loading spinner
            try:
                conn = get_connection()
                # Run the query and load the results into a Pandas DataFrame
                df = pd.read_sql(query1, conn)
                # Display the DataFrame in the Streamlit UI
                st.dataframe(df)
                conn.close()
                st.success("Query successful! Data fetched directly from CSV and joined locally.")
            except Exception as e:
                st.error(f"Error: {e}")

# ==========================================
# TAB 2: postgres_fdw Demo
# ==========================================
with tab2:
    st.header("Joining Local Table with Remote PostgreSQL")
    st.write("We will join `customers` (Local Table) with `orders_remote` (Remote Postgres Table accessed via `postgres_fdw`).")
    
    # Similar standard SQL query.
    # Here, PostgreSQL will act as a client, reach out to the remote database over the network,
    # ask for the order data, and then join it with the local customers table.
    query2 = """
    SELECT
        c.customer_name,
        c.city,
        c.segment,
        o.order_id,
        o.product_category,
        o.amount,
        o.status
    FROM customers c
    JOIN orders_remote o
    ON c.customer_id = o.customer_id;
    """
    st.code(query2, language="sql")
    
    if st.button("Run postgres_fdw Join Query"):
        with st.spinner("Querying..."):
            try:
                conn = get_connection()
                df = pd.read_sql(query2, conn)
                st.dataframe(df)
                conn.close()
                st.success("Query successful! Data fetched over the network from the remote database and joined locally.")
            except Exception as e:
                st.error(f"Error: {e}")
