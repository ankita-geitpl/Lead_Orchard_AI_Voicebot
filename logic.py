from dependency import *
import constants
from ghl_calendar_api import *
from prompt import prompts

openai_api_key = os.environ["OPENAI_API_KEY"] = constants.APIKEY
GOHIGHLEVEL_API_URL = constants.GOHIGHLEVEL_API_URL


current_date = datetime.now().date()
end_of_day = datetime.combine(current_date + timedelta(days=1), datetime.min.time()) - timedelta(seconds=1)
end_session_time = end_of_day.replace(hour=23, minute=59, second=59)

sessions = {}


class TwilioCallHandler:

    def __init__(self):
        pass
    
    def get_prompt_file(self , company_number):
        # Replace these values with your PostgreSQL database information
        prompt_data = None
        data_pdf_path = None
        location_id = None
        api_key = None
        company_id = None
        company_name = None
        user_id = None
        
        db_params = constants.db_params
        
        try:
            # Create a connection to the database
            connection = psycopg2.connect(**db_params)
            print()   
            print("===========================================================")
            print("Connected to the database!")
            print("===========================================================")
            print()
            
            # Create a cursor
            cursor = connection.cursor()
            
            # Fetch the PDF file from the database based on the phone number
            cursor.execute("SELECT user_id , prompt_file_path ,location_id , company_id , company_name ,access_token FROM company_data WHERE phone_number = %s", (company_number,))
            retrieve_data = cursor.fetchone()
            user_id = retrieve_data[0]
            prompt_pdf_path = retrieve_data[1]
            location_id = retrieve_data[2]
            company_id = retrieve_data[3]
            company_name = retrieve_data[4]
            api_key = retrieve_data[5]

            
            with open(prompt_pdf_path , 'rb') as file:
                pdf_reader = PdfReader(io.BytesIO(file.read()))
                # Extract text from the PDF
                prompt_data = ""
                for page_num in range(len(pdf_reader.pages)):
                    prompt_data += pdf_reader.pages[page_num].extract_text()

            if '{context}' not in prompt_data:
                prompt_data = prompt_data+" : "+"{context}"
            
            cursor.execute("SELECT data_file_path FROM company_data WHERE phone_number = %s", (company_number,))
            data_pdf_path = cursor.fetchone()[0]
            data_pdf_path = str(data_pdf_path)
        
        except Error as e:
            print()   
            print("===========================================================")
            print("Error reading PDF from database:", e)
            print("===========================================================")
            print()
            return jsonify({"error": "Error reading PDF from database"}), 500
        
        finally:
            # Close the cursor and connection
            if connection:
                cursor.close()
                connection.close()
                print()   
                print("===========================================================")
                print("Connection closed.")  
                print("===========================================================")
                print()

        return user_id , prompt_data , data_pdf_path , location_id , company_id , company_name , api_key

    def extract_date(self , text):
        time_cleaned = text.replace('.', '')
        time_cleaned = time_cleaned.lower().replace('I am', '')
        if "am".lower() not in time_cleaned.lower() and "pm".lower() not in time_cleaned.lower():
            try:
                # Check if the text contains references to "today" or "tomorrow"
                today = datetime.now().date()
                if 'today' in text.lower():
                    return today.strftime("%d-%m-%Y")
                elif 'tomorrow' in text.lower():
                    tomorrow = today + timedelta(days=1)
                    return tomorrow.strftime("%d-%m-%Y")
                # Attempt to parse the date using dateutil.parser
                if "clock".lower() not in time_cleaned.lower():
                    parsed_date = parser.parse(text, fuzzy=True)
                    formatted_date = parsed_date.strftime("%d-%m-%Y")
                    return formatted_date
            except ValueError:
                # If parsing fails, return None
                return None
           
    def get_documents_from_web(self , data_pdf_path):
        file_loader = PyMuPDFLoader(data_pdf_path)
        documents = file_loader.load()
        print()
        print("===========================================================")
        print("documents:" , documents)
        print("===========================================================")
        print()
        
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=800,
            chunk_overlap=50
        )
        splitdocs = splitter.split_documents(documents)
        embedding = OpenAIEmbeddings(openai_api_key=openai_api_key)
        vectorStore = FAISS.from_documents(splitdocs, embedding=embedding)
        return vectorStore
    
    def create_chain(self, call_sid , vectorStore):
        # Create and return a retrieval chain
        # global prompt_data
        prompt_data = sessions[call_sid]['prompt_data']
        model = ChatOpenAI(model="gpt-3.5-turbo-1106", temperature=0)
        print
        print("===========================================================")
        print("prompt_data:" , prompt_data)
        print("===========================================================")
        print()
        
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

    def run_assistant(self, call_sid , ques):
        vectorStore = self.get_documents_from_web(sessions[call_sid]['data_pdf_path'])
        # Run the assistant based on the user's question and session ID
        chain = self.create_chain(call_sid , vectorStore)
        chat_history = sessions[call_sid]['chat_history']
        
        if any(trigger_word in ques.lower() for trigger_word in ['quit', 'q', 'exit', 'goodbye', 'end call', 'cut call']):
            answer = "Thank you for using Availably. Have a great day!"            
            time.sleep(2)  

        else:
            start_time = time.time()
            answer = self.process_chat(chain, ques, chat_history)
            end_time = time.time()
            chat_history.append(HumanMessage(content=ques))
            chat_history.append(AIMessage(content=answer))
            sessions[call_sid]['chat_history'] = chat_history
            print("Time taken for processing:", end_time - start_time, "seconds")

        return answer
    
    
