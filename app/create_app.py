# -*- coding: utf-8  -*-
# @Author: ty
# @File name: create_app.py 
# @IDE: PyCharm
# @Create time: 1/9/21 7:09 PM
# @Description:
from flask import Flask
from werkzeug.middleware.proxy_fix import ProxyFix

from app.init_blueprints import init_blueprints
from app.error_handler import init_error_handlers
from app.init_extensions import init_extensions
from app.init_hook import init_hook
from app.init_log import init_logging
from app.template_filters import init_template_filters


def create_app(config=None, app_name=None, blueprints=None):
    """

    :return:
    """
    if app_name is None:
        app_name = config.Config.PROJECT

    if app_name != config.APP_NAME.work:
        pass
    app = Flask(__name__, static_folder='../static', template_folder='../templates')
    # app.config.from_object(config.get(env))
    # 初始化第三方插件
    configure_app(app, config)
    init_hook(app, app_name)
    init_extensions(app)
    init_blueprints(app, app_name, blueprints)
    init_logging(app)
    init_template_filters(app)
    init_error_handlers(app)
    app.wsgi_app = ProxyFix(app.wsgi_app)
    return app


def configure_app(app, config):
    """

    :param app:
    :param configure:
    :return:
    """
    pass











