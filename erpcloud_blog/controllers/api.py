"""Small public JSON-RPC API exposing only published blog content."""

from odoo import http
from odoo.http import request


class BlogAPIController(http.Controller):

    @http.route('/api/blog/posts', type='jsonrpc', auth='public', methods=['POST'], csrf=False)
    def get_posts(self, limit=12, offset=0):
        try:
            limit = max(1, min(int(limit), 50))
            offset = max(0, min(int(offset), 10000))
        except (TypeError, ValueError):
            return {'error': 'invalid_pagination'}
        posts = request.env['erpcloud.blog.post'].sudo().search(
            [('state', '=', 'published'), ('is_published', '=', True)],
            limit=limit, offset=offset, order='published_date desc, id desc')
        return {'posts': [{
            'id': post.id, 'title': post.name, 'slug': post.slug,
            'excerpt': post.excerpt or '', 'category': post.category_id.name,
            'published_date': post.published_date.isoformat() if post.published_date else None,
        } for post in posts]}

    @http.route('/api/blog/post/<int:post_id>', type='jsonrpc', auth='public', methods=['POST'], csrf=False)
    def get_post(self, post_id):
        post = request.env['erpcloud.blog.post'].sudo().search([
            ('id', '=', post_id), ('state', '=', 'published'), ('is_published', '=', True)
        ], limit=1)
        if not post:
            return {'error': 'not_found'}
        return {'post': {
            'id': post.id, 'title': post.name, 'slug': post.slug,
            'excerpt': post.excerpt or '', 'content': post.content or '',
            'category': post.category_id.name,
            'published_date': post.published_date.isoformat() if post.published_date else None,
        }}
