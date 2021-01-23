# -*- coding: utf-8  -*-
# @Author: ty
# @File name: cart.py 
# @IDE: PyCharm
# @Create time: 1/23/21 3:35 PM
# @Description:
import datetime
from collections import Counter

from app.models.cart.cart import Cart, CartEntry, EntrySpec


def _get_cart(user_id, session_key):
    """
    获取购物车
    :param user_id:
    :param session_key:
    :return:
    """
    if user_id:
        cart = Cart.objects(user_id=user_id).modify(upsert=True, new=True, set__user_id=user_id)
    elif session_key:
        cart = Cart.objects(session_key=session_key).modify(upsert=True, new=True, set__session_key=session_key)
    return cart


def _cart_specs_info(cart):
    """
    购物车信息
    :param cart:
    :return:
    """
    return get_specs_info([entry.sku for entry in cart.entries])


def _new_entry(sku, quantity, cart):
    """

    :param sku:
    :param quantity:
    :param cart:
    :return:
    """
    now = datetime.datetime.utcnow()
    return CartEntry(sku=sku, quantity=quantity, created_at=now)


def _remove_cart_from_spec(sku, cart_id):
    """

    :param sku:
    :param cart_id:
    :return:
    """
    cart = Cart.objects(id=cart_id).first()
    if sku in (entry.sku for entry in cart.entries):
        return
    EntrySpec.objects(sku=sku).update_one(pull__carts=cart)
    spec = EntrySpec.objects(sku=sku).first()
    if spec and not spec.carts:
        spec.update(set__last_empty_date=datetime.datetime.utcnow())


def remove_cart_from_specs(skus, cart_id):
    """

    :param skus:
    :param cart_id:
    :return:
    """
    for sku in skus:
        _remove_cart_from_spec(sku, cart_id)


def get_cart_entries_num(user_id=None, session_key=None):
    """

    :param user_id:
    :param session_key:
    :return:
    """
    cart = _get_cart(user_id, session_key)
    return len(cart.entries)


def update_cart_entry(sku, quantity=1, incr_quantity=True, user_id=None, session_key=None):
    """

    :param sku:
    :param quantity:
    :param incr_quantity:
    :param user_id:
    :param session_key:
    :return:
    """
    cart = _get_cart(user_id, session_key)
    for entry in cart.entries:
        if entry.sku == sku:
            if incr_quantity:
                entry.quantity += quantity
            else:
                entry.quantity = quantity
            cart.save()
            break
        else:
            if sku:
                entry = _new_entry(sku=sku, quantity=quantity, cart=cart)
                cart.entries.append(entry)
                cart.save()

    return cart_json(cart)


def remove_from_cart(skus, user_id=None, session_key=None):
    """

    :param skus:
    :param user_id:
    :param session_key:
    :return:
    """
    cart = _get_cart(user_id, session_key)
    cart.entries = [entry for entry in cart.entries if entry.sku not in skus]
    cart.save()
    remove_cart_from_specs(skus, str(cart.id))
    return cart_json(cart)


def empty_cart(user_id=None, session_key=None):
    """
    清空购物车
    :param user_id:
    :param session_key:
    :return:
    """
    cart = _get_cart(user_id, session_key)
    del_skus = [entry.sku for entry in cart.entries]
    cart.entries = []
    cart.save()
    remove_cart_from_specs(del_skus, str(cart.id))
    return cart_json(cart)


def update_cart(entries_info, user_id=None, session_key=None):
    """

    :param entries_info:
    :param user_id:
    :param session_key:
    :return:
    """
    cart = _get_cart(user_id, session_key)
    quantities = {entry.get('sku'): entry.get('quantity') for entry in entries_info}
    original_skus = set(entry.sku for entry in cart.entries)
    current_skus = set(entry.get('sku') for entry in entries_info)
    new_skus = current_skus - original_skus
    del_skus = []
    entries = []
    for entry in cart.entries:
        if entry.sku not in current_skus:
            del_skus.append(entry.sku)
            continue
        if not entry.sku:
            continue

        entry.quantity = quantities.get(entry.sku, 1)
        entries.append(entry)

    for sku in new_skus:
        if not sku:
            continue
        entries.append(_new_entry(sku=sku, quantity=quantities.get(sku, 1), cart=cart))

    cart.entries = entries
    cart.save()

    remove_cart_from_specs(del_skus, str(cart.id))
    return cart_json(cart)


def get_cart(user_id=None, session_key=None):
    """

    :param user_id:
    :param session_key:
    :return:
    """
    cart = _get_cart(user_id, session_key)
    return cart_json(cart)


def merge_carts(user_id_from=None, session_key_from=None, user_id_to=None, session_key_to=None):
    """

    :param user_id_from:
    :param session_key_from:
    :param user_id_to:
    :param session_key_to:
    :return:
    """
    from_cart = _get_cart(user_id_from, session_key_from)
    to_cart = _get_cart(user_id_to, session_key_to)
    info = Counter({entry.sku: entry.quantity for entry in from_cart.entries})
    info.update({entry.sku: entry.quantity for entry in to_cart.entries})
    res = update_cart([{'sku': k, 'quantity': v} for k, v in info.items()], user_id_to, session_key_to)
    empty_cart(user_id_from, session_key_from)
    return res


def entry_info_from_ids(entries):
    """

    :param entries:
    :return:
    """
    entries_info = []
    for entry in entries:
        e = {}
        e['item_id'] = entry['item_id']
        e['sku'] = entry['sku']
        e['quantity'] = entry['quantity']
        entries_info.append(e)

    return entries_info
