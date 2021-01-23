# -*- coding: utf-8  -*-
# @Author: ty
# @File name: cart.py 
# @IDE: PyCharm
# @Create time: 1/23/21 3:19 AM
# @Description: 购物车
from flask import Blueprint, jsonify, session, request
from flask_login import user_logged_in, current_user

from app.models.user.guest import GuestRecord
from app.utils.utils import get_session_key

cart = Blueprint('cart', __name__, url_prefix='/api/cart', static_folder='../../../static',
                 template_folder='../../../templates')


@user_logged_in.connect
def combine_cart(sender, user):
    """
    合并购物车
    :param sender:
    :param user:
    :return:
    """
    merge_carts(session_key_from=session.sid, user_id_to=str(user.id))


@user_logged_in.connect
def combine_favor_items(sender, user):
    """

    :param sender:
    :param user:
    :return:
    """
    guest_record = GuestRecord.by_key(key=get_session_key())
    current_user.favor_items = list(set(current_user.favor_items + guest_record.favor_items))
    current_user.num_favors = len(current_user.favor_items)
    current_user.save()


def get_user_id_for_cart():
    """

    :return:
    """
    if current_user.is_authenticated:
        user_id = str(current_user.id)
        session_key = None
    else:
        user_id = None
        session_key = session.sid
    return user_id, session_key


@ cart.route('/', methods=['GET'])
def check_cart():
    """

    :return:
    """
    user_id, session_key = get_user_id_for_cart()
    cart = get_cart(user_id, session_key)
    return jsonify(message='OK', cart=cart)

@cart.route('/add/<int:spec_id>', methods=['POST'])
def add_cart(spec_id):
    """

    :param spec_id:
    :return:
    """
    user_id, session_key = get_user_id_for_cart()
    quantity = int(request.json.get('quantity', 1))
    res = update_cart_entry(spec_id, quantity, incr_quantity=False, uses_id=user_id, session_key=session_key)
    return jsonify(message='OK', cart=res)


@cart.route('/entry/delete', methods=['POST'])
def remove_entries_from_cart():
    """

    :return:
    """
    user_id, session_key = get_user_id_for_cart()
    skus = request.json.get('skus', '[]')
    res = remove_from_cart(skus, user_id, session_key)
    return jsonify(message='OK', cart=res)

@cart.route('/entry/<int:entry_id>/update', methods=['POST'])
def update_entry(entry_id):
    """

    :param entry_id:
    :return:
    """
    quantity = int(request.json.get('quantity', 1))
    user_id, session_key = get_user_id_for_cart()
    res = update_cart_entry(entry_id, quantity, incr_quantity=False, user_id=user_id, session_key=session_key)
    return jsonify(message='OK', cart=res)

@cart.route('/empty', methods=['GET'])
def cart_empty():
    """

    :return:
    """
    user_id, session_key = get_user_id_for_cart()
    res = empty_cart(user_id, session_key)
    return jsonify(message='OK', cart=res)
