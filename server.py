import json
import tormysql
from tornado.web import *
from tornado.template import *
from tornado.ioloop import IOLoop

MAX_WORKERS = 16
POOL = tormysql.ConnectionPool(
    max_connections=64,
    idle_seconds=7200,
    wait_connection_timeout=3,
    host=os.environ.get('MYSQL_HOST'),
    user=os.environ.get('MYSQL_USER'),
    passwd=os.environ.get('MYSQL_PASSWORD'),
    db='db',
    charset='utf8'
)
USERS_FIELDS = [
    'id',
    'name',
    'email',
    'gender',
    'location'
]


class Index(RequestHandler):
    @gen.coroutine
    def get(self):
        self.write('Hello, World!')


class User(RequestHandler):
    @gen.coroutine
    def get_user_from_db(self):
        con = yield POOL.Connection()
        cur = con.cursor()
        yield cur.execute('SELECT * FROM users ORDER BY RAND() LIMIT 1')
        data = cur.fetchone()
        yield cur.close()
        yield con.close()
        return dict(zip(USERS_FIELDS, data))

    @gen.coroutine
    def get(self):
        self.set_header('Content-Type', 'application/json')
        data = yield self.get_user_from_db()
        self.write(data)

    @gen.coroutine
    def put(self):
        pass


application = Application([
    ('^/', Index),
    ('^/user/?$', User),
])


if __name__ == '__main__':
    application.loop = IOLoop.current()
    application.listen(os.environ.get('PORT', 5000))
    application.loop.start()
