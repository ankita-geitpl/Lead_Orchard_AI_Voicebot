from dependency import *
import constants

openai_api_key = constants.APIKEY

client = OpenAI(
  api_key=openai_api_key,
)

class FineTunedModelUpdater:
    def __init__(self) -> None:
        self.db_params = constants.db_params
        self.dashboard_url_auth_token = constants.DASHBOARD_URL_AUTH_TOKEN
        self.dashboard_url_company_data = constants.DASHBOARD_URL_COMPANY_DATA
        self.username = constants.DASHBOARD_USERNAME
        self.password = constants.DASHBOARD_PASSWORD
        self.job_id = None

    def get_fine_tuned_model_date_and_time(self) -> List[str]:
        extracted_date_and_time_from_database = []
        timestamps = []
        phone_numbers = []
        try:
            connection = psycopg2.connect(**self.db_params)
            cursor = connection.cursor()
            cursor.execute("SELECT last_updated_finetune_model FROM finetuning_data")
            last_updated_finetune_model = cursor.fetchall()
            for item in last_updated_finetune_model:
                for value in item:
                    extracted_date_and_time_from_database.append(value)
            for value in extracted_date_and_time_from_database:
                if value is not None:
                    if isinstance(value, datetime):
                        value = value.strftime("%Y-%m-%d %H:%M:%S.%f")
                    timestamp = datetime.strptime(value, "%Y-%m-%d %H:%M:%S.%f")
                    timestamps.append(timestamp)
                elif value is None:
                    timestamps.append(None)
            current_datetime = datetime.now()
            one_month_ago = current_datetime - timedelta(days=30)
            for timestamp in timestamps:
                if timestamp is None:
                    cursor.execute("SELECT phone_number FROM finetuning_data WHERE last_updated_finetune_model IS NULL")
                    result = cursor.fetchall()
                    for item in result:
                        for value in item:
                            if value not in phone_numbers:
                                phone_numbers.append(value)
                elif timestamp >= one_month_ago:
                    cursor.execute("SELECT phone_number FROM finetuning_data WHERE last_updated_finetune_model = %s", (timestamp,))
                    result = cursor.fetchall()
                    for value in result:
                        phone_numbers.append(value)
            connection.commit()
        except psycopg2.Error as e:
            print("Error connecting to the database:", e)
        finally:
            if connection:
                cursor.close()
                connection.close()
        return phone_numbers
    
    def get_auth_token(self) -> Optional[str]:
        credentials = {
            'username': self.username,
            'password': self.password
        }
        response = requests.post(self.dashboard_url_auth_token, json=credentials)
        if response.status_code == 200:
            data = response.json()
            token = data.get('token')
            return token
        else:
            print('Failed to fetch data:', response.status_code, response.text)
            return None
        
    def get_all_company_data(self) -> dict:
        token = self.get_auth_token()
        phone_numbers = self.get_fine_tuned_model_date_and_time()
        company_ids_phone_dict = {}
        headers = {
            'accept': 'application/json',
            'X-CSRFToken': 'fsrXgcTJbOZgL6QrhkWDRgwNuu1Z90m1im9bqBkvbBOCYCzvavlFK019anqm5UCy',
            'Authorization': f'Token {token}'
        }
        response = requests.get(self.dashboard_url_company_data , headers=headers)
        if response.status_code == 200:
            data = response.json()
            for phone_number in phone_numbers:
                for item in data:
                    if item['phone'] == phone_number:
                        id = item['id']
                        company_ids_phone_dict[f'{id}'] = phone_number
                        break
        else:
            print('Failed to fetch data:', response.status_code, response.text)
        return company_ids_phone_dict
    
    def get_questionnaire_data(self , company_id) -> Optional[dict]:
        token = self.get_auth_token()
        organization_id = company_id 
        url = f'http://45.79.197.171:8000/api/v1/questions/questions_answers/{organization_id}/'
        headers = {
            'accept': 'application/json',
            'X-CSRFToken': 'fsrXgcTJbOZgL6QrhkWDRgwNuu1Z90m1im9bqBkvbBOCYCzvavlFK019anqm5UCy',
            'Authorization': f'Token {token}'
        }
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            return data
        else:
            print('Failed to fetch data:', response.status_code, response.text)
            return None
    
    def prepare_data(self , dictionary_data , file_name) -> None:
        with open(file_name, 'w') as outfile:
            for entry in dictionary_data:
                json.dump(entry, outfile)
                outfile.write('\n')
    
    def signal_handler(self) -> None:
        status = client.fine_tuning.jobs.retrieve(self.job_id).status
        print(f"Stream interrupted. Job is still {status}.")

    def finetunning_job(self) -> None:
        company_ids_phone_dict = self.get_all_company_data()
        for organisation_id, phone_number in company_ids_phone_dict.items():
            fine_tune_date_time = datetime.now()
            dataset = self.get_questionnaire_data(organisation_id)
            random.shuffle(dataset)
            
            training_data = dataset[:int(len(dataset)*0.8)]
            validation_data = dataset[int(len(dataset)*0.8):]
            
            train_file_name = TRAIN_DATA_SYS_PATH +"train_"+f'{phone_number}_'+organisation_id
            val_file_name = VAL_DATA_SYS_PATH +'val_'+f'{phone_number}_'+organisation_id
            
            self.prepare_data(training_data, train_file_name)
            self.prepare_data(validation_data, val_file_name)
            training_file_id = client.files.create(
                                file=open(train_file_name, "rb"),
                                purpose="fine-tune"
                                )

            validation_file_id = client.files.create(
                                file=open(val_file_name, "rb"),
                                purpose="fine-tune"
                                )

            print(f"Training File ID: {training_file_id}")
            print(f"Validation File ID: {validation_file_id}")
            
            response = client.fine_tuning.jobs.create(
                        training_file=training_file_id.id, 
                        validation_file=validation_file_id.id,
                        model="gpt-3.5-turbo-1106", 
                        # hyperparameters={
                        #     "n_epochs": 15,
                        #     "batch_size": 3,
                        #     "learning_rate_multiplier": 0.3
                        # }
                        )
            
            self.job_id = response.id
            status = response.status

            print(f'Fine-tuning model with jobID: {self.job_id}.')
            print(f"Training Response: {response}")
            print(f"Training Status: {status}")
            
            print(f"Streaming events for the fine-tuning job: {self.job_id}")

            signal.signal(signal.SIGINT, self.signal_handler)

            events = client.fine_tuning.jobs.list_events(fine_tuning_job_id=self.job_id)
            try:
                for event in events:
                    print(
                        f'{datetime.fromtimestamp(event.created_at)} {event.message}'
                    )
            except Exception:
                print("Stream interrupted (client disconnected).")
                
            status = client.fine_tuning.jobs.retrieve(self.job_id).status
            if status not in ["succeeded", "failed"]:
                print(f"Job not in terminal status: {status}. Waiting.")
                while status not in ["succeeded", "failed"]:
                    time.sleep(2)
                    status = client.fine_tuning.jobs.retrieve(self.job_id).status
                    print(f"Status: {status}")
            else:
                print(f"Finetune job {self.job_id} finished with status: {status}")
            
            print("Checking other finetune jobs in the subscription.")
            result = client.fine_tuning.jobs.list()
            print(f"Found {len(result.data)} finetune jobs.")
            
            fine_tuned_model = result.data[0].fine_tuned_model
            print(fine_tuned_model)
                        
            try:
                connection = psycopg2.connect(**self.db_params)
                cursor = connection.cursor()
                cursor.execute("UPDATE finetuning_data SET company_id = %s, model_id = %s, last_updated_finetune_model = %s WHERE phone_number = %s", (organisation_id, fine_tuned_model, fine_tune_date_time, phone_number))
                print("Successfully updated the database")
                connection.commit()
            except psycopg2.Error as e:
                print("Error connecting to the database:", e)
            finally:
                if connection:
                    cursor.close()
                    connection.close()

# Example of using the class:
updater = FineTunedModelUpdater()
updater.finetunning_job()