class GHLAppointmentHandler:
    
    def __init__(self):
        pass
    
    def contact_id_generate(self , phone_number , call_sid , data):
        # Replace these values with your PostgreSQL database information
        db_params = constants.db_params
        try:
            # Create a connection to the database
            connection = psycopg2.connect(**db_params)
            print()
            print("===========================================================")
            print("Connected to the database!")
            print("===========================================================")
            print()
            # Create a cursor
            cursor = connection.cursor()

            # # Check if the phonenumbers table exists, if not, create it
            # cursor.execute("""
            #     CREATE TABLE IF NOT EXISTS customer_data (
            #         user_id VARCHAR(255) NOT NULL,
            #         phone_number VARCHAR(20) UNIQUE,
            #         contact_id TEXT UNIQUE
            #     )
            # """)    
            #  # Check if the phone number exists in the database
            cursor.execute("SELECT * FROM customer_data WHERE phone_number = %s", (phone_number,))
            existing_record = cursor.fetchone()
            if existing_record:
                cursor.execute("SELECT contact_id FROM customer_data WHERE phone_number = %s", (phone_number,))
                retrieve_data = cursor.fetchone()
                contact_id = retrieve_data[0]
                self.update_contact(call_sid , contact_id , data)
                sessions[call_sid]['contact_id'] = contact_id
            else:
                contact_id = self.create_contact(call_sid , data)
                company_id = sessions[call_sid]['company_id']
                company_name = sessions[call_sid]['company_name']
                cursor.execute("INSERT INTO customer_data (company_id , company_name , phone_number, contact_id) VALUES (%s, %s, %s , %s)", (company_id , company_name , phone_number, contact_id))
                sessions[call_sid]['contact_id'] = contact_id
            connection.commit()
            print()
            print("===========================================================")
            print("Data saved successfully!")
            print("===========================================================")
            print()

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
                print()
                print("===========================================================")
                print("Connection closed.")
                print("===========================================================")
                print()
                    
    def get_subaccount_info(self , call_sid , appointment_info , customer_number):
        email = None
        data_dict_clean = {key.lstrip('- '): value if '-' in key else value for key, value in appointment_info.items()}
        
        # Access the values using the keys
        first_name = data_dict_clean["First Name"]
        last_name = data_dict_clean["Last Name"]
        company_name = data_dict_clean["Company Name"]
        date_selected = data_dict_clean["Date Selected"]
        time_selected = data_dict_clean["Time Selected"]
        location_id = sessions[call_sid]['location_id']
        contact_data = {
            "phone": customer_number,
            "firstName": first_name,
            "lastName": last_name,
            "name": first_name + " " + last_name,
            "locationId": location_id,
            "companyName": company_name,
            "dateSelected": date_selected,
            "timeSelected": time_selected,
            "email": email,
            "tags": [
                    "By AI softwere"
                    ]
        }
        return contact_data

    def create_contact(self , call_sid , user_data):
        api_key = sessions[call_sid]['api_key']
        conn = http.client.HTTPSConnection("services.leadconnectorhq.com")

        payload = user_data
        keys_to_remove = ['dateSelected', 'timeSelected']
        for key in keys_to_remove:
            payload.pop(key)

        headers = {
            'Authorization': f"Bearer {api_key}",
            'Version': "2021-07-28",
            'Content-Type': "application/json",
            'Accept': "application/json"
        }

        conn.request("POST", "/contacts/", json.dumps(payload), headers)

        res = conn.getresponse()
        data = res.read()
        print("+++++++++++++++++data:",data)
        response_dict = json.loads(data.decode('utf-8'))
        contact_id = response_dict['contact']['id']
        print("======================================================" , response_dict)
        if res.status == 201 or res.status == 200:
            print()   
            print("===========================================================")
            print("Contact created successfully!")
            print("===========================================================")
            print()
        return contact_id
            
    def update_contact(self , call_sid , contact_id , user_data):
        api_key = sessions[call_sid]['api_key']
        conn = http.client.HTTPSConnection("services.leadconnectorhq.com")

        payload = user_data
        keys_to_remove = ['dateSelected', 'timeSelected' , 'locationId']
        for key in keys_to_remove:
            payload.pop(key)
            
        headers = {
            'Authorization': f"Bearer {api_key}",
            'Version': "2021-07-28",
            'Content-Type': "application/json",
            'Accept': "application/json"
        }
        
        headers = {'Authorization': f"Bearer {api_key}",'Version': "2021-07-28",'Content-Type': "application/json",'Accept': "application/json"}

        conn.request("PUT", f"/contacts/{contact_id}", json.dumps(payload), headers)

        res = conn.getresponse()
        # import pdb; pdb.set_trace()
        data = res.read()

        if res.status == 201 or res.status == 200:
            print()   
            print("===========================================================")
            print("Contact updated successfully!")
            print("===========================================================")
            print()
    
    def get_user_id(self , call_sid):
        api_key = sessions[call_sid]['api_key']
        location_id = sessions[call_sid]['location_id']
        conn = http.client.HTTPSConnection("services.leadconnectorhq.com")
        headers = {
                    'Authorization': f"Bearer {api_key}",
                    'Version': "2021-07-28",
                    'Content-Type': "application/json",
                    'Accept': "application/json"
                }

        conn.request("GET", f"/users/?locationId={location_id}", headers=headers)

        res = conn.getresponse()
        data = res.read()
        user_id_data = data.decode("utf-8")
        response_data = json.loads(user_id_data)

        if 'users' in response_data and len(response_data['users']) > 0:
                user_id = response_data['users'][0]['id']
        
        return user_id
    
    def create_task(self , call_sid):  
        user_id = self.get_user_id(call_sid)
        path = sessions[call_sid]['file_name']
        api_key = sessions[call_sid]['api_key']
        contact_id = sessions[call_sid]['contact_id']
        with open(path, "r") as json_file:    
             data_dict = json.load(json_file)
        print("Data Dict:", data_dict)
        data_dict_clean = {key.lstrip('- '): value if '-' in key else value for key, value in data_dict.items()}
        keys_to_remove = ['dateSelected', 'timeSelected']
        for key in keys_to_remove:
            data_dict_clean.pop(key)
            
        data_dict_clean.update({
            "assignedTo": user_id,
            "completed": False,
            "title": "Task for " + data_dict_clean["firstName"],
            "body": "Task for " + data_dict_clean["firstName"],
            "dueDate": "2024-06-20T11:00:00Z"
        })
        
        headers = {
            'Authorization': f"Bearer {api_key}",
            'Version': "2021-07-28",
            'Content-Type': "application/json",
            'Accept': "application/json"
        }

        conn = http.client.HTTPSConnection("services.leadconnectorhq.com")

        payload = data_dict_clean
        conn.request("POST", f"/contacts/{contact_id}/tasks", json.dumps(payload), headers)

        res = conn.getresponse()
        data = res.read()

        print(data.decode("utf-8"))
        return
    
    def background_task(self , call_sid):
        ghl_calender = GHLCalendarAPI()
        api_key = sessions[call_sid]['api_key']
        file_path = sessions[call_sid]['file_name']
        location_id = sessions[call_sid]['location_id']
        calendars_id = ghl_calender.get_calender(location_id , api_key)
        start_date, end_date, time_24h_format , date_selected = ghl_calender.get_date_time(file_path)
        slot , get_free_slots , text = ghl_calender.fetch_available_slots(calendars_id , api_key , start_date, end_date, time_24h_format, date_selected)
        print("get_free_slots :",get_free_slots)
        time.sleep(5)
        return text , get_free_slots , calendars_id , slot