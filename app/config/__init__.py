# -*- coding: utf-8  -*-
# @Author: ty
# @File name: config.py 
# @IDE: PyCharm
# @Create time: 1/6/21 11:55 PM
# @Description:配置文件设置
import os
import datetime

from blinker import Namespace
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
    PROJECT = APP_NAME.maybe
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

    SESSION_COOKIE_DOMAIN = '.maybe.cn'
    SERVER_NAME = 'maybe.cn'
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
            'schedule': crontab(minute=0, hour='*/8'),
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

namespace = Namespace()
notification = namespace.signal('noti')

# user actions
user_signup = namespace.signal('user_signup')
ref_visit = namespace.signal('ref_visit')
item_visit = namespace.signal('item_visit')
item_bought = namespace.signal('item_bought')
coupon_received = namespace.signal('coupon_received')

# system notification
# 购物车
cart_changed = namespace.signal('cart_changed')
payment_received = namespace.signal('payment_received')

# model events
# 订单
order_created = namespace.signal('order_created')
order_finished = namespace.signal('order_finished')

order_logistic_status_changed = namespace.signal('order_logistic_status_changed')
logistic_status_changed = namespace.signal('logistic_status_changed') # 物流状态该变
logistic_auto_splitted = namespace.signal('logistic_auto_splitted') # 物流自动


order_status_changed = namespace.signal('order_status_changed') # 订单状态改变
logistic_info_updated = namespace.signal('logistic_info_updated') # 物流信息更新

express_tracking_updated = namespace.signal('express_tracking_updated')


UEDITOR_CONFIG = {
    'imageActionName': 'uploadimage',
    'imageFieldName': 'upfile',
    'imageMaxSize': 2048000,
    'imageAllowFiles': ['.png', '.jpg', '.jpeg', '.gif', '.bmp'],
    'imageCompressEnable': True,
    'imageCompressBorder': 1600,
    'imageInsertAlign': 'none',
    'imageUrlPrefix': '',
    'imagePathFormat': '/ueditor/php/upload/image/{yyyy}{mm}{dd}/{time}{rand:6}',

    'scrawlActionName': 'uploadscrawl',
    'scrawlFieldName': 'upfile',
    'scrawlPathFormat': '/ueditor/php/upload/image/{yyyy}{mm}{dd}/{time}{rand:6}',
    'scrawlMaxSize': 2048000,
    'scrawlUrlPrefix': '',
    'scrawlInsertAlign': 'none',

    'snapscreenActionName': 'uploadimage',
    'snapscreenPathFormat': '/ueditor/php/upload/image/{yyyy}{mm}{dd}/{time}{rand:6}',
    'snapsereenUrlPrefix': '',
    'snapscreenInsertAlign': 'none',

    'catcherLocalDomain': ['127.0.0.1', 'localhost', 'img.baidu.com'],
    'catcherActionName': 'catchimage',
    'catcherFieldName': 'source',
    'catcherPathFormat': '/ueditor/php/upload/image/{yyyy}{mm}{dd}/{time}{rand:6}',
    'catcherUrlPrefix': '',
    'catcherMaxSize': 2048000,
    'catcheraAllowFiles': ['.png', '.jpg', '.jpeg', '.gif', '.bmp'],

    'videoActionName': 'uploadvideo',
    'videoFileName': 'upfile',
    'videoPathFormat': '/ueditor/php/upload/video/{yyyy}{mm}{dd}/{time}{rand:6}',
    'videoUrlPrefix': '',
    'videoMaxSize': 102400000,
    'videoAllowFiles': ['.flv', '.swf', '.mkv', '.avi', '.rm', '.rmvb', '.mpeg', '.mpg', '.ogg', '.ogv', '.mov', '.wmv', '.mp4', '.webm', '.mp3', '.wav', '.mid'],

    'fileActionName': 'uploadfile',
    'fileFieldName': 'upfile',
    'filePathFormat': '/ueditor/php/upload/file/{yyyy}{mm}{dd}/{time}{rand:6}',
    'fileUrlPrefix': '',
    'fileMaxSize': 51200000,
    'fileAllowFiles': ['.png', '.jpg', '.jpeg', '.gif', '.bmp', '.flv', '.swf', '.mkv', '.avi', '.rm', '.rmvb', '.mpeg', '.mpg', '.ogg', '.ogv', '.mov', 'wmv', '.mp4', '.webm', '.mp3', '.wav', '.mid', '.rar', '.zip', '.rar', '.zip', '.tar', '.gz', '.7z', '.bz2', '.cab', '.iso', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx', '.pdf', '.txt', '.md', '.xml'],

    'imageManagerActionName': 'listimage',
    'imageManagerListPath': '/ueditor/php/upload/image/',
    'imageManagerListSize': 20,
    'imageManagerUrlPrefix': '',
    'imageManagerInsertAlign': 'none',
    'imageManagerAllowFiles': ['.png', '.jpg', '.jpeg', '.gif', '.bmp'],

    'fileManagerActionName': 'listfile',
    'fileManagerListPath': '/ueditor/php/upload/file/',
    'fileManagerUrlPrefix': '',
    'fileManagerListSize': 20,
    'fileManagerAllowFiles': ['.png', '.jpg', '.jpeg', '.gif', '.bmp', '.flv', '.swf', '.mkv', '.avi', '.rm', '.rmvb', '.mpeg', '.mpg', '.ogg', '.ogv', '.mov', '.wmv', '.mp4', '.webm', '.mp3', '.wav', '.mid', '.rar', '.zip', '.tar', '.gz', '.7z', '.bz2', '.cab', '.iso', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx', '.pdf', '.txt', '.md', '.xml'],
}