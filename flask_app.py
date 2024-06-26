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
# from finetunning import *


#-----------------------------------------------------INITIALIZATION--------------------------------------------------------------------------------------------------------------------------------------------------


call_handler = TwilioCallHandler() 
contact_handler = GHLContactHandler()
task_create = GHLTaskNotesHandler()
appointment_create = GHLAppointmentHandler()
slots_create = GHLSlotsHandler()
user_ai_summary = UserAISummary()
auth_token = AuthTokenGenerator()
timezone_fetch = TimezoneFetch()
# finetune_updater = FineTunedModelUpdater()



#-------------------------------------------------ERROR HANDLING API------------------------------------------------------------------------------------------------------------------


@app.route('/error-message', methods=['GET' , 'POST'])
def error_message():
    response = VoiceResponse()
    response.say(voice_app_error_message,language='en-US')
    return str(response)


#-----------------------------------------------------VOICE API--------------------------------------------------------------------------------------------------------------------------------------------------

@app.route('/voice', methods=['GET' , 'POST'])
def voice():
    """Handle incoming voice call."""
    print()
    print("===========================================================")
    print("VOICE HANDLER")
    print("===========================================================")
    print()
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
    customer_number = request.form.get('From')
    print()
    print("===========================================================")
    print("Forwarded From : ",company_number)
    print("===========================================================")
    print()
    
    starttime_token = datetime.now()
    auth_token.generate_auth_token(starttime_token , company_number)
    
    session_id = None
    user_id , prompt_data , data_pdf_path , location_id , company_id , company_name , access_token , gpt_model_id = call_handler.get_prompt_file(company_number)
        
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
        sessions[call_sid]['customer_number'] = customer_number
        sessions[call_sid]['company_number'] = company_number
        
        contact_check_id = task_create.contact_id_check(call_sid , customer_number)
        if contact_check_id is not None:
            sessions[call_sid]['contact_id'] = contact_check_id  
        else:
            sessions[call_sid]['contact_id'] = None  
        
        with response.gather(input='speech dtmf', enhanced=True, speech_model='phone_call', speech_timeout='2', timeout = '50' , action_on_empty_result = True , action='/handle-voice') as gather:
            gather.say(call_handler.run_assistant(call_sid, ques='Initial Greeting'),language='en-US')
    
    except Exception as e:
        response.say(voice_api_error_message,language='en-US')

    return str(response)


#---------------------------------------------------HANDLE VOICE API-------------------------------------------------------------------------------------------------------------------------------------------------------------


@app.route('/handle-voice', methods=['POST'])
def handle_voice_input():
    print()
    print("===========================================================")
    print("HANDLE-VOICE HANDLER")
    print("===========================================================")
    print()
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

        elif "Here is the summary of scheduling details".lower() in ai_response.lower():
            user_data_sys_path = constants.USER_DATA_SYS_PATH
            file_name = user_data_sys_path+customer_number+"+"+company_number+".json"
            sessions[call_sid]['file_name'] = file_name  
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
        
        elif "Here is the update summary of scheduling details".lower() in ai_response.lower():
            user_data_sys_path = constants.USER_DATA_SYS_PATH
            file_name = user_data_sys_path+customer_number+"+"+company_number+".json"
            sessions[call_sid]['file_name'] = file_name  
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
        
        else:
            handler = "/handle-voice"
            
        with response.gather(input='speech dtmf', enhanced=True, speech_model='phone_call', speech_timeout='2', timeout = '50' , action_on_empty_result = True , action=handler) as gather:
            gather.say(ai_response, language='en-US')
             
    else:
        ai_response = no_voice_input_message
        handler = "/handle-voice"
    
    with response.gather(input='speech dtmf', enhanced=True, speech_model='phone_call', speech_timeout='2', timeout = '50' , action_on_empty_result = True , action=handler) as gather:
        gather.say(ai_response, language='en-US')
    
    user_ai_summary.create_summary(request.form.get('CallSid') , request.form.get('CallStatus'))
    return str(response)


#--------------------------------------------------CREATE APPOINTMENT API---------------------------------------------------------------------------------------------------------------------------------------------------------


