# -*- coding: utf-8 -*-

import json
import logging
import re
import requests

from odoo import api, fields, models
from odoo.exceptions import UserError
from odoo.tools import html2plaintext

_logger = logging.getLogger(__name__)


class ErpcloudLivechatJob(models.Model):
    _name = 'erpcloud.livechat.job'
    _description = 'ERPCloud Livechat AI Job'
    _order = 'id desc'

    state = fields.Selection(
        [
            ('pending', 'Pending'),
            ('running', 'Running'),
            ('done', 'Done'),
            ('error', 'Error'),
        ],
        default='pending',
        required=True,
        index=True,
    )

    channel_id = fields.Many2one('discuss.channel', required=True, index=True, ondelete='cascade')
    trigger_message_id = fields.Many2one('mail.message', required=True, index=True, ondelete='cascade')

    error_message = fields.Text()

    @api.model
    def create_job_if_needed(self, channel, message):
        """Idempotency guard: create at most one pending job per message."""
        existing = self.search([
            ('channel_id', '=', channel.id),
            ('trigger_message_id', '=', message.id),
            ('state', 'in', ['pending', 'running', 'done']),
        ], limit=1)
        if existing:
            return existing
        return self.create({'channel_id': channel.id, 'trigger_message_id': message.id})

    def _contains_payment_card_data(self, text):
        digits = re.sub(r'[^0-9]', '', text or '')
        return 13 <= len(digits) <= 19

    def _enforce_max_turns(self, channel, livechat_cfg):
        max_turns = int(livechat_cfg.erpcloud_max_auto_turns or 0)
        if not max_turns:
            return False
        bot_partner = livechat_cfg.erpcloud_bot_partner_id
        if not bot_partner:
            return False
        bot_count = len(channel.message_ids.filtered(
            lambda m: m.message_type == 'comment' and m.author_id == bot_partner
        ))
        return bot_count >= max_turns

    def _get_handoff_keywords(self, livechat_cfg):
        raw = (livechat_cfg.erpcloud_handoff_keywords or '').strip()
        if not raw:
            return []
        return [k.strip().lower() for k in raw.split(',') if k.strip()]

    def _build_transcript(self, channel, limit=20):
        msgs = channel.message_ids.filtered(lambda m: m.message_type == 'comment').sorted('id')[-limit:]
        transcript = []
        bot_partner = channel.livechat_channel_id.erpcloud_bot_partner_id
        for m in msgs:
            content = html2plaintext(m.body or '').strip()
            if not content:
                continue
            is_bot = bool(bot_partner and m.author_id == bot_partner)
            is_visitor = bool(m.author_guest_id) or (channel.channel_type == 'livechat' and not m.author_id.user_ids)
            role = 'assistant' if (is_bot or not is_visitor) else 'user'
            transcript.append({'role': role, 'content': content})
        return transcript

    def _post_bot_message(self, channel, body_text):
        livechat_cfg = channel.livechat_channel_id
        bot_partner = livechat_cfg.erpcloud_bot_partner_id or self.env.ref(
            'erpcloud_ai_livechat.partner_erpcloud_livechat_bot', raise_if_not_found=False
        )
        if not bot_partner:
            bot_partner = self.env['res.partner'].search([('name', '=', 'ERPCloud AI Assistant')], limit=1)
        if not bot_partner:
            bot_partner = self.env.user.partner_id
        return channel.with_context(mail_post_autofollow_author_skip=True).sudo().message_post(
            author_id=bot_partner.id,
            body=body_text,
            message_type='comment',
            subtype_xmlid='mail.mt_comment',
        )

    def _handoff_to_human(self, channel):
        try:
            return bool(channel._forward_human_operator(chatbot_script_step=None).get('agent'))
        except Exception:
            _logger.exception('Livechat handoff failed for channel %s', channel.id)
            return False

    def _call_llm(self, livechat_cfg, transcript):
        """Self-contained LLM invocation using standard OpenAI-compatible API or Gemini."""
        api_key = (livechat_cfg.erpcloud_ai_api_key or '').strip()
        if not api_key:
            return '⚠️ Chưa cấu hình API Key trong thiết lập kênh Livechat AI.'

        provider = livechat_cfg.erpcloud_ai_provider or 'openai'
        model = (livechat_cfg.erpcloud_ai_model or '').strip()
        system_prompt = (livechat_cfg.erpcloud_ai_system_prompt or '').strip()
        temperature = livechat_cfg.erpcloud_ai_temperature if livechat_cfg.erpcloud_ai_temperature is not False else 0.7

        if provider == 'gemini':
            # Gemini via Google's OpenAI-compatible endpoint
            api_base = 'https://generativelanguage.googleapis.com/v1beta/openai'
            if not model:
                model = 'gemini-1.5-flash'
        else:
            api_base = (livechat_cfg.erpcloud_ai_api_base or 'https://api.openai.com/v1').strip().rstrip('/')
            if not model:
                model = 'gpt-4o-mini'

        endpoint = f"{api_base.rstrip('/')}/chat/completions"
        headers = {
            'Authorization': f"Bearer {api_key}",
            'Content-Type': 'application/json',
        }
        messages = []
        if system_prompt:
            messages.append({'role': 'system', 'content': system_prompt})
        messages.extend(transcript)

        payload = {
            'model': model,
            'messages': messages,
            'temperature': temperature,
        }

        try:
            resp = requests.post(endpoint, headers=headers, json=payload, timeout=30)
            if resp.status_code != 200:
                _logger.warning('LLM API returned HTTP %s for livechat channel %s', resp.status_code, livechat_cfg.id)
                return f"⚠️ Lỗi kết nối AI (Mã lỗi {resp.status_code})."
            data = resp.json()
            choices = data.get('choices') or []
            if choices and choices[0].get('message'):
                return choices[0]['message'].get('content', '').strip()
            return '⚠️ AI không trả về phản hồi phù hợp.'
        except requests.exceptions.Timeout:
            _logger.warning('LLM API timeout for channel %s', livechat_cfg.id)
            return '⚠️ Hệ thống AI phản hồi chậm, vui lòng thử lại sau giây lát.'
        except Exception:
            _logger.exception('LLM API call failed for livechat channel %s', livechat_cfg.id)
            return '⚠️ Dịch vụ AI tạm thời không khả dụng. Vui lòng thử lại hoặc gặp nhân viên hỗ trợ.'

    def _run_one(self):
        self.ensure_one()
        channel = self.channel_id.sudo()
        msg = self.trigger_message_id.sudo()
        livechat_cfg = channel.livechat_channel_id.sudo()

        if channel.channel_type != 'livechat' or not livechat_cfg:
            self.state = 'done'
            return
        if livechat_cfg.erpcloud_mode != 'agent':
            self.state = 'done'
            return

        bot_partner = livechat_cfg.erpcloud_bot_partner_id or self.env.ref(
            'erpcloud_ai_livechat.partner_erpcloud_livechat_bot', raise_if_not_found=False
        )
        if bot_partner and msg.author_id == bot_partner:
            self.state = 'done'
            return

        # Payment card security check
        if self._contains_payment_card_data(msg.body):
            self._post_bot_message(
                channel,
                '⚠️ Vì lý do bảo mật, xin vui lòng không gửi thông tin số thẻ tín dụng hoặc thanh toán qua tin nhắn.'
            )
            self.state = 'done'
            return

        # Handoff keyword detection
        keywords = self._get_handoff_keywords(livechat_cfg)
        user_text = html2plaintext(msg.body or '').strip().lower()
        if keywords and any(k in user_text for k in keywords):
            connected = self._handoff_to_human(channel)
            message = ('A human operator will continue this chat.' if connected else
                       'No operator is available right now. Please try again later.')
            self._post_bot_message(channel, message)
            self.state = 'done'
            return

        # Enforce max turns limit
        if self._enforce_max_turns(channel, livechat_cfg):
            connected = self._handoff_to_human(channel)
            message = ('The AI turn limit was reached. A human operator will continue this chat.' if connected else
                       'The AI turn limit was reached. No operator is available right now.')
            self._post_bot_message(channel, message)
            self.state = 'done'
            return

        # Rate limit: at most 1 AI reply per 2 seconds per channel
        if bot_partner:
            last_bot_msg = channel.message_ids.filtered(
                lambda m: m.message_type == 'comment' and m.author_id == bot_partner
            ).sorted('id')[-1:]
            if last_bot_msg and last_bot_msg.create_date:
                delta = fields.Datetime.now() - last_bot_msg.create_date
                if delta.total_seconds() < 2:
                    self.state = 'done'
                    return

        # Build transcript and query AI
        transcript = self._build_transcript(channel)
        ai_reply = self._call_llm(livechat_cfg, transcript)
        if ai_reply:
            self._post_bot_message(channel, ai_reply)

        self.state = 'done'

    @api.model
    def run_pending_jobs(self, limit=20):
        jobs = self.search([('state', '=', 'pending')], limit=limit)
        for job in jobs:
            try:
                job.state = 'running'
                job._run_one()
            except Exception as e:
                _logger.exception('Livechat AI job failed: %s', e)
                job.write({'state': 'error', 'error_message': str(e)})
