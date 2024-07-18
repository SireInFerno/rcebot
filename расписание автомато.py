import time
import requests as r
from datetime import datetime, timedelta
import schedule

token = '6606763517:AAH-xjYFkQczrrJv2R9qqC_A3tRuf_2daNY'
offset = 0
group_name = None

def apiMethod(method, params):
    response = r.get(f'https://api.telegram.org/bot{token}/{method}', params=params)
    return response.json()

def get_schedule(date):
    date_data = {
        'day': date.day,
        'month': date.month,
        'year': date.year
    }
    response = r.get('https://api.rcenext.ru/schedule', params=date_data)
    try:
        return response.json()
    except ValueError:
        return None

def send_schedule(chat_id, date):
    schedule_data = get_schedule(date)
    if schedule_data and isinstance(schedule_data, list) and len(schedule_data) > 0:
        message_text = f"Расписание на {date.strftime('%d-%m-%Y')} для группы {group_name}:\n"
        for item in schedule_data:
            if isinstance(item, dict) and 'time' in item and 'subject' in item:
                message_text += f"{item['time']} - {item['subject']}\n"
            else:
                message_text = "Формат данных расписания неверен."
                break
    else:
        message_text = "Расписание не найдено."
    
    apiMethod('sendMessage', {
        'chat_id': chat_id,
        'text': message_text
    })

def handle_updates(updates):
    global group_name, offset
    for result in updates['result']:
        offset = result['update_id']
        message = result.get('message', {}) or result.get('edited_message', {})
        message_text = message.get('text', '')
        user = message.get('from', {})
        chat_id = message['chat']['id']
        username = user.get('username', user.get('first_name', 'Незнакомец'))

        print(f"Сообщение от {username}: {message_text}")

        if message_text.startswith('/start'):
            apiMethod('sendMessage', {
                'chat_id': chat_id,
                'text': 'Привет! Введите название вашей группы:'
            })
        elif message_text.startswith('/schedule'):
            parts = message_text.split()
            if len(parts) == 2:
                try:
                    date = datetime.strptime(parts[1], '%d-%m-%Y')
                    send_schedule(chat_id, date)
                except ValueError:
                    apiMethod('sendMessage', {
                        'chat_id': chat_id,
                        'text': 'Неверный формат даты. Пожалуйста, используйте формат DD-MM-YYYY.'
                    })
            else:
                apiMethod('sendMessage', {
                    'chat_id': chat_id,
                    'text': 'Пожалуйста, укажите дату в формате DD-MM-YYYY.'
                })
        elif group_name is None:
            group_name = message_text
            apiMethod('sendMessage', {
                'chat_id': chat_id,
                'text': f'Название группы установлено: {group_name}. Теперь я буду отправлять расписание каждый день.'
            })
            schedule.every().day.at("09:00").do(send_schedule, chat_id=chat_id, date=datetime.now() + timedelta(days=1))
        else:
            apiMethod('sendMessage', {
                'chat_id': chat_id,
                'text': f'Вы уже установили название группы: {group_name}. Для получения расписания на определенную дату используйте команду /schedule DD-MM-YYYY.'
            })

last_checked = datetime.now()

while True:
    updates = apiMethod('getUpdates', {
        'offset': offset + 1,
        'timeout': 5
    })
    if updates['result']:
        handle_updates(updates)
    
    schedule.run_pending()
    time.sleep(1)