@app.route('/contact-information', methods=['GET', 'POST'])

def contact_information():
    print()
    print("===========================================================")
    print("CONTACT HANDLER - 1")
    print("===========================================================")
    print()
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
            
        elif "Here is the update summary of scheduling details".lower() in ai_response.lower():
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
            
        with response.gather(input='speech', enhanced=True, speech_model='phone_call', speech_timeout='2', timeout = '50' , action_on_empty_result = True , action=handler) as gather:
            gather.say(ai_response, language='en-US')
        
    else:
        ai_response = no_voice_input_message
        handler = "/contact-information"
    
    with response.gather(input='speech', enhanced=True, speech_model='phone_call', speech_timeout='2', timeout = '50' , action_on_empty_result = True , action=handler) as gather:
        gather.say(ai_response, language='en-US')
    
    user_ai_summary.create_summary(request.form.get('CallSid') , request.form.get('CallStatus'))
    return str(response)


# ----------------------------------------------CREATE APPOINTMENT API CONT.--------------------------------------------------------------------------------------------------------------------------------------------------------------------


@app.route('/appointment-confirmation', methods=['GET' , 'POST'])
def appointment_confirmation(): 
    print()
    print("===========================================================")
    print("CONTACT HANDLER - 2")
    print("===========================================================")
    print()
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
            print()
            print("===========================================================")
            print("AI Response: Appointment scheduled successfully")
            print("===========================================================")
            print()
            ai_ask = f"Your appointment has been scheduled successfully for {date_offer} at {time_offer}. Thank you for using our service. , Do you have any other questions or is there anything else I can help with?"
            handler = "/handle-voice"
        else:
            print()
            print("===========================================================")
            print("AI Response: Failed to reschedule appointment")
            print("===========================================================")
            print()
            ai_ask = message_for_failed_appointment
            handler = "/handle-voice"
        
    elif "Nearest Time SLot is Available".lower() == text.lower():
        sessions[call_sid]['text'] = text
        date_time_offer = []
        for date_time in get_free_slots:
            slot = datetime.strptime(date_time, '%Y-%m-%dT%H:%M:%S%z').strftime('%Y-%m-%dT%H:%M:%S')
            date = timezone_fetch.convert_timezone(slot , timezone_user , sessions[call_sid]['timezone'])
            _ , time_offer_con = timezone_fetch.date_and_time(date)
            print("==================================================time  ",time_offer_con)
            date_time_offer.append(time_offer_con)
        ai_ask = f"This time slot is not available , but we have other time slots for you that are {date_time_offer[0]} and {date_time_offer[1]} or provide another date and time for the scheduling the appointment"     
        chat_history = sessions[call_sid]['chat_history']
        chat_history.append(AIMessage(content=ai_ask))
        sessions[call_sid]['chat_history'] = chat_history
        handler = "/appointment-fixed"

    elif "Time SLot is not Available".lower() == text.lower():
        start_time , end_time = timezone_fetch.find_start_end_time(sessions[call_sid]['access_token'] , timezone_user , sessions[call_sid]['timezone'])
        ai_ask = f"Our executives are available from {start_time} to {end_time}. On Saturdays and Sundays, we are not available, so please provide an alternative date and time."
        handler = "/appointment-fixed"

    with response.gather(input='speech', enhanced=True, speech_model='phone_call', speech_timeout='2', timeout = '50' , action_on_empty_result = True , action=handler) as gather:
        gather.say(ai_ask , language='en-US')
    
    user_ai_summary.create_summary(request.form.get('CallSid') , request.form.get('CallStatus'))
    return str(response)


#---------------------------------------------------CREATE APPOINTMENT API CONT.---------------------------------------------------------------------------------------------------------------------------------------------------------


