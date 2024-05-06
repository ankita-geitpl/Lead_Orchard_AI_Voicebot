#----------------------------------------------------IMPORT LIBRARIES--------------------------------------------------------------------------------------------------------------------------------------------------------------------


from dependency import *

from logic import *

from GHL_schedule_appointment import *
from ghl_contact_create import *
from GHL_task_notes_create import *
from GHL_calender_API import *
from user_ai_consum import *
from Availably_UI import *
from Authtoken import *
from timezonefetch import *
from utters import *


#-----------------------------------------------------INITIALIZATION--------------------------------------------------------------------------------------------------------------------------------------------------


call_handler = TwilioCallHandler() 
contact_handler = GHLContactHandler()
task_create = GHLTaskNotesHandler()
appointment_create = GHLAppointmentHandler()
slots_create = GHLSlotsHandler()
user_ai_summary = UserAISummary()
auth_token = AuthTokenGenerator()
timezone_fetch = TimezoneFetch()


#-----------------------------------------------------VOICE API--------------------------------------------------------------------------------------------------------------------------------------------------

@app.route('/voice', methods=['GET' , 'POST'])
def voice():
    """Handle incoming voice call."""
    global end_session_time

    response = VoiceResponse()
    chat_history = [] 
    date_extract = None
    start_session_time = datetime.now()
    
    if start_session_time > end_session_time:
        sessions.clear()
        current_date = datetime.now().date()
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
    
    starttime_token = datetime.now()
    auth_token.generate_auth_token(starttime_token , to_num)
    
    session_id = None
    user_id , prompt_data , data_pdf_path , location_id , company_id , company_name , access_token , gpt_model_id = call_handler.get_prompt_file(to_num)
        
    timezone = timezone_fetch.time_zone_fetch(customer_number)

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
        sessions[call_sid]['timezone'] = timezone  
        sessions[call_sid]['gpt_model_id'] = gpt_model_id
        
        contact_check_id = task_create.contact_id_check(call_sid , customer_number)
        if contact_check_id is not None:
            sessions[call_sid]['contact_id'] = contact_check_id  
        else:
            sessions[call_sid]['contact_id'] = None  
        
        with response.gather(input='speech', enhanced=True, speech_model='phone_call', speech_timeout='2', timeout = '30' , action_on_empty_result = True , action='/handle-voice') as gather:
            gather.say(call_handler.run_assistant(call_sid, ques='Initial Greeting'),language='en-US')
    
    except Exception as e:
        response.say(voice_api_error_message,language='en-US')

    return str(response)


#---------------------------------------------------HANDLE VOICE API-------------------------------------------------------------------------------------------------------------------------------------------------------------


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
    
    if session_id is None:
        session_id = str(random.randint(1000, 999999))
        sessions[call_sid] = {'session': session_id}
        
    print()   
    print("===========================================================")
    print("User Response:", speech_result)
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
            handler = "/contact-information"

        elif "I'm here to accommodate your schedule".lower() in ai_response.lower():
            handler = "/update-information"
        
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

        elif ("cancel".lower() in ai_response.lower() or "cancelling".lower() in ai_response.lower()) and "appointment".lower() in ai_response.lower():
            handler = "/cancel-appointment"
        
        else:
            handler = "/handle-voice"
            
        with response.gather(input='speech', enhanced=True, speech_model='phone_call', speech_timeout='2', timeout = '30' , action_on_empty_result = True , action=handler) as gather:
            gather.say(ai_response, language='en-US')
             
    else:
        ai_response = no_voice_input_message
        handler = "/handle-voice"
    
    with response.gather(input='speech', enhanced=True, speech_model='phone_call', speech_timeout='2', timeout = '30' , action_on_empty_result = True , action=handler) as gather:
        gather.say(ai_response, language='en-US')
    
    user_ai_summary.create_summary(request.form.get('CallSid') , request.form.get('CallStatus'))
    return str(response)


#--------------------------------------------------CREATE APPOINTMENT API---------------------------------------------------------------------------------------------------------------------------------------------------------


