# import json

# # Example JSON data
# data = {
#     "BACKGROUND INFO": {
#         "welcome_message": "Welcome to RubyPy , your helpful and knowledgeable AI assistant! My primary goal is to assist you in any way possible. Whether you have questions, need help with tasks, or simply want to chat, I’m here for you. The answer should be in a more Human-Like way .",
#         "how_liam_works": {
#             "knowledge_base": "Liam has access to a vast knowledge base containing a range of information about Availably Company. When you ask a question, Liam will first search its knowledge base to find a relevant answer about Availably.",
#             "gpt_assistance": "If Liam can’t find an answer in its knowledge base regarding Availably, then it will utilize the power of GPT to generate a response based on the context of your query. This ensures that even if the information isn’t readily available, Liam can still provide you with valuable insights.",
#             "chat history": "Liam remembers our past conversations to provide personalized assistance. For example, if you’ve previously shared your name during our chats and then ask Liam what your name is, it will retrieve the information from our chat history and provide you with the answer."
#         }
#     },
#     "RULES": "Start the conversation with 'Hey' or 'Hi,' avoiding 'Hello.' Direct prospects to our product specialists for in-depth technical queries or to discuss pricing details. Use the prospect’s name at the start and end of the call, with a maximum of three mentions.\", Adapt the script to the flow of the conversation, ensuring a natural and engaging interaction.\", Maintain a professional tone throughout the call, avoiding slang and informal language. Never interrupt the customer while they are speaking, and allow them to fully express.\", If a caller seems upset or has a concern about billing inquiry, service confirmation, service completion, provide estimate, send quote, update status, address concerns, we can guide them through creating a task for our team to address it.",
#     "SCRIPT": {
#         "initial_greeting": "You: 'Thank you for calling Availably. I’m Liam, your AI voice assistant. I can answer your questions and I can also schedule a time for you to speak with a live representative. How can I help you today?",
#         "company_overview": "Caller: 'What is Availably?'\\nYou: 'Availably offers a mix of human and AI Virtual Receptionist services, specializing in lead qualification and appointment scheduling. Availably is tailored for businesses seeking efficient call handling and lead management solutions. We’ll answer your businesses phone calls, chats, texts and messages 24 hours a day 7 days a week. We’ll handle your communications so you can focus on your work.",
#         "service_details": "Caller: 'What can your Virtual Receptionists do?'\\nYou: 'Our Virtual Receptionists can handle call answering, message taking, call forwarding, and respond to customer inquiries. We can customize these services based on your specific business needs.",
#         "lead_qualification_service": "Caller: 'How does your lead qualification service work?'\\nYou: 'We identify potential leads through calls and can integrate this information with your CRM systems for efficient lead tracking. We qualify them for your business based on your requirements.",
#         "appointment_scheduling": "Caller: 'Can you manage appointment scheduling?'\\nYou: 'Yes, we use calendar management software and can sync with your business calendars for real-time scheduling.",
#         "compatibility_with_existing_platforms": "Caller: 'Is your service compatible with our existing platforms?'\\nYou: 'Our service is compatible with various platforms and systems, including popular CRM and calendar applications via open API connections. If your system is compatible with Zapier, we can share data.",
#         "pricing_and_plans": "Caller: 'What are your pricing plans?'\\nYou: 'We offer three tiered plans to meet your specific needs. All plans offer the same features. The difference is in the amount of call and chat time you require for your business per month. Our first tier plan comes with 200 minutes for $360 per month. Overage is charged at $1.90 per additional minute. Our second tier plan comes with 360 minutes for $450 per month. Overage is charged at $1.65 per additional minute. And our third tier plan comes with 500 minutes for $580 per month. Overage is charged at $1.60 per additional minute.",
#         "features_of_plans": "Caller: 'What features do the plans come with?'\\nYou: 'All plans come with Live call answering, Live text, chat, Facebook messaging, Lead intake and qualification, Lead follow up automation, Customized call scripting, Calendar and CRM system access and integration, Appointment scheduling, and Appointment confirmations. All our receptionists are US-based and we have a goal of answering all of your calls in under a 5-second response time. All plans are billed month to month, with no long-term contracts.",
#         "customer_support": "Caller: 'How can I contact customer support?'\\nYou: 'You can reach our customer support via phone, email, or live chat.",
#         "user_testimonials_and_case_studies": "Caller: 'Do you have any success stories or client feedback?'\\nYou: 'Yes, we have several success stories and testimonials from clients who have seen significant benefits from using our services. These include improvements in lead management and customer service efficiency.",
#         "legal_and_compliance": "Caller: 'Can you tell me about your privacy policy and compliance standards?'\\nYou: 'Our privacy policy ensures the utmost security of your data. We adhere to industry-specific compliance standards to maintain the highest level of service integrity. You can read our complete terms of service and privacy policy on our website.",
#         "technical_support_and_troubleshooting": "caller: 'What should I do if I encounter technical issues?'\\nYou: 'For any technical issues, you can reach out to your account rep for help.",
#         "customization_and_personalization": "Caller: 'How can the service be customized to fit our business?'\\nYou: 'Our receptionist can be trained to match your business’s tone, language, and specific requirements. This includes custom greetings, specific FAQs related to your business, and personalized responses.",
#         "training_and_onboarding": "Caller: 'How do we train and onboard the receptionists for our business?'\\nYou: 'We provide a comprehensive onboarding process that includes training our human receptionists as well as our AI on your specific business needs, setting up the system, and ensuring it’s fully operational and tailored to your requirements."
#     }
# }



