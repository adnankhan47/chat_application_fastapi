import os

import psycopg2
from psycopg2.extras import DictCursor

# Finer control over your data, then use psycopg2
class SupabaseConnection:
    def __init__(self, host, database, user, password, port):
        self.connection = psycopg2.connect(
            host=host,
            database=database,
            user=user,
            password=password,
            port=port
        )

    def __enter__(self):
        self.cursor = self.connection.cursor(cursor_factory=DictCursor)
        return self.cursor

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type: # When there is an exception
            self.connection.rollback()
            raise exc_type(exc_val)
        else: # Normal execution
            self.cursor.close()
            self.connection.commit()

HOST='aws-0-ap-south-1.pooler.supabase.com'
DB='postgres'
PORT='5432'
USER='postgres.claaenmfimnmsaxsvobz'
PASSWORD='Adnan@2000@kliky'

# host = os.getenv("HOST")
# db = os.getenv("DB")
# port = os.getenv("PORT")
# user = os.getenv("USER")
# password = os.getenv("PASSWORD")

print(PASSWORD)

db_connection = SupabaseConnection(HOST, DB, USER, PASSWORD, PORT)

# Context manager to implement transactions in db
# with db as cursor:
#     # __enter__
#     cursor.execute("UPDATE * FROM users")
#     result = cursor.fetchall()
#     result = [dict(row) for row in result]
#     result
#     # __exit__