@app.route('/contact-information', methods=['GET', 'POST'])
def contact_information():
    user_ai_summary.create_summary(request.form.get('CallSid') , request.form.get('CallStatus'))
    response = VoiceResponse()
    speech_result = request.form.get('SpeechResult')
    confidence_score = float(request.form.get('Confidence', 0.0))
    call_sid = request.form.get('CallSid')
    customer_number = request.form.get('From')
    company_number = request.form.get('ForwardedFrom')
    session_id = sessions[call_sid]['session']
    contact_id = sessions[call_sid]['contact_id']

    if session_id is None:
        session_id = str(random.randint(1000, 999999))
        sessions[call_sid]['session'] = session_id
    
    print()   
    print("===========================================================")
    print("User Response:", speech_result)
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
        user_data_sys_path = constants.USER_DATA_SYS_PATH
        file_name = user_data_sys_path+customer_number+"+"+company_number+".json"
        sessions[call_sid]['file_name'] = file_name  

        if "Here is the summary of scheduling details".lower() in ai_response.lower():
            user_contact_info = contact_handler.get_subaccount_info_create(call_sid , ai_response , customer_number) 
            
            print()   
            print("===========================================================")
            print("Contact Information:", user_contact_info)
            print("===========================================================")
            print()
            
            with open(file_name, 'w') as json_file:
                json.dump(user_contact_info, json_file, indent=4)
            
            contact_handler.contact_id_generate(customer_number , call_sid , user_contact_info)
            ai_response = waiting_message_for_appointment_creation
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
        
        elif ("cancel".lower() in ai_response.lower() or "cancelling".lower() in ai_response.lower()) and "appointment".lower() in ai_response.lower():
            handler = "/cancel-appointment"
            
        with response.gather(input='speech', enhanced=True, speech_model='phone_call', speech_timeout='2', timeout = '30' , action_on_empty_result = True , action=handler) as gather:
            gather.say(ai_response, language='en-US')
        
    else:
        ai_response = no_voice_input_message
        handler = "/contact-information"
    
    with response.gather(input='speech', enhanced=True, speech_model='phone_call', speech_timeout='2', timeout = '30' , action_on_empty_result = True , action=handler) as gather:
        gather.say(ai_response, language='en-US')
    
    user_ai_summary.create_summary(request.form.get('CallSid') , request.form.get('CallStatus'))
    return str(response)


# ----------------------------------------------CREATE APPOINTMENT API CONT.--------------------------------------------------------------------------------------------------------------------------------------------------------------------


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
    
    text , get_free_slots , calendars_id , slot , timezone_user = result
    
    sessions[call_sid]['get_free_slots'] = get_free_slots
    sessions[call_sid]['calendars_id'] = calendars_id
    sessions[call_sid]['slot'] = slot
    sessions[call_sid]['text'] = None
    sessions[call_sid]['timezone_user'] = timezone_user

    if "Time SLot is Available".lower() == text.lower():
        status_code = appointment_create.create_appointment(call_sid , calendars_id  , slot)

        if status_code == 201 or status_code == 200:
            slot = datetime.strptime(slot, '%Y-%m-%dT%H:%M:%S%z').strftime('%Y-%m-%dT%H:%M:%S')
            date = timezone_fetch.convert_timezone(slot , timezone_user , sessions[call_sid]['timezone'])
            date_offer , time_offer = timezone_fetch.date_and_time(date)
            print(f"Appointment scheduled successfully")
            ai_ask = f"Your appointment has been scheduled successfully for {date_offer} at {time_offer}. Thank you for using our service. , if you want to know more about our service feel free to ask"
            handler = "/handle-voice"
        else:
            print("Failed to reschedule appointment")
            ai_ask = message_for_failed_appointment
            handler = "/handle-voice"
        
    elif "Nearest Time SLot is Available".lower() == text.lower():
        sessions[call_sid]['text'] = text
        ai_ask = message_for_nearest_slots_available        
        handler = "/appointment-fixed"

    elif "Time SLot is not Available".lower() == text.lower():
        ai_ask = message_for_no_slots_available
        handler = "/appointment-fixed"

    with response.gather(input='speech', enhanced=True, speech_model='phone_call', speech_timeout='2', timeout = '30' , action_on_empty_result = True , action=handler) as gather:
        gather.say(ai_ask , language='en-US')
    
    user_ai_summary.create_summary(request.form.get('CallSid') , request.form.get('CallStatus'))
    return str(response)


