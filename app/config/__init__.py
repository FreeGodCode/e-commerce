# -*- coding: utf-8  -*-
# @Author: ty
# @File name: config.py 
# @IDE: PyCharm
# @Create time: 1/6/21 11:55 PM
# @Description:配置文件设置
import os
import datetime

from celery.schedules import crontab
from pymongo import ReadPreference

from app.config.enum import Enum

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def get_db_uri(db_info):
    engine = db_info.get('ENGINE') or 'mysql'
    driver = db_info.get('DRIVER') or 'pymysql'
    user = db_info.get('USER') or 'root'
    password = db_info.get('PASSWORD') or '123456'
    host = db_info.get('HOST') or 'localhost'
    port = db_info.get('PORT') or '3306'
    db_name = db_info.get('DBNAME') or ''
    return '{}+{}://{}:{}@{}:{}/{}'.format(engine, driver, user, password, host, port, db_name)


E = Enum(['develop', 'production', 'testing'])
APP_NAME = Enum(['maybe', 'admin', 'worker'])


class Config:
    DEBUG = False
    SECRET_KEY = 'tycarry'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    PROJECT = APP_NAME.meybe
    VERSION = 'V1.0'

    # flask_debug_toolbar
    DEBUG_TB_INTERCEPT_REDIRECTS = False
    DEBUG_TB_TEMPLATE_EDITOR_ENABLED = True
    DEBUG_TB_PROFILTER_ENABLED = True
    DEBUG_TB_PANELS = [
        'flask_debugtoolbar.panels.versions.VersionDebugPanel',
        'flask_debugtoolbar.panels.timer.TimerDebugPanel',
        'flask_debugtoolbar.panels.header.HeaderDebugPanel',
        'flask_debugtoolbar.panels.request_vars.RequestVarsDebugPanel',
        'flask_debugtoolbar.panels.config_vars.ConfigVarsDebugPanel',
        'flask_debugtoolbar.panels.template.TemplateDebugPanel',
        'flask_debugtoolbar.panels.logger.LoggingPanel',
        'flask_debugtoolbar.panels.profiler.ProfilerDebugPanel',
        'flask_debugtoolbar.panels.MongoDebugPanel',
    ]

    ADMINS = frozenset(['season@maybi.cn'])

    IDCARD_KEY = ''
    CSRF_ENABLED = False
    WTF_CSRF_ENABLED = False
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'upload')
    AVATAR_FOLDER = os.path.join(BASE_DIR, 'static/img/avatar')

    SESSION_COOKIE_DOMAIN = '.maybi.cn'
    SERVER_NAME = 'maybi.cn'
    # flask_login
    REMEMBER_COOKIE_DOMAIN = 'maybe.cn'
    PERMANENT_SESSION_LIFETIME = datetime.timedelta(days=31)

    # flask_pymongo
    MONGODB_SETTINGS = {
        'db': 'db_ecommerce',
        'host': 'localhost',
        'port': 27017,
        'read_preference': ReadPreference.PRIMARY_PREFERRED,
    }
    # 订单
    ORDER_DB_CONFIG = {
        'alias': 'db_order',
        'name': 'order',
        'host': 'localhost',
        'port': 27017,
    }
    # 库存
    INVENTORY_DB_CONFIG = {
        'alias': 'db_inventory',
        'name': 'inventory',
        'host': 'localhost',
        'port': 27017,
    }
    # 购物车
    CART_DB_CONFIG = {
        'alias': 'db_cart',
        'name': 'cart',
        'host': 'localhost',
        'port': 27017,
    }
    # content
    CONTENT_DB_CONFIG = {
        'alias': 'db_content',
        'name': 'content',
        'host': 'localhost',
        'port': 27017,
    }
    # log
    LOG_DB_CONFIG = {
        'alias': 'db_log',
        'name': 'log',
        'host': 'localhost',
        'port': 27017,
    }
    # session
    SESSION_REDIS = {
        'db': 0,
        'host': 'localhost',
        'port': 6379,
        'encoding': 'utf-8',
        'encoding_errors': 'strict',
        'decode_response': False,
    }
    # redis
    REDIS_CONFIG = {
        'db': 0,
        'host': 'localhost',
        'port': 6379,
        'encoding': 'utf-8',
        'encoding_errors': 'strict',
        'decode_response': False,
    }

    MONGO_INVENTORY_HOST = 'localhost'
    MONGO_INVENTORY_PORT = 27017
    MONGO_INVENTORY_DB_NAME = 'inventory'

    # flask_mail
    MAIL_DEBUG = False
    MAIL_SERVER = 'smtp@163.com'
    MAIL_PORT = 465
    MAIL_USER_TLS = False
    MAIL_USER_SSL = False
    MAIL_USERNAME = 'thechosenone_ty@163.com'
    MAIL_PASSWORD = ''
    DEFAULT_MAIL_SENDER = MAIL_USERNAME

    # flask_babel
    ACCEPT_LANGUAGES = ['ZH', 'EN']
    BABEL_DEFAULT_LOCALE = 'ZH'

    # flask_cache
    CACHE_TYPE = 'redis'
    TRACKING_EXCLUDE = (

    )

    # celery定时任务设置
    CELERY_BROKER_URL = ''
    CELERY_RESULT_BACKEND = ''
    CELERY_IMPORTS = (
        'app.services.jobs.image',
        'app.services.jobs.notification',
        'app.services.jobs.express',
        'app.services.scheduling.forex',
        'app.services.scheduling.express',
    )
    CELERY_TASK_TIME_LIMIT = 300
    CELERY_TASK_SOFT_TIME_LIMIT = 120
    CELERY_OPTIONS = '--time-limit=300  --concurrency=1'

    CELERYBEAT_SCHEDULE = {

        'rocord_latest_forex_rate_every_2_hours': {
            'task': 'app.services.scheduling.forex.record_latest_forex_rate',
            'schedule': crontab(minute=0, hour='*/2'),
        },
        # 快递
        'kuaidi_request_every_8_hour': {
            'task': 'app.services.scheduling.express.check_kuaidi',
            'schedule': crontab(minure=0, hour='*/8'),
        },
    }


