# -*- coding: utf-8  -*-
# @Author: ty
# @File name: statistics.py 
# @IDE: PyCharm
# @Create time: 1/17/21 5:18 PM
# @Description: 统计
from app import db

__all__ = ['Statistics']


class Statistics(db.Document):
    """统计"""
    meta = {
        'db_alias': 'db_inventory',
        'indexes': ['tag', 'sub_category', 'main_category', 'brand'],
    }
    main_category = db.StringField()
    sub_category = db.StringField()
    brand = db.StringField()
    tag = db.StringField()
    sex_tag = db.StringField()
    count = db.IntField(required=True, defualt=1)

    @classmethod
    def create(cls, main_category, sub_category, brand, tags, sex_tag):
        if not tags:
            tags = [None]

        for tag in tags:
            try:
                stats = cls.objects.get(main_category=main_category, sub_category=sub_category, brand=brand, tag=tag,
                                        sex_tag=sex_tag)
                stats.count += 1
                stats.save()
            except:
                stats = cls(main_category=main_category, sub_category=sub_category, brand=brand, tag=tag,
                            sex_tag=sex_tag)
                stats.save()

    def to_json(self):
        return dict(
            main_category=self.main_category,
            sub_category=self.sub_category,
            brand=self.brand,
            tag=self.tag,
            sex_tag=self.sex_tag,
            count=self.count,
        )
