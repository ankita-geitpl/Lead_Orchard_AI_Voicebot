from dependency import *
import pika


# Marketplace account
CLIENT_ID = constants.MP_CLIENT_ID
CLIENT_SECRET =  constants.MP_CLIENT_SECRET
REDIRECT_URI =  constants.MP_REDIRECT_URL
SCOPE  = constants.SCOPE

api_url = (
    "https://marketplace.gohighlevel.com/oauth/chooselocation?"
    f"response_type=code&"
    f"redirect_uri={REDIRECT_URI}&"
    f"client_id={CLIENT_ID}&"
    f"scope={SCOPE}"
)


app = Flask(__name__)

app.secret_key = constants.SECRET_KEY
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.config['PROMPT_UPLOAD_FOLDER'] = constants.PROMPT_UPLOAD_FOLDER
app.config['DATA_UPLOAD_FOLDER'] = constants.DATA_UPLOAD_FOLDER

messages = []
# RabbitMQ connection parameters
RABBITMQ_HOST = 'localhost'
RABBITMQ_QUEUE = 'flask_queue'

def get_companies_data():
    try:
        # Connect to the database
        db_params = constants.db_params
    
        # Create a connection to the database
        conn = psycopg2.connect(**db_params)

        # Create a cursor object
        cur = conn.cursor()

        # Execute SQL query to fetch data
        cur.execute("SELECT * FROM company_data")

        # Fetch all rows
        rows = cur.fetchall()

        # Convert rows to list of dictionaries
        company_data = []
        for row in rows:
            company_data.append({
                'id': row[9],
                # 'access_token': row[1],
                # 'token_type': row[2],
                'expires_in': row[3],
                # 'refresh_token': row[4],
                # 'scope': row[5],
                # 'user_type': row[6],
                'location_id': row[6],
                # 'company_id': row[8],
                # 'approved_locations': row[9],
                # 'user_id': row[10],
                # 'plan_id': row[11],
                'phone_number': row[1],
                'prompt_file': row[2],
                # 'prompt_file_path': row[14],
                'directory_file': row[4],
                # 'data_file_path': row[16],
                # 'api_key': row[17],
                'company_name': row[8],
                'is_active': row[19],
                'is_ai_only': row[20],
            })

        # Close cursor and connection
        cur.close()
        conn.close()
      
        # Return JSON response
        return company_data

    except Exception as e:
        print(e)
        return jsonify({'error': str(e)}), 500

def get_company_data(id):
    try:
        # Connect to the database
        db_params = constants.db_params
    
        # Create a connection to the database
        conn = psycopg2.connect(**db_params)

        # Create a cursor object
        cur = conn.cursor()

        # Execute SQL query to fetch data
        cur.execute("SELECT * FROM company_data WHERE id = %s LIMIT 1", (id,))

        # Fetch a single row
        row = cur.fetchone()
        if row:
            # Construct a dictionary with the fetched data
            company_data = {
                'id': row[9],
                'expires_in': row[3],
                'location_id': row[6],
                'phone_number': row[1],
                'prompt_file': row[2],
                'directory_file': row[4],
                'company_name': row[8],
                'is_active': row[19],
                'api_key': row[7],
                'is_ai_only': row[20],
                'task_assignee_id': row[22]
                
            }

        else:
            # Handle case where no row is found for the given id
            company_data = {}

        # Return the dictionary as JSON response
        return company_data

    except Exception as e:
        print("errrors", e)
        return jsonify({'error': str(e)}), 500
    
    finally:
        # Close the cursor and connection
        if conn:
            cur.close()
            conn.close()
            print("Connection closed.")