@app.route('/appointment-fixed', methods=['POST'])
def appointment_fixed():
    print()
    print("===========================================================")
    print("CONTACT HANDLER - 3")
    print("===========================================================")
    print()
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

    with open(sessions[call_sid]['file_name'], "r") as json_file:    
        user_data_dict = json.load(json_file)
    

    speech_result_new = f"""
    In the {sessions[call_sid]['chat_history']} , AI is offering two time slot which is in the line 'This time slot is not available , but we have other time slots for' , so use that time slot.
    Don't Try to Implement Other Prompts in this like SCRIPT FOR SETTING UP AN ACCOUNT/GETTING STARTED/REGISTRATION PROCESS/SPEAK TO SALES REPRESENTATIVE/CREATE AN ACCOUNT , SCRIPT OF CREATE TASK(BILLING INQUIRY, SERVICE CONFIRMATION, SERVICE COMPLETION, PROVIDE ESTIMATE, SEND QUOTE, UPDATE STATUS, ADDRESS CONCERNS) , SCRIPT FOR CANCEL THE APPOINTMENT/RESCIND APPOINTMENT/REVOKE APPOINTMENT/CALL OFF APPOINTMENT/ABANDON APPOINTMENT , SCRIPT FOR UPDATE AN ACCOUNT/RESCHEDULE THE APPOINTMENT/UPDATE AN ACCOUNT/MODIFY AN APPOINTMENT
    Don't Try To Include any of the script mentioned above in this , Only Include SCRIPT FOR EXTRACTION OF DATE AND TIME FOR PARTICULAR CALLER this script.
    Always and Always Go to **SCRIPT FOR EXTRACTION OF DATE AND TIME FOR PARTICULAR CALLER:** with this {speech_result} to provide the Caller Details Extracting Date and Time with a title ’Here is your detailed Imformation You Provided’
    MORE RULES FOR **SCRIPT FOR EXTRACTION OF DATE AND TIME FOR PARTICULAR CALLER:**

    7. If Caller give the date , then this value will be consider as [date]. This will be the first priority.
        for example :-
                    Caller given the date 18-05-2024 or Caller Say 'I am available on/at 18-05-2024', then , 
                    [date] = 18-05-2024
                    [time] = timeSelected from {user_data_dict}
    8. If Caller doesn't provide any date then Go Through the {user_data_dict} and If the value of dateSelected in {user_data_dict} is not "" then the value of dateselected will be the value for [date].
        for example :-
                    then , 
                    [date] = dateSelected from {user_data_dict}
                    [time] = timeSelected from {user_data_dict}    
    9. If Caller give the time , then this value will be consider as [time]. This will be the also the first priority.
        for example :-
                    Caller given the time 8 PM or Caller Say 'I am available on/at 8 PM', then , 
                    [date] = dateSelected from {user_data_dict}
                    [time] = 8 PM    
    10. If Caller doesn't provide any time then Go Through the {user_data_dict} and If the value of timeSelected in {user_data_dict} is not "" then the value of timeSelected will be the value for [time]. 
        for example :-
                    then , 
                    [date] = dateSelected from {user_data_dict}
                    [time] = timeSelected from {user_data_dict}        
    11. Also change the [date] and [time] based of 7 , 8 , 9 , 10 rules
    
    12. Look for common patterns and keywords that indicate time, such as 'AM', 'PM', 'o'clock', 'morning', 'afternoon', 'evening', etc.
        Examples:
            - 'I am available at 8 PM'
            - 'Can we do 10 o'clock?'
            - 'How about 2 in the afternoon?'
        Extract the time part from these phrases and assign it to [time].
    At end the using this whole details , go to '**SCRIPT FOR EXTRACTION OF DATE AND TIME FOR PARTICULAR CALLER:**' , to provide the below summary :-
                        <format>
                                Title: Here is the summary of scheduling details :-
                                Date Selected: [date]
                                Time Selected: [time]
                        <format>
                
                Output format:
                Beautiful JSON with the keys in format.

    Example Usage:
        Caller says: "I am available at 9 PM"
        Extracted Details:
            [date] = dateSelected from {user_data_dict}
            [time] = 9 PM
        Summary:
            <format>
                Title: Here is the summary of scheduling details:,
                Date Selected: dateSelected from {user_data_dict},
                Time Selected: 9 PM
            <format>
        Caller says: "I am available on 20-06-2024"
        Extracted Details:
            [date] = 20-06-2024
            [time] = timeSelected from {user_data_dict}
        Summary:
            <format>
                Title: Here is the summary of scheduling details:,
                Date Selected: 20-06-2024,
                Time Selected: timeSelected from {user_data_dict}
            <format>
        Important Notes:

        Do not include any scripts related to account setup, task creation, cancellation, or update processes.
        Only focus on extracting date and time for scheduling.

    """
                            
    ai_response = call_handler.run_assistant(call_sid, speech_result_new)
    print()
    print("===========================================================")
    print("AI Response: ",ai_response)
    print("===========================================================")
    print()
    
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
            print()
            print("===========================================================")
            print("AI Response: Appointment scheduled successfully")
            print("===========================================================")
            print()
            ai_ask = f"Your appointment has been scheduled successfully for {date_offer} at {time_offer}. Thank you for using our service. , Do you have any other questions or is there anything else I can help with?"
            handler = "/handle-voice"
        else:
            print()
            print("===========================================================")
            print("AI Response: Failed to schedule appointment")
            print("===========================================================")
            print()
            ai_ask = message_for_failed_appointment
            handler = "/handle-voice"
        
    elif "Nearest Time SLot is Available".lower() == text.lower():
        sessions[call_sid]['text'] = text
        date_time_offer = []
        for date_time in get_free_slots:
            slot = datetime.strptime(date_time, '%Y-%m-%dT%H:%M:%S%z').strftime('%Y-%m-%dT%H:%M:%S')
            date = timezone_fetch.convert_timezone(slot , timezone_user , sessions[call_sid]['timezone'])
            _ , time_offer_con = timezone_fetch.date_and_time(date)
            print("==================================================time  ",time_offer_con)
            date_time_offer.append(time_offer_con)
        ai_ask = f"This time slot is not available , but we have other time slots for you that are {date_time_offer[0]} and {date_time_offer[1]} or provide another date and time for the scheduling the appointment"     
        handler = "/appointment-fixed"
        
    elif "Time SLot is not Available".lower() == text.lower():
        start_time , end_time = timezone_fetch.find_start_end_time(sessions[call_sid]['access_token'] , timezone_user , sessions[call_sid]['timezone'])
        ai_ask = f"Our executives are available from {start_time} to {end_time}. On Saturdays and Sundays, we are not available, so please provide an alternative date and time."
        handler = "/appointment-fixed"
    
    with response.gather(input='speech', enhanced=True, speech_model='phone_call', speech_timeout='2', timeout = '50' , action_on_empty_result = True , action=handler) as gather:
        gather.say(ai_ask , language='en-US')

    user_ai_summary.create_summary(request.form.get('CallSid') , request.form.get('CallStatus'))
    return str(response)


