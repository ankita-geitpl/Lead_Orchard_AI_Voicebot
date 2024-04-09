from dependency import *
from logic import *


class GHLContactHandler:
    
    def __init__(self):
        pass
    
    def contact_id_generate(self , phone_number , call_sid , data):
        # Replace these values with your PostgreSQL database information
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
            cursor.execute("SELECT * FROM customer_data WHERE phone_number = %s AND location_id = %s", (phone_number,location_id,))
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
                cursor.execute("INSERT INTO customer_data (company_id , company_name , phone_number, contact_id , location_id) VALUES (%s, %s, %s , %s , %s)", (company_id , company_name , phone_number, contact_id , location_id))
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
        data_dict_clean = {key.lstrip('- '): value if '-' in key else value for key, value in appointment_info.items()}
        
        # Access the values using the keys
        first_name = data_dict_clean["First Name"]
        last_name = data_dict_clean["Last Name"]
        company_name = data_dict_clean["Company Name"]
        date_selected = data_dict_clean["Date Selected"]
        time_selected = data_dict_clean["Time Selected"]
        location_id = sessions[call_sid]['location_id']
        email = "example@example.com"
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

    # def create_contact(self , call_sid , user_data):
    #     api_key = sessions[call_sid]['api_key']
    #     conn = http.client.HTTPSConnection("services.leadconnectorhq.com")

    #     payload = user_data
    #     import pdb; pdb.set_trace()
    #     for key in payload.keys():
    #         if key == "title":
    #             keys_to_remove = ['title' , 'body' , 'dueDate' , 'completed']
    #             for key in keys_to_remove:
    #                 payload.pop(key)
    #         elif key == 'dateSelected' or key == 'timeSelected':
    #             keys_to_remove = ['dateSelected', 'timeSelected']
    #             for key in keys_to_remove:
    #                 payload.pop(key)

    #     headers = {
    #         'Authorization': f"Bearer {api_key}",
    #         'Version': "2021-07-28",
    #         'Content-Type': "application/json",
    #         'Accept': "application/json"
    #     }

    #     conn.request("POST", "/contacts/", json.dumps(payload), headers)

    #     res = conn.getresponse()
    #     data = res.read()
    #     response_dict = json.loads(data.decode('utf-8'))
    #     contact_id = response_dict['contact']['id']
        
    #     if res.status == 201 or res.status == 200:
    #         print()   
    #         print("===========================================================")
    #         print("Contact created successfully!")
    #         print("===========================================================")
    #         print()
    #     return contact_id
    
    def create_contact(self, call_sid, user_data):
        api_key = sessions[call_sid]['api_key']
        conn = http.client.HTTPSConnection("services.leadconnectorhq.com")

        payload = user_data

        # Keys to remove from payload
        keys_to_remove = ['title', 'body', 'dueDate', 'completed', 'dateSelected', 'timeSelected']

        # Create a new dictionary without the keys to remove
        updated_payload = {key: value for key, value in payload.items() if key not in keys_to_remove}

        headers = {
            'Authorization': f"Bearer {api_key}",
            'Version': "2021-07-28",
            'Content-Type': "application/json",
            'Accept': "application/json"
        }

        conn.request("POST", "/contacts/", json.dumps(updated_payload), headers)

        res = conn.getresponse()
        data = res.read()
        response_dict = json.loads(data.decode('utf-8'))
        contact_id = response_dict['contact']['id']

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
        import pdb; pdb.set_trace()
        data = res.read()

        if res.status == 201 or res.status == 200:
            print()   
            print("===========================================================")
            print("Contact updated successfully!")
            print("===========================================================")
            print()