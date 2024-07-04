import streamlit as st
import requests
import logging
import os
import json
# from openai import OpenAI
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO)

# Load environment variables from .env file
load_dotenv()

# API keys and IDs
auth_token = os.getenv('AUTH_TOKEN')
phone_number_id = os.getenv('PHONE_NUMBER_ID')
openApi = os.getenv('OPENAI_API_KEY')

# client = OpenAI(api_key=openApi)

# Load the dataset
def load_dataset(file_path):
    data = []
    with open(file_path, 'r') as f:
        for line in f:
            data.append(json.loads(line))
    return data

dataset = load_dataset('dataset.jsonl')

def fetch_user_data():
    url = 'https://test.attflex.com/flex360/opera/api/flexuser'
    headers = {
        'authtoken': 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ1c2VyIjoiQVRUQ2FsbFZ1IiwibmFtZSI6IkFUVCBDYWxsIFZ1IiwicGFzc3dvcmQiOm51bGwsIkFQSV9USU1FIjoxNjkxNTE2MDMxfQ.tBRxp40WbFSkzaJyXXzgKhM5Cxt4zz6RRqGlgwQVlJk',
        'Content-Type': 'application/x-www-form-urlencoded',
        'Accept': 'application/json'
    }
    data = {'flex360_email': 'demo@123.com'}
    response = requests.post(url, headers=headers, data=data)
    if response.status_code == 200:
        return response.json()
    else:
        logging.error(f"Failed to fetch user data: {response.text}")
        return None

def search_answer(question, dataset):
    for entry in dataset:
        if entry['messages'][0]['content'].lower() in question.lower():
            return entry['messages'][1]['content']
    return None

def make_call(phone_number, user_data, question):
    answer = search_answer(question, dataset)
    if answer:
        user_prompt = answer
    else:
        if user_data is None:
            user_prompt = "Unfortunately, we couldn't retrieve any user details."
        else:
            user_prompt = "\n".join([f"{key}: {value}" for key, value in user_data.items()])

    headers = {
        'Authorization': f'Bearer {auth_token}',
        'Content-Type': 'application/json',
    }

    first_name = user_data.get('FIRST NAME', 'User')

    system_prompt = f"""
    {user_prompt}
    you are the customer support at flexpert
    To provide you with the best assistance:
    - First, could you please confirm your first name and your FLEX360_ID?
    - After you provide your details, I will verify them against our records.
    - If the details you provide match our records, I'll provide you with the specific information you need.
    - If there is no match, I will inform you that the information could not be found and advise you to verify the details you've provided.
    """

    data = {
        'assistant': {
            "firstMessage": f"Hello {first_name}! How can I assist you today?",
            "model": {
                "provider": "openai",
                "model": "gpt-4-turbo",
                "messages": [
                    {
                        "role": "system",
                        "content": system_prompt.strip()
                    },
                    {
                        "role": "user",
                        "content": f"My name is {user_data.get('FIRST NAME', 'unknown')} and my FLEX360_ID is {user_data.get('FLEX360_ID', 'unknown')}."
                    },
                    {
                        "role": "system",
                        "content": "Let me check that information for you."
                    },
                    {
                        "role": "system",
                        "content": "Here is your information:" if user_data.get('FIRST NAME', '').lower() == 'degq' and str(user_data.get('FLEX360_ID', '')) == '1' else "I'm sorry, I couldn't find your information. Please verify your name and FLEX360_ID."
                    }
                ]
            },
            "voice": "jennifer-playht"
        },
        'phoneNumberId': phone_number_id,
        'customer': {
            'number': phone_number,
        },
    }

    try:
        json_data = json.dumps(data)  # Ensure the data is correctly formatted as JSON
        logging.info(f"Request data: {json_data}")  # Log the JSON payload for debugging
        response = requests.post('https://api.vapi.ai/call/phone', headers=headers, data=json_data)
        response.raise_for_status()
        return 'Call created successfully.', response.json()
    except requests.RequestException as e:
        logging.error(f"Error making call: {e.response.text}")  # Log the response text for detailed error
        return 'Failed to create call', e.response.text

# Streamlit App configuration
st.title('Call Dashboard')
st.sidebar.title('Navigation')
options = ['Single Call']
choice = st.sidebar.selectbox('Select a section', options)

if choice == 'Single Call':
    st.header('Single Call')
    phone_number = st.text_input('Enter phone number (with country code)')
    question = st.text_area('Enter your question')

    if st.button('Make Call'):
        user_data = fetch_user_data()
        message, response = make_call(phone_number, user_data, question)
        st.write(message)
        st.json(response)