# def json_to_string(data, indent=0):
#     result = ""
#     indent_str = "  " * indent

#     if isinstance(data, dict):
#         for key, value in data.items():
#             result += f"{indent_str}{key}:\n"
#             result += json_to_string(value, indent + 1)
#     elif isinstance(data, list):
#         for item in data:
#             result += json_to_string(item, indent)
#     else:
#         result += f"{indent_str}{data}\n"

#     return result

# json_string = json_to_string(data)
# print(json_string)

from langchain_community.document_loaders import JSONLoader
import json
from pathlib import Path
from pprint import pprint


# data = {
#     "messages": [
#         {
#             "content": "Gemini 1.5 Pro is its long-context understanding across modalities."
#         },
#         {
#             "content": "Google claims that the Gemini 1.5 Pro is capable of achieving similar results as the recently launched Gemini 1.0 Ultra, albeit with much less computing power."
#         },
#         {
#             "content": "And, the most outstanding aspect of the Gemini 1.5 Pro is its ability to process the amount of information by up to one million tokens consistently."
#         },
#         {
#             "content": "This is certainly the longest context window for any large-scale foundation model developed yet."
#         },
#         {
#             "content": "To put into perspective, the Gemini 1.0 models have a context window of up to 32,000 tokens, GPT-4 Turbo has 1,28,000 tokens and Claude 2.1 has 2,00,000 tokens."
#         },
#         {
#             "content": "The Gemini 1.5 Pro can reportedly ingest up to 7,00,000 words or about 30,000 lines of code."
#         },
#         {
#             "content": "This is 35 times more than what Gemini 1.0 Pro can take in."
#         },
#         {
#             "content": "Besides, the Gemini 1.5 Pro can process up to 11 hours of audio and 1 hour of video in a wide range of languages."
#         },
#         {
#             "content": "The demo videos posted on Google’s official YouTube channel showed the long context understanding of the model by using a 402-page-long PDF."
#         },
#         {
#             "content": "The demo also showed a live interaction with the model based on the PDF file as prompt, which was 3,26,658 tokens and had 256 tokens worth of images."
#         },
#         {
#             "content": "The demo used a total of 3,27,309 tokens."
#         },
#         {
#             "content": "Reportedly, in a preview, Google said that the Gemini 1.5 Pro with a 1 million-token context window will be free to use."
#         },
#         {
#             "content": "Google may introduce pricing tiers in the future on the model that starts at 1,28,000 context windows and will scale up to 1 million tokens."
#         },
#         {
#             "content": "Gemini 1.5 Pro is a new frontier in Google’s AI developments."
#         },
#         {
#             "content": "In December last year, Google introduced its most flexible AI model Gemini 1.0 in three different sizes, including Gemini Ultra, Gemini Pro, and Gemini Nano."
#         },
#         {
#             "content": "At the time of launch, Google claimed that its Gemini 1.0 surpassed several state-of-the-art performances on a range of benchmarks including coding and text."
#         },
#         {
#             "content": "The Gemini series has been known for its next-generation capabilities and sophisticated reasoning."
#         },
#         {
#             "content": "All Gemini sizes have been known for their multimodality — the ability to understand text, images, audio and more."
#         }
#     ]
# }



