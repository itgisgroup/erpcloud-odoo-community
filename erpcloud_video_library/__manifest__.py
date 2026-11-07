# -*- coding: utf-8 -*-
{
    'name': 'ERPCloud Video Library',
    'version': '20.0.1.2.0',
    'category': 'Website',
    'summary': 'Dynamic Video Showcase & Snippet for Odoo Websites',
    'description': """
Manage and display professional tutorial and marketing videos on your website.
Features:
- YouTube video ID validation and public thumbnail display with a branded fallback
- Categorization & Tags
- Featured videos
- Website page and drag-and-drop snippet
    """,
    'author': 'ERPCloud',
    'website': 'https://erpcloud.vn',
    'support': 'info@erpcloud.vn',
    'license': 'LGPL-3',
    'depends': [
        'website',
        'mail',
        'portal',
    ],
    'data': [
        'security/video_security.xml',
        'security/ir.access.csv',
        'views/video_category_views.xml',
        'views/video_tag_views.xml',
        'views/video_views.xml',
        'views/video_snippet_templates.xml',
        'views/video_library_page.xml',
        'views/video_snippets.xml',
        'views/video_menus.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'erpcloud_video_library/static/src/css/video_library.css',
            'erpcloud_video_library/static/src/js/video_library.js',
        ],
    },
    'images': [
        'static/description/cover.png',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
