# -*- coding: utf-8  -*-
# @Author: ty
# @File name: extensions.py 
# @IDE: PyCharm
# @Create time: 1/6/21 10:54 PM
# @Description:
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy

# 数据库
db = SQLAlchemy()
# 数据库迁移
migrate = Migrate()


def init_extensions(app):
    """
    初始化第三方插件
    :return:
    """
    db.init_app(app)
    migrate.init_app(app, db)
