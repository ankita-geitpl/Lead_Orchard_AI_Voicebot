from dependency import *
import constants
from GHL_calendar_API import *
# from GHL_task_notes_create import GHLTaskNotesHandler

openai_api_key = os.environ["OPENAI_API_KEY"] = constants.APIKEY
GOHIGHLEVEL_API_URL = constants.GOHIGHLEVEL_API_URL

sessions = {}

current_date = datetime.now().date()
end_of_day = datetime.combine(current_date + timedelta(days=1), datetime.min.time()) - timedelta(seconds=1)
end_session_time = end_of_day.replace(hour=23, minute=59, second=59)


class TwilioCallHandler:

    def __init__(self):
        pass
    
    def check_status(self, call_sid , call_status):
        if call_status == "completed":
            speech_input = """Your are a intelligent  bot for summering the conversation for the important key points of the conversation so Please summarize the conversation between the user and the voice bot, highlighting key points only. Don't take note of unnecessary points."""
            ai_response = self.run_assistant(call_sid , speech_input)
            
            def create_notes(call_sid , ai_response):
                access_token = sessions[call_sid]['access_token']
                contact_id = sessions[call_sid]['contact_id'] 
                
                data_dict_clean = {}
                data_dict_clean.update({
                    "body": ai_response
                })
                
                headers = {
                    'Authorization': f"Bearer {access_token}",
                    'Version': "2021-07-28",
                    'Content-Type': "application/json",
                    'Accept': "application/json"
                }

                conn = http.client.HTTPSConnection("services.leadconnectorhq.com")

                conn.request("POST", f"/contacts/{contact_id}/notes", json.dumps(data_dict_clean), headers)

                res = conn.getresponse()
                if res.status == 201 or res.status == 200:
                    print("Note created successfully!")
                else:  
                    print("Note creation failed!")
            
            create_notes(call_sid , ai_response)
    
    def get_prompt_file(self , company_number):
        # Replace these values with your PostgreSQL database information
        prompt_data = None
        data_pdf_path = None
        location_id = None
        access_token = None
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
            cursor.execute("SELECT user_id , prompt_file_path ,location_id , company_id , company_name , access_token FROM company_data WHERE phone_number = %s", (company_number,))
            retrieve_data = cursor.fetchone()
            user_id = retrieve_data[0]
            prompt_pdf_path = retrieve_data[1]
            location_id = retrieve_data[2]
            company_id = retrieve_data[3]
            company_name = retrieve_data[4]
            access_token = retrieve_data[5]

            
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

        return user_id , prompt_data , data_pdf_path , location_id , company_id , company_name , access_token

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
        
        start_time = time.time()
        answer = self.process_chat(chain, ques, chat_history)
        end_time = time.time()
        chat_history.append(HumanMessage(content=ques))
        chat_history.append(AIMessage(content=answer))
        sessions[call_sid]['chat_history'] = chat_history
        print("Time taken for processing:", end_time - start_time, "seconds")

        return answer
    
    
    
class GHLSlotsHandler:
    
    def __init__(self):
        pass
    
    def background_task(self , call_sid):
        ghl_calender = GHLCalendarAPI()
        
        access_token = sessions[call_sid]['access_token']
        user_data = sessions[call_sid]['file_name']
        location_id = sessions[call_sid]['location_id']
        
        calendars_id = ghl_calender.get_calender(location_id , access_token)
        
        start_date, end_date, time_24h_format , date_selected = ghl_calender.get_date_time(user_data)
        
        slot , get_free_slots , text = ghl_calender.fetch_available_slots(calendars_id , access_token , start_date, end_date, time_24h_format, date_selected)
        
        print()   
        print("===========================================================")
        print("Free slots:" , get_free_slots)
        print("===========================================================")
        print()
        
        time.sleep(5)
        
        return text , get_free_slots , calendars_id , slot