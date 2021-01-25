# -*- coding: utf-8  -*-
# @Author: ty
# @File name: cart.py 
# @IDE: PyCharm
# @Create time: 1/25/21 4:06 PM
# @Description:
from app.models.cart.cart import EntrySpec
from app.services.inventory import get_specs_info


def cart_json(cart):
    """

    :param cart:
    :return:
    """
    info  = get_specs_info([entry.sku for entry in cart.entries])
    specs = []
    for entry, spec in zip(cart.entries, info):
        if not spec.get('found'):
            entry_spec = EntrySpec.objects(sku=entry.sku).first()
            if not entry_spec:
                continue

            spec = entry_spec.to_mongo()
            spec['available'] = False

        spec['quantity'] = entry.quantity
        specs.append(spec)

    entries = []
    for spec in specs:
        entries.append({
            'id': '{}-{}-{}'.format(spec['item_id'], spec['sku'], spec['quantity']),
            'item': {
                'item_id': spec['item_id'],
                'title': spec['title'],
                'primary_image': spec['primary_image'],
                'available': spec['item_available'],
            },
            'spec': {
                'item_id': spec['item_id'],
                'sku': spec['sku'],
                'images': spec['images'],
                'price': spec['price'],
                'available': spec['available'],
                'attributes': spec['attributes'],
            },
            'unit_price': spec['price'],
            'amount': spec['price'] * entry.quantity,
            'quantity': spec['quantity'],
        })

    return entries
