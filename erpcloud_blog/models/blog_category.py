# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import ValidationError
import re


class BlogCategory(models.Model):
    _name = 'erpcloud.blog.category'
    _description = 'Blog Category'
    _order = 'sequence, name'
    _parent_name = 'parent_id'
    _parent_store = True

    name = fields.Char(
        string='Tên danh mục',
        required=True,
        translate=True,
        help="Tên danh mục blog"
    )

    slug = fields.Char(
        string='URL Slug',
        required=True,
        index=True,
        help="URL-friendly slug (auto-generated from name)"
    )

    description = fields.Text(
        string='Mô tả',
        translate=True,
        help="Mô tả ngắn về danh mục"
    )

    parent_id = fields.Many2one(
        'erpcloud.blog.category',
        string='Danh mục cha',
        ondelete='cascade',
        index=True
    )

    parent_path = fields.Char(index=True)

    child_ids = fields.One2many(
        'erpcloud.blog.category',
        'parent_id',
        string='Danh mục con'
    )

    icon = fields.Char(
        string='Icon Class',
        help='Font Awesome icon class (e.g., fa-book, fa-video)',
        default='fa-folder'
    )

    color = fields.Char(
        string='Màu sắc',
        help='Hex color code (e.g., #2563eb)',
        default='#2563eb'
    )

    cover_image = fields.Image(
        string='Ảnh bìa danh mục',
        max_width=1920,
        max_height=600
    )

    sequence = fields.Integer(
        string='Thứ tự',
        default=10,
        help="Thứ tự hiển thị"
    )

    # SEO Fields
    seo_title = fields.Char(
        string='SEO Title',
        help='Meta title (60 chars max)'
    )

    seo_description = fields.Text(
        string='SEO Description',
        help='Meta description (160 chars max)'
    )

    # Stats
    post_count = fields.Integer(
        string='Số bài viết',
        compute='_compute_post_count',
        store=True,
        help="Tổng số bài viết đã xuất bản trong danh mục này"
    )

    active = fields.Boolean(
        string='Active',
        default=True
    )

    @api.depends('name')
    def _compute_slug(self):
        """Auto-generate slug from name"""
        for record in self:
            if record.name and not record.slug:
                record.slug = self._generate_slug(record.name)

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

    @api.depends('child_ids.post_count')
    def _compute_post_count(self):
        """Compute total post count including child categories"""
        for record in self:
            # Count posts directly in this category
            direct_count = self.env['erpcloud.blog.post'].search_count([
                ('category_id', '=', record.id),
                ('state', '=', 'published')
            ])

            # Count posts in child categories
            child_count = sum(record.child_ids.mapped('post_count'))

            record.post_count = direct_count + child_count

    @api.constrains('parent_id')
    def _check_parent_recursion(self):
        """Prevent circular parent relationships"""
        if not self._check_recursion():
            raise ValidationError('Không thể tạo danh mục cha con đệ quy!')

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

    @api.model_create_multi
    def create(self, vals_list):
        """Auto-generate slug on create"""
        for vals in vals_list:
            if 'name' in vals and 'slug' not in vals:
                vals['slug'] = self._generate_slug(vals['name'])
            elif 'slug' in vals:
                # Ensure slug is URL-friendly
                vals['slug'] = self._generate_slug(vals['slug'])
        return super().create(vals_list)

    def write(self, vals):
        """Auto-generate slug on write if name changes"""
        if 'name' in vals and 'slug' not in vals:
            vals['slug'] = self._generate_slug(vals['name'])
        elif 'slug' in vals:
            # Ensure slug is URL-friendly
            vals['slug'] = self._generate_slug(vals['slug'])
        return super().write(vals)

    def name_get(self):
        """Display full path for nested categories"""
        result = []
        for record in self:
            if record.parent_id:
                name = f"{record.parent_id.name} / {record.name}"
            else:
                name = record.name
            result.append((record.id, name))
        return result

    @api.model
    def _name_search(self, name, args=None, operator='ilike', limit=100, name_get_uid=None):
        """Search by name or slug"""
        args = args or []
        domain = []
        if name:
            domain = ['|', ('name', operator, name), ('slug', operator, name)]
        return self._search(domain + args, limit=limit, access_rights_uid=name_get_uid)
