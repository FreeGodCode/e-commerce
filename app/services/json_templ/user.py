# -*- coding: utf-8  -*-
# @Author: ty
# @File name: user.py 
# @IDE: PyCharm
# @Create time: 1/25/21 5:05 PM
# @Description:
from flask_login import current_user

from app.models.order.order_status import OrderStatus


def get_user_info(user):
    """

    :param user:
    :return:
    """
    coin_wallet = user.coin_wallet
    coins = coin_wallet.balance
    cash = coin_wallet.cash
    status = OrderStatus.by_user(user_id=user.id)

    info = dict(
        id=str(user.id),
        name=user.name,
        avatar_url=user.avatar_url,
        avatar_thumb=user.avatar_thumb,
        coins=coins,
        cash=cash,
        consumable_coupons=[c.to_json() for c in user.wallet.consumable_coupons if not c.is_espired],
        num_followers=user.num_followers,
        num_followings=user.num_followings,
        total=status.received,
        num_orders=status.num_orders,
        num_waiting=status.num_waiting,
        num_unpaid=status.num_unpaid,
        num_favors=user.num_favors,
    )
    return info


def user_json(user):
    """

    :param user:
    :return:
    """

    return dict(
        id=str(user.id),
        name=user.name,
        avatar_url=user.avatar_url,
        avatar_thumb=user.avatar_thumb,
        num_followers=user.num_followers,
        num_followings=user.num_followings,
        is_following=current_user.is_following(user) if current_user and current_user.is_authenticated else False,
    )
