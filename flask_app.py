from dependency import *
from logic import *
from flask import render_template, redirect, flash, get_flashed_messages
from werkzeug.utils import secure_filename

openai_api_key = os.environ["OPENAI_API_KEY"] = constants.APIKEY
GOHIGHLEVEL_API_URL = constants.GOHIGHLEVEL_API_URL
# API_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJsb2NhdGlvbl9pZCI6ImIwTkQ0cTZHT1FTaElHMWVhQk04IiwiY29tcGFueV9pZCI6IjZ5aDhvREF4V3FxVFVFMjFrS2JIIiwidmVyc2lvbiI6MSwiaWF0IjoxNzA4Njg0NDcyNjM0LCJzdWIiOiJ1c2VyX2lkIn0.j6A2ceU9L5YW18I_QiE3vBXvc13pffRlQ2SDDlt1yp8"

call_handler = TwilioCallHandler() 

# T account
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
app.config['PROMPT_UPLOAD_FOLDER'] = "pdf_data/prompt_data/"
app.config['DATA_UPLOAD_FOLDER'] = "pdf_data/datafile_data/"



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
                'id': row[0],
                'expires_in': row[3],
                'location_id': row[6],
                'phone_number': row[1],
                'prompt_file': row[2],
                'directory_file': row[4],
                'company_name': row[8],
                'is_active': row[19]
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
       
# View to render a web page
@app.route('/admin')
def home():
    messages = get_flashed_messages()
    code = request.args.get('code')
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
           
            # Do something with the access token and refresh token
            # print("Access Token:", access_token)
            # print("Refresh Token:", refresh_token)

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

