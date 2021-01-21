# -*- coding: utf-8  -*-
# @Author: ty
# @File name: user.py 
# @IDE: PyCharm
# @Create time: 1/21/21 5:03 PM
# @Description:
from uuid import uuid4

from flask import Blueprint, jsonify, request, render_template, current_app
from flask_babel import gettext
from flask_login import current_user, login_required
from flask_mail import Message

from app import mail
from app.models.order.order import Order
from app.models.user.user import User
from app.utils.utils import get_session_key, paginate

user = Blueprint('user', __name__, url_prefix='/api/users', static_folder='../../../static',
                 template_folder='../../../templates')


@user.route('/session_key', methods=['GET'])
def session_key():
    """
    获取session key
    :return:
    """
    return jsonify(message='OK', session_key=get_session_key())


@user.route('/permissions', methods=['GET'])
def permissions():
    """
    权限
    :return:
    """
    if not current_user.is_authenticated:
        return jsonify(message='Failed')

    roles = current_user.roles
    return jsonify(message='OK', roles=roles)


@user.route('/coupons/by_entries', methods=['POST'])
@login_required
def coupon_by_entries():
    """
    获取优惠卷
    :return:
    """
    data = request.json
    entry_ids = data.get('entries')
    if not entry_ids:
        return jsonify(message='Failed', error=gettext('please choose the item'))

    entries_info = entry_info_from_ids(entry_ids)

    order = FakeCart(entries_info, user=current_user._get_current_object())

    price = cal_order_price(order)
    c_jsons = []
    for c in current_user.wallet.consumable_coupons:
        if c.is_expired:
            continue
        c_json = c.to_json()
        c_json['can_apply'] = c.coupon.is_effective() and c.coupon.can_apply(price)
        c_json['saving'] = PRICE_FN.ORDER_COUPON[c.coupon.coupon_type](price, c.coupon)[1]
        c_jsons.append(c_json)

    return jsonify(message='OK', consumable_coupons=c_jsons)


@user.route('/coupons/by_order', methods=['POST'])
@login_required
def coupon_by_order():
    """
    通过订单获取优惠卷
    :return:
    """
    data = request.json
    order_id = data.get('order_id')
    if not order_id:
        return jsonify(message='Failed', error=gettext('please choose order'))

    order = Order.objects(id=order_id).first()
    price = cal_order_price(order)
    c_jsons = []
    for c in current_user.wallet.consumable_coupons:
        if c.is_expired:
            continue
        c_json = c.to_json()
        c_json['can_apply'] = c.coupon.is_effective() and c.coupon.can_apply(price)
        c_json['saving'] = PRICE_FN.ORDER_COUPON[c.coupon.coupon_type](price, c.coupon)[1]
        c_jsons.append(c_json)

    return jsonify(message='OK', consumble_coupons=c_jsons)


@user.route('/account/change_password', methods=['POST'])
@login_required
def change_password():
    """
    修改密码
    :return:
    """
    user = current_user
    password = request.json.get('password', '')
    password_confirm = request.json.get('password_confirm', '')
    if not password.isalnum():
        return jsonify(message='Failed', error=gettext('password contains illegal characters'))

    if len(password) < 6:
        return jsonify(message='Failed', error=gettext('password is too short'))

    if password != password_confirm:
        return jsonify(message='Failed', error=gettext('password is inconsistent'))

    user.account.password = password
    user.save()

    return jsonify(message='OK')


@user.route('/account/reset_password', methods=['POST'])
def reset_password():
    """
    重置密码
    :return:
    """
    email = request.json.email
    user = User.objects(account__email=email).first()
    if user:
        user.account.activation_key = str(uuid4())
        user.save()

        url = 'http://m.maybe.cn/account/confirm_reset_password?activation_key=%s&email=%s' % (
            user.account.activation_key, user.account.email)
        html = render_template('admin/user/_reset_password.html', project=current_app.config['PROJECT'],
                               username=user.name, url=url)
        message = Message(subject=gettext('reset your password in ') + 'maybe', html=html,
                          recipients=[user.account.email])
        message.sender = 'thechosenone_ty@163.com'
        mail.send(message)
        return jsonify(message='OK',
                       desc=gettext('please see your email for instructions on how to access your account'))
    else:
        return jsonify(message='Failed', desc=gettext('sorry, not found user for that email address'))


@user.route('/update_avatar', methods=['POST'])
def update_avatar():
    """
    上传头像
    :return:
    """
    path = request.json.get('avatar_url')
    if path:
        url = 'http://assets.maybe.cn/%s' % path
        jobs.image.make_thumbnails('maybe-img', path, url)

        user = current_user._get_current_object()
        user.avatar_url = url
        user.save()
    return jsonify(message='OK', user=json.get_user_info(user))


@user.route('/update_username', methods=['POST'])
@login_required
def update_username():
    """
    更新用户昵称
    :return:
    """
    username = request.json.get('username')
    if username:
        if len(username) > 16:
            return jsonify(message='Failed', error=gettext('username is too long'))
        user = current_user._get_current_object()
        user.name = username
        user.save()
        return jsonify(message='OK', user=json.get_user_info(user))
    return jsonify(message='Failed', error='参数不对')


@user.route('/user_info/<user_id>', methods=['GET'])
def user_info(user_id):
    """
    获取用户信息
    :param user_id:
    :return:
    """
    user = User.objects(id=user_id).first_or_404()
    return jsonify(message='OK', user=json.user_json(user))


@user.route('/follow/<follow_id>', methods=['GET'])
@login_required
def follow(follow_id):
    """

    :param follow_id:
    :return:
    """
    follow_user = User.objects(id=follow_id).first_or_404()
    if follow_user.id == current_user.id:
        return jsonify(message='Failed', error='Can not follow yourself')
    current_user.follow(follow_user)
    return jsonify(message='OK')


@user.route('/unfollow/<follow_id>', methods=['GET'])
@login_required
def unfollow(follow_id):
    """

    :param follow_id:
    :return:
    """
    follow_user = User.objects(id=follow_id).first_or_404()
    current_user.unfollow(follow_user)
    return jsonify(message='OK')


@user.route('/followers', methods=['GET'])
def user_followers():
    """

    :return:
    """
    data = request.args
    user_id = data.get('user_id')
    page = int(data.get('page', 0))
    per_page = int(data.get('per_page', 20))

    user = User.objects(id=user_id).first_or_404()
    followers = user.followers
    users = paginate(followers, page, per_page)
    return jsonify(message='OK', users=[json.user_json(u) for u in users])


@user.route('/followings', methods=['GET'])
def user_followings():
    """

    :return:
    """
    data = request.args
    user_id = data.get('user_id')
    page = int(data.get('page', 0))
    per_page = int(data.get('per_page', 20))

    user = User.objects(id=user_id).first_or_404()
    followings = user.followings
    users = paginate(followings, page, per_page)

    return jsonify(message='OK', users=[json.user_json(u) for u in users])
