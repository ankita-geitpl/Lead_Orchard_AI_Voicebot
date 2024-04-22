from dependency import *

from logic import *

from GHL_schedule_appointment import *
from ghl_contact_create import *
from GHL_task_notes_create import *
from GHL_calender_API import *
from user_ai_consum import *
from Availably_UI import *
from Authtoken import *


call_handler = TwilioCallHandler() 
contact_handler = GHLContactHandler()
task_create = GHLTaskNotesHandler()
appointment_create = GHLAppointmentHandler()
slots_create = GHLSlotsHandler()
user_ai_summary = UserAISummary()
auth_token = AuthTokenGenerator()


@app.route('/voice', methods=['GET' , 'POST'])
def voice():
    """Handle incoming voice call."""
    global end_session_time

    response = VoiceResponse()
    call_status = request.form.get('CallStatus')
    print("=============================")
    print("Response is : ", call_status)
    print("=============================")
    chat_history = [] 
    date_extract = None
    start_session_time = datetime.datetime.now()
    
    if start_session_time > end_session_time:
        sessions.clear()
        current_date = datetime.datetime.now().date()
        end_of_day = datetime.combine(current_date + timedelta(days=1), datetime.min.time()) - timedelta(seconds=1)
        end_session_time = end_of_day.replace(hour=23, minute=59, second=59)
    
    call_sid = request.form.get('CallSid')
    company_number = request.form.get('ForwardedFrom')
    to_num = request.form.get('To')
    customer_number = request.form.get('From')
    print()
    print("===========================================================")
    print("Forwarded From : ",company_number)
    print("===========================================================")
    print()
    
    starttime_token = datetime.datetime.now()
    auth_token.generate_auth_token(starttime_token , company_number)
    
    session_id = None
    user_id , prompt_data , data_pdf_path , location_id , company_id , company_name , access_token = call_handler.get_prompt_file(company_number)
        
    if call_sid not in sessions:
        sessions[call_sid] = {}
    try:
        if session_id is None:
            session_id = str(random.randint(1000, 999999))
            sessions[call_sid]['session'] = session_id
        
        sessions[call_sid]['user_id'] = user_id
        sessions[call_sid]['prompt_data'] = prompt_data
        sessions[call_sid]['data_pdf_path'] = data_pdf_path
        sessions[call_sid]['location_id'] = location_id
        sessions[call_sid]['access_token'] = access_token  
        sessions[call_sid]['date_extract'] = date_extract 
        sessions[call_sid]['chat_history'] = chat_history  
        sessions[call_sid]['company_id'] = company_id
        sessions[call_sid]['company_name'] = company_name 
        
        
        contact_check_id = task_create.contact_id_check(call_sid , customer_number)
        if contact_check_id is not None:
            sessions[call_sid]['contact_id'] = contact_check_id  
        else:
            sessions[call_sid]['contact_id'] = None  
        
        with response.gather(input='speech', enhanced=True, speech_model='phone_call', speech_timeout='2', timeout = '30' , action_on_empty_result = True , action='/handle-voice') as gather:
            gather.say(call_handler.run_assistant(call_sid, ques='Initial Greeting'),language='en-US')
    
    except Exception as e:
        print("Error" , e)
        response.say("There was an error processing your request . Please try again later.",language='en-US')

    return str(response)


