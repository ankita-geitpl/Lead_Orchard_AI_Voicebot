from dependency import *

class GHLCalendarAPI:
    def __init__(self):
        pass

    def parse_time(self , time_str):
        try:
            time_object = datetime.strptime(time_str, '%I:%M %p')
        except ValueError:
            time_object = datetime.strptime(time_str, '%I %p')
        
        return time_object

    def get_date_time(self , user_data , date = None):
        with open(user_data, "r") as json_file:    
            user_data_dict = json.load(json_file)

        print()   
        print("===========================================================")
        print("Data Dict:", user_data_dict)
        print("===========================================================")
        print()
        
        user_data_clean = {key.lstrip('- '): value if '-' in key else value for key, value in user_data_dict.items()}
        
        if date is not None:
            date_selected = date
        else:
            date_selected = user_data_clean["dateSelected"]
        time_selected = user_data_clean["timeSelected"]
        
        time_selected = time_selected.replace('.', '')
        time_selected = time_selected.lower()
        
        time_selected = self.parse_time(time_selected)
        
        time_24h_format = time_selected.strftime('%H:%M:%S')
        start_date = date_selected + " " + time_24h_format
        date_object = datetime.strptime(start_date, '%d-%m-%Y %H:%M:%S')
        
        start_date = int(date_object.timestamp() * 1000)
        end_time_string = '23:59:59'
        end_date = date_selected + " " + end_time_string
        end_date_time = datetime.strptime(end_date, '%d-%m-%Y %H:%M:%S')
        end_date = int(end_date_time.timestamp() * 1000)
        
        return start_date, end_date, time_24h_format, date_selected

    def get_calender(self , location_id , access_token):
        conn = http.client.HTTPSConnection("services.leadconnectorhq.com")

        headers = {
                'Authorization': f"Bearer {access_token}",
                'Version': "2021-07-28",
                'Content-Type': "application/json",
                'Accept': "application/json"
            }

        conn.request("GET", f"/calendars/?locationId={location_id}", headers=headers)

        res = conn.getresponse()
        data = res.read()
        calender_data = data.decode("utf-8")
        response_data = json.loads(calender_data)

        # Extract the ID from the first calendar entry
        if 'calendars' in response_data and len(response_data['calendars']) > 0:
            calendar_id = response_data['calendars'][0]['id']
        else:
            calendar_id = None
        
        return calendar_id

    def fetch_available_slots(self , calender_id , api_key , start_date, end_date, time_24h_format, date_selected):
        try:
            conn = http.client.HTTPSConnection("services.leadconnectorhq.com")

            headers = {
                        'Authorization': f"Bearer {api_key}",
                        'Version': "2021-07-28",
                        'Content-Type': "application/json",
                        'Accept': "application/json"
                    }

            conn.request("GET", f"/calendars/{calender_id}/free-slots?startDate={start_date}&endDate={end_date}", headers=headers)

            res = conn.getresponse()
            data = res.read()
            slots_data = data.decode("utf-8")
            response_data = json.loads(slots_data)
            
            available_slots = response_data[datetime.strptime(date_selected, '%d-%m-%Y').strftime('%Y-%m-%d')]['slots']
            
            if "+05:30" in available_slots[0]:
                time_check = datetime.strptime(date_selected, '%d-%m-%Y').strftime('%Y-%m-%d')+"T"+time_24h_format+"+05:30"
                
                available_slot_times = [datetime.strptime(slot, '%Y-%m-%dT%H:%M:%S+05:30') for slot in available_slots]
                time_check_dt = datetime.strptime(time_check, '%Y-%m-%dT%H:%M:%S+05:30')
                if time_check_dt in available_slot_times:
                        index = available_slot_times.index(time_check_dt)
                        nearest_slots = available_slot_times[index:min(index + 2, len(available_slots))]
                else:
                        sorted_slots = sorted([slot for slot in available_slot_times if slot > time_check_dt], key=lambda x: abs(x - time_check_dt))
                        nearest_slots = sorted_slots[:2]

                nearest_slots_str = [slot.strftime('%Y-%m-%dT%H:%M:%S+05:30') for slot in nearest_slots]
                time_check_str = time_check_dt.strftime('%Y-%m-%dT%H:%M:%S+05:30')
            
            elif "-04:00" in available_slots[0]:
                time_check = datetime.strptime(date_selected, '%d-%m-%Y').strftime('%Y-%m-%d')+"T"+time_24h_format+"-04:00"
                
                available_slot_times = [datetime.strptime(slot, '%Y-%m-%dT%H:%M:%S-04:00') for slot in available_slots]
                time_check_dt = datetime.strptime(time_check, '%Y-%m-%dT%H:%M:%S-04:00')
                if time_check_dt in available_slot_times:
                        index = available_slot_times.index(time_check_dt)
                        nearest_slots = available_slot_times[index:min(index + 2, len(available_slots))]
                else:
                        sorted_slots = sorted([slot for slot in available_slot_times if slot > time_check_dt], key=lambda x: abs(x - time_check_dt))
                        nearest_slots = sorted_slots[:2]

                nearest_slots_str = [slot.strftime('%Y-%m-%dT%H:%M:%S-04:00') for slot in nearest_slots]
                time_check_str = time_check_dt.strftime('%Y-%m-%dT%H:%M:%S-04:00')
            
            
            if time_check_str in nearest_slots_str:
                return time_check , nearest_slots_str , "Time SLot is Available"
            else:
                if len(nearest_slots_str) > 0:
                    return time_check , nearest_slots_str , "Nearest Time SLot is Available"
                else:
                    return "No time slot is available" , [] , "Time SLot is not Available"
        
        except Exception as e:
            print()   
            print("===========================================================")
            print("An error occurred while fetching available slots:", e)   
            print("===========================================================")
            print()
<<<<<<< HEAD
            return "" , [] , "Time SLot is not Available"
=======
            return "", "", "An error occurred while fetching available slots"
>>>>>>> b8f2b3dfc46510064523efdb68166cd617835c47





