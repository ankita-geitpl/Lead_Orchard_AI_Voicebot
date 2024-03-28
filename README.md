# Voice Bot


## Description
The Voice Bot serves as an AI voice assistant for Availably, a company offering human and AI virtual receptionist services. When initial calls are sent to Flex for live answering but no one is available or picks up within 8 seconds, the Voice Bot steps in to assist.


## Company Details
Availably offers a mix of human and AI Virtual Receptionist services, specializing in lead qualification and appointment scheduling. Availably is tailored for businesses seeking efficient call handling and lead management solutions. They handle various communication channels 24/7, allowing businesses to focus on their work.


## Folder Structure
The project directory structure is organized as follows:

Voice-Bot/
│
├── data/
│   └── data_file.pdf         
│
├── app.wsgi                   
├── botcode.py         
├── constant.py 
├── dependency.py         
└── requirements.txt            

In this structure:

* The data folder contains the data_file.pdf file, which serves as the dataset for training the Voice Bot model.
* The constant.py file holds all the required environment variables and keys necessary for the project to function properly.
* The app.wsgi file serves as a configuration file for establishing a proxy connection between the web server and the Python application, defining how requests and responses are handled in the WSGI environment.
* botcode.py holds the main application for running our voicebot
* dependency.py includes all the import libraries and modules utilized within the project.
* requirements.txt lists all the Python dependencies required for the project, facilitating easy installation.

This folder structure ensures that all necessary files and resources are organized logically, making it easier for developers to navigate and understand the project.


## Installation

Before installing the project dependencies listed in `requirements.txt`, ensure you have the necessary system dependencies installed:

### 1. Install PortAudio Development Files
```bash
sudo apt-get install portaudio19-dev
```
This step is required for PyAudio, which is used for audio input/output in the project.


### 2. Install Python Dependencies
Once you have installed the PortAudio development files, proceed to install the Python dependencies using pip:
```bash
pip install -r requirements.txt
```
This command will install all the required modules and dependencies listed in the requirements.txt file.

### 3. install this library manually 
If you require support for CSV file handling in the unstructured library, you'll need to install the library with the CSV extension. You can do this manually using the following command:
```bash
pip install "unstructured[csv]"
```
This command installs the unstructured library along with its CSV extension, enabling you to work with CSV files seamlessly in your project.

### 4. Additional Manual Installation
After installing the dependencies, you'll need to manually install the ffmpeg library:
```bash
sudo apt install ffmpeg
```
This library is necessary for certain audio processing functionalities in the project.

### 5. Setting up a Proxy with Apache and WSGI
To set up a proxy using Apache and a WSGI file, you first enable the **mod_proxy** module in Apache. 
Then, in your Apache configuration, you use the **ProxyPass** directive to specify the URL you want to proxy and the backend server. 
Additionally, you configure a **WSGIScriptAlias** in your Apache configuration to point to your WSGI file, which is responsible for serving your application. 
Finally, you restart Apache to apply the changes.


By following these steps, you'll ensure that all necessary dependencies are installed correctly, allowing you to run the project smoothly.
Feel free to adjust the formatting or content as needed!


## Usage
The Voice Bot serves as an AI voice assistant for Availably. It provides assistance in a human-like manner, utilizing various capabilities:
- **Knowledge Base**: Accesses a vast knowledge base containing information about Availably Company.
- **GPT Assistance**: Utilizes GPT to generate responses based on the context of queries.
- **Chat History**: Remembers past conversations to provide personalized assistance.
- **Impact on Your Agency**: Recognizes the impact of AI solutions and seeks input and guidance to meet agency needs effectively.
- **Keeping the Discussion Focused**: Ensures conversations stay focused on relevant topics.


