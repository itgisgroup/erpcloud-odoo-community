# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import re

class Video(models.Model):
    _name = 'erpcloud.video'
    _description = 'Tutorial Video'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'website.seo.metadata', 'website.published.mixin']
    _order = 'sequence, published_date desc'

    name = fields.Char(string='Tiêu đề', required=True, translate=True, tracking=True)
    sequence = fields.Integer(string='Thứ tự', default=10)
    video_url = fields.Char(string='YouTube URL', required=True, tracking=True)
    video_id = fields.Char(string='Video ID', compute='_compute_video_id', store=True)
    duration = fields.Char(string='Thời lượng', help="Ví dụ: 3:42")
    description = fields.Text(string='Mô tả ngắn', translate=True)
    content = fields.Html(string='Nội dung chi tiết', translate=True)

    category_id = fields.Many2one('erpcloud.video.category', string='Danh mục', required=True)
    tag_ids = fields.Many2many('erpcloud.video.tag', string='Tags')

    published_date = fields.Datetime(string='Ngày xuất bản', default=fields.Datetime.now)
    is_featured = fields.Boolean(string='Nổi bật', default=False)
    view_count = fields.Integer(string='Lượt xem', default=0, readonly=True)

    state = fields.Selection([
        ('draft', 'Nháp'),
        ('published', 'Đã xuất bản'),
    ], default='draft', string='Trạng thái', tracking=True)

    @api.depends('video_url')
    def _compute_video_id(self):
        for record in self:
            if record.video_url:
                # Regex to extract YouTube ID
                pattern = r'(?:https?:\/\/)?(?:www\.)?(?:youtube\.com\/(?:[^\/\n\s]+\/\S+\/|(?:v|e(?:mbed)?)\/|\S*?[?&]v=)|youtu\.be\/)([a-zA-Z0-9_-]{11})'
                match = re.search(pattern, record.video_url)
                record.video_id = match.group(1) if match else False
            else:
                record.video_id = False

    def action_publish(self):
        if any(not video.video_id for video in self):
            raise ValidationError('Enter a valid YouTube URL before publishing.')
        self.write({'state': 'published', 'is_published': True})

    def action_unpublish(self):
        self.write({'state': 'draft', 'is_published': False})
