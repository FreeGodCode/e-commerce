# -*- coding: utf-8  -*-
# @Author: ty
# @File name: item.py 
# @IDE: PyCharm
# @Create time: 1/21/21 11:16 AM
# @Description:
import os
import time
from math import ceil
from urllib import parse
from uuid import uuid4

from bson import json_util
from flask import make_response, jsonify, request
from flask_admin import expose
from flask_babel import gettext
from flask_login import current_user

from app.config import BASE_DIR, UEDITOR_CONFIG
from app.config.price import COST_PRICE, CURRENT_PRICE, ORIGIN_PRICE
from app.models.inventory.category import Category
from app.models.inventory.item import Item, ItemSpec
from app.models.inventory.statistics import Statistics
from app.views.admin import AdminView

num_per_page = 50

TEMPLATE_DIR = os.path.join(BASE_DIR, '../../../../templates')


def restruct_query(data):
    """
    重构查询
    :param data:
    :return:
    """
    status = data.get('status')
    query = {}
    for k, v in data.items():
        if v in [None, 'None', '', 'null']:
            continue
        if k == 'query':
            query.update({'item_id': v})
        elif k == 'cate':
            query.update({'sub_category': v})
        elif k == 'availability':
            query.update({k: v == 'true' and True or False})
        else:
            query.update({'%s' % k: v})
    return query


def to_json(item):
    """

    :param item:
    :return:
    """
    return dict(
        meta=item.to_mongo(),
        specs=[spec.to_mongo() for spec in item.specs]
    )