#---------------------------------------------------CREATE APPOINTMENT API CONT.---------------------------------------------------------------------------------------------------------------------------------------------------------


@app.route('/appointment-fixed', methods=['POST'])
def appointment_fixed():
    user_ai_summary.create_summary(request.form.get('CallSid') , request.form.get('CallStatus'))
    response = VoiceResponse()
    speech_result = request.form.get('SpeechResult')
    call_sid = request.form.get('CallSid')
    get_free_slots = sessions[call_sid]['get_free_slots']
    calendars_id = sessions[call_sid]['calendars_id'] 
    slot = sessions[call_sid]['slot']
    text = sessions[call_sid]['text']
    
    print("===================================================")
    print("User Input = ",speech_result)
    print("===================================================")

    if any(word in speech_result.lower() for word in ['yes', 'yeah', 'sure', 'okay', 'ok' , 'yup']): 
        if text.lower() == "Nearest time slot is available".lower():
            slot = get_free_slots[0]

        status_code = appointment_create.create_appointment(call_sid , calendars_id  , slot)

        if status_code == 201 or status_code == 200:
            slot = datetime.strptime(slot, '%Y-%m-%dT%H:%M:%S%z').strftime('%Y-%m-%dT%H:%M:%S')
            date = timezone_fetch.convert_timezone(slot , sessions[call_sid]['timezone_user'] , sessions[call_sid]['timezone'])
            date_offer , time_offer = timezone_fetch.date_and_time(date)
            print(f"Appointment scheduled successfully")
            ai_ask = f"Your appointment has been scheduled successfully for {date_offer} at {time_offer}. Thank you for using our service. , if you want to know more about our service feel free to ask"
            handler = "/handle-voice"
        else:
            print("Failed to schedule appointment")
            ai_ask = message_for_failed_appointment
            handler = "/handle-voice"
    
    elif any(word in speech_result.lower() for word in ['no', 'nope', 'not', 'cancel']):
        ai_ask = "Thank you for using our service. If you want to know more about our service feel free to ask"
        handler = "/handle-voice"
        
    else:
        speech_result = "Goto **SCRIPT FOR GENERATING DATE AND TIME:**"+""+speech_result
        ai_response = call_handler.run_assistant(call_sid, speech_result)
        date , time = contact_handler.get_subaccount_info_2(ai_response) 
        sessions[call_sid]['date_extract'] = date
        ghl_calender = GHLCalendarAPI()
        contact_handler.user_data_changer(sessions[call_sid]['file_name'] , time , sessions[call_sid]['date_extract'])
        
        
        start_date, end_date, time_24h_format , date_selected = ghl_calender.get_date_time(sessions[call_sid]['file_name'])
        slot , get_free_slots , text , timezone_user = ghl_calender.fetch_available_slots(calendars_id , sessions[call_sid]['access_token'] , start_date, end_date, time_24h_format, date_selected , sessions[call_sid]['timezone'])
        sessions[call_sid]['get_free_slots'] = get_free_slots
        sessions[call_sid]['calendars_id'] = calendars_id
        sessions[call_sid]['slot'] = slot
        sessions[call_sid]['text'] = None
        sessions[call_sid]['timezone_user'] = timezone_user
        

        if "Time SLot is Available".lower() == text.lower():
            status_code = appointment_create.create_appointment(call_sid , calendars_id  , slot)

            if status_code == 201 or status_code == 200:
                slot = datetime.strptime(slot, '%Y-%m-%dT%H:%M:%S%z').strftime('%Y-%m-%dT%H:%M:%S')
                date = timezone_fetch.convert_timezone(slot , timezone_user , sessions[call_sid]['timezone'])
                date_offer , time_offer = timezone_fetch.date_and_time(date)
                print(f"Appointment scheduled successfully")
                ai_ask = f"Your appointment has been scheduled successfully for {date_offer} at {time_offer}. Thank you for using our service. , if you want to know more about our service feel free to ask"
                handler = "/handle-voice"
            else:
                print("Failed to schedule appointment")
                ai_ask = message_for_failed_appointment
                handler = "/handle-voice"
            
        elif "Nearest Time SLot is Available".lower() == text.lower():
            sessions[call_sid]['text'] = text
            ai_ask = message_for_nearest_slots_available
            handler = "/appointment-fixed" 
            
        elif "Time SLot is not Available".lower() == text.lower():
            ai_ask = message_for_no_slots_available
            handler = "/appointment-fixed"
    
    with response.gather(input='speech', enhanced=True, speech_model='phone_call', speech_timeout='2', timeout = '30' , action_on_empty_result = True , action=handler) as gather:
        gather.say(ai_ask , language='en-US')

    user_ai_summary.create_summary(request.form.get('CallSid') , request.form.get('CallStatus'))
    return str(response)


