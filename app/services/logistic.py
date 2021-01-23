# -*- coding: utf-8  -*-
# @Author: ty
# @File name: logistic.py 
# @IDE: PyCharm
# @Create time: 1/23/21 3:37 PM
# @Description:
from functools import reduce

from app.config.enum import ORDER_TYPE
from app.models.order.logistic import Logistic, LogisticDetail, generate_uid
from app.models.order.partner import Partner
from app.utils.utils import group_by


class LogisticSpliter(object):
    """"""

    def __init__(self, order=None, entries=None, log=None, debug=False):
        if order:
            self.order = order
            self.entries = entries or order.entries
            self.log = log

        if log:
            self.order = log.order
            self.entries = entries or log.entries
            self.log = log

        self.debug = debug

    def check_shoes_and_handbags(self):
        main_categories = [entry.item_snapshot.main_category for entry in self.entries]
        if 'shoes' in main_categories and not len(main_categories) == 1:
            # all are shoes
            if len(set(main_categories)) == 1:
                return False
            else:
                grouped_entries = group_by(self.entries, lambda x: x.item_snapshot.main_category == 'shoes')
                return [self.do(self.order, list(entry)) for k, entry in grouped_entries]

        else:
            return False

    def split_with_amount(self):

        def gen_split_case(entries, packages=[], p_total=0):
            for entry in entries:
                if entry.amount_usd > 200:
                    yield [entry]
                    continue
                if p_total + entry.amount_usd > 200:
                    p_total = entry.amount_usd
                    if packages:
                        pkg = packages
                        packages = [entry]
                        yield pkg
                    else:
                        yield [entry]
                else:
                    packages.append(entry)
                    p_total += entry.amount_usd

                if entries.index(entry) == len(entries) - 1:
                    if packages:
                        yield packages

        amount = reduce(lambda x, y: x + y.amount_usd, self.entries, 0)

        if not amount > 200:
            return False
        else:
            entry = sorted(self.entries, key=lambda x: x.amount_usd, reverse=True)
            cases = [i for i in gen_split_case(entry)]
            if len(cases) == 1:
                return False
            return [self.do(self.order, entry) for entry in cases]

    def create(self):
        try:
            log = Logistic(detail=self.log.detail)
        except:
            log = Logistic(detail=LogisticDetail())

        log.order = self.order
        log.entries = list(self.entries)
        self.order.logistics.append(log)
        if not self.debug:
            log.detail.partner = Partner.objects().first()
            log.detail.partner_tracking_no = generate_uid()
            log.save()
            self.order.save()
        return log

    def do(self, order=None, entries=None):
        self.__init__(order=order, entries=entries, log=self.log)
        return reduce(lambda x, y: x or y(), [self.check_shoes_and_handbags, self.split_with_amount, self.create], False)


@signals.logistic_info_updated.connect
def look_for_new_tracking_no(sender, logistic):
    """

    :param sender:
    :param logistic:
    :return:
    """
    tracking = logistic.express_tracking
    if not tracking:
        return
    if not tracking.is_subscribed:
        jobs.express.kuaidi_request.delay(tracking.company, tracking.number)
    else:
        print(tracking.number, ' is already subscribed')


def logistic_provider_dispatcher(order):
    """

    :param order:
    :return:
    """
    Logistic.create(order)
    for logistic in order.logistics:
        if len(logistic.entries) > 1:
            logs = LogisticSpliter(log=logistic).do()
            if len(logs) > 1:
                logistic.close(reason='close by auto spliter')

    order.reload()
    for logistic in order.logistics:
        if order.order_type == ORDER_TYPE.TRANSFER:
            logistic.detail.route = order.order_type
        logistic.save()

    return order
