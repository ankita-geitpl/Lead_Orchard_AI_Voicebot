from dependency import *
import datetime

CLIENT_ID = constants.MP_CLIENT_ID
CLIENT_SECRET =  constants.MP_CLIENT_SECRET

class AuthTokenGenerator:
    def __init__(self):
        self.auth_token = None

    def generate_auth_token(self , starttime_token , company_number):
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
            cursor.execute("SELECT token_refresh_date FROM company_data WHERE phone_number = %s", (company_number,))
            endtime_token = cursor.fetchone()[0]
            print("==================================================")
            print(endtime_token)
            print("==================================================")
            # import pdb; pdb.set_trace()
            if endtime_token is None or starttime_token >= endtime_token:
                # import pdb; pdb.set_trace()
                cursor.execute("SELECT refresh_token FROM company_data WHERE phone_number = %s", (company_number,))
                refresh_token = cursor.fetchone()[0]
                conn = http.client.HTTPSConnection("services.leadconnectorhq.com")
                payload = f"client_id={CLIENT_ID}&client_secret={CLIENT_SECRET}&grant_type=refresh_token&code={refresh_token}&refresh_token={refresh_token}"

                headers = {
                    'Content-Type': "application/x-www-form-urlencoded",
                    'Accept': "application/json"
                }

                conn.request("POST", "/oauth/token", payload, headers)

                res = conn.getresponse()
                data = res.read()
                token_details = json.loads(data.decode("utf-8"))
                access_token_new = token_details.get('access_token')
                refresh_token_new = token_details.get('refresh_token')
                endtime_token = starttime_token + datetime.timedelta(days=1)
                cursor.execute("UPDATE company_data SET token_refresh_date = %s , access_token = %s , refresh_token = %s WHERE phone_number = %s" , (endtime_token , access_token_new , refresh_token_new , company_number))
            
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