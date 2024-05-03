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
    
