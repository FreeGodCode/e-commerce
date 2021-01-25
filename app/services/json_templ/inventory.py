# -*- coding: utf-8  -*-
# @Author: ty
# @File name: inventory.py 
# @IDE: PyCharm
# @Create time: 1/25/21 4:31 PM
# @Description: 仓储
from app.models.inventory.brand import Brand
from app.models.inventory.category import Category
from app.models.inventory.item import Item

ATTRIBUTES_MAPPING = {
    'size': '尺码',
    'color': '颜色',
    'style': '样式',
}


def get_item_attribute_list(item):
    """

    :param item:
    :return:
    """
    attribute_desc = {}
    for k in item.attributes:
        attribute_desc[k] = ATTRIBUTES_MAPPING.get(k)

    return attribute_desc


def old_combination_json(item):
    def get_combination_values(spec, fields):
        values = {}
        for k in fields:
            value = spec.attributes[k]
            values.update({k: value})

        return values

    specs = item.available_specs
    fields = item.attributes

    combinations = []
    for spec in specs:
        if not spec.availability:
            continue

        values = get_combination_values(spec, fields)
        combinations.append(values)

    return combinations


def combination_json(item):
    """

    :param item:
    :return:
    """
    specs = item.available_specs
    combinations = []
    for spec in specs:
        if not spec.availability:
            continue

        combinations.append(spec.attributes)

    return combinations


def item_json_in_list(item):
    """

    :param item:
    :return:
    """

    return dict(
        item_id=item.item_id,
        title=item.title,
        primary_img=item.primary_img,
        thumbnail=item.large_thumbnail,
        main_category=item.main_category,
        sub_category=item.sub_category,
        brand=item.brand,
        status=item.status,
        price=item.price,
        weight=item.weight,
        original_price=item.original_price,
        discount=item.discount,
    )


def item_json(item):
    """

    :param item:
    :return:
    """
    main = Category.objects(en=item.main_category, level=1).first()
    sub = Category.objects(en=item.sub_category, level=2).first()
    brand_doc = Brand.objects(en=item.brand).first()

    main_category = main.to_json() if main else ''
    sub_category = sub.to_json() if sub else ''
    brand = brand_doc.to_json() if brand_doc else dict(cn=item.brand, en=item.brand)

    attributes_desc = get_item_attribute_list(item)

    item_dict = dict(
        item_id=item.item_id,
        title=item.title,
        brand=brand,
        attributes_desc=attributes_desc,
        main_category=main_category,
        sub_category=sub_category,
        detail=item.description,
        source=item.vendor,
        price=item.price,
        weight=item.weight,
        original_price=item.original_price,
        discount=item.discount,
        primary_img=item.primary_img,
        large_thumbnail=item.large_thumbnail,
        small_thumbnail=item.small_thumbnail,
        status=item.status,
        specs=[spec_json(spec) for spec in item.available_specs]
    )
    return item_dict


def spec_json(spec):
    """

    :param spec:
    :return:
    """
    return dict(
        item_id=spec.item_id,
        sku=spec.sku,
        images=spec.images,
        original_price=spec.original_price,
        price=spec.price,
        available=spec.availability,
        attributes=getattr(spec, 'attribures', None)
    )


def board_json(board):
    """

    :param board:
    :return:
    """
    return dict(
        id=str(board.id),
        date=str(board.published_at),
        image=board.image,
        desc=board.description,
        title=board.title,
        items=[item_json_in_list(item) for item in Item.objects(web_id__in=board.items[: 8])]
    )
