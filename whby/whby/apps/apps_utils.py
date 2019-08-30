from psycopg2 import extras
from django.conf import settings
from psycopg2.pool import AbstractConnectionPool


class UtilsPostgresql(AbstractConnectionPool):
    """Postgresql数据库连接池"""

    def __init__(self):
        super().__init__(minconn=5, maxconn=30, database=settings.POSTGRESQL_DATABASE, user=settings.POSTGRESQL_USER,
                         password=settings.POSTGRESQL_PASSWORD, host=settings.POSTGRESQL_HOST,
                         port=settings.POSTGRESQL_PORT)

    def connect_postgresql(self):
        connection = AbstractConnectionPool._getconn(self)
        cursor = connection.cursor(cursor_factory=extras.RealDictCursor)
        # cursor = connection.cursor()
        # print(connection)
        return connection, cursor

    def disconnect_postgresql(self, connection):
        AbstractConnectionPool._putconn(self, connection)