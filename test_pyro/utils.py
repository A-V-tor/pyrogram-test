import asyncio
import re
import aiohttp
import json
import datetime


# валидация ссылок
url_pattern = re.compile(
    r'^(https?://)?([A-Za-z0-9\-]+\.)+[A-Za-z]{2,6}(/[A-Za-z0-9\-._~:/?#[\]@!$&\'()*+,;=]*)?$'
)


async def make_requests(session, sl):
    user_id, url = [i for i in sl.items()][0]

    # тайм-аут 3 секунды
    ten_millis = aiohttp.ClientTimeout(total=3)
    try:
        async with session.get(url, timeout=ten_millis) as result:
            return result.status, user_id, url
    except TimeoutError:
        return 'timeout', user_id, url


async def check_url():
    # список ссылок для проверки
    urls = []

    try:
        with open('users.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
            for key_note in data.keys():
                if data[key_note]:
                    url = data[key_note][0].get('url', None)
                    urls.append({key_note: url})
    except Exception as e:
        print(str(e))

    async with aiohttp.ClientSession() as session:

        # список запросов
        fetchers = [make_requests(session, i) for i in urls]

        # обновление файла новыми данными по их готовности
        for finished_task in asyncio.as_completed(fetchers):
            status, user, url = await finished_task
            with open('users.json', 'r', encoding='utf-8') as f:
                data = json.load(f)
                with open('users.json', 'w', encoding='utf-8') as f:
                    date = datetime.datetime.now().isoformat()
                    data[user][0]['ping'].append({date: [status, url]})
                    json.dump(data, f, ensure_ascii=False, indent=4)


async def process_address(user_id, address):
    user_id = str(user_id)
    if not url_pattern.match(address):
        return 'Не валидный адрес'

    # загружаем данные из файла в словарь
    with open('users.json', 'r', encoding='utf-8') as f:
        data = json.load(f)

    date = datetime.datetime.now().isoformat()

    if user_id in data:
        # если есть сохраненные запросы
        check = data[user_id]
        if len(check) > 0:
            pong_data = data[user_id][0].get('ping')
            data[user_id] = [{'url': address, 'date': date, 'ping': pong_data}]
        else:
            data[user_id] = [{'url': address, 'date': date, 'ping': []}]

        # запись обновленных данных
        with open('users.json', 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

        return f'Сайт {address} добавлен в реестр'

    return 'Пройдите для начало регистрацию\n /start'
