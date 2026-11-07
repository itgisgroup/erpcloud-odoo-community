# -*- coding: utf-8 -*-
{
    'name': 'ERPCloud Blog & News',
    'version': '20.0.1.1.0',
    'category': 'Website/Blog',
    'summary': 'Professional Blog & News Content Management System',
    'description': """
Professional Blog and News content management system with categories, tags, comments, SEO metadata, and frontend website templates.
Features:
- WYSIWYG rich text content editing
- Categories and tags management
- Editorial workflow (Draft -> Review -> Published)
- Editable SEO title and description fields
- Comment system with moderation
- Reading time calculation and view tracking
- Clean responsive frontend templates
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
        'security/blog_security.xml',
        'security/ir.access.csv',
        'views/blog_post_views.xml',
        'views/blog_category_views.xml',
        'views/blog_tag_views.xml',
        'views/blog_comment_views.xml',
        'views/blog_media_views.xml',
        'views/blog_menus.xml',
        'views/blog_list_template.xml',
        'views/blog_detail_template.xml',
        'views/blog_website_menu.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'erpcloud_blog/static/src/css/blog_list.css',
            'erpcloud_blog/static/src/css/blog_detail.css',
            'erpcloud_blog/static/src/css/blog_content_images.css',
        ],
    },
    'images': [
        'static/description/cover.png',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
