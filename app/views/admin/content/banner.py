# -*- coding: utf-8  -*-
# @Author: ty
# @File name: banner.py 
# @IDE: PyCharm
# @Create time: 1/21/21 11:16 AM
# @Description:
import datetime

from flask import request, flash, redirect, jsonify, url_for
from flask_admin import expose
from flask_babel import gettext
from mongoengine import ValidationError
from werkzeug.utils import secure_filename

from app.models.content.banner import Banner
from app.models.content.board import Board
from app.utils.utils import redirect_url
from app.views.admin import AdminView


class BannerView(AdminView):
    """轮播图视图处理类"""
    _permission = 'content'

    @expose(url='/', methods=['GET'])
    def index(self):
        banners = Banner.objects().order_by('-order')
        return self.render('admin/content/banner.html', banner=banners)

    @expose(url='/set/<id>', methods=['POST'])
    def set(self, id):
        """

        :param id:
        :return:
        """
        banner = Banner.objects(id=id).first()
        date_from = request.form.get('from')
        date_until = request.form.get('until')
        if date_from:
            try:
                dt = datetime.datetime.strptime(date_from, '%Y-%m-%d %H:%M:%S')
            except ValueError:
                flash(gettext('invalid date format. example: 2020-01-09 12:11:11'), 'error')
            else:
                banner.date_from = dt
        if date_until:
            try:
                dt = datetime.datetime.strptime(date_until, '%Y-%m-%d %H:%M:%S')
            except ValueError:
                flash(gettext('invalid date format. example: 2020-01-09 12:11:11'), 'error')
            else:
                banner.date_until = dt

        banner.target = request.form.get('target').strip()
        banner.banner_type = request.form.get('banner_type').strip()
        banner.save()
        flash('successfully updated')
        return redirect(redirect_url())

    @expose(url='/move', methods=['PATCH'])
    def move(self):
        """

        :return:
        """
        a_from = request.form.get('from')
        a_to = request.form.get('to')
        if a_from and a_to:
            b_from = Banner.objects(id=a_from).first_or_404()
            b_to = Banner.objects(id=a_to).first_or_404()
            b_from.order, b_to.order = b_to.order, b_from.order
            b_from.save()
            b_to.save()
            return jsonify(message='OK', bfrom=b_from.order, bto=b_to.order)
        return jsonify(message='Failed')

    @expose(url='/unpublish/<id>', methods=['GET'])
    def unpublish(self, id):
        """
        发布
        :param id:
        :return:
        """
        banner = Banner.objects(id=id).first()
        banner.published = False
        banner.save()
        return redirect(redirect_url())

    @expose(url='/delete/<id>', methods=['GET'])
    def delete(self, id):
        """
        根据id删除
        :param id:
        :return:
        """
        banner = Banner.objects(id=id).first()
        if banner:
            banner.delete()

        return redirect(redirect_url())

    @expose(url='/upload_img/<id>', methods=['POST'])
    def upload_img(self, id):
        """
        上传轮播图
        :param id:
        :return:
        """
        banner = Banner.objects(id=id).first()
        img = request.files.get('img')
        if img:
            name, extension = img.filename.rsplit('.', 1)
            name = datetime.datetime.now().strftime('%Y-%m-%d-%H%M%S')
            filename = secure_filename(name)
            path = '{}/{}.{}'.format('banner', filename, extension)
            url = jobs.image.upload('maybe-img', path, image=img.read(), make_thumbnails=True)
            banner.img = url
            banner.save()

        return redirect(redirect_url())

    @expose(url='/upload', methods=['GET', 'POST'])
    def upload(self):
        """

        :return:
        """
        if request.method == 'GET':
            return self.render('admin/content/upload.html')

        target = request.form.get('boardid', '')
        banner_type = request.form.get('banner_type')
        img = request.files.get('image')
        name, ext = img.filename.rsplit('.', 1)
        name = datetime.datetime.now().strftime('%Y-%m-%d-%H%M%S')
        filename = secure_filename(name)
        path = '{}/{}.{}'.format('banner', filename, ext)
        url = jobs.image.upload('maybe-img', path, image=img.read(), make_thumbnails=True)

        if banner_type == 'URL':
            if target.startswith('http') == False:
                flash(gettext('upload failed. if you select board, please fill in board id, otherwise fill in url.'))
                return redirect(redirect_url())

        # 广播
        elif banner_type == 'BOARD':
            try:
                board = Board.objects(id=target).first()
            except ValidationError:
                flash('upload failed, please fill in a valid board id')
                return redirect(redirect_url())

        Banner(banner_type=banner_type, target=target, img=url, published=True).save()
        flash(gettext('upload successfully'))

        return redirect(url_for('bannerview.index'))


admin.add_view(BannerView(name='Banner', category='Content', menu_icon_type='fa', menu_icon_value='gift'))
