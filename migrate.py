import sys

import psycopg2

import config

migration_file = sys.argv[1]

with open(migration_file, mode="r", encoding="utf-8") as fp:
    sql = fp.read()
    with psycopg2.connect(config.POSTGRES_URI) as conn:
        with conn.cursor() as curs:
            curs.execute(sql)
