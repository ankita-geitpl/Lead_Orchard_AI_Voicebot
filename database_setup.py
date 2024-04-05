import psycopg2

def create_table_with_columns():
    # Database connection parameters
    conn_params = {
        'host': 'localhost',
        'port': '5432',
        'database': 'voicebot',
        'user': 'availably_ai',
        'password': 'Fr4g!le$ecuR1ty!'
    }

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
        CONSTRAINT location_id_uniq UNIQUE (location_id),
        CONSTRAINT location_id_unique UNIQUE (location_id)
    );
    """

    # Columns to add if they don't exist
    columns_to_add = [
        "id SERIAL PRIMARY KEY",
        "access_token TEXT NULL",
        "token_type TEXT NULL",
        "expires_in INTEGER NULL",
        "refresh_token TEXT NULL",
        "scope TEXT NULL",
        "user_type VARCHAR(50) NULL",
        "company_id VARCHAR(255) NULL",
        "approved_locations TEXT[] NULL",
        "plan_id VARCHAR(255) NULL",
        "is_active BOOLEAN DEFAULT false",
        # Add other columns here
    ]

    # Constraints to add if they don't exist
    constraints_to_add = [
        "CONSTRAINT location_id_uniq UNIQUE (location_id)",
        # "CONSTRAINT company_data_pkey PRIMARY KEY (id),

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
            if not column_exists(cur, column_name):
                add_column_query = f"ALTER TABLE company_data ADD COLUMN {column} NULL;"
                cur.execute(add_column_query)
                print(f"Column '{column_name}' added successfully.")

        # Add constraints if they don't exist
        for constraint in constraints_to_add:
            constraint_name = constraint.split()[1]
            if not constraint_exists(cur, constraint_name):
                add_constraint_query = f"ALTER TABLE company_data ADD {constraint};"
                cur.execute(add_constraint_query)
                print(f"Constraint '{constraint_name}' added successfully.")

        # Commit and close the connection
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        print("Error:", e)

def column_exists(cur, column_name):
    # Check if column exists in the table
    cur.execute(
        "SELECT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'company_data' AND column_name = %s)",
        [column_name]
    )
    return cur.fetchone()[0]

def constraint_exists(cur, constraint_name):
    # Check if constraint exists in the table
    cur.execute(
        "SELECT EXISTS (SELECT 1 FROM information_schema.table_constraints WHERE table_name = 'company_data' AND constraint_name = %s)",
        [constraint_name]
    )
    return cur.fetchone()[0]

if __name__ == "__main__":
    create_table_with_columns()
