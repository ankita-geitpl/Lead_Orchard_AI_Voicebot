from dependency import *
from ghl_contact_create import *

class GHLTaskHandler:
    
    def __init__ (self):
        pass
    
    def parse_time(self , time_str):
        try:
            # Try parsing with minutes
            time_object = datetime.strptime(time_str, '%I:%M %p')
        except ValueError:
            # If parsing with minutes fails, try parsing without minutes
            time_object = datetime.strptime(time_str, '%I %p')
        
        return time_object
    
    def get_due_date_time(self , due_date , due_time):
        # import pdb; pdb.set_trace()
        time_selected = due_time
        time_selected = time_selected.replace('.', '')
        time_selected = time_selected.lower()
        time_selected = self.parse_time(time_selected)
        time_24h_format = time_selected.strftime('%H:%M:%S')
        due_date_time = datetime.strptime(due_date, '%d-%m-%Y').strftime('%Y-%m-%d')+"T"+ time_24h_format+"Z"
        return due_date_time
    
    def contact_id_check(self , call_sid , phone_number):
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
            cursor.execute("SELECT contact_id FROM customer_data WHERE phone_number = %s AND location_id = %s", (phone_number,location_id,))
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
            # Close the cursor and connection
            if connection:
                cursor.close()
                connection.close()
                print()
                print("===========================================================")
                print("Connection closed.")
                print("===========================================================")
                print()
                
        return contact_id
    
    # def get_clean_data(self , call_sid , appointment_info , customer_number):
    #     data_dict_clean = {key.lstrip('- '): value if '-' in key else value for key, value in appointment_info.items()}

    #     first_name = data_dict_clean["First Name"]
    #     last_name = data_dict_clean["Last Name"]
    #     company_name = data_dict_clean["Company Name"]
    #     title = data_dict_clean["Title"]
    #     description = data_dict_clean["Description"]
    #     location_id = sessions[call_sid]['location_id']
    #     due_date = data_dict_clean["Due Date"]
    #     # import pdb ; pdb.set_trace()
    #     for key in data_dict_clean.keys():
    #         if key == "Due Time":
    #             due_time = data_dict_clean["Due Time"]
    #         elif key == "Time":
    #             due_time = data_dict_clean["Time"]
    #     due_date_time = self.get_due_date_time(due_date , due_time)
    #     completed = False
    #     contact_data = {
    #         "title": title,
    #         "body": description,
    #         "dueDate": due_date_time , 
    #         "completed": completed , 
    #         "phone": customer_number,
    #         "firstName": first_name,
    #         "lastName": last_name,
    #         "name": first_name + " " + last_name,
    #         "locationId": location_id,
    #         "companyName": company_name,
    #         "tags": [
    #                 "By AI softwere"
    #                 ]
    #     }
    #     return contact_data
    
    def get_clean_data(self, call_sid, appointment_info, customer_number):
        data_dict_clean = {key.lstrip('- '): value if '-' in key else value for key, value in appointment_info.items()}

        # Check if keys exist and replace with default values if missing
        keys_to_check = ["First Name", "Last Name", "Company Name", "Title", "Description", "Due Date"]
        default_values = {"First Name": "", "Last Name": "", "Company Name": "", "Title": "", "Description": "", "Due Date": ""}
        for key in keys_to_check:
            if key not in data_dict_clean:
                data_dict_clean[key] = default_values[key]

        first_name = data_dict_clean["First Name"]
        last_name = data_dict_clean["Last Name"]
        company_name = data_dict_clean["Company Name"]
        title = data_dict_clean["Title"]
        description = data_dict_clean["Description"]
        location_id = sessions[call_sid]['location_id']
        
        # Check if either "Due Time" or "Time" exists and assign value to due_time
        for key in data_dict_clean.keys():
            if key == "Due Time":
                due_time = data_dict_clean["Due Time"]
            elif key == "Time":
                due_time = data_dict_clean["Time"]

        due_date = data_dict_clean["Due Date"]
        due_date_time = self.get_due_date_time(due_date, due_time)
        completed = False
        contact_data = {
            "title": title,
            "body": description,
            "dueDate": due_date_time,
            "completed": completed,
            "phone": customer_number,
            "firstName": first_name,
            "lastName": last_name,
            "name": first_name + " " + last_name,
            "locationId": location_id,
            "companyName": company_name,
            "tags": ["By AI software"]
        }
        return contact_data

    
    def create_task(self , call_sid , contact_info): 
        api_key = sessions[call_sid]['api_key']
        contact_id = sessions[call_sid]['contact_id']
        title = contact_info["title"]
        description = contact_info["body"]   
        due_date = contact_info["dueDate"]
         
        data_dict_clean = {}
        data_dict_clean.update({
            "title": title,
            "body": description,
            "completed": False,
            "dueDate": due_date
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
        import pdb; pdb.set_trace()
        data = res.read()
        print(data.decode("utf-8"))
        
        return