# -*- coding: utf-8  -*-
# @Author: ty
# @File name: frontend.py 
# @IDE: PyCharm
# @Create time: 1/23/21 10:55 PM
# @Description:
from flask_wtf import Form
from wtforms import HiddenField, TextField, PasswordField, SubmitField
from wtforms.fields.html5 import EmailField
from wtforms.validators import DataRequired, Length, Email, EqualTo

from app.utils.utils import PASSWORD_LEN_MAX, PASSWORD_LEN_MIN


class LoginForm(Form):
    """登录表单"""
    next = HiddenField()
    login = TextField('username or email', [DataRequired()])
    password = PasswordField('password', [DataRequired(), Length(PASSWORD_LEN_MIN, PASSWORD_LEN_MAX)])
    submit = SubmitField('sign in ')


class SignupForm(Form):
    """注册表单"""
    # pass
    email = EmailField('your email', [Email()])
    submit = SubmitField('send instructions')


class RecoverPasswordForm(Form):
    """恢复密码表单类"""
    # pass
    password = PasswordField('password', [DataRequired()])
    password_again = PasswordField('password again', [EqualTo('password', message='password dont match')])
    submit = SubmitField('save')


class ChangePasswordForm(Form):
    """修改密码表单类"""
    # pass
    activation_key = HiddenField()
    email = HiddenField()
    password = PasswordField('password', [DataRequired()])
    password_again = PasswordField('password again', [EqualTo('password', message='password dont match')])


class ConfirmResetPasswordForm(Form):
    """确认重置密码表单类"""
    # pass
    next = HiddenField()
    password = PasswordField('password', [DataRequired(), Length(PASSWORD_LEN_MIN, PASSWORD_LEN_MAX)])
    submit = SubmitField('reauthenticate')
