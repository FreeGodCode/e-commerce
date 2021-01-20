# -*- coding: utf-8  -*-
# @Author: ty
# @File name: logistic.py 
# @IDE: PyCharm
# @Create time: 1/20/21 12:12 PM
# @Description:
import datetime
import os
from itertools import chain

from bson import ObjectId, json_util
from flask import make_response, jsonify, request
from flask_admin import expose
from flask_login import current_user
from mongoengine import Q

from app.config import BASE_DIR
from app.models.order.logistic import LogisticDetail, Logistic, LogisticIrregular, LogisticRemark
from app.models.order.order import Order
from app.models.order.partner import Partner
from app.models.user.address import Address
from app.views.admin import AdminView

num_per_page = 50
delay_status_by_date = {
    'PAYMENT_RECEIVED': 3,
    'PROCESSING': 1,
    'SHIPPING': 5,
    'PORT_ARRIVED': 4,
}
TEMPLATE_DIR = os.path.join(BASE_DIR, '../../templates')


def to_json(lo):
    """

    :param lo:
    :return:
    """
    dt = {}
    dt['id'] = str(lo.id)
    dt['is_closed'] = lo.is_closed
    dt['closed_reason'] = lo.closed_reason
    dt['created_at'] = lo.created_at
    dt['detail'] = lo.detail.to_mongo()
    dt['detail']['partner'] = (lambda p: p and p.name)(lo.detail.partner)
    dt['address'] = lo.order.address.to_json()
    dt['order_id'] = lo.order.short_id
    dt['logistic_provider'] = lo.order.logistic_provider
    dt['entries'] = [entry_to_json(entry) for entry in lo.entries]
    dt['estimated_weight'] = lo.estimated_weight
    dt['returned_entries'] = [entry_to_json(entry) for entry in lo.returned_entries]
    return dt


def entry_to_json(entry):
    """

    :param entry:
    :return:
    """
    dt = {}
    dt['id'] = str(entry.id)
    dt['item'] = entry.item_snapshot.to_mongo()
    dt['spec'] = entry.item_spec_snapshot.to_mongo()
    try:
        dt['item']['weight'] = entry.item_snapshot.weight
    except:
        pass

    try:
        dt['item']['title_en'] = entry.item_snapshot.title_en
    except:
        pass

    dt['amount_usd'] = entry.amount_usd
    dt['amount'] = entry.amount
    dt['quantity'] = entry.quantity
    dt['unit_price'] = entry.unit_price
    dt['created_at'] = entry.created_at
    dt['remark'] = entry.remark
    dt['shipping_info'] = entry.shipping_info
    return dt


def restruct_query(data):
    """

    :param data:
    :return:
    """
    format_date = lambda d: datetime.datetime.strptime(d, '%Y-%m-%d %H:%M:%S.%f')
    status = data.get('status')
    query = {}
    for k, v in data.items():
        if v in [None, 'None', '', 'null']:
            continue
        if k[-3:] == '_no':
            query.update({'detail__%s' % k: v})
        elif k in ['status']:
            query.update({'detail__%s' % k: v})
        elif k == 'start':
            if status:
                date_field = LogisticDetail.attr_by_log_status[status]
                query.update({'detail__%s__gte' % date_field: format_date(v)})
            else:
                query.update({'created_at__gte': format_date(v)})
        elif k == 'end':
            if status:
                date_field = LogisticDetail.attr_by_log_status[status]
                query.update({'detail__%s__lt' % date_field: format_date(v)})
            else:
                query.update({'created_at__lt': format_date(v)})
        elif k == 'query':
            if v.startswith('MB'):
                query.update({'detail__partner_tracking_no': v})
            elif ObjectId.is_vaild(v):
                query.update({'id': v})
            else:
                query.update({'tracking_no': v})

        elif k == 'partner':
            partner = Partner.objects(name=v).first()
            query.update({'detail__partner': partner})
        elif k == 'channel':
            query.update({'detail__channel': v})
        else:
            query.update({'%s' % k: v})

    return query


