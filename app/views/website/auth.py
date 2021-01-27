# -*- coding: utf-8  -*-
# @Author: ty
# @File name: auth.py 
# @IDE: PyCharm
# @Create time: 1/21/21 11:24 PM
# @Description:

import time
from uuid import uuid4

from flask import Blueprint, current_app, jsonify, request, render_template
from flask_babel import gettext
from flask_login import current_user, logout_user, login_user, login_required

from app.config.settings import SOCIALOAUTH_SITES
from app.models.user.user import SocialOAuth, User
from app.services import jobs, json_templ
from app.services.cache import cached
from app.services.user import add_oauth

auth = Blueprint('auth', __name__, url_prefix='/api/auth', static_folder='../../../static', template_folder='../../../templates')


def get_oauth_token(sitename, code):
    """

    :param sitename:
    :param code:
    :return:
    """
    if not code or code == 'authdeny':
        return None, 'NO CODE'

    socialsites = SocialSites(SOCIALOAUTH_SITES)
    site = socialsites.get_site_object_by_name(sitename)
    try:
        site.get_access_token(code)
    except SocialAPIError as e:
        current_app.logger.error('SocialAPIError. sitename: {}; url: {}; msg: {}'.format(e.site_name, e.url, e.error_msg))
        return None, e.error_msg
    else:
        return site, ''


def parse_token_response(sitename, data):
    """
    解析token
    :param sitename:
    :param data:
    :return:
    """
    socialsites = SocialSites(SOCIALOAUTH_SITES)
    site = socialsites.get_site_object_by_name(sitename)
    try:
        site.parse_token_response(data)
    except SocialAPIError as e:
        current_app.logger.error('SocialAPIError. sitename: {}; url: {}; msg: {}'.format(e.site_name, e.url, e.error_msg))
        return None, e.error_msg
    else:
        return site, ''


@auth.route('/user_info', methods=['GET'])
def user_info():
    """

    :return:
    """
    if not current_user.is_authenticated:
        return jsonify(message='Failed', logged_in=False)

    info = json_templ.get_user_info(current_user)
    return jsonify(message='OK', logged_in=True, user=info)


@auth.route('/logout', methods=['GET'])
def logout():
    """

    :return:
    """
    if current_user.is_authenticated:
        logout_user()
    return jsonify(message='OK')


@auth.route('/oauth/links', methods=['GET'])
@cached(21600)
def oauth_links():
    """
    认证链接
    :return:
    """
    def _link(site_class):
        _s = socialsites.get_site_object_by_name(site_class)
        a_content = _s.site_name
        return (_s.authorize_url, a_content)

    socialsites = SocialSites(SOCIALOAUTH_SITES)
    links = map(_link, ['wechat', 'weibo', 'facebook'])
    return jsonify(message='OK', links=list(links))


@auth.route('/oauth/<sitename>', methods=['GET'])
def callback(sitename):
    """
    OAuth认证
    :param sitename:
    :return:
    """
    if sitename in ['weibo_app', 'qq_app', 'facebook_app']:
        site, msg = parse_token_response(sitename, request.args)
        app = 'IOS'
    else:
        code = request.args.get('code')
        site, msg = get_oauth_token(sitename, code)
        app = sitename != 'wechat_app' and 'MOBILEWEB' or 'IOS'

    if site is None:
        return jsonify(message='Failed', error=msg)

    if sitename in ['wechat', 'wechat_app']:
        oauth = SocialOAuth.objects(unionid=site.unionid).first()
    else:
        oauth = SocialOAuth.objects(site_uid=site.uid).first()

    if not oauth:
            oauth = SocialOAuth.create(site.site_name, site.uid, site.name, site.access_token, site.expires_in, site.refresh_token, app=app, unionid=getattr(site, 'unionid', None), gender=site.gender)
            path = 'avatar/{}/{}.jpeg'.format(oauth.user.id, str(time.time()).replace('.', ''))
            jobs.image.save_avatar('maybe-img', path, url=site.avatar_large, save_original=True)
            url = 'http://assets.maybe.cn/%s' % path
            oauth.update_avatar(url)
            user_id = str(oauth.user.id)
            login_user(oauth.user, remember=True)
            return jsonify(message='OK', login=False, user_id=user_id)
    else:
        oauth.re_auth(site.access_token, site.expires_in, site.refresh_token, getattr(site, 'unionid', None))
        if oauth.user.account.is_email_verified:
            login_user(oauth.user, remember=True)
            return jsonify(message='OK', login=True, remember_token=oauth.user.generate_auth_token(), user=json_templ.get_user_info(oauth.user))

        else:
            user_id = str(oauth.user.id)
            return jsonify(message='OK', login=False, user_id=user_id)