# Define a route to handle GET and POST requests for updating location information
@app.route('/admin/update_location/<string:record_id>', methods=['GET', 'POST'])
def update_location(record_id):
    messages = get_flashed_messages()
    if request.method == 'POST':
        is_active = False
        # Get form datasss
        company_name = request.form['company_name']
        location_id = request.form['location_id']
        if 'is_active' in request.form:
           is_active = True
        is_active = is_active
        phone_number = request.form['phone_number'].replace("-", "")


        # Check if required data is present
        if phone_number is None:
          return jsonify({"error": "Phone number is required"}), 400

        # Get uploaded files
        prompt_file = request.files['prompt_file']
        directory_file = request.files['directory_file']

        # Save uploaded files to a directory
        if prompt_file:
            prompt_filename = secure_filename(prompt_file.filename)
            prompt_file_path = os.path.join(app.config['PROMPT_UPLOAD_FOLDER'], prompt_filename)
            prompt_file.save(prompt_file_path)
           
        if directory_file:
            directory_filename = secure_filename(directory_file.filename)
            directory_filepath = os.path.join(app.config['DATA_UPLOAD_FOLDER'], directory_filename)
            directory_file.save(directory_filepath)

        form_data = {
            "company_name":  company_name,
            "location_id": location_id,
            "is_active": is_active,
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
        if res:
           flash('Location Updated Successfully', 'success')
           # Redirect to the Home page
           return redirect('/admin')
        else:
           messages = get_flashed_messages()
           return render_template('update_location.html',messages=messages, record_id=record_id, company_data= form_data )


    if request.method == "GET":
        # Render the update location form
        company_data =  get_company_data(record_id)
        return render_template('update_location.html',messages=messages, record_id=record_id, company_data= company_data )

# Define a route to handle DELETE requests for DELETE location information
@app.route('/admin/delete_location/<string:record_id>', methods=['POST'])
def delete_location(record_id):
    remove_company_data(record_id)
    # Redirect to the Home page
    flash('Location Removed Successfully', 'success')
    return redirect('/admin')

# Define a route to handle DELETE requests for DELETE location information
@app.route('/ai_number_list', methods=['GET'])
def get_ai_numbers():
    return list_ai_enable_numbers()    

# Twilio call Handling endpoints
@app.route('/voice', methods=['GET' , 'POST'])
def voice():
    """Handle incoming voice call."""
    response = VoiceResponse()
    chat_history = [] 
    call_sid = request.form.get('CallSid')
    company_number = request.form.get('ForwardedFrom')
    print("==============================================")
    print("Forwarded From : ",company_number)
    print("==============================================")
    print()
    print()
    session_id = sessions.get(call_sid, None)

    call_handler.get_prompt_file(company_number)

    try:
        if not session_id:
            session_id = str(random.randint(1000, 999999))
            sessions[call_sid] = session_id

        with response.gather(input='speech', enhanced=True, speech_model='phone_call', speech_timeout='auto', action='/handle-voice') as gather:
            gather.say(call_handler.run_assistant(session_id, ques='Initial Greeting'),language='en-US')
    except Exception as e:
        print("Error" , e)
        response.say("There was an error processing your request . Please try again later.",language='en-US')

    return str(response)

@app.route('/handle-voice', methods=['GET' , 'POST'])
def handle_voice_input():
    """Handle user input during the call."""
    response = VoiceResponse()
    speech_result = request.form.get('SpeechResult')
    confidence_score = float(request.form.get('Confidence', 0.0))
    call_sid = request.form.get('CallSid')
    from_sid = request.form.get('From')
    session_id = sessions.get(call_sid, None)



    if not session_id:
        session_id = str(random.randint(1000, 999999))
        sessions[call_sid] = session_id

    if confidence_score > 0.60 and speech_result:
        
        ai_response = call_handler.run_assistant(session_id, speech_result)
        print("chat_history:", sessions[session_id])
        
        print()
        print()
        print("===============================================unknown",ai_response)
        print()
        print()
        handler = "/handle-voice"
        inf_1 = "I can help you with that"
        if inf_1.lower() in ai_response.lower():
            handler = "contact-information" 
            with response.gather(input='speech', enhanced=True, speech_model='phone_call', speech_timeout='auto', action=handler) as gather:
                gather.say(ai_response, language='en-US')
            
        
        else:
            with response.gather(input='speech', enhanced=True, speech_model='phone_call', speech_timeout='auto', action=handler) as gather:
                gather.say(ai_response, language='en-US')
        
        
    else:
        with response.gather(input='speech', enhanced=True, speech_model='phone_call', speech_timeout='auto', action="/handle-voice") as gather:
            gather.say("No voice input received. Please try again.")

    return str(response)

@app.route('/contact-information', methods=['GET', 'POST'])
def contact_information():
    global date_new
    response = VoiceResponse()

    speech_result = request.form.get('SpeechResult')
    confidence_score = float(request.form.get('Confidence', 0.0))
    call_sid = request.form.get('CallSid')
    session_id = sessions.get(call_sid, None)
    caller_number = request.form.get('From')
    company_number = request.form.get('ForwardedFrom')
    date = call_handler.extract_date(speech_result)

    print()
    print()
    print()
    print()
    print()
    print("phone_number is =========================================",company_number)
    print()
    print()
    print()
    print()
    print()

    if not session_id:
        session_id = str(random.randint(1000, 999999))
        sessions[call_sid] = session_id
    
    
    
    if date is not None:
        date_new = date

    handler = "contact-information" 
    if confidence_score > 0.60 and speech_result:
        
        ai_response = call_handler.run_assistant(session_id, speech_result)
        print("chat_history:", sessions[session_id])
        handler = "contact-information" 
        
        # file_name = "C://Users//akash//OneDrive//Desktop//Availably-Voicebot-GEITPL//user_appoint_data//"+"availbaly"+from_sid+".json"
        file_name = "/home/akash_raut/voicebot/pdf_data/user_appoint_data/"+caller_number+"+"+company_number+".json"
        # inf = "detailed information"
        if "detailed information".lower() in ai_response.lower() or "Here is a summary".lower() in ai_response.lower():
            print("Entered")
            lines = ai_response.split('\n')

            # Initialize an empty dictionary to store appointment information
            appointment_info = {}

            # Parse each line of the appointment information
            for line in lines:
                # Skip lines that don't contain a colon
                if ':' not in line:
                    continue
                key, value = line.split(':', 1)
                # if 
                appointment_info[key.strip()] = value.strip()
            appointment_info["Date Selected"] = date_new
            # Store appointment information in JSON file
            
            # with open(file_name, 'w') as json_file:
            #     json.dump(appointment_info, json_file, indent=4)
            
            contact_info = call_handler.get_subaccount_info(appointment_info , caller_number) 
            
            print()
            print()
            print()   
            print("===========================================9999999999999",contact_info)
            print()
            print()
            print() 

            with open(file_name, 'w') as json_file:
                json.dump(contact_info, json_file, indent=4)

            _ , status_code = call_handler.create_contact(contact_info)

        
            # Check the response status code
            if status_code == 200:
                print("Contact updated successfully")
            elif status_code == 201:
                print("Contact created successfully")
            else:
                print("Failed to create or update contact")
            
        with response.gather(input='speech', enhanced=True, speech_model='phone_call', speech_timeout='auto', action=handler) as gather:
            gather.say(ai_response, language='en-US')
        
    else:
        with response.gather(input='speech', enhanced=True, speech_model='phone_call', speech_timeout='auto', action=handler) as gather:
            gather.say("No voice input received. Please try again.")
    
     
    return str(response)

@app.route('/modify-prompt', methods=['POST'])
def modify_prompt():
    # Retrieve data from the POST request
    directory_file = request.files.get("directory_file")
    prompt_file = request.files.get("prompt_file")
    phone_number = request.form.get("phone_number")
    phone_number = phone_number.replace("-", "")
    

    # Check if required data is present
    if phone_number is None:
        return jsonify({"error": "Phone number is required"}), 400

    # Replace these values with your PostgreSQL database information
    db_params = constants.db_params

    try:
        # Create a connection to the database
        connection = psycopg2.connect(**db_params)
        print("Connected to the database!")

        # Create a cursor
        cursor = connection.cursor()

        # Check if the phonenumbers table exists, if not, create it
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS company_data (
                user_id VARCHAR PRIMARY KEY,
                phone_number VARCHAR(20) UNIQUE,
                prompt_file VARCHAR,
                prompt_file_path TEXT,
                directory_file VARCHAR,
                data_file_path TEXT,
                location_id TEXT,
                api_key TEXT
            )
        """)

        # Check if the phone number exists in the database
        cursor.execute("SELECT * FROM company_data WHERE phone_number = %s", (phone_number,))
        existing_record = cursor.fetchone()
        pdf_directory = "/home/akash_raut/voicebot/pdf_data/prompt_data/"
        data_directory = "/home/akash_raut/voicebot/pdf_data/datafile_data/"
        prompt_path = None
        data_path = None

        if existing_record:
            # If record exists, update it with the new PDF file if provided
            if prompt_file.filename and not directory_file.filename:
                prompt_path = os.path.join(pdf_directory, prompt_file.filename)
                prompt_file.save(prompt_path)
                cursor.execute("UPDATE company_data SET prompt_file = %s , prompt_file_path = %s WHERE phone_number = %s",
                            (prompt_file.filename, prompt_path, phone_number))
            elif directory_file.filename and not prompt_file.filename:
                data_path = os.path.join(data_directory, directory_file.filename)
                directory_file.save(data_path)
                cursor.execute("UPDATE company_data SET directory_file = %s , data_file_path = %s WHERE phone_number = %s",
                            (directory_file.filename, data_path, phone_number))
            else:
                prompt_path = os.path.join(pdf_directory, prompt_file.filename)
                prompt_file.save(prompt_path)
                data_path = os.path.join(data_directory, directory_file.filename)
                directory_file.save(data_path)
                cursor.execute("UPDATE company_data SET prompt_file = %s , prompt_file_path = %s ,  directory_file = %s , data_file_path = %s WHERE phone_number = %s",
                        (prompt_file.filename, prompt_path, directory_file.filename, data_path, phone_number))
            
        else:
            # If record doesn't exist, insert a new record
            if prompt_file.filename and not directory_file.filename:
                prompt_path = os.path.join(pdf_directory, prompt_file.filename)
                prompt_file.save(prompt_path)
                cursor.execute("INSERT INTO company_data (user_id , phone_number, prompt_file , prompt_file_path) VALUES (%s, %s, %s , %s)",
                        (call_handler.user_id_generate(), phone_number, prompt_file.filename, prompt_path))
            elif directory_file.filename and not prompt_file.filename:
                data_path = os.path.join(data_directory, directory_file.filename)
                directory_file.save(data_path)
                cursor.execute("INSERT INTO company_data (user_id , phone_number, directory_file , data_file_path) VALUES (%s, %s, %s , %s)",
                        (call_handler.user_id_generate(), phone_number, directory_file.filename, data_path))
            else:
                prompt_path = os.path.join(pdf_directory, prompt_file.filename)
                prompt_file.save(prompt_path)
                data_path = os.path.join(data_directory, directory_file.filename)
                directory_file.save(data_path)
                cursor.execute("INSERT INTO company_data (user_id , phone_number, prompt_file , prompt_file_path , directory_file , data_file_path) VALUES (%s, %s, %s , %s , %s , %s)",
                        (call_handler.user_id_generate(), phone_number, prompt_file.filename, prompt_path, directory_file.filename, data_path))

        connection.commit()
        print("Data saved successfully!")
        return jsonify({"message": "Data added or updated successfully"}), 200

    except Error as e:
        print("Error connecting to the database:", e)
        return jsonify({"error": "Error connecting to the database"}), 500

    finally:
        # Close the cursor and connection
        if connection:
            cursor.close()
            connection.close()
            print("Connection closed.")

@app.route('/get-user-phone-list', methods=['GET'])
def get_user_phone_list():
    try:
        db_params = constants.db_params
        
        # Create a connection to the database
        connection = psycopg2.connect(**db_params)

        # Create a cursor
        cursor = connection.cursor()

        # Check if the phonenumbers table exists, if not, create it
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS company_data (
                user_id VARCHAR PRIMARY KEY,
                phone_number VARCHAR(20) UNIQUE,
                prompt_file VARCHAR,
                prompt_file_path TEXT,
                directory_file VARCHAR,
                data_file_path TEXT
                location_id TEXT,
                api_key TEXT
            )
        """)

        # Retrieve the user_id, phone_number, and prompt_file from the database
        cursor.execute("SELECT user_id, phone_number, prompt_file , directory_file FROM company_data")
        records = cursor.fetchall()

        user_phone_list = [{"user_id": record[0], "phone_number": record[1], "prompt_file": record[2] , "directory_file": record[3]} for record in records]
        return jsonify({"user_phone_list": user_phone_list}), 200

    except Error as e:
        return jsonify({"error": "Error connecting to the database"}), 500

    finally:
        # Close the cursor and connection
        if connection:
            cursor.close()
            connection.close()

if __name__ == "__main__":
    app.run(host="localhost", port=3000, debug=False)
