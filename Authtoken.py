from dependency import *
import datetime

CLIENT_ID = constants.MP_CLIENT_ID
CLIENT_SECRET =  constants.MP_CLIENT_SECRET

class AuthTokenGenerator:
    def __init__(self):
        self.auth_token = None
    
    def generate_auth_token(self, start_time_token, company_number):
        # Get database parameters from constants
        db_params = constants.db_params
        
        try:
            # Create a connection to the database
            with psycopg2.connect(**db_params) as connection:
                with connection.cursor() as cursor:
                    # Retrieve the token refresh date from the database
                    cursor.execute("SELECT token_refresh_date FROM company_data WHERE phone_number = %s", (company_number,))
                    end_time_token = cursor.fetchone()[0]
                    
                    # If token is expired or doesn't exist, refresh it
                    if end_time_token is None or start_time_token >= end_time_token:
                        cursor.execute("SELECT refresh_token FROM company_data WHERE phone_number = %s", (company_number,))
                        refresh_token = cursor.fetchone()[0]
                        
                        # Request a new token
                        conn = http.client.HTTPSConnection("services.leadconnectorhq.com")
                        payload = f"client_id={constants.MP_CLIENT_ID}&client_secret={constants.MP_CLIENT_SECRET}&grant_type=refresh_token&code={refresh_token}&refresh_token={refresh_token}"
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
                        
                        # Calculate new token expiration time
                        end_time_token = start_time_token + datetime.timedelta(days=1)
                        
                        # Update the database with new token details
                        cursor.execute("UPDATE company_data SET token_refresh_date = %s, access_token = %s, refresh_token = %s WHERE phone_number = %s", (end_time_token, access_token_new, refresh_token_new, company_number))
                    
                    connection.commit()
        
        except Error as e:
            print()
            print("===========================================================")
            print("Error connecting to the database:", e)
            print("===========================================================")
            print()