#---------------------------------------------------DELETE APPOINTMENT API----------------------------------------------------------------------------------------------------------------------------------------------------------------


@app.route('/cancel-appointment', methods=['GET' , 'POST'])
def cancel_appointment():
    user_ai_summary.create_summary(request.form.get('CallSid') , request.form.get('CallStatus'))
    response = VoiceResponse()
    call_sid = request.form.get('CallSid')
    speech_result = request.form.get('SpeechResult')

    try:
        speech_result = "Goto **SCRIPT FOR DELETE SCHEDULING SUMMARISATION:** to provide the Caller Details Delete Summarization with a title ’Here is your detailed delete Imformation You Provided’"+""+speech_result
        ai_response = call_handler.run_assistant(call_sid, speech_result)
        date , _ = contact_handler.get_subaccount_info_2(ai_response) 
        sessions[call_sid]['date_extract'] = date
        
        ai_response = appointment_create.delete_appointment(call_sid , sessions[call_sid]['date_extract'])
        handler = "/handle-voice"
        with response.gather(input='speech', enhanced=True, speech_model='phone_call', speech_timeout='2', timeout = '30' , action_on_empty_result = True , action=handler) as gather:
            gather.say(ai_response , language='en-US')
    except:
        ai_response = no_voice_input_message
        handler = "/handle-voice"
        with response.gather(input='speech', enhanced=True, speech_model='phone_call', speech_timeout='2', timeout = '30' , action_on_empty_result = True , action=handler) as gather:
            gather.say(ai_response , language='en-US')
    
    user_ai_summary.create_summary(request.form.get('CallSid') , request.form.get('CallStatus'))
    return str(response)


#---------------------------------------------------UPDATE APPOINTMENT API----------------------------------------------------------------------------------------------------------------------------------------------------------------


@app.route('/update-information', methods=['GET' , 'POST'])
def update_information():
    user_ai_summary.create_summary(request.form.get('CallSid') , request.form.get('CallStatus'))
    response = VoiceResponse()
    speech_result = request.form.get('SpeechResult')
    confidence_score = float(request.form.get('Confidence', 0.0))
    call_sid = request.form.get('CallSid')
    customer_number = request.form.get('From')
    company_number = request.form.get('ForwardedFrom')
    session_id = sessions[call_sid]['session']
    contact_id = sessions[call_sid]['contact_id']

    if session_id is None:
        session_id = str(random.randint(1000, 999999))
        sessions[call_sid]['session'] = session_id
    
    print()   
    print("===========================================================")
    print("User Response:", speech_result)
    print("===========================================================")
    print()
    
    handler = "update-information" 
    
    if confidence_score > 0.60 and speech_result:
        
        ai_response = call_handler.run_assistant(call_sid, speech_result)
        
        print()
        print("===========================================================")
        print("AI Response:", ai_response)
        print("===========================================================")
        print()
        
        handler = "update-information" 
        
        user_data_sys_path = constants.USER_DATA_SYS_PATH
        file_name = user_data_sys_path+customer_number+"+"+company_number+".json"
        sessions[call_sid]['file_name'] = file_name  

        if "Here is the update summary of scheduling details".lower() in ai_response.lower():
            user_contact_info , previous_date = contact_handler.get_subaccount_info_update(call_sid , ai_response , customer_number) 
            sessions[call_sid]['date_extract'] = previous_date
            
            with open(file_name, 'w') as json_file:
                json.dump(user_contact_info, json_file, indent=4)
            
            contact_handler.contact_id_generate(customer_number , call_sid , user_contact_info)
            ai_response = waiting_message_for_appointment_updation
            handler = "/appointment-confirmation-two"
            
        
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
        
        elif ("cancel".lower() in ai_response.lower() or "cancelling".lower() in ai_response.lower()) and "appointment".lower() in ai_response.lower():
            handler = "/cancel-appointment"

        with response.gather(input='speech', enhanced=True, speech_model='phone_call', speech_timeout='2', timeout = '30' , action_on_empty_result = True , action=handler) as gather:
            gather.say(ai_response, language='en-US')
        
    else:
        ai_response = no_voice_input_message
        handler = "/update-information"
        with response.gather(input='speech', enhanced=True, speech_model='phone_call', speech_timeout='2', timeout = '30' , action_on_empty_result = True , action=handler) as gather:
            gather.say(ai_response, language='en-US')
    
    user_ai_summary.create_summary(request.form.get('CallSid') , request.form.get('CallStatus'))
    return str(response)


