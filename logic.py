from dependency import *

openai_api_key = os.environ["OPENAI_API_KEY"] = constants.APIKEY
GOHIGHLEVEL_API_URL = "https://rest.gohighlevel.com/v1/contacts"
API_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJsb2NhdGlvbl9pZCI6ImIwTkQ0cTZHT1FTaElHMWVhQk04IiwiY29tcGFueV9pZCI6IjZ5aDhvREF4V3FxVFVFMjFrS2JIIiwidmVyc2lvbiI6MSwiaWF0IjoxNzA4Njg0NDcyNjM0LCJzdWIiOiJ1c2VyX2lkIn0.j6A2ceU9L5YW18I_QiE3vBXvc13pffRlQ2SDDlt1yp8"
sessions = {}
# chat_history = []
data_pdf_path = ""
prompt_data = ""
api_key=""
location_id = ""

class TwilioCallHandler:

    def __init__(self):
        pass

    def user_id_generate(self):
        uuid_bytes = uuid.uuid1().bytes
        encoding = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789'
        short_uuid = ''.join(encoding[b % 62] for b in uuid_bytes[:8])
        return short_uuid
    
    def get_prompt_file(self , to):
        # Replace these values with your PostgreSQL database information
        global prompt_data , data_pdf_path, location_id, api_key
        db_params = constants.db_params
        
        try:
            # Create a connection to the database
            connection = psycopg2.connect(**db_params)
            print("Connected to the database!")
            
            # Create a cursor
            cursor = connection.cursor()
            
            # Fetch the PDF file from the database based on the phone number
            cursor.execute("SELECT prompt_file_path,location_id,api_key FROM company_data WHERE phone_number = %s", (to,))
            retrieve_data = cursor.fetchone()
            prompt_pdf_path = retrieve_data[0]
            location_id = retrieve_data[1]
            api_key = retrieve_data[2]

            
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
    
    def extract_date(self,text):
        print("++++++++++++++++++++++++++++++++++++++text",text)
        time_cleaned = text.replace('.', '')
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
                parsed_date = parser.parse(text, fuzzy=True)
                formatted_date = parsed_date.strftime("%d-%m-%Y")
                return formatted_date
            except ValueError:
                # If parsing fails, return None
                return None
        
    def get_subaccount_info(self , appointment_info , to_number):
        # Read the JSON file
        # with open(path, "r") as json_file:
        #     data_dict = json.load(json_file)

        # import pdb;pdb.set_trace()
        data_dict_clean = {key.lstrip('- '): value if '-' in key else value for key, value in appointment_info.items()}
        print("@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@")
        print("@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@")
        print("data_dict_clean--------------------------------------",data_dict_clean)
        # Access the values using the keys
        first_name = data_dict_clean["First Name"]
        last_name = data_dict_clean["Last Name"]
        company_name = data_dict_clean["Company Name"]
        # appointment_info.update({'locationId':location_id})
        phone_number_preference = data_dict_clean["Is this phone number the best to call"]
        # confirmation = data_dict_clean["Confirmation"]
        date_selected = data_dict_clean["Date Selected"]
        time_selected = data_dict_clean["Time Selected"]


        contact_data = {
            "phone": to_number,
            "firstName": first_name,
            "lastName": last_name,
            "name": first_name + " " + last_name,
            "locationId": location_id,
            "companyName": company_name,
            "dateSelected": date_selected,
            "timeSelected": time_selected,
            "tags": [
                    "By AI softwere"
                    ]
        }
        # file_name = "C://Users//akash//OneDrive//Desktop//Availably-Voicebot-GEITPL//user_appoint_data//"+"availbaly_1_new"+".json"
        # with open(file_name, 'w') as json_file:
        #         json.dump(contact_data, json_file, indent=4)

        return contact_data

    def create_contact(self , data):
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        response = requests.post(GOHIGHLEVEL_API_URL, headers=headers, json=data)
        if response.status_code == 200:
            return response.json().get('data', {}),201
        else:
            return None
        
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