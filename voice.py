from dependency import *
import constants
import datetime
from dateutil import parser
import re
import datetime
from dateutil import parser
from datetime import datetime, timedelta
import requests
from flask import url_for
from dateutil import parser
from flask import jsonify


warnings.filterwarnings("ignore", category=UserWarning, module="pydub")
warnings.filterwarnings("ignore", category=DeprecationWarning, module="langchain")

openai_api_key = os.environ["OPENAI_API_KEY"] = constants.APIKEY
GOHIGHLEVEL_API_URL = "https://rest.gohighlevel.com/v1/contacts"
# API_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJsb2NhdGlvbl9pZCI6ImIwTkQ0cTZHT1FTaElHMWVhQk04IiwiY29tcGFueV9pZCI6IjZ5aDhvREF4V3FxVFVFMjFrS2JIIiwidmVyc2lvbiI6MSwiaWF0IjoxNzA4Njg0NDcyNjM0LCJzdWIiOiJ1c2VyX2lkIn0.j6A2ceU9L5YW18I_QiE3vBXvc13pffRlQ2SDDlt1yp8"
API_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJsb2NhdGlvbl9pZCI6Ik9CSHdzNmczSUdxZ1ROazhtU3hYIiwidmVyc2lvbiI6MSwiaWF0IjoxNzExNDU2NDY2Mzc5LCJzdWIiOiJSOG1jcXJWVjN5N0VWVUFPeUVBUSJ9.ff_UqRxJOlUme0ZR0WEebSPX3AKcj6pxXSTqlFP3epM"
app = Flask(__name__)

# Dictionary to store session IDs and chat history
sessions = {}
# chat_history = []
data_pdf_path = ""
prompt_data = ""

