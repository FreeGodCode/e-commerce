# -*- coding: utf-8  -*-
# @Author: ty
# @File name: extensions.py 
# @IDE: PyCharm
# @Create time: 1/6/21 10:54 PM
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
from flask_sqlalchemy import SQLAlchemy

# 数据库
# db = SQLAlchemy()
from redis import Redis

db = MongoEngine()
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


def init_extensions(app):
    """
    初始化第三方插件
    :return:
    """
    db.init_app(app)
    migrate.init_app(app, db)
    mail.init_app(app)
    cache.init_app(app)
    admin.init_app(app)
    login_manager.init_app(app)
    principal.init_app(app)
    bcrypt.init_app(app)
    babel.init_app(app)
    toolbar.init_app(app)
    assets.init_app(app)
