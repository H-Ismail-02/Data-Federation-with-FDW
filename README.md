# Data Federation with PostgreSQL Foreign Data Wrappers

This project demonstrates advanced **data federation** using PostgreSQL Foreign Data Wrappers (FDW). It shows how PostgreSQL can seamlessly query and join external data sources (like flat CSV files or remote databases) as if they were local tables, eliminating the need to physically import or duplicate data.

## Technologies Used
- PostgreSQL 15/16
- `file_fdw` extension (for reading external CSVs)
- `postgres_fdw` extension (for reading from remote PostgreSQL instances)
- Python (Pandas, Faker) for synthetic data generation
- Streamlit for the user interface

## Setup Instructions

1. **Install Python Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure Database Credentials**
   Rename `.env.example` to `.env` and enter your local PostgreSQL credentials.

3. **Run the Pipeline**
   This script will generate synthetic data (500 customers, 5,000 orders) and execute the setup scripts to create the local tables and map the foreign data wrappers.
   ```bash
   python run_pipeline.py
   ```

4. **Launch the Demo**
   Start the Streamlit application to visualize the FDW joins in action.
   ```bash
   streamlit run app/streamlit_app.py
   ```
