# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import re
import json
from datetime import datetime
from lxml import html as lxml_html


class BlogPost(models.Model):
    _name = 'erpcloud.blog.post'
    _description = 'Blog Post'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'website.seo.metadata', 'website.published.mixin']
    _order = 'published_date desc, create_date desc'

    # ==================== BASIC INFO ====================

    name = fields.Char(
        string='Tiêu đề',
        required=True,
        translate=True,
        tracking=True,
        help="Tiêu đề bài viết"
    )

    subtitle = fields.Char(
        string='Tiêu đề phụ',
        translate=True,
        help="Tiêu đề phụ (hiển thị dưới tiêu đề chính)"
    )

    slug = fields.Char(
        string='URL Slug',
        required=False,
        index=True,
        tracking=True,
        help="URL-friendly slug (auto-generated from title)"
    )

    # ==================== AUTHOR INFO ====================

    author_id = fields.Many2one(
        'res.users',
        string='Tác giả',
        default=lambda self: self.env.user,
        required=True,
        tracking=True
    )

    author_name = fields.Char(
        string='Tên tác giả hiển thị',
        help="Override tên tác giả (nếu để trống sẽ dùng tên user)"
    )

    author_avatar = fields.Image(
        string='Avatar tác giả',
        related='author_id.image_128',
        readonly=True
    )

    # ==================== DATES ====================

    published_date = fields.Datetime(
        string='Ngày xuất bản',
        tracking=True,
        help="Ngày xuất bản bài viết (để trống = xuất bản ngay)"
    )

    create_date = fields.Datetime(
        string='Ngày tạo',
        readonly=True
    )

    write_date = fields.Datetime(
        string='Ngày cập nhật',
        readonly=True
    )

    # ==================== CONTENT ====================

    content = fields.Html(
        string='Nội dung',
        sanitize=True,
        translate=True,
        help="Nội dung bài viết (HTML)"
    )

    excerpt = fields.Text(
        string='Trích đoạn',
        translate=True,
        help="Mô tả ngắn hiển thị trong danh sách (auto-generate nếu để trống)"
    )

    cover_image = fields.Image(
        string='Ảnh bìa',
        max_width=1920,
        max_height=1080,
        help="Ảnh bìa bài viết"
    )

    cover_image_url = fields.Char(
        string='URL ảnh bìa',
        help="URL ảnh bìa từ nguồn external (CDN, etc.)"
    )

    # ==================== CATEGORIZATION ====================

    category_id = fields.Many2one(
        'erpcloud.blog.category',
        string='Danh mục',
        required=True,
        tracking=True,
        help="Danh mục chính của bài viết"
    )

    tag_ids = fields.Many2many(
        'erpcloud.blog.tag',
        'erpcloud_blog_post_tag_rel',
        'post_id',
        'tag_id',
        string='Tags',
        help="Thẻ tag của bài viết"
    )

    # ==================== SEO FIELDS ====================

    seo_title = fields.Char(
        string='SEO Title',
        translate=True,
        help='Meta title (50-60 chars recommended)'
    )

    seo_description = fields.Text(
        string='SEO Description',
        translate=True,
        help='Meta description (150-160 chars recommended)'
    )

    seo_keywords = fields.Char(
        string='SEO Keywords',
        help='Comma-separated keywords'
    )

    # Open Graph (Facebook, LinkedIn)
    og_title = fields.Char(
        string='OG Title',
        translate=True,
        help='Open Graph title (Facebook, LinkedIn)'
    )

    og_description = fields.Text(
        string='OG Description',
        translate=True,
        help='Open Graph description'
    )

    og_image = fields.Image(
        string='OG Image',
        max_width=1200,
        max_height=630,
        help='Open Graph image (1200x630px recommended)'
    )

    # Schema.org Structured Data
    schema_type = fields.Selection([
        ('article', 'Article'),
        ('blog_posting', 'BlogPosting'),
        ('news_article', 'NewsArticle'),
        ('tech_article', 'TechArticle'),
    ], default='blog_posting', string='Schema Type', required=True)

    # ==================== STATUS & WORKFLOW ====================

    state = fields.Selection([
        ('draft', 'Nháp'),
        ('review', 'Chờ duyệt'),
        ('published', 'Đã xuất bản'),
        ('archived', 'Lưu trữ'),
    ], default='draft', required=True, tracking=True, string='Trạng thái')

    is_featured = fields.Boolean(
        string='Bài viết nổi bật',
        tracking=True,
        help="Hiển thị trong slider featured posts"
    )

    is_pinned = fields.Boolean(
        string='Ghim lên đầu',
        tracking=True,
        help="Luôn hiển thị ở đầu danh sách"
    )

    allow_comments = fields.Boolean(
        string='Cho phép bình luận',
        default=True,
        help="Cho phép người dùng bình luận"
    )

    # ==================== ANALYTICS ====================

    view_count = fields.Integer(
        string='Lượt xem',
        default=0,
        readonly=True,
        help="Tổng số lượt xem"
    )

    reading_time = fields.Integer(
        string='Thời gian đọc (phút)',
        compute='_compute_reading_time',
        store=True,
        help="Ước tính thời gian đọc (250 words/min)"
    )

    comment_ids = fields.One2many(
        'erpcloud.blog.comment',
        'post_id',
        string='Bình luận',
        help="Danh sách bình luận của bài viết"
    )

    comment_count = fields.Integer(
        string='Số bình luận',
        compute='_compute_comment_count',
        store=True,
        help="Tổng số bình luận đã duyệt"
    )

    share_count = fields.Integer(
        string='Lượt chia sẻ',
        default=0,
        help="Tổng số lượt chia sẻ"
    )

    # ==================== RELATED CONTENT ====================

    related_post_ids = fields.Many2many(
        'erpcloud.blog.post',
        'erpcloud_blog_post_related_rel',
        'post_id',
        'related_id',
        string='Bài viết liên quan',
        help="Bài viết liên quan (auto-suggest based on category/tags)"
    )

    # ==================== TABLE OF CONTENTS ====================

    toc_json = fields.Text(
        string='Table of Contents JSON',
        compute='_compute_toc',
        store=True,
        help="Auto-generated from H2, H3 tags"
    )

    # ==================== ACTIVE ====================

    active = fields.Boolean(
        string='Active',
        default=True
    )

    # ==================== COMPUTED FIELDS ====================

    @api.depends('content')
    def _compute_reading_time(self):
        """Calculate reading time based on word count (250 words/min)"""
        for record in self:
            if record.content:
                # Strip HTML tags
                text = re.sub(r'<[^>]+>', '', record.content)
                # Count words
                word_count = len(text.split())
                # Calculate reading time (250 words per minute)
                record.reading_time = max(1, round(word_count / 250))
            else:
                record.reading_time = 1

    @api.depends('content')
    def _compute_toc(self):
        """Auto-generate table of contents from H2, H3 tags"""
        for record in self:
            if record.content:
                try:
                    tree = lxml_html.fromstring(record.content)
                    toc = []
                    for heading in tree.xpath('.//h2 | .//h3'):
                        level = int(heading.tag[1])  # 2 or 3
                        text = heading.text_content().strip()
                        # Generate ID from text
                        heading_id = re.sub(r'[^a-z0-9]+', '-', text.lower()).strip('-')
                        toc.append({
                            'level': level,
                            'text': text,
                            'id': heading_id
                        })
                    record.toc_json = json.dumps(toc, ensure_ascii=False)
                except:
                    record.toc_json = '[]'
            else:
                record.toc_json = '[]'

    @api.depends('comment_ids', 'comment_ids.state')
    def _compute_comment_count(self):
        """Count approved comments"""
        for record in self:
            record.comment_count = len(record.comment_ids.filtered(lambda c: c.state == 'approved'))

    # ==================== CONSTRAINTS ====================

    @api.constrains('slug')
    def _check_slug_unique(self):
        """Ensure slug is unique"""
        for record in self:
            if record.slug:
                duplicate = self.search([
                    ('slug', '=', record.slug),
                    ('id', '!=', record.id)
                ], limit=1)
                if duplicate:
                    raise ValidationError(f'Slug "{record.slug}" đã tồn tại! Vui lòng chọn slug khác.')

    @api.constrains('seo_title')
    def _check_seo_title_length(self):
        """Check SEO title length"""
        for record in self:
            if record.seo_title and len(record.seo_title) > 60:
                raise ValidationError('SEO Title nên dưới 60 ký tự để hiển thị tốt trên Google!')

    @api.constrains('seo_description')
    def _check_seo_description_length(self):
        """Check SEO description length"""
        for record in self:
            if record.seo_description and len(record.seo_description) > 160:
                raise ValidationError('SEO Description nên dưới 160 ký tự để hiển thị tốt trên Google!')

    # ==================== CRUD METHODS ====================

    @api.model
    def _generate_slug(self, text):
        """Generate URL-friendly slug from text"""
        if not text:
            return ''

        # Convert to lowercase
        slug = text.lower()

        # Vietnamese character mapping
        vietnamese_map = {
            'à': 'a', 'á': 'a', 'ả': 'a', 'ã': 'a', 'ạ': 'a',
            'ă': 'a', 'ằ': 'a', 'ắ': 'a', 'ẳ': 'a', 'ẵ': 'a', 'ặ': 'a',
            'â': 'a', 'ầ': 'a', 'ấ': 'a', 'ẩ': 'a', 'ẫ': 'a', 'ậ': 'a',
            'đ': 'd',
            'è': 'e', 'é': 'e', 'ẻ': 'e', 'ẽ': 'e', 'ẹ': 'e',
            'ê': 'e', 'ề': 'e', 'ế': 'e', 'ể': 'e', 'ễ': 'e', 'ệ': 'e',
            'ì': 'i', 'í': 'i', 'ỉ': 'i', 'ĩ': 'i', 'ị': 'i',
            'ò': 'o', 'ó': 'o', 'ỏ': 'o', 'õ': 'o', 'ọ': 'o',
            'ô': 'o', 'ồ': 'o', 'ố': 'o', 'ổ': 'o', 'ỗ': 'o', 'ộ': 'o',
            'ơ': 'o', 'ờ': 'o', 'ớ': 'o', 'ở': 'o', 'ỡ': 'o', 'ợ': 'o',
            'ù': 'u', 'ú': 'u', 'ủ': 'u', 'ũ': 'u', 'ụ': 'u',
            'ư': 'u', 'ừ': 'u', 'ứ': 'u', 'ử': 'u', 'ữ': 'u', 'ự': 'u',
            'ỳ': 'y', 'ý': 'y', 'ỷ': 'y', 'ỹ': 'y', 'ỵ': 'y',
        }

        # Replace Vietnamese characters
        for vn_char, en_char in vietnamese_map.items():
            slug = slug.replace(vn_char, en_char)

        # Replace spaces and special characters with hyphens
        slug = re.sub(r'[^a-z0-9]+', '-', slug)

        # Remove leading/trailing hyphens
        slug = slug.strip('-')

        # Remove consecutive hyphens
        slug = re.sub(r'-+', '-', slug)

        return slug

    @api.model_create_multi
    def create(self, vals_list):
        """Auto-generate slug, excerpt, SEO fields on create"""
        for vals in vals_list:
            # Auto-generate slug from title
            if 'name' in vals and 'slug' not in vals:
                vals['slug'] = self._generate_slug(vals['name'])
            elif 'slug' in vals:
                vals['slug'] = self._generate_slug(vals['slug'])

            # Auto-generate excerpt from content
            if 'content' in vals and 'excerpt' not in vals:
                vals['excerpt'] = self._generate_excerpt(vals['content'])

            # Auto-generate SEO fields
            if 'name' in vals:
                if 'seo_title' not in vals:
                    vals['seo_title'] = vals['name'][:60]
                if 'og_title' not in vals:
                    vals['og_title'] = vals['name']

            if 'excerpt' in vals and 'seo_description' not in vals:
                vals['seo_description'] = vals['excerpt'][:160]

            # Set published_date if publishing
            if vals.get('state') == 'published' and 'published_date' not in vals:
                vals['published_date'] = fields.Datetime.now()

        return super().create(vals_list)

    def write(self, vals):
        """Auto-update slug, excerpt, SEO fields on write"""
        # Auto-generate slug if title changes
        if 'name' in vals and 'slug' not in vals:
            vals['slug'] = self._generate_slug(vals['name'])
        elif 'slug' in vals:
            vals['slug'] = self._generate_slug(vals['slug'])

        # Auto-generate excerpt if content changes
        if 'content' in vals and 'excerpt' not in vals:
            vals['excerpt'] = self._generate_excerpt(vals['content'])

        # Set published_date when publishing
        if vals.get('state') == 'published':
            for record in self:
                if not record.published_date:
                    vals['published_date'] = fields.Datetime.now()

        return super().write(vals)

    @api.model
    def _generate_excerpt(self, content, max_length=200):
        """Generate excerpt from HTML content"""
        if not content:
            return ''

        # Strip HTML tags
        text = re.sub(r'<[^>]+>', '', content)
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        # Truncate to max_length
        if len(text) > max_length:
            text = text[:max_length].rsplit(' ', 1)[0] + '...'

        return text

    # ==================== ACTIONS ====================

    def action_publish(self):
        """Publish post"""
        self.ensure_one()
        self.write({
            'state': 'published',
            'is_published': True,
            'published_date': fields.Datetime.now()
        })
        return True

    def action_unpublish(self):
        """Unpublish post (move to draft)"""
        self.ensure_one()
        self.write({'state': 'draft', 'is_published': False})
        return True

    def action_archive(self):
        """Archive post"""
        self.ensure_one()
        self.write({'state': 'archived', 'is_published': False})
        return True

    def action_submit_review(self):
        """Submit for review"""
        self.ensure_one()
        self.write({'state': 'review'})
        return True

    def action_increment_view(self):
        """Increment view count"""
        self.ensure_one()
        self._track_view()
        return True

    def _track_view(self):
        """Count page views atomically without storing visitor identifiers."""
        for post in self:
            self.env.cr.execute(
                'UPDATE erpcloud_blog_post SET view_count = COALESCE(view_count, 0) + 1 WHERE id = %s',
                [post.id],
            )
        self.invalidate_recordset(['view_count'])

    def action_increment_share(self):
        """Increment share count"""
        self.ensure_one()
        self.sudo().write({'share_count': self.share_count + 1})
        return True

    # ==================== SEARCH ====================

    @api.model
    def _name_search(self, name, args=None, operator='ilike', limit=100, name_get_uid=None):
        """Search by name, slug, or excerpt"""
        args = args or []
        domain = []
        if name:
            domain = ['|', '|', ('name', operator, name), ('slug', operator, name), ('excerpt', operator, name)]
        return self._search(domain + args, limit=limit, access_rights_uid=name_get_uid)
