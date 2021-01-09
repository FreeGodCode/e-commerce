# -*- coding: utf-8  -*-
# @Author: ty
# @File name: __init__.py.py 
# @IDE: PyCharm
# @Create time: 1/6/21 10:49 PM
# @Description:
from flask_admin import Admin
from flask_assets import Environment
from flask_babel import Babel
from flask_bcrypt import Bcrypt
from flask_cache import Cache
from flask_debugtoolbar import DebugToolbarExtension
from flask_login import LoginManager
from flask_mail import Mail
from flask_migrate import Migrate
from flask_mongoengine import MongoEngine
from flask_principal import Principal
from flask_pymongo import PyMongo
from redis import Redis

# 数据库
# db = SQLAlchemy()

db = MongoEngine()

# flask_pymongo
mongo_inventory = PyMongo()

# 数据库迁移
migrate = Migrate()

# 邮件
mail = Mail()

# 缓存
cache = Cache()

# 管理
admin = Admin()

# 登录管理
login_manager = LoginManager()

principal = Principal()

bcrypt = Bcrypt()

babel = Babel()

# 调试工具
toolbar = DebugToolbarExtension()

assets = Environment()

# redis
redis = Redis()
session_redis = Redis()

