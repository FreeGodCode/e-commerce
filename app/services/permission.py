# -*- coding: utf-8  -*-
# @Author: ty
# @File name: permission.py 
# @IDE: PyCharm
# @Create time: 1/23/21 3:36 PM
# @Description:
from flask_login import current_user
from flask_principal import UserNeed, RoleNeed


def principal_on_identity_loaded(sender, identity):
    """

    :param sender:
    :param identity:
    :return:
    """
    # set the identity user object
    identity.user = current_user

    # add the userneed to the identity
    if hasattr(current_user, 'id'):
        identity.provides.add(UserNeed(str(current_user.id)))

    # assuming the user model has a list of roles, update the identity with the roles that the user provides
    if hasattr(current_user, 'roles'):
        for role in current_user.roles:
            identity.provides.add(RoleNeed(role))
