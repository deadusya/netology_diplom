import config

from db import Db

db = Db(dsn=config.POSTGRES_URI)

peter = {
    "id": 1234,
    "age": 18,
    "sex": 1,
    "city": 1234,
}

olga = {
    "id": 2222,
    "age": 28,
    "sex": 2,
    "city": 99,
}

db.create_user(peter)
user = db.find_user(user_id=1234)
print(user)
user['age'] = 33
db.update_user(user)
print(user)

db.save_shown(user['id'], olga['id'])

print(db.get_shown(peter['id']))