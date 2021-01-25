# -*- coding: utf-8  -*-
# @Author: ty
# @File name: frontend.py 
# @IDE: PyCharm
# @Create time: 1/23/21 10:55 PM
# @Description:
from flask_wtf import Form
from flask import Markup
from wtforms import HiddenField, PasswordField, SubmitField, BooleanField, TextField
from wtforms.fields.html5 import EmailField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError

from app.models.user.user import User
from app.utils.utils import PASSWORD_LEN_MAX, PASSWORD_LEN_MIN, USERNAME_LEN_MIN, USERNAME_LEN_MAX


class LoginForm(Form):
    """登录表单"""
    next = HiddenField()
    login = TextField('username or email', [DataRequired()])
    password = PasswordField('password', [DataRequired(), Length(PASSWORD_LEN_MIN, PASSWORD_LEN_MAX)])
    submit = SubmitField('sign in ')


class SignupForm(Form):
    """注册表单类"""
    # pass
    next = HiddenField()
    email = EmailField('email', [DataRequired(), Email()], description='your email address')
    password = PasswordField('password', [DataRequired(), Length(PASSWORD_LEN_MIN, PASSWORD_LEN_MAX)], description='%s characters or more! be tricky. ' % PASSWORD_LEN_MIN)
    name = TextField('username', [DataRequired(), Length(USERNAME_LEN_MIN, USERNAME_LEN_MAX)], description='dont worry. you can change it later.')
    agree = BooleanField('agree to the' + Markup('<a target="blank" href="/terms"> terms of service</a>'), [DataRequired()])
    submit = SubmitField('sign up')

    def validate_name(self, field):
        if User.objects(name=field.data).first() is not None:
            raise ValidationError('此用户名已存在')

    def validate_email(self, field):
        if User.objects(account__email=field.data).first() is not None:
            raise ValidationError('此邮箱已被注册')


class RecoverPasswordForm(Form):
    """恢复密码表单类"""
    # pass
    email = EmailField('your email', [Email()])
    submit = SubmitField('send instructions')


class ChangePasswordForm(Form):
    """修改密码表单类"""
    # pass
    password = PasswordField('password', [DataRequired()])
    password_again = PasswordField('password again', [EqualTo('password', message='password dont match')])
    submit = SubmitField('save')


class ConfirmResetPasswordForm(Form):
    """确认重置密码表单类"""
    # pass
    activation_key = HiddenField()
    email = HiddenField()
    password = PasswordField('password', [DataRequired()])
    password_again = PasswordField('password again', [EqualTo('password', message='password dont match')])


class ReauthForm(Form):
    """再认证表单类"""
    next = HiddenField()
    password = PasswordField('password', [DataRequired(), Length(PASSWORD_LEN_MIN, PASSWORD_LEN_MAX)])
    submit = SubmitField('reauthenticate')