# -*- coding: utf-8 -*-
from odoo import models, fields

class VideoTag(models.Model):
    _name = 'erpcloud.video.tag'
    _description = 'Video Tag'

    name = fields.Char(string='Tên tag', required=True, translate=True)
    slug = fields.Char(string='Slug', index=True)
    color = fields.Integer(string='Màu sắc')
    active = fields.Boolean(default=True)
