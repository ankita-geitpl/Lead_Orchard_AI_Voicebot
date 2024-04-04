from dependency import *
from logic import *
GHL_APPOINTMENTS_URL = "https://rest.gohighlevel.com/v1/appointments"

class AppointmentHandler:

    def __init__(self):
        pass

    def create_appointment(self, account_number, data, calendar_id, time_zone,slot):        
        subaccount_info = TwilioCallHandler.get_subaccount_info(account_number)
        location_id = subaccount_info["location_id"]
        data.update({'locationId': location_id})       
        api_key = subaccount_info["api_key"]
        

        # Update data dictionary with calendarId and timezone
        data.update({
            "calendarId": calendar_id,
            "selectedTimezone": time_zone,
            # "selectedSlot": slot,
            # "email": "example@example.com",
            # "phone": account_number,
        })

    
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        response = requests.post(GHL_APPOINTMENTS_URL, headers=headers, json=data)
        
        if response.status_code == 200:
            return response.json().get('data', {}), 200
        else:
            return None