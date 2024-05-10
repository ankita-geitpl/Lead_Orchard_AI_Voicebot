import psycopg2
from psycopg2 import Error
from dependency import constants

def create_table_with_columns(table_name, create_table_query, columns_to_add, constraints_to_add):
    try:
        conn_params = constants.db_params
        with psycopg2.connect(**conn_params) as conn:
            with conn.cursor() as cur:
                cur.execute(create_table_query)
                print(f"Table '{table_name}' created successfully.")

                for column in columns_to_add:
                    column_name = column.split()[0]
                    if not column_exists(cur, column_name, table_name):
                        add_column_query = f"ALTER TABLE {table_name} ADD COLUMN {column} NULL;"
                        cur.execute(add_column_query)
                        print(f"Column '{column_name}' added successfully.")

                for constraint in constraints_to_add:
                    constraint_name = constraint.split()[1]
                    if not constraint_exists(cur, constraint_name, table_name):
                        add_constraint_query = f"ALTER TABLE {table_name} ADD {constraint};"
                        cur.execute(add_constraint_query)
                        print(f"Constraint '{constraint_name}' added successfully.")

                conn.commit()
    except Error as e:
        print("Error:", e)

def column_exists(cur, column_name, table_name):
    cur.execute(
        f"SELECT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = '{table_name}' AND column_name = %s)",
        [column_name]
    )
    return cur.fetchone()[0]

def constraint_exists(cur, constraint_name, table_name):
    cur.execute(
        f"SELECT EXISTS (SELECT 1 FROM information_schema.table_constraints WHERE table_name = '{table_name}' AND constraint_name = %s)",
        [constraint_name]
    )
    return cur.fetchone()[0]

if __name__ == "__main__":
    # Define queries, columns, and constraints for each table
    create_table_query_company_data = """
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
        id SERIAL PRIMARY KEY
    );
    """

    columns_to_add_company_data = [
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
        "is_ai_only BOOLEAN DEFAULT false",
        "task_assignee_id VARCHAR NULL"
    ]

    constraints_to_add_company_data = [
        "CONSTRAINT location_id_uniq UNIQUE (location_id)"
    ]

    create_table_query_customer_data = """
    CREATE TABLE IF NOT EXISTS customer_data (
        company_id VARCHAR(255) NOT NULL,
        company_name TEXT NOT NULL,
        phone_number VARCHAR(20),
        contact_id TEXT UNIQUE,
        location_id TEXT NOT NULL
    )
    """

    columns_to_add_customer_data = []
    constraints_to_add_customer_data = []

    create_table_query_finetunning_data = """
    CREATE TABLE IF NOT EXISTS finetuning_data (
        company_id VARCHAR(255) NOT NULL DEFAULT 'DEFAULT',
        company_name TEXT NOT NULL,
        phone_number VARCHAR(20),
        location_id TEXT NOT NULL,
        model_id TEXT DEFAULT 'gpt-3.5-turbo-1106',
        last_updated_finetune_model TIMESTAMP
    )
    """

    columns_to_add_finetunning_data = []
    constraints_to_add_finetunning_data = []

    # Create tables with columns and constraints
    create_table_with_columns("company_data", create_table_query_company_data, columns_to_add_company_data, constraints_to_add_company_data)
    create_table_with_columns("customer_data", create_table_query_customer_data, columns_to_add_customer_data, constraints_to_add_customer_data)
    create_table_with_columns("finetunning_data", create_table_query_finetunning_data, columns_to_add_finetunning_data, constraints_to_add_finetunning_data)