#---------------------------------------------------DELETE APPOINTMENT API----------------------------------------------------------------------------------------------------------------------------------------------------------------


@app.route('/cancel-appointment', methods=['GET' , 'POST'])
def cancel_appointment():
    print()
    print("===========================================================")
    print("DELETE HANDLER")
    print("===========================================================")
    print()
    user_ai_summary.create_summary(request.form.get('CallSid') , request.form.get('CallStatus'))
    response = VoiceResponse()
    call_sid = request.form.get('CallSid')
    speech_result = request.form.get('SpeechResult')

    print("===================================================")
    print("User Input = ",speech_result)
    print("===================================================")

    try:
        speech_result = f"Always Goto **SCRIPT FOR DELETE SCHEDULING SUMMARISATION:** with this {speech_result} to provide the Caller Details Delete Summarization with a title ’Here is your detailed delete Imformation You Provided’"
        ai_response = call_handler.run_assistant(call_sid, speech_result)
        print()
        print("===========================================================")
        print("AI Response_123:",ai_response)
        print("===========================================================")
        print()
        if "Here is the delete summary of scheduling details".lower() not in ai_response.lower():
            ai_response = no_voice_input_message
            handler = "/handle-voice"
            with response.gather(input='speech', enhanced=True, speech_model='phone_call', speech_timeout='2', timeout = '50' , action_on_empty_result = True , action=handler) as gather:
                gather.say(ai_response , language='en-US')
        else:
            date , _ = contact_handler.get_subaccount_info_2(ai_response) 
            sessions[call_sid]['date_extract'] = date
            
            ai_response = appointment_create.delete_appointment(call_sid , sessions[call_sid]['date_extract'])
            print()
            print("===========================================================")
            print("AI Response: Appointment cancelled successfully")
            print("===========================================================")
            print()
            handler = "/handle-voice"
            with response.gather(input='speech', enhanced=True, speech_model='phone_call', speech_timeout='2', timeout = '50' , action_on_empty_result = True , action=handler) as gather:
                gather.say(ai_response , language='en-US')
    except:
        ai_response = no_voice_input_message
        print()
        print("===========================================================")
        print("AI Response: Failed to cancelled appointment")
        print("===========================================================")
        print()
        handler = "/handle-voice"
        with response.gather(input='speech', enhanced=True, speech_model='phone_call', speech_timeout='2', timeout = '50' , action_on_empty_result = True , action=handler) as gather:
            gather.say(ai_response , language='en-US')
    
    user_ai_summary.create_summary(request.form.get('CallSid') , request.form.get('CallStatus'))
    return str(response)


