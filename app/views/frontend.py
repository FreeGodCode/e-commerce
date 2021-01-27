# -*- coding: utf-8  -*-
# @Author: ty
# @File name: frontend.py 
# @IDE: PyCharm
# @Create time: 1/18/21 10:25 PM
# @Description:
import os
import uuid

from flask import Blueprint, url_for, redirect, make_response, request, jsonify, flash, render_template, current_app, \
    session, Response
from flask_admin.menu import MenuLink
from flask_babel import gettext
from flask_login import current_user, login_user, confirm_login, login_required, logout_user, login_fresh, \
    fresh_login_required
from mongoengine import Q

from app import login_manager, admin
from app.config import BASE_DIR
from app.models.user.user import User
from app.services import jobs
from app.services.forms import ReauthForm, ConfirmResetPasswordForm, ChangePasswordForm, RecoverPasswordForm
from app.views.admin import AuthenticatedMenuLink, NotAuthenticatedMenuLink

frontend = Blueprint('frontend', __name__, url_prefix='', static_folder='../static',
                     template_folder='../templates')

TEMPLATE_DIR = os.path.join(BASE_DIR, '../../templates')


def redirect_next():
    """
    页面重定向
    :return:
    """
    return redirect(url_for('admin.index'))


@frontend.route('/', methods=['GET'])
def index():
    """
    首页
    :return:
    """
    return make_response(open(os.path.join(TEMPLATE_DIR, 'index.html')).read())


@frontend.route('/api/v1/apps/<appid>/updates/check/', methods=['POST'])
@frontend.route('/api/v1/apps/<appid>/updates/check/<uuid>', methods=['POST'])
def app_update(appid, uuid=None):
    """
    application update
    :param appid:
    :param uuid:
    :return:
    """
    uuid = '1.1.0'
    device_app_version = request.json.get('device_app_version')
    update_available = True
    if float(device_app_version.replace('.', '')) >= float(uuid.replace('.', '')):
        update_available = False

    res = {'compatible_binary': True, 'update_available': update_available,
           'update': {'uuid': uuid, 'url': 'http://127.0.0.1:5000/api/update/get/www_%s.zip' % uuid}}
    return jsonify(res)


@frontend.route('/api/update/get/<filename>', methods=['GET'])
def get_file(filename):
    """
    获取文件 zip格式
    :param filename:
    :return:
    """
    return make_response(open(os.path.join(TEMPLATE_DIR, filename)).read())


@frontend.route('/account/oauth/<sitename>', methods=['GET'])
def oauth(sitename):
    """

    :param sitename:
    :return:
    """
    code = request.args.get('code')
    return redirect('http://m.maybe.cn/#/account/oauth/%s?code=%s' % (sitename, code))


@frontend.route('/admin/login', methods=['GET', 'POST'])
def login():
    """
    登录
    :return:
    """
    if request.user_agent.platform in ['ipad', 'iphone', 'android']:
        return jsonify(error='请先登录')
    # 用户验证通过直接跳转到首页
    if current_user.is_authenticated:
        return redirect_next()
    if request.method == 'POST':
        email = request.form.get('email', None)
        password = request.form.get('password', None)
        if email and password:
            user, authenticated = User.authenticate(email=email, password=password)
        else:
            flash(gettext('please enter the correct email and password.'))
            return redirect_next()

        if user and authenticated:
            # remember = request.form.get('remember') == 'y'
            remember = True
            login_user(user, remember)
        else:
            flash('帐号或密码不正确')

        return redirect_next()

    return render_template('admin/user/login.html')


@frontend.route('/admin/reauth', methods=['GET', 'POST'])
def reauth():
    """
    重新授权(确认)
    :return:
    """
    form = ReauthForm(next=request.args.get('next'))

    if request.method == 'POST':
        user, authenticated = User.authenticate(email=current_user.email, password=form.password.data)
        if user and authenticated:
            confirm_login()
            current_app.logger.debug('reauth: %s' % session['_fresh'])
            flash(gettext('Reauthenticated.'), 'success')
            return redirect('frontend.change_password')

        flash(gettext('password is wrong.'), 'error')

    return render_template('admin/user/reauth.html', form=form)


