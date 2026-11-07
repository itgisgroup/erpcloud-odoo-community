# -*- coding: utf-8 -*-

from odoo import models, fields, api


class BlogMedia(models.Model):
    _name = 'erpcloud.blog.media'
    _description = 'Blog Media Library'
    _order = 'create_date desc'

    name = fields.Char(
        string='Tên file',
        required=True,
        help="Tên file media"
    )

    description = fields.Text(
        string='Mô tả',
        help="Mô tả về file media"
    )

    file_type = fields.Selection([
        ('image', 'Hình ảnh'),
        ('video', 'Video'),
        ('document', 'Tài liệu'),
    ], required=True, string='Loại file', default='image')

    # File info
    file_data = fields.Binary(
        string='File',
        attachment=True
    )

    file_name = fields.Char(
        string='File Name'
    )

    file_size = fields.Integer(
        string='File Size (bytes)',
        help="Kích thước file (bytes)"
    )

    mime_type = fields.Char(
        string='MIME Type',
        help="MIME type của file"
    )

    url = fields.Char(
        string='URL',
        help="URL của file (nếu lưu trên CDN hoặc external)"
    )

    # Image specific
    image = fields.Image(
        string='Image',
        max_width=1920,
        max_height=1080
    )

    thumbnail = fields.Image(
        string='Thumbnail',
        max_width=300,
        max_height=300
    )

    alt_text = fields.Char(
        string='Alt Text',
        help='Alt text cho SEO và accessibility'
    )

    width = fields.Integer(
        string='Width (px)',
        help="Chiều rộng ảnh (px)"
    )

    height = fields.Integer(
        string='Height (px)',
        help="Chiều cao ảnh (px)"
    )

    # Video specific
    video_url = fields.Char(
        string='Video URL',
        help='URL video (YouTube, Vimeo, etc.)'
    )

    video_embed_code = fields.Text(
        string='Embed Code',
        help='Mã nhúng video'
    )

    duration = fields.Integer(
        string='Duration (seconds)',
        help="Thời lượng video (giây)"
    )

    # Categorization
    folder = fields.Char(
        string='Folder',
        help='Thư mục (để tổ chức media)'
    )

    tags = fields.Char(
        string='Tags',
        help='Tags (phân cách bằng dấu phẩy)'
    )

    # Usage tracking
    usage_count = fields.Integer(
        string='Lượt sử dụng',
        default=0,
        help="Số lần media được sử dụng trong bài viết"
    )

    create_date = fields.Datetime(
        string='Ngày tải lên',
        readonly=True
    )

    active = fields.Boolean(
        string='Active',
        default=True
    )

    # ==================== METHODS ====================

    @api.model_create_multi
    def create(self, vals_list):
        """Auto-generate thumbnail for images"""
        records = super().create(vals_list)
        for record in records:
            if record.file_type == 'image' and record.image and not record.thumbnail:
                record.thumbnail = record.image
        return records

    def action_increment_usage(self):
        """Increment usage count"""
        self.ensure_one()
        self.sudo().write({'usage_count': self.usage_count + 1})
        return True
