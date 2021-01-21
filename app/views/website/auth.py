# -*- coding: utf-8  -*-
# @Author: ty
# @File name: auth.py 
# @IDE: PyCharm
# @Create time: 1/21/21 11:24 PM
# @Description:
import time

from flask import Blueprint, current_app, jsonify, request
from flask_login import current_user, logout_user, login_user

from app.config.settings import SOCIALOAUTH_SITES
from app.models.user.user import SocialOAuth

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

    info = json.get_user_info(current_user)
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
            return jsonify(message='OK', login=True, remember_token=oauth.user.generate_auth_token(), user=json.get_user_info(oauth.user))

        else:
            user_id = str(oauth.user.id)
            return jsonify(message='OK', login=False, user_id=user_id)
