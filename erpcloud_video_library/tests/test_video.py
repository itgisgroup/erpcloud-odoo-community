# -*- coding: utf-8 -*-
from odoo.tests.common import TransactionCase


class TestERPCloudVideo(TransactionCase):

    def setUp(self):
        super().setUp()
        self.category = self.env['erpcloud.video.category'].create({
            'name': 'Tutorials',
            'slug': 'tutorials',
        })
        self.tag = self.env['erpcloud.video.tag'].create({
            'name': 'ERP',
            'slug': 'erp',
        })

    def test_youtube_video_id_computation(self):
        video = self.env['erpcloud.video'].create({
            'name': 'Odoo 20 Overview',
            'video_url': 'https://www.youtube.com/watch?v=dQw4w9WgXcQ',
            'category_id': self.category.id,
            'tag_ids': [(6, 0, [self.tag.id])],
        })
        self.assertEqual(video.video_id, 'dQw4w9WgXcQ')
        self.assertEqual(video.state, 'draft')
        self.assertFalse(video.is_published)

        # Test publish action
        video.action_publish()
        self.assertEqual(video.state, 'published')
        self.assertTrue(video.is_published)

        # Test unpublish action
        video.action_unpublish()
        self.assertEqual(video.state, 'draft')
        self.assertFalse(video.is_published)
