import psycopg2


class Db:
    """Клас, в котором собраны методы для работы с базой данных"""
    def __init__(self, dsn):
        self._dsn = dsn

    def create_user(self, user: dict):
        """Сохраняет пользователя и возвращает его же"""
        with psycopg2.connect(self._dsn) as conn:
            with conn.cursor() as curs:
                sql = """INSERT INTO users (id, age, sex, city)
                            VALUES (%s, %s, %s, %s)"""
                curs.execute(
                    sql,
                    (
                        user["id"],
                        user.get("age"),
                        user.get("sex"),
                        user.get("city"),
                    ),
                )
                return user

    def update_user(self, user: dict):
        """Обновляет данные пользователя"""
        with psycopg2.connect(self._dsn) as conn:
            with conn.cursor() as curs:
                sql = """UPDATE users
                            SET age=%s, sex=%s, city=%s
                            WHERE id = %s"""
                curs.execute(
                    sql,
                    (
                        user.get("age"),
                        user.get("sex"),
                        user.get("city"),
                        user["id"],
                    ),
                )

    def find_user(self, user_id):
        """Возвращает пользователя по его user_id, если не находит
        возвращает None
        """
        with psycopg2.connect(self._dsn) as conn:
            with conn.cursor() as curs:
                sql = "SELECT id, age, sex, city FROM users WHERE id=%s"
                curs.execute(sql, (user_id,))
                row = curs.fetchone()
                if row:
                    return {
                        "id": row[0],
                        "age": row[1],
                        "sex": row[2],
                        "city": row[3],
                    }

    def save_shown(self, user_id, shownuser_id):
        """Сохраняет в базу id показанного пользователя"""
        with psycopg2.connect(self._dsn) as conn:
            with conn.cursor() as curs:
                sql = """INSERT INTO shownusers (id, user_id)
                            VALUES (%s, %s)"""
                curs.execute(sql, (shownuser_id, user_id))

    def get_shown(self, user_id):
        """Получает список id показанных пользователей"""
        with psycopg2.connect(self._dsn) as conn:
            with conn.cursor() as curs:
                sql = "SELECT id FROM shownusers WHERE user_id=%s"
                curs.execute(sql, (user_id,))
                return [row[0] for row in curs.fetchall()]
