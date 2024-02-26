import os
from os.path import join, dirname
import requests
from dotenv import load_dotenv

def get_from_env(key):
    dotenv_path = join(dirname(__file__), '.env')
    load_dotenv(dotenv_path)
    return os.environ.get(key) # Возращаем секретный токен

def send_message(chat_id, text):
    method = 'sendMessage'
    token = get_from_env('TELEBOT')
    url = f'https://api.telegram.org/bot{token}/{method}'
    data = {'chat_id': chat_id, 'text': text}
    requests.post(url, data=data)