#---------------------------------------------------UPDATE APPOINTMENT API CONT.---------------------------------------------------------------------------------------------------------------------------------------------------------


@app.route('/appointment-confirmation-two', methods=['GET' , 'POST'])
def appointment_confirmation_two(): 
    user_ai_summary.create_summary(request.form.get('CallSid') , request.form.get('CallStatus'))
    response = VoiceResponse()
    call_sid = request.form.get('CallSid')
    queue = Queue()
    
    def background_task():
        result = slots_create.background_task(call_sid)
        queue.put(result)

    threading.Thread(target=background_task).start()
    result = queue.get()
    
    text , get_free_slots , calendars_id , slot , timezone_user = result
    
    sessions[call_sid]['get_free_slots'] = get_free_slots
    sessions[call_sid]['calendars_id'] = calendars_id
    sessions[call_sid]['slot'] = slot
    sessions[call_sid]['text'] = None
    sessions[call_sid]['timezone_user'] = timezone_user

    if "Time SLot is Available".lower() == text.lower():
        status_code = appointment_create.update_appointment(call_sid , calendars_id  , slot)
        
        if status_code == 201 or status_code == 200:
            slot = datetime.strptime(slot, '%Y-%m-%dT%H:%M:%S%z').strftime('%Y-%m-%dT%H:%M:%S')
            date = timezone_fetch.convert_timezone(slot , timezone_user , sessions[call_sid]['timezone'])
            date_offer , time_offer = timezone_fetch.date_and_time(date)
            print(f"Appointment rescheduled successfully")
            ai_ask = f"Your appointment has been rescheduled successfully for {date_offer} at {time_offer}. Thank you for using our service. , if you want to know more about our service feel free to ask"
            handler = "/handle-voice"
        else:
            print("Failed to reschedule appointment")
            ai_ask = message_for_failed_appointment
            handler = "/handle-voice"
        
    elif "Nearest Time SLot is Available".lower() == text.lower():
        sessions[call_sid]['text'] = text
        ai_ask = message_for_nearest_slots_available_for_updation        
        handler = "/appointment-fixed-two"

    elif "Time SLot is not Available".lower() == text.lower():
        ai_ask = message_for_no_slots_available
        handler = "/appointment-fixed-two"

    with response.gather(input='speech', enhanced=True, speech_model='phone_call', speech_timeout='2', timeout = '30' , action_on_empty_result = True , action=handler) as gather:
        gather.say(ai_ask , language='en-US')
    
    user_ai_summary.create_summary(request.form.get('CallSid') , request.form.get('CallStatus'))
    return str(response)


#---------------------------------------------------UPDATE APPOINTMENT API CONT.---------------------------------------------------------------------------------------------------------------------------------------------------------


