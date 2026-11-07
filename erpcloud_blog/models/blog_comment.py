# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import ValidationError
import re


class BlogComment(models.Model):
    _name = 'erpcloud.blog.comment'
    _description = 'Blog Comment'
    _order = 'create_date desc'
    _parent_name = 'parent_id'
    _parent_store = True

    post_id = fields.Many2one(
        'erpcloud.blog.post',
        string='Bài viết',
        required=True,
        ondelete='cascade',
        index=True
    )

    parent_id = fields.Many2one(
        'erpcloud.blog.comment',
        string='Bình luận cha',
        ondelete='cascade',
        index=True,
        help="For nested/threaded comments"
    )

    parent_path = fields.Char(index=True)

    child_ids = fields.One2many(
        'erpcloud.blog.comment',
        'parent_id',
        string='Phản hồi'
    )

    # Author info
    author_name = fields.Char(
        string='Tên',
        required=True,
        help="Tên người bình luận"
    )

    author_email = fields.Char(
        string='Email',
        required=True,
        help="Email người bình luận"
    )

    author_website = fields.Char(
        string='Website',
        help="Website của người bình luận (optional)"
    )

    # Content
    content = fields.Text(
        string='Nội dung',
        required=True,
        help="Nội dung bình luận"
    )

    # Tracking
    ip_address = fields.Char(
        string='IP Address',
        help="IP address of commenter"
    )

    user_agent = fields.Text(
        string='User Agent',
        help="Browser user agent"
    )

    # Moderation
    state = fields.Selection([
        ('pending', 'Chờ duyệt'),
        ('approved', 'Đã duyệt'),
        ('spam', 'Spam'),
        ('rejected', 'Từ chối'),
    ], default='pending', required=True, string='Trạng thái')

    is_author_reply = fields.Boolean(
        string='Phản hồi từ tác giả',
        help="Đánh dấu là phản hồi từ tác giả bài viết"
    )

    create_date = fields.Datetime(
        string='Ngày tạo',
        readonly=True
    )

    active = fields.Boolean(
        string='Active',
        default=True
    )

    # ==================== CONSTRAINTS ====================

    @api.constrains('author_email')
    def _check_email(self):
        """Validate email format"""
        for record in self:
            if record.author_email:
                if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', record.author_email):
                    raise ValidationError('Email không hợp lệ!')

    @api.constrains('parent_id')
    def _check_parent_recursion(self):
        """Prevent circular parent relationships"""
        if not self._check_recursion():
            raise ValidationError('Không thể tạo bình luận đệ quy!')

    # ==================== ACTIONS ====================

    def action_approve(self):
        """Approve comment"""
        self.write({'state': 'approved'})
        # Update post comment count
        self.post_id._compute_comment_count()
        return True

    def action_reject(self):
        """Reject comment"""
        self.write({'state': 'rejected'})
        return True

    def action_mark_spam(self):
        """Mark as spam"""
        self.write({'state': 'spam'})
        return True

    def action_pending(self):
        """Move back to pending"""
        self.write({'state': 'pending'})
        return True
