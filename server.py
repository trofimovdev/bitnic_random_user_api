import tormysql
import requests
from tornado.web import *
from tornado.template import *
from dotenv import load_dotenv
from tornado.ioloop import *

load_dotenv('.env')
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
    @staticmethod
    @gen.coroutine
    def generate_page():
        return Loader('template')\
            .load('index.html')\
            .generate()

    @gen.coroutine
    def get(self):
        page = yield self.generate_page()
        self.write(page)


class User(RequestHandler):
    @staticmethod
    @gen.coroutine
    def get_user_from_db():
        con = yield POOL.Connection()
        cur = con.cursor()
        yield cur.execute('SELECT * FROM users ORDER BY RAND() LIMIT 1')
        data = cur.fetchone()
        yield cur.close()
        yield con.close()
        return dict(zip(USERS_FIELDS, data))

    @staticmethod
    @gen.coroutine
    def add_new_users(n=5):
        c = 0
        con = yield POOL.Connection()
        cur = con.cursor()
        while c < n:
            response = requests.get('https://randomuser.me/api/?results=5').json().get('results')
            print('request')
            for user in response:
                name = (user['name']['first'] + ' ' + user['name']['last'])
                if 'r' not in name.lower():
                    email = user['email']
                    gender = int(user['gender'] == 'male')
                    location = ', '.join([
                        str(user['location']['postcode']),
                        user['location']['country'],
                        user['location']['state'],
                        user['location']['city']
                    ])
                    yield cur.execute('INSERT INTO users (name, email, gender, location) VALUES(%s, %s, %s, %s)',
                                      (name, email, gender, location))
                    c += 1
        yield con.commit()
        yield cur.close()
        yield con.close()

    @gen.coroutine
    def get(self):
        self.set_header('Content-Type', 'application/json')
        data = yield self.get_user_from_db()
        self.write(data)

    @gen.coroutine
    def put(self):
        yield self.add_new_users()
        self.finish()


application = Application([
    ('^/', Index),
    ('^/user/?$', User),
    ('/(.*)', StaticFileHandler, {'path': 'template/'})
    if os.environ.get('PORT') is None
    else ('', None)  # Make nginx work instead of poor Tornado
])

if __name__ == '__main__':
    application.loop = IOLoop.current()
    application.listen(os.environ.get('PORT', 5000))
    application.loop.start()