@app.route('/handle-voice', methods=['POST'])
def handle_voice_input():
    user_ai_summary.create_summary(request.form.get('CallSid') , request.form.get('CallStatus'))
    response = VoiceResponse()
    speech_result = request.form.get('SpeechResult')
    confidence_score = float(request.form.get('Confidence', 0.0))
    call_sid = request.form.get('CallSid')
    customer_number = request.form.get('From')
    session_id = sessions.get(call_sid, {}).get('session')
    contact_id = sessions.get(call_sid, {}).get('contact_id')
    due_date = None
    
    if session_id is None:
        session_id = str(random.randint(1000, 999999))
        sessions[call_sid] = {'session': session_id}

    date = call_handler.extract_date(speech_result)

    if date is not None:
        sessions[call_sid]['due_date'] = date
        due_date = sessions[call_sid]['due_date']
        
    print()   
    print("===========================================================")
    print("User Response:", speech_result)
    print("===========================================================")
    print()

    print()
    print("===========================================================")
    print("Due Date:", due_date)
    print("===========================================================")
    print()

    if confidence_score > 0.60 and speech_result:
        ai_response = call_handler.run_assistant(call_sid, speech_result)

        print()
        print("===========================================================")
        print("AI Response:", ai_response)
        print("===========================================================")
        print()

        if "I can help you with that".lower() in ai_response.lower():
            handler = "contact-information"
            user_ai_summary.create_summary(call_sid , request.form.get('CallStatus'))
            with response.gather(input='speech', enhanced=True, speech_model='phone_call', speech_timeout='2', timeout = '30' , action_on_empty_result = True , action=handler) as gather:
                gather.say(ai_response, language='en-US')
        
        if "Here is the summary".lower() in ai_response.lower() or "Here's the summary".lower() in ai_response.lower():
            user_contact_info = task_create.get_clean_data(call_sid , ai_response , customer_number)
            
            if contact_id is not None:
                contact_handler.update_contact(call_sid , sessions[call_sid]["contact_id"]  , user_contact_info)
                ai_response = task_create.create_task(call_sid , user_contact_info)
                handler = "/handle-voice" 
                user_ai_summary.create_summary(call_sid , request.form.get('CallStatus'))
                with response.gather(input='speech', enhanced=True, speech_model='phone_call', speech_timeout='2', timeout = '30' , action_on_empty_result = True , action=handler) as gather:
                    gather.say(ai_response, language='en-US')
            
            else:
                contact_handler.contact_id_generate(customer_number , call_sid , user_contact_info)
                contact_id = task_create.contact_id_check(call_sid , customer_number)
                ai_response = task_create.create_task(call_sid , user_contact_info)
                handler = "/handle-voice"
                user_ai_summary.create_summary(call_sid , request.form.get('CallStatus'))
                with response.gather(input='speech', enhanced=True, speech_model='phone_call', speech_timeout='2', timeout = '30' , action_on_empty_result = True , action=handler) as gather:
                    gather.say(ai_response, language='en-US')
                user_ai_summary.create_summary(call_sid , request.form.get('CallStatus'))
        
        else:
            handler = "/handle-voice"
            user_ai_summary.create_summary(call_sid , request.form.get('CallStatus'))
            with response.gather(input='speech', enhanced=True, speech_model='phone_call', speech_timeout='2', timeout = '30' , action_on_empty_result = True , action=handler) as gather:
                gather.say(ai_response, language='en-US')
            user_ai_summary.create_summary(call_sid , request.form.get('CallStatus'))
             
    else:
        ai_response = "No voice input received. Please try again."
        handler = "/handle-voice"
        user_ai_summary.create_summary(call_sid , request.form.get('CallStatus'))
        with response.gather(input='speech', enhanced=True, speech_model='phone_call', speech_timeout='2', timeout = '30' , action_on_empty_result = True , action=handler) as gather:
            gather.say(ai_response, language='en-US')
    
    user_ai_summary.create_summary(request.form.get('CallSid') , request.form.get('CallStatus'))
    return str(response)

