from celery import Celery
import requests
app = Celery('tasks', broker='redis://localhost:6379/0')
class GetFreeSlotAPI:
    def __init__(self):
        # Initialize API endpoint and other necessary parameters
        self.endpoint = "your_get_free_slot_api_endpoint"
    def get_free_slots(self, preferred_time):
        # Call the Get Free Slot API with preferred time
        response = requests.get(self.endpoint, params={"preferred_time": preferred_time})
        if response.status_code == 200:
            return response.json()["free_slots"]
        else:
            return []