"""
Используя данные из VK, нужно сделать сервис намного лучше, чем Tinder, а именно: чат-бота "VKinder". Бот должен искать людей, подходящих под условия, на основании информации о пользователе из VK:
    - возраст,
    - пол,
    - город,
    - семейное положение.

Входные данные
    - Имя пользователя или его id в ВК, для которого мы ищем пару.

Если информации недостаточно нужно дополнительно спросить её у пользователя.

Требования:
    - Код программы удовлетворяет PEP8.
    - Получать токен от пользователя с нужными правами.
    - Программа декомпозирована на функции/классы/модули/пакеты.
    - Результат программы записывать в БД.
    - Люди не должны повторяться при повторном поиске.
    - Не запрещается использовать внешние библиотеки для vk.
"""
import logging
from typing import Any, Dict

import vk_api
from vk_api.longpoll import VkLongPoll, VkEventType, Event
from vk_api.utils import get_random_id

from db import Db
from vkapi import VkApi
from utils import ParseError, make_parse_city, parse_age, parse_sex

logger = logging.getLogger(__name__)

greet_msg = 'Привет, {name}! Я помогу найти тебе пару, напиши "поиск" в чат!'
help_msg = (
    "Я понимаю следующие команды:\n"
    "привет - отвечу приветствием\n"
    "поиск - начну искать для тебя пару"
)
age_msg = "Напиши мне свой возраст"
city_msg = "В каком городе ты живешь?"
sex_msg = "Чуть не забыл!😄 Напиши мне свой пол (м/ж)"


class VkinderBot:
    def __init__(self, token: str, api: VkApi, db: Db):
        self.state: Dict[int, Any] = {}
        self.api = api
        self.db = db
        self.vk = vk_api.VkApi(token=token)

    def run_pooling(self):
        """Инициализирует и запускает бота"""
        self.longpoll = VkLongPoll(self.vk)
        for event in self.longpoll.listen():
            if event.type == VkEventType.MESSAGE_NEW:
                if event.to_me:
                    if self.state.get(event.user_id) is None:
                        self.state[event.user_id] = None
                    try:
                        self.handle_message(event)
                    except:
                        self.write_msg(event.user_id, "Что-то пошло не так")
                        logger.exception("При обработке сообщения произошла ошибка")

    def handle_message(self, event: Event):
        """Обработчик новых сообщений"""
        state = self.state[event.user_id]
        message = event.text

        # state нужен чтобы отличать команды от данных пользователя,
        # которые мы у него запросили
        if state == "age":
            self.process_age(event)
        elif state == "sex":
            self.process_sex(event)
        elif state == "city":
            self.process_city(event)
        elif message == "привет":
            self.process_greeting(event)
        elif message == "поиск":
            self.process_search(event)
        else:
            self.show_help(event)

    def get_user(self, user_id):
        user = self.db.find_user(user_id)
        # если пользователя нет в базе, получаем данные из его профиля вк
        # и сохраняем в базу
        if user is None:
            user = self.api.get_user(user_id)
            user = self.db.create_user(user)
        return user

    def process_search(self, event: Event):
        user_id = event.user_id
        user = self.get_user(user_id)
        # если у пользоателя нет каких-то данных, запрашиваем их и
        # записываем в state какие данные ожидаем, чтобы при следующем
        # сообщении их распарсить
        if user.get("age") is None:
            self.write_msg(user_id, age_msg)
            self.state[user_id] = "age"
            return

        if user.get("city") is None:
            self.write_msg(user_id, city_msg)
            self.state[user_id] = "city"
            return

        if user.get("sex") is None:
            self.write_msg(user_id, sex_msg)
            self.state[user_id] = "sex"
            return

        self.search_friends(user_id)

    def show_help(self, event: Event):
        self.write_msg(event.user_id, help_msg)

    def search_friends(self, user_id):
        offer = self.api.search_new_friend(user_id)
        attachment = ",".join(
            map(lambda p: f'{"photo"}{offer["id"]}_{p["id"]}', offer["photos"])
        )
        link = f'https://vk.com/id{offer["id"]}'
        name = f'{offer.get("first_name")}'
        text = f"{name}\n{link}\n\n"
        self.write_msg(user_id, text=text, attachment=attachment)

    def process_greeting(self, event: Event):
        name = self.api.get_user(event.user_id)["first_name"]
        self.write_msg(event.user_id, greet_msg.format(name=name))

    def process_age(self, event: Event):
        user_id = event.user_id
        user = self.db.find_user(user_id)
        try:
            user["age"] = parse_age(event.text)
            self.db.update_user(user)
            self.state[user_id] = None
            self.process_search(event)
        except ParseError as e:
            self.write_msg(user_id, e)

    def process_sex(self, event: Event):
        user_id = event.user_id
        user = self.db.find_user(user_id)
        try:
            user["sex"] = parse_sex(event.text)
            self.db.update_user(user)
            self.state[user_id] = None
            self.process_search(event)
        except ParseError as e:
            self.write_msg(user_id, e)

    def process_city(self, event: Event):
        parse_city = make_parse_city(self.api)

        user_id = event.user_id
        user = self.db.find_user(user_id)
        try:
            user["city"] = parse_city(event.text)
            self.db.update_user(user)
            self.state[user_id] = None
            self.process_search(event)
        except ParseError as e:
            self.write_msg(user_id, e)

    def process_help(self, event: Event):
        self.write_msg(event.user_id, "process_help")

    def write_msg(self, user_id, text=None, attachment=None, keyboard=None):
        values = {
            "user_id": user_id,
            "random_id": get_random_id(),
        }

        if text:
            values["message"] = text

        if attachment:
            values["attachment"] = attachment

        if keyboard:
            values["keyboard"] = keyboard

        self.vk.method("messages.send", values)