@app.route('/contact-information', methods=['GET', 'POST'])
def contact_information():
    user_ai_summary.create_summary(request.form.get('CallSid') , request.form.get('CallStatus'))
    response = VoiceResponse()
    speech_result = request.form.get('SpeechResult')
    confidence_score = float(request.form.get('Confidence', 0.0))
    call_sid = request.form.get('CallSid')
    customer_number = request.form.get('From')
    local_company_number = request.form.get('To')
    session_id = sessions[call_sid]['session']
    contact_id = sessions[call_sid]['contact_id']
    date_extract = None

    if session_id is None:
        session_id = str(random.randint(1000, 999999))
        sessions[call_sid]['session'] = session_id
    
    print()   
    print("===========================================================")
    print("User Response:", speech_result)
    print("===========================================================")
    print()
    
    date = call_handler.extract_date(speech_result)

    if date is not None:
        sessions[call_sid]['date_extract'] = date
        date_extract = sessions[call_sid]['date_extract']
    
    print()   
    print("===========================================================")
    print("Date Extracted", date_extract)
    print("===========================================================")
    print()
    
    handler = "contact-information" 
    
    if confidence_score > 0.60 and speech_result:
        
        ai_response = call_handler.run_assistant(call_sid, speech_result)
        
        print()
        print("===========================================================")
        print("AI Response:", ai_response)
        print("===========================================================")
        print()
        
        handler = "contact-information" 
        
        file_name = "/home/akash_raut/voicebot/pdf_data/user_appoint_data/"+customer_number+"+"+local_company_number+".json"
        sessions[call_sid]['file_name'] = file_name  
        
        today_date = datetime.datetime.now()

        if sessions[call_sid]['date_extract'] < str(today_date):
            ai_response = "Please Provide the Future Date !"
            handler = "/contact-information"

        if "Here is the summary of scheduling details".lower() in ai_response.lower():
            user_contact_info = contact_handler.get_subaccount_info(call_sid , ai_response , customer_number , sessions[call_sid]['date_extract']) 
            
            print()   
            print("===========================================================")
            print("Contact Information:", user_contact_info)
            print("===========================================================")
            print()
            
            with open(file_name, 'w') as json_file:
                json.dump(user_contact_info, json_file, indent=4)
            
            contact_handler.contact_id_generate(customer_number , call_sid , user_contact_info)
            ai_response = "Thanks for your patience! I'm in the process of setting up your appointment. Is it okay for you?"
            handler = "/appointment-confirmation"
            
        
        elif "Here is the summary".lower() in ai_response.lower() or "Here's the summary".lower() in ai_response.lower():
            user_contact_info = task_create.get_clean_data(call_sid , ai_response , customer_number)
            
            if contact_id is not None:
                contact_handler.update_contact(call_sid , sessions[call_sid]["contact_id"]  , user_contact_info)
                ai_response = task_create.create_task(call_sid , user_contact_info)
                handler = "/handle-voice" 
            
            else:
                contact_handler.contact_id_generate(customer_number , call_sid , user_contact_info)
                contact_id = task_create.contact_id_check(call_sid , customer_number)
                ai_response = task_create.create_task(call_sid , user_contact_info)
                handler = "/handle-voice"
        
        user_ai_summary.create_summary(call_sid , request.form.get('CallStatus'))
        with response.gather(input='speech', enhanced=True, speech_model='phone_call', speech_timeout='2', timeout = '30' , action_on_empty_result = True , action=handler) as gather:
            gather.say(ai_response, language='en-US')
        
    else:
        ai_response = "No voice input received. Please try again."
        handler = "/contact-information"
        user_ai_summary.create_summary(call_sid , request.form.get('CallStatus'))
        with response.gather(input='speech', enhanced=True, speech_model='phone_call', speech_timeout='2', timeout = '30' , action_on_empty_result = True , action=handler) as gather:
            gather.say(ai_response, language='en-US')
    
    user_ai_summary.create_summary(request.form.get('CallSid') , request.form.get('CallStatus'))
    return str(response)

@app.route('/appointment-confirmation', methods=['GET' , 'POST'])
def appointment_confirmation(): 
    user_ai_summary.create_summary(request.form.get('CallSid') , request.form.get('CallStatus'))
    response = VoiceResponse()
    call_sid = request.form.get('CallSid')
    queue = Queue()
    
    def background_task():
        result = slots_create.background_task(call_sid)
        queue.put(result)

    threading.Thread(target=background_task).start()
    result = queue.get()
    
    text , get_free_slots , calendars_id , slot = result
    
    sessions[call_sid]['get_free_slots'] = get_free_slots
    sessions[call_sid]['calendars_id'] = calendars_id
    sessions[call_sid]['slot'] = slot

    if "Time SLot is Available".lower() in text.lower():
        status_code = appointment_create.create_appointment(call_sid , calendars_id  , slot)

        if status_code == 201 or status_code == 200:
            print("Appointment scheduled successfully")
            ai_ask = f"Your appointment has been scheduled successfully . Thank you for using our service. , if you want to know more about our service feel free to ask"
            handler = "/handle-voice"
        else:
            print("Failed to schedule appointment")
            ai_ask = "Sorry, I was unable to schedule the appointment. Please try again later."
            handler = "/handle-voice"
        
    elif "Nearest Time SLot is Available".lower() in text.lower():
        ai_ask = "This time slot is not available. Would you like me to schedule appointment which is nearest to your mentioned time slot? Please say Yes or No"        
        
    elif "Time SLot is not Available".lower() in text.lower():
        ai_ask = "It seems that the time slot for this date is not available. Could you please suggest an alternative date and time for the appointment?"
        
    handler = "/appointment-fixed"
    
    # user_ai_summary.summary(call_sid , request.form.get('CallStatus'))
    user_ai_summary.create_summary(call_sid , request.form.get('CallStatus'))
    with response.gather(input='speech', enhanced=True, speech_model='phone_call', speech_timeout='2', timeout = '30' , action_on_empty_result = True , action=handler) as gather:
        gather.say(ai_ask , language='en-US')
    
    user_ai_summary.create_summary(request.form.get('CallSid') , request.form.get('CallStatus'))
    return str(response)

