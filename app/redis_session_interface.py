# -*- coding: utf-8  -*-
# @Author: ty
# @File name: redis_session_interface.py 
# @IDE: PyCharm
# @Create time: 1/11/21 11:29 AM
# @Description:
import pickle
from datetime import timedelta

from uuid import uuid4

from flask.sessions import SessionMixin, SessionInterface
from redis import Redis
from werkzeug.datastructures import CallbackDict


class RedisSession(CallbackDict, SessionMixin):
    """"""
    def __init__(self, initial=None, sid=None, new=False):
        def on_update(self):
            self.modified = True
            CallbackDict.__init__(self, initial, on_update)
            self.sid = sid
            self.new = new
            self.modified = False

class RedisSessionInterface(SessionInterface):
    """"""
    serializer = pickle
    session_class = RedisSession

    def __init__(self, redis=None, prefix='session:'):
        if redis is None:
            redis = Redis()
        self.redis = redis
        self.prefix = prefix

    def generate_sid(self):
        """
        生成uuid
        :return:
        """
        return str(uuid4())

    def get_redis_expiration_time(self, app, session):
        """
    获取session的过期时间
        :param app:
        :param session:
        :return:
        """
        # session设置为永久
        if session.permanent:
            return app.permanent_session_lifetime
        return timedelta(days=1)

    def open_session(self, app, request):
        """
        SessionId
        :param app:
        :param request:
        :return:
        """
        sid = request.cookies.get(app.session_cookie_name)
        if not sid:
            sid = self.generate_sid()
            return self.session_class(sid=sid, new=True)
        val = self.redis.get(self.prefix + sid)
        if val is not None:
            data = self.serializer.loads(val)
            return self.session_class(data, sid=sid)
        return self.session_class(sid=sid, new=True)

    def save_session(self, app, session, response):
        """

        :param app:
        :param session:
        :param response:
        :return:
        """
        domain = self.get_cookie_domain(app)
        if not session:
            self.redis.delete(self.prefix + session.sid)
            if session.modified:
                response.delete_cookie(app.session_cookie_name, domain=domain)
                return
            # redis的过期时间
            redis_exp = self.get_redis_expiration_time(app, session)
            # cookie的过期时间
            cookie_exp = self.get_expiration_time(app, session)
            # 序列化
            val = self.serializer.dumps(dict(session))
            self.redis.setex(self.prefix + session.sid, val, int(redis_exp.total_seconds()))
            response.set_cookie(app.session_cookie_name, session.sid, expires=cookie_exp, httponly=True, domain=domain)
