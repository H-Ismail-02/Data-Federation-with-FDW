import os
import random
import pandas as pd
from faker import Faker

def generate_synthetic_data():
    """
    This function generates fake (synthetic) data for our project.
    We are generating two datasets:
    1. Customers: This will go into our LOCAL PostgreSQL database.
    2. Orders: This will be saved as an EXTERNAL CSV file to simulate data from another system.
    """
    print("Generating synthetic data...")
    # Initialize the Faker library to generate realistic Turkish names and cities
    fake = Faker('tr_TR')
    
    # ==========================================
    # 1. Generate Customers (Local Database Data)
    # ==========================================
    num_customers = 500
    customers = []
    segments = ['Premium', 'Standard', 'Basic', 'VIP']
    
    # Loop 500 times to create 500 unique customers
    for i in range(1, num_customers + 1):
        customers.append({
            'customer_id': i,                          # Unique ID for the customer
            'customer_name': fake.name(),              # Fake realistic name
            'city': fake.city(),                       # Fake realistic city
            'segment': random.choice(segments),        # Randomly assign them a membership segment
            'signup_date': fake.date_between(start_date='-2y', end_date='today').strftime('%Y-%m-%d')
        })
        
    # Convert our list of dictionaries into a Pandas DataFrame (a table structure)
    df_customers = pd.DataFrame(customers)
    
    # ==========================================
    # 2. Generate Orders (External Data Source)
    # ==========================================
    num_orders = 5000
    orders = []
    categories = ['Electronics', 'Clothing', 'Books', 'Home', 'Sports', 'Beauty', 'Grocery']
    statuses = ['Delivered', 'Pending', 'Shipped', 'Cancelled', 'Processing']
    
    # Loop 5000 times to create 5000 orders
    for i in range(1, num_orders + 1):
        orders.append({
            'order_id': i + 1000,                                 # Unique order ID starting at 1001
            'customer_id': random.randint(1, num_customers),      # Randomly assign this order to one of our 500 customers
            'order_date': fake.date_between(start_date='-1y', end_date='today').strftime('%Y-%m-%d'),
            'product_category': random.choice(categories),        # Pick a random product category
            'amount': round(random.uniform(10.0, 5000.0), 2),     # Random price between 10.00 and 5000.00
            'status': random.choice(statuses)                     # Random delivery status
        })
        
    df_orders = pd.DataFrame(orders)
    
    # ==========================================
    # 3. Save the Data to Files
    # ==========================================
    # Create the folders if they don't exist yet
    os.makedirs('data/local', exist_ok=True)
    os.makedirs('data/external', exist_ok=True)
    
    # Save the customers to a local CSV. We will insert this into our main PostgreSQL database later.
    df_customers.to_csv('data/local/customers.csv', index=False)
    
    # Save the orders to an external CSV. 
    # IMPORTANT: We will NOT insert this into a normal database table!
    # Instead, we will use PostgreSQL 'file_fdw' to read this file directly from the hard drive.
    df_orders.to_csv('data/external/external_orders.csv', index=False)
    
    print(f"Generated {num_customers} customers and {num_orders} orders.")
    print("Saved to data/local/customers.csv and data/external/external_orders.csv")

if __name__ == "__main__":
    generate_synthetic_data()