#---------------------------------------------------UPDATE APPOINTMENT API----------------------------------------------------------------------------------------------------------------------------------------------------------------


@app.route('/update-information', methods=['GET' , 'POST'])
def update_information():
    print()
    print("===========================================================")
    print("UPDATE HANDLER - 1")
    print("===========================================================")
    print()
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
            
        elif "Here is the summary of scheduling details".lower() in ai_response.lower():
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

        with response.gather(input='speech', enhanced=True, speech_model='phone_call', speech_timeout='2', timeout = '50' , action_on_empty_result = True , action=handler) as gather:
            gather.say(ai_response, language='en-US')
        
    else:
        ai_response = no_voice_input_message
        handler = "/update-information"
        with response.gather(input='speech', enhanced=True, speech_model='phone_call', speech_timeout='2', timeout = '50' , action_on_empty_result = True , action=handler) as gather:
            gather.say(ai_response, language='en-US')
    
    user_ai_summary.create_summary(request.form.get('CallSid') , request.form.get('CallStatus'))
    return str(response)


#---------------------------------------------------UPDATE APPOINTMENT API CONT.---------------------------------------------------------------------------------------------------------------------------------------------------------


@app.route('/appointment-confirmation-two', methods=['GET' , 'POST'])
def appointment_confirmation_two(): 
    print()
    print("===========================================================")
    print("UPDATE HANDLER - 2")
    print("===========================================================")
    print()
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
            print()
            print("===========================================================")
            print("AI Response: Appointment rescheduled successfully")
            print("===========================================================")
            print()
            ai_ask = f"Your appointment has been rescheduled successfully for {date_offer} at {time_offer}. Thank you for using our service. , Do you have any other questions or is there anything else I can help with?"
            handler = "/handle-voice"
        else:
            print()
            print("===========================================================")
            print("AI Response: Failed to rescheduled appointment")
            print("===========================================================")
            print()
            ai_ask = message_for_failed_appointment
            handler = "/handle-voice"
        
    elif "Nearest Time SLot is Available".lower() == text.lower():
        sessions[call_sid]['text'] = text
        date_time_offer = []
        for date_time in get_free_slots:
            slot = datetime.strptime(date_time, '%Y-%m-%dT%H:%M:%S%z').strftime('%Y-%m-%dT%H:%M:%S')
            date = timezone_fetch.convert_timezone(slot , timezone_user , sessions[call_sid]['timezone'])
            _ , time_offer_con = timezone_fetch.date_and_time(date)
            print("==================================================time  ",time_offer_con)
            date_time_offer.append(time_offer_con)
        ai_ask = f"This time slot is not available , but we have other time slots for you that are {date_time_offer[0]} and {date_time_offer[1]} or provide another date and time for the recheduling the appointment"           
        handler = "/appointment-fixed-two"

    elif "Time SLot is not Available".lower() == text.lower():
        start_time , end_time = timezone_fetch.find_start_end_time(sessions[call_sid]['access_token'] , timezone_user , sessions[call_sid]['timezone'])
        ai_ask = f"Our executives are available from {start_time} to {end_time}. On Saturdays and Sundays, we are not available, so please provide an alternative date and time."
        handler = "/appointment-fixed"

    with response.gather(input='speech', enhanced=True, speech_model='phone_call', speech_timeout='2', timeout = '50' , action_on_empty_result = True , action=handler) as gather:
        gather.say(ai_ask , language='en-US')
    
    user_ai_summary.create_summary(request.form.get('CallSid') , request.form.get('CallStatus'))
    return str(response)


