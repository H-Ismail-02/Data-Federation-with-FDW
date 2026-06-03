import sys
import os

# Add the 'src' directory to Python's system path so we can import our custom modules
sys.path.append(os.path.join(os.path.dirname(__file__), "src"))

# Import the function that creates our fake customers and orders
from src.generate_data import generate_synthetic_data

# Import the main database setup function and rename it to 'setup_databases' for clarity
from src.db_setup import main as setup_databases

def main():
    """
    This is the master script that runs our entire project setup from start to finish.
    It generates the data, creates the databases, and links them using Foreign Data Wrappers.
    """
    print("=== Step 1: Generating Synthetic Data ===")
    # Step 1: Call the function to create our 500 customers and 5000 orders.
    # This simulates having a real business dataset without needing to download one.
    generate_synthetic_data()
    
    print("\n=== Step 2: Setting up PostgreSQL Databases and Foreign Data Wrappers ===")
    try:
        # Step 2: Call the function that connects to PostgreSQL.
        # This creates 'main_company_db' and 'sales_remote_db', loads the data, and sets up FDW.
        setup_databases()
    except Exception as e:
        # If something goes wrong (like wrong password or Postgres isn't running), catch the error and stop.
        print(f"Error setting up databases: {e}")
        print("Please ensure PostgreSQL is running and credentials in .env are correct.")
        sys.exit(1)
        
    print("\n=== Pipeline Complete ===")
    print("You can now run the Streamlit demo by typing the following command in your terminal:")
    print("streamlit run app/streamlit_app.py")

# This is a standard Python convention. It means: "If this script is run directly, execute the main() function."
if __name__ == "__main__":
    main()
