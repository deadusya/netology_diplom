from datetime import datetime
from enum import IntEnum

import vk_api

from db import Db
from utils import diff_in_years


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
    def __init__(self, token, db: Db):
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

        bdate = user.get("bdate")
        if bdate:
            age = diff_in_years(datetime.today(), datetime.strptime(bdate, "%d.%m.%Y"))
            user["age"] = age
        return user

    def search_cities(self, city):
        response = self._vk.method("database.getCities", values={"q": city})
        return response["items"]

    def search_new_friend(self, user_id):
        user = self.db.find_user(user_id)

        sex = 1 if user["sex"] == 2 else 2
        age_from = user["age"] - 2
        age_to = user["age"] + 2

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

        users = self._vk.method(
            "users.search",
            values={
                "offset": 0,
                "count": 500,
                "has_photo": 1,
                "status": Relation.ACTIVELY_SEARCHING.value,
                "sex": sex,
                "city_id": user["city"],
                "age_from": age_from,
                "age_to": age_to,
                "fields": ",".join(fields),
            },
        )

        for candidate in users["items"]:
            # если профиль закрыт переходим к след. кандидату
            if candidate["is_closed"]:
                continue
            # если находится в просмотренных, пропускаем
            shown_candidates = self.db.get_shown(user["id"])
            if candidate["id"] in shown_candidates:
                continue

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
            
            photos = photos_response["items"]
            # сортируем по рейтингу и берем первый три
            best_photos = sorted(photos, key=compute_rating)[:3]
            # наверное, лучше вынести в отдельный метод, чтобы можно было вызывать снаружи
            self.db.save_shown(user_id=user["id"], shownuser_id=candidate["id"])
            return candidate | {"photos": best_photos}
