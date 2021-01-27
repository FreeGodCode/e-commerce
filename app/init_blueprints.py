# -*- coding: utf-8  -*-
# @Author: ty
# @File name: init_blueprints.py
# @IDE: PyCharm
# @Create time: 1/9/21 7:10 PM
# @Description:
from app import views


def init_blueprints(app, app_name, blueprints):
    """
    initial blueprints in views.
    :param app:
    :param app_name:
    :param blueprints:
    :return:
    """
    if app_name == ConfigsModel.APP_NAME.worker:
        return

    if app_name == ConfigModel.APP_NAME.maybe:
        blueprints = views.default_blueprints
    elif app_name == ConfigModel.APP_NAME.admin:
        blueprints = [views.frontend.frontend]
    else:
        blueprints = views.default_blueprints

    if blueprints:
        for blueprint in blueprints:
            app.register_blueprint(blueprint)