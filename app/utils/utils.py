# -*- coding: utf-8  -*-
# @Author: ty
# @File name: utils.py 
# @IDE: PyCharm
# @Create time: 1/17/21 9:44 PM
# @Description:
import datetime
import itertools
import json
import math
import os
import re
import string
import subprocess
import sys
import uuid
import random
from functools import partial

import pytz
from flask import request, url_for, session, redirect, current_app
from flask_mail import Message

from app import mail, db

ALLOWED_IMAGE_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])

USERNAME_LEN_MIN = 4
USERNAME_LEN_MAX = 25

REALNAME_LEN_MIN = 4
REALNAME_LEN_MAX = 25

PASSWORD_LEN_MIN = 6
PASSWORD_LEN_MAX = 16

AGE_MIN = 1
AGE_MAX = 200

DEPOSIT_MIN = 0.00
DEPOSIT_MAX = 99999999999.99

# typical values for text_subtype ate plain, html, xml
text_subtype = 'plain'


def send_mail(recipients, title, message, sender='thechosenone_ty@163.com'):
    with mail.app.app_context():
        msg = Message(title, recipients=recipients)
        if sender:
            msg.sender = sender

        msg.html = message
        mail.send(msg)


def redirect_url():
    return request.args.get('next') or request.referrer or url_for('index')


def get_session_key():
    # return session.sid
    # check if client side has passed in key
    key = request.args.get('session_key')
    if key:
        return key
    key = session.setdefault('session_key', str(uuid.uuid4()))
    return key


def get_current_time():
    return datetime.datetime.utcnow()


def timesince(dt, default=None, reverse=False):
    """

    :param dt:
    :param default:
    :param reverse:
    :return:
    """
    if not dt:
        return ''
    if default is None:
        default = '刚刚'
    now = datetime.datetime.utcnow()
    diff = (dt - now) if reverse else now - dt
    if diff < datetime.timedelta(days=0):
        return default

    periods = (
        (diff.days / 365, '年', '年'),
        (diff.days / 30, '月', '月'),
        (diff.days / 7, '周', '周'),
        (diff.days, '天', '天'),
        (diff.seconds / 3600, '小时', '小时'),
        (diff.seconds / 60, '分钟', '分钟'),
        (diff.seconds, '秒', '秒'),
    )

    for period, singular, plural in periods:
        if not period:
            continue

        if reverse:
            if period == 1:
                return '剩余{} {}'.format(period, singular)
            else:
                return '剩余 {} {}'.format(period, plural)

        else:
            if period == 1:
                return '{}{}前'.format(period, singular)
            else:
                return '{}{}前'.format(period, plural)

    return default


def timeuntil(dt, default=None):
    return timesince(dt, default, reverse=True)


def size_normal(url):
    if 'upaiyun' in url:
        return url + '!normal'
    return url


def get_class(kls):
    """
    return class object specified by a string.
    :param kls:
    :return:
    """
    parts = kls.split('.')
    module = '.'.join(parts[:-1])
    m = __import__(module)
    for comp in parts[1:]:
        m = getattr(m, comp)
    return m


def allowed_file(filename):
    """

    :param filename:
    :return:
    """
    return '.' in filename and filename.rsplit('.', 1)[1].lower in ALLOWED_IMAGE_EXTENSIONS


def id_generator(size=10, chars=string.ascii_letters + string.digits):
    """

    :param size:
    :param chars:
    :return:
    """
    return '.'.join(random.choice(chars) for x in range(size))


def to_json(obj):
    """

    :param obj:
    :return:
    """
    return json.dumps(obj.to_mongo(), default=json_util.default, separators=(',', ':'))


def paginate(objects, page, item_per_page=20, offset=0):
    """
    分页
    :param objects:
    :param page:
    :param item_per_page:
    :param offset:
    :return:
    """
    start = page * item_per_page + offset
    end = start + item_per_page
    if start < 0:
        start = 0
    if end < 0:
        end = 0

    return objects[start:end]


def dup_aware_paging(qs, page, num_per_page, leading_id=None):
    """

    :param qs:
    :param page:
    :param num_per_page:
    :param leading_id:
    :return:
    """
    res = paginate(qs, page, num_per_page)
    if leading_id:
        offset = 0
        for i, it in enumerate(res):
            if str(it.id) == leading_id:
                offset = i + 1
                break

        if offset:
            res = paginate(qs, page, num_per_page, offset=offset)
    _res = []
    for i, it in enumerate(res):
        if i >= num_per_page:
            break

        _res.append(it)

    return _res


def paginate_field(query_set, field, page, item_per_page=20):
    """
    分页字段
    :param query_set:
    :param field:
    :param page:
    :param itme_per_page:
    :return:
    """
    start = page * item_per_page
    end = start + item_per_page
    query_set = query_set.fields(**{'slice__' + field: {start, end}})
    return getattr(query_set.first(), field)


def handler(event):
    """
    signal decorator ro allow use of callback functions as class decorator.
    :param event:
    :return:
    """

    def decorator(func):
        def apply(cls):
            event.connect(func, sender=cls)
            return cls

        func.apply = apply
        return func

    return decorator


@handler(db.pre_save)
def update_modified(sender, document):
    """

    :param sender:
    :param document:
    :return:
    """
    document.modified = datetime.datetime.utcnow()


