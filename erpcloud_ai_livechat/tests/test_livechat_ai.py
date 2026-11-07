# -*- coding: utf-8 -*-
from odoo.tests.common import TransactionCase
from unittest.mock import patch


class TestERPCloudLivechatAI(TransactionCase):

    def setUp(self):
        super().setUp()
        self.bot_partner = self.env.ref(
            'erpcloud_ai_livechat.partner_erpcloud_livechat_bot', raise_if_not_found=False
        ) or self.env['res.partner'].create({'name': 'Test Bot'})

        self.livechat_channel = self.env['im_livechat.channel'].create({
            'name': 'Customer Care Support',
            'erpcloud_mode': 'agent',
            'erpcloud_bot_partner_id': self.bot_partner.id,
            'erpcloud_ai_provider': 'openai',
            'erpcloud_ai_api_key': 'sk-test-key-12345',
            'erpcloud_ai_model': 'gpt-4o-mini',
            'erpcloud_ai_system_prompt': 'You are a test customer support bot.',
            'erpcloud_handoff_keywords': 'nhân viên, human, support',
        })

    def test_livechat_channel_configuration(self):
        self.assertEqual(self.livechat_channel.erpcloud_mode, 'agent')
        self.assertEqual(self.livechat_channel.erpcloud_ai_provider, 'openai')
        self.assertEqual(self.livechat_channel.erpcloud_ai_model, 'gpt-4o-mini')

    def test_discuss_post_hook_preserves_core_message_flow(self):
        channel = self.env['discuss.channel'].create({'name': 'Internal QA'})
        message = channel.message_post(body='Message from an internal Odoo user')
        self.assertEqual(message.model, 'discuss.channel')
        self.assertEqual(message.res_id, channel.id)

    def test_handoff_reports_only_an_assigned_operator(self):
        job = self.env['erpcloud.livechat.job'].new()
        channel = self.env['discuss.channel'].create({'name': 'Handoff QA'})
        with patch.object(type(channel), '_forward_human_operator', return_value={'agent': False}):
            self.assertFalse(job._handoff_to_human(channel))
        with patch.object(type(channel), '_forward_human_operator', return_value={'agent': self.env.user}):
            self.assertTrue(job._handoff_to_human(channel))

    def test_payment_card_check(self):
        job = self.env['erpcloud.livechat.job'].new()
        self.assertTrue(job._contains_payment_card_data('Here is my card 4532 0150 1234 5678'))
        self.assertFalse(job._contains_payment_card_data('Order id #12345'))

    def test_handoff_keywords_extraction(self):
        job = self.env['erpcloud.livechat.job'].new()
        keywords = job._get_handoff_keywords(self.livechat_channel)
        self.assertIn('nhân viên', keywords)
        self.assertIn('human', keywords)
        self.assertIn('support', keywords)

    def test_provider_error_does_not_reach_visitor(self):
        job = self.env['erpcloud.livechat.job'].new()
        with patch('odoo.addons.erpcloud_ai_livechat.models.erpcloud_livechat_job.requests.post',
                   side_effect=RuntimeError('private-provider-detail')):
            reply = job._call_llm(self.livechat_channel, [{'role': 'user', 'content': 'Hello'}])
        self.assertIn('không khả dụng', reply)
        self.assertNotIn('private-provider-detail', reply)

    def test_provider_success_uses_configured_model(self):
        job = self.env['erpcloud.livechat.job'].new()
        with patch('odoo.addons.erpcloud_ai_livechat.models.erpcloud_livechat_job.requests.post') as post:
            post.return_value.status_code = 200
            post.return_value.json.return_value = {'choices': [{'message': {'content': 'Xin chào'}}]}
            reply = job._call_llm(self.livechat_channel, [{'role': 'user', 'content': 'Hello'}])
        self.assertEqual(reply, 'Xin chào')
        self.assertEqual(post.call_args.kwargs['json']['model'], 'gpt-4o-mini')
