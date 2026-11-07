# ERPCloud AI Livechat — Odoo 20 Community

Add an optional AI reply assistant to Odoo's standard Livechat channels. Configure each channel's provider, model, prompt and handoff policy from the channel form.

## Included

- OpenAI-compatible chat-completions API, including compatible Gemini endpoints
- Per-channel API key, endpoint, model, persona and temperature
- Human handoff keywords, anti-loop limits and maximum AI turns
- Background handling of incoming visitor messages
- A safe visitor error message that does not expose provider response details

## Install and use

1. Install on Odoo 20 Community with standard `im_livechat` and `mail` apps available.
2. Open a Livechat channel and enable AI mode. Enter your provider endpoint, model and API key.
3. Test on a staging website with your own provider account before enabling it for production visitors.

No provider key or sample conversation is installed. External provider fees and network access are the operator's responsibility. Automated tests use mocked provider replies; a live provider acceptance test requires customer credentials and is not included in the release gate.

LGPL-3. Support: info@erpcloud.vn.
