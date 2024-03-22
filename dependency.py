import os
import uuid
import time
import json
import elevenlabs
import warnings
import prompt
import random
import io
import psycopg2
import constants
from psycopg2 import Error
from pydub import AudioSegment
from PyPDF2 import PdfReader
from flask import Flask, request , jsonify
from twilio.twiml.voice_response import VoiceResponse
from langchain_openai import ChatOpenAI
from langchain_community.document_loaders import DirectoryLoader , PyMuPDFLoader
from langchain.indexes import VectorstoreIndexCreator
from langchain_core.prompts import ChatPromptTemplate
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.chains import create_retrieval_chain
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.prompts import MessagesPlaceholder
from langchain.chains.history_aware_retriever import create_history_aware_retriever
from langchain.indexes.vectorstore import VectorStoreIndexWrapper
from langchain_community.embeddings import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_community.document_loaders import PyPDFDirectoryLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores.faiss import FAISS
