import os
import uuid
import time
import json
import warnings
import random
import io
import ast
import psycopg2
import constants
import datetime
import re
import requests
import threading
import pytz
import http.client
from queue import Queue
from psycopg2 import Error
from pydub import AudioSegment
from PyPDF2 import PdfReader
from dateutil import parser
from datetime import datetime, timedelta
from werkzeug.utils import secure_filename
from flask import Flask, request , jsonify , url_for , redirect , render_template , flash , get_flashed_messages , send_file
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


warnings.filterwarnings("ignore", category=UserWarning, module="pydub")
warnings.filterwarnings("ignore", category=DeprecationWarning, module="langchain")