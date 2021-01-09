# -*- coding: utf-8  -*-
# @Author: ty
# @File name: error_handler.py 
# @IDE: PyCharm
# @Create time: 1/9/21 6:05 PM
# @Description:
from flask import jsonify
from flask_babel import gettext
from flask_principal import PermissionDenied


def init_error_handlers(app):
    """
    初始化异常处理
    :param app:
    :return:
    """

    @app.errorhandler(PermissionDenied)
    def permission_error(error):
        """
        permission denied exception
        :param error:
        :return:
        """
        return jsonify(msg='Failed', code=403, error=gettext('Permission Denied'))

    @app.errorhandler(401)
    def login_required_page(error):
        """
        登录要求
        :param error:
        :return:
        """
        return jsonify(msg='Failed', code=403, error=gettext('Login required'))

    @app.errorhandler(404)
    def page_not_found(error):
        """
        页面不存在
        :param error:
        :return:
        """
        return jsonify(msg='Failed', code=404, error=gettext('Page not found'))

    @app.errorhandler(500)
    def server_error_page(error):
        """
        服务器内部错误
        :param error:
        :return:
        """
        return jsonify(msg='Failed', code=500, error=gettext('Internal Server error'))
