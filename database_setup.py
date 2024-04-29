from dependency import *
import constants

def create_table_with_columns():
    # Database connection parameters
    conn_params = constants.db_params

    # Define table creation query
    create_table_query = """
    CREATE TABLE IF NOT EXISTS public.company_data (
        user_id VARCHAR NULL,
        phone_number VARCHAR(20) NULL,
        prompt_file VARCHAR NULL,
        prompt_file_path TEXT NULL,
        directory_file VARCHAR NULL,
        data_file_path TEXT NULL,
        location_id TEXT NULL,
        api_key TEXT NULL,
        company_name TEXT NULL,
        id SERIAL PRIMARY KEY,
        access_token TEXT NULL,
        token_type TEXT NULL,
        expires_in INTEGER NULL,
        refresh_token TEXT NULL,
        "scope" TEXT NULL,
        user_type VARCHAR(50) NULL,
        company_id VARCHAR(255) NULL,
        approved_locations TEXT[] NULL,
        plan_id VARCHAR(255) NULL,
        is_active BOOLEAN DEFAULT false,
        is_ai_only BOOLEAN DEFAULT false,
        task_assignee_id VARCHAR NULL,
        CONSTRAINT location_id_uniq UNIQUE (location_id),
        CONSTRAINT location_id_unique UNIQUE (location_id)
    );
    """

    # Columns to add if they don't exist
    columns_to_add = [
        "id SERIAL PRIMARY KEY,"
        "access_token TEXT NULL,"
        "token_type TEXT NULL,"
        "expires_in INTEGER NULL,"
        "refresh_token TEXT NULL,"
        "scope TEXT NULL,"
        "user_type VARCHAR(50) NULL,"
        "company_id VARCHAR(255) NULL,"
        "approved_locations TEXT[] NULL,"
        "plan_id VARCHAR(255) NULL,"
        "is_active BOOLEAN DEFAULT false,"
        "is_ai_only BOOLEAN DEFAULT false,"
        "task_assignee_id VARCHAR NULL,"
        # Add other columns here
    ]

    # Constraints to add if they don't exist
    constraints_to_add = [
        "CONSTRAINT location_id_uniq UNIQUE (location_id)",
        "CONSTRAINT location_id_unique UNIQUE (location_id)"
        # Add other constraints here
    ]

    try:
        # Connect to PostgreSQL database
        conn = psycopg2.connect(**conn_params)
        cur = conn.cursor()

        # Execute the create table query
        cur.execute(create_table_query)
        print("Table 'company_data' created successfully.")

        # Add columns if they don't exist
        for column in columns_to_add:
            column_name = column.split()[0]
            if not column_exists(cur, column_name , "company_data"):
                add_column_query = f"ALTER TABLE company_data ADD COLUMN {column} NULL;"
                cur.execute(add_column_query)
                print(f"Column '{column_name}' added successfully.")

        # Add constraints if they don't exist
        for constraint in constraints_to_add:
            constraint_name = constraint.split()[1]
            if not constraint_exists(cur, constraint_name , "company_data"):
                add_constraint_query = f"ALTER TABLE company_data ADD {constraint};"
                cur.execute(add_constraint_query)
                print(f"Constraint '{constraint_name}' added successfully.")

        # Commit and close the connection
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        print("Error:", e)

def customer_data_create():
    # Database connection parameters
    conn_params = constants.db_params
    
    create_table_query = """
    CREATE TABLE IF NOT EXISTS customer_data (
                company_id VARCHAR(255) NOT NULL,
                company_name TEXT NOT NULL,
                phone_number VARCHAR(20) UNIQUE,
                contact_id TEXT UNIQUE,
                location_id TEXT NOT NULL
            )
    """

    columns_to_add = []
    constraints_to_add = []

    try:
        # Connect to PostgreSQL database
        conn = psycopg2.connect(**conn_params)
        cur = conn.cursor()

        # Execute the create table query
        cur.execute(create_table_query)
        print("Table 'customer_data' created successfully.")

        # Add columns if they don't exist
        for column in columns_to_add:
            column_name = column.split()[0]
            if not column_exists(cur, column_name , "customer_data"):
                add_column_query = f"ALTER TABLE customer_data ADD COLUMN {column} NULL;"
                cur.execute(add_column_query)
                print(f"Column '{column_name}' added successfully.")

        # Add constraints if they don't exist
        for constraint in constraints_to_add:
            constraint_name = constraint.split()[1]
            if not constraint_exists(cur, constraint_name , "customer_data"):
                add_constraint_query = f"ALTER TABLE customer_data ADD {constraint};"
                cur.execute(add_constraint_query)
                print(f"Constraint '{constraint_name}' added successfully.")

        # Commit and close the connection
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        print("Error:", e)

def finetune_data_create():
    # Database connection parameters
    conn_params = constants.db_params

    create_table_query = """
    CREATE TABLE IF NOT EXISTS finetunning_data (
                company_id VARCHAR(255) NOT NULL,
                company_name TEXT NOT NULL,
                phone_number VARCHAR(20) UNIQUE,
                location_id TEXT NOT NULL,
                model_id TEXT UNIQUE,
                last_updated_finetune_model TIMESTAMP
            )
    """

    try:
        # Connect to PostgreSQL database
        conn = psycopg2.connect(**conn_params)
        cur = conn.cursor()

        # Execute the create table query
        cur.execute(create_table_query)
        print("Table 'finetunning_data' created successfully.")

        # Add columns if they don't exist
        for column in columns_to_add:
            column_name = column.split()[0]
            if not column_exists(cur, column_name , "finetunning_data"):
                add_column_query = f"ALTER TABLE finetunning_data ADD COLUMN {column} NULL;"
                cur.execute(add_column_query)
                print(f"Column '{column_name}' added successfully.")

        # Add constraints if they don't exist
        for constraint in constraints_to_add:
            constraint_name = constraint.split()[1]
            if not constraint_exists(cur, constraint_name , "finetunning_data"):
                add_constraint_query = f"ALTER TABLE finetunning_data ADD {constraint};"
                cur.execute(add_constraint_query)
                print(f"Constraint '{constraint_name}' added successfully.")

        # Commit and close the connection
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        print("Error:", e)


def column_exists(cur, column_name , tablename):
    # Check if column exists in the table
    cur.execute(
        f"SELECT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = {tablename} AND column_name = %s)",
        [column_name]
    )
    return cur.fetchone()[0]

def constraint_exists(cur, constraint_name , tablename):
    # Check if constraint exists in the table
    cur.execute(
        f"SELECT EXISTS (SELECT 1 FROM information_schema.table_constraints WHERE table_name = {tablename} AND constraint_name = %s)",
        [constraint_name]
    )
    return cur.fetchone()[0]

if __name__ == "__main__":
    create_table_with_columns()
    customer_data_create()
