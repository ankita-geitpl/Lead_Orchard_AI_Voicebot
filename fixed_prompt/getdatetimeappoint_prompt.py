from datetime import datetime

date = datetime.now()

dt_appoint_prompt = f"""
                **SCRIPT FOR EXTRACTION OF DATE AND TIME:**
                
                1. You: Goto **SCRIPT FOR EXTRACTION OF DATE AND TIME FROM THE DATA:** to provide the Caller
                Details Summarization with a title ’Here is your detailed Imformation You Provided’
                
                **SCRIPT FOR EXTRACTION OF DATE AND TIME FOR PARTICULAR CALLER:**
                RULES: 1.Create User Details Extracting Date and Time in the below JSON format.
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
                                Title: Here is the summary of scheduling details :-
                                Date Selected: 
                                Time Selected:
                        <format>
                
                Output format:
                Beautiful JSON with the keys in format.
"""