# -*- coding: utf-8 -*-
from odoo import models, fields

class VideoCategory(models.Model):
    _name = 'erpcloud.video.category'
    _description = 'Video Category'
    _order = 'sequence, id'

    name = fields.Char(string='Tên danh mục', required=True, translate=True)
    sequence = fields.Integer(string='Thứ tự', default=10)
    slug = fields.Char(string='Slug', required=True)
    active = fields.Boolean(default=True)