#---------------------------------------------------UPDATE APPOINTMENT API CONT.---------------------------------------------------------------------------------------------------------------------------------------------------------


@app.route('/appointment-fixed-two', methods=['POST'])
def appointment_fixed_two():
    print()
    print("===========================================================")
    print("UPDATE HANDLER - 3")
    print("===========================================================")
    print()
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

    with open(sessions[call_sid]['file_name'], "r") as json_file:    
        user_data_dict = json.load(json_file)
    
    speech_result_new = f"""
    In the {sessions[call_sid]['chat_history']} , AI is offering two time slot which is in the line 'This time slot is not available , but we have other time slots for' , so use that time slot.
    Don't Try to Implement Other Prompts in this like SCRIPT FOR SETTING UP AN ACCOUNT/GETTING STARTED/REGISTRATION PROCESS/SPEAK TO SALES REPRESENTATIVE/CREATE AN ACCOUNT , SCRIPT OF CREATE TASK(BILLING INQUIRY, SERVICE CONFIRMATION, SERVICE COMPLETION, PROVIDE ESTIMATE, SEND QUOTE, UPDATE STATUS, ADDRESS CONCERNS) , SCRIPT FOR CANCEL THE APPOINTMENT/RESCIND APPOINTMENT/REVOKE APPOINTMENT/CALL OFF APPOINTMENT/ABANDON APPOINTMENT , SCRIPT FOR UPDATE AN ACCOUNT/RESCHEDULE THE APPOINTMENT/UPDATE AN ACCOUNT/MODIFY AN APPOINTMENT
    Don't Try To Include any of the script mentioned above in this , Only Include SCRIPT FOR EXTRACTION OF DATE AND TIME FOR PARTICULAR CALLER this script.
    Always and Always Go to **SCRIPT FOR EXTRACTION OF DATE AND TIME FOR PARTICULAR CALLER:** with this {speech_result} to provide the Caller Details Extracting Date and Time with a title ’Here is your detailed Imformation You Provided’
    MORE RULES FOR **SCRIPT FOR EXTRACTION OF DATE AND TIME FOR PARTICULAR CALLER:**

    7. If Caller give the date , then this value will be consider as [date]. This will be the first priority.
        for example :-
                    Caller given the date 18-05-2024 or Caller Say 'I am available on/at 18-05-2024', then , 
                    [date] = 18-05-2024
                    [time] = timeSelected from {user_data_dict}
    8. If Caller doesn't provide any date then Go Through the {user_data_dict} and If the value of dateSelected in {user_data_dict} is not "" then the value of dateselected will be the value for [date].
        for example :-
                    then , 
                    [date] = dateSelected from {user_data_dict}
                    [time] = timeSelected from {user_data_dict}    
    9. If Caller give the time , then this value will be consider as [time]. This will be the also the first priority.
        for example :-
                    Caller given the time 8 PM or Caller Say 'I am available on/at 8 PM', then , 
                    [date] = dateSelected from {user_data_dict}
                    [time] = 8 PM    
    10. If Caller doesn't provide any time then Go Through the {user_data_dict} and If the value of timeSelected in {user_data_dict} is not "" then the value of timeSelected will be the value for [time]. 
        for example :-
                    then , 
                    [date] = dateSelected from {user_data_dict}
                    [time] = timeSelected from {user_data_dict}        
    11. Also change the [date] and [time] based of 7 , 8 , 9 , 10 rules
    
    12. Look for common patterns and keywords that indicate time, such as 'AM', 'PM', 'o'clock', 'morning', 'afternoon', 'evening', etc.
        Examples:
            - 'I am available at 8 PM'
            - 'Can we do 10 o'clock?'
            - 'How about 2 in the afternoon?'
        Extract the time part from these phrases and assign it to [time].
    At end the using this whole details , go to '**SCRIPT FOR EXTRACTION OF DATE AND TIME FOR PARTICULAR CALLER:**' , to provide the below summary :-
                        <format>
                                Title: Here is the summary of scheduling details :-
                                Date Selected: [date]
                                Time Selected: [time]
                        <format>
                
                Output format:
                Beautiful JSON with the keys in format.

    Example Usage:
        Caller says: "I am available at 9 PM"
        Extracted Details:
            [date] = dateSelected from {user_data_dict}
            [time] = 9 PM
        Summary:
            <format>
                Title: Here is the summary of scheduling details:,
                Date Selected: dateSelected from {user_data_dict},
                Time Selected: 9 PM
            <format>
        Caller says: "I am available on 20-06-2024"
        Extracted Details:
            [date] = 20-06-2024
            [time] = timeSelected from {user_data_dict}
        Summary:
            <format>
                Title: Here is the summary of scheduling details:,
                Date Selected: 20-06-2024,
                Time Selected: timeSelected from {user_data_dict}
            <format>
        Important Notes:

        Do not include any scripts related to account setup, task creation, cancellation, or update processes.
        Only focus on extracting date and time for scheduling.

    """
    
    ai_response = call_handler.run_assistant(call_sid, speech_result_new)
    print()
    print("===========================================================")
    print("AI Response: ",ai_response)
    print("===========================================================")
    print()
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
            print()
            print("===========================================================")
            print("AI Response: Appointment rescheduled successfully")
            print("===========================================================")
            print()
            ai_ask = f"Your appointment has been rescheduled successfully for {date_offer} at {time_offer}. Thank you for using our service. , Do you have any other questions or is there anything else I can help with?"
            handler = "/handle-voice"
        else:
            print()
            print("===========================================================")
            print("AI Response: Failed to rescheduled appointment")
            print("===========================================================")
            print()
            ai_ask = "Sorry, I was unable to schedule the appointment. Please try again later."
            handler = "/handle-voice"
        
    elif "Nearest Time SLot is Available".lower() == text.lower():
        sessions[call_sid]['text'] = text
        date_time_offer = []
        for date_time in get_free_slots:
            slot = datetime.strptime(date_time, '%Y-%m-%dT%H:%M:%S%z').strftime('%Y-%m-%dT%H:%M:%S')
            date = timezone_fetch.convert_timezone(slot , timezone_user , sessions[call_sid]['timezone'])
            _ , time_offer_con = timezone_fetch.date_and_time(date)
            print("==================================================time  ",time_offer_con)
            date_time_offer.append(time_offer_con)
        ai_ask = f"This time slot is not available , but we have other time slots for you that are {date_time_offer[0]} and {date_time_offer[1]} or provide another date and time for the recheduling the appointment"     
        handler = "/appointment-fixed-two" 
        
    elif "Time SLot is not Available".lower() == text.lower():
        start_time , end_time = timezone_fetch.find_start_end_time(sessions[call_sid]['access_token'] , timezone_user , sessions[call_sid]['timezone'])
        ai_ask = f"Our executives are available from {start_time} to {end_time}. On Saturdays and Sundays, we are not available, so please provide an alternative date and time."
        handler = "/appointment-fixed"
    
    with response.gather(input='speech', enhanced=True, speech_model='phone_call', speech_timeout='2', timeout = '50' , action_on_empty_result = True , action=handler) as gather:
        gather.say(ai_ask , language='en-US')

    user_ai_summary.create_summary(request.form.get('CallSid') , request.form.get('CallStatus'))
    return str(response)

if __name__ == "__main__":
    app.run(host="localhost", port=3000, debug=False)


#---------------------------------------------------FINETUNNIG API CONT.---------------------------------------------------------------------------------------------------------------------------------------------------------


# @app.route('/finetune', methods=['POST'])
# def finetune():
#     try:
#         # Run the finetuning job
#         finetune_updater.finetunning_job()
#         return jsonify({'message': 'Finetuning job started successfully'})
#     except Exception as e:
#         return jsonify({'message': str(e)})