class DevelopConfig(Config):
    """开发环境"""
    DEBUG = True
    db_info = {
        'ENGINE': 'mysql',
        'DRIVER': 'pymysql',
        'USER': 'root',
        'PASSWORD': '123456',
        'HOST': 'localhost',
        'PORT': '3306',
        'DBNAME': 'db_ecommerce'
    }
    SQLALCHEMY_DATABASE_URI = get_db_uri(db_info)

    MONGODB_SETTINGS = {
        'db': 'db_ecommerce',
        'host': 'localhost',
        'port': 27017,
        'read_preference': ReadPreference.PRIMARY_PREFERRED,
    }

    ASSETS_DEBUG = True
    # limited the maxiumu allowed payload to 16MB
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024


class TestingConfig(Config):
    """开发环境"""

    db_info = {
        'ENGINE': 'sqlite',
        'DRIVER': '',
        'USER': '',
        'PASSWORD': '',
        'HOST': '',
        'PORT': '',
        'DBNAME': 'db_test_ecommerce'
    }
    SQLALCHEMY_DATABASE_URI = get_db_uri(db_info)

    MONGODB_SETTINGS = {
        'db': 'db_test',
        'host': 'localhost',
        'port': 27017,
    }


class ProductionConfig(Config):
    """开发环境"""
    DEBUG = True
    db_info = {
        'ENGINE': 'mysql',
        'DRIVER': 'pymysql',
        'USER': 'root',
        'PASSWORD': '123456',
        'HOST': 'localhost',
        'PORT': '3306',
        'DBNAME': 'db_product_ecommerce'
    }
    SQLALCHEMY_DATABASE_URI = get_db_uri(db_info)


config = {
    'develop': DevelopConfig,
    'test': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopConfig,
}


def get_config(env, app=''):
    if app == 'worker':
        env = 'production'
    return config.get(env)


def get_config_form_host(app):
    flask_env = os.environ.get('FLASK_ENV', 'develop')
    configure = get_config(flask_env, app)
    return configure
