from dependency import *
from logic import *

GHL_APPOINTMENTS_URL = constants.GHL_APPOINTMENTS_URL

class AppointmentHandler:

    def __init__(self):
        pass
    
    def slot_mapper(self, start_time_str):
        start_time = datetime.fromisoformat(start_time_str.replace('Z', '+00:00'))
        # Add 30 minutes
        end_time = start_time + timedelta(minutes=30)
        # Convert back to ISO format
        end_time_str = end_time.isoformat()
        return end_time_str

    def create_appointment(self, call_sid , calendar_id, start_time): 
        path = sessions[call_sid]['file_name']
        contact_id = sessions[call_sid]['contact_id']
        api_key = sessions[call_sid]['api_key']
        with open(path, "r") as json_file:    
            data_dict = json.load(json_file)
        data_dict_clean = {key.lstrip('- '): value if '-' in key else value for key, value in data_dict.items()}
        
        first_name = data_dict_clean["firstName"]
        last_name = data_dict_clean["lastName"]
        end_time = self.slot_mapper(start_time)
        # Update data dictionary with calendarId and timezone
        data_dict_clean.update({
            "calendarId": calendar_id,
            "contactId": contact_id,
            "startTime": start_time,
            "endTime": end_time,
            "title": f"{first_name} {last_name}"
        })
        
        
        conn = http.client.HTTPSConnection("services.leadconnectorhq.com")

        payload = data_dict_clean
        keys_to_remove = ['dateSelected', 'timeSelected']
        for key in keys_to_remove:
            payload.pop(key)
        
        headers = {
                    'Authorization': f"Bearer {api_key}",
                    'Version': "2021-07-28",
                    'Content-Type': "application/json",
                    'Accept': "application/json"
                }


        conn.request("POST", "/calendars/events/appointments", json.dumps(payload), headers)

        res = conn.getresponse()
        data = res.read()

        # import pdb; pdb.set_trace()
        
        if res.status == 201:
            return res.status
        else:
            return None