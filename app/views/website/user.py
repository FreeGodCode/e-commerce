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
from app.utils.utils import get_session_key

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

        url = 'http://m.maybe.cn/account/confirm_reset_password?activation_key=%s&email=%s' % (user.account.activation_key, user.account.email)
        html = render_template('admin/user/_reset_password.html', project=current_app.config['PROJECT'], username=user.name, url=url)
        message = Message(subject=gettext('reset your password in ') + 'maybe', html=html, recipients=[user.account.email])
        message.sender = 'thechosenone_ty@163.com'
        mail.send(message)
        return jsonify(message='OK', desc=gettext('please see your email for instructions on how to access your account'))
    else:
        return jsonify(message='Failed', desc=gettext('sorry, not found user for that email address'))
