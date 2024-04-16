from dependency import *
from logic import sessions

class GHLContactHandler:
    
    def __init__(self):
        pass
    
    def get_contacts(self , call_sid , location_id , access_token , customer_number):
        conn = http.client.HTTPSConnection("services.leadconnectorhq.com")

        headers = {
            'Authorization': f"Bearer {access_token}",
            'Version': "2021-07-28",
            'Content-Type': "application/json",
            'Accept': "application/json"
        }

        conn.request("GET", f"/contacts/?locationId={location_id}", headers=headers)

        res = conn.getresponse()
        data = res.read()

        users_data_dict = json.loads(data) 
        phone_numbers = [contact["phone"] for contact in users_data_dict["contacts"]]
        
        if customer_number in phone_numbers:
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
                cursor.execute("SELECT contact_id FROM customer_data WHERE phone_number = %s AND location_id = %s", (customer_number,location_id,))
                existing_record = cursor.fetchone()
                
                if existing_record:
                    flag = True
                    contact_id = existing_record[0]
                
                else:
                    company_id = sessions[call_sid]['company_id']
                    company_name = sessions[call_sid]['company_name']
                    for contact in users_data_dict["contacts"]:
                        if contact["phone"] == customer_number:
                            contact_id = contact["id"]
                    cursor.execute("INSERT INTO customer_data (company_id , company_name , phone_number, contact_id , location_id) VALUES (%s, %s, %s , %s , %s)", (company_id , company_name , customer_number , contact_id , location_id))
                    flag = True
                
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
        else:
            flag = False
            contact_id = None
        
        return flag , contact_id
    
    def contact_id_generate(self , customer_number , call_sid , user_contact_info):
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
            cursor.execute("SELECT * FROM customer_data WHERE phone_number = %s AND location_id = %s", (customer_number,location_id,))
            existing_record = cursor.fetchone()
            
            if existing_record:
                cursor.execute("SELECT contact_id FROM customer_data WHERE phone_number = %s AND location_id = %s", (customer_number,location_id))
                retrieve_data = cursor.fetchone()
                contact_id = retrieve_data[0]
                self.update_contact(call_sid , contact_id , user_contact_info)
                sessions[call_sid]['contact_id'] = contact_id
            
            else:
                contact_id , flag = self.create_contact(call_sid , user_contact_info , customer_number)
                if flag == True:
                    sessions[call_sid]['contact_id'] = contact_id
                elif flag == False:
                    company_id = sessions[call_sid]['company_id']
                    company_name = sessions[call_sid]['company_name']
                    cursor.execute("INSERT INTO customer_data (company_id , company_name , phone_number, contact_id , location_id) VALUES (%s, %s, %s , %s , %s)", (company_id , company_name , customer_number, contact_id , location_id))
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
            if connection:
                cursor.close()
                connection.close()
                print()
                print("===========================================================")
                print("Connection closed.")
                print("===========================================================")
                print()
                    
    def get_subaccount_info(self , call_sid , user_appointment_info , customer_number , date_selected):
        # user_data_clean = {key.lstrip('- '): value if '-' in key else value for key, value in user_appointment_info.items()}
        start_index = user_appointment_info.find('{')
        end_index = user_appointment_info.rfind('}') + 1
        json_string = user_appointment_info[start_index:end_index]
        
        parsed_data = json.loads(json_string)
        
        first_name = parsed_data.get("First Name")
        last_name = parsed_data.get("Last Name")
        company_name = parsed_data.get("Company Name")
        time_selected = parsed_data.get("Time Selected")
        location_id = sessions[call_sid]['location_id']
        
        if date_selected is None:
            date_selected = datetime.datetime.now().strftime("%d-%m-%Y")
        
        contact_data = {
            "phone": customer_number,
            "firstName": first_name,
            "lastName": last_name,
            "name": first_name + " " + last_name,
            "locationId": location_id,
            "companyName": company_name,
            "dateSelected": date_selected,
            "timeSelected": time_selected,
            "tags": [
                    "By AI Software"
                    ]
        }
        return contact_data
    
    def create_contact(self, call_sid , user_contact_info , customer_number):
        access_token = sessions[call_sid]['access_token']
        
        conn = http.client.HTTPSConnection("services.leadconnectorhq.com")

        keys_to_remove = ['title', 'body', 'dueDate', 'completed', 'dateSelected', 'timeSelected']
        user_contact_info = {key: value for key, value in user_contact_info.items() if key not in keys_to_remove}
        
        status , contact_id = self.get_contacts(call_sid , sessions[call_sid]['location_id'] , access_token , customer_number)
        
        if status == True:
            flag = True
            self.update_contact(call_sid , contact_id , user_contact_info)
            
        elif status == False:
            headers = {
                'Authorization': f"Bearer {access_token}",
                'Version': "2021-07-28",
                'Content-Type': "application/json",
                'Accept': "application/json"
            }

            conn.request("POST", "/contacts/", json.dumps(user_contact_info), headers)

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
            flag = False
        
        return contact_id , flag
            
    def update_contact(self , call_sid , contact_id , user_contact_info):
        access_token = sessions[call_sid]['access_token']
        
        conn = http.client.HTTPSConnection("services.leadconnectorhq.com")

        keys_to_remove = ['title', 'body', 'dueDate', 'completed', 'dateSelected', 'timeSelected' , 'locationId']
        user_contact_info = {key: value for key, value in user_contact_info.items() if key not in keys_to_remove}
        
        headers = {'Authorization': f"Bearer {access_token}",
                   'Version': "2021-07-28",
                   'Content-Type': "application/json",
                   'Accept': "application/json"}

        conn.request("PUT", f"/contacts/{contact_id}", json.dumps(user_contact_info), headers)

        res = conn.getresponse()
        data = res.read()
        print(data.decode("utf-8"))
        
        
        if res.status == 201 or res.status == 200:
            print()   
            print("===========================================================")
            print("Contact updated successfully!")
            print("===========================================================")
            print()
            
        else:
            print()
            print("===========================================================")
            print("Error updating contact!")
            print("===========================================================")
            print()