from dependency import *
import constants
from GHL_calender_API import *
from fixed_prompt.create_appointment_prompt import *
from fixed_prompt.getdatetime_prompt import *
from fixed_prompt.delete_appointment_prompt import *
from fixed_prompt.create_task_prompt import *
from fixed_prompt.update_appointment_prompt import *


openai_api_key = os.environ["OPENAI_API_KEY"] = constants.APIKEY
GOHIGHLEVEL_API_URL = constants.GOHIGHLEVEL_API_URL

sessions = {}

current_date = datetime.now().date()
end_of_day = datetime.combine(current_date + timedelta(days=1), datetime.min.time()) - timedelta(seconds=1)
end_session_time = end_of_day.replace(hour=23, minute=59, second=59)

create_app_prompt = appoint_prompt
gendatetime_prompt = dt_appoint_prompt
delete_app_prompt = delete_appoint_prompt
create_task_prompt = task_prompt
update_app_prompt = update_appoint_prompt

class TwilioCallHandler:

    def __init__(self):
        pass
    
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
                prompt_data = prompt_data+"\n\n"+create_app_prompt+"\n\n"+gendatetime_prompt+"\n\n"+delete_app_prompt+"\n\n"+create_task_prompt+"\n\n"+update_app_prompt+" : "+"{context}"
            else:
                prompt_data = prompt_data+"\n\n"+create_app_prompt+"\n\n"+gendatetime_prompt+"\n\n"+delete_app_prompt+"\n\n"+create_task_prompt+"\n\n"+update_app_prompt
            
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

        return user_id , prompt_data , data_pdf_path , location_id , company_id , company_name , access_token

    def extract_date(self , text):
        time_cleaned = text.replace('.', '')
        time_cleaned = time_cleaned.lower().replace('i am', '')
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

    def extract_date_2(self , text):
        time_cleaned = text.replace('.', '')
        time_cleaned = time_cleaned.lower().replace('i am', '')
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
                    formatted_date = parsed_date.strftime("%Y-%m-%d")
                    return formatted_date
            
            except ValueError:
                # If parsing fails, return None
                return None

    def preprocess_sentence(self , sentence):
        # Replace 'today' with today's date
        today_date = datetime.now().strftime('%d-%m-%Y')
        sentence = re.sub(r'\b(?:today)\b', today_date, sentence, flags=re.IGNORECASE)
    
        # Replace 'tomorrow' with tomorrow's date
        tomorrow_date = (datetime.now() + timedelta(days=1)).strftime('%d-%m-%Y')
        sentence = re.sub(r'\b(?:tomorrow)\b', tomorrow_date, sentence, flags=re.IGNORECASE)  
        return sentence

    def extract_time(self , text):
        # Regular expression to match time in the format hh:mm AM/PM
        if "." in text:
            text = text.lower().replace("." , "")
        time_pattern = r'\b\d{1,2}\s*(?::\s*\d{2})?\s*(?:AM|PM|am|pm|)?\b'

        # Search for the time pattern in the text
        time_match = re.search(time_pattern, text)

        if time_match:
            return time_match.group(0)
        else:
            return None

    def get_documents_from_web(self , data_pdf_path):
        file_loader = PyMuPDFLoader(data_pdf_path)
        documents = file_loader.load()
        
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
        timezone = sessions[call_sid]['timezone']
        
        calendars_id = ghl_calender.get_calender(location_id , access_token)
        
        start_date, end_date, time_24h_format , date_selected = ghl_calender.get_date_time(user_data)
        
        slot , get_free_slots , text , timezone_user = ghl_calender.fetch_available_slots(calendars_id , access_token , start_date, end_date, time_24h_format, date_selected , timezone)
        
        time.sleep(5)
        
        return text , get_free_slots , calendars_id , slot , timezone_user