from dotenv import load_dotenv
import os
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from enum import Enum, auto
import json
from test_pyro.utils import (
    check_url,
    process_address,
)

from pyrogram import Client, filters
from pyrogram.types import ReplyKeyboardMarkup, KeyboardButton
import logging


logging.basicConfig(level=logging.WARNING)

load_dotenv()

api_id = int(os.getenv('api_id'))
api_hash = os.getenv('api_hash')
app = Client('userbot', api_id=api_id, api_hash=api_hash)


class UserState(Enum):
    WAIT_FOR_ADDRESS = auto()


# хранение состояния
user_states = {}


@app.on_message(filters.command('start') & filters.private)
async def start_command(client, message):
    user_id = str(message.from_user.id)

    try:
        with open('users.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
    except FileNotFoundError:
        data = {}

    msg = 'Твои данные уже занесены в базу'

    if user_id not in data:
        data[user_id] = []
        msg = f'Привет {user_id}! Теперь ты зарегистрирован.'

        with open('users.json', 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

    button_1 = KeyboardButton('/set')
    button_2 = KeyboardButton('/list')
    kb = ReplyKeyboardMarkup([[button_1, button_2]], resize_keyboard=True)
    await message.reply(msg, reply_markup=kb)


@app.on_message(filters.command('list') & filters.private)
async def get_last_requests(client, message):
    user_id = str(message.from_user.id)
    try:
        with open('users.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
    except FileNotFoundError as e:
        print(str(e))
        msg = 'Что то не так!'
    else:
        msg = json.dumps(
            {'last_5_links': data[user_id][0].get('ping', None)[-5:]}
        )
    await message.reply(msg)


@app.on_message(filters.command('set') & filters.private)
async def set_command(client, message):
    # Устанавливаем состояние "WAIT_FOR_ADDRESS" для пользователя
    user_states[message.from_user.id] = UserState.WAIT_FOR_ADDRESS

    # Отправляем сообщение с инструкцией о вводе адреса сайта
    await message.reply('Введите адрес сайта:')


@app.on_message(filters.private)
async def handle_private_message(client, message):
    # Проверяем состояние пользователя
    user_state = user_states.get(message.from_user.id)
    if user_state == UserState.WAIT_FOR_ADDRESS:
        # Получаем адрес сайта от пользователя
        address = message.text

        # сохраняем адрес
        msg = await process_address(message.from_user.id, address)

        # Сбрасываем состояние пользователя после успешной обработки адреса
        user_states[message.from_user.id] = None

        # Отправляем сообщение об успешном установлении адреса
        await message.reply(msg)

    else:
        # Обработка всех остальных сообщений от пользователя
        await message.reply(
            'Для установки адреса сайта используйте команду /set'
        )


def main():
    scheduler = AsyncIOScheduler()
    scheduler.add_job(check_url, 'interval', seconds=60)

    scheduler.start()

    app.run()
