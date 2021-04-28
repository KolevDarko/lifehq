import datetime

import redis

REDIS_CONNECTION = {
    'host': 'localhost',
    'port': 6379,
    'db': 0
}

class AnalyticsClientManager:

    def __init__(self):
        try:
            self.redis_db = redis.StrictRedis(host=REDIS_CONNECTION['host'], port=REDIS_CONNECTION['port'],
                                                        db=REDIS_CONNECTION['db'])
        except:
            self.redis_db = None

    def get_client(self, user_id):
        if self.redis_db:
            return AnalyticsClient(user_id, self.redis_db)
        else:
            return AnalyticsNullClient()

    def record(self, user_id, key):
        client = self.get_client(user_id)
        client.db_count_key(key)

    def analize_all(self, analyze_points):
        all_keys = self.redis_db.keys("analytics:*")
        results = {}
        power_users = 0
        for hash_key in all_keys:
            user_analytics = {}
            user_points = 0
            raw_analytics = self.redis_db.hgetall(hash_key)
            for raw_key, val in raw_analytics.items():
                key = raw_key.decode()
                user_analytics[key] = val.decode()
                user_points += int(val.decode())
            if user_points >= analyze_points:
                power_users += 1
                results[hash_key.decode()] = user_analytics
        return results, power_users


PAYMENTS = 'PAYMENTS'
PROJECT = 'PROJECT'
JOURNAL = 'JOURNAL'
HABIT = 'HABIT'
HABIT_ACTION = 'HABIT_ACTION'
PROJECT_TASK = 'PROJECT_TASK'
PROJECT_TODO_LIST = 'PROJECT_TODO_LIST'
MASTER_TASK = 'MASTER_TASK'
POMODORO_SESSION = 'POMODORO_SESSION'
POMODORO_CYCLE = 'POMODORO_CYCLE'


class AnalyticsNullClient:

    def db_count_key(self, key):
        pass

    def count_project(self):
        pass

    def count_journal(self):
        pass


class AnalyticsClient:

    def __init__(self, user_id, redis_conn):
        self.red = redis_conn
        self.user_id = user_id
        self.hash_name = "analytics:{}".format(user_id)

    def db_count_key(self, key):
        date_str = datetime.datetime.utcnow().date().isoformat()
        date_key = "{}:{}".format(date_str, key)
        self.red.hincrby(self.hash_name, date_key)

    def count_project(self):
        self.db_count_key(PROJECT)

    def count_journal(self):
        self.db_count_key(JOURNAL)

AnalyticsManager = AnalyticsClientManager()
