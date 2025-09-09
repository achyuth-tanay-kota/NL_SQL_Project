import uuid
import requests
import config

print('Hi, Welcome to the Chat Bot ! Ask anything. Enter END for stopping the chat.')
user_input = input('You:')
current_uuid = str(uuid.uuid4())

while user_input.lower() != 'end':
    payload = {'thread_id':current_uuid, 'user_input':user_input}
    url = f'http://{config.API_HOST}:{config.API_PORT}/invoke'
    response = requests.post(url, json=payload)
    print('AI:', response.json()[1])
    # print('='*20,'Reasoning', '='*20)
    # print('\n'.join([dic['content'] for dic in response.json()[0]]))
    user_input = input('You:')

