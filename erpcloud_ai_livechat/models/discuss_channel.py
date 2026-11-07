# -*- coding: utf-8 -*-

import logging

from odoo import models

_logger = logging.getLogger(__name__)


class DiscussChannel(models.Model):
    _inherit = 'discuss.channel'

    def _message_post_after_hook(self, message):
        res = super()._message_post_after_hook(message)

        for channel in self:
            try:
                if channel.channel_type != 'livechat':
                    continue
                livechat_cfg = channel.livechat_channel_id
                if not livechat_cfg or livechat_cfg.erpcloud_mode != 'agent':
                    continue

                # Skip bot messages (anti-loop)
                bot_partner = livechat_cfg.erpcloud_bot_partner_id or self.env.ref(
                    'erpcloud_ai_livechat.partner_erpcloud_livechat_bot', raise_if_not_found=False
                )
                if bot_partner and message.author_id == bot_partner:
                    continue

                # Trigger only on visitor messages
                is_visitor = bool(message.author_guest_id) or (channel.channel_type == 'livechat' and not message.author_id.user_ids)
                if not is_visitor:
                    continue

                self.env['erpcloud.livechat.job'].sudo().create_job_if_needed(channel, message)
            except Exception:
                _logger.exception('Could not enqueue AI livechat reply for channel %s', channel.id)
                continue

        return res
