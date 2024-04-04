from dependency import *
from logic import *
openai_api_key = os.environ["OPENAI_API_KEY"] = constants.APIKEY
GOHIGHLEVEL_API_URL = constants.GOHIGHLEVEL_API_URL
# API_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJsb2NhdGlvbl9pZCI6ImIwTkQ0cTZHT1FTaElHMWVhQk04IiwiY29tcGFueV9pZCI6IjZ5aDhvREF4V3FxVFVFMjFrS2JIIiwidmVyc2lvbiI6MSwiaWF0IjoxNzA4Njg0NDcyNjM0LCJzdWIiOiJ1c2VyX2lkIn0.j6A2ceU9L5YW18I_QiE3vBXvc13pffRlQ2SDDlt1yp8"

app = Flask(__name__)


call_handler = TwilioCallHandler() 

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
