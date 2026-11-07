# -*- coding: utf-8 -*-

from odoo import fields, models


class ImLivechatChannel(models.Model):
    _inherit = 'im_livechat.channel'

    erpcloud_mode = fields.Selection(
        selection=[('human', 'Human'), ('agent', 'AI Agent')],
        string='Conversation Mode',
        default='human',
        required=True,
        help='Human: default livechat behavior. AI Agent: auto-reply using AI agent.',
    )

    erpcloud_bot_partner_id = fields.Many2one(
        'res.partner',
        string='Bot Partner',
        help='Partner used as author for AI messages (anti-loop).',
    )

    erpcloud_ai_provider = fields.Selection(
        selection=[
            ('openai', 'OpenAI / Compatible (ChatGPT, Groq, DeepSeek, Ollama)'),
            ('gemini', 'Google Gemini'),
        ],
        string='AI Provider',
        default='openai',
        help='LLM API provider for automated livechat responses.',
    )

    erpcloud_ai_api_key = fields.Char(
        string='API Key',
        copy=False,
        help='API Key for OpenAI / Gemini provider.',
    )

    erpcloud_ai_api_base = fields.Char(
        string='API Endpoint',
        default='https://api.openai.com/v1',
        help='Base URL for API requests. E.g. https://api.openai.com/v1 or custom OpenAI-compatible endpoint.',
    )

    erpcloud_ai_model = fields.Char(
        string='AI Model',
        default='gpt-4o-mini',
        help='Model identifier (e.g. gpt-4o-mini, gpt-4o, gemini-1.5-flash).',
    )

    erpcloud_ai_system_prompt = fields.Text(
        string='System Prompt',
        default='Bạn là trợ lý AI thông minh hỗ trợ khách hàng của ERPCloud. Hãy trả lời ngắn gọn, lịch sự và giải đáp chính xác thắc mắc của khách hàng.',
        help='System instructions that guide the AI tone and answers.',
    )

    erpcloud_ai_temperature = fields.Float(
        string='Temperature',
        default=0.7,
        help='Sampling temperature between 0.0 and 1.0.',
    )

    erpcloud_handoff_keywords = fields.Char(
        string='Handoff Keywords',
        default='gặp người, nhân viên, tư vấn viên, gặp tư vấn viên, hỗ trợ người',
        help="Comma-separated keywords that trigger handoff to human.",
    )

    erpcloud_max_auto_turns = fields.Integer(
        string='Max Auto Turns',
        default=30,
        help='Safety limit for auto replies per conversation.',
    )