def update_company_data(id, form_json):
    try:
        # Replace these values with your PostgreSQL database information
        db_params = constants.db_params

        # Create a connection to the database
        connection = psycopg2.connect(**db_params)
       
        print("Connected to the database!")

        # Create a cursor
        cursor = connection.cursor()

        phone = form_json["phone_number"]
       
        # Check if the phone number exists in the database
        cursor.execute("SELECT * FROM company_data WHERE phone_number = %s AND id != %s", (phone, id,))
        existing_record = cursor.fetchone()
        if existing_record:
            # Close cursor and connection
            cursor.close()
            connection.close()
            # Render the form page with an error message
            company_data =  get_company_data(id)
            flash('Phone number already with another account!', 'success')
            return False
            
        # Initialize the SET clause and parameter list
        set_clause = ''
        params = []

        # Construct the SET clause dynamically based on keys present in the remaining data
        for key, value in form_json.items():
            set_clause += f"{key} = %s, "
            params.append(value)

        print(params)

        # Add id to the end of the parameter list
        params.append(id)

        # Construct and execute the SQL update query
        sql_query = f"UPDATE company_data SET {set_clause.rstrip(', ')} WHERE id = %s"
        print(sql_query)

        # Execute the SQL query with parameters
        cursor.execute(sql_query, params)


        connection.commit()

        return True

    except Error as e:
        flash("Error connecting to the database: {e}", "error")
        return False

    finally:
        # Close the cursor and connection
        if connection:
            cursor.close()
            connection.close()
            print("Connection closed.")
            
def remove_company_data(id):
    try:
        # Connect to the database
        db_params = constants.db_params
    
        # Create a connection to the database
        conn = psycopg2.connect(**db_params)

        # Create a cursor object
        cur = conn.cursor()

        # Execute SQL query to fetch data
        cur.execute("DELETE FROM company_data WHERE id = %s", (id,))
        
        # Commit the transaction
        conn.commit()

    except Exception as e:
        print("errrors", e)
        return jsonify({'error': str(e)}), 500
    
    finally:
        # Close the cursor and connection
        if conn:
            cur.close()
            conn.close()
            print("Connection closed.")
            
def list_ai_enable_numbers():
    try:
        # Connect to the database
        db_params = constants.db_params
    
        # Create a connection to the database
        conn = psycopg2.connect(**db_params)

        # Create a cursor object
        cur = conn.cursor()

        # Execute SQL query to fetch data
        cur.execute("SELECT phone_number FROM company_data WHERE is_active = True",)

        # Fetch all rows
        rows = cur.fetchall()
        

        # Convert rows to list of dictionaries
        company_numbers = []
        for row in rows:
            company_numbers.append(row[0])
        # # Close cursor and connection
        cur.close()
        conn.close()

        # Return JSON response
        return company_numbers

    except Exception as e:
        print(e)
        return jsonify({'error': str(e)}), 500
    
    
def list_ai_only_enable_numbers():
    try:
        # Connect to the database
        db_params = constants.db_params
    
        # Create a connection to the database
        conn = psycopg2.connect(**db_params)

        # Create a cursor object
        cur = conn.cursor()

        # Execute SQL query to fetch data
        cur.execute("SELECT phone_number FROM company_data WHERE is_ai_only = True",)

        # Fetch all rows
        rows = cur.fetchall()
        

        # Convert rows to list of dictionaries
        company_numbers = []
        for row in rows:
            company_numbers.append(row[0])
        # # Close cursor and connection
        cur.close()
        conn.close()

        # Return JSON response
        return company_numbers

    except Exception as e:
        print(e)
        return jsonify({'error': str(e)}), 500
    
def update_fine_tuned_model(form_data_2):
    company_name = form_data_2["company_name"]
    location_id = form_data_2["location_id"]
    phone_number = form_data_2["phone_number"]
    db_params = constants.db_params
    
    try:
        # Create a connection to the database
        connection = psycopg2.connect(**db_params)
        
        # Create a cursor
        cursor = connection.cursor()
        
        # Fetch the PDF file from the database based on the phone number
        cursor.execute("SELECT location_id FROM finetuning_data where phone_number = %s", (phone_number,))
        existing_record = cursor.fetchone()
        if existing_record:
            cursor.execute("UPDATE finetuning_data SET company_name = %s , location_id = %s , model_id = %s WHERE phone_number = %s", (company_name, location_id, "gpt-3.5-turbo-1106", phone_number,))
        else:
            cursor.execute("INSERT INTO finetuning_data (company_id, company_name, location_id, phone_number , model_id) VALUES (%s, %s, %s, %s , %s)", ("DEFAULT", company_name, location_id, phone_number, "gpt-3.5-turbo-1106"))
        
        connection.commit()
    
    except Error as e:
                print()
                print("===========================================================")
                print("Error connecting to the database:", e)
                print("===========================================================")
                print()
            
    finally:
        # Close the cursor and connection
        if connection:
            cursor.close()
            connection.close()
    
