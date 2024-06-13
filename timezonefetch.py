from dependency import *

class TimezoneFetch:
    def __init__(self):
        pass

    def time_zone_fetch(self , customer_number):
        try:
            # Parse the phone number
            parsed_number = phonenumbers.parse(customer_number, None)

            if not phonenumbers.is_valid_number(parsed_number):
                print("Invalid phone number.")
                return None

            # Get the timezone ID based on the phone number
            timezone_id = timezone.time_zones_for_number(parsed_number)

            return timezone_id[0] if timezone_id else None

        except phonenumbers.phonenumberutil.NumberParseException as e:
            print("Error parsing phone number:", e)
            return None

    def convert_timezone(self , date , timezone_1 , timezone_2):
        datetime_ny = datetime.strptime(date, '%Y-%m-%dT%H:%M:%S')
        # Set the timezone to America/New_York
        datetime_ny = pytz.timezone(timezone_1).localize(datetime_ny)
        # Convert the datetime to IST (Indian Standard Time)
        datetime_ist = datetime_ny.astimezone(pytz.timezone(timezone_2))
        # Extract timezone offset for IST timezone
        offset_ist = datetime_ist.utcoffset()
        # Format offset as string
        offset_ist_str = "{:0=+3}:{:0=2}".format(offset_ist.days * 24 + offset_ist.seconds // 3600, offset_ist.seconds % 3600 // 60)
        return datetime_ist.strftime("%Y-%m-%dT%H:%M:%S") + offset_ist_str
    
    def date_and_time(self , date_time):
        date_time_obj = datetime.fromisoformat(date_time)
        date = date_time_obj.date()
        time = date_time_obj.time()
        time_obj = datetime.strptime(str(time), '%H:%M:%S') 
        time_12hr_format = time_obj.strftime('%I:%M %p')
        return date , time_12hr_format

    def find_start_end_time(self , access_token , timezone_1 , timezone_2):
        conn = http.client.HTTPSConnection("services.leadconnectorhq.com")
        # Set the headers
        headers = {
            'Authorization': f"Bearer {access_token}",
            'Version': "2021-07-28",
            'Content-Type': "application/json",
            'Accept': "application/json"
        }

        conn.request("GET", "/calendars/vPtjefpTMc6xnLlse5jr", headers=headers)

        res = conn.getresponse()
        data = res.read()

        # Load JSON data
        data = json.loads(data.decode('utf-8'))


        # Get the current date
        current_date = datetime.now()
        current_day_of_week = current_date.weekday() + 1  # Python's weekday() starts from 0 (Monday), JSON daysOfTheWeek starts from 1 (Monday)

        # Adjust date if it's Saturday (6) or Sunday (7)
        if current_day_of_week == 6:  # Saturday
            current_date += timedelta(days=2)  # Move to Monday
        elif current_day_of_week == 7:  # Sunday
            current_date += timedelta(days=1)  # Move to Monday

        # Recalculate the day of the week after adjustment
        day_of_week = current_date.weekday() + 1  # Python's weekday() starts from 0 (Monday), JSON daysOfTheWeek starts from 1 (Monday)

        # Extract open hours
        open_hours = data['calendar']['openHours']


        # Find and format start and end times for the current date
        for day in open_hours:
            if day_of_week in day['daysOfTheWeek']:
                hours = day['hours'][0]
                open_hour = hours['openHour']
                open_minute = hours['openMinute']
                close_hour = hours['closeHour']
                close_minute = hours['closeMinute']
                
                # Include current_date in start_time and end_time
                # start_time = current_date.replace(hour=open_hour, minute=open_minute, second=0)
                # end_time = current_date.replace(hour=close_hour, minute=close_minute, second=0)
                start_time = current_date.replace(hour=open_hour, minute=open_minute, second=0).strftime('%Y-%m-%dT%H:%M:%S')
                end_time = current_date.replace(hour=close_hour, minute=close_minute, second=0).strftime('%Y-%m-%dT%H:%M:%S')

        start_date_time = self.convert_timezone(start_time , timezone_1 , timezone_2)
        end_date_time = self.convert_timezone(end_time , timezone_1 , timezone_2)


        print("=========================================================================1")
        print(start_date_time)
        print("=========================================================================1")
        print("=========================================================================1")
        print(end_date_time)
        print("=========================================================================1")
        print("=========================================================================1")
        
        # offset_start_time_ist_str = datetime.strptime(offset_start_time_ist_str, '%Y-%m-%dT%H:%M:%S%z').strftime('%Y-%m-%dT%H:%M:%S')
        # offset_end_time_ist_str = datetime.strptime(offset_end_time_ist_str, '%Y-%m-%dT%H:%M:%S%z').strftime('%Y-%m-%dT%H:%M:%S')

        _ , start_time = self.date_and_time(start_date_time)
        _ , end_time = self.date_and_time(end_date_time)

        return start_time , end_time
    