@auth.route('/login_email', methods=['POST'])
def login_email():
    """

    :return:
    """
    data = request.json
    email = data.get('email', '')
    user, authenticated = User.authenticate(email=email, password=data.get('password', ''))
    if not authenticated:
        return jsonify(message='Failed')
    login_user(user, remember=True)
    return jsonify(message='OK', user=json_templ.get_user_info(user), remember_token=user.generate_auth_token())


@auth.route('/login_with_token', methods=['POST'])
def login_with_token():
    """

    :return:
    """
    data = request.json
    token = data.get('token', '')
    user = User.verify_auth_token(token)
    if not user:
        return jsonify(message='Failed')
    login_user(user, remember=True)
    return jsonify(message='OK', user=json_templ.get_user_info(user), remember_token=user.generate_auth_token())


@auth.route('/add_oauth/<sitename>', methods=['GET'])
@login_required
def add_another_oauth(sitename):
    """

    :param sitename:
    :return:
    """
    user = current_user._get_current_object()
    # 已存在
    if SocialOAuth.objects(user=user, site=sitename):
        return jsonify(message='Failed', error=gettext('multi oauth of same site'))
    if '_app' in sitename:
        site, msg = parse_token_response(sitename, request.args)
    else:
        code = request.args.get('code')
        sitename, msg = get_oauth_token(sitename, code)

    if site is None:
        return jsonify(message='Failed', error=msg)

    oauth = SocialOAuth.objects.get_or_create(site_uid=site.id, site=site.site_name, defaults={'access_token': site.access_token})
    oauth.re_auth(site.access_token, site.expires_in, site.refresh_token)
    add_oauth(current_user, oauth)
    return jsonify(message='OK')


@auth.route('/signup', methods=['POST'])
def email_signup():
    """
    邮箱注册
    :return:
    """
    data = request.json
    name = data.get('name')
    email = data.get('email', '')
    password = data.get('password', '')
    if not password:
        return jsonify(message='Failed', error=gettext('please fill in.'))
    if User.objects(account__email=email):
        return jsonify(message='Failed', error=gettext('this name has been registered.'))
    if not name:
        name = 'maybe' + str(time.time()).replace('.', '')
    user = User.create(name=name, email=email, password=password)
    login_user(user, remember=True)
    return jsonify(message='OK', user=json_templ.get_user_info(user), remember_token=user.generate_auth_token())


@auth.route('/bind_email', methods=['POST'])
def bind_email():
    """

    :return:
    """
    email = request.json.get('email')
    user_id = request.json.get('user_id')
    if not email:
        return jsonify(message='Failed', error=gettext('no email'))
    if User.objects(account__email=email):
        return jsonify(message='Failed', error=gettext('the email alreadly exists'))
    user = User.objects(id=user_id).first()
    user.account.email = email
    user.account.is_email_verified = True
    user.save()
    login_user(user, remember=True)
    return jsonify(message='OK', user=json_templ.get_user_info(user), remember_token=user.generate_auth_token())


@auth.route('/change_password', methods=['POST'])
@login_required
def change_password():
    """

    :return:
    """
    original_password = request.json.get('original_password', '')
    user = current_user._get_current_object()
    if not user.account.check_password(original_password):
        return jsonify(message='Failed', error=gettext('wrong password'))

    password = request.form.get('password', '')
    if not password.isalnum():
        return jsonify(message='Failed', error=gettext('password contains illegal characters'))
    if len(password) < 6:
        return jsonify(message='Failed', error=gettext('password is too short'))
    update_password(user, password)
    return jsonify(message='OK')


@auth.route('/forget_password', methods=['POST'])
def forget_password():
    """

    :return:
    """
    email = request.json.get('email', '')
    if not email:
        return jsonify(message='Failed', error=gettext('please correct the email format'))

    user = User.objects(account__email=email).first()
    if not user:
        return jsonify(message='Failed', error=gettext('sorry, no user found for that email address'))

    user.account.activation_key = str(uuid4())
    user.save()
    url = 'http://account.maybe.cn/account/confirm_reset_password?activation_key=%s&email=%s' % (user.account.activation_key, user.account.email)
    html = render_template('admin/user/_reset_password.html', username=user.name, url=url)
    jobs.notification.send_mail.delay([user.account.email], gettext('reset your password in ') + 'maybe', html=html)
    return jsonify(message='OK')