def list_ghl_account_user(id):
    try:
        # Connect to the database
        db_params = constants.db_params
    
        # Create a connection to the database
        conn = psycopg2.connect(**db_params)

        # Create a cursor object
        cur = conn.cursor()

        # Execute SQL query to fetch data
        cur.execute("SELECT * FROM company_data WHERE id = %s LIMIT 1", (id,))

        # Fetch a single row
        row = cur.fetchone()

        if row:
            # Construct a dictionary with the fetched data
            company_data = {
                'access_token': row[10],
                'location_id': row[6]
            }

        else:
            # Handle case where no row is found for the given id
            company_data = {}
        # Return the dictionary as JSON response
        return fetch_and_extract_admin_user_ids(company_data["location_id"],company_data["access_token"])

    except Exception as e:
        print("errrors", e)
        return jsonify({'error': str(e)}), 500
    
    finally:
        # Close the cursor and connection
        if conn:
            cur.close()
            conn.close()
            print("Connection closed.")
            
def fetch_and_extract_admin_user_ids(location_id, access_token):
    url = 'https://services.leadconnectorhq.com/users/'
    params = {
        'locationId': location_id
    }
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Version': '2021-07-28',
        'Accept': 'application/json'
    }
    
    # Convert params dictionary to query string
    query_string = '&'.join([f"{key}={value}" for key, value in params.items()])
     
    response = requests.get(f'{url}?{query_string}', headers=headers)

    response.raise_for_status()  # Raise an exception for 4xx or 5xx errors
    
    data = response.json()
    # Filter users by role
    admin_users = [user for user in data['users'] if user['roles']['role'] == 'admin']
    admin_user_options = []
    for user in admin_users:
        admin_user_options.append({'value': user['id'], 'text': user['name']})
    
    return admin_user_options
      

def connect_to_rabbitmq():
    connection = pika.BlockingConnection(pika.ConnectionParameters(host=RABBITMQ_HOST))
    channel = connection.channel()
    channel.queue_declare(queue=RABBITMQ_QUEUE)
    return connection, channel
def callback(ch, method, properties, body):
    global messages
    message = json.loads(body)
    messages.append(message)
    print(f"Received message: {message}")
    ch.basic_ack(delivery_tag=method.delivery_tag)
def start_consumer():
    connection, channel = connect_to_rabbitmq()
    channel.basic_consume(queue=RABBITMQ_QUEUE, on_message_callback=callback, auto_ack=False)
    print('Started consuming')
    channel.start_consuming()


# View to render a web page
@app.route('/admin')
def home():
    messages = get_flashed_messages()
    code = request.args.get('code')
    print("=====================================code")
    print(code)
    if code:
        # Assuming you have an API endpoint to add a user using the code
        url = f"https://services.leadconnectorhq.com/oauth/token"

        # Parameters
        grant_type = "authorization_code"
        user_type = "Location"
        redirect_uri = REDIRECT_URI

        # Request body
        data = {
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "grant_type": grant_type,
            "code": code,
            "user_type": user_type,
            "redirect_uri": redirect_uri
        }

        # Make POST request to the API endpoint
        response = requests.post(url, data=data)

        # Check if the request was successful (status code 200)
        if response.status_code == 200:
            access_token = response.json()["access_token"]
            refresh_token = response.json()["refresh_token"]
            response_json = response.json()
           

            # API response JSON
            response_json = response.json()

            # Connect to PostgreSQL database
            db_params = constants.db_params
        
            # Create a connection to the database
            conn = psycopg2.connect(**db_params)

            # Create a cursor object
            cur = conn.cursor()

            # Define the SQL statement to insert data into the company_data table
            sql = """
                INSERT INTO company_data (access_token, token_type, expires_in, refresh_token, scope, user_type, location_id, company_id, user_id)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (location_id) DO UPDATE
                SET 
                    access_token = EXCLUDED.access_token,
                    token_type = EXCLUDED.token_type,
                    expires_in = EXCLUDED.expires_in,
                    refresh_token = EXCLUDED.refresh_token,
                    scope = EXCLUDED.scope,
                    user_type = EXCLUDED.user_type,
                    company_id = EXCLUDED.company_id,
                    user_id = EXCLUDED.user_id
            """


            # Execute the SQL statement with the data from the API response JSON
            cur.execute(sql, (
                response_json["access_token"],
                response_json["token_type"],
                response_json["expires_in"],
                response_json["refresh_token"],
                response_json["scope"],
                response_json["userType"],
                response_json["locationId"],
                response_json["companyId"],
                response_json["userId"]
            ))

            # Commit the transaction
            conn.commit()

            cur.execute("SELECT id FROM company_data WHERE location_id = %s LIMIT 1", (response_json["locationId"],))
            id = cur.fetchone()[0]

            # Close the cursor and connection
            cur.close()
            conn.close()

            flash('Account fetched Successfully', 'success')

            return redirect(url_for('update_location', record_id=id))

        else:
            print("Error:", response.text)
            return render_template('error.html', error =  response.text)

    else:
        locations =  get_companies_data()
        
        # Render a template with a button that redirects to the page where the user can generate the choose the location
        return render_template('setup_location.html', api_url=api_url, locations=locations, messages=messages)
    
