# -*- coding: utf-8  -*-
# @Author: ty
# @File name: image.py 
# @IDE: PyCharm
# @Create time: 1/25/21 11:56 AM
# @Description:
from io import StringIO
from urllib import request

import boto as boto
from PIL import ImageOps
from PIL.Image import Image
from boto.s3.key import Key

from app.config import settings
from app.services import celery


@celery.task
def upload(space, path, image=None, url=None, async=True, make_thumbnails=True):
    """
    上传
    :param space:
    :param path:
    :param image:
    :param url:
    :param make_thumbnails:
    :return:
    """
    connect = boto.connect_s3(settings.AWS_ACCESS_KEY_ID, settings.AWS_SECRET_ACCESS_KEY)
    bucket_name = space
    bucket = connect.get_bucket(bucket_name)
    k = Key(bucket)

    def make_thumb(image):
        """
        打指纹
        :param image:
        :return:
        """
        img = Image.open(image)
        for size in [(400, 400), (150, 150)]:
            output = StringIO()
            img2 = ImageOps.fit(img, size, Image.ANTIALIAS)
            img2.save(output, 'JPEG')
            k.key = 'thumbnails/%sx%s/%s' % (size[0], size[1], path)
            k.set_contents_from_string(output.getvalue())
            k.make_public()
            output.close()

    # save original img
    if image is None and url:
        res = request.urlopen(url)
        image = StringIO(res.read())
    else:
        image = StringIO(image)

    k.key = path
    k.set_contents_from_file(image)
    k.make_public()

    # make thumbnails
    if make_thumbnails:
        make_thumb(image)

    image.close()
    origin_url = 'http://assets.maybe.cn/%s' % path
    return origin_url


@celery.task
def make_thumbnails(space, path, url, async=True):
    """
    指纹
    :param space:
    :param path:
    :param url:
    :return:
    """
    connect = boto.connect_s3(settings.AWS_ACCESS_KEY_ID, settings.AWS_SECRET_ACCESS_KEY)
    bucket_name = space
    bucket = connect.get_bucket(bucket_name)
    k = Key(bucket)

    # save original img
    res = request.urlopen(url)
    image = StringIO(res.read())

    img = Image.open(image)
    for size in [(480, 480), (180, 180)]:
        output = StringIO()
        img2 = ImageOps.fit(img, size, Image.ANTIALIAS)
        img2.save(output, 'JPEG')

        k.key = 'post_thumbs/%sx%s/%s' % (size[0], size[1], path)
        k.set_contents_from_string(output.getvalue())
        k.make_public()
        output.close()


@celery.task
def save_avatar(space, path, url, save_original=False, async=True):
    """

    :param space:
    :param path:
    :param url:
    :param save_original:
    :return:
    """
    connect = boto.connect_s3(settings.AWS_ACCESS_KEY_ID, settings.AWS_SECRET_ACCESS_KEY)
    bucket_name = space
    bucket = connect.get_bucket(bucket_name)
    k = Key(bucket)
    res = request.urlopen(url)
    image = StringIO(res.read())

    if save_original:
        k.key = path
        k.set_contents_from_file(image)
        k.make_public()

        img = Image.open(image)
        for size in [(200, 200), (80, 80)]:
            output = StringIO()
            img2 = ImageOps.fit(img, size, Image.ANTIALIAS)
            img2.save(output, 'JPEG')

            k.key = 'avatar_thmubs/%sx%s/%s' % (size[0], size[1], path)
            k.set_contents_from_string(output.getvalue())
            k.make_public()
            output.close()