class TwilioCallHandler:
    
    # Set system message
    system_message = prompt.prompts

    def __init__(self):
        pass

    def liam_voice(self):
        voice = elevenlabs.Voice(
            voice_id="TX3LPaxmHKxFdv7VOQHJ",
            settings=elevenlabs.VoiceSettings(
                stability=0.5,
                similarity_boost=0.8
            )
        )
        return voice

    def user_id_generate(self):
        uuid_bytes = uuid.uuid1().bytes
        encoding = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789'
        short_uuid = ''.join(encoding[b % 62] for b in uuid_bytes[:8])
        return short_uuid
    
    def get_prompt_file(self , to):
        # Replace these values with your PostgreSQL database information
        global prompt_data , data_pdf_path
        db_params = constants.db_params
        
        try:
            # Create a connection to the database
            connection = psycopg2.connect(**db_params)
            print("Connected to the database!")
            
            # Create a cursor
            cursor = connection.cursor()
            
            # Fetch the PDF file from the database based on the phone number
            cursor.execute("SELECT prompt_file_path FROM company_data WHERE phone_number = %s", (to,))
            prompt_pdf_path = cursor.fetchone()[0]
            
            with open(prompt_pdf_path , 'rb') as file:
                pdf_reader = PdfReader(io.BytesIO(file.read()))
                # Extract text from the PDF
                prompt_data = ""
                for page_num in range(len(pdf_reader.pages)):
                    prompt_data += pdf_reader.pages[page_num].extract_text()

                
                    
            if '{context}' not in prompt_data:
                prompt_data = prompt_data+" : "+"{context}"
            
            cursor.execute("SELECT data_file_path FROM company_data WHERE phone_number = %s", (to,))
            data_pdf_path = cursor.fetchone()[0]
            data_pdf_path = str(data_pdf_path)
        
        except Error as e:
            print("Error reading PDF from database:", e)
            return jsonify({"error": "Error reading PDF from database"}), 500
        
        finally:
            # Close the cursor and connection
            if connection:
                cursor.close()
                connection.close()
                print("Connection closed.")
    
    def extract_date(self , text):
        try:
            # Check if the text contains references to "today" or "tomorrow"
            today = datetime.now().date()
            if 'today' in text.lower():
                return today.strftime("%d-%m-%Y")
            elif 'tomorrow' in text.lower():
                tomorrow = today + timedelta(days=1)
                return tomorrow.strftime("%d-%m-%Y")
            # Attempt to parse the date using dateutil.parser
            parsed_date = parser.parse(text, fuzzy=True)
            formatted_date = parsed_date.strftime("%d-%m-%Y")
            return formatted_date
        except ValueError:
            # If parsing fails, return None
            return None
        

    def contact_creation(self , appointment_data , to_number):
        # Read the JSON file
        # with open(path, "r") as json_file:
        #     data_dict = json.load(json_file)
    
        data_dict_clean = {key.lstrip('- '): value if '-' in key else value for key, value in appointment_data.items()}
        import pdb;pdb.set_trace()
        # Access the values using the keys
        first_name = data_dict_clean["First Name"]
        last_name = data_dict_clean["Last Name"]
        company_name = data_dict_clean["Company Name"]
        phone_number_preference = data_dict_clean["Is this phone number the best to call"]
        confirmation = data_dict_clean["Confirmation"]
        date_selected = data_dict_clean["Date Selected"]

        contact_data = {
            "phone": to_number,
            "firstName": first_name,
            "lastName": last_name,
            "name": first_name + " " + last_name,
            "locationId": "OBHws6g3IGqgTNk8mSxX",
            "companyName":company_name,
            "tags": [
                    "By AI softwere"
                    ]
        }
        return contact_data
    
    def create_or_update_contact(self , data , call_sid , from_sid):
        # call_sid = request.form.get('CallSid')
        # from_sid = request.form.get('From')
        # data = data
        # email = data.get('email')

        existing_contact = self.check_existing_contact(from_sid)
        print("=========================================432323136634",existing_contact)
        
        if existing_contact:
            self.update_contact(existing_contact['id'], data)
            return jsonify({"message": "Contact updated successfully", "contact": existing_contact}), 200
        else:
            new_contact = self.create_contact(data)
            return jsonify({"message": "Contact created successfully", "contact": new_contact}), 201
    
    def check_existing_contact(self , phone):
        headers = {"Authorization": f"Bearer {API_KEY}"}
        params = {"search": phone}
        response = requests.get(GOHIGHLEVEL_API_URL, headers=headers, params=params)
        if response.status_code == 200:
            contacts = response.json().get('data', [])
            if contacts:
                return contacts[0]  # Return the first matching contact
        return None
    

    
    def create_contact(self , data):
        headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
        response = requests.post(GOHIGHLEVEL_API_URL, headers=headers, json=data)
        if response.status_code == 200:
            return response.json().get('data', {}),201
        else:
            return None
        
    def update_contact(self , contact_id, data):
        headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
        update_url = f"{GOHIGHLEVEL_API_URL}/{contact_id}"
        response = requests.put(update_url, headers=headers, json=data)
        if response.status_code != 200:
            print("Failed to update contact:", response.text)

    def get_documents_from_web(self , data_pdf_path):
        file_loader = PyMuPDFLoader(data_pdf_path)
        documents = file_loader.load()
        print("documents:" , documents)
        
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=800,
            chunk_overlap=50
        )
        splitdocs = splitter.split_documents(documents)
        embedding = OpenAIEmbeddings(openai_api_key=openai_api_key)
        vectorStore = FAISS.from_documents(splitdocs, embedding=embedding)
        return vectorStore

    
    def create_chain(self, vectorStore):
        # Create and return a retrieval chain
        global prompt_data
        model = ChatOpenAI(model="gpt-3.5-turbo-1106", temperature=0)
        print('8888888888888888888888888888888888888888888888888888888888888888888')
        print(prompt_data)
        print('8888888888888888888888888888888888888888888888888888888888888888888')
        prompt = ChatPromptTemplate.from_messages([
            ("system", prompt_data),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}")
        ])
        
        chain = create_stuff_documents_chain(llm=model, prompt=prompt)
        retriever = vectorStore.as_retriever(search_kwargs={"k": 1})
        retriever_prompt = ChatPromptTemplate.from_messages([
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}"),
            ("human", "Given the above conversation, generate a search query from the knowledge base first to look up in order to get information relevant to the conversation")
        ])
        
        history_aware_retriever = create_history_aware_retriever(llm=model, retriever=retriever, prompt=retriever_prompt)
        retriever_chain = create_retrieval_chain(history_aware_retriever, chain)
        
        return retriever_chain

    def process_chat(self, chain, question, chat_history):
        # Process the chat using the retrieval chain
        response = chain.invoke({"input": question, "chat_history": chat_history})
        return response['answer']

    def run_assistant(self, session_id , ques):

        vectorStore = self.get_documents_from_web(data_pdf_path)
        print("Vector Store:" , vectorStore)
        # Run the assistant based on the user's question and session ID
        chain = self.create_chain(vectorStore)
        print("Chain:" , chain)
        print("Human : " , ques)
        chat_history = sessions.get(session_id, [])
        
        if any(trigger_word in ques.lower() for trigger_word in ['quit', 'q', 'exit', 'goodbye', 'end call', 'cut call']):
            answer = "Thank you for using Availably. Have a great day!"            
            time.sleep(2)  

        else:
            start_time = time.time()
            answer = self.process_chat(chain, ques, chat_history)
            end_time = time.time()
            chat_history.append(HumanMessage(content=ques))
            chat_history.append(AIMessage(content=answer))
            sessions[session_id] = chat_history
            print("AI:", answer)
            print("Time taken for processing:", end_time - start_time, "seconds")

        return answer

call_handler = TwilioCallHandler()

