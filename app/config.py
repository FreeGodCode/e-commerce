# -*- coding: utf-8  -*-
# @Author: ty
# @File name: config.py 
# @IDE: PyCharm
# @Create time: 1/6/21 11:55 PM
# @Description:配置文件设置
import os

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


class Config:
    DEBUG = False
    SECRET_KEY = 'tycarry'
    SQLALCHEMY_TRACK_MODIFICATIONS = False



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


class ProductConfig(Config):
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
    'product': ProductConfig,
    'default': DevelopConfig,
}