@app.route('/admin/update_location/<string:record_id>', methods=['GET', 'POST'])
def update_location(record_id):
    messages = get_flashed_messages()
    user_list  = list_ghl_account_user(record_id)

    
    if request.method == 'POST':
        is_active = False
        # Get form datasss
        company_name = request.form['company_name']
        location_id = request.form['location_id']
        task_assignee_id = request.form['adminUserSelect']
        
        # api_key =     request.form['api_key']
        if 'is_active' in request.form:
           is_active = True
        is_active = is_active
        is_ai_only = False
        if 'is_ai_only' in request.form:
           is_ai_only = True
        is_ai_only = is_ai_only
        phone_number = request.form['phone_number'].replace("-", "")


        # Check if required data is present
        if phone_number is None:
          return jsonify({"error": "Phone number is required"}), 400

        # Get uploaded files
        prompt_file = request.files['prompt_file']
        directory_file = request.files['directory_file']

        # Get the current datetime
        current_datetime = datetime.now()

        # Generate a unique string based on the current datetime
        datetime_string = current_datetime.strftime("%Y-%m-%d_%H-%M-%S")


        # Save uploaded files to a directory
        if prompt_file:
            filename = prompt_file.filename
            name, extension = os.path.splitext(filename)
            # Secure the filename and append datetime string and extension
            prompt_filename = secure_filename(f"{name}_{datetime_string}{extension}")
            prompt_file_path = os.path.join(app.config['PROMPT_UPLOAD_FOLDER'], prompt_filename)
            prompt_file.save(prompt_file_path)

        if directory_file:
            filename = directory_file.filename
            name, extension = os.path.splitext(filename)
            # Secure the filename and append datetime string and extension
            directory_filename = secure_filename(f"{name}_{datetime_string}{extension}")
            directory_filepath = os.path.join(app.config['DATA_UPLOAD_FOLDER'], directory_filename)
            directory_file.save(directory_filepath)

        form_data = {
            "company_name":  company_name,
            "location_id": location_id,
            "is_active": is_active,
            "phone_number": phone_number,
            # 'api_key': api_key,
            "is_ai_only": is_ai_only,
            "task_assignee_id": task_assignee_id,
        }
        
        form_data_2 = {
            "company_name":  company_name,
            "location_id": location_id,
            "phone_number": phone_number,
        }

        # Add "prompt_file" and "directory_file" to data if present
        if prompt_file:
            form_data['prompt_file'] = prompt_filename
            form_data['prompt_file_path'] = prompt_file_path
        if directory_file:
            form_data['directory_file'] = directory_filename
            form_data['data_file_path'] = directory_filepath

        # Update database with the new information
        res =  update_company_data(record_id, form_data)
        update_fine_tuned_model(form_data_2)
        if res:
           flash('Location Updated Successfully', 'success')
           # Redirect to the Home page
           return redirect('/admin')
        else:
           messages = get_flashed_messages()
           return render_template('update_location.html',messages=messages, record_id=record_id, company_data= form_data, user_list=user_list)


    if request.method == "GET":
        # Render the update location form
        company_data =  get_company_data(record_id)

        return render_template('update_location.html',messages=messages, record_id=record_id, company_data= company_data, user_list=user_list)
    
    data = request.json
    user_id = data.get('userId')
    user_name = data.get('userName')

    db_params = constants.db_params
    
    
    connection = psycopg2.connect(**db_params)
    cursor = connection.cursor()
    # Check if the record exists
    cursor.execute("SELECT task_assignee_id FROM company_data WHERE id = %s", (record_id,))
    row = cursor.fetchone()

    if row is not None:
        return True
    else:
        # If record doesn't exist, insert new row
        return False
    