class N(AdminView):
    """"""
    _permission = 'logistic'

    @expose('/', methods=['GET', 'POST', 'DELETE', 'PATCH'])
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

    @expose('/logistics', methods=['GET'])
    def logistics(self):
        """
        物流
        :return:
        """
        items_range = request.headers.get('Range', '0-9')
        start, end = items_range.split('-')
        per_page = int(end) - int(start) + 1
        query = restruct_query(request.args)
        tracking_no = query.pop('tracking_no', '')
        include_closed = query.get('include_closed') and query.pop('include_closed')
        try:
            if include_closed:
                logistic = Logistic.objects(**query)
            else:
                logistic = Logistic.objects(is_closed=False, **query)
            if tracking_no:
                logistic = logistic.filter(
                    Q(detail__us_tracking_no=tracking_no) | Q(detail__cn_tracking_no=tracking_no))

            if request.args.get('status'):
                logistic = logistic.order_by(
                    'detail__%s' % LogisticDetail.attr_by_log_status[request.args.get('status')])
        except:
            pass

        if query.get('receiver'):
            address = Address.objects(receiver=query.get('receiver')).distinct('id')
            orders = Order.commodities(address__in=address)
            logistic = list(chain.from_iterable(order.logistics for order in orders))
        if query.get('order_id'):
            orders = Order.commodities(short_id=int(query.get('order_id')))
            logistic = list(chain.from_iterable(order.logistics for order in orders))

        try:
            logistic_size = logistic.count()
        except:
            logistic_size = len(logistic)

        data = logistic[int(start): int(end)]
        data = [to_json(l) for l in data]
        resp = make_response(json_util.dumps(data), 200)
        resp.headers['Accept_Range'] = 'items'
        resp.headers['Content_Range'] = '%s-%s/%s' % (start, end, logistic_size)
        resp.headers['Content_Type'] = 'application/json'
        return resp

    @expose('/logistics_delay/<status>/<delay_type>', methods=['GET'])
    @expose('/logistics_delay/<status>/', methods=['GET'])
    @expose('/logistics_delay/', methods=['GET'])
    def logistics_delay(self, status=None, delay_type=None):
        """
        物流延迟
        :param status:
        :param delay_type:
        :return:
        """
        utcnow = datetime.datetime.utcnow()
        if status:
            items_range = request.headers.get('Range', '0-9')
            start, end = items_range.split('-')
            per_page = int(end) - int(start) + 1

            query = restruct_query(request.args)
            tracking_no = query.pop('tracking_no', '')
            date_field = LogisticDetail.attr_by_log_status[status]
            delay_days = datetime.timedelta(days=delay_status_by_date[status])
            query.update({'detail__%s__lt' % date_field: utcnow - delay_days, 'detail__status': status,})
            logistic = Logistic.objects(is_closed=False, **query).order_by('detail__%s' % date_field)

            if tracking_no:
                logistic = logistic.filter(Q(detail__us_tracking_no=tracking_no) | Q(detail__cn_tracking_no=tracking_no))
            if delay_type:
                logistic = logistic.filter(detail__delay_details__reason__contains=delay_type)

            data = logistic[int(start): int(end)]
            data = [to_json(l) for l in data]
            resp = make_response(json_util.dumps(data), 200)
            resp.headers['Accept_Range'] = 'items'
            resp.headers['Content_Range'] = '%s-%s/%s' % (start, end, logistic.count())
            resp.headers['Content_Type'] = 'application/json'
            return resp

        data = {}
        for status in ['PAYMENT_RECEIVED', 'PROCESSING', 'SHIPPING', 'PORT_ARRIVED']:
            logistic = Logistic.objects(is_closed=False)
            date_field = LogisticDetail.attr_by_log_status[status]
            delay_days = datetime.timedelta(days=delay_status_by_date[status])
            query = {'detail__%s__lt' % date_field: utcnow - delay_days, 'detail__status': status,}
            count = logistic.filter(**query).count()
            data.update({status: count})

        return jsonify(results=data)

    @expose('/logistics_irregular/<process_status>/<irr_type>', methods=['GET'])
    @expose('/logistics_irregular/<process_status>/', methods=['GET'])
    @expose('/logistics_irregular', methods=['GET'])
    def logistics_irregular(self, process_status=None, irr_type=None):
        """

        :param process_status:
        :param irr_type:
        :return:
        """
        utcnow = datetime.datetime.utcnow()
        if process_status:
            items_range = request.headers.get('Range', '0-9')
            start, end = items_range.split('-')
            query = restruct_query(request.args)
            tracking_no = query.pop('tracking_no', '')
            logistic = Logistic.objects(detail__irregular_details__process_status=process_status, **query).order_by('-detail.irregular_details.created_at')
            if irr_type:
                logistic = logistic.filter(detail__irregular_details__irr_type=irr_type).order_by('-detail.irregular_details.created_at')

            if tracking_no:
                logistic = logistic.filter(Q(detail__us_tracking_no=tracking_no) | Q(detail__cn_tracking_no=tracking_no))

            data = logistic[int(start): int(end)]
            data = [to_json(l) for l in data]
            resp = make_response(json_util.dumps(data), 200)
            resp.headers['Accept-Range'] = 'items'
            resp.headers['Content-Range'] = '%s-%s/%s' % (start, end, logistic.count())
            resp.headers['Content_Type'] = 'application/json'
            return resp

        data = {}
        for status in ['WAITTING_PROCESS', 'PROCESSING', 'PROCESSED']:
            logistic = Logistic.objects(detail__irregular_details_process_status=status)
            data.udpate({status: logistic.count()})

        return jsonify(results=data)

    @expose('/update', methods=['PUT'])
    def update(self):
        """

        :return:
        """
        query = request.get_json()
        data = {}
        for k, v in query.items():
            if v in [None, 'None', '', 'null']:
                continue
            if 'date' in k:
                val = datetime.datetime.strptime(v, '%Y-%m-%d')
            elif k.startswith('real'):
                val = float(v)
            elif k == 'partner':
                val = Partner.objects(name=v).first()
            elif k == 'irregularity':
                val = LogisticIrregular(irr_at_status=v.get('status'), irr_type=v.get('type'), reason=v.get('reason'), desc=v.get('desc'))
            else:
                val = v.strip()
            data.update({k: val})

        try:
            logistic = Logistic.objects.get(id=data.pop('lid'))
            logistic.update_logistic(data)
            return jsonify(message='OK', remarks=logistic.detail.remarks, delays=logistic.detail.delay_details, irregularities=logistic.detail.irregular_details)
        except Exception as e:
            return jsonify(message='Failed', desc=e)

    @expose('/update_delay', methods=['PUT'])
    def update_delay(self):
        """

        :return:
        """
        query = request.get_json()
        try:
            logistic = Logistic.objects.get(id=query['lid'])
            delays = logistic.detail.delay_details.filter(status=query['status'])
            delays.update(is_done=query['is_done'])
            logistic.save()
            return jsonify(message='OK')
        except Exception as e:
            return jsonify(message='Failed', desc=e)

    @expose('/update_irr_step', methods=['PUT'])
    def update_irr_step(self):
        """

        :return:
        """
        query = request.get_json()
        data = {}
        for k, v in query.items():
            data.update({k: v})

        try:
            logistic = Logistic.objects.get(id=data['lid'])
            irregular = logistic.detail.irregular_details.filter(irr_type=data['irr_type']).first()
            irregular.steps = data['solutions']
            logistic.save()
            return jsonify(message='OK', irr_detail=irregular)
        except Exception as e:
            return jsonify(message='Failed', desc=e)

    @expose('/set_irr_done', methods=['PUT'])
    def set_irr_done(self):
        """

        :return:
        """
        query = request.get_json()
        data = {}
        for k, v in query.items():
            data.update({k: v})

        try:
            logistic = Logistic.objects.get(id=data['lid'])
            irregular = logistic.detail.irregular_details.filter(irr_type=data['irr_type']).first()
            irregular.process_status = data['process_status']
            logistic.save()
            return jsonify(message='OK', irr_detail = irregular)
        except Exception as e:
            return jsonify(message='OK', desc=e)

    @expose('/update_irr_remark', methods=['PUT'])
    def update_irr_remark(self):
        """

        :return:
        """
        query = request.get_json()
        data = {}
        for k, v in query.items():
            data.update({k: v})

        try:
            logistic = Logistic.objects.get(id=data['lid'])
            irregular = logistic.detail.irregular_details.filter(irr_type=data['irr_type']).first()
            remark = LogisticRemark(content=data['irr_remark'], creator=current_user.name)
            irregular.remarks.append(remark)
            logistic.save()
            return jsonify(message='OK', irr_detail=irregular)
        except Exception as e:
            return jsonify(message='Failed', desc=e)