class I(AdminView):
    """"""
    _permission = 'content'

    @expose(url='/', methods=['GET', 'POST', 'DELETE', 'PATCH'])
    def index(self, status='ALL'):
        """

        :param status:
        :return:
        """

        def render_templ(status):
            return make_response(open(os.path.join(TEMPLATE_DIR, 'admin/logistic/index.html')).read())

        def render_json(lid):
            return jsonify(message='OK')

        return request.is_xhr and {'GET': lambda f: render_json(f.get('id')), }[request.method](
            request.form) or render_templ(status)

    @expose(url='/items', methods=['GET'])
    def items(self):
        """

        :return:
        """
        items_range = request.headers.get('Range', '0-24')
        start, end = items_range.split('-')

        query = restruct_query(request.args)
        try:
            items = Item.objects(**query).order_by('-created_at')
        except:
            pass

        try:
            items_size = items.count()
        except:
            items_size = len(items)

        data = items[int(start): int(end)]
        data = [to_json(item) for item in data]
        resp = make_response(json_util.dumps(data), 200)
        resp.headers['Range-Unit'] = 'items'
        resp.headers['Content-Range'] = '%s-%s/%s' % (start, end, items_size)
        resp.headers['Content_Type'] = 'application/json'
        return resp

    @expose(url='/update', methods=['PUT'])
    def update(self):
        """

        :return:
        """
        query = request.get_json()
        data = {}
        for k, v in query['meta'].items():
            if v in [None, 'None', '', 'null']:
                continue
            if type(v) == dict:
                continue
            elif 'price' in k:
                val = float(v)
            elif k == 'weight':
                val = float(v)
            elif k == 'primary_img':
                path = '{}/{}.jpg'.format('other', uuid4())
                val = jobs.image.upload('maybe-img', path, url=v, make_thumbnails=True)
            else:
                val = v
            data.update({k: val})
        data.update({'discount': ceil(((data['original_price'] - data['price']) / data['original_price']) * 100)})
        data.update({'meta': data})
        try:
            item = Item.objects(web_id=data['web_id']).first()
            item.modify(data, data['price'])
            return jsonify(message='OK')
        except Exception as e:
            return jsonify(message='Failed', desc=e)

    @expose(url='categories', methods=['GET'])
    @cached(timeout=120)
    def categories(self):
        """
        分类
        :return:
        """
        category_dict = defaultdict(set)
        # 统计
        for stats in Statistics.objects:
            category_dict[stats.main_category].add(stats.sub_category)

        category_list = []
        for main_category in category_dict.keys():
            main = Category.objects(level=1, en=main_category).first()
            sub_list = []
            for sub_category in category_dict[main_category]:
                sub = Category.objects(level=2, en=sub_category).first()
                if main and sub:
                    sub_list.append(dict(en=sub.en, cn=sub.cn))
            category_list.append(dict(en=main.en, cn=main.cn, sub_list=sub_list, ))
        # return jsonify({'message': 'OK', 'categories': category_list})
        return jsonify(dict(message='OK', categories=category_list))

    @expose(url='update_spec', methods=['PUT'])
    def update_spec(self):
        """

        :return:
        """
        query = request.get_json()
        data = {}
        for k, v in query.items():
            if v in [None, 'None', '', 'null']:
                continue
            if k != 'attributes' and type(v) == dict:
                continue
            elif 'price' in k:
                val = float(v)
            elif k == 'images':
                val = []
                if type(v) == 'unicode':
                    v = v.split(',')
                for img in v:
                    if img.startswith('http://assets.maybe'):
                        val.append(img)
                    else:
                        path = '{}/{}.jpg'.format(query.get('brand', 'other'), uuid4())
                        url = jobs.image.upload('maybe-img', path, url=img, make_thumbnails=True)
                        val.append(url)

                else:
                    val = v
                data.update({k: val})

            try:
                spec = ItemSpec.objects(sku=data['_id']).first()
                spec.update_spec(data)
                return jsonify(message='OK', spec=spec)
            except Exception as e:
                return jsonify(message='Failed', desc=e)

    @expose(url='/add_spec', methods=['POST'])
    def add_spec(self):
        """

        :return:
        """
        query = request.get_json()
        data = {}
        for k, v in query.items():
            if v in [None, 'None', '', 'null']:
                continue
            elif 'price' in k:
                val = float(v)
            elif k == 'images':
                images = v.split(',')
                val = []
                for img in images:
                    if img.startswith('http://assets.maybe'):
                        val.append(img)
                    else:
                        path = '{}/{}.jgp'.format(query.get('brand', 'other'), uuid4())
                        url = jobs.image.upload('maybe-img', path, url=img, make_thumbnails=True)
                        val.append(url)
            else:
                val = v
            data.update({k: val})
        data.update({'web_sku': str(time.time()).replace('.', '')})
        try:
            spec = ItemSpec(**data).save()
            return jsonify(message='OK', spec=spec)
        except Exception as e:
            return jsonify(message='Failed', desc=e)

    @expose(url='/delete_spec', methods=['DELETE'])
    def delete_spec(self):
        """

        :return:
        """
        query = request.get_json()
        sku = query.get('sku')
        if 'ADMIN' not in current_user.roles:
            return jsonify(message='Failed', desc='Sorry, you dont have permission to do this')
        try:
            ItemSpec.objects(sku=sku).delete()
            return jsonify(message='OK')
        except Exception as e:
            return jsonify(message='Failed', desc=e)

    @expose(url='/add_item', methods=['POST'])
    def add_item(self):
        """

        :return:
        """
        query = request.get_json()
        data = {}
        for k, v in query.items():
            if v in [None, 'None', '', 'null']:
                continue
            elif 'price' in k:
                val = float(v)
            elif k == 'primary_img':
                path = '{}/{}.jpg'.format('other', uuid4())
                val = jobs.image.upload('maybe-img', path, url=v, make_thumbnails=True)
            else:
                val = v
            data.update({k: val})
        try:
            china_price = data['china_price'] + data.pop('express_price')
            cost_price = COST_PRICE(china_price, data['weight'])
            price = CURRENT_PRICE(cost_price)
            origin_price = ORIGIN_PRICE(price)
            vendor = 'taobao'
            brand = 'other'
            main_category = 'home'
            sub_category = 'unclassified'
            ps = parse.urlparse(data['url'])
            web_id = parse.parse_qs(ps.query)['id'][0]
            translator = MSTranslate('maybe', '')
            title_en = translator.translate(data['title'], 'en', 'zh')

            data.update({
                'web_id': web_id,
                'title_en': title_en,
                'china_price': china_price,
                'original_price': origin_price,
                'price': price,
                'main_category': main_category,
                'sub_category': sub_category,
                'creator': current_user.name,
                'vendor': vendor,
                'brand': brand,
                'availability': False,
                'currency': 'USD',
                'sex_tag': 'UNCLASSIFIED',
                'tags': [],
                'discount': ceil(((origin_price - price) / origin_price) * 100),
            })

            attr_data = {}
            for attr in data['attributes']:
                attr_data.update({attr: None})

            spec_data = {
                'web_sku': str(time.time()).replace('.', ''),
                'images': [data['primary_img']],
                'china_price': china_price,
                'original_price': origin_price,
                'price': price,
                'attributes': attr_data,
            }
            data = {'meta': data, 'spec': [spec_data]}
            item = Item.create(data)
            return jsonify(message='OK', item=item)
        except Exception as e:
            return jsonify(message='OK', desc=e)

    @expose(url='/upload', methods=['GET', 'POST', 'OPTIONS'])
    def upload_img(self):
        """
        UEditor文件上传接口,config 配置文件
        :return:
        """
        result = {}
        action = request.args.get('action')
        CONFIG = UEDITOR_CONFIG
        if action == 'config':
            result = CONFIG
        elif action == 'uploadimage':
            img = request.files.get('upfile')
            name, extension = img.filename.rsplit('.', 1)
            filename = uuid4()
            path = '{}/{}.{}'.format('detail', filename, extension)
            url = jobs.image.upload('maybe-img', path, image=img.read(), make_thumbnails=True)
            result = {
                'state': 'SUCCESS',
                'url': url,
                'title': filename,
                'original': filename,
                'type': extension,
                'size': ''
            }
        elif action == 'catchimage':
            field_name = CONFIG['catcherFieldName']
            if field_name in request.form:
                source = []
            elif '%s[]' % field_name in request.form:
                source = request.form.getlist('%s[]' % field_name)

            _list = []
            for imgurl in source:
                filename = uuid4()
                path = '{}/{}.jpg'.format('details', filename)
                url = jobs.image.upload('maybe-img', path, url=imgurl, make_thumbnails=False)
                _list.append({
                    'state': 'SUCCESS',
                    'url': url,
                    'original': filename,
                    'source': imgurl,
                })
            result['state'] = 'SUCCESS' if len(_list) > 0 else 'ERROR'
            result['list'] = _list
        else:
            result['state'] = '请求地址出错'
        return jsonify(result)


admin.add_view(
    I(name=gettext('Item Backend'), category=gettext('Content'), menu_icon_type='fa', menu_icon_value='gift'))