@app.route('/voice', methods=['GET' , 'POST'])
def voice():
    """Handle incoming voice call."""
    response = VoiceResponse()
    chat_history = [] 
    call_sid = request.form.get('CallSid')
    from_num = request.form.get('ForwardedFrom')
    print("==============================================")
    print("Forwarded From : ",from_num)
    print("==============================================")
    print()
    print()
    session_id = sessions.get(call_sid, None)
    from_num_1 = request.form.get('To')
    print("==============================================")
    print("TO NUMBERS From : ",from_num_1)
    print("==============================================")
    print()
    print()
    call_handler.get_prompt_file(from_num_1)

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
    speech_result = request.form.get('SpeechResult')
   
    confidence_score = float(request.form.get('Confidence', 0.0))
    response = VoiceResponse()
    call_sid = request.form.get('CallSid')
    from_sid = request.form.get('From')
    print("Call SID:", call_sid)
    session_id = sessions.get(call_sid, None)

    if not session_id:
        session_id = str(random.randint(1000, 999999))
        sessions[call_sid] = session_id

    if confidence_score > 0.60:
        if speech_result:
            ans_1 = call_handler.run_assistant(session_id, speech_result)
            unknown_answer = ans_1
            print("chat_history:", sessions[session_id])
            handler = "/handle-voice" 
            print()
            print()
            print("===============================================unknown",unknown_answer)
            print()
            print()
            
            inf_1 = "I can help you with that"
            if inf_1.lower() in unknown_answer.lower():
                handler = "contact-information" 
                with response.gather(input='speech', enhanced=True, speech_model='phone_call', speech_timeout='auto', action=handler) as gather:
                    gather.say(unknown_answer, language='en-US')
                
            
            else:
                with response.gather(input='speech', enhanced=True, speech_model='phone_call', speech_timeout='auto', action=handler) as gather:
                    gather.say(unknown_answer, language='en-US')
            
            
        else:
            with response.gather(input='speech', enhanced=True, speech_model='phone_call', speech_timeout='auto', action="/handle-voice") as gather:
                gather.say("No voice input received. Please try again.", voice=call_handler.liam_voice())
    else:
        with response.gather(input='speech', enhanced=True, speech_model='phone_call', speech_timeout='auto', action="/handle-voice") as gather:
            gather.say("No voice input received. Please try again.", voice=call_handler.liam_voice())

    return str(response)

@app.route('/contact-information', methods=['GET', 'POST'])
def contact_information():
    global date_new
    
    speech_result = request.form.get('SpeechResult')
    confidence_score = float(request.form.get('Confidence', 0.0))
    response = VoiceResponse()
    call_sid = request.form.get('CallSid')
    session_id = sessions.get(call_sid, None)
    from_sid = request.form.get('From')
    from_num = request.form.get('ForwardedFrom')
    date = call_handler.extract_date(speech_result)
    if not session_id:
        session_id = str(random.randint(1000, 999999))
        sessions[call_sid] = session_id
    
    response_1 = None
    
    if date is not None:
        date_new = date

    handler = "contact-information" 
    if confidence_score > 0.60:
        if speech_result:
            unknown_answer = call_handler.run_assistant(session_id, speech_result)
            print("chat_history:", sessions[session_id])
            handler = "contact-information" 
            # file_name = "/home/akash_raut_ar99/voicebot/pdf_data/user_appoint_data/"+"availbaly"+from_sid+".txt"
            # file_name = "C://Users//akash//OneDrive//Desktop//Availably-Voicebot-GEITPL//user_appoint_data//"+"availbaly"+from_sid+".json"
            inf = "detailed information"
            if inf.lower() in unknown_answer.lower():
                print("Entered")
                lines = unknown_answer.split('\n')

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
                
                new_appointment_info = call_handler.contact_creation(appointment_info , from_sid)    
                
                _ , status_code = call_handler.create_contact(new_appointment_info)
               
                # Check the response status code

                if status_code == 200:
                    print("Contact updated successfully")
                elif status_code == 201:
                    print("Contact created successfully")
                else:
                    print("Failed to create or update contact")
                
                print(f"==============================================21313313{response}")
            with response.gather(input='speech', enhanced=True, speech_model='phone_call', speech_timeout='auto', action=handler) as gather:
                gather.say(unknown_answer, language='en-US')
            
        else:
            with response.gather(input='speech', enhanced=True, speech_model='phone_call', speech_timeout='auto', action=handler) as gather:
                gather.say("No voice input received. Please try again.", voice=call_handler.liam_voice())
    else:
        with response.gather(input='speech', enhanced=True, speech_model='phone_call', speech_timeout='auto', action=handler) as gather:
            gather.say("No voice input received. Please try again.", voice=call_handler.liam_voice())
     
    return str(response)


@app.route('/contacts', methods=['POST'])
def create_or_update_contact(data):
    call_sid = request.form.get('CallSid')
    from_sid = request.form.get('From')
    data = data
    # email = data.get('email')

    existing_contact = call_handler.check_existing_contact(from_sid)
    
    if existing_contact:
        call_handler.update_contact(existing_contact['id'], data)
        return jsonify({"message": "Contact updated successfully", "contact": existing_contact}), 200
    else:
        new_contact = call_handler.create_contact(data)
        return jsonify({"message": "Contact created successfully", "contact": new_contact}), 201


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
        pdf_directory = "C:/Users/akash/OneDrive/Desktop/Availably-Voicebot-GEITPL/pdf_data/prompt_data/"
        data_directory = "C:/Users/akash/OneDrive/Desktop/Availably-Voicebot-GEITPL/pdf_data/datafile_data/"
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