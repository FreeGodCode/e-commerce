# -*- coding: utf-8  -*-
# @Author: ty
# @File name: __init__.py.py 
# @IDE: PyCharm
# @Create time: 1/18/21 10:24 PM
# @Description:
import datetime

from flask import url_for, redirect, request
from flask_admin import BaseView
from flask_admin.contrib.mongoengine import ModelView

from flask_admin.menu import MenuLink
from flask_login import current_user

from app.models.permission.permission import BackendPermission
from app.utils.utils import format_date


class Roled(object):
    """角色"""

    def is_accessible(self):
        """
        是否验证通过
        :return:
        """
        roles_accepted = getattr(self, '_permission', 'admin')
        m = BackendPermission.objects(name=roles_accepted).first()
        if 'ADMIN' in current_user.roles:
            return True
        if m.roles:
            accessible = any([role in current_user.roles for role in m.roles])
            return accessible
        return False

    def _handle_view(self, name, *args, **kwargs):
        """

        :param name:
        :param args:
        :param kwargs:
        :return:
        """
        # 未验证或验证不通过
        if not current_user.is_authenticated or not self.is_accessible():
            return redirect(url_for('frontend.login', next=url_for(self.endpoint + '.' + name, **request.args)))


class AdminView(Roled, BaseView):
    """管理"""
    pass


class PermissionModelView(Roled, ModelView):
    """权限模型视图"""

    def __init__(self, *args, **kwargs):
        self._permission = kwargs.pop('permission', 'admin')
        return super(PermissionModelView, self).__init__(*args, **kwargs)


class MBModelView(PermissionModelView):
    """"""
    column_type_formatters = {datetime.datetime: lambda view, value: format_date(value)}


class PermissionMenuLink(Roled, MenuLink):
    """权限菜单链接"""

    def __init__(self, *args, **kwargs):
        self.permission = kwargs.pop('permission', 'admin')
        return super(PermissionMenuLink, self).__init__(*args, **kwargs)


class AuthenticatedMenuLink(MenuLink):
    """验证菜单链接"""

    def is_accessible(self):
        """
        是否验证通过
        :return: 已验证
        """
        return current_user.is_authenticated


class NotAuthenticatedMenuLink(MenuLink):
    """未验证菜单链接"""

    def is_accessible(self):
        """
        是否验证通过
        :return: 未进行验证
        """
        return not current_user.is_authenticated
