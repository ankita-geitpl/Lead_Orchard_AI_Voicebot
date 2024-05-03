from dependency import *
from logic import sessions
from utters import task_created_message , task_failed_message

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
                
        return contact_id
    
    def get_clean_data(self, call_sid, appointment_info, customer_number):
        start_index = appointment_info.find('{')
        end_index = appointment_info.rfind('}') + 1
        json_string = appointment_info[start_index:end_index]
        
        data = json.loads(json_string)

        # Store values in variables, handling missing values
        first_name = data.get("First Name", "")
        last_name = data.get("Last Name", "")
        company_name = data.get("Company Name" , "")
        title = data.get("Title")
        body = data.get("Description")


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
        location_id = sessions[call_sid]['location_id']
        db_params = constants.db_params
        
        try:
            # Create a connection to the database
            connection = psycopg2.connect(**db_params)
            
            # Create a cursor
            cursor = connection.cursor()
 
            #  # Check if the phone number exists in the database
            cursor.execute("SELECT task_assignee_id FROM company_data WHERE location_id = %s", (location_id,))
            existing_record = cursor.fetchone()
            if existing_record:
                task_assignee_id = existing_record[0]
            else:
                task_assignee_id = None
            
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
                
        return task_assignee_id
    
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
            return task_created_message
        else:  
            return task_failed_message