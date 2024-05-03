from dependency import *
from logic import sessions
from utters import message_for_no_appointment_scheduled_deletation , appointment_cancellation_message , message_for_error_encountered_while_appointment_cancellation

GHL_APPOINTMENTS_URL = constants.GHL_APPOINTMENTS_URL

class GHLAppointmentHandler:

    def __init__(self):
        pass
    
    def get_event_id(self , call_sid , date = None):
        access_token = sessions[call_sid]['access_token']
        contact_id = sessions[call_sid]['contact_id']
        if date is None:
            conn = http.client.HTTPSConnection("services.leadconnectorhq.com")
            headers = {
                            'Authorization': f"Bearer {access_token}",
                            'Version': "2021-07-28",
                            'Content-Type': "application/json",
                            'Accept': "application/json"
                    }
            conn.request("GET", f"/contacts/{contact_id}/appointments", headers=headers)
            
            res = conn.getresponse()
            data = res.read()
            
            user_appoint_data = data.decode("utf-8")
            response_data = json.loads(user_appoint_data)
            if response_data["events"]:
                for event in response_data["events"]:
                    event_id = event["id"]
                    return event_id
            else:
                return None

        elif date is not None:
            conn = http.client.HTTPSConnection("services.leadconnectorhq.com")
            headers = {
                            'Authorization': f"Bearer {access_token}",
                            'Version': "2021-07-28",
                            'Content-Type': "application/json",
                            'Accept': "application/json"
                    }
            conn.request("GET", f"/contacts/{contact_id}/appointments", headers=headers)
            
            res = conn.getresponse()
            data = res.read()
            user_appoint_data = data.decode("utf-8")
            response_data = json.loads(user_appoint_data)
            try:
                if response_data:
                    desired_date = datetime.strptime(date, "%d-%m-%Y").strftime("%Y-%m-%d")

                    # Extract ids based on the desired date
                    ids = [event["id"] for event in response_data["events"] if event["startTime"].startswith(desired_date)]

                    print(ids)

                    return ids[0]
            
                else:
                    return None
            except:
                return None


    def slot_mapper(self, start_time):
        start_time = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
        end_time = start_time + timedelta(minutes=30)
        end_time = end_time.isoformat()
        return end_time

    def create_appointment(self, call_sid , calendar_id, start_time): 
        user_data_file = sessions[call_sid]['file_name']
        contact_id = sessions[call_sid]['contact_id']
        access_token = sessions[call_sid]['access_token']
        
        with open(user_data_file, "r") as json_file:    
            user_data = json.load(json_file)
        user_data_clean = {key.lstrip('- '): value if '-' in key else value for key, value in user_data.items()}
    
        end_time = self.slot_mapper(start_time)
        
        # Update data dictionary with calendarId and timezone
        user_data_clean.update({
            "calendarId": calendar_id,
            "contactId": contact_id,
            "startTime": start_time,
            "endTime": end_time,
            "title": "Scheduling Appointment with AI Voicebot",
        })
        
        conn = http.client.HTTPSConnection("services.leadconnectorhq.com")

        keys_to_remove = ['dateSelected', 'timeSelected']
        for key in keys_to_remove:
            user_data_clean.pop(key)
        
        headers = {
                    'Authorization': f"Bearer {access_token}",
                    'Version': "2021-07-28",
                    'Content-Type': "application/json",
                    'Accept': "application/json"
                }

        conn.request("POST", "/calendars/events/appointments", json.dumps(user_data_clean), headers)

        res = conn.getresponse()
        
        if res.status == 201 or res.status == 200:
            return res.status
        else:
            return None


    def update_appointment(self, call_sid , calendar_id, start_time):
        user_data_file = sessions[call_sid]['file_name']
        contact_id = sessions[call_sid]['contact_id']
        access_token = sessions[call_sid]['access_token']
        date = sessions[call_sid]['date_extract']
        event_id = self.get_event_id(call_sid , date)
        
        with open(user_data_file, "r") as json_file:    
            user_data = json.load(json_file)
        user_data_clean = {key.lstrip('- '): value if '-' in key else value for key, value in user_data.items()}

        end_time = self.slot_mapper(start_time)

        # Update data dictionary with calendarId and timezone
        user_data_clean.update({
            "calendarId": calendar_id,
            "contactId": contact_id,
            "startTime": start_time,
            "endTime": end_time,
            "title": "Scheduling Appointment with AI Voicebot",
        })
        conn = http.client.HTTPSConnection("services.leadconnectorhq.com")
            
        keys_to_remove = ['dateSelected', 'timeSelected']
        for key in keys_to_remove:
            user_data_clean.pop(key)
            
        headers = {
                        'Authorization': f"Bearer {access_token}",
                        'Version': "2021-07-28",
                        'Content-Type': "application/json",
                        'Accept': "application/json"
                }
        
        conn.request("PUT", f"/calendars/events/appointments/{event_id}", json.dumps(user_data_clean), headers)
    
        res = conn.getresponse()
        if res.status == 201 or res.status == 200:
            return res.status
        else:
            return None

    def delete_appointment(self , call_sid , date):
            access_token = sessions[call_sid]['access_token']
            event_id = self.get_event_id(call_sid , date)
            
            if event_id is None:
                return message_for_no_appointment_scheduled_deletation
            
            conn = http.client.HTTPSConnection("services.leadconnectorhq.com")
            headers = {
                            'Authorization': f"Bearer {access_token}",
                            'Version': "2021-07-28",
                            'Content-Type': "application/json",
                            'Accept': "application/json"
                        }

            conn.request("DELETE", f"/calendars/events/{event_id}", headers=headers)
            res = conn.getresponse()
            
            if res.status == 201 or res.status == 200:
                return appointment_cancellation_message
            else:
                return message_for_error_encountered_while_appointment_cancellation








