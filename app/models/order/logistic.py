# -*- coding: utf-8  -*-
# @Author: ty
# @File name: logistic.py 
# @IDE: PyCharm
# @Create time: 1/12/21 10:38 PM
# @Description:仓储
import datetime
import random

from flask_login import current_user

from app import db

date_format = '%Y-%m-%d %H:%M:%S'

def generate_uid():
    current_time = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
    num = random.randint(1, 999)
    return 'MB' + current_time + str(num)

def get_date(obj, field):
    value = getattr(obj, field)
    return value.strftime(date_format) if value else ''
class Logistic(db.Document):
    """"""
    meta = {
        'db_alias': 'db_order',
        'indexes': ['is_closed',
                    '-created_at',
                    'order', 'entries',
                    'detail.status',
                    'detail.channel',
                    'detail.modified',
                    'detail.cn_tracking_no',
                    'detail.cn_logistic_name',
                    'detail.payment_received_date',
                    'detail.processing_date',
                    'detail.shipping_date',
                    'detail_port_arrived_date',
                    'detail.received_date',
                    'detail.partner',
                    'detail.partner_tracking_no',
                    ('detail.status', '-created_at'),
                    ]
    }
    order = db.ReferenceField('Order', required=True)
    entries = db.ListField(db.ReferenceField('OrderEntry'))
    returned_entries = db.ListField(db.ReferenceField('OrderEntry'))
    is_closed = db.BooleanField(default=False, required=True)
    close_reason = db.StringField()
    closed_at = db.DateTimeField()
    created_at = db.DateTimeField(required=True, default=datetime.datetime.utcnow())
    detail = db.EmbededDocumentField('LogisticDetail')

    def __unicode__(self):
        return '%s'%str(self.id)

    @property
    def estimated_weight(self):
        return sum(float(entry.item_snapshot.weight) * entry.quantity for entry in self.entries)

    def to_json(self):
        detail = self.detail
        return dict(cn_tracking_no=detail.cn_tracking_no,
                    cn_logistic_name=detail.cn_tracking_name,
                    partner_tracking_no=detail.partner_tracking_no,
                    partner_name=detail.partner_name if detail.partner else '',
                    payment_received_date=get_date(detail, 'payment_received_date'),
                    processing_date=get_date(detail, 'processing_date'),
                    shipping_date=get_date(detail, 'shipping_date'),
                    port_arrived_date=get_date(detail, 'port_arrived_date'),
                    received_date=get_date(detail, 'received_date'),
                    estimated_weight=self.estimated_weight,
                    real_weight=detail.real_weight,
                    status=detail.status)

    @property
    def amount(self):
        return sum(entry.amount for entry in self.entries)

    @property
    def amount_usd(self):
        return sum(entry.amount_usd for entry in self.entries)

    @classmethod
    def create(cls, order):
        def update_order(o):
            o.logistics.append(log)
            o.save()
            o.update_logistic_status()

        def create_logistic(order):
            log = cls(detail=LogisticDetail())
            log.order = order
            log.entries = order.entries
            log.detail.partner = Partner.objects().first()
            log.detail.partner_tracking_no = generate_uid()
            log.detail.status = order.status
            date_field = log.detail.attr_by_log_status[order.status]
            setattr(log.detail, date_field, datetime.datetime.utcnow())

            log.save()
            return log

        log = create_logistic(order)
        update_order(order)
        return log

    @classmethod
    def merge_with(cls, los):
        if not type(los) is list:
            return False

        start = 0
        for index in range(len(los)-1):
            if los[index+1].detail.cn_tracking_no != los[start].detail.cn_tracking_no or los[index+1].order != los[0].order:
                return False

        for index in range(len(los)-1):
            map(lambda e: los[index+1].entries.append(e), los[index].entries)
            los[index].entries = []
            los[index].save()
            los[index].close('merged with %s' % los[index+1].id, datetime.datetime.utcnow())
            los[index+1].save()

            if index+1 == len(los)-1:
                comment = LogisticRemark(content='合并单', creator=current_user.name)
                los[index+1].detail.remarks.append(comment)
                los[index+1].save()
                return los[index+1]


    def close(self, reason, time=None):
        """

        :param reason:
        :param time:
        :return:
        """



class LogisticDetail(db.EmbecedDocument):
    """"""

class LogisticRemark(db.EmbededDocument):
    """"""

class LogisticDelay(db.EmbededDocument):
    """"""

class LogisticIrregular(db.EmbededDocument):
    """"""







