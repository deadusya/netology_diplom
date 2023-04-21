from datetime import datetime
from enum import IntEnum

import vk_api

from db import Db
from utils import diff_in_years

wrong_response_msg = 'Неверный формат ответа'

class VkError(Exception):
    def __init__(self, message):
        super().__init__(message)
        

class Relation(IntEnum):
    NOT_SPECIFIED = 0
    SINGLE = 1
    IN_RELATIONSHIP = 2
    ENGAGED = 3
    MARRIED = 4
    ITS_COMPLICATED = 5
    ACTIVELY_SEARCHING = 6
    IN_LOVE = 7
    IN_CIVIL_UNION = 8


def compute_rating(photo):
    comments_count = photo["comments"]["count"]
    likes_count = photo["likes"]["count"]
    # пусть комментарии будут ценнее лайков в два раза
    return likes_count + comments_count * 2


class VkApi:
    USERS_COUNT = 100

    def __init__(self, token, db: Db):
        self.cache = {}
        self.offsets = {}
        self.i = 0
        self.db = db
        self.token = token
        self._vk = vk_api.VkApi(token=self.token)

    def get_user(self, user_id):
        fields = [
            "sex",
            "bdate",
            "country",
            "city",
        ]

        user = self._vk.method(
            "users.get",
            values={
                "user_ids": [user_id],
                "fields": ",".join(fields),
            },
        )[0]

        # проверяем только id т.к. остальных полей может не быть 
        if user.get('id') is None:
            raise VkError(wrong_response_msg)

        bdate = user.get("bdate")
        # если есть дата рождения рассчитываем возраст
        if bdate:
            age = diff_in_years(datetime.today(), datetime.strptime(bdate, "%d.%m.%Y"))
            user["age"] = age
        return user

    def search_cities(self, city):
        response = self._vk.method("database.getCities", values={"q": city})
        cities = response["items"]
        if cities is None:
            raise VkError(wrong_response_msg)
        return cities

    def search_new_friend(self, user_id):
        user = self.db.find_user(user_id)
        sex = 1 if user["sex"] == 2 else 2
        age_range = 2
        age_from = user["age"] - age_range
        age_to = user["age"] + age_range

        fields = [
            "domain",
            "country",
            "city",
            "photo_max",
            "status",
            "interests",
            "occupation",
            "bdate",
        ]

        users = self.cache.get(user_id, [])
        offset = self.offsets.get(user_id, 0)
        shown_candidates = self.db.get_shown(user["id"])
        if not users:
            response = self._vk.method(
                "users.search",
                values={
                    "offset": offset,
                    "count": self.USERS_COUNT,
                    "has_photo": 1,
                    "status": Relation.ACTIVELY_SEARCHING.value,
                    "sex": sex,
                    "city_id": user["city"],
                    "age_from": age_from,
                    "age_to": age_to,
                    "fields": ",".join(fields),
                },
            )
            users = response.get("items")

            if users is None:
                raise VkError(wrong_response_msg)

            # отбираем новых кандидатов, у которых открыт профиль
            filtered_users = []
            for u in users:
                # если профиль закрыт переходим к след. кандидату
                if u["is_closed"]:
                    continue
                # если находится в просмотренных, пропускаем
                if u["id"] in shown_candidates:
                    continue
                filtered_users.append(u)

            self.cache[user_id] = filtered_users
            self.offsets[user_id] = offset + len(users)

        candidate = self.cache[user_id][0]
        photos_response = self._vk.method(
            "photos.get",
            values={
                "offset": 0,
                "count": 1000,
                "owner_id": candidate["id"],
                "extended": 1,
                "type": "album",
                "album_id": "profile",
            },
        )
        photos = photos_response.get("items")

        if photos is None:
            raise VkError(wrong_response_msg)

        # сортируем по рейтингу и берем первый три
        best_photos = sorted(photos, key=compute_rating)[:3]
        # наверное, лучше вынести в отдельный метод, чтобы можно было вызывать снаружи
        self.db.save_shown(user_id=user["id"], shownuser_id=candidate["id"])
        self.cache[user_id] = self.cache[user_id][1:]
        return candidate | {"photos": best_photos}