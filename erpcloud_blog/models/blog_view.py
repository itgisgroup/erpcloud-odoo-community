# -*- coding: utf-8 -*-

from odoo import models, fields, api


class BlogView(models.Model):
    _name = 'erpcloud.blog.view'
    _description = 'Blog View Tracking'
    _order = 'view_date desc'
    _rec_name = 'post_id'

    post_id = fields.Many2one(
        'erpcloud.blog.post',
        string='Bài viết',
        required=True,
        ondelete='cascade',
        index=True
    )

    session_id = fields.Char(
        string='Session ID',
        index=True,
        help="Browser session ID"
    )

    ip_address = fields.Char(
        string='IP Address',
        help="IP address của người xem"
    )

    user_agent = fields.Text(
        string='User Agent',
        help="Browser user agent"
    )

    referrer = fields.Char(
        string='Referrer URL',
        help="URL trang giới thiệu"
    )

    # UTM Tracking
    utm_source = fields.Char(
        string='UTM Source',
        help="UTM source parameter"
    )

    utm_medium = fields.Char(
        string='UTM Medium',
        help="UTM medium parameter"
    )

    utm_campaign = fields.Char(
        string='UTM Campaign',
        help="UTM campaign parameter"
    )

    utm_term = fields.Char(
        string='UTM Term',
        help="UTM term parameter"
    )

    utm_content = fields.Char(
        string='UTM Content',
        help="UTM content parameter"
    )

    view_date = fields.Datetime(
        string='Ngày xem',
        default=fields.Datetime.now,
        index=True,
        required=True
    )

    reading_time_seconds = fields.Integer(
        string='Thời gian đọc (giây)',
        help="Thời gian thực tế đọc bài viết"
    )

    scroll_depth = fields.Integer(
        string='Scroll Depth (%)',
        help="Phần trăm scroll xuống (0-100%)"
    )

    # Device info
    device_type = fields.Selection([
        ('desktop', 'Desktop'),
        ('mobile', 'Mobile'),
        ('tablet', 'Tablet'),
    ], string='Loại thiết bị')

    browser = fields.Char(
        string='Browser',
        help="Tên trình duyệt"
    )

    os = fields.Char(
        string='Operating System',
        help="Hệ điều hành"
    )

    # ==================== METHODS ====================

    @api.model
    def track_view(self, post_id, session_id, ip_address=None, user_agent=None,
                   referrer=None, utm_params=None):
        """Track a blog post view"""
        vals = {
            'post_id': post_id,
            'session_id': session_id,
            'ip_address': ip_address,
            'user_agent': user_agent,
            'referrer': referrer,
        }

        if utm_params:
            vals.update({
                'utm_source': utm_params.get('utm_source'),
                'utm_medium': utm_params.get('utm_medium'),
                'utm_campaign': utm_params.get('utm_campaign'),
                'utm_term': utm_params.get('utm_term'),
                'utm_content': utm_params.get('utm_content'),
            })

        # Create view record
        view = self.create(vals)

        # Increment post view count
        post = self.env['erpcloud.blog.post'].browse(post_id)
        post.action_increment_view()

        return view.id