@app.route('/appointment-fixed', methods=['POST'])
def appointment_fixed():
    user_ai_summary.create_summary(request.form.get('CallSid') , request.form.get('CallStatus'))
    response = VoiceResponse()
    speech_result = request.form.get('SpeechResult')
    call_sid = request.form.get('CallSid')
    get_free_slots = sessions[call_sid]['get_free_slots']
    calendars_id = sessions[call_sid]['calendars_id'] 
    slot = sessions[call_sid]['slot']
    date_extract = None
    
    date = call_handler.extract_date_and_time(speech_result)
    time = call_handler.extract_time(speech_result)
    
    print("===================================================")
    print("User Input = ",speech_result)
    print("===================================================")
    print("===================================================")
    print("1 - Date Extracted = ",sessions[call_sid]['date_extract'])
    print("===================================================")
    
    if date is not None:
        sessions[call_sid]['date_extract'] = date
        date_extract = sessions[call_sid]['date_extract']
    
    print()   
    print("===========================================================")
    print("Date Extracted", date_extract)
    print("===========================================================")
    print()
    
    today_date = datetime.datetime.now()

    if sessions[call_sid]['date_extract'] < str(today_date):
        ai_response = "Please Provide the Future Date !"
        handler = "/appointment-fixed"


    if any(word in speech_result.lower() for word in ['yes', 'yeah', 'sure', 'okay', 'ok' , 'yup']): 
        if slot.lower() == "No time slot is available".lower():
            slot = get_free_slots[0]

        status_code = appointment_create.create_appointment(call_sid , calendars_id  , slot)

        if status_code == 201 or status_code == 200:
            print("Contact created successfully")
            ai_ask = "Your appointment has been scheduled successfully. Thank you for using our service. , if you want to know more about our service feel free to ask"
            handler = "/handle-voice"
        else:
            print("Failed to schedule appointment")
            ai_ask = "Sorry, I was unable to schedule the appointment. Please try again later."
            handler = "/handle-voice"
    
    elif any(word in speech_result.lower() for word in ['no', 'nope', 'not', 'cancel']):
        ai_ask = "Thank you for using our service. If you want to know more about our service feel free to ask"
        handler = "/handle-voice"
        
    else:
        ghl_calender = GHLCalendarAPI()
        contact_handler.user_data_changer(sessions[call_sid]['file_name'] , time , sessions[call_sid]['date_extract'])
        print("===================================================")
        print("Date Extracted = ",sessions[call_sid]['date_extract'])
        print("===================================================")
        print("===================================================")
        print("Time Extracted = ",time)
        print("===================================================")
        
        
        start_date, end_date, time_24h_format , date_selected = ghl_calender.get_date_time(sessions[call_sid]['file_name'] , date_extract)
        slot , get_free_slots , text = ghl_calender.fetch_available_slots(calendars_id , sessions[call_sid]['access_token'] , start_date, end_date, time_24h_format, date_selected)
        sessions[call_sid]['get_free_slots'] = get_free_slots
        sessions[call_sid]['calendars_id'] = calendars_id
        sessions[call_sid]['slot'] = slot

        if "Time SLot is Available".lower() in text.lower():
            status_code = appointment_create.create_appointment(call_sid , calendars_id  , slot)

            if status_code == 201 or status_code == 200:
                print("Appointment scheduled successfully")
                ai_ask = "Your appointment has been scheduled successfully. Thank you for using our service. , if you want to know more about our service feel free to ask"
                handler = "/handle-voice"
            else:
                print("Failed to schedule appointment")
                ai_ask = "Sorry, I was unable to schedule the appointment. Please try again later."
                handler = "/handle-voice"
            
        elif "Nearest Time SLot is Available".lower() in text.lower():
            ai_ask = "This time slot is not available. Would you like me to schedule appointment which is nearest to your mentioned time slot? Please say Yes or No"
            handler = "/appointment-fixed" 
            
        elif "Time SLot is not Available".lower() in text.lower():
            ai_ask = "It seems that the time slot for this date is not available. Could you please suggest an alternative date and time for the appointment?"
            handler = "/appointment-fixed"
    
    user_ai_summary.create_summary(call_sid , request.form.get('CallStatus'))
    with response.gather(input='speech', enhanced=True, speech_model='phone_call', speech_timeout='2', timeout = '30' , action_on_empty_result = True , action=handler) as gather:
        gather.say(ai_ask , language='en-US')

    user_ai_summary.create_summary(request.form.get('CallSid') , request.form.get('CallStatus'))
    return str(response)

if __name__ == "__main__":
    app.run(host="localhost", port=3000, debug=False)
