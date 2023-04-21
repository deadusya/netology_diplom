import config
from db import Db
from vkapi import VkApi
from vkinder import VkinderBot


if __name__ == "__main__":
    db = Db(config.POSTGRES_URI)
    db.init()
    api = VkApi(token=config.USER_TOKEN, db=db)

    bot = VkinderBot(
        token=config.GROUP_TOKEN,
        api=api,
        db=db,
    )

    bot.run_pooling()