# Define a route to handle DELETE requests for DELETE location information
@app.route('/admin/delete_location/<string:record_id>', methods=['POST'])
def delete_location(record_id):
    remove_company_data(record_id)
    # Redirect to the Home page
    flash('Location Removed Successfully', 'success')
    return redirect('/admin')

@app.route('/admin/download/<string:record_id>', methods=['GET' , 'POST'])
def download_files(record_id):
    # Replace this with your actual database connection logic
    # Example: connect to the database using location_id to retrieve file paths
    # You need to replace these with your actual database connection and query logic
    db_params = constants.db_params
    connection = psycopg2.connect(**db_params)
    cursor = connection.cursor()

    # Execute SQL query to fetch data
    cursor.execute("SELECT prompt_file_path, data_file_path FROM company_data WHERE id = %s", (record_id,))
    existing_record = cursor.fetchone()
    if existing_record:
        prompt_file_path = existing_record[0]
        directory_file_path = existing_record[1]
    connection.close()

    if not existing_record:
        flash("No files found for this location_id", "error")
        return render_template('error.html', error_message="No files found for this location_id"), 404

    # prompt_file_path, directory_file_path = result

    if prompt_file_path:
        # Send prompt file as attachment
        flash("Prompt file downloaded successfully", "success")
        return send_file(prompt_file_path, as_attachment=True)
    elif directory_file_path:
        # Send directory file as attachment
        flash("Data file downloaded successfully", "success")
        return send_file(directory_file_path, as_attachment=True)
    else:
        # Handle case when no files are found
        flash("No files found for this location_id", "error")
        return render_template('error.html', error_message="No files found for this location_id"), 404
    
# Define a route to handle DELETE requests for DELETE location information
@app.route('/ai_number_list', methods=['GET'])
def get_ai_numbers():
    return list_ai_enable_numbers() 

@app.route('/ai_only_number_list', methods=['GET'])
def get_ai_only_numbers():
    return list_ai_only_enable_numbers()

# Route to fetch access_token and location_id from the database
@app.route('/admin/api/get_credentials/<string:record_id>')
def get_credentials(record_id):
    db_params = constants.db_params
    try:
        connection = psycopg2.connect(**db_params)
        cursor = connection.cursor()

        # Assuming you have a table named company_data with columns access_token and location_id
        cursor.execute("SELECT access_token, location_id FROM company_data where id = %s" , (record_id,))
        row = cursor.fetchone()

        if row:
            access_token, location_id = row
            return jsonify({'access_token': access_token, 'location_id': location_id})
        else:
            return jsonify({'error': 'No credentials found'})

    except psycopg2.Error as e:
        print("Error fetching credentials from database:", e)
        return jsonify({'error': 'Database error'})

    finally:
        if connection:
            cursor.close()
            connection.close()

@app.route('/admin/api/submit_user_info/<string:record_id>', methods=['POST'])
def submit_user_info(record_id):
    try:
        data = request.json
        user_id = data.get('userId')
        user_name = data.get('userName')

        db_params = constants.db_params
    
        try:
            connection = psycopg2.connect(**db_params)
            cursor = connection.cursor()

            # Check if the record exists
            cursor.execute("SELECT task_assignee_id FROM company_data WHERE id = %s", (record_id,))
            row = cursor.fetchone()

            if row is not None:
                # If record exists, update task_assignee_id
                cursor.execute("UPDATE company_data SET task_assignee_id = %s WHERE id = %s", (user_id, record_id,))
            else:
                # If record doesn't exist, insert new row
                cursor.execute("INSERT INTO company_data (id, task_assignee_id) VALUES (%s, %s)", (record_id, user_id))

            # Commit the transaction
            connection.commit()

        except psycopg2.Error as e:
            print("Error accessing database:", e)
            return jsonify({'error': 'Database error'})

        finally:
            if connection:
                cursor.close()
                connection.close()

        print(f"Received User Info - User ID: {user_id}, User Name: {user_name}")
        return jsonify({'message': 'User info received successfully'}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/messages', methods=['GET'])
def get_messages():
    global messages
    return jsonify({'messages': messages}), 200