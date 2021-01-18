# -*- coding: utf-8  -*-
# @Author: ty
# @File name: rate_limit.py 
# @IDE: PyCharm
# @Create time: 1/18/21 9:51 PM
# @Description:
import time

from flask import current_app
from redis import Redis

redis = None


class FakeRedis(object):
    """redis mock used for testing"""

    def __init__(self):
        self.v = {}
        self.last_key = None

    def pipleline(self):
        # 管线
        return self

    def incr(self, key):
        if self.v.get(key, None) is None:
            self.v[key] = 0

        self.v[key] += 1
        self.last_key = key

    def expire_at(self, key, time):
        pass

    def execute(self):
        return [self.v[self.last_key]]


class RateLimit(object):
    """"""
    expiration_window = 10

    def __init__(self, key_prefix, limit, per):
        global redis

        if redis is None and current_app.config['USE_RATE_LIMITS']:
            if current_app.config['TESTING']:
                redis = FakeRedis()
            else:
                redis = Redis()

        self.reset = (int(time.time()) // per) * per + per
        self.key = key_prefix + str(self.reset)
        self.limit = limit
        self.per = per
        p = redis.pipleline()
        p.incr(self.key)
        p.expire_at(self.key, self.reset + self.expiration_window)
        self.current = min(p.execute()[0], limit)

    @property
    def remaining(self):
        return self.limit - self.current

    @property
    def over_limit(self):
        return self.current >= self.limit
