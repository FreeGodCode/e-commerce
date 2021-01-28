# -*- coding: utf-8  -*-
# @Author: ty
# @File name: snapshot.py 
# @IDE: PyCharm
# @Create time: 1/14/21 12:22 AM
# @Description: 简介
from datetime import datetime

from app import db

__all__ = ['ItemSnapshot', 'ItemSpecSnapshot']

from app.models.inventory.item import Item, ItemSpec


class ItemSnapshot(db.Document):
    meta = {
        'db_alias': 'db_order',
        'indexes': ['item_id', 'web_id', 'head']
    }
    head = db.IntField(required=True, default=0)
    specs = db.ListField(db.ReferenceField('ItemSpecSnapshot'))
    created_at = db.DateTimeField(default=datetime.utcnow())

    def __unicode__(self):
        return '%s' % self.head

    @classmethod
    def create(cls, item):
        data = item._data
        shot = cls(**data)
        shot.head = shot.item_id
        shot.save()
        return shot

    @property
    def small_thumbnail(self):
        return self.primary_img[:23] + 'thumbnails/150x150/' + self.primary_img[23:]

    @property
    def large_thumbnail(self):
        return self.primary_img[:23] + 'thumbnails/400x400/' + self.primary_img[23:]

    def update_to_head(self):
        head = Item.objects(item_id=self.head).first()
        if head:
            data = head._data
            for k, v in data.items():
                setattr(self, k, v)
            self.save()
        else:
            return self

    @property
    def is_changed(self):
        head = Item.objects(item_id=self.head).first()
        if not head:
            return True
        if self.modify != head.modified:
            return True
        return False


class ItemSpecSnapshot(db.DynamicDocument):
    meta = {
        'db_alias': 'db_order',
        'indexes': ['item_id', 'sku', 'head']
    }
    head = db.IntField(required=True, default=0)
    item = db.ReferenceField('ItemSnapshot')
    created_at = db.DateTimeField(default=datetime.utcnow())

    def __unicode__(self):
        return '%s:%s' % (self.item.head, self.head)

    @classmethod
    def create(cls, spec, itemsnapshot=None):
        if not itemsnapshot:
            itemsnapshot = ItemSnapshot.create(spec.item).save()

        data = spec._data
        shot = cls(**data)
        shot.head = shot.sku
        shot.item = itemsnapshot
        shot.save()
        itemsnapshot.specs.append(shot)
        itemsnapshot.save()
        return shot

    def update_to_head(self):
        head = ItemSpec.objects(sku=self.head).first()
        if self.item and isinstance(self.item, ItemSnapshot):
            self.item.update_to_head()

        if head:
            data = head._data
            for k, v in data.items():
                setattr(self, k, v)
            self.save()

        else:
            return self

    @property
    def is_change(self):
        head = ItemSpec.objects(sku=self.head).first()
        if not head:
            return True
        if self.modified != head.modified:
            return True

        return False
