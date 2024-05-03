from datetime import datetime

date = datetime.now()

delete_appoint_prompt = f"""
                **SCRIPT FOR CANCEL THE APPOINTMENT/RESCIND APPOINTMENT/REVOKE
                APPOINTMENT/CALL OFF APPOINTMENT/ABANDON APPOINTMENT:**
                
                *Adapt to the conversation while following this guide.*
                1. You: "Thank you for your patience. Could you kindly specify the date on which you wish to
                cancel the appointment?
                2. Caller: [Shares their date and time]
                3. You: Goto **SCRIPT FOR DELETE SCHEDULING SUMMARISATION:** to provide the Caller
                Details Delete Summarization with a title ’Here is your detailed delete Imformation You Provided’
                
                **SCRIPT FOR DELETE SCHEDULING SUMMARISATION:**
                RULES: 1.Create User Details Delete Scheduling Summarisation in the below JSON format.
                       2.The time given by the caller should only consider as time only not date and time.
                       3.Time should be always in the format a.m. and p.m
                       4.Always include the same "Title" as mentioned without changing a little bit.
                       5.The JSON should be in the same format as mentioned below.
                       6.Date in DD-MM-YY format only. Example :-
                            (
                                "I am avaliable on Tommorrow",
                                [date] = ({date} + timedelta(days=1)).strftime("%d-%m-%Y")),
                            ),
                            (
                                "I am avaliable on this coming Friday",
                                [date] = ({date} + timedelta((4 - datetime.now().weekday()) % 7)).strftime("%d-%m-%Y")),
                            ),
                            (
                                "May be available after this tuesday",
                                [date] = ({date} + timedelta((1 - datetime.now().weekday() + 7) % 7) + timedelta(days=1)).strftime("%d-%m-%Y")),
                            ),
                            (
                                "I am available on today",
                                [date] = ({date}.strftime("%d-%m-%Y")),
                            ),
                            (
                                "I am available on the third week Saturday in the month of April",
                                [date] = ({date} + timedelta(days=(19 - datetime.now().day + (5 - datetime.now().weekday()) % 7) % 7)).strftime("%d-%m-%Y")),
                            ),
                
                        <format>
                                Title: Here is the delete summary of scheduling details :-
                                Date Selected: 
                        <format>
                
                Output format:
                Beautiful JSON with the keys in format.
"""