@frontend.route('/admin/logout')
@login_required
def logout():
    """
    退出
    :return:
    """
    logout_user()
    return redirect(url_for('frontend.login'))


@frontend.route('/admin/signup', methods=['GET', 'POST'])
def signup():
    """
    注册
    :return:
    """
    return redirect(url_for('frontend.signup'))


@frontend.route('/admin/confirm_reset_password', methods=['GET', 'POST'])
@frontend.route('/account/confirm_reset_password', methods=['GET', 'POST'])
def confirm_reset_password():
    """
    确认密码
    :return:
    """
    if request.method == 'GET':
        if current_user.is_authenticated:
            if not login_fresh():
                return login_manager.needs_refresh()
            user = current_user
        elif 'activation_key' in request.args and 'email' in request.args:
            activation_key = request.args.get('activation_key')
            email = request.args.get('email')
            user = User.objects(Q(account__activation_key=activation_key) & Q(account__email=email)).first()
        else:
            return Response('邮件已失效')

        form = ConfirmResetPasswordForm(activation_key=user.account.activation_key, email=user.account.email)
        return render_template('admin/user/confirm_reset_password.html', form=form)
    if request.method == 'POST':
        form = ConfirmResetPasswordForm()
        activation_key = form.activation_key.data
        email = form.email.data
        user = User.objects(Q(account__activation_key=activation_key) & Q(account__email=email)).first()
        # 修改密码成功
        if form.validate_on_submit():
            user.account.password = form.password.data
            user.account.activation_key = None
            user.save()
            flash(gettext('your password has been changed, please login again'), 'success')
            return render_template('admin/user/success_reset_password.html')
        # 修改密码失败
        flash(gettext('fail, please confirm your password'), 'success')
        return render_template('admin/user/confirm_reset_password.html', form=form)


@frontend.route('/admin/change_password', methods=['GET', 'POST'])
def change_password():
    """
    修改密码
    :return:
    """
    user = current_user
    form = ChangePasswordForm()
    if form.validate_on_submit():
        user.account.password = form.password.data
        user.save()

        logout_user()
        flash(gettext('your password has been changed, please login again.'), 'success')
        return redirect(url_for('frontend.login'))
    return render_template('admin/user/change_password.html', form=form)


@frontend.route('/admin/reset_password', methods=['GET', 'POST'])
def reset_password():
    """
    重置密码
    :return:
    """
    form = RecoverPasswordForm()
    if form.validate_on_submit():
        user = User.objects(account__email=form.email.data).first()
        if user:
            flash(gettext('please see your email for instructions on how to access your account'), 'success')
            user.account.activation_key = str(uuid.uuid4())
            user.save()

            # send recover password html
            # TODO: change project name
            url = 'http://bigbang.maybe.cn/admin/confirm_reset_password?activation_key=%s&email=%s'%(user.account.activation_key, user.account.email)
            html = render_template('admin/user/_reset_password.html', project=current_app.config['PROJECT'], username=user.name, url=url)
            jobs.notification.send_mail.delay([user.account.email], gettext('reset your password in ') + 'Maybe', html)
            return render_template('admin/user/reset_password.html', form=form)
        else:
            flash(gettext('sorry, no user found for that email address'), 'error')

    return render_template('admin/user/reset_password.html', form=form)


@frontend.route('/admin/secret')
@fresh_login_required
def secret():
    """
    保密
    :return:
    """
    if current_user.is_authenticated:
        print(current_user)
    return jsonify(success='OK')


admin.add_link(MenuLink(name='Home', url='/admin'))
admin.add_link(NotAuthenticatedMenuLink(name='Login', endpoint='frontend.login'))
admin.add_link(AuthenticatedMenuLink(name='Logout', endpoint='frontend.logout'))
admin.add_link(AuthenticatedMenuLink(name='Change Password', endpoint='frontend.change_password'))