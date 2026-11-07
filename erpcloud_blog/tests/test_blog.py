# -*- coding: utf-8 -*-
from odoo.tests.common import TransactionCase


class TestERPCloudBlog(TransactionCase):

    def setUp(self):
        super().setUp()
        self.category = self.env['erpcloud.blog.category'].create({
            'name': 'ERP Technology',
            'slug': 'erp-technology',
        })
        self.tag = self.env['erpcloud.blog.tag'].create({
            'name': 'Innovation',
            'slug': 'innovation',
        })

    def test_blog_post_lifecycle(self):
        post = self.env['erpcloud.blog.post'].create({
            'name': 'Getting Started with Odoo 20',
            'category_id': self.category.id,
            'tag_ids': [(6, 0, [self.tag.id])],
            'content': '<p>This is a test post about Odoo 20 capabilities.</p>',
        })
        self.assertEqual(post.state, 'draft')
        self.assertFalse(post.is_published)

        # Test submit review
        post.action_submit_review()
        self.assertEqual(post.state, 'review')

        # Test publish
        post.action_publish()
        self.assertEqual(post.state, 'published')
        self.assertTrue(post.is_published)

        # Test unpublish
        post.action_unpublish()
        self.assertEqual(post.state, 'draft')
        self.assertFalse(post.is_published)

    def test_comment_creation(self):
        post = self.env['erpcloud.blog.post'].create({
            'name': 'Comment Test Post',
            'category_id': self.category.id,
            'content': '<p>Testing comments.</p>',
        })
        comment = self.env['erpcloud.blog.comment'].create({
            'post_id': post.id,
            'author_name': 'Test User',
            'author_email': 'test@example.com',
            'content': 'Great article!',
        })
        self.assertEqual(comment.state, 'pending')
        comment.action_approve()
        self.assertEqual(comment.state, 'approved')
