# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request
from werkzeug.exceptions import BadRequest

class VideoController(http.Controller):

    @http.route('/video-library', type='http', auth='public', website=True, sitemap=True)
    def video_library_page(self, **kwargs):
        return request.render('erpcloud_video_library.video_library_page')

    @http.route(['/video_library/get_videos'], type='jsonrpc', auth='public', website=True)
    def get_videos(self, category_id=None, limit=6):
        try:
            limit = max(1, min(int(limit), 24))
            selected_category = int(category_id) if category_id and category_id != 'all' else None
        except (TypeError, ValueError) as exc:
            raise BadRequest('Invalid video filter') from exc
        domain = [('state', '=', 'published'), ('is_published', '=', True)]
        if selected_category:
            domain.append(('category_id', '=', selected_category))

        videos = request.env['erpcloud.video'].sudo().search(domain, limit=limit)
        categories = request.env['erpcloud.video.category'].sudo().search([('active', '=', True)])

        return {
            'videos': [{
                'id': v.id,
                'name': v.name,
                'video_url': v.video_url,
                'video_id': v.video_id,
                'duration': v.duration,
                'description': v.description,
                'category_name': v.category_id.name,
                'category_slug': v.category_id.slug,
                'is_featured': v.is_featured,
            } for v in videos],
            'categories': [{
                'id': c.id,
                'name': c.name,
                'slug': c.slug,
            } for c in categories]
        }
