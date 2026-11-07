# -*- coding: utf-8 -*-
{
    'name': 'ERPCloud AI Livechat',
    'version': '20.0.1.2.0',
    'category': 'Productivity/AI',
    'summary': 'Automated AI Operator for Odoo Livechat',
    'description': """
Automate customer livechat inquiries using AI agents powered by OpenAI, Google Gemini, or compatible LLMs.

Key Features:
- Enable/disable AI Operator per livechat channel
- Support OpenAI (ChatGPT), Google Gemini, and OpenAI-compatible endpoints (Ollama, DeepSeek, Groq)
- Customizable system prompt and bot persona per channel
- Intelligent handoff to human operators upon user request
- Anti-loop protection and conversational rate limiting
- Background processing for incoming chat messages
    """,
    'author': 'ERPCloud',
    'website': 'https://erpcloud.vn',
    'support': 'info@erpcloud.vn',
    'license': 'LGPL-3',
    'depends': [
        'im_livechat',
        'mail',
    ],
    'data': [
        'security/ir.access.csv',
        'data/erpcloud_ai_livechat_data.xml',
        'views/im_livechat_channel_views.xml',
    ],
    'images': [
        'static/description/cover.png',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
