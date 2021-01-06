# -*- coding: utf-8  -*-
# @Author: ty
# @File name: __init__.py.py 
# @IDE: PyCharm
# @Create time: 1/6/21 10:49 PM
# @Description:
from flask import Flask

from app.config import config
from app.extensions import init_extensions


def create_app(env):
    """

    :return:
    """
    app = Flask(__name__)
    app.config.from_object(config.get(env))
    # 初始化第三方插件
    init_extensions(app)

    return app
