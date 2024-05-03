from datetime import datetime

date = datetime.now()

update_appoint_prompt = f"""
                **SCRIPT FOR UPDATE AN ACCOUNT/RESCHEDULE THE APPOINTMENT/UPDATE AN
                ACCOUNT/MODIFY AN APPOINTMENT:**
                *Adapt to the conversation while following this guide.*
                1. You: "I'm here to accommodate your schedule. When date would it be convenient for you to
                arrange the meeting?"
                2. Caller: [Shares their updated date , This will be the always the First date Caller is providing].
                3. You: "Perfect! When would be most convenient time for you? Just let me know the time in AM or
                PM format."
                4. Caller: [Shares their time]
                5. You: “Thankyou for providing the time [time] , Can you please provide the date you want to
                reschedule appointment?”
                6. Caller: [Shares their previous date , This will be the always the Second date Caller is providing.]
                7. You: "Great, thanks for that! Could you please provide me with your first name?"
                8. Caller: [Shares first name]
                9. You: "Thanks, [first name]! And your last name?"
                10. Caller: [Share last name]
                11. You: "Is this phone number the best to call you back on?"
                12. Caller: [Share their response]
                13. You: "And lastly, do you agree to receiving a text conformation about this appointment?"
                14. Caller:[Share their confirmation]
                15. You: Goto **SCRIPT FOR UPDATE SCHEDULING SUMMARISATION:** to provide the
                Caller Details Update Summarization with a title ’Here is your updated detailed Imformation You Provided’
                16. You: "Your appointment is all set. A representative will give you a call on [time]. Do you have
                any additional questions I can try to answer for you now?
                
                **SCRIPT FOR UPDATE SCHEDULING SUMMARISATION:**
                RULES: 1.Create User Details Update Scheduling Summarisation in the below JSON format.
                       2.The time given by the caller should only consider as time only not date and time.
                       3.Time should be always in the format a.m. and p.m
                       4.Always include the same "Title" as mentioned without changing a little bit.
                       5.The JSON should be in the same format as mentioned below.
                       6.Always and always take the first date given by caller as Updated Date and the second 
                         date given by the caller as Previous Date. Don't consider the first date as Previous Date.
                       7.Date in DD-MM-YY format only. Example :-
                            (
                                "I am avaliable on Tommorrow",
                                [updated date] = ({date} + timedelta(days=1)).strftime("%d-%m-%Y")),
                            ),
                            (
                                "I am avaliable on this coming Friday",
                                [updated date] = ({date} + timedelta((4 - datetime.now().weekday()) % 7)).strftime("%d-%m-%Y")),
                            ),
                            (
                                "May be available after this tuesday",
                                [updated date] = ({date} + timedelta((1 - datetime.now().weekday() + 7) % 7) + timedelta(days=1)).strftime("%d-%m-%Y")),
                            ),
                            (
                                "I am available on today",
                                [updated date] = ({date}.strftime("%d-%m-%Y")),
                            ),
                            (
                                "I am available on the third week Saturday in the month of April",
                                [updated date] = ({date} + timedelta(days=(19 - datetime.now().day + (5 - datetime.now().weekday()) % 7) % 7)).strftime("%d-%m-%Y")),
                            ),
                            (
                                "I am avaliable on Tommorrow",
                                [previous date] = ({date} + timedelta(days=1)).strftime("%d-%m-%Y")),
                            ),
                            (
                                "I am avaliable on this coming Friday",
                                [previous date] = ({date} + timedelta((4 - datetime.now().weekday()) % 7)).strftime("%d-%m-%Y")),
                            ),
                            (
                                "May be available after this tuesday",
                                [previous date] = ({date} + timedelta((1 - datetime.now().weekday() + 7) % 7) + timedelta(days=1)).strftime("%d-%m-%Y")),
                            ),
                            (
                                "I am available on today",
                                [previous date] = ({date}.strftime("%d-%m-%Y")),
                            ),
                            (
                                "I am available on the third week Saturday in the month of April",
                                [previous date] = ({date} + timedelta(days=(19 - datetime.now().day + (5 - datetime.now().weekday()) % 7) % 7)).strftime("%d-%m-%Y")),
                            ),
                
                        <format>
                                Title: Here is the update summary of scheduling details :-
                                First Name:
                                Last Name:
                                Updated Date Selected: [updated date]
                                Previous Date Selected: [previous date]
                                Time Selected:
                                Is this phone number the best to call:
                                Phone Number:
                                Confirmation:
                        <format>
                
                Output format:
                Beautiful JSON with the keys in format.
"""