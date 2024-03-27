import requests

def fetch_available_slots():
    url = "https://rest.gohighlevel.com/v1/appointments/slots"
    
    try:
        fetch_status = "inprogress"
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            # Assuming the response contains a list of available slots
            available_slots = data.get('slots', [])
            # Extract only the time information from the available slots
            available_times = [slot['time'] for slot in available_slots]
            fetch_status = "completed"
            return available_times
        else:
            print("Failed to fetch available slots. Status code:", response.status_code)
            return []
    except Exception as e:
        print("An error occurred while fetching available slots:", e)
        return []

# Example usage:
available_slots = fetch_available_slots()
print("Available slots:", available_slots)