# # file_path='/home/akash_raut/voicebot/data.json'
# loader = JSONLoader(
#     file_path='/home/akash_raut/voicebot/data.json',
#     jq_schema='.messages[].content',
#     text_content=False)

# data = loader.load()
# pprint(data)


from typing import Any, Union, Dict, List
import json
import os
from dependency import *
import constants

openai_api_key = os.environ["OPENAI_API_KEY"] = constants.APIKEY

class JSONLoader:
    def __init__(self, data: Union[str, Dict[str, Any]], jq_schema: str, text_content: bool = False):
        if isinstance(data, str):
            self.data = json.loads(data)
        else:
            self.data = data
        self.jq_schema = jq_schema
        self.text_content = text_content

    def load(self):
        import jq
        return jq.compile(self.jq_schema).input(self.data).all()

# Sample data
data = {
    "messages": [
        {"content": "Gemini 1.5 Pro is its long-context understanding across modalities."},
        {"content": "Google claims that the Gemini 1.5 Pro is capable of achieving similar results as the recently launched Gemini 1.0 Ultra, albeit with much less computing power."},
        {"content": "And, the most outstanding aspect of the Gemini 1.5 Pro is its ability to process the amount of information by up to one million tokens consistently."},
        {"content": "This is certainly the longest context window for any large-scale foundation model developed yet."},
        {"content": "To put into perspective, the Gemini 1.0 models have a context window of up to 32,000 tokens, GPT-4 Turbo has 1,28,000 tokens and Claude 2.1 has 2,00,000 tokens."},
        {"content": "The Gemini 1.5 Pro can reportedly ingest up to 7,00,000 words or about 30,000 lines of code."},
        {"content": "This is 35 times more than what Gemini 1.0 Pro can take in."},
        {"content": "Besides, the Gemini 1.5 Pro can process up to 11 hours of audio and 1 hour of video in a wide range of languages."},
        {"content": "The demo videos posted on Google’s official YouTube channel showed the long context understanding of the model by using a 402-page-long PDF."},
        {"content": "The demo also showed a live interaction with the model based on the PDF file as prompt, which was 3,26,658 tokens and had 256 tokens worth of images."},
        {"content": "The demo used a total of 3,27,309 tokens."},
        {"content": "Reportedly, in a preview, Google said that the Gemini 1.5 Pro with a 1 million-token context window will be free to use."},
        {"content": "Google may introduce pricing tiers in the future on the model that starts at 1,28,000 context windows and will scale up to 1 million tokens."},
        {"content": "Gemini 1.5 Pro is a new frontier in Google’s AI developments."},
        {"content": "In December last year, Google introduced its most flexible AI model Gemini 1.0 in three different sizes, including Gemini Ultra, Gemini Pro, and Gemini Nano."},
        {"content": "At the time of launch, Google claimed that its Gemini 1.0 surpassed several state-of-the-art performances on a range of benchmarks including coding and text."},
        {"content": "The Gemini series has been known for its next-generation capabilities and sophisticated reasoning."},
        {"content": "All Gemini sizes have been known for their multimodality — the ability to understand text, images, audio and more."}
    ]
}

# Initialize loader with data
loader = JSONLoader(data=data, jq_schema='.messages[].content', text_content=False)

# Load and print data
loaded_data = loader.load()
from pprint import pprint
pprint(loaded_data)

# Create a document-like structure for each content
class Document:
    def __init__(self, page_content: str, metadata: Dict[str, Any] = None):
        self.page_content = page_content
        self.metadata = metadata or {}


documents: List[Document] = [Document(content) for content in loaded_data]

# Initialize text splitter
splitter = RecursiveCharacterTextSplitter(
    chunk_size=800,
    chunk_overlap=50
)

# Split documents
split_docs = splitter.split_documents(documents)

# Convert split documents back to a list of strings for embedding
split_texts = [doc.page_content for doc in split_docs]

# Initialize OpenAI Embeddings
embedding = OpenAIEmbeddings(openai_api_key=openai_api_key)

# Create vector store
vectorStore = FAISS.from_texts(split_texts, embedding=embedding)
# vectors = vectorStore.get_all_vectors()
# print(vectors)


embeddings = vectorStore.similarity_search
print(dir(embeddings))

print(dir(vectorStore))