@app.route('/appointment-fixed-two', methods=['POST'])
def appointment_fixed_two():
    user_ai_summary.create_summary(request.form.get('CallSid') , request.form.get('CallStatus'))
    response = VoiceResponse()
    speech_result = request.form.get('SpeechResult')
    call_sid = request.form.get('CallSid')
    get_free_slots = sessions[call_sid]['get_free_slots']
    calendars_id = sessions[call_sid]['calendars_id'] 
    slot = sessions[call_sid]['slot']
    text = sessions[call_sid]['text']


    print("===================================================")
    print("User Input = ",speech_result)
    print("===================================================")

    if any(word in speech_result.lower() for word in ['yes', 'yeah', 'sure', 'okay', 'ok' , 'yup']): 
        if text.lower() == "No time slot is available".lower():
            slot = get_free_slots[0]

        status_code = appointment_create.update_appointment(call_sid , calendars_id  , slot)

        if status_code == 201 or status_code == 200:
            slot = datetime.strptime(slot, '%Y-%m-%dT%H:%M:%S%z').strftime('%Y-%m-%dT%H:%M:%S')
            date = timezone_fetch.convert_timezone(slot , sessions[call_sid]['timezone_user'] , sessions[call_sid]['timezone'])
            date_offer , time_offer = timezone_fetch.date_and_time(date)
            print(f"Appointment scheduled successfully")
            ai_ask = f"Your appointment has been scheduled successfully for {date_offer} at {time_offer}. Thank you for using our service. , if you want to know more about our service feel free to ask"
            handler = "/handle-voice"
        else:
            print("Failed to schedule appointment")
            ai_ask = "Sorry, I was unable to schedule the appointment. Please try again later."
            handler = "/handle-voice"
    
    elif any(word in speech_result.lower() for word in ['no', 'nope', 'not', 'cancel']):
        ai_ask = "Thank you for using our service. If you want to know more about our service feel free to ask"
        handler = "/handle-voice"
        
    else:
        speech_result = "Goto **SCRIPT FOR GENERATING DATE AND TIME:**"+""+speech_result
        ai_response = call_handler.run_assistant(call_sid, speech_result)
        date , time = contact_handler.get_subaccount_info_2(ai_response) 
        sessions[call_sid]['date_update'] = date
        ghl_calender = GHLCalendarAPI()
        contact_handler.user_data_changer(sessions[call_sid]['file_name'] , time , sessions[call_sid]['date_update'])
        
        
        start_date, end_date, time_24h_format , date_selected = ghl_calender.get_date_time(sessions[call_sid]['file_name'])
        slot , get_free_slots , text , timezone_user = ghl_calender.fetch_available_slots(calendars_id , sessions[call_sid]['access_token'] , start_date, end_date, time_24h_format, date_selected , sessions[call_sid]['timezone'])
        sessions[call_sid]['get_free_slots'] = get_free_slots
        sessions[call_sid]['calendars_id'] = calendars_id
        sessions[call_sid]['slot'] = slot
        sessions[call_sid]['text'] = None
        sessions[call_sid]['timezone_user'] = timezone_user

        if "Time SLot is Available".lower() == text.lower():
            status_code = appointment_create.update_appointment(call_sid , calendars_id  , slot)

            if status_code == 201 or status_code == 200:
                slot = datetime.strptime(slot, '%Y-%m-%dT%H:%M:%S%z').strftime('%Y-%m-%dT%H:%M:%S')
                date = timezone_fetch.convert_timezone(slot , timezone_user , sessions[call_sid]['timezone'])
                date_offer , time_offer = timezone_fetch.date_and_time(date)
                print(f"Appointment rescheduled successfully")
                ai_ask = f"Your appointment has been rescheduled successfully for {date_offer} at {time_offer}. Thank you for using our service. , if you want to know more about our service feel free to ask"
                handler = "/handle-voice"
            else:
                print("Failed to reschedule appointment")
                ai_ask = "Sorry, I was unable to schedule the appointment. Please try again later."
                handler = "/handle-voice"
            
        elif "Nearest Time SLot is Available".lower() == text.lower():
            sessions[call_sid]['text'] = text
            ai_ask = message_for_nearest_slots_available_for_updation
            handler = "/appointment-fixed-two" 
            
        elif "Time SLot is not Available".lower() == text.lower():
            ai_ask = message_for_no_slots_available
            handler = "/appointment-fixed-two"
    
    with response.gather(input='speech', enhanced=True, speech_model='phone_call', speech_timeout='2', timeout = '30' , action_on_empty_result = True , action=handler) as gather:
        gather.say(ai_ask , language='en-US')

    user_ai_summary.create_summary(request.form.get('CallSid') , request.form.get('CallStatus'))
    return str(response)

if __name__ == "__main__":
    app.run(host="localhost", port=3000, debug=False)