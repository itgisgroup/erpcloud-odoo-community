# -*- coding: utf-8 -*-

from odoo import http
from odoo.http import request
from werkzeug.exceptions import NotFound
from markupsafe import Markup
from odoo.tools import html_sanitize
import logging
import json
import re

_logger = logging.getLogger(__name__)


class BlogController(http.Controller):
    """Frontend Blog Controller - Professional Blog System"""

    def _convert_embedded_video_to_iframe(self, content):
        """
        Convert Odoo embedded video components to simple iframes
        This fixes Owl component mounting issues in custom layouts

        Example input:
        <div data-embedded="video" data-embedded-props='{"videoId":"6tg8lDr4cPE","platform":"youtube","params":{...}}' class="media_iframe_video"></div>

        Example output:
        <div class="video-responsive-wrapper">
            <iframe src="https://www.youtube.com/embed/6tg8lDr4cPE?..." ...></iframe>
        </div>
        """
        if not content:
            return content

        try:
            # Pattern to find embedded video divs (handles both ' and " quotes, and HTML entities)
            pattern = r'<div[^>]*data-embedded=["\']video["\'][^>]*data-embedded-props=["\']([^"\']+)["\'][^>]*>.*?</div>'

            def replace_video(match):
                try:
                    # Extract props JSON (may contain HTML entities)
                    props_json = match.group(1)

                    # Unescape HTML entities
                    import html
                    props_json = html.unescape(props_json)

                    props = json.loads(props_json)

                    video_id = props.get('videoId', '')
                    platform = props.get('platform', 'youtube')
                    params = props.get('params', {})

                    if not video_id:
                        return match.group(0)

                    # Build YouTube URL with params
                    if platform == 'youtube':
                        param_str = '&'.join([f"{k}={v}" for k, v in params.items()])
                        iframe_src = f"https://www.youtube.com/embed/{video_id}"
                        if param_str:
                            iframe_src += f"?{param_str}"

                        # Create responsive iframe wrapper
                        return f'''<div class="video-responsive-wrapper" style="position: relative; padding-bottom: 56.25%; height: 0; overflow: hidden; margin: 32px 0; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.1);">
    <iframe src="{iframe_src}" frameborder="0" allowfullscreen="allowfullscreen" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" style="position: absolute; top: 0; left: 0; width: 100%; height: 100%; border-radius: 12px;" aria-label="Video"></iframe>
</div>'''

                    return match.group(0)

                except Exception as e:
                    _logger.warning(f"Error parsing video props: {str(e)}")
                    return match.group(0)

            # Replace all embedded videos
            result = re.sub(pattern, replace_video, content, flags=re.DOTALL)

            # Count replacements
            count = len(re.findall(pattern, content, flags=re.DOTALL))
            if count > 0:
                _logger.info(f"Converted {count} embedded video(s) to iframe(s)")

            return result

        except Exception as e:
            _logger.error(f"Error converting embedded videos: {str(e)}")
            return content

    # ==================== BLOG LIST ====================

    @http.route([
        '/blog',
        '/blog/page/<int:page>',
        '/tin-tuc',
        '/tin-tuc/page/<int:page>',
    ], type='http', auth='public', website=True, sitemap=True)
    def blog_list(self, page=1, category=None, tag=None, search=None, **kwargs):
        """
        Blog list page with pagination, filtering, and search

        URL Examples:
        - /blog
        - /blog/page/2
        - /blog?category=b2b-ecommerce
        - /blog?tag=odoo
        - /blog?search=make+to+order
        """

        # Posts per page
        posts_per_page = 12

        # Build domain
        domain = [('state', '=', 'published')]

        # Filter by category
        if category:
            cat = request.env['erpcloud.blog.category'].sudo().search([
                ('slug', '=', category)
            ], limit=1)
            if cat:
                domain.append(('category_id', '=', cat.id))

        # Filter by tag
        if tag:
            tag_obj = request.env['erpcloud.blog.tag'].sudo().search([
                ('slug', '=', tag)
            ], limit=1)
            if tag_obj:
                domain.append(('tag_ids', 'in', tag_obj.id))

        # Search
        if search:
            domain.append('|')
            domain.append(('name', 'ilike', search))
            domain.append(('content', 'ilike', search))

        # Get posts
        Post = request.env['erpcloud.blog.post'].sudo()
        total_posts = Post.search_count(domain)

        # Pagination
        offset = (page - 1) * posts_per_page
        posts = Post.search(domain, limit=posts_per_page, offset=offset, order='published_date DESC, id DESC')

        # Calculate pagination
        total_pages = (total_posts + posts_per_page - 1) // posts_per_page

        # Get featured posts (for sidebar)
        featured_posts = Post.search([
            ('state', '=', 'published'),
            ('is_featured', '=', True)
        ], limit=5, order='published_date DESC')

        # Get categories (for sidebar)
        categories = request.env['erpcloud.blog.category'].sudo().search([], order='sequence, name')

        # Get popular tags (for sidebar)
        tags = request.env['erpcloud.blog.tag'].sudo().search([], order='post_count DESC, name', limit=20)

        values = {
            'posts': posts,
            'total_posts': total_posts,
            'page': page,
            'total_pages': total_pages,
            'posts_per_page': posts_per_page,
            'featured_posts': featured_posts,
            'categories': categories,
            'tags': tags,
            'current_category': category,
            'current_tag': tag,
            'search_query': search,
        }

        return request.render('erpcloud_blog.blog_list_template', values)

    # ==================== BLOG DETAIL ====================

    @http.route([
        '/blog/<string:slug>',
        '/tin-tuc/<string:slug>',
    ], type='http', auth='public', website=True, sitemap=True)
    def blog_detail(self, slug, **kwargs):
        """
        Blog detail page with related posts, comments, social share

        URL Examples:
        - /blog/b2b-ecommerce-la-gi-huong-dan-toan-dien
        - /tin-tuc/make-to-order-mo-hinh-san-xuat-theo-don-hang
        """

        # Get post by slug
        post = request.env['erpcloud.blog.post'].sudo().search([
            ('slug', '=', slug),
            ('state', '=', 'published')
        ], limit=1)

        if not post:
            raise NotFound()

        # Track view (async, don't block page load)
        try:
            post.sudo()._track_view()
        except Exception as e:
            _logger.warning(f"Could not track view for post {post.id}: {str(e)}")

        # Get related posts (same category or tags)
        related_posts = request.env['erpcloud.blog.post'].sudo().search([
            ('id', '!=', post.id),
            ('state', '=', 'published'),
            '|',
            ('category_id', '=', post.category_id.id),
            ('tag_ids', 'in', post.tag_ids.ids)
        ], limit=6, order='published_date DESC')

        # Get approved comments
        comments = request.env['erpcloud.blog.comment'].sudo().search([
            ('post_id', '=', post.id),
            ('state', '=', 'approved')
        ], order='create_date DESC')

        # Get next/previous posts
        next_post = request.env['erpcloud.blog.post'].sudo().search([
            ('published_date', '>', post.published_date),
            ('state', '=', 'published')
        ], limit=1, order='published_date ASC')

        prev_post = request.env['erpcloud.blog.post'].sudo().search([
            ('published_date', '<', post.published_date),
            ('state', '=', 'published')
        ], limit=1, order='published_date DESC')

        # Convert embedded videos to simple iframes
        processed_content = Markup(html_sanitize(self._convert_embedded_video_to_iframe(post.content or '')))

        values = {
            'post': post,
            'processed_content': processed_content,
            'related_posts': related_posts,
            'comments': comments,
            'next_post': next_post,
            'prev_post': prev_post,
        }

        return request.render('erpcloud_blog.blog_detail_template', values)

    # ==================== CATEGORY PAGE ====================

    @http.route([
        '/blog/category/<string:slug>',
        '/blog/category/<string:slug>/page/<int:page>',
    ], type='http', auth='public', website=True, sitemap=True)
    def blog_category(self, slug, page=1, **kwargs):
        """Category page - redirect to blog list with category filter"""
        return self.blog_list(page=page, category=slug, **kwargs)

    # ==================== TAG PAGE ====================

    @http.route([
        '/blog/tag/<string:slug>',
        '/blog/tag/<string:slug>/page/<int:page>',
    ], type='http', auth='public', website=True, sitemap=True)
    def blog_tag(self, slug, page=1, **kwargs):
        """Tag page - redirect to blog list with tag filter"""
        return self.blog_list(page=page, tag=slug, **kwargs)

    # ==================== COMMENT SUBMISSION ====================

    @http.route('/blog/comment/submit', type='http', auth='public', methods=['POST'], website=True, csrf=True)
    def submit_comment(self, **post):
        """Submit a comment (requires moderation)"""

        post_id = post.get('post_id')
        name = post.get('name')
        email = post.get('email')
        content = post.get('content')

        if not all([post_id, name, email, content]) or len(name) > 100 or len(email) > 255 or len(content) > 5000:
            return request.redirect('/blog?error=missing_fields')

        # Create comment (pending approval)
        try:
            post_obj = request.env['erpcloud.blog.post'].sudo().browse(int(post_id)).exists()
            if not post_obj or post_obj.state != 'published' or not post_obj.allow_comments:
                raise ValueError('Comments are closed')
            comment = request.env['erpcloud.blog.comment'].sudo().create({
                'post_id': post_obj.id,
                'author_name': name.strip(),
                'author_email': email.strip(),
                'content': content,
                'state': 'pending',
            })
            _logger.info('Blog comment %s submitted for moderation', comment.id)

            # Redirect back to post with success message
            return request.redirect(f'/blog/{post_obj.slug}?comment=success')

        except (ValueError, TypeError) as e:
            _logger.info('Blog comment rejected: %s', e)
            return request.redirect('/blog?error=comment_failed')
        except Exception:
            _logger.exception('Could not create blog comment')
            return request.redirect('/blog?error=comment_failed')
