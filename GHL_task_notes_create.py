from dependency import *
from logic import sessions

class GHLTaskNotesHandler:
    
    def __init__ (self):
        pass
    
    def get_due_date_time(self):
        current_datetime = datetime.now()
        future_datetime = current_datetime + timedelta(hours=48)
        future_date_time = future_datetime.strftime('%Y-%m-%dT%H:%M:%SZ')
        return future_date_time
    
    def contact_id_check(self , call_sid , customer_number):
        location_id = sessions[call_sid]['location_id']
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
 
            #  # Check if the phone number exists in the database
            cursor.execute("SELECT contact_id FROM customer_data WHERE phone_number = %s AND location_id = %s", (customer_number,location_id,))
            existing_record = cursor.fetchone()
            if existing_record:
                contact_id = existing_record[0]
            else:
                contact_id = None
            
            connection.commit()
        
        except Error as e:
            print()
            print("===========================================================")
            print("Error connecting to the database:", e)
            print("===========================================================")
            print()
        
        finally:
            if connection:
                cursor.close()
                connection.close()
                print()
                print("===========================================================")
                print("Connection closed.")
                print("===========================================================")
                print()
                
        return contact_id
    
    def get_clean_data(self, call_sid, appointment_info, customer_number):
        # user_data_clean = {key.lstrip('- '): value if '-' in key else value for key, value in appointment_info.items()}
        if type(appointment_info) is str:
            start_index = appointment_info.find('{')
            end_index = appointment_info.rfind('}') + 1
            json_string = appointment_info[start_index:end_index]
            
            parsed_data = json.loads(json_string)

            first_name = parsed_data.get("First Name")
            last_name = parsed_data.get("Last Name")
            company_name = parsed_data.get("Company Name")
            title = parsed_data.get("Title")
            body = parsed_data.get("Description")
        
        elif type(appointment_info) is dict:
            braces_indices = [(m.start(), m.end()) for m in re.finditer(r'\{|\}', appointment_info)]
            start_index, end_index = braces_indices[0][0], braces_indices[-1][1]
            appointment_info = appointment_info[start_index:end_index]
            # Iterate over the dictionary and clean values
            for key, value in appointment_info.items():
                # Check if value contains double quotes or commas
                if '"' in value or ',' in value:
                    # Remove double quotes and commas from the value
                    appointment_info[key] = value.strip('",')
                    

            # Accessing specific fields from the dictionary
            title = appointment_info.get('Title', '')
            body = appointment_info.get('Description', '')
            first_name = appointment_info.get('First Name', '')
            last_name = appointment_info.get('Last Name', '')
            company_name = appointment_info.get('Company Name', '')

        location_id = sessions[call_sid]['location_id']
        due_date_time = self.get_due_date_time()
        
        user_contact_data = {
            "title": title,
            "body": body,
            "dueDate": due_date_time,
            "phone": customer_number,
            "firstName": first_name,
            "lastName": last_name,
            "name": first_name + " " + last_name,
            "locationId": location_id,
            "companyName": company_name,
            "tags": ["By AI software"]
        }
        
        return user_contact_data

    def get_admin_id(self , call_sid):
        access_token = sessions[call_sid]['access_token']
        location_id = sessions[call_sid]['location_id']
        
        conn = http.client.HTTPSConnection("services.leadconnectorhq.com")
        headers = {
                        'Authorization': f"Bearer {access_token}",
                        'Version': "2021-07-28",
                        'Content-Type': "application/json",
                        'Accept': "application/json"
                }

        conn.request("GET", f"/users/?locationId={location_id}", headers=headers)

        res = conn.getresponse()
        data = res.read()
        user_id_data = data.decode("utf-8")
        response_data = json.loads(user_id_data)
        admin_ids = []
        for user in response_data["users"]:
                if user["roles"]["role"] == "admin":
                        admin_ids.append(user["id"])

        return admin_ids[0]
    
    def create_task(self , call_sid , contact_info): 
        access_token = sessions[call_sid]['access_token']
        contact_id = sessions[call_sid]['contact_id']
        title = contact_info["title"]
        description = contact_info["body"]   
        due_date = contact_info["dueDate"]
        admin_id = str(self.get_admin_id(call_sid))
        
        user_task_data = {}
        user_task_data.update({
            "title": title,
            "body": description,
            "completed": False,
            "dueDate": due_date,
            "assignedTo": admin_id
        })
        
        headers = {
            'Authorization': f"Bearer {access_token}",
            'Version': "2021-07-28",
            'Content-Type': "application/json",
            'Accept': "application/json"
        }

        conn = http.client.HTTPSConnection("services.leadconnectorhq.com")

        conn.request("POST", f"/contacts/{contact_id}/tasks", json.dumps(user_task_data), headers)

        res = conn.getresponse()
        
        if res.status == 201 or res.status == 200:
            return "Task created successfully!"
        else:  
            return "Task creation failed!"