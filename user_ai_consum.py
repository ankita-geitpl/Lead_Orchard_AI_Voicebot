from dependency import *
from logic import sessions

class UserAISummary :
    def __init__(self):
        pass    
    
    def summary(self, call_sid , call_status):
        if call_status == "completed":
            speech_input = """Create notes summarizing a conversation between an AI assistant and a user discussing various aspects of the product, including product inquiries, pricing plans, onboarding processes, scheduling appointments, scheduling tasks, and note-taking. The notes should capture key points discussed in the conversation and present them in bullet points for easy reference."""
            ai_response = self.run_assistant(call_sid , speech_input)
            
            def create_notes(call_sid , ai_response):
                access_token = sessions[call_sid]['access_token']
                contact_id = sessions[call_sid]['contact_id'] 
                
                data_dict_clean = {}
                data_dict_clean.update({
                    "body": ai_response
                })
                
                headers = {
                    'Authorization': f"Bearer {access_token}",
                    'Version': "2021-07-28",
                    'Content-Type': "application/json",
                    'Accept': "application/json"
                }

                conn = http.client.HTTPSConnection("services.leadconnectorhq.com")

                conn.request("POST", f"/contacts/{contact_id}/notes", json.dumps(data_dict_clean), headers)

                res = conn.getresponse()
                if res.status == 201 or res.status == 200:
                    print("Note created successfully!")
                else:  
                    print("Note creation failed!")
            
            create_notes(call_sid , ai_response)