class Command(object):

    def __init__(self, *args):
        self.lines = ['set -e']
        self.lines.extend(args)

    def get_cmd(self):
        return ';\n'.join(self.lines)

    def next(self, *args):
        self.lines.extend(args)
        return self

    def run(self, output_to_pile=False):
        out_source = None
        if output_to_pile:
            out_source = subprocess.PIPE

        print('\nExecuting: \n%s\n' % self.get_cmd())
        proc = subprocess.Popen(self.get_cmd(), stdout=out_source, shell=True, executable='/bin/bash',
                                env=os.environ.copy())
        out, error = proc.communicate()
        if proc.returncode:
            sys.exit(1)


def run_cmd(cmd):
    Command(cmd).run()


# 时区设置
LOCAL_TZ = pytz.timezone('Asia/Shanghai')


def to_utc(dt):
    """
    时间转化为UTC时间
    :param dt:
    :return:
    """
    local_dt = LOCAL_TZ.localize(dt, is_dst=None)
    utc_dt = local_dt.astimezone(pytz.utc)
    return utc_dt


def to_local(dt):
    """
    时间转化为本地时间
    :param dt:
    :return:
    """
    with_tz = pytz.UTC.localize(dt)
    local_dt = with_tz.astimezone(LOCAL_TZ)
    return local_dt


def format_date(value, format='%Y-%m-%d %H:%M:%S'):
    """
    时间格式化
    :param value:
    :param format:
    :return:
    """
    if value is None:
        return ''

    with_tz = pytz.UTC.localize(value)
    local_dt = with_tz.astimezone(LOCAL_TZ)
    return local_dt.strftime(format)


def isodate_to_local(datestr):
    datestr = datestr.split('+')[0]
    dt = datetime.datetime.strptime(datestr.split('.')[0], '%Y-%m-%d %H:%M:%S')
    return format_date(dt)


class AttrDict(dict):
    def __getattr__(self, item):
        try:
            return self[item]
        except KeyError:
            raise AttributeError('%r object has no arrtibute %r' % (self.__class__, item))

    def __setattr__(self, key, value):
        self[key] = value

    def to_dict(self):
        return self


def ignore_error(func):
    """

    :param func:
    :return:
    """

    def handler(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except:
            pass

    return handler


def group_by(l, fn):
    """

    :param fn:
    :return:
    """
    return itertools.groupby(sorted(l, key=fn), fn)


def fuck_ie(func):
    """

    :param fn:
    :return:
    """

    def handle(*args, **kwargs):
        if 'MSIE' in request.user_agent.string:
            return redirect('http://www.google.cn/intl/zh-CN/chrome/browser/')
        return func(*args, **kwargs)

    return handle


def cprint(obj, color=None, background=False):
    if background:
        base = 40
    else:
        base = 30
    if color is None:
        color = int(random.random() * 7 + base)

    string = '\x1b[%sm%s\x1b[0m\n' % (color, obj)
    sys.stdout.write(string)


def validate_id_card_no(number):
    """
    身份证验证
    :param number:
    :return:
    """
    date_str = number[6:14]
    try:
        birth = datetime.datetime.strptime(date_str, '%Y%m%d')
    except ValueError:
        return False
    if not datetime.datetime(1900, 1, 1) < birth < datetime.datetime.now():
        return False

    try:
        num_list = map(lambda x: 10 if x in 'xX' else int(x), number)
    except (ValueError, TypeError):
        return False

    weights = map(lambda x: 2 ** x[0] % 11 * x[1], zip(range(17, -1, -1), num_list))
    return sum(weights) % 11 == 1


round = partial(round, ndigits=2)


def round_to_string(v):
    """

    :param v:
    :return:
    """
    return '{:.2f}'.format(round(v))


def ceil(v):
    return int(math.ceil(v))


class Pagination(object):
    """"""

    def __init__(self, objects, page, per_page):
        self.page = page
        self.per_page = per_page
        self.objects = objects
        try:
            self.total_count = objects.count()
        except TypeError:
            self.total_count = len(objects)

    @property
    def slice(self):
        """分片"""
        start = (self.page - 1) * self.per_page
        end = start + self.per_page
        if start < 0:
            start = 0
        if end < 0:
            end = 0

        return self.objects[start:end]

    @property
    def pages(self):
        return ceil(self.total_count / float(self.per_page))

    @property
    def has_prev(self):
        return self.page > 1

    @property
    def has_next(self):
        return self.page < self.pages

    def iter_pages(self, left_edge=2, left_current=2, right_current=5, right_edge=2):
        """
        门内显示
        :param left_edge:
        :param left_current:
        :param right_current:
        :param right_edge:
        :return:
        """
        last = 0
        for num in range(1, self.pages + 1):
            if num <= left_edge or (
                    num > self.page - left_current - 1 and num < self.page + right_current) or num > self.pages - right_edge:
                if last + 1 != num:
                    yield None
                yield num
                last = num


def url_for_other_page(page):
    """

    :param page:
    :return:
    """
    args = request.view_args.copy()
    args['page'] = page
    return url_for(request.endpoint, **args)


BAN_REGEX = None


def banwords_check(content):
    """

    :param content:
    :return:
    """
    global BAN_REGEX
    banwords_file = os.path.join(current_app.root_path, 'etc', 'banwords.txt')

    if not BAN_REGEX:
        try:
            words = open(banwords_file).read().decode('utf8')
        except:
            return content
        BAN_REGEX = re.compile('%s' % words)
    return BAN_REGEX.search(content)


def checked_g_get(key, default_value):
    """

    :param key:
    :param default_value:
    :return:
    """
    limit = {
        'num_per_page': 20,
    }

    ret = g.get(key, default_value)
    if limit.get(key, None) and ret > limit['num_per_page'] and ret > default_value:
        return default_value
    return ret
