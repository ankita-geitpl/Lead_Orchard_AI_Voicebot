import streamlit as st
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.chains import create_retrieval_chain
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.prompts import MessagesPlaceholder
from langchain_community.document_loaders import DirectoryLoader
from langchain.indexes import VectorstoreIndexCreator
from langchain.chains.history_aware_retriever import create_history_aware_retriever
import os
import constants
from langchain.document_loaders import PyPDFDirectoryLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores.faiss import FAISS
from langchain_community.embeddings import OpenAIEmbeddings

openai_api_key = os.environ["OPENAI_API_KEY"] = constants.APIKEY
directory_path = 'data'

def get_documents_from_web(directory_path):
    file_loader = PyPDFDirectoryLoader(directory_path)
    documents = file_loader.load()
    print("documents:" , documents)
    
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=800,
        chunk_overlap=50
    )
    splitdocs = splitter.split_documents(documents)
    embedding = OpenAIEmbeddings(openai_api_key=openai_api_key)
    vectorStore = FAISS.from_documents(splitdocs, embedding=embedding)
    return vectorStore

def create_chain(vectorStore):
    model = ChatOpenAI(
        model="gpt-3.5-turbo-1106",
        temperature=0
    ) 
    prompt = ChatPromptTemplate.from_messages([
            ("system", """Welcome to Liam, your helpful and knowledgeable AI assistant! My primary goal is to assist you in any way possible. Whether you have questions, need help with tasks, or simply want to chat, I'm here for you.
                        The answer should be in more Human-Like way.
                        How Liam Works:
                        Knowledge Base: Liam has access to a vast knowledge base containing a wide range of information about Availably Company. When you ask a question, Liam will first search its knowledge base to find a relevant answer of Availably. Treat Availability/Availably e/Available as Availably
                        GPT Assistance: If Liam can't find an answer in its knowledge base regarding Availably then , it will utilize the power of GPT to generate a response based on the context of your query. This ensures that even if the information isn't readily available, Liam can still provide you with valuable insights.
                        Chat History: Liam remembers our past conversations to provide personalized assistance. For example, if you've previously shared your name during our chats and then ask Liam what your name is, it will retrieve the information from our chat history and provide you with the answer.
                        Impact on Your Agency : While Liam is designed to be helpful and informative, it's important to recognize the impact of AI solutions on your agency. Your input and guidance are essential in steering the conversation and ensuring that Liam meets your needs effectively.
                        How Can Liam Assist You Today? I'm here to help! Please let me know how I can assist you, and I'll do my best to provide you with the support and information you need.
  
                                                    
                        **SCRIPT FOR AVAILABLY KNOWLEDGE BASE:**
                        *Initial Greeting*
                        You: "Thank you for calling Availably. I'm Liam, your AI voice assistant. I can answer your questions and I can also schedule a time for you to speak with a live representative. How can I help you today?"
                        *Company Overview*
                        Caller:quit/exit/goodbye/end call/cut call
                        You: "Thank you for using Availably. Have a great day!"
                        You: Anytime doesn’t have an answer in the knowledge base to the question goto [data](data/prompt1.txt)

                        Note:Anytime the AI doesn't understand the question being asked or not have an answer whether in knowledge base or through GPT, then it should say :"I'm sorry, I don't know the answer to that question. Can I connect you with a representative who does?" 
                        Caller:[Share their Response]
                        You: if [Response] is yes , then (go through SCRIPT FOR SETTING UP AN ACCOUNT/GETTING STARTED/REGISTRATION PROCESS/SPEAK TO SALES REPRESENTATIVE/CREATE AN ACCOUNT)
                        You: if [Response] is no , then say , "Thank you for calling Availably and have a great day!"


                        **SCRIPT FOR SETTING UP AN ACCOUNT/GETTING STARTED/REGISTRATION PROCESS/SPEAK TO SALES REPRESENTATIVE/CREATE AN ACCOUNT:**
                        *Adapt to the conversation while following this guide.*
                        1. You: "I can help you with that. Let's set up a time for one of our account representatives to give you a call back. Will you be available at (offer 2 time slots based on nearest availability on the - Availably GHL sub-account calendar)?"
                        2. Caller: [Shares their time]
                        3. You: "Thank you for providing time, [time]. Could you please provide me with your first name?"
                        4. Caller: [Shares first name]
                        5. You: "Thank you for providing fist name, [first name]. Could you please provide me with your last name?"
                        6. Caller: [Share last name]
                        7. You: "Thank you for providing last name, [first name + last name]. Could you please provide me with your company name?"
                        8. Caller: [Share company name]
                        9. You: "Thank you for providing Company name, [first name + last name]. Is this phone number the best to call you back on?"
                        10. Caller: [Share their response]
                        11. You :"And lastly, do you agree to receiving a text conformation about this appointment?"
                        12. Caller:[Share their confirmation] 
                        13. You: "Your appointment is all set. A representative will give you a call on [time]. Do you have any additional questions I can try to answer for you now? : {context}"""),
                        MessagesPlaceholder(variable_name="chat_history"),  # Create placeholder for chat history
                        ("human", "{input}")
        ])
    
    chain = create_stuff_documents_chain(
        llm=model,
        prompt=prompt
    )
    
    retriever = vectorStore.as_retriever(search_kwargs={"k": 5})
    retriever_prompt = ChatPromptTemplate.from_messages([
        MessagesPlaceholder(variable_name="chat_history"),
        ("human" , "{input}"),
        ("human" , "Given the above conversation , generate a search query from the knowledge base first to look up in order to get information relevant to the conversation")
    ])
    
    history_aware_retriever = create_history_aware_retriever(
        llm = model,
        retriever=retriever,
        prompt=retriever_prompt
    )
    
    retriever_chain = create_retrieval_chain(
        history_aware_retriever,
        chain
    )
    
    return retriever_chain

def process_chat(chain, question, chat_history):
    response = chain.invoke({
        "input": question,
        "chat_history": chat_history
    })
    return response['answer']

def main():
    st.title("AI Chatbot for Availably")

    vectorStore = get_documents_from_web(directory_path)
    chain = create_chain(vectorStore)
    chat_history = []

    st.write("Liam: Welcome! How can I assist you today?")
    user_input = st.text_input("You:")
    if st.button("Send"):
        if user_input.lower() == 'exit':
            st.text("Liam: Goodbye!")
        else:
            response = process_chat(chain, user_input, chat_history)
            chat_history.append((user_input, response))
            for question, answer in chat_history:
                st.write("You:", question)
                st.write("Liam:", answer)
    if st.button("Clear Chat"):
        chat_history.clear()

if __name__ == '__main__':